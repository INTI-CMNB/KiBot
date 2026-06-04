# -*- coding: utf-8; -*-
"""Macro debugging utilities."""

__all__ = ["step_expansion", "StepExpansion", "step_phases",
           "show_bindings", "format_bindings",
           "SourceLocationInfoValidator"]

import ast
import functools
import io
import sys
import textwrap

from .astdumper import dump
from .colorizer import setcolor, colorize, ColorScheme
from .dialects import StepExpansion  # re-export for discoverability, it's a debug feature
from .expander import MacroCollector, namemacro, parametricmacro
from .multiphase import step_phases  # re-export for discoverability, it's a debug feature
from .unparser import unparse_with_fallbacks
from .utils import NestingLevelTracker, format_macrofunction, format_context
from .walkers import ASTVisitor


_step_expansion_level = NestingLevelTracker()

@parametricmacro
def step_expansion(tree, *, args, syntax, expander, **kw):
    """[syntax, expr/block] Macroexpand `tree`, showing each step of the expansion.

    Syntax::

        step_expansion[...]
        step_expansion[arg, ...][...]
        with step_expansion:
            ...
        with step_expansion[arg, ...]:
            ...

    This calls `expander.visit_once` in a loop, discarding the `Done` markers,
    and showing the AST at each step, by printing to `sys.stderr`.

    A step is defined as when `expander.visit_once` returns control to the
    expander core. If your macro does `expander.visit(subtree)`, that will
    expand `subtree` by one layer of macros (without adding a `Done` marker)
    before returning control; if it does `expander.visit_recursively(subtree)`,
    then that subtree will be expanded, in a single step, until no macros remain.

    However, the argument `"detailed"` can be used to report all macro expansions
    within each step, including those done by `expander.visit(subtree)`.

    Since this is a debugging utility, the source code is rendered in the debug
    mode of `unparse`, which prints also invisible nodes such as `Module` and
    `Expr` (as well as any AST markers) in a Python-like pseudocode notation.

    The source code is rendered with syntax highlighting suitable for terminal
    output.

    Supported macro arguments (can be given in any order):

      - One of the strings `"unparse"` (default) or `"dump"` sets the renderer mode.

        If `"unparse"`, then at each step, the AST will be shown as source code.
        If `"dump"`, then at each step, the AST will be shown as a raw AST dump.

      - One of the strings `"summary"` (default) or `"detailed"` sets the report
        detail level.

        If `"summary"`, then the whole tree is printed once per step.
        If `"detailed"`, also each macro expansion in each step is reported,
        by printing the relevant subtree before and after expansion.

    This macro steps the expansion at macro expansion time. If you have a
    run-time AST value (such as a quasiquoted tree), and want to step the
    expansion of that at run time, see the `stepr` macro in `mcpyrate.metatools`.
    It supports the same arguments as `step_expansion`.
    """
    if syntax not in ("expr", "block"):
        raise SyntaxError("`step_expansion` is an expr and block macro only")

    supported_args = ("unparse", "dump", "detailed", "summary")
    formatter = functools.partial(unparse_with_fallbacks, debug=True, color=True,
                                  expander=expander)
    print_details = False
    for arg in args:
        if type(arg) is ast.Constant:
            v = arg.value
        else:
            raise TypeError(f"expected str argument, got {repr(arg)} {unparse_with_fallbacks(arg)}")

        if v not in supported_args:
            raise ValueError(f"unknown argument {repr(v)}")

        if v == "dump":
            formatter = functools.partial(dump, include_attributes=True, color=True)
        elif v == "detailed":
            print_details = True

    c, CS = setcolor, ColorScheme

    with _step_expansion_level.changed_by(+1):  # The level is used for nested invocations of `step_expansion`.
        indent = 2 * _step_expansion_level.value
        stars = indent * '*'
        codeindent = indent
        tag = id(tree)

        print(f"{c(CS.HEADING1)}{stars}Tree {c(CS.HEADING2)}0x{tag:x} ({expander.filename}) {c(CS.HEADING1)}before macro expansion:{c()}",
              file=sys.stderr)
        print(textwrap.indent(f"{formatter(tree)}", codeindent * ' '), file=sys.stderr)

        step = 0
        def doit():
            nonlocal step
            nonlocal tree
            mc = MacroCollector(expander)
            mc.visit(tree)
            while mc.collected:
                step += 1
                tree = expander.visit_once(tree)  # -> Done(body=...)
                tree = tree.body
                print(f"{c(CS.HEADING1)}{stars}Tree {c(CS.HEADING2)}0x{tag:x} ({expander.filename}) {c(CS.HEADING1)}after step {step}:{c()}",
                      file=sys.stderr)
                print(textwrap.indent(formatter(tree), codeindent * ' '), file=sys.stderr)
                mc.clear()
                mc.visit(tree)

        if print_details:
            def print_step(invocationsubtreeid, invocationtree, expandedtree, macroname, macrofunction):
                print(f"{c(CS.HEADING1)}{stars}Tree {c(CS.HEADING2)}0x{tag:x} ({expander.filename}) {c(CS.HEADING1)}processing step {step}:",
                      file=sys.stderr)
                print(textwrap.indent(f"{c(CS.HEADING2)}Applying {c(CS.MACRONAME)}{macroname}{c(CS.HEADING2)} at subtree 0x{invocationsubtreeid:x}:{c()}", codeindent * ' '), file=sys.stderr)
                print(textwrap.indent(f"{formatter(invocationtree)}", (codeindent + 2) * ' '), file=sys.stderr)
                print(textwrap.indent(f"{c(CS.HEADING2)}Result:{c()}", codeindent * ' '), file=sys.stderr)
                print(textwrap.indent(f"{formatter(expandedtree)}", (codeindent + 2) * ' '), file=sys.stderr)

            with expander.debughook(print_step):
                doit()
        else:
            doit()

        plural = "s" if step != 1 else ""
        print(f"{c(CS.HEADING1)}{stars}Tree {c(CS.HEADING2)}0x{tag:x} ({expander.filename}) {c(CS.HEADING1)}macro expansion complete after {step} step{plural}.{c()}",
              file=sys.stderr)
    return tree


@namemacro
def show_bindings(tree, *, syntax, expander, **kw):
    """[syntax, name] Show all bindings of the macro expander.

    Syntax::

        show_bindings

    This can appear in any expression position, and at run time evaluates to `None`.
    If you instead want to programmatically examine, at run time, the bindings
    the expander had at macro expansion time, see the `macro_bindings` macro
    in `mcpyrate.metatools`.

    At macro expansion time, when the macro expander reaches the `show_bindings`
    expression, bindings *that are in effect at that point in time* are shown.

    (That disclaimer is important, because hygienically unquoted macros may add
     new bindings as those expressions are reached, and true to the dynamic nature
     of Python, when any macro runs, it is allowed to edit the expander's bindings.)

    For each macro binding, we print to `sys.stderr` the macro name, and the
    fully qualified name of the corresponding macro function.

    Any bindings that have an uuid as part of the name are hygienically
    unquoted macros. Those bindings are global across all modules and
    all expander instances.
    """
    if syntax != "name":
        raise SyntaxError("`show_bindings` is an identifier macro only")
    print(format_bindings(expander, globals_too=False, color=True), file=sys.stderr)
    return None


def format_bindings(expander, *, globals_too=False, color=False):
    """Return a human-readable report of the macro bindings currently seen by `expander`.

    If `globals_too=True`, global bindings (across all expanders) are also included.

    If `color=True`, colorize the output for printing into a terminal.

    If you want to access them programmatically, just access `expander.bindings` directly.
    """
    def maybe_setcolor(*colors):
        if not color:
            return ""
        return setcolor(*colors)
    def maybe_colorize(text, *colors):
        if not color:
            return text
        return colorize(text, *colors)

    c, CS = maybe_setcolor, ColorScheme

    bindings = expander.bindings if globals_too else expander.local_bindings
    with io.StringIO() as output:
        output.write(f"{c(CS.HEADING1)}Macro bindings for {c(CS.SOURCEFILENAME)}{expander.filename}{c(CS.HEADING1)}:{c()}\n")
        if not bindings:
            output.write(maybe_colorize("    <no bindings>\n",
                                        ColorScheme.GREYEDOUT))
        else:
            for k, v in sorted(bindings.items()):
                k = maybe_colorize(k, ColorScheme.MACRONAME)
                output.write(f"    {k}: {format_macrofunction(v)}\n")
        return output.getvalue()


class SourceLocationInfoValidator(ASTVisitor):
    """Collect nodes that are missing `lineno` and/or `col_offset`.

    Usage::

        v = SourceLocationInfoValidator()
        v.visit(tree)
        print(v.collected)

    It's a rather common occurrence when developing macros to have the source
    location info missing somewhere, but when we `compile`, Python won't tell us
    *which* nodes are missing them.

    This can also be used to debug whether the problem is what Python claims it is.
    Python's `compile` is notorious for yelling about a missing source location
    when the actual problem is that is got a bare value in a position where an
    AST node was expected.

    The macro expander *should* fill in missing source location info when it expands
    a macro, so this utility will be needed only rarely.

    After `visit(tree)`, `self.collected` becomes a `list` of items in the format
    `(subtree, sourcecode, missing_field_names)`. Each `sourcecode` is truncated
    if too long.
    """
    def __init__(self, ignore={}, n=5, check_fields=["lineno", "col_offset"]):
        """Constructor.

        Parameters:

            `ignore={tree0, ...}` to ignore given subtrees (such as if you have
            a top-level `Module` node; those don't need source location info).
            Subtrees are detected by their `id`.

            `n`: maximum number of source lines to show for each collected item.

            `check_fields`: which fields are considered mandatory for every node
            in `tree`. Defaults to checking source location info.
        """
        self.ignore = ignore
        self.n = n
        self.check_fields = check_fields
        super().__init__()

    def examine(self, tree):
        if tree not in self.ignore:
            present = [hasattr(tree, x) for x in self.check_fields]
            if not all(present):
                code = format_context(tree, n=self.n)
                self.collect((tree,
                              code,
                              [fieldname for fieldname, p in zip(self.check_fields, present) if not p]))
        self.generic_visit(tree)
