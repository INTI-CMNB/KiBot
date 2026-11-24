# -*- coding: utf-8; -*-
"""Dump an AST into a string, with pythonic indentation.

Based on Alex Leone's `astpp.py`, with changes to indentation logic.
    http://alexleone.blogspot.co.uk/2010/01/python-ast-pretty-printer.html
"""

__all__ = ["dump"]

from ast import AST, iter_fields

from .colorizer import colorize, ColorScheme

NoneType = type(None)

def dump(tree, *, include_attributes=False, multiline=True, color=False):
    """Return a formatted dump of `tree`, as a string.

    `tree` can be an AST node or a statement suite (`list` of AST nodes).

    Attributes such as line numbers and column offsets are not dumped
    by default. If this is wanted, use `include_attributes=True`.

    To use indentation similar to how the code to construct the AST would
    appear as Python source code, use `multiline=True`.

    To put everything on one line, use `multiline=False`.

    If you're printing the result into a terminal, consider `color=True`.

    Similar to `macropy`'s `real_repr`, but with indentation. The method
    `ast.AST.__repr__` itself can't be monkey-patched, because `ast.AST`
    is a built-in/extension type.
    """
    def maybe_colorize(text: str, *colors):
        if not color:
            return text
        return colorize(text, *colors)

    def maybe_colorize_value(value):
        if type(value) in (str, bytes, NoneType, bool, int, float, complex):
            # Pass through an already formatted list-as-a-string from an inner level.
            if isinstance(value, str) and value.startswith("["):
                return value
            return maybe_colorize(str(value), ColorScheme.BAREVALUE)
        return str(value)

    def recurse(tree, previndent=0):
        def separator() -> str:
            if multiline:
                return f",\n{(previndent + moreindent) * ' '}"
            return ", "

        if isinstance(tree, AST):
            moreindent = len(f"{tree.__class__.__name__}(")
            fields = [(k, recurse(v, previndent + moreindent + len(f"{k}="))) for k, v in iter_fields(tree)]
            if include_attributes and tree._attributes:
                fields.extend([(k, recurse(getattr(tree, k, None),
                                           previndent + moreindent + len(f"{k}=")))
                               for k in tree._attributes])
            colorized_fields = [(maybe_colorize(k, ColorScheme.FIELDNAME),
                                 maybe_colorize_value(v))
                                for k, v in fields]
            return "".join([
                maybe_colorize(tree.__class__.__name__, ColorScheme.NODETYPE),
                "(",
                separator().join((f"{k}={v}" for k, v in colorized_fields)),
                ")"])

        elif isinstance(tree, list):
            moreindent = len("[")
            items = [recurse(elt, previndent + moreindent) for elt in tree]
            if items:
                items[0] = "[" + items[0].lstrip()
                items[-1] = items[-1] + "]"
                return separator().join(items)
            return "[]"

        return repr(tree)

    if not isinstance(tree, (AST, list)):
        raise TypeError(f"expected AST, got {tree.__class__.__name__!r}")
    return recurse(tree)
