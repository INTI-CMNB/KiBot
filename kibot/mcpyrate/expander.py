# -*- coding: utf-8; -*-
"""Find and expand macros.

This layer provides the actual macro expander, defining:

 - Syntax for establishing macro bindings::
       from ... import macros, ...

 - Macro invocation types:
   - expr:      `macroname[...]`, `macroname[arg0, ...][...]`
   - block:     `with macroname:`, `with macroname as result:`,
                `with macroname[arg0, ...]:`, `with macroname[arg0, ...] as result:`
   - decorator: `@macroname`, `@macroname[arg0, ...]`
   - name:      `macroname`
"""

# We use bracket syntax for sending macro arguments, because parentheses evoke
# the idea of full function-call syntax. This includes keyword arguments, and
# the distinction between parameter slots (which are always named) and how the
# actual arguments provided in a call are bound to those slots (whether by
# position or by name; and don't forget *args and **kwargs, both at the
# receiving and sending end).
#
# Nowadays it's possible to easily support all this properly via `inspect.signature`
# and `inspect.Signature.bind`. But to get a call signature to bind to, the
# macro function's own signature won't do - that's for when the function is
# called by the macro expander, not for sending macro arguments (which form
# a separate namespace).
#
# So we would need a reference callable to `@parametricmacro`, not to be
# called, but only to have its call signature extracted. In practice, it would
# be a `lambda ...: None`, with the confusing `lambda` and `None` mandatory,
# when the only interesting part is in the `...`, the parameter declarations.
#
# This could then be used to establish a *second* call signature for the
# parametric macro function, to receive the macro arguments in, say, a
# dictionary always named `args` (binding parameter names to values provided
# in the macro call; cf. our current list `args`, which just lists the values).
# Confused yet? See commit 10691ce for a sketch.
#
# The system is much simpler to explain if we just use brackets, and have
# positional args only.
#
# Even this choice of syntax unfortunately leads to an ambiguity as to what
# `macro[...][...]` and even just `macro[...]` mean, but perhaps it's the
# lesser evil. This is one reason why we require parametric macros to be
# explicitly declared - avoid that ambiguity when not needed.

__all__ = ["namemacro", "isnamemacro",
           "parametricmacro", "isparametricmacro",
           "MacroExpander", "MacroCollector",
           "expand_macros", "find_macros"]

import sys
from ast import (AST, Assign, Call, Starred, Constant, Import, Lambda, Name,
                 NodeVisitor, Store, Subscript, Tuple, alias, arguments,
                 copy_location, iter_fields)
from copy import copy
from warnings import warn_explicit

from .core import BaseMacroExpander, Done, global_postprocess
from .coreutils import get_macros, ismacroimport
from .unparser import unparse_with_fallbacks
from .utils import format_location, format_macrofunction


def namemacro(function):
    """Decorator. Declare a macro function as an identifier macro.

    Identifier macros are a rarely needed feature. Hence, the expander invokes
    as identifier macros only macros that are declared as such.

    This (or `@parametricmacro`, if used too) must be the outermost decorator.
    """
    function._isnamemacro = True
    return function

def isnamemacro(function):
    """Return whether the macro function `function` has been declared as an identifier macro."""
    return hasattr(function, "_isnamemacro")

def parametricmacro(function):
    """Decorator. Declare a macro function as taking macro arguments.

    Macro arguments are a rarely needed feature. Hence, the expander interprets
    macro argument syntax only for macros that are declared as parametric.

    This (or `@namemacro`, if used too) must be the outermost decorator.
    """
    function._isparametricmacro = True
    return function

def isparametricmacro(function):
    """Return whether the macro function `function` has been declared as taking macro arguments."""
    return hasattr(function, "_isparametricmacro")

# --------------------------------------------------------------------------------

def destructure_candidate(tree, *, filename, _validate_call_syntax=True):
    """Destructure a macro call candidate AST, `macroname` or `macroname[arg0, ...]`."""
    if type(tree) is Name:
        return tree.id, []
    elif type(tree) is Subscript and type(tree.value) is Name:
        if sys.version_info >= (3, 9, 0):  # Python 3.9+: no ast.Index wrapper
            macroargs = tree.slice
        else:
            macroargs = tree.slice.value

        if type(macroargs) is Tuple:  # [a0, a1, ...]
            macroargs = macroargs.elts
        else:  # anything that doesn't have at least one comma at the top level
            macroargs = [macroargs]
        return tree.value.id, macroargs
    # Up to Python 3.8, decorators cannot be subscripted. This is a problem for
    # decorator macros that would like to have macro arguments.
    #
    # To work around this, we allow passing macro arguments also using parentheses
    # (like in `macropy`). Note macro arguments must still be passed positionally!
    #
    # For uniformity, we limit to a subset of the function call syntax that
    # remains valid if you replace the parentheses with brackets in Python 3.9.
    elif type(tree) is Call and type(tree.func) is Name and not tree.keywords:
        # `MacroExpander._detect_macro_items` needs to perform a preliminary check
        # without full validation when it is trying to detect which `with` items
        # and decorators are in fact macro invocations.
        if _validate_call_syntax:
            if not tree.args:  # reject empty args
                approx_sourcecode = unparse_with_fallbacks(tree, debug=True, color=True)
                loc = format_location(filename, tree, approx_sourcecode)
                raise SyntaxError(f"{loc}\nmust provide at least one argument when passing macro arguments")
            if any(type(arg) is Starred for arg in tree.args):  # reject starred items
                approx_sourcecode = unparse_with_fallbacks(tree, debug=True, color=True)
                loc = format_location(filename, tree, approx_sourcecode)
                raise SyntaxError(f"{loc}\nunpacking (splatting) not supported in macro argument position")
        return tree.func.id, tree.args
    return None, None  # not a macro invocation


class MacroExpander(BaseMacroExpander):
    """The actual macro expander."""

    def ismacrocall(self, macroname: str, macroargs, syntax):
        """Shorthand to check `destructure_candidate` output.

        Return whether that output is a macro call to a macro (of invocation
        type `syntax`) bound in this expander or globally.
        """
        if not (macroname and self.isbound(macroname)):
            return False
        if syntax == 'name':
            return isnamemacro(self.isbound(macroname))
        return not macroargs or isparametricmacro(self.isbound(macroname))

    def visit_Subscript(self, subscript):
        """Detect an expression (expr) macro invocation.

        Detected syntax::

            macroname[...]
            macroname[arg0, ...][...]  # allowed if @parametricmacro

        Replace the `Subscript` node with the AST returned by the macro.
        The core controls whether to expand again in the result.
        """
        # We must silently ignore when a non-parametric expr macro is invoked with macro args,
        # because things like `(some_expr_macro[tree])[subscript_expression]` are valid. This
        # is actually exploited by `h`, as in `q[h[target_macro][tree_for_target_macro]]`.
        candidate = subscript.value
        macroname, macroargs = destructure_candidate(candidate, filename=self.filename,
                                                     _validate_call_syntax=False)
        if self.ismacrocall(macroname, macroargs, "expr"):
            # Now we know it's a macro invocation, so we can validate the parenthesis syntax to pass arguments.
            macroname, macroargs = destructure_candidate(candidate, filename=self.filename)
            kw = {"args": macroargs}
            if sys.version_info >= (3, 9, 0):  # Python 3.9+: no ast.Index wrapper
                tree = subscript.slice
            else:
                tree = subscript.slice.value
            sourcecode = unparse_with_fallbacks(subscript, debug=True, color=True, expander=self)
            new_tree = self.expand("expr", subscript, macroname, tree, sourcecode=sourcecode, kw=kw)
            if new_tree is None:
                # Expression slots in the AST cannot be empty, but we can make
                # something that evaluates to `None` at run-time, and get
                # correct coverage while at it.
                new_tree = _make_coverage_dummy_expr(subscript)
        else:
            new_tree = self.generic_visit(subscript)
        return new_tree

    def visit_With(self, withstmt):
        """Detect a block macro invocation.

        Detected syntax::

            with macroname:
                ...
            with macroname as result:
                ...
            with macroname[arg0, ...]:  # allowed if @parametricmacro
                ...
            with macroname[arg0, ...] as result:  # allowed if @parametricmacro
                ...

        Replace the `With` node with the AST returned by the macro.

        The `result` part is sent to the macro as `kw["optional_vars"]`; it's a
        `Name`, `Tuple` or `List` node. What to do with it is up to the macro;
        the typical meaning is to assign something to the name(s).
            https://greentreesnakes.readthedocs.io/en/latest/nodes.html#withitem

        Invoking several block macros in the same `with` is shorthand for nesting::

            with macro1, macro2:
                ...

        is equivalent with::

            with macro1:
                with macro2:  # part of `tree` for `macro1`, in either notation
                    ...

        We pop the first block macro in the withitem list and expand it. The
        core controls whether to expand again in the result. A block macro may
        do anything it wants to its input tree. Any remaining block macro
        invocations are attached to the `With` node, so if that is removed,
        they will be skipped.

        **NOTE**: At least up to v3.3.0, if there are three or more macro
        invocations in the same `with` statement::

            with macro1, macro2, macro3:
                ...

        this is equivalent with::

            with macro1:
                with macro2, macro3:
                    ...

        and **not** equivalent with::

            with macro1:
                with macro2:
                    with macro3:
                        ...

        which may be important if `macro1` needs to scan for invocations of
        `macro2` and `macro3` to work together with them.
        """
        macros, others = self._detect_macro_items(withstmt.items, "block")
        if not macros:
            return self.generic_visit(withstmt)
        with_item = macros[0]
        candidate = with_item.context_expr
        macroname, macroargs = destructure_candidate(candidate, filename=self.filename)

        # let the source code and `invocation` see also the withitem we pop away
        sourcecode = unparse_with_fallbacks(withstmt, debug=True, color=True, expander=self)
        original_withstmt = copy(withstmt)
        original_withstmt.items = copy(withstmt.items)

        withstmt.items.remove(with_item)
        kw = {"args": macroargs}
        kw.update({"optional_vars": with_item.optional_vars})
        tree = withstmt.body if not withstmt.items else [withstmt]
        new_tree = self.expand("block", original_withstmt, macroname, tree, sourcecode=sourcecode, kw=kw)
        new_tree = _insert_coverage_dummy_stmt(new_tree, withstmt, macroname, self.filename)
        return new_tree

    def visit_ClassDef(self, classdef):
        return self._visit_Decorated(classdef)

    def visit_FunctionDef(self, functiondef):
        return self._visit_Decorated(functiondef)

    def _visit_Decorated(self, decorated):
        """Detect a decorator macro invocation.

        Detected syntax::

            @macroname
            def f():
                ...
            @macroname[arg0, ...]  # allowed if @parametricmacro
            def f():
                ...
            @macroname
            class C():
                ...
            @macroname[arg0, ...]  # allowed if @parametricmacro
            class C:
                ...

        Replace the whole decorated node with the AST returned by the macro.

        We pop the innermost decorator macro and expand it. The core controls
        whether to expand again in the result. A decorator macro may edit the
        decorator list; it may also emit additional nodes (by returning a
        `list`), or even delete the decorated node or replace it altogether.
        Any remaining decorator macro invocations are attached to the original
        decorated node, so if that is removed, they will be skipped.

        The body is expanded after the whole decorator list has been processed.
        """
        macros, others = self._detect_macro_items(decorated.decorator_list, "decorator")
        if not macros:
            return self.generic_visit(decorated)
        innermost_macro = macros[-1]
        macroname, macroargs = destructure_candidate(innermost_macro, filename=self.filename)

        # let the source code and `invocation` see also the decorator we pop away
        sourcecode = unparse_with_fallbacks(decorated, debug=True, color=True, expander=self)
        original_decorated = copy(decorated)
        original_decorated.decorator_list = copy(decorated.decorator_list)

        decorated.decorator_list.remove(innermost_macro)
        kw = {"args": macroargs}
        new_tree = self.expand("decorator", original_decorated, macroname, decorated, sourcecode=sourcecode, kw=kw)
        new_tree = _insert_coverage_dummy_stmt(new_tree, innermost_macro, macroname, self.filename)
        return new_tree

    def _detect_macro_items(self, items, syntax):
        """Split a list `items` into `(macros, others)`.

        `syntax`: str, "block" or "decorator"
            "block": `items` is a `With.items`
            "decorator": `items` is a `decorator_list`
        """
        assert syntax in ("block", "decorator")
        context = "in `with` header" if syntax == "block" else "as decorator"

        macros, others = [], []
        for item in items:
            if syntax == "block":
                candidate = item.context_expr
            else:
                candidate = item
            macroname, macroargs = destructure_candidate(candidate, filename=self.filename,
                                                         _validate_call_syntax=False)

            # warn about likely mistake
            if (macroname and self.isbound(macroname) and
                    (macroargs and not isparametricmacro(self.bindings[macroname]))):
                msg = f"expr macro `{macroname}` invoked {context}; `{format_macrofunction(self.bindings[macroname])}` maybe missing `@parametricmacro` declaration?"
                lineno = item.lineno if hasattr(item, "lineno") else 0
                warn_explicit(msg, SyntaxWarning, filename=self.filename, lineno=lineno)

            if self.ismacrocall(macroname, macroargs, syntax):
                macros.append(item)
            else:
                others.append(item)

        return macros, others

    def visit_Name(self, name: str):
        """Detect an identifier (name) macro invocation.

        Detected syntax::

            macroname

        The `Name` node itself is the input tree for the macro.
        Replace the `Name` node with the AST returned by the macro.

        Otherwise the core controls whether to expand again in the
        result, but we stop if the macro returns the original `tree`,
        telling the expander to use the name as a regular run-time name.
        """
        # We must silently ignore when a non-name macro is invoked as a name macro,
        # because things like `q[h[some_expr_macro][...]]` are valid.
        if self.ismacrocall(name.id, None, "name"):
            macroname = name.id
            def ismodified(tree) -> bool:
                return not (type(tree) is Name and tree.id == macroname)
            with self._recursive_mode(False):
                kw = {"args": None}
                sourcecode = unparse_with_fallbacks(name, debug=True, color=True, expander=self)
                new_tree = self.expand("name", name, macroname, name, sourcecode=sourcecode, kw=kw)
            if new_tree is None:
                # Expression slots in the AST cannot be empty, but we can make
                # something that evaluates to `None` at run-time, and get
                # correct coverage while at it.
                new_tree = _make_coverage_dummy_expr(name)
            else:
                if not ismodified(new_tree):
                    new_tree = Done(new_tree)
                elif self.recursive:  # and modified
                    new_tree = self.visit(new_tree)
        else:
            new_tree = name
        return new_tree


class MacroCollector(NodeVisitor):
    """Scan `tree` for macro invocations, with respect to given `expander`.

    Collect a list of `(macroname, syntax)`. Usage::

        mc = MacroCollector(expander)
        mc.visit(tree)
        print(mc.collected)
        # ...do something to tree...
        mc.clear()
        mc.visit(tree)
        print(mc.collected)

    Sister class of the actual `MacroExpander`, mirroring its syntax detection.
    """
    def __init__(self, expander):
        """`expander`: a `MacroExpander` instance to query macro bindings from.

        `filename`: full path to `.py` file being expanded, for error reporting.
                    Only used for errors during `destructure_candidate`.
        """
        self.expander = expander
        self.clear()

    def clear(self):
        self._seen = set()
        self.collected = []

    def visit(self, tree):
        """Scan `tree` for macro invocations.

        No-op if `self.expander` has no macro bindings, or if `tree` is marked
        as `Done`.

        Treat `visit(stmt_suite)` as a loop for individual elements.
        No-op if `tree is None`.
        """
        if not self.expander.bindings or isinstance(tree, Done):
            return
        if tree is None:
            return
        if isinstance(tree, list):
            for elt in tree:
                self.visit(elt)
            return
        return super().visit(tree)

    def visit_Subscript(self, subscript):
        candidate = subscript.value
        macroname, macroargs = destructure_candidate(candidate, filename=self.expander.filename)
        if self.expander.ismacrocall(macroname, macroargs, "expr"):
            key = (macroname, "expr")
            if key not in self._seen:
                self.collected.append(key)
                self._seen.add(key)
            self.visit(macroargs)
            # Don't `self.generic_visit(tree)`; that'll incorrectly detect
            # the name part as an identifier macro. Recurse only in the expr.
            if sys.version_info >= (3, 9, 0):  # Python 3.9+: no ast.Index wrapper
                self.visit(subscript.slice)
            else:
                self.visit(subscript.slice.value)
        else:
            self.generic_visit(subscript)

    def visit_With(self, withstmt):
        macros, others = self.expander._detect_macro_items(withstmt.items, "block")
        if macros:
            for with_item in macros:
                candidate = with_item.context_expr
                macroname, macroargs = destructure_candidate(candidate, filename=self.expander.filename)
                key = (macroname, "block")
                if key not in self._seen:
                    self.collected.append(key)
                    self._seen.add(key)
                self.visit(macroargs)
            for with_item in others:
                self.visit(with_item)
            self.visit(withstmt.body)
        else:
            self.generic_visit(withstmt)

    def visit_ClassDef(self, classdef):
        self._visit_Decorated(classdef)

    def visit_FunctionDef(self, functiondef):
        self._visit_Decorated(functiondef)

    def _visit_Decorated(self, decorated):
        macros, others = self.expander._detect_macro_items(decorated.decorator_list, "decorator")
        if macros:
            for macro in macros:
                macroname, macroargs = destructure_candidate(macro, filename=self.expander.filename)
                key = (macroname, "decorator")
                if key not in self._seen:
                    self.collected.append(key)
                    self._seen.add(key)
                self.visit(macroargs)
            for decorator in others:
                self.visit(decorator)
            for k, v in iter_fields(decorated):
                if k in ("decorator_list", "name"):
                    continue
                self.visit(v)
        else:
            self.generic_visit(decorated)

    def visit_Name(self, name: str):
        macroname = name.id
        if self.expander.ismacrocall(macroname, None, "name"):
            key = (macroname, "name")
            if key not in self._seen:
                self.collected.append(key)
                self._seen.add(key)


def _insert_coverage_dummy_stmt(tree, macronode, macroname: str, filename):
    """Force statement `macronode` to be reported as covered by coverage tools.

    A dummy node will be injected to `tree`. The `tree` must appear in a
    statement position, so `ast.NodeTransformer.visit` may return a list of nodes.

    `macronode` is the macro invocation node to copy source location info from.
    `macroname` and `filename` are included in the dummy node, to ease debugging.
    """
    # `macronode` itself might be macro-generated. In that case don't bother.
    if not hasattr(macronode, "lineno") and not hasattr(macronode, "col_offset"):
        return tree
    if tree is None:
        tree = []
    elif isinstance(tree, AST):
        tree = [tree]
    # The dummy node must actually run to get coverage, so an `ast.Pass` won't do.
    # It must *do* something, or CPython optimizes it away, so an `ast.Expr` won't do.
    # We must set location info manually, because we run after `expand`.
    v = copy_location(Constant(value=f"{filename}:{macronode.lineno} invoked macro '{macroname}'"),
                      macronode)
    t = copy_location(Name(id="_mcpyrate_coverage", ctx=Store()),
                      macronode)
    dummy = copy_location(Assign(targets=[t], value=v), macronode)
    tree.insert(0, Done(dummy))  # mark as Done so any expansions further out won't mess this up.
    return tree


def _make_coverage_dummy_expr(macronode):
    """Force expression `macronode` to be reported as covered by coverage tools.

    This facilitates "deleting" expression nodes by `return None` from a macro.
    Since an expression slot in the AST cannot be empty, we inject a dummy node
    that evaluates to `None`.

    `macronode` is the macro invocation node to copy source location info from.
    """
    # TODO: inject the macro name for human-readability
    # We inject a lambda and an immediate call to it, because a constant `None`,
    # if it appears alone in an `ast.Expr`, is optimized away by CPython.
    # We must set location info manually, because we run after `expand`.
    non = copy_location(Constant(value=None), macronode)
    lam = copy_location(Lambda(args=arguments(posonlyargs=[], args=[], vararg=None,
                                              kwonlyargs=[], kw_defaults=[], kwarg=None,
                                              defaults=[]),
                               body=non),
                        macronode)
    call = copy_location(Call(func=lam, args=[], keywords=[]), macronode)
    return Done(call)


# --------------------------------------------------------------------------------

def expand_macros(tree, bindings, *, filename):
    """Expand `tree` with macro bindings `bindings`. Top-level entry point.

    Note that while this is a top-level entry point for the **macro** expander,
    expanding macros is only a part of the full import algorithm. See the function
    `mcpyrate.compiler.expand` for the 30,000ft (9,144m) view.

    Primarily meant to be called with `tree` the AST of a module that uses
    macros, but works with any `tree` (even inside a macro, if you need an
    independent second instance of the expander with different bindings).

    `bindings`: dict of macro name/function pairs.

    `filename`: str, full path to the `.py` being macroexpanded, for error reporting.
                In interactive use, can be an arbitrary label.
    """
    expansion = MacroExpander(bindings, filename).visit(tree)
    expansion = global_postprocess(expansion)
    return expansion


def find_macros(tree, *, filename, reload=False, self_module=None, transform=True):
    """Establish macro bindings from `tree`. Top-level entry point.

    Note that while this is a top-level entry point for the **macro** expander,
    expanding macros is only a part of the full import algorithm. See the function
    `mcpyrate.compiler.expand` for the 30,000ft (9,144m) view.

    Collect bindings from each macro-import statement (`from ... import macros, ...`)
    at the top level of `tree.body`.

    As a side effect, import the macro definition modules. (We must do this in order
    to load the macro function definitions, so that we can bind to them.)

    Primarily meant to be called with `tree` the AST of a module that
    uses macros, but works with any `tree` that has a `body` attribute,
    where that `body` is a `list` of statement AST nodes.

    `filename`: str, full path to the `.py` being macroexpanded, for resolving
                relative macro-imports and for error reporting. In interactive
                use, can be an arbitrary label.

    `reload`:   If enabled, refresh modules, causing different uses of the same macros
                to point to different function objects. Enable only if implementing a REPL.

    `self_module`: str, optional, absolute dotted module name of the module being
                   expanded. Used for supporting `from __self__ import macros, ...`
                   for multi-phase compilation (a.k.a. staging).

    `transform`: If enabled, transform each macro-import into `import ...`,
                 where `...` is the absolute module name the macros are being
                 imported from. Usually this is the Right Thing to do, to honor
                 the unhygienic expose API guarantee.

                 The notable exception is multi-phase compilation, which needs
                 to produce two versions of the code: one to run immediately
                 (to produce the temporary module for the current phase), and
                 another to be lifted into the next phase. The code for the
                 next phase needs to have the original macro-imports so we can
                 establish the same bindings again in that phase; but in the code
                 to run immediately, macro-imports should be transformed away so
                 that the temporary module works as expected.

    Return value is a dict `{macroname: function, ...}` with all collected bindings.
    """
    stmts_to_delete = []
    bindings = {}
    for index, statement in enumerate(tree.body):
        if ismacroimport(statement):
            module_absname, more_bindings = get_macros(statement, filename=filename, reload=reload, self_module=self_module)
            bindings.update(more_bindings)
            if transform:
                if self_module and statement.module == "__self__":
                    # Remove self-macro-imports after establishing bindings.
                    # No need to import a module at run time; the importer lifts all
                    # the higher-phase code also into the code of the current phase.
                    #
                    # `statement` usually has location info, in which case we can replace the
                    # self-macro-import with a coverage dummy node. But it might not, if we are
                    # dealing with a dynamically generated module that's being multi-phase compiled.
                    # In that case it's best to just delete the statement now that it's done its job.
                    dummies = _insert_coverage_dummy_stmt(None, statement, "<self-macro-import>", filename)
                    if dummies is not None:  # had location info?
                        tree.body[index] = dummies[0]
                    else:
                        stmts_to_delete.append(index)
                else:
                    # Remove all names to prevent macros being used as regular run-time objects.
                    # Always use an absolute import, for the unhygienic expose API guarantee.
                    thealias = copy_location(alias(name=module_absname, asname=None),
                                             statement)
                    tree.body[index] = copy_location(Import(names=[thealias]),
                                                     statement)
    for index in reversed(stmts_to_delete):
        tree.body.pop(index)
    return bindings
