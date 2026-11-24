# -*- coding: utf-8; -*-
"""General utilities. Can be useful for writing both macros as well as macro expanders."""
from typing import Optional

__all__ = ["gensym", "scrub_uuid", "flatten", "rename", "extract_bindings", "getdocstring",
           "get_lineno", "format_location", "format_macrofunction", "format_context",
           "NestingLevelTracker"]

import ast
from contextlib import contextmanager
import uuid

from .colorizer import colorize, ColorScheme
from . import markers
from . import unparser
from . import walkers


_previous_gensyms = set()
def gensym(basename: Optional[str]=None):
    """Create a name for a new, unused lexical identifier, and return the name as an `str`.

    We include an uuid in the name to avoid the need for any lexical scanning.

    Can also be used for globally unique string keys, in which case `basename`
    does not need to be a valid identifier.

    Examples::

        gensym()         # --> 'gensym_e010a36f9cd64ad2b14041751ef40a6e'
        gensym("kitty")  # --> 'kitty_65cc5638659d46209af11e1133698462'
        gensym("")       # --> '7cf67f3eb02c4fdaa1a13e7f55bca908' (bare uuid only)
    """
    if basename and not isinstance(basename, str):
        raise TypeError(f"`basename` must be str, got {type(basename)} with value {repr(basename)}")

    if basename is None:
        basename = "gensym_"
    elif len(basename):
        basename = basename + "_"
    # else basename = ""

    def generate() -> str:
        unique = str(uuid.uuid4()).replace("-", "")
        return f"{basename}{unique}"
    sym = generate()
    # The uuid spec does not guarantee no collisions, only a vanishingly small chance.
    while sym in _previous_gensyms:
        sym = generate()  # pragma: no cover
    _previous_gensyms.add(sym)
    return sym


def scrub_uuid(string: str):
    """Scrub any existing `"_uuid"` suffix from `string`."""
    idx = string.rfind("_")
    if idx != -1:
        maybe_uuid = string[(idx + 1):]
        if len(maybe_uuid) == 32:
            try:
                _ = int(maybe_uuid, base=16)
            except ValueError:
                pass
            else:  # yes, it was an uuid
                return string[:idx]
    return string


def flatten(lst, *, recursive: bool=True):
    """Flatten a nested list.

    Useful for splicing in transformations of statement suites.
    """
    out = []
    for elt in lst:
        if isinstance(elt, list):
            sublst = flatten(elt) if recursive else elt
            out.extend(sublst)
        elif elt is not None:
            out.append(elt)
    return out


def rename(oldname: str, newname: str, tree):
    """Rename all occurrences of a name in `tree`.

    We look in all places in the AST that hold name-like things.

    Currently: identifiers (names), attribute names, function and class names,
    function parameter names, arguments passed by name, name and asname in imports,
    and the as-part of an exception handler (binding a name to the exception object).

    Some constructs such as `For` and `With` use `Name` nodes for named things,
    so those are transformed too.

    With this you can do things like::

        from mcpyrate.quotes import macros, q
        from mcpyrate import gensym
        from mcpyrate.utils import rename

        tree = q[lambda _: ...]
        tree = rename("_", gensym(), tree)

    The tree is modified in-place. For convenience, we return `tree`.
    """
    class Renamer(walkers.ASTTransformer):
        def transform(self, tree):
            T = type(tree)
            if T is ast.Name:
                if tree.id == oldname:
                    tree.id = newname
            # Look for "raw string" in GTS for a full list of the following.
            # https://greentreesnakes.readthedocs.io/en/latest/nodes.html
            elif T is ast.Attribute:
                if tree.attr == oldname:
                    tree.attr = newname
            elif T in (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef):
                if tree.name == oldname:
                    tree.name = newname
            elif T is ast.arg:  # function parameter
                if tree.arg == oldname:
                    tree.arg = newname
            elif T is ast.keyword:  # in function call, argument passed by name
                if tree.arg == oldname:
                    tree.arg = newname
            elif T is ast.ImportFrom:
                if tree.module == oldname:
                    tree.module = newname
            elif T is ast.alias:  # in ast.Import, ast.ImportFrom
                if tree.name == oldname:
                    tree.name = newname
                if tree.asname == oldname:
                    tree.asname = newname
            elif T is ast.ExceptHandler:
                if tree.name == oldname:
                    tree.name = newname
            return self.generic_visit(tree)
    return Renamer().visit(tree)


def extract_bindings(bindings, *functions, global_only=False):
    """Scan `bindings` for given macro functions.

    Return all matching bindings as a dictionary of macro name/function pairs,
    which can be used to instantiate a new expander (that recognizes only those
    bindings).

    Note functions, not names. This is convenient as a helper when expanding
    macros inside-out, but only those in a given set, accounting for any renames
    due to as-imports.

    Useful input values for `bindings` include `expander.bindings` (in a macro;
    will see both local and global bindings), `mcpyrate.core.global_bindings`
    (for global bindings only), and the run-time output of the name macro
    `mcpyrate.metatools.macro_bindings`.

    Typical usage::

        bindings = extract_bindings(expander.bindings, mymacro1, mymacro2, mymacro3)
        tree = MacroExpander(bindings, expander.filename).visit(tree)
    """
    functions = set(functions)
    return {name: function for name, function in bindings.items() if function in functions}


def getdocstring(body):
    """Extract docstring from `body` if it has one.

    Only static strings (no f-strings or string arithmetic) are recognized as docstrings.

    `body` must be a `list` of statement AST nodes. (As a special case, if `body is None`,
    we return `None`, allowing the caller to emit some boilerplate checks.)

    Return value is either the docstring (as an `str`), or `None`.
    """
    if not body:
        return None
    if not isinstance(body, list):
        raise TypeError(f"`body` must be a `list`, got {type(body)} with value {repr(body)}")
    if type(body[0]) is ast.Expr and type(body[0].value) is ast.Constant:
        docstring_node = body[0].value  # Expr -> Expr.value
        return docstring_node.value
    return None

# --------------------------------------------------------------------------------

def get_lineno(tree):
    """Extract the source line number from `tree`.

    `tree`: AST node, list of AST nodes, or an AST marker.

    `tree` is searched recursively (depth first) until a `lineno` attribute is found;
    its value is then returned.

    If no `lineno` attribute is found anywhere inside `tree`, the return value is `None`.
    """
    if hasattr(tree, "lineno"):
        return tree.lineno
    elif isinstance(tree, markers.ASTMarker) and hasattr(tree, "body"):  # look inside AST markers
        return get_lineno(tree.body)
    elif isinstance(tree, ast.AST):  # look inside AST nodes
        # Note `iter_fields` ignores attribute fields such as line numbers and column offsets,
        # so we don't recurse into those.
        for fieldname, node in ast.iter_fields(tree):
            lineno = get_lineno(node)
            if lineno:
                return lineno
    elif isinstance(tree, list):  # look inside statement suites
        for node in tree:
            lineno = get_lineno(node)
            if lineno:
                return lineno
    return None


def format_location(filename, tree, sourcecode) -> str:
    """Format a source code location in a standard way, for error messages.

    `filename`: full path to `.py` file.
    `tree`: AST node to get source line number from. (Looks inside automatically if needed.)
    `sourcecode`: source code (typically, to get this, `unparse(tree)`
                  before expanding it), or `None` to omit it.

    Return value is an `str` containing colored text, suitable for terminal output.
    Example outputs for single-line and multiline source code::

        /path/to/hello.py:42: print("hello!")

        /path/to/hello.py:1337:
        if helloing:
            print("hello!")
    """
    if sourcecode:
        sep = " " if "\n" not in sourcecode else "\n"
        source_with_sep = f"{sep}{sourcecode}"
    else:
        source_with_sep = ""

    return f'{colorize(filename, ColorScheme.SOURCEFILENAME)}:{get_lineno(tree)}:{source_with_sep}'


def format_macrofunction(function):
    """Format the fully qualified name of a macro function, for error messages.

    Return value is an `str` with the fully qualified name.
    """
    # Catch broken bindings due to erroneous imports in user code
    # (e.g. accidentally to a module object instead of to a function object)
    if not (hasattr(function, "__module__") and hasattr(function, "__qualname__")):
        return repr(function)
    if not function.__module__:  # Macros defined in the REPL have `__module__=None`.
        return function.__qualname__
    return f"{function.__module__}.{function.__qualname__}"


def format_context(tree, *, n=5):
    """Format up to the first `n` lines of source code of `tree`.

    The source code is produced from `tree` by unparsing.

    Return value is an `str` containing colored text with syntax highlighting,
    suitable for terminal output.
    """
    code_lines = unparser.unparse_with_fallbacks(tree, debug=True, color=True).split("\n")
    code = "\n".join(code_lines[:n])
    if len(code_lines) > n:
        code += "\n" + colorize("...", ColorScheme.GREYEDOUT)
    return code

# --------------------------------------------------------------------------------

class NestingLevelTracker:
    """Track the nesting level in a set of co-operating, related macros.

    Useful for implementing macros that are syntactically only valid inside the
    invocation of another macro (i.e. when the level is `> 0`).

    Note that in order for level tracking to work, the context (outer) macros
    must expand inside-out (i.e. call `expander.visit` explicitly). If they
    expand outside-in (default), the outer macro invocation will already have
    exited when the inner macro invocation gets expanded.
    """
    def __init__(self, start=0):
        """start: int, initial level"""
        self.stack = [start]

    def _get_value(self):
        return self.stack[-1]
    value = property(fget=_get_value, doc="The current level. Read-only. Use `set_to` or `change_by` to change.")

    def set_to(self, value):
        """Context manager. Run a section of code with the level set to `value`.

        Example::

            t = NestingLevelTracker()
            assert t.value == 0
            with t.set_to(42):
                assert t.value == 42
                ...
            assert t.value == 0
        """
        if not isinstance(value, int):
            raise TypeError(f"Expected integer `value`, got {type(value)} with value {repr(value)}")
        if value < 0:
            raise ValueError(f"`value` must be >= 0, got {repr(value)}")
        @contextmanager
        def _set_to():
            self.stack.append(value)
            try:
                yield
            finally:
                self.stack.pop()
                assert self.stack  # postcondition
        return _set_to()

    def changed_by(self, delta):
        """Context manager. Run a section of code with the level incremented by `delta`.

        Example::

            t = NestingLevelTracker()
            assert t.value == 0
            with t.changed_by(+21):
                assert t.value == 21
                with t.changed_by(+21):
                    assert t.value == 42
                    ...
                assert t.value == 21
            assert t.value == 0
        """
        return self.set_to(self.value + delta)
