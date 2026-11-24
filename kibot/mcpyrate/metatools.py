# -*- coding: utf-8; -*-
"""Macros that expand macros.

Less silly than it sounds; these are convenient when working with quasiquoted
code, and with run-time AST values in general. Run-time AST values are exactly
the kind of thing macros operate on: the macro expansion time of the use site
is the run time of the macro implementation itself.

Also, if you have a quasiquoted tree, run-time expansion also has the benefit
that any unquoted values will have been spliced in. Unquotes operate partly
at run time of the use site of `q`. They must; the only context that has the
user-provided names (where the unquoted data comes from) in scope is each
particular use site of `q`, at its run time. The quasiquoted tree is only
fully ready at run time of the use site of `q`.

The suffixes `1srq` mean:

 - `1`: once. Expand one layer of macros only.
 - `s`: statically, i.e. at macro expansion time.
 - `r`: dynamically, i.e. at run time.
 - `q`: quote first. Apply `q` first, then the expander.

You'll most likely want `expandr` or `expand1r`.

**When to use**:

If you want to expand a tree using the macro bindings *from your macro's use
site*, you should use `expander.visit` and its sisters (`visit_once`,
`visit_recursively`).

If you want to expand a tree using the macro bindings *from your macro's
definition site*, you should use the `expand` family of macros.
"""

__all__ = ["macro_bindings",
           "fill_location",
           "expand1sq", "expandsq",
           "expand1s", "expands",
           "expand1rq", "expandrq",
           "expand1r", "expandr",
           "stepr",
           "expand_first"]

import ast

# Note we import some macros as regular functions. We just want their syntax transformers.
from .astfixers import fix_locations  # noqa: F401, used in macro output.
from .coreutils import _mcpyrate_attr
from .debug import step_expansion  # noqa: F401, used in macro output.
from .expander import MacroExpander, namemacro, parametricmacro
from .quotes import astify, capture_value, q, unastify
from .unparser import unparse_with_fallbacks
from .utils import extract_bindings


def _mcpyrate_metatools_attr(attr):
    """Create an AST that, when compiled and run, looks up `mcpyrate.metatools.attr`."""
    return _mcpyrate_attr(f"metatools.{attr}")

# --------------------------------------------------------------------------------

def runtime_expand1(bindings, filename, tree):
    """Macro-expand an AST value `tree` at run time, once. Run-time part of `expand1r`.

    `bindings` and `filename` are as in `mcpyrate.core.BaseMacroExpander`.

    Convenient for experimenting with quoted code in the REPL.
    """
    expander = MacroExpander(bindings, filename)
    return expander.visit_once(tree).body  # Done(body=...) -> ...


def runtime_expand(bindings, filename, tree):
    """Macro-expand an AST value `tree` at run time, until no macros remain. Run-time part of `expandr`.

    `bindings` and `filename` are as in `mcpyrate.core.BaseMacroExpander`.

    Convenient for experimenting with quoted code in the REPL.
    """
    expander = MacroExpander(bindings, filename)
    return expander.visit_recursively(tree)

# --------------------------------------------------------------------------------

@namemacro
def macro_bindings(tree, *, syntax, expander, **kw):  # tree argument is unused
    """[syntax, name] Capture the macro expander's macro bindings.

    This macro snapshots the macro expander's current macro bindings at macro
    expansion time (when the invocation of `macro_bindings` is reached), and
    at run time, evaluates to that snapshot.

    The snapshot is a `dict` that contains the macro bindings. It is in the
    format used for instantiating a `mcpyrate.expander.MacroExpander`.

    The snapshot is retained across process boundaries (function references
    are pickled), so bytecode caching will work as expected.
    """
    if syntax != "name":
        raise SyntaxError("`macro_bindings` is a name macro only")
    # This is exactly the kind of thing the hygienic capture system was
    # designed to do.
    keys = list(astify(k) for k in expander.bindings.keys())
    values = list(capture_value(v, k) for k, v in expander.bindings.items())
    return ast.Dict(keys=keys, values=values)


def fill_location(tree, *, syntax, invocation, **kw):
    """[syntax, expr] Fill missing source location info, recursively.

    The source location is copied from the invocation of `fill_location` itself
    at macro expansion time. The filling itself is delayed *until run time*.

    This is useful to set a source location for a run-time AST value, such as a
    quoted tree; especially if you intend to macro-expand it at run time, so that
    the traceback for any macro expansion error will sensibly identify the use site
    in your code.

    Usage::

        quoted = fill_location[q[...]]

    or::

        with q as quoted:
            ...
        quoted = fill_location[quoted]

    Using this macro, you don't need to manually determine `lineno` and `col_offset`
    to be used as the fill values. If you wish to use custom values, don't use
    this macro; use the function `mcpyrate.astfixers.fix_locations` instead.
    Here's the pattern::

        fake_lineno = 9999
        fake_col_offset = 9999
        reference_node = ast.Constant(value=None, lineno=fake_lineno, col_offset=fake_col_offset)
        fix_locations(tree, reference_node, mode="reference")
    """
    if syntax != "expr":
        raise SyntaxError("`fill_location` is an expr macro only")
    if not (hasattr(invocation, "lineno") and hasattr(invocation, "col_offset")):
        raise SyntaxError("`fill_location` invocation itself is missing source location info.")
    fake_lineno = invocation.lineno
    fake_col_offset = invocation.col_offset
    reference_node = ast.Constant(value="source location dummy")  # We want this as a run-time AST value.
    # By design, an astified run-time AST value does not carry a source location, because typically,
    # it's used by `q`, and the quoted code will be ultimately spliced in to a different source file.
    # (It will be spliced in to the use site of the macro that uses `q`, which is usually different
    # from the file where the implementation of that macro - the use site of `q` - resides.)
    #
    # So we modify the `Call` node, to pass in our captured source location info at run time.
    #
    # (If this looks confusing, `step_expansion` the output at the use site; the "dump" mode may help.
    #  It may also be useful to set `fake_lineno` and `fake_col_offset` to 9999 here, to see more clearly
    #  where exactly those values end up in the output AST.)
    astified_reference_node = astify(reference_node)
    astified_reference_node.keywords.extend([ast.keyword("lineno", astify(fake_lineno)),
                                             ast.keyword("col_offset", astify(fake_col_offset))])
    return ast.Call(_mcpyrate_metatools_attr("fix_locations"),
                    [tree,
                     astified_reference_node],
                    [ast.keyword("mode", astify("reference"))])


# --------------------------------------------------------------------------------

def expand1sq(tree, *, syntax, **kw):
    """[syntax, expr/block] quote-then-expand-once.

    Quasiquote `tree`, then expand one layer of macros in it. Return the result
    quasiquoted.

    Because the expansion runs at macro expansion time, unquoted values are not
    available. If you need to expand also in those, see `expand1rq`.

    `expand1sq[...]` is shorthand for `expand1s[q[...]]`.

    `with expand1sq as quoted` has the corresponding effect on a block.
    but does not factor into `q` and `expand1s`, because the quote is
    applied first, but with the expander outside of it.

    If your tree is quasiquoted, use `expands1` instead.
    """
    if syntax not in ("expr", "block"):
        raise SyntaxError("`expand1sq` is an expr and block macro only")
    tree = q(tree, syntax=syntax, **kw)
    kw = dict(kw)
    if "optional_vars" in kw:  # the asname was meant for `q`, `expand1s` doesn't take it.
        kw["optional_vars"] = None
    return expand1s(tree, syntax=syntax, **kw)


def expandsq(tree, *, syntax, **kw):
    """[syntax, expr/block] quote-then-expand.

    Quasiquote `tree`, then expand it until no macros remain. Return the result
    quasiquoted.

    Because the expansion runs at macro expansion time, unquoted values are not
    available. If you need to expand also in those, see `expandrq`.

    `expandsq[...]` is shorthand for `expands[q[...]]`.

    `with expandsq as quoted` has the corresponding effect on a block.
    but does not factor into `q` and `expands`, because the quote is
    applied first, with the expander outside of it.

    If your tree is quasiquoted, use `expands` instead.

    This operator should produce results closest to those of `macropy`'s `q`.
    """
    if syntax not in ("expr", "block"):
        raise SyntaxError("`expandsq` is an expr and block macro only")
    tree = q(tree, syntax=syntax, **kw)
    kw = dict(kw)
    if "optional_vars" in kw:
        kw["optional_vars"] = None
    return expands(tree, syntax=syntax, **kw)


def expand1s(tree, *, syntax, expander, **kw):
    """[syntax, expr/block] expand one layer of macros in quasiquoted `tree`.

    The result remains in quasiquoted form.

    Like calling `expander.visit_once(tree)`, but for a quasiquoted `tree`,
    already at macro expansion time (of the use site of `expand1s`).

    Because the expansion runs at macro expansion time, unquoted values are not
    available. If you need to expand also in those, see `expand1r`.

    `tree` must be an "astified" AST; i.e. output from, or an invocation of,
    `q`, `expand1sq`, `expandsq`, `expand1s`, or `expands`. Passing any other
    AST as `tree` raises `TypeError`.

    If your `tree` is not quasiquoted, use `expand1sq` instead.
    """
    if syntax not in ("expr", "block"):
        raise SyntaxError("`expand1s` is an expr and block macro only")
    if syntax == "block" and kw['optional_vars'] is not None:
        raise SyntaxError("`expand1s` (block mode) does not take an asname")
    # We first invert the quasiquote operation, then use the garden variety
    # `expander` on the result, and then re-quote the expanded AST.
    #
    # The first `visit_once` makes any quote invocations inside this macro invocation expand first.
    # If the input `tree` is an already expanded `q`, it will do nothing, because any macro invocations
    # are then in a quoted form, which don't look like macro invocations to the expander.
    # If the input `tree` is a `Done`, it will likewise do nothing.
    tree = expander.visit_once(tree)  # -> Done(body=...)
    tree = expander.visit_once(unastify(tree.body))  # On wrong kind of input, `unastify` will `TypeError` for us.
    # The final piece of the magic, why this works in the expander's recursive mode,
    # without wrapping the result with `Done`, is that after `q` has finished, the output
    # will be a **quoted** AST, so macro invocations in it don't look like macro invocations.
    # Hence upon looping on the output, the expander finds no more macros.
    return q(tree.body, syntax=syntax, expander=expander, **kw)


def expands(tree, *, syntax, expander, **kw):
    """[syntax, expr/block] expand quasiquoted `tree` until no macros remain.

    The result remains in quasiquoted form.

    Like calling `expander.visit_recursively(tree)`, but for a quasiquoted `tree`,
    already at macro expansion time (of the use site of `expands`).

    Because the expansion runs at macro expansion time, unquoted values are not
    available. If you need to expand also in those, see `expandr`.

    `tree` must be an "astified" AST; i.e. output from, or an invocation of,
    `q`, `expand1sq`, `expandsq`, `expand1s`, or `expands`. Passing any other
    AST as `tree` raises `TypeError`.

    If your `tree` is not quasiquoted, use `expandsq` instead.
    """
    if syntax not in ("expr", "block"):
        raise SyntaxError("`expands` is an expr and block macro only")
    if syntax == "block" and kw['optional_vars'] is not None:
        raise SyntaxError("`expands` (block mode) does not take an asname")
    tree = expander.visit_once(tree)  # make the quotes inside this invocation expand first; -> Done(body=...)
    # Always use recursive mode, because `expand[...]` may appear inside
    # another macro invocation that uses `visit_once` (which sets the expander
    # mode to non-recursive for the dynamic extent of the `visit_once`).
    tree = expander.visit_recursively(unastify(tree.body))  # On wrong kind of input, `unastify` will `TypeError` for us.
    return q(tree, syntax=syntax, expander=expander, **kw)

# --------------------------------------------------------------------------------

def expand1rq(tree, *, syntax, **kw):
    """[syntax, expr/block] quote-then-expand-once-at-runtime.

    Quasiquote `tree`, then set it up to have one layer of macros expanded
    at run time. At run time, return the resulting AST.

    Convenient for interactive experimentation in the REPL.

    Because the expansion runs at run time (of the use site of `expand1rq`),
    unquoted values have been spliced in by the time the expansion is performed.

    Macro bindings are captured from the use site at macro expansion time.

    `expand1rq[...]` is shorthand for `expand1r[q[...]]`.

    `with expand1rq as quoted` has the corresponding effect on a block, but
    does not factor into `q` and `expand1r`, because the quote is to be applied
    first, but with the expander outside of it. Also, block mode `q` generates
    an `ast.Assign`. The call to the expander is spliced in around its RHS.

    If your tree is quasiquoted, use `expand1r` instead.
    """
    if syntax not in ("expr", "block"):
        raise SyntaxError("`expand1rq` is an expr and block macro only")
    tree = q(tree, syntax=syntax, **kw)
    if syntax == "expr":
        return expand1r(tree, syntax=syntax, **kw)
    else:
        assert syntax == "block"
        assert type(tree) is ast.Assign
        kw = dict(kw)
        kw["optional_vars"] = None  # the asname was meant for `q`, `expand1r` doesn't take it.
        tree.value = expand1r(tree.value, syntax=syntax, **kw)
        return tree


def expandrq(tree, *, syntax, **kw):
    """[syntax, expr/block] quote-then-expand-at-runtime.

    Quasiquote `tree`, then set it up to have it expanded, at run time,
    until no macros remain. At run time, return the resulting AST.

    Convenient for interactive experimentation in the REPL.

    Because the expansion runs at run time (of the use site of `expandrq`),
    unquoted values have been spliced in by the time the expansion is performed.

    Macro bindings are captured from the use site at macro expansion time.

    `expandrq[...]` is shorthand for `expandr[q[...]]`.

    `with expandrq as quoted` has the corresponding effect on a block, but
    does not factor into `q` and `expandr`, because the quote is to be applied
    first, but with the expander outside of it. Also, block mode `q` generates
    an `ast.Assign`. The call to the expander is spliced in around its RHS.

    If your tree is already quasiquoted, use `expandr` instead.

    The results from this operator resemble those from `macropy`'s `q`,
    except macro expansion is applied inside any unquoted AST snippets, too.
    """
    if syntax not in ("expr", "block"):
        raise SyntaxError("`expandrq` is an expr and block macro only")
    tree = q(tree, syntax=syntax, **kw)
    if syntax == "expr":
        return expandr(tree, syntax=syntax, **kw)
    else:
        assert syntax == "block"
        assert type(tree) is ast.Assign
        kw = dict(kw)
        kw["optional_vars"] = None
        tree.value = expandr(tree.value, syntax=syntax, **kw)
        return tree


def expand1r(tree, *, syntax, expander, **kw):
    """[syntax, expr/block] Expand macros at run time, once.

    Convenient for interactive experimentation on quoted code in the REPL.

    Because the expansion runs at run time (of the use site of `expand1r`),
    unquoted values have been spliced in by the time the expansion is performed.

    Macro bindings are captured from the use site at macro expansion time.

    If you want to quote some code to produce `tree` and then immediately expand it,
    use `expand1rq` instead.
    """
    if syntax == "block" and kw["optional_vars"] is not None:
        raise SyntaxError("`expand1r` (block mode) does not take an asname")
    return _expandr_impl(tree, syntax, expander, macroname="expand1r")


def expandr(tree, *, syntax, expander, **kw):
    """[syntax, expr/block] Expand macros at run time, until no macros remain.

    Convenient for interactive experimentation on quoted code in the REPL.

    Because the expansion runs at run time (of the use site of `expandr`),
    unquoted values have been spliced in by the time the expansion is performed.

    Macro bindings are captured from the use site at macro expansion time.

    If you want to quote some code to produce `tree` and then immediately expand it,
    use `expandrq` instead.
    """
    if syntax == "block" and kw["optional_vars"] is not None:
        raise SyntaxError("`expandr` (block mode) does not take an asname")
    return _expandr_impl(tree, syntax, expander, macroname="expandr")


def _expandr_impl(tree, syntax, expander, macroname: str):
    if syntax not in ("expr", "block"):
        raise SyntaxError(f"`{macroname}` is an expr and block macro only")

    if macroname == "expandr":
        runtime_operator = "runtime_expand"
    elif macroname == "expand1r":
        runtime_operator = "runtime_expand1"
    else:
        raise ValueError(f"Unknown macroname '{macroname}'; valid: 'expandr', 'expand1r'")

    # Pass args by name to improve human-readability of the expanded output.
    #
    # We must keep the macro names as-is (because that's how they'll appear
    # inside the run-time `tree` AST value). So we capture the macro functions
    # as regular run-time values (from *our* run time). As a bonus, this also
    # avoids polluting the global bindings table.
    return ast.Call(_mcpyrate_metatools_attr(runtime_operator),
                    [],
                    [ast.keyword("bindings", macro_bindings(None, syntax="name", expander=expander)),
                     ast.keyword("filename", astify(expander.filename)),
                     ast.keyword("tree", tree)])

# --------------------------------------------------------------------------------

@parametricmacro
def stepr(tree, *, args, syntax, expander, **kw):
    """[syntax, expr] Like `mcpyrate.debug.step_expansion`, but at run time.

    This macro shows the steps `expandr` takes for a run-time AST value,
    by using `step_expansion` with macro bindings captured from the use site
    as in `expandr`.

    Macro arguments are passed to `step_expansion`. For example, to use the
    `"dump"` mode, `stepr["dump"][tree]`.

    The run-time return value is the same as `expandr[tree]`.

    There's no separate `steprq`; create your quoted `tree` first, then pass
    `tree` in to this macro.
    """
    if syntax != "expr":
        raise SyntaxError("`stepr` is an expr macro only")

    # Note the `macro_bindings` macro is called now, whereas everything else is delayed until run time.
    expander_node = ast.Call(_mcpyrate_metatools_attr("MacroExpander"),
                             [],
                             [ast.keyword("bindings", macro_bindings(None, syntax="name", expander=expander)),
                              ast.keyword("filename", astify(expander.filename))])
    return ast.Call(_mcpyrate_metatools_attr("step_expansion"),
                    [tree],
                    [ast.keyword("args", astify(args)),
                     ast.keyword("syntax", astify(syntax)),
                     ast.keyword("expander", expander_node)])

# --------------------------------------------------------------------------------

@parametricmacro
def expand_first(tree, *, args, syntax, expander, **kw):
    """[syntax, block] Force given macros to expand before other macros.

    Usage::

        with expand_first[macro0, ...]:
            ...

    Each argument can be either a bare macro name, e.g. `macro0`, or a
    hygienically unquoted macro, e.g. `q[h[macro0]]`.

    As an example, consider::

        with your_block_macro:
            macro0[expr]

    In this case, if `your_block_macro` expands outside-in, it will transform the
    `expr` inside the `macro0[expr] before `macro0` even sees the AST. If the test
    fails or errors, the error message will contain the expanded version of `expr`,
    not the original one. Now, if we change the example to::

        with expand_first[macro0]:
            with your_block_macro:
                macro0[expr]

    In this case, `expand_first` arranges things so that `macro0[expr]` expands first
    (even if `your_block_macro` expands outside-in), so it will see the original,
    unexpanded AST.

    This does imply that `your_block_macro` will then receive the expanded form of
    `macro0[expr]` as input, but that's macros for you.

    There is no particular ordering in which the given set of macros expands;
    they are handled by one expander with bindings registered for all of them.
    (So the expansion order is determined by the order their use sites are
     encountered; the ordering of the names in the argument list does not matter.)
    """
    if syntax != "block":
        raise SyntaxError("expand_first is a block macro only")  # pragma: no cover
    if syntax == "block" and kw['optional_vars'] is not None:
        raise SyntaxError("expand_first does not take an as-part")  # pragma: no cover
    if not args:
        raise SyntaxError("expected a comma-separated list of `macroname` or `q[h[macroname]]` in `with expand_first[macro0, ...]:`; no macro arguments were given")

    # Expand macros in `args` to handle `q[h[somemacro]]`.
    #
    # We must use the full `bindings`, not only those of the quasiquote operators
    # (see `mcpyrate.quotes._expand_quasiquotes`), so that the expander recognizes
    # which hygienic captures are macros.
    args = MacroExpander(expander.bindings, filename=expander.filename).visit(args)

    # In the arguments, we should now have `Name` nodes only.
    invalid_args = [node for node in args if type(node) is not ast.Name]
    if invalid_args:
        invalid_args_str = ", ".join(unparse_with_fallbacks(node, color=True, debug=True)
                                     for node in invalid_args)
        raise SyntaxError(f"expected a comma-separated list of `macroname` or `q[h[macroname]]` in `with expand_first[macro0, ...]:`; invalid args: {invalid_args_str}")

    # Furthermore, all the specified names must be bound as macros in the current expander.
    invalid_args = [name_node for name_node in args if name_node.id not in expander.bindings]
    if invalid_args:
        invalid_args_str = ", ".join(unparse_with_fallbacks(node, color=True, debug=True)
                                     for node in invalid_args)
        raise SyntaxError(f"all macro names in `with expand_first[macro0, ...]:` must be bound in the current expander; the following are not: {invalid_args_str}")

    # All ok. First map the names to macro functions:
    macros = [expander.bindings[name_node.id] for name_node in args]

    # Then map the macro functions to *all* their names in `expander`:
    macro_bindings = extract_bindings(expander.bindings, *macros)
    return MacroExpander(macro_bindings, filename=expander.filename).visit(tree)
