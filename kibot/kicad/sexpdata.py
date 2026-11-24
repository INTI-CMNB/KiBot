# -*- coding: utf-8 -*-
# [[[cog import cog; cog.outl('"""\n%s\n"""' % file('README.rst').read()) ]]]
"""
S-expression parser for Python
==============================

`sexpdata` is a simple S-expression parser/serializer.  It has
simple `load` and `dump` functions like `pickle`, `json` or `PyYAML`
module.

>>> from sexpdata import loads, dumps
>>> loads('("a" "b")')
['a', 'b']
>>> print(dumps(['a', 'b']))
("a" "b")


You can install `sexpdata` from PyPI_::

  pip install sexpdata


Links:

* `Documentation (at Read the Docs) <http://sexpdata.readthedocs.org/>`_
* `Repository (at GitHub) <https://github.com/tkf/sexpdata>`_
* `Issue tracker (at GitHub) <https://github.com/tkf/sexpdata/issues>`_
* `PyPI <http://pypi.python.org/pypi/sexpdata>`_
* `Travis CI <https://travis-ci.org/#!/tkf/sexpdata>`_


License
-------

`sexpdata` is licensed under the terms of the BSD 2-Clause License.
See the source code for more information.

"""
from typing import Optional

# [[[end]]]

# Copyright (c) 2012 Takafumi Arakaki
# All rights reserved.

# Copyright (c) 2022 Salvador E. Tropea
# Copyright (c) 2022 Instituto Nacional de Tecnología Industrial
# - Adapted to KiCad
# - Added sexp_iter

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:

# Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.

# Redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

__version__ = '0.0.4.dev1'
__author__ = 'Takafumi Arakaki'
__license__ = 'BSD License'
__all__ = [
    # API functions:
    'load', 'loads', 'dump', 'dumps',
    # Utility functions:
    'car', 'cdr',
    # S-expression classes:
    'Symbol', 'String', 'Quoted',
]

import re
from string import whitespace
import functools

BRACKETS = {'(': ')', '[': ']'}


# ** Generic errors

class SExpData(Exception):
    pass


# ** Utility

def return_as(converter):
    """
    Decorator to convert result of a function.

    It is just a function composition. The following two codes are
    equivalent.

    Using `@return_as`::

        @return_as(converter)
        def generator(args):
            ...

        result = generator(args)

    Manually do the same::

        def generator(args):
            ...

        result = converter(generator(args))

    Example:

    >>> @return_as(list)
    ... def f():
    ...     for i in range(3):
    ...         yield i
    ...
    >>> f()  # this gives a list, not an iterator
    [0, 1, 2]

    """
    def wrapper(generator):
        @functools.wraps(generator)
        def func(*args, **kwds):
            return converter(generator(*args, **kwds))
        return func
    return wrapper


# ** Interface

def load(filelike, **kwds):
    """
    Load object from S-expression stored in `filelike`.

    :arg  filelike: A text stream object.

    See :func:`loads` for valid keyword arguments.

    >>> import io
    >>> fp = io.StringIO()
    >>> sexp = [Symbol('a'), Symbol('b')]   # let's dump and load this object
    >>> dump(sexp, fp)
    >>> _ = fp.seek(0)
    >>> load(fp) == sexp
    True

    """
    return loads(filelike.read(), **kwds)


def loads(string: str, **kwds):
    r"""
    Load object from S-expression `string`.

    :arg        string: String containing an S-expression.
    :type          nil: str or None
    :keyword       nil: A symbol interpreted as an empty list.
                        Default is ``'nil'``.
    :type         true: str or None
    :keyword      true: A symbol interpreted as True.
                        Default is ``'t'``.
    :type        false: str or None
    :keyword     false: A symbol interpreted as False.
                        Default is ``None``.
    :type     line_comment: str
    :keyword  line_comment: Beginning of line comment.
                            Default is ``';'``.

    >>> loads('(a b)')
    [Symbol('a'), Symbol('b')]
    >>> loads('a')
    Symbol('a')
    >>> loads('(a \'b)')
    [Symbol('a'), Quoted(Symbol('b'))]
    >>> loads('(a \'(b))')
    [Symbol('a'), Quoted([Symbol('b')])]
    >>> loads('''
    ... ;; This is a line comment.
    ... 'a' 'b')  ; this is also a comment.
    ... ''')
    ['a', 'b']
    >>> loads('''
    ... # This is a line comment.
    ... ('a' 'b')  # this is also a comment.
    ... ''', line_comment='#')
    ['a', 'b']

    ``nil`` is converted to an empty list by default.  You can use
    keyword argument `nil` to change what symbol must be interpreted
    as nil:

    >>> loads('nil')
    []
    >>> loads('null', nil='null')
    []
    >>> loads('nil', nil=None)
    Symbol('nil')

    ``t`` is converted to True by default.  You can use keyword
    argument `true` to change what symbol must be converted to True.:

    >>> loads('t')
    True
    >>> loads('#t', true='#t')
    True
    >>> loads('t', true=None)
    Symbol('t')

    No symbol is converted to False by default.  You can use keyword
    argument `false` to convert a symbol to False.

    >>> loads('#f')
    Symbol('#f')
    >>> loads('#f', false='#f')
    False
    >>> loads('nil', false='nil', nil=None)
    False

    """
    obj = parse(string, **kwds)
    if len(obj) != 1:
        raise SExpData("Not an s-expression file")
    return obj


def dump(obj, filelike, **kwds):
    """
    Write `obj` as an S-expression into given stream `filelike`.

    :arg       obj: A Python object.
    :arg  filelike: A text stream object.

    See :func:`dumps` for valid keyword arguments.

    >>> import io
    >>> fp = io.StringIO()
    >>> dump([Symbol('a'), Symbol('b')], fp)
    >>> print(fp.getvalue())
    (a b)

    """
    filelike.write(dumps(obj))


def dumps(obj, **kwds):
    """
    Convert python object into an S-expression.

    :arg           obj: A Python object.
    :type       str_as: ``'symbol'`` or ``'string'``
    :keyword    str_as: How string should be interpreted.
                        Default is ``'string'``.
    :type     tuple_as: ``'list'`` or ``'array'``
    :keyword  tuple_as: How tuple should be interpreted.
                        Default is ``'list'``.
    :type      true_as: str
    :keyword   true_as: How True should be interpreted.
                        Default is ``'t'``
    :type     false_as: str
    :keyword  false_as: How False should be interpreted.
                        Default is ``'()'``
    :type      none_as: str
    :keyword   none_as: How None should be interpreted.
                        Default is ``'()'``

    Basic usage:

    >>> print(dumps(['a', 'b']))
    ('a' 'b')
    >>> print(dumps(['a', 'b'], str_as='symbol'))
    (a b)
    >>> print(dumps(dict(a=1)))
    (:a 1)
    >>> print(dumps([None, True, False, ()]))
    (() t () ())
    >>> print(dumps([None, True, False, ()],
    ...             none_as='null', true_as='#t', false_as='#f'))
    (null #t #f ())
    >>> print(dumps(('a', 'b')))
    ('a' 'b')
    >>> print(dumps(('a', 'b'), tuple_as='array'))
    ['a' 'b']

    More verbose usage:

    >>> print(dumps([Symbol('a'), Symbol('b')]))
    (a b)
    >>> print(dumps(Symbol('a')))
    a
    >>> print(dumps([Symbol('a'), Quoted(Symbol('b'))]))
    (a 'b)
    >>> print(dumps([Symbol('a'), Quoted([Symbol('b')])]))
    (a '(b))

    """
    return tosexp(obj, **kwds)


def car(obj):
    """
    Alias of ``obj[0]``.

    >>> car(loads('(a . b)'))
    Symbol('a')
    >>> car(loads('(a b)'))
    Symbol('a')

    """
    return obj[0]


def cdr(obj):
    """
    `cdr`-like function.

    >>> cdr(loads('(a . b)'))
    Symbol('b')
    >>> cdr(loads('(a b)'))
    [Symbol('b')]
    >>> cdr(loads('(a . (b))'))
    [Symbol('b')]
    >>> cdr(loads('(a)'))
    []
    >>> cdr(loads('(a . nil)'))
    []

    """
    # This is very lazy implementation.  Probably the best way to do
    # it is to define `Cons` S-expression class.
    if len(obj) > 2:
        dot = obj[1]
        if isinstance(dot, Symbol) and dot.value() == '.':
            return obj[2]
    return obj[1:]


# ** Core

class Sep(object):
    pass


def tosexp(obj, str_as='string', tuple_as='list',
           true_as='t', false_as='()', none_as='()', indent=0):
    """
    Convert an object to an S-expression (`dumps` is just calling this).

    See this table for comparison of lispy languages, to support them
    as much as possible:
    `Lisp: Common Lisp, Scheme/Racket, Clojure, Emacs Lisp - Hyperpolyglot
    <http://hyperpolyglot.org/lisp>`_

    """
    def _tosexp(x):
        return tosexp(x, str_as=str_as, tuple_as=tuple_as, true_as=true_as, false_as=false_as, none_as=none_as, indent=indent)

    if isinstance(obj, list):
        c = 1 if not indent else 2
        indent += c
        res = Bracket(obj, '(').tosexp(_tosexp)
        if res.endswith('  )') or res.endswith('\n )'):
            res = res[:-2] + ')'
        indent -= c
    elif isinstance(obj, tuple):
        c = 1 if not indent else 2
        indent += c
        if tuple_as == 'list':
            res = Bracket(obj, '(').tosexp(_tosexp)
        elif tuple_as == 'array':
            res = Bracket(obj, '[').tosexp(_tosexp)
        else:
            raise ValueError("tuple_as={0!r} is not valid".format(tuple_as))
        indent -= c
    elif obj is True:  # must do this before ``isinstance(obj, int)``
        res = true_as
    elif obj is False:
        res = false_as
    elif obj is None:
        res = none_as
    elif isinstance(obj, (int, float)):
        res = str(obj)
    elif isinstance(obj, str):
        if str_as == 'symbol':
            res = obj
        elif str_as == 'string':
            res = String(obj).tosexp()
        else:
            raise ValueError("str_as={0!r} is not valid".format(str_as))
    elif isinstance(obj, dict):
        res = _tosexp(dict_to_plist(obj))
    elif isinstance(obj, SExpBase):
        res = obj.tosexp(_tosexp)
    elif isinstance(obj, Sep):
        res = '\n' + ' '*indent
    else:
        raise TypeError(
            "Object of type '{0}' cannot be converted by `tosexp`. "
            "It's value is '{1!r}'".format(type(obj), obj))
    return res


@return_as(list)
def dict_to_plist(obj):
    for key in obj:
        yield Symbol(":{0}".format(key))
        yield obj[key]


class SExpBase(object):

    def __init__(self, val):
        self._val = val

    def __repr__(self) -> str:
        return "{0}({1!r})".format(self.__class__.__name__, self._val)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self._val == other._val
        else:
            return False

    def value(self):
        return self._val

    def tosexp(self, tosexp=tosexp):
        """
        Decode this object into an S-expression string.

        :arg tosexp: A function to be used when converting sub S-expression.

        """
        raise NotImplementedError

    @classmethod
    def quote(cls, string: str):
        for (s, q) in cls._lisp_quoted_specials:
            string = string.replace(s, q)
        return string

    @classmethod
    def unquote(cls, string: str):
        return cls._lisp_quoted_to_raw.get(string, string)


class Symbol(SExpBase):

    _lisp_quoted_specials = [
        ('\\', '\\\\'),    # must come first to avoid doubly quoting "\"
        ("'", r"\'"), ("`", r"\`"), ('"', r'\"'),
        ('(', r'\('), (')', r'\)'), ('[', r'\['), (']', r'\]'),
        (' ', r'\ '), (',', r'\,'), ('?', r'\?'),  # ('.', r'\.'), not in KiCad
        (';', r'\;'), ('#', r'\#'),
    ]

    _lisp_quoted_to_raw = {q: r for (r, q) in _lisp_quoted_specials}

    def tosexp(self, tosexp=None):
        return self.quote(self._val)


class String(SExpBase):

    _lisp_quoted_specials = [  # from Pymacs
        ('\\', '\\\\'),    # must come first to avoid doubly quoting "\"
        ('"', '\\"'), ('\b', '\\b'), ('\f', '\\f'),
        ('\n', '\\n'), ('\r', '\\r'), ('\t', '\\t')]

    _lisp_quoted_to_raw = {q: r for (r, q) in _lisp_quoted_specials}

    def tosexp(self, tosexp=None) -> str:
        return '"{0}"'.format(self.quote(self._val))


class Quoted(SExpBase):

    def tosexp(self, tosexp=tosexp) -> str:
        return "'{0}".format(tosexp(self._val))


class Bracket(SExpBase):

    def __init__(self, val, bra):
        assert bra in BRACKETS  # FIXME: raise an appropriate error
        super(Bracket, self).__init__(val)
        self._bra = bra

    def __repr__(self) -> str:
        return "{0}({1!r}, {2!r})".format(self.__class__.__name__, self._val, self._bra)

    def tosexp(self, tosexp=tosexp) -> str:
        bra = self._bra
        ke = BRACKETS[self._bra]
        c = ''
        for i, v in enumerate(self._val):
            v = tosexp(v)
            if i:
                # Separate by spaces
                c += ' '
            if v[0] == '\n':
                # Avoid spaces at the end of lines
                c = c.rstrip(' ')
            c += v
        return "{0}{1}{2}".format(bra, c, ke)


def bracket(val, bra):
    if bra == '(':
        return val
    else:
        return Bracket(val, bra)


class ExpectClosingBracket(Exception):

    def __init__(self, got, expect):
        super(ExpectClosingBracket, self).__init__(
            "Not enough closing brackets. "
            "Expected {0!r} to be the last letter in the sexp. "
            "Got: {1!r}".format(expect, got))


class ExpectNothing(Exception):

    def __init__(self, got):
        super(ExpectNothing, self).__init__(
            "Too many closing brackets. "
            "Expected no character left in the sexp. "
            "Got: {0!r}".format(got))


class Parser(object):

    closing_brackets = set(BRACKETS.values())
    _atom_end_basic = set(BRACKETS) | set(closing_brackets) | set('"\'') | set(whitespace)
    _atom_end_basic_or_escape_regexp = "|".join(map(re.escape,
                                                    _atom_end_basic | set('\\')))
    quote_or_escape_re = re.compile(r'"|\\')

    def __init__(self, string: str, string_to: Optional[str] = None, nil='nil', true='t', false=None,
                 line_comment=';'):
        self.string = string
        self.nil = nil
        self.true = true
        self.false = false
        self.string_to = (lambda x: x) if string_to is None else string_to
        self.line_comment = line_comment
        self.atom_end = {line_comment} | self._atom_end_basic
        self.atom_end_or_escape_re = re.compile("{0}|{1}".format(self._atom_end_basic_or_escape_regexp,
                                                re.escape(line_comment)))

    def parse_str(self, i):
        string = self.string
        chars = []
        append = chars.append
        search = self.quote_or_escape_re.search

        assert string[i] == '"'  # never fail
        while True:
            i += 1
            match = search(string, i)
            end = match.start()
            append(string[i:end])
            c = match.group()
            if c == '"':
                i = end + 1
                break
            elif c == '\\':
                i = end + 1
                append(String.unquote(c + string[i]))
        else:
            raise ExpectClosingBracket('"', None)
        return (i, ''.join(chars))

    def parse_atom(self, i):
        string = self.string
        chars = []
        append = chars.append
        search = self.atom_end_or_escape_re.search
        atom_end = self.atom_end

        while True:
            match = search(string, i)
            if not match:
                append(string[i:])
                i = len(string)
                break
            end = match.start()
            append(string[i:end])
            c = match.group()
            if c in atom_end:
                i = end  # this is different from str
                break
            elif c == '\\':
                i = end + 1
                append(Symbol.unquote(c + string[i]))
            i += 1
        else:
            raise ExpectClosingBracket('"', None)
        return (i, self.atom(''.join(chars)))

    def atom(self, token):
        if token == self.nil:
            return []
        if token == self.true:
            return True
        if token == self.false:
            return False
        try:
            return int(token)
        except ValueError:
            try:
                return float(token)
            except ValueError:
                return Symbol(token)

    def parse_sexp(self, i):
        string = self.string
        len_string = len(self.string)
        sexp = []
        append = sexp.append
        while i < len_string:
            c = string[i]
            if c == '"':
                (i, subsexp) = self.parse_str(i)
                append(self.string_to(subsexp))
            elif c in whitespace:
                i += 1
                continue
            elif c in BRACKETS:
                close = BRACKETS[c]
                (i, subsexp) = self.parse_sexp(i + 1)
                append(bracket(subsexp, c))
                try:
                    nc = string[i]
                except IndexError:
                    nc = None
                if nc != close:
                    raise ExpectClosingBracket(nc, close)
                i += 1
            elif c in self.closing_brackets:
                break
            elif c == "'":
                (i, subsexp) = self.parse_sexp(i + 1)
                append(Quoted(subsexp[0]))
                sexp.extend(subsexp[1:])
            elif c == self.line_comment:
                i = string.find('\n', i) + 1
                if i <= 0:
                    i = len_string
                    break
            else:
                (i, subsexp) = self.parse_atom(i)
                append(subsexp)
        return (i, sexp)

    def parse(self):
        (i, sexp) = self.parse_sexp(0)
        if i < len(self.string):
            raise ExpectNothing(self.string[i:])
        return sexp


def parse(string: str, **kwds):
    r"""
    Parse s-expression.

    >>> parse('(a b)')
    [[Symbol('a'), Symbol('b')]]
    >>> parse('a')
    [Symbol('a')]
    >>> parse('(a \'b)')
    [[Symbol('a'), Quoted(Symbol('b'))]]
    >>> parse('(a \'(b))')
    [[Symbol('a'), Quoted([Symbol('b')])]]

    """
    return Parser(string, **kwds).parse()


def sexp_iter(vect, path):
    """
    Returns an iterator to filter all the elements described in the path.
    """
    elems = path.split('/')
    total = len(elems)
    for i, e in enumerate(elems):
        iter = filter(lambda x: isinstance(x, list) and isinstance(x[0], Symbol) and x[0].value() == e, vect)
        if i == total-1:
            return iter
        vect = next(iter, None)
        if vect is None:
            return None
