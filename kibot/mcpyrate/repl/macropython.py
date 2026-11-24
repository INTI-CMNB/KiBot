#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Universal bootstrapper for macro-enabled Python programs powered by mcpyrate."""

# TODO: Currently tested in CPython 3.6, and PyPy3 7.3.0 (Python 3.6). Test in 3.7+.

import argparse
import atexit
import os
import pathlib
import sys
from importlib import import_module
from importlib.util import module_from_spec, resolve_name

from .. import __version__ as __mcpyrate_version__
from .. import activate  # noqa: F401
from ..core import MacroApplicationError
from ..coreutils import relativize
from ..pycachecleaner import deletepycachedirs, getpycachedirs

__version__ = "3.1.0"

_config_dir = "~/.config/mcpyrate"
_macropython_module = None  # sys.modules doesn't always seem to keep it, so stash it locally too.

# --------------------------------------------------------------------------------

def import_module_as_main(name: str, script_mode):
    """Import a module, pretending it's __main__.

    We support only new-style loaders that provide `exec_module`; old-style
    loaders that provide `load_module` and `create_module` are not supported.

    Upon success, replaces `sys.modules["__main__"]` with the module that
    was imported. Upon failure, propagates any exception raised.

    This is a customized approximation of the standard import semantics, based on:

        https://docs.python.org/3/library/importlib.html#approximating-importlib-import-module
        https://docs.python.org/3/reference/import.html#loading
        https://docs.python.org/3/reference/import.html#import-related-module-attributes
        https://docs.python.org/3/reference/import.html#module-path
        https://docs.python.org/3/reference/import.html#special-considerations-for-main
    """
    absolute_name = resolve_name(name, package=None)

    # If already loaded, normally we should return the module from `sys.modules`,
    # but `sys.modules["__main__"]` is for now this bootstrapper, not the user __main__.
    #
    # Note __main__ and somemod are distinct modules, even when the same file,
    # because __main__ triggers `if __name__ == '__main__'` checks, but somemod doesn't.
    #
    # try:
    #     return sys.modules[absolute_name]
    # except KeyError:
    #     pass

    path = None
    if '.' in absolute_name:
        if script_mode:
            raise ValueError("In script mode, please add the containing directory to `sys.path` and then top-level import the final component of the name.")
        # Import the module's parent package normally to initialize parent packages.
        # Get the appropriate `path` for `find_spec` to find subpackages and modules.
        parent_name, _, child_name = absolute_name.rpartition('.')
        parent_module = import_module(parent_name)
        path = parent_module.__spec__.submodule_search_locations

    for finder in sys.meta_path:
        if not hasattr(finder, "find_spec"):  # pkg_resources.extern.VendorImporter has no find_spec
            continue
        # https://docs.python.org/3/library/importlib.html#importlib.abc.MetaPathFinder.find_spec
        spec = finder.find_spec(absolute_name, path)
        if spec is not None:
            break
    else:
        msg = f"No module named {absolute_name}"
        raise ModuleNotFoundError(msg, name=absolute_name)

    spec.name = "__main__"
    if spec.loader:
        spec.loader.name = "__main__"

    module = module_from_spec(spec)
    try_mainpy = False
    if script_mode:  # e.g. "macropython somepackage/__init__.py"
        module.__package__ = ""
    elif path:  # e.g. "macropython -m somepackage.module"
        module.__package__ = parent_name
    elif spec.origin.endswith("__init__.py"):  # e.g. "macropython -m somepackage"
        module.__package__ = absolute_name
        try_mainpy = True

    if spec.origin == "namespace":
        # https://docs.python.org/3/reference/import.html#__path__
        module.__path__ = spec.submodule_search_locations

    if try_mainpy:
        # e.g. "import somepackage" in the above case; it's not __main__, so import it normally.
        assert not script_mode
        parent_module = import_module(absolute_name)
    elif spec.loader:
        sys.modules["__main__"] = module  # replace this bootstrapper with the new __main__
        try:
            spec.loader.exec_module(module)
        except Exception as err:
            sys.modules["__main__"] = _macropython_module
            if isinstance(err, MacroApplicationError):
                # To avoid noise, discard most of the traceback of the chained
                # macro-expansion errors emitted by the expander core. The
                # linked (`__cause__`) exceptions have the actual tracebacks.
                #
                # Keep just the last entry, which should state that this
                # exception came from `expand` in `core.py`.
                tb = err.__traceback__
                while tb.tb_next:
                    tb = tb.tb_next
                raise err.with_traceback(tb)
            raise
        # # __main__ has no parent module so we don't need to do this.
        # if path is not None:
        #     setattr(parent_module, child_name, module)
    else:  # namespace packages have loader=None
        try_mainpy = True

    # __init__.py (if any) has run; run __main__.py, like `python -m somepackage` does.
    if try_mainpy:
        has_mainpy = True
        try:
            # __main__.py doesn't need to have its name set to "__main__", so import it normally.
            import_module(f"{absolute_name}.__main__")
        except ImportError as e:
            if "No module named" in e.msg:
                has_mainpy = False
            else:
                raise
        if not has_mainpy:
            raise ImportError(f"No module named {absolute_name}.__main__; '{absolute_name}' is a package and cannot be directly executed")

    return module

def main():
    """Handle command-line arguments and run the specified main program."""
    parser = argparse.ArgumentParser(description="""Run a Python program or an interactive interpreter with mcpyrate enabled.""",
                                     formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument('-v', '--version', action='version', version=('%(prog)s ' + __version__ + ' (mcpyrate ' + __mcpyrate_version__ + ')'))
    parser.add_argument(dest='filename', nargs='?', default=None, type=str, metavar='file',
                        help='script to run')
    parser.add_argument('-m', '--module', dest='module', default=None, type=str, metavar='mod',
                        help='run library module as a script (like python -m mod)')
    parser.add_argument('-i', '--interactive', dest='interactive', action="store_true", default=False,
                        help='interactive mode (macro-enabled Python interpreter). '
                             'If -i is given, <filename> and -m <mod> are ignored.')
    parser.add_argument('-p', '--pylab', dest='pylab', action="store_true", default=False,
                        help='For use together with "-i". Automatically "import numpy as np", '
                             '"import matplotlib.pyplot as plt", and enable mpl\'s interactive '
                             'mode (somewhat like IPython\'s pylab mode).')
    parser.add_argument('-c', '--clean', dest='path_to_clean', default=None, type=str, metavar='dir',
                        help='Delete Python bytecode (`.pyc`) caches inside given directory, recursively, '
                             'and then exit. This removes the `__pycache__` directories, too. '
                             'The purpose is to facilitate testing `mcpyrate` and programs that use it, '
                             'because the expander only runs when the `.pyc` cache for the module being '
                             'imported is out of date or does not exist. For any given module, once the '
                             'expander is done, Python\'s import system automatically writes the `.pyc` '
                             'cache for that module.')
    parser.add_argument("-n", "--dry-run", dest="dry_run", action="store_true", default=False,
                        help='For use together with "-c". Just scan for and print the .pyc cache '
                             'directory paths, don\'t actually clean them.')
    opts = parser.parse_args()

    if opts.path_to_clean:
        # If an error occurs during cleaning, we just let it produce a standard stack trace.
        if not opts.dry_run:
            deletepycachedirs(opts.path_to_clean)
        else:
            for x in getpycachedirs(opts.path_to_clean):
                print(x)
        sys.exit(0)  # only reached if cleaning (or dry run) successful

    if opts.interactive:
        import readline  # noqa: F401, side effect: enable GNU readline in input()
        import rlcompleter  # noqa: F401, side effects: readline tab completion

        from .console import MacroConsole
        repl_locals = {}
        if opts.pylab:  # like IPython's pylab mode, but we keep things in separate namespaces.
            import matplotlib.pyplot
            import numpy
            repl_locals["np"] = numpy
            repl_locals["plt"] = matplotlib.pyplot
            matplotlib.pyplot.ion()
        readline.set_completer(rlcompleter.Completer(namespace=repl_locals).complete)
        readline.parse_and_bind("tab: complete")  # PyPy ignores this, but not needed there.

        config_dir = pathlib.Path(_config_dir).expanduser().resolve()
        try:
            readline.read_history_file(config_dir / "macropython_history")
        except FileNotFoundError:
            pass

        def save_history():
            config_dir.mkdir(parents=True, exist_ok=True)
            readline.set_history_length(1000)
            readline.write_history_file(config_dir / "macropython_history")
        atexit.register(save_history)

        # Add CWD to import path like the builtin interactive console does.
        if sys.path[0] != "":
            sys.path.insert(0, "")
        m = MacroConsole(locals=repl_locals)
        return m.interact()

    if not opts.filename and not opts.module:
        parser.print_help()
        sys.exit(0)
    if opts.filename and opts.module:
        raise ValueError("Please specify just one main program to run (either filename.py or -m module, not both).")

    # Import the module, pretending its __name__ is "__main__".
    #
    # We must import so that macros get expanded, so we can't use
    # runpy.run_module here (which just execs without importing).
    #
    # As for sys.path, we're not interested in the directory the `macropython`
    # script itself lives in. To imitate how Python itself behaves:
    #
    #   - If run as `macropython -m something`, then `sys.path[0]`
    #     should be set to the cwd.
    #   - If run as `macropython some/path/to/script.py`, then `sys.path[0]`
    #     should be set to the directory containing `script.py`.
    #
    if opts.module:
        # Python 3.7 and later resolve the cwd at interpreter startup time, and use that.
        # Python 3.6 and earlier use the empty string, which dynamically resolves to
        # whatever is the current cwd whenever a module is imported.
        #     https://bugs.python.org/issue33053
        if sys.version_info >= (3, 7, 0):
            cwd = str(pathlib.Path.cwd().expanduser().resolve())
            if sys.path[0] != cwd:
                sys.path.insert(0, cwd)
        else:
            if sys.path[0] != "":
                sys.path.insert(0, "")

        # https://www.python.org/dev/peps/pep-0582/
        if sys.version_info >= (3, 8, 0):
            local_pypackages_dir = pathlib.Path.cwd().expanduser().resolve() / "__pypackages__"
            if local_pypackages_dir.is_dir():
                # TODO: figure out correct insert index (spec: "after cwd, just before site packages")
                sys.path.insert(1, str(local_pypackages_dir))

        import_module_as_main(opts.module, script_mode=False)

    else:  # no module, so use opts.filename
        fullpath = pathlib.Path(opts.filename).expanduser().resolve()
        if not fullpath.is_file():
            raise FileNotFoundError(f"Can't open file '{opts.filename}'")

        containing_directory = str(fullpath.parent)
        if sys.path[0] != containing_directory:
            sys.path.insert(0, containing_directory)

        # https://www.python.org/dev/peps/pep-0582/
        if sys.version_info >= (3, 8, 0):
            local_pypackages_dir = fullpath.parent / "__pypackages__"
            if local_pypackages_dir.is_dir():
                # TODO: figure out correct insert index (spec: "after cwd, just before site packages")
                sys.path.insert(1, str(local_pypackages_dir))

        # This approach finds the standard loader even for macro-enabled scripts.
        # TODO: For mcpyrate, that could be ok, since we monkey-patch just that.
        # TODO: But maybe better to leave the option to replace the whole loader later.
        # spec = spec_from_file_location("__main__", str(fullpath))
        # if not spec:
        #     raise ImportError(f"Not a Python module: '{opts.filename}'"
        # module = module_from_spec(spec)
        # TODO: if we use this approach, we should first initialize parent packages.
        # sys.modules[module.__name__] = module
        # spec.loader.exec_module(module)

        root_path, relative_path = relativize(opts.filename)
        module_name = relative_path.replace(os.path.sep, '.')
        if module_name.endswith(".__init__.py"):
            module_name = module_name[:-12]
        elif module_name.endswith(".py"):
            module_name = module_name[:-3]

        import_module_as_main(module_name, script_mode=True)

if __name__ == "__main__":
    _macropython_module = sys.modules["__macropython__"] = sys.modules["__main__"]
    main()
