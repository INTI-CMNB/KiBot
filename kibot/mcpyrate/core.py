# -*- coding: utf-8; -*-
"""Expander core; essentially, how to apply a macro invocation."""

__all__ = ["MacroExpansionError", "MacroExpanderMarker", "Done",
           "BaseMacroExpander", "global_postprocess",
           "add_postprocessor", "remove_postprocessor"]

from ast import AST, NodeTransformer
from collections import ChainMap
from contextlib import contextmanager
from copy import deepcopy
from typing import Any, Callable, Dict, List

from .astfixers import fix_ctx, fix_locations
from .markers import ASTMarker, delete_markers
from .utils import flatten, format_location

# Global macro bindings shared across all expanders in the current process.
# This is used by `mcpyrate.quotes` for hygienically captured macro functions.
#
# TODO: In reality, a macro function is not just any callable, but it takes certain
# (especially named) arguments, and its return type is `Union[AST, List[AST], None]`,
# but as of 3.1.0, we skim over this detail.
global_bindings: Dict[str, Callable[..., Any]] = {}

# User function hook for `global_postprocess`.
global_postprocessors: List[Callable[..., Any]] = []

class MacroExpansionError(Exception):
    """Base class for errors specific to macro expansion.

    For errors detected **at macro expansion time**, we recommend raising:

     - `SyntaxError` with a descriptive message, if there's something wrong
       with how the macro was invoked, or with the AST layout of the `tree`
       (or `args`) it got vs. what it was expecting.

     - `TypeError` or `ValueError` as appropriate, if there is a problem in
       the macro arguments meant for the macro itself. (As opposed to macro
       arguments such as in the `let` demo, where `args` is just another
       place to send in an AST to be transformed.)

     - `MacroExpansionError`, or a custom descendant of it, if something else
       macro-related went wrong.

    Some operations represented by a macro may inject a call to a run-time part
    of that operation itself (e.g. the quasiquote system does this). For errors
    detected **at run time of the use site**:

     - Use whichever exception type you would in regular Python code that
       doesn't use macros. For example, a `TypeError`, `ValueError` or
       `RuntimeError` may be appropriate.
    """

class MacroApplicationError(MacroExpansionError):
    """The expander core caught an exception while applying a macro function.

    The expander uses this type to automatically telescope use site reports
    for nested macro invocations (which occur when a macro opts to expand
    inside-out).

    The `macropython` wrapper also strips most of the traceback when it catches
    an exception of this type. We know that for the internal uses of this type,
    the traceback speaks of things such as `macropython` itself, the importer,
    and the macro expander, and it is typically very long. The linked ("direct
    cause") exceptions contain the actually relevant, client code tracebacks.

    **CAUTION**: This type is for internal use only.
    """

class MacroExpanderMarker(ASTMarker):
    """Base class for AST markers used by the macro expander itself."""

class Done(MacroExpanderMarker):
    """A subtree that is done. Any further visits by the expander will skip it.

    Emitted by `BaseMacroExpander.visit_once`, to protect the once-expanded form
    from further expansion.
    """

# --------------------------------------------------------------------------------

class BaseMacroExpander(NodeTransformer):
    """Expander core. Base class for macro expanders.

    After identifying valid macro syntax, each `visit` method of the actual
    expander should return the result of calling the `expand()` method with
    the proper arguments.

    Constructor parameters:

        bindings: dictionary of macro name/function pairs
        filename: full path to `.py` file being expanded, for error reporting
    """

    def __init__(self, bindings: Dict[str, Callable[..., Any]], filename: str):
        self.local_bindings = bindings
        self.bindings = ChainMap(self.local_bindings, global_bindings)
        self.filename = filename
        self.recursive = True
        self._debughook = None  # see `mcpyrate.debug.step_expansion`

    def visit(self, tree):
        """Expand macros in `tree`, using current setting for recursive mode.

        No-op if no macro bindings, or if `tree` is marked as `Done`.

        Treat `visit(stmt_suite)` as a loop for individual elements.
        No-op if `tree is None`.

        This is the standard visitor method; it continues an ongoing visit.
        """
        if not self.bindings or isinstance(tree, Done):
            return tree
        if tree is None:
            return None
        if isinstance(tree, list):
            new_tree = flatten(self.visit(elt) for elt in tree)
            if new_tree:
                tree[:] = new_tree
                return tree
            return None
        return super().visit(tree)

    def visit_recursively(self, tree):
        """Entry point. Expand macros in `tree`, in recursive mode.

        That is, iterate the expansion process until no macros are left.
        Recursive mode is temporarily enabled even if currently inside the
        dynamic extent of a `visit_once`.

        This starts a new visit. The dynamic extents of visits may be nested.
        """
        with self._recursive_mode(True):
            return self.visit(tree)

    def visit_once(self, tree):
        """Entry point. Expand macros in `tree`, in non-recursive mode.

        That is, make just one pass, regardless of whether there are macros
        remaining in the output. Then mark `tree` as `Done`, so the rest of
        the macro expansion process will leave it alone. Recursive mode is
        temporarily disabled even if currently inside the dynamic extent
        of a `visit_recursively`.

        This starts a new visit. The dynamic extents of visits may be nested.
        """
        with self._recursive_mode(False):
            return Done(self.visit(tree))

    def _recursive_mode(self, isrecursive: bool):
        """Context manager. Change recursive mode, restoring the old mode when the context exits."""
        @contextmanager
        def recursive_mode():
            wasrecursive = self.recursive
            try:
                self.recursive = isrecursive
                yield
            finally:
                self.recursive = wasrecursive
        return recursive_mode()

    def debughook(self, hook: Callable[..., None]):
        """Context manager. Temporarily set a debug hook, restoring the old one when the context exits.

        The debug hook, if one is installed, is called whenever a macro expands.

        The hook receives the following arguments, passed positionally in this order:
            invocationsubtreeid: int, the `id()` of the *original* macro invocation subtree
                                 before anything was done to it.
            invocationtree:      AST, (a deepcopy of) the macro invocation subtree before expansion.
            expandedtree:        AST, the replacement subtree after expanding once. It's the actual live copy.
            macroname:           str, name of the macro that was applied, as it appears in this expander's
                                 bindings.
            macrofunction:       callable, the macro function that was applied.
        """
        @contextmanager
        def debughook_context():
            oldhook = self._debughook
            try:
                self._debughook = hook
                yield
            finally:
                self._debughook = oldhook
        return debughook_context()

    def expand(self, syntax, target, macroname: str, tree, sourcecode, kw=None):
        """Expand a macro invocation.

        This is a hook for actual macro expanders. Macro libraries typically
        don't need to care about this; you'll want one of the `visit` methods
        instead.

        Transform the `target` node, replacing it with the expansion result
        of applying `macroname` on `tree`. Then postprocess locally, by
        `_visit_expansion`.

        `syntax` is the type of macro invocation detected by the actual macro
        expander, such as `expr` or `block`. What invocation types exist and
        what values of `syntax` represent them are defined by the actual macro
        expander. The value of `syntax` and its type can be anything; we don't
        even look at it, but just pass it on.

        `sourcecode` is a source code dump (or unparsed backconversion from AST)
        for error messages. It is a parameter, because the actual expander may
        edit the `target` node (e.g. to pop a block macro) before we get control.

        When calling the macro function, we pass the following named arguments:

          - `syntax`:     Our `syntax` argument, as-is.
          - `expander`:   The expander instance.
          - `invocation`: The `target` AST node as-is, for introspection if you
                          need to see not only the destructured `tree` and `args`,
                          but the macro invocation itself, without any processing.

                          Very rarely needed; if you need it, you'll know.

                          **CAUTION**: Not a copy, or at most a shallow copy.

                          **CAUTION**: The caller, i.e. the concrete expander's
                                       visit method that corresponds to the macro
                                       invocation `syntax` being processed,
                                       is responsible for providing a complete,
                                       unmodified `invocation`.

                                       So for example, if your concrete expander
                                       needs to pop a block macro, be sure to stash
                                       an appropriately prepared copy of the invocation
                                       (so that it looks like the original one)
                                       before you edit the original. This is used for
                                       debug purposes, so preserving the appearance
                                       of the original invocation is important.

        To send additional named arguments from the actual expander to the
        macro function, place them in a dictionary and pass that dictionary
        as `kw`.
        """
        loc = format_location(self.filename, target, sourcecode)  # macro use site

        kw = kw or {}
        kw.update({"syntax": syntax,
                   "expander": self,
                   "invocation": target})

        try:
            # Resolve macro binding.
            macro = self.isbound(macroname)
            if not macro:  # pragma: no cover
                raise MacroApplicationError(f"{loc}\n""in {syntax} macro invocation for '{macroname}': the name '{macroname}' is not bound to a macro.")

            # Expand the macro.
            expansion = self._apply_macro(macro, tree, kw, macroname, target)

            # Convert possible iterable result to `list`, then typecheck macro output.
            try:
                if expansion is not None and not isinstance(expansion, AST):
                    expansion = list(expansion)

                if isinstance(expansion, AST) or expansion is None:
                    pass  # ok
                elif isinstance(expansion, list):
                    if not all(isinstance(elt, AST) for elt in expansion):
                        raise TypeError("Expected all elements of list returned by macro function to be ASTs")
                else:
                    raise TypeError("Unexpected return type from macro function")
            except Exception:
                reason = f"in {syntax} macro invocation for '{macroname}': expected macro to return AST node, iterable of AST nodes, or None; got {type(expansion)} with value {repr(expansion)} (after iterable to list conversion)"
                msg = f"{loc}\n{reason}"
                err = MacroApplicationError(msg)
                err.__suppress_context__ = True
                raise err

        # If something went wrong, generate a standardized macro use site report.
        except Exception as err:
            msg = f"{loc}\n""in {syntax} macro invocation for '{macroname}'"
            if isinstance(err, MacroApplicationError) and err.__cause__:
                # Telescope nested use site reports, by keeping the original
                # traceback and `__cause__`, but combining the messages.
                #
                # When macro invocations are nested, the `expand` call
                # that is processing the innermost macro raises first.
                # So when the next outer one catches the exception,
                # it should add its own message to the beginning,
                # to make the report read in an outside-in order,
                # similarly to a Python traceback.
                oldmsg = err.args[0]
                oldmsg_lines = oldmsg.split("\n")
                hint = "An exception occurred during macro expansion.\n\nMacro use site (most recent macro application last):"
                hint_lines = hint.split("\n")
                hint_length_in_lines = len(hint_lines)
                if oldmsg_lines[0] == hint_lines[0]:
                    oldmsg = "\n".join(oldmsg_lines[hint_length_in_lines:])
                msg = f"{hint}\n{msg}\n{oldmsg}"
                raise MacroApplicationError(msg).with_traceback(err.__traceback__) from err.__cause__
            else:
                # Not nested; tack on a `MacroApplicationError` with
                # use site info to whatever exception we originally got.
                #
                # Use site report telescoping uses the fact that this
                # is the only raise-from for a `MacroApplicationError`.
                # So if it has a `__cause__`, it came from here.
                raise MacroApplicationError(msg) from err

        return self._visit_expansion(expansion, target)

    def _apply_macro(self, macro, tree, kw, macroname: str, target):
        """Execute `macro` on `tree`, with the dictionary `kw` unpacked into macro's named arguments.

        `macro` is the macro function.

        `tree` is the AST to apply the macro to. This is what the macro gets as its `tree` argument.

        `kw` is a dictionary-like, unpacked into the macro's named arguments.

        `macroname` is the name (str) the macro function `macro` is bound as in this expander.

        `target` is the whole macro invocation AST. A deepcopy is passed to the debug hook (if installed).
        """
        # There's no guarantee whether `macro` edits the AST in-place or produces a new tree,
        # so to produce reliable debug information, we should take the old `id` and a deep copy
        # of the macro invocation.
        if self._debughook:
            oldid = id(target)
            oldtree = deepcopy(target)  # including the macro invocation itself

        newtree = macro(tree, **kw)

        if self._debughook:
            self._debughook(oldid, oldtree, newtree, macroname, macro)
        return newtree

    def _visit_expansion(self, expansion, target):
        """Perform local postprocessing.

        Add in missing source location info and `ctx`.

        Then, if in recursive mode, recurse into (`visit`) the once-expanded
        macro output. That will cause the actual expander to `expand` again
        if it detects any more macro invocations.
        """
        if expansion is not None:
            expansion = fix_locations(expansion, target, mode="reference")
            expansion = fix_ctx(expansion, copy_seen_nodes=False)
            if self.recursive:
                expansion = self.visit(expansion)

        return expansion

    def isbound(self, name: str, *, global_only=False):
        """Return the macro function the string `name` is bound to, or `False`."""
        bindings = self.bindings if not global_only else global_bindings
        if name in bindings:
            return bindings[name]
        return False


# Final postprocessing for the top-level walk can't be done at the end of the
# entry points `visit_once` and `visit_recursively`, because it is valid for a
# macro to call those for a subtree.
def global_postprocess(tree):
    """Perform global postprocessing for the top-level expansion.

    Delete any AST markers emitted by the macro expander that it uses to talk
    with itself during expansion.

    Call this after macro expansion is otherwise done, before sending `tree`
    to Python's `compile`.
    """
    tree = delete_markers(tree, cls=MacroExpanderMarker)

    # A name macro, appearing as an assignment target, gets the wrong ctx,
    # because when expanding the name macro, the expander sees only the Name
    # node, and thus puts an `ast.Load` there as the ctx.
    tree = fix_ctx(tree, copy_seen_nodes=True)

    # Run the user hooks, if any.
    for custom_postprocessor in global_postprocessors:
        tree = custom_postprocessor(tree)

    return tree

def add_postprocessor(function):
    """Add a custom postprocessor for the top-level expansion.

    `function` must accept `AST` and `list` of `AST`, and return
    the same type.

    Custom postprocessors are automatically called by `global_postprocess`
    (which is called just after macro expansion for a module ends), in the
    order they were registered by calling `add_postprocessor`.

    This e.g. allows a macro library to use its own `ASTMarker` subclasses
    for internal communication between macros, and delete (only) its own
    markers when done.

    Put something like this somewhere in your library initialization code
    (preferably somewhere it's easy to discover for someone reading your
    code, such as in a package `__init__.py`):

        from functools import partial

        import mcpyrate.core
        from mcpyrate.markers import delete_markers

        _delete_my_markers = partial(delete_markers,
                                     cls=MyCustomMarkerBase)
        mcpyrate.core.add_postprocessor(_delete_my_markers)
    """
    if function not in global_postprocessors:
        global_postprocessors.append(function)

def remove_postprocessor(function):
    """Remove a previously added custom postprocessor.

    The `function` is the callable object that was registered as a
    postprocessor using `add_postprocessor`.
    """
    if function in global_postprocessors:
        global_postprocessors.remove(function)
