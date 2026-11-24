# -*- coding: utf-8; -*-
"""Utilities related to writing macro expanders and similar meta-metaprogramming tasks."""

__all__ = ["resolve_package", "relativize", "match_syspath",
           "ismacroimport", "get_macros",
           "isfutureimport", "split_futureimports", "inject_after_futureimports"]

import ast
import importlib
import importlib.util
import os
import pathlib
import sys

from .unparser import unparse_with_fallbacks
from .utils import format_location, getdocstring


def resolve_package(filename):  # TODO: for now, `guess_package`, really. Check the docs again.
    """Resolve absolute Python package name for .py source file `filename`.

    If `filename` is at the top level of the matching entry in `sys.path`, raises `ImportError`.
    If `filename` is not under any directory in `sys.path`, raises `ValueError`.
    """
    containing_directory = pathlib.Path(filename).expanduser().resolve().parent
    root_path, relative_path = relativize(containing_directory)
    if not relative_path:  # at the root_path - not inside a package
        absolute_filename = str(pathlib.Path(filename).expanduser().resolve())
        resolved = f" (resolved to {absolute_filename})" if absolute_filename != str(filename) else ""
        raise ImportError(f"{filename}{resolved} is not in a package, but at the root level of syspath {str(root_path)}")
    package_dotted_name = relative_path.replace(os.path.sep, ".")
    return package_dotted_name


def relativize(filename):
    """Convert `filename` into a relative one under the matching `sys.path`.

    Return value is `(root_path, relative_path)`, where `root_path` is the
    return value of `match_syspath` (a `pathlib.Path`), and `relative_path`
    is a string containing the relative path of `filename` under `root_path`.

    `filename` can be a .py source file or a package directory.
    """
    absolute_filename = str(pathlib.Path(filename).expanduser().resolve())
    root_path = match_syspath(absolute_filename)
    relative_path = absolute_filename[len(str(root_path)):]
    if relative_path.startswith(os.path.sep):
        relative_path = relative_path[len(os.path.sep):]
    return root_path, relative_path


def match_syspath(filename):
    """Return the entry in `sys.path` the `filename` is found under.

    Return value is a `pathlib.Path` for the matching `sys.path` directory,
    resolved to an absolute directory.

    If `filename` is not under any directory in `sys.path`, raises `ValueError`.
    """
    absolute_filename = str(pathlib.Path(filename).expanduser().resolve())
    # Match deeper paths first; for readability, break ties lexicographically.
    # This allows the matching to work also if e.g. both `/home/user/.local/`
    # and `/home/user/.local/lib/python3.8/site-packages/` end up on `sys.path`.
    def sortkey(s):
        return -s.count(os.path.sep), s
    for root_path in sorted(sys.path, key=sortkey):
        root_path = pathlib.Path(root_path).expanduser().resolve()
        if absolute_filename.startswith(str(root_path)):
            return root_path
    resolved = f" (resolved to {absolute_filename})" if absolute_filename != str(filename) else ""
    raise ValueError(f"{filename}{resolved} not under any directory in `sys.path`")

# --------------------------------------------------------------------------------

def ismacroimport(statement, magicname: str='macros') -> bool:
    """Return whether `statement` is a macro-import.

    A macro-import is a statement of the form::

        from ... import macros, ...

    where "macros" is the literal string given as `magicname`.
    """
    if isinstance(statement, ast.ImportFrom):
        firstimport = statement.names[0]
        if firstimport.name == magicname and firstimport.asname is None:
            return True
    return False


def get_macros(macroimport, *, filename, reload=False, allow_asname=True, self_module=None):
    """Get absolute module name, macro names and macro functions from a macro-import.

    A macro-import is a statement of the form::

        from ... import macros, ...

    where `macros` is the magic name that your actual macro expander uses to recognize
    a macro-import (see `ismacroimport`). This function does not care about what the
    actual magic name is, and simply ignores the first name that is imported by the
    import statement.

    As a side effect, import the macro definition module.

    Return value is `module_absname, {macroname0: macrofunction0, ...}`.

    `filename` is the full path to the `.py` being macroexpanded, for resolving
    relative macro-imports and for error reporting. In interactive use, can be
    an arbitrary label.

    Use the `reload` flag only when implementing a REPL, because it'll refresh modules,
    causing different uses of the same macros to point to different function objects.

    Use `allow_asname` to say whether your expander supports renaming macros
    at the use site. Usually it's a good idea to support it; but e.g. renaming a
    dialect makes no sense.

    `self_module` is an optional string, the absolute dotted module name of the
    module being expanded. Used for supporting `from __self__ import macros, ...`
    for multi-phase compilation (a.k.a. staging).

    This function is meant for implementing actual macro expanders.
    """
    package_absname = None
    if macroimport.level and filename.endswith(".py"):
        try:
            package_absname = resolve_package(filename)
        except (ValueError, ImportError) as err:
            raise ImportError(f"while resolving absolute package name of {filename}, which uses relative macro-imports") from err

    if macroimport.module is None:
        # fallbacks may trigger if the macro-import is programmatically generated.
        approx_sourcecode = unparse_with_fallbacks(macroimport, debug=True, color=True)
        loc = format_location(filename, macroimport, approx_sourcecode)
        raise SyntaxError(f"{loc}\nmissing module name in macro-import")

    # macro-import from an earlier phase of a module using `with phase`
    if macroimport.module == "__self__":
        if macroimport.level:
            approx_sourcecode = unparse_with_fallbacks(macroimport, debug=True, color=True)
            loc = format_location(filename, macroimport, approx_sourcecode)
            raise SyntaxError(f"{loc}\nself-macro-imports cannot be relative")
        # When we get here, the module, as compiled up to the previous phase,
        # is already in `sys.modules`, because the importer temporarily places
        # it there. That way we can load macro bindings from it, while the
        # current phase is being compiled.
        #
        # If the highest phase tries to self-macro-import (which is incorrect),
        # a blank dummy module will have been placed in `sys.modules` by Python's
        # import system itself. So this should never trigger a `KeyError`;
        # it'll instead trigger an error when attempting to import a name
        # from that blank module.
        #
        # But just in case that some exotic use case leads to a `KeyError` here,
        # translate that to an error sensible at this level of abstraction.
        module_absname = self_module
        try:
            module = sys.modules[module_absname]
        except KeyError:
            approx_sourcecode = unparse_with_fallbacks(macroimport, debug=True, color=True)
            loc = format_location(filename, macroimport, approx_sourcecode)
            raise ModuleNotFoundError(f"{loc}\nModule {module_absname} not found in `sys.modules`")

    # regular macro-import
    else:
        module_absname = importlib.util.resolve_name("." * macroimport.level + macroimport.module, package_absname)

        try:
            module = importlib.import_module(module_absname)
        except ModuleNotFoundError as err:
            approx_sourcecode = unparse_with_fallbacks(macroimport, debug=True, color=True)
            loc = format_location(filename, macroimport, approx_sourcecode)
            raise ModuleNotFoundError(f"{loc}\nNo module named {module_absname}") from err

        if reload:
            module = importlib.reload(module)

    bindings = {}
    for name in macroimport.names[1:]:  # skip the "macros" in `from ... import macros, ...`
        if not allow_asname and name.asname is not None:
            approx_sourcecode = unparse_with_fallbacks(macroimport, debug=True, color=True)
            loc = format_location(filename, macroimport, approx_sourcecode)
            raise ImportError(f"{loc}\nThis expander (see traceback) does not support as-naming macro-imports.")

        try:
            macro = getattr(module, name.name)
        except AttributeError as err:
            approx_sourcecode = unparse_with_fallbacks(macroimport, debug=True, color=True)
            loc = format_location(filename, macroimport, approx_sourcecode)
            raise ImportError(f"{loc}\ncannot import name '{name.name}' from module {module_absname}") from err

        if not callable(macro):
            approx_sourcecode = unparse_with_fallbacks(macroimport, debug=True, color=True)
            loc = format_location(filename, macroimport, approx_sourcecode)
            raise ImportError(f"{loc}\nname '{name.name}' in module {module_absname} is not a callable object (got {type(macro)} with value {repr(macro)}), so it cannot be imported as a macro.")

        bindings[name.asname or name.name] = macro

    return module_absname, bindings

# --------------------------------------------------------------------------------

def _mcpyrate_attr(dotted_name: str, *, force_import=False):
    """Create an AST that, when compiled and run, looks up an attribute of `mcpyrate`.

    `dotted_name` is an `str`. Examples::

        _mcpyrate_attr("dump")  # -> mcpyrate.dump
        _mcpyrate_attr("quotes.lookup_value")  # -> mcpyrate.quotes.lookup_value

    If `force_import` is `True`, use the builtin `__import__` function to
    first import the `mcpyrate` module whose attribute will be accessed.
    This is useful when the eventual use site might not import any `mcpyrate`
    modules.
    """
    if not isinstance(dotted_name, str):
        raise TypeError(f"dotted_name name must be str; got {type(dotted_name)} with value {repr(dotted_name)}")

    if dotted_name.find(".") != -1:
        submodule_dotted_name, _ = dotted_name.rsplit(".", maxsplit=1)
    else:
        submodule_dotted_name = None

    # Issue #21: `mcpyrate` might not be in scope at the use site. Fortunately,
    # `__import__` is a builtin, so we are guaranteed to always have that available.
    if not force_import:
        mcpyrate_module = ast.Name(id="mcpyrate")
    else:
        globals_call = ast.Call(ast.Name(id="globals"),
                                [],
                                [])

        if submodule_dotted_name:
            modulename_to_import = f"mcpyrate.{submodule_dotted_name}"
        else:
            modulename_to_import = "mcpyrate"

        import_call = ast.Call(ast.Name(id="__import__"),
                               [ast.Constant(value=modulename_to_import),
                                globals_call,  # globals (used for determining context)
                                ast.Constant(value=None),  # locals (unused)
                                ast.Tuple(elts=[]),  # fromlist
                                ast.Constant(value=0)],  # level
                               [])
        # When compiled and run, the import call will evaluate to a reference
        # to the top-level `mcpyrate` module.
        mcpyrate_module = import_call

    value = mcpyrate_module
    for name in dotted_name.split("."):
        value = ast.Attribute(value=value, attr=name)

    return value

# --------------------------------------------------------------------------------

def isfutureimport(tree):
    """Return whether `tree` is a `from __future__ import ...`."""
    return isinstance(tree, ast.ImportFrom) and tree.module == "__future__"

def split_futureimports(body):
    """Split `body` into `__future__` imports and everything else.

    `body`: list of `ast.stmt`, the suite representing a module top level.

    Return value is `[docstring, future_imports, the_rest]`, where each item
    is a list of `ast.stmt` (possibly empty).
    """
    if getdocstring(body):
        docstring, *body = body
        docstring = [docstring]
    else:
        docstring = []

    k = -1  # ensure `k` gets defined even if `body` is empty
    for k, bstmt in enumerate(body):
        if not isfutureimport(bstmt):
            break
    if k >= 0:
        return docstring, body[:k], body[k:]
    return docstring, [], body

def inject_after_futureimports(stmts, body):
    """Inject one or more statements into `body` after its `__future__` imports.

    `stmts`: `ast.stmt` or list of `ast.stmt`, the statement(s) to inject.
    `body`: list of `ast.stmt`, the suite representing a module top level.

    Return value is the list `[docstring] + futureimports + stmts + the_rest`.

    If `body` has no docstring node at its beginning, the docstring part is
    automatically omitted.

    If `body` has no `__future__` imports at the beginning just after the
    optional docstring, the `futureimports` part is automatically omitted.
    """
    if not isinstance(body, list):
        raise TypeError(f"`body` must be a `list`, got {type(body)} with value {repr(body)}")
    if not isinstance(stmts, list):
        if not isinstance(stmts, ast.stmt):
            raise TypeError(f"`stmts` must be `ast.stmt` or a `list` of `ast.stmt`, got {type(stmts)} with value {repr(stmts)}")
        stmts = [stmts]
    docstring, futureimports, body = split_futureimports(body)
    return docstring + futureimports + stmts + body
