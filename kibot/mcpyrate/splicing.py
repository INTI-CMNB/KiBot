# -*- coding: utf-8; -*-
"""Utilities for splicing the actual code into a code template."""

__all__ = ["splice_expression", "splice_statements", "splice_dialect"]

import ast
from copy import deepcopy

from .astfixers import fix_locations
from .coreutils import ismacroimport, split_futureimports
from .markers import ASTMarker
from .utils import getdocstring
from .walkers import ASTTransformer


def splice_expression(expr, template, tag="__paste_here__"):
    """Splice `expr` into `template`.

    This is somewhat like `mcpyrate.quotes.a`, but must be called from outside the
    quoted snippet.

    Parameters:

        `expr`: an expression AST node, or an AST marker containing such.
            The expression you would like to splice in.

        `template`: an AST node, or a `list` of AST nodes.
            Template into which to splice `expr`.

            Must contain a paste-here indicator AST node that specifies where
            `expr` is to be spliced in. The node is expected to have the format::

                ast.Name(id=tag)

            Or in plain English, it's a bare identifier.

            The first-found instance (in AST scan order) of the paste-here indicator
            is replaced by `expr`.

            If the paste-here indicator appears multiple times, second and further
            instances are replaced with a `copy.deepcopy` of `expr` so that they will
            stay independent during any further AST edits.

        `tag`: `str`
            The name of the paste-here indicator in `template`.

    Returns `template` with `expr` spliced in. Note `template` is **not** copied,
    and will be mutated in-place.
    """
    if not template:
        return expr

    if not (isinstance(expr, ast.expr) or
            (isinstance(expr, ASTMarker) and isinstance(expr.body, ast.expr))):
        raise TypeError(f"`expr` must be an expression AST node or AST marker containing such; got {type(expr)} with value {repr(expr)}")
    if not isinstance(template, (ast.AST, list)):
        raise TypeError(f"`template` must be an AST or `list`; got {type(template)} with value {repr(template)}")

    def ispastehere(tree):
        return type(tree) is ast.Name and tree.id == tag

    class ExpressionSplicer(ASTTransformer):
        def __init__(self):
            self.first = True
            super().__init__()

        def transform(self, tree):
            if ispastehere(tree):
                if not self.first:
                    return deepcopy(expr)
                self.first = False
                return expr
            return self.generic_visit(tree)

    return ExpressionSplicer().visit(template)


# TODO: this is actually a generic list-of-ast splicer, not specific to statements.
def splice_statements(body, template, tag="__paste_here__"):
    """Splice `body` into `template`.

    This is somewhat like `mcpyrate.quotes.a`, but must be called from outside the
    quoted snippet.

    Parameters:

        `body`: `list` of statements
            The statements you would like to splice in.

        `template`: `list` of statements
            Template into which to splice `body`.

            Must contain a paste-here indicator AST node, in a statement position,
            that specifies where `body` is to be spliced in. The node is expected
            to have the format::

                ast.Expr(value=ast.Name(id=tag))

            Or in plain English, it's a bare identifier in a statement position.

            The first-found instance (in AST scan order) of the paste-here indicator
            is replaced by `body`.

            If the paste-here indicator appears multiple times, second and further
            instances are replaced with a `copy.deepcopy` of `body` so that they will
            stay independent during any further AST edits.

        `tag`: `str`
            The name of the paste-here indicator in `template`.

    Returns `template` with `body` spliced in. Note `template` is **not** copied,
    and will be mutated in-place.

    Example::

        from mcpyrate.quotes import macros, q
        from mcpyrate.splicing import splice_statements

        body = [...]  # a list of statements

        with q as template:
            ...
            __paste_here__
            ...

        splice_statements(body, template)

    (Flake8 will complain about the undefined name `__paste_here__`. You can silence
     it with the appropriate `# noqa`, or to make it happy, import the `n` macro from
     `mcpyrate.quotes` and use `n["__paste_here__"]` instead of a plain `__paste_here__`.)
    """
    if isinstance(body, ast.AST):
        body = [body]
    if isinstance(template, ast.AST):
        body = [template]
    if not body:
        raise ValueError("expected at least one statement in `body`")
    if not template:
        return body

    def ispastehere(tree):
        return type(tree) is ast.Expr and type(tree.value) is ast.Name and tree.value.id == tag

    class StatementSplicer(ASTTransformer):
        def __init__(self):
            self.first = True
            super().__init__()

        def transform(self, tree):
            if ispastehere(tree):
                if not self.first:
                    return deepcopy(body)
                self.first = False
                return body
            return self.generic_visit(tree)

    return StatementSplicer().visit(template)


def splice_dialect(body, template, tag="__paste_here__", lineno=None, col_offset=None):
    """In a dialect AST transformer, splice module `body` into `template`.

    On top of what `splice_statements` does, this function handles macro-imports
    and dialect-imports specially, gathering them all at the top level of the
    final module body, so that mcpyrate sees them when the module is sent to
    the macro expander. This is to allow a dialect template to splice the body
    into the inside of a `with` block (e.g. to invoke some code-walking macro
    that changes the language semantics, such as an auto-TCO or a lazifier),
    without breaking macro-imports (and further dialect-imports) introduced
    by user code in the body.

    Any dialect-imports in the template are placed first (in the order they
    appear in the template), followed by any dialect-imports in the user code
    (in the order they appear in the user code), followed by macro-imports in
    the template, then macro-imports in the user code.

    We also handle the module docstring, future-imports, and the magic `__all__`.

    The optional `lineno` and `col_offset` parameters can be used to tell
    `splice_dialect` the source location info of the dialect-import (in the
    unexpanded source code) that triggered this template. If specified, they
    are used to mark all the lines coming from the template as having come
    from that dialect-import statement. During dialect expansion, you can
    get these from the `lineno` and `col_offset` attributes of your dialect
    instance (these attributes are filled in by `DialectExpander`).

    If both `body` and `template` have a module docstring, they are concatenated
    to produce the module docstring for the result. If only one of them has a
    module docstring, that docstring is used as-is. If neither has a module docstring,
    the docstring is omitted.

    The primary use of a module docstring in a dialect template is to be able to say
    that the program was written in dialect X, more information on which can be found at...

    Future-imports from `template` and `body` are concatenated.

    The magic `__all__` is taken from `body`; if `body` does not define it,
    it is omitted.

    In the result, the ordering is::

        docstring
        template future-imports
        body future-imports
        __all__ (if defined in body)
        template dialect-imports
        body dialect-imports
        template macro-imports
        body macro-imports
        the rest

    Parameters:

        `body`: `list` of `ast.stmt`, or a single `ast.stmt`
            Original module body from the user code (input).

        `template`: `list` of `ast.stmt`, or a single `ast.stmt`
            Template for the final module body (output).

            Must contain a paste-here indicator as in `splice_statements`.

        `tag`: `str`
            The name of the paste-here indicator in `template`.

        `lineno`: optional `int`
        `col_offset`: optional `int`
            Source location info of the dialect-import that triggered this template.

    Return value is `template` with `body` spliced in.

    Note `template` and `body` are **not** copied, and **both** will be mutated
    during the splicing process.
    """
    if isinstance(body, ast.AST):
        body = [body]
    if isinstance(template, ast.AST):
        template = [template]
    if not body:
        raise ValueError("expected at least one statement in `body`")
    if not template:
        return body

    # Generally speaking, dialect templates are fully macro-generated
    # quasiquoted snippets with no source location info to start with.
    # Even if they have location info, it's for a different file compared
    # to the use site where `body` comes from.
    #
    # Pretend the template code appears at the given source location,
    # or if not given, at the beginning of `body`.
    if lineno is not None and col_offset is not None:
        srcloc_dummynode = ast.Constant(value=None)
        srcloc_dummynode.lineno = lineno
        srcloc_dummynode.col_offset = col_offset
    else:
        srcloc_dummynode = body[0]
    for stmt in template:
        fix_locations(stmt, srcloc_dummynode, mode="overwrite")

    user_docstring, user_futureimports, body = split_futureimports(body)
    template_docstring, template_futureimports, template = split_futureimports(template)

    # Combine user and template docstrings if both are defined.
    if user_docstring and template_docstring:
        # We must extract the bare strings, combine them, and then pack the result into an AST node.
        user_doc = getdocstring(user_docstring)
        template_doc = getdocstring(template_docstring)
        sep = "\n" + ("-" * 79) + "\n"
        new_doc = user_doc + sep + template_doc
        new_docstring = ast.copy_location(ast.Constant(value=new_doc),
                                          user_docstring[0])
        docstring = [new_docstring]
    else:
        docstring = user_docstring or template_docstring

    futureimports = template_futureimports + user_futureimports

    def extract_magic_all(tree):
        def ismagicall(tree):
            if not (type(tree) is ast.Assign and len(tree.targets) == 1):
                return False
            target = tree.targets[0]
            return type(target) is ast.Name and target.id == "__all__"
        class MagicAllExtractor(ASTTransformer):
            def transform(self, tree):
                if ismagicall(tree):
                    self.collect(tree)
                    return None
                # We get just the top level of body by not recursing.
                return tree
        w = MagicAllExtractor()
        w.visit(tree)
        return tree, w.collected
    body, user_magic_all = extract_magic_all(body)
    template, ignored_template_magic_all = extract_magic_all(template)

    def extract_macroimports(tree, *, magicname: str="macros"):
        class MacroImportExtractor(ASTTransformer):
            def transform(self, tree):
                if ismacroimport(tree, magicname):
                    self.collect(tree)
                    return None
                return self.generic_visit(tree)
        w = MacroImportExtractor()
        w.visit(tree)
        return tree, w.collected
    template, template_dialect_imports = extract_macroimports(template, magicname="dialects")
    template, template_macro_imports = extract_macroimports(template)
    body, user_dialect_imports = extract_macroimports(body, magicname="dialects")
    body, user_macro_imports = extract_macroimports(body)

    finalbody = splice_statements(body, template, tag)
    return (docstring +
            futureimports +
            user_magic_all +
            template_dialect_imports + user_dialect_imports +
            template_macro_imports + user_macro_imports +
            finalbody)
