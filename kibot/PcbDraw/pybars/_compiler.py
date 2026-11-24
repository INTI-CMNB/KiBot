#
# Copyright (c) 2015 Will Bond, Mjumbe Wawatu Ukweli, 2012 Canonical Ltd
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, version 3 only.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
# GNU Lesser General Public License version 3 (see the file LICENSE).

"""The compiler for pybars."""

import os
import re
import sys
from types import ModuleType
import linecache
from typing import Optional

# The following code allows importing pybars from the current dir
prev_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if sys.path[0] != prev_dir:
    try:
        sys.path.remove(prev_dir)
    except ValueError:
        pass
    sys.path.insert(0, prev_dir)

import pybars
from pybars import _templates
from .pymeta.grammar import OMeta

__all__ = [
    'Compiler',
    'strlist',
    'Scope'
    ]

__metaclass__ = type
# Flag for testing
debug = False


# Note that unless we presume handlebars is only generating valid html, we have
# to accept anything - so a broken template won't be all that visible - it will
# just render literally (because the anything rule matches it).

# this grammar generates a tokenised tree
handlebars_grammar = r"""

template ::= (<text> | <templatecommand>)*:body => ['template'] + body
text ::= <newline_text> | <whitespace_text> | <other_text>
newline_text ::= (~(<start>) ('\r'?'\n'):char) => ('newline', u'' + char)
whitespace_text ::= (~(<start>) (' '|'\t'))+:text => ('whitespace', u''.join(text))
other_text ::= (~(<start>) <anything>)+:text => ('literal', u''.join(text))
other ::= <anything>:char => ('literal', u'' + char)
templatecommand ::= <blockrule>
    | <comment>
    | <escapedexpression>
    | <expression>
    | <partial>
    | <rawblock>
start ::= '{' '{'
finish ::= '}' '}'
comment ::= <start> '!' (~(<finish>) <anything>)* <finish> => ('comment', )
space ::= ' '|'\t'|'\r'|'\n'
arguments ::= (<space>+ (<kwliteral>|<literal>|<path>|<subexpression>))*:arguments => arguments
subexpression ::= '(' <spaces> <path>:p (<space>+ (<kwliteral>|<literal>|<path>|<subexpression>))*:arguments <spaces> ')' => ('subexpr', p, arguments)
expression_inner ::= <spaces> <path>:p <arguments>:arguments <spaces> <finish> => (p, arguments)
expression ::= <start> '{' <expression_inner>:e '}' => ('expand', ) + e
    | <start> '&' <expression_inner>:e => ('expand', ) + e
escapedexpression ::= <start> <expression_inner>:e => ('escapedexpand', ) + e
block_inner ::= <spaces> <symbol>:s <arguments>:args <spaces> <finish>
    => (u''.join(s), args)
partial_inner ::= <spaces> <partialname>:s <arguments>:args <spaces> <finish>
    => (s, args)
alt_inner ::= <spaces> ('^' | 'e' 'l' 's' 'e') <spaces> <finish>
partial ::= <start> '>' <partial_inner>:i => ('partial',) + i
path ::= ~('/') <pathseg>+:segments => ('path', segments)
kwliteral ::= <safesymbol>:s '=' (<literal>|<path>|<subexpression>):v => ('kwparam', s, v)
literal ::= (<string>|<integer>|<boolean>|<null>|<undefined>):thing => ('literalparam', thing)
string ::= '"' <notdquote>*:ls '"' => u'"' + u''.join(ls) + u'"'
    | "'" <notsquote>*:ls "'" => u"'" + u''.join(ls) + u"'"
integer ::= '-'?:sign <digit>+:ds => int((sign if sign else '') + ''.join(ds))
boolean ::= <false>|<true>
false ::= 'f' 'a' 'l' 's' 'e' => False
true ::= 't' 'r' 'u' 'e' => True
null ::= ('n' 'u' 'l' 'l') => None
undefined ::= ('u' 'n' 'd' 'e' 'f' 'i' 'n' 'e' 'd') => None
notdquote ::= <escapedquote>
    | '\n' => '\\n'
    | '\r' => '\\r'
    | '\\' => '\\\\'
    | (~('"') <anything>)
notsquote ::= <escapedquote>
    | '\n' => '\\n'
    | '\r' => '\\r'
    | '\\' => '\\\\'
    | (~("'") <anything>)
escapedquote ::= '\\' '"' => '\\"'
    | "\\" "'" => "\\'"
notclosebracket ::= (~(']') <anything>)
safesymbol ::=  ~<alt_inner> '['? (<letter>|'_'):start (<letterOrDigit>|'_')+:symbol ']'? => start + u''.join(symbol)
symbol ::=  ~<alt_inner> '['? (<letterOrDigit>|'-'|'@')+:symbol ']'? => u''.join(symbol)
partialname ::= <subexpression>:s => s
    | ~<alt_inner> ('['|'"')? (~(<space>|<finish>|']'|'"' ) <anything>)+:symbol (']'|'"')? => ('literalparam', '"' + u''.join(symbol) + '"')
pathseg ::= '[' <notclosebracket>+:symbol ']' => u''.join(symbol)
    | ('@' '.' '.' '/') => u'@@_parent'
    | <symbol>
    | '/' => u''
    | ('.' '.' '/') => u'@_parent'
    | '.' => u''
pathfinish :expected ::= <start> '/' <path>:found ?(found == expected) <finish>
symbolfinish :expected ::= <start> '/' <symbol>:found ?(found == expected) <finish>
blockrule ::= <start> '#' <block_inner>:i
      <template>:t <alttemplate>:alt_t <symbolfinish i[0]> => ('block',) + i + (t, alt_t)
    | <start> '^' <block_inner>:i
      <template>:t <alttemplate>:alt_t <symbolfinish i[0]> => ('invertedblock',) + i + (t, alt_t)
alttemplate ::= (<start> <alt_inner> <template>)?:alt_t => alt_t or []
rawblockstart ::= <start> <start> <block_inner>:i <finish> => i
rawblockfinish :expected ::= <start> <symbolfinish expected> <finish>
rawblock ::= <rawblockstart>:i (~(<rawblockfinish i[0]>) <anything>)*:r <rawblockfinish i[0]>
    => ('rawblock',) + i + (''.join(r),)
"""

# this grammar compiles the template to python
compile_grammar = """
compile ::= <prolog> <rule>* => builder.finish()
prolog ::= "template" => builder.start()
rule ::= <literal>
    | <expand>
    | <escapedexpand>
    | <comment>
    | <block>
    | <invertedblock>
    | <rawblock>
    | <partial>
block ::= [ "block" <anything>:symbol [<arg>*:arguments] [<compile>:t] [<compile>?:alt_t] ] => builder.add_block(symbol, arguments, t, alt_t)
comment ::= [ "comment" ]
literal ::= [ ( "literal" | "newline" | "whitespace" ) :value ] => builder.add_literal(value)
expand ::= [ "expand" <path>:value [<arg>*:arguments]] => builder.add_expand(value, arguments)
escapedexpand ::= [ "escapedexpand" <path>:value [<arg>*:arguments]] => builder.add_escaped_expand(value, arguments)
invertedblock ::= [ "invertedblock" <anything>:symbol [<arg>*:arguments] [<compile>:t] [<compile>?:alt_t] ] => builder.add_invertedblock(symbol, arguments, t, alt_t)
rawblock ::= [ "rawblock" <anything>:symbol [<arg>*:arguments] <anything>:raw ] => builder.add_rawblock(symbol, arguments, raw)
partial ::= ["partial" <complexarg>:symbol [<arg>*:arguments]] => builder.add_partial(symbol, arguments)
path ::= [ "path" [<pathseg>:segment]] => ("simple", segment)
 | [ "path" [<pathseg>+:segments] ] => ("complex", u"resolve(context, u'" + u"', u'".join(segments) + u"')" )
complexarg ::= [ "path" [<pathseg>+:segments] ] => u"resolve(context, u'" + u"', u'".join(segments) + u"')"
    | [ "subexpr" ["path" <pathseg>:name] [<arg>*:arguments] ] => u'resolve_subexpr(helpers, "' + name + '", context' + (u', ' + u', '.join(arguments) if arguments else u'') + u')'
    | [ "literalparam" <anything>:value ] => {str}(value)
arg ::= [ "kwparam" <anything>:symbol <complexarg>:a ] => {str}(symbol) + '=' + a
    | <complexarg>
pathseg ::= "/" => ''
    | "." => ''
    | "" => ''
    | "this" => ''
pathseg ::= <anything>:symbol => u''.join(symbol)
"""  # noqa: E501
compile_grammar = compile_grammar.format(str=str.__name__)


class PybarsError(Exception):

    pass


class strlist(list):

    """A quasi-list to let the template code avoid special casing."""

    def __str__(self):
        return ''.join(self)

    def grow(self, thing):
        """Make the list longer, appending for unicode, extending otherwise."""
        if type(thing) == str:
            self.append(thing)
        else:
            # Recursively expand to a flat list; may deserve a C accelerator at
            # some point.
            for element in thing:
                self.grow(element)


_map = {
    '&': '&amp;',
    '"': '&quot;',
    "'": '&#x27;',
    '`': '&#x60;',
    '<': '&lt;',
    '>': '&gt;',
    }


def substitute(match, _map=_map):
    return _map[match.group(0)]


_escape_re = re.compile(r"&|\"|'|`|<|>")


def escape(something, _escape_re=_escape_re, substitute=substitute):
    return _escape_re.sub(substitute, something)


def pick(context, name: str, default=None):
    try:
        return context[name]
    except (KeyError, TypeError, AttributeError):
        if isinstance(name, str) and hasattr(context, name):
            return getattr(context, name)
        if hasattr(context, 'get'):
            return context.get(name)
        return default


sentinel = object()


class Scope:

    def __init__(self, context, parent, root, overrides=None, index=None, key=None, first=None, last=None):
        self.context = context
        self.parent = parent
        self.root = root
        # Must be dict of keys and values
        self.overrides = overrides
        self.index = index
        self.key = key
        self.first = first
        self.last = last

    def get(self, name: str, default=None):
        if name == '@root':
            return self.root
        if name == '@_parent':
            return self.parent
        if name == '@index' and self.index is not None:
            return self.index
        if name == '@key' and self.key is not None:
            return self.key
        if name == '@first' and self.first is not None:
            return self.first
        if name == '@last' and self.last is not None:
            return self.last
        if name == 'this':
            return self.context
        if self.overrides and name in self.overrides:
            return self.overrides[name]
        return pick(self.context, name, default)
    __getitem__ = get

    def __len__(self):
        return len(self.context)

    def __str__(self):
        return str(self.context)


def resolve(context, *segments):
    carryover_data = False

    # This makes sure that bare "this" paths don't return a Scope object
    if segments == ('',) and isinstance(context, Scope):
        return context.get('this')

    for segment in segments:

        # Handle @../index syntax by popping the extra @ along the segment path
        if carryover_data:
            carryover_data = False
            segment = u'@%s' % segment
        if len(segment) > 1 and segment[0:2] == '@@':
            segment = segment[1:]
            carryover_data = True

        if context is None:
            return None
        if segment in (None, ""):
            continue
        if type(context) in (list, tuple):
            if segment == 'length':
                return len(context)
            offset = int(segment)
            context = context[offset]
        elif isinstance(context, Scope):
            context = context.get(segment)
        else:
            context = pick(context, segment)
    return context


def resolve_subexpr(helpers, name: str, context, *args, **kwargs):
    if name not in helpers:
        raise PybarsError(u"Could not find property %s" % (name,))
    return helpers[name](context, *args, **kwargs)


def prepare(value, should_escape):
    """
    Prepares a value to be added to the result

    :param value:
        The value to add to the result

    :param should_escape:
        If the string should be HTML-escaped

    :return:
        A unicode string or strlist
    """

    if value is None:
        return u''
    type_ = type(value)
    if type_ is not strlist:
        if type_ is not str:
            if type_ is bool:
                value = u'true' if value else u'false'
            else:
                value = str(value)
        if should_escape:
            value = escape(value)
    return value


def ensure_scope(context, root):
    return context if isinstance(context, Scope) else Scope(context, context, root)


def _each(this, options, context):
    result = strlist()

    # All sequences in python have a length
    try:
        last_index = len(context) - 1

        # If there are no items, we want to trigger the else clause
        if last_index < 0:
            raise IndexError()

    except (TypeError, IndexError):
        return options['inverse'](this)

    # We use the presence of a keys method to determine if the
    # key attribute should be passed to the block handler
    has_keys = hasattr(context, 'keys')

    index = 0
    for value in context:
        kwargs = {
            'index': index,
            'first': index == 0,
            'last': index == last_index
        }

        if has_keys:
            kwargs['key'] = value
            value = context[value]

        scope = Scope(value, this, options['root'], **kwargs)

        # Necessary because of cases such as {{^each things}}test{{/each}}.
        try:
            result.grow(options['fn'](scope))
        except TypeError:
            pass
        index += 1

    return result


def _if(this, options, context):
    if hasattr(context, '__call__'):
        context = context(this)
    if context:
        return options['fn'](this)
    else:
        return options['inverse'](this)


def _log(this, context):
    pybars.log(context)


def _unless(this, options, context):
    if not context:
        return options['fn'](this)


def _lookup(this, context, key):
    try:
        return context[key]
    except (KeyError, IndexError, TypeError):
        return


def _blockHelperMissing(this, options, context):
    if hasattr(context, '__call__'):
        context = context(this)
    if context != u"" and not context:
        return options['inverse'](this)
    if type(context) in (list, strlist, tuple):
        return _each(this, options, context)
    if context is True:
        callwith = this
    else:
        callwith = context
    return options['fn'](callwith)


def _helperMissing(scope, name: str, *args):
    if not args:
        return None
    raise PybarsError(u"Could not find property %s" % (name,))


def _with(this, options, context):
    return options['fn'](context)


# scope for the compiled code to reuse globals
_pybars_ = {
    'helpers': {
        'blockHelperMissing': _blockHelperMissing,
        'each': _each,
        'if': _if,
        'helperMissing': _helperMissing,
        'log': _log,
        'unless': _unless,
        'with': _with,
        'lookup': _lookup,
    },
}


class FunctionContainer:

    """
    Used as a container for functions by the CodeBuidler
    """

    def __init__(self, name: str, code):
        self.name = name
        self.code = code

    @property
    def full_code(self):
        headers = (
            u'import pybars\n'
            u'\n'
            u'if pybars.__version__ != %s:\n'
            u'    raise pybars.PybarsError("This template was precompiled with pybars3 version %s, running version %%s" %% pybars.__version__)\n'
            u'\n'
            u'from pybars import strlist, Scope, PybarsError\n'
            u'from pybars._compiler import _pybars_, escape, resolve, resolve_subexpr, prepare, ensure_scope\n'
            u'\n'
            u'from functools import partial\n'
            u'\n'
            u'\n'
        ) % (repr(pybars.__version__), pybars.__version__)

        return headers + self.code


class CodeBuilder:

    """Builds code for a template."""

    def __init__(self):
        self._reset()

    def _reset(self):
        self.stack = []
        self.var_counter = 1
        self.render_counter = 0

    def start(self):
        function_name = 'render' if self.render_counter == 0 else 'block_%s' % self.render_counter
        self.render_counter += 1

        self.stack.append((strlist(), {}, function_name))
        self._result, self._locals, _ = self.stack[-1]
        # Context may be a user hash or a Scope (which injects '@_parent' to
        # implement .. lookups). The JS implementation uses a vector of scopes
        # and then interprets a linear walk-up, which is why there is a
        # disabled test showing arbitrary complex path manipulation: the scope
        # approach used here will probably DTRT but may be slower: reevaluate
        # when profiling.
        if len(self.stack) == 1:
            self._result.grow([
                u"def render(context, helpers=None, partials=None, root=None):\n"
                u"    _helpers = dict(_pybars_['helpers'])\n"
                u"    if helpers is not None:\n"
                u"        _helpers.update(helpers)\n"
                u"    helpers = _helpers\n"
                u"    if partials is None:\n"
                u"        partials = {}\n"
                u"    called = root is None\n"
                u"    if called:\n"
                u"        root = context\n"
            ])
        else:
            self._result.grow(u"def %s(context, helpers, partials, root):\n" % function_name)
        self._result.grow(u"    result = strlist()\n")
        self._result.grow(u"    context = ensure_scope(context, root)\n")

    def finish(self):
        lines, ns, function_name = self.stack.pop(-1)

        # Ensure the result is a string and not a strlist
        if len(self.stack) == 0:
            self._result.grow(u"    if called:\n")
            self._result.grow(u"        result = %s(result)\n" % str.__name__)
        self._result.grow(u"    return result\n")

        source = str(u"".join(lines))

        self._result = self.stack and self.stack[-1][0]
        self._locals = self.stack and self.stack[-1][1]

        code = ''
        for key in ns:
            if isinstance(ns[key], FunctionContainer):
                code += ns[key].code + '\n'
            else:
                code += '%s = %s\n' % (key, repr(ns[key]))
        code += source

        result = FunctionContainer(function_name, code)
        if debug and len(self.stack) == 0:
            print('Compiled Python')
            print('---------------')
            print(result.full_code)

        return result

    def _wrap_nested(self, name: str) -> str:
        return u"partial(%s, helpers=helpers, partials=partials, root=root)" % name

    def add_block(self, symbol, arguments, nested, alt_nested):
        name = nested.name
        self._locals[name] = nested

        if alt_nested:
            alt_name = alt_nested.name
            self._locals[alt_name] = alt_nested

        call = self.arguments_to_call(arguments)
        self._result.grow([
            u"    options = {'fn': %s}\n" % self._wrap_nested(name),
            u"    options['helpers'] = helpers\n"
            u"    options['partials'] = partials\n"
            u"    options['root'] = root\n"
            ])
        if alt_nested:
            self._result.grow([
                u"    options['inverse'] = ",
                self._wrap_nested(alt_name),
                u"\n"
                ])
        else:
            self._result.grow([
                u"    options['inverse'] = lambda this: None\n"
                ])
        self._result.grow([
            u"    value = helper = helpers.get(u'%s')\n" % symbol,
            u"    if value is None:\n"
            u"        value = resolve(context, u'%s')\n" % symbol,
            u"    if helper and hasattr(helper, '__call__'):\n"
            u"        value = helper(context, options%s\n" % call,
            u"    else:\n"
            u"        value = helpers['blockHelperMissing'](context, options, value)\n"
            u"    result.grow(value or '')\n"
            ])

    def add_literal(self, value):
        self._result.grow(u"    result.append(%s)\n" % repr(value))

    def _lookup_arg(self, arg):
        if not arg:
            return u"context"
        return arg

    def arguments_to_call(self, arguments):
        params = list(map(self._lookup_arg, arguments))
        output = u', '.join(params) + u')'
        if len(params) > 0:
            output = u', ' + output
        return output

    def find_lookup(self, path, path_type, call):
        if path_type == "simple":  # simple names can reference helpers.
            # TODO: compile this whole expression in the grammar; for now,
            # fugly but only a compile time overhead.
            # XXX: just rm.
            realname = path.replace('.get("', '').replace('")', '')
            self._result.grow([
                u"    value = helpers.get(u'%s')\n" % realname,
                u"    if value is None:\n"
                u"        value = resolve(context, u'%s')\n" % path,
                ])
        else:
            realname = None
            self._result.grow(u"    value = %s\n" % path)
        self._result.grow([
            u"    if hasattr(value, '__call__'):\n"
            u"        value = value(context%s\n" % call,
            ])
        if realname:
            self._result.grow(
                u"    elif value is None:\n"
                u"        value = helpers['helperMissing'](context, u'%s'%s\n"
                    % (realname, call)
                )

    def add_escaped_expand(self, path_type_path, arguments):
        (path_type, path) = path_type_path
        call = self.arguments_to_call(arguments)
        self.find_lookup(path, path_type, call)
        self._result.grow([
            u"    result.grow(prepare(value, True))\n"
            ])

    def add_expand(self, path_type_path, arguments):
        (path_type, path) = path_type_path
        call = self.arguments_to_call(arguments)
        self.find_lookup(path, path_type, call)
        self._result.grow([
            u"    result.grow(prepare(value, False))\n"
            ])

    def _debug(self):
        self._result.grow(u"    import pdb;pdb.set_trace()\n")

    def add_invertedblock(self, symbol, arguments, nested, alt_nested):
        name = nested.name
        self._locals[name] = nested

        if alt_nested:
            alt_name = alt_nested.name
            self._locals[alt_name] = alt_nested

        call = self.arguments_to_call(arguments)
        self._result.grow([
            u"    options = {'inverse': %s}\n" % self._wrap_nested(name),
            u"    options['helpers'] = helpers\n"
            u"    options['partials'] = partials\n"
            u"    options['root'] = root\n"
            ])
        if alt_nested:
            self._result.grow([
                u"    options['fn'] = ",
                self._wrap_nested(alt_name),
                u"\n"
                ])
        else:
            self._result.grow([
                u"    options['fn'] = lambda this: None\n"
                ])
        self._result.grow([
            u"    value = helper = helpers.get(u'%s')\n" % symbol,
            u"    if value is None:\n"
            u"        value = resolve(context, u'%s')\n" % symbol,
            u"    if helper and hasattr(helper, '__call__'):\n"
            u"        value = helper(context, options%s\n" % call,
            u"    else:\n"
            u"        value = helpers['blockHelperMissing'](context, options, value)\n"
            u"    result.grow(value or '')\n"
            ])

    def add_rawblock(self, symbol, arguments, raw):
        call = self.arguments_to_call(arguments)
        self._result.grow([
            u"    options = {'fn': lambda this: %s}\n" % repr(raw),
            u"    options['helpers'] = helpers\n"
            u"    options['partials'] = partials\n"
            u"    options['root'] = root\n"
            u"    options['inverse'] = lambda this: None\n"
            u"    helper = helpers.get(u'%s')\n" % symbol,
            u"    if helper and hasattr(helper, '__call__'):\n"
            u"        value = helper(context, options%s\n" % call,
            u"    else:\n"
            u"        value = %s\n" % repr(raw),
            u"    result.grow(value or '')\n"
            ])

    def _invoke_template(self, fn_name: str, this_name: str):
        self._result.grow([
            u"    result.grow(",
            fn_name,
            u"(",
            this_name,
            u", helpers=helpers, partials=partials, root=root))\n"
            ])

    def add_partial(self, symbol, arguments):
        arg = ""

        overrides = None
        positional_args = 0
        if arguments:
            for argument in arguments:
                kwmatch = re.match(r'(\w+)=(.+)$', argument)
                if kwmatch:
                    if not overrides:
                        overrides = {}
                    overrides[kwmatch.group(1)] = kwmatch.group(2)
                else:
                    if positional_args != 0:
                        raise PybarsError("An extra positional argument was passed to a partial")
                    positional_args += 1
                    arg = argument

        overrides_literal = 'None'
        if overrides:
            overrides_literal = u'{'
            for key in overrides:
                overrides_literal += u'"%s": %s, ' % (key, overrides[key])
            overrides_literal += u'}'
        self._result.grow([u"    overrides = %s\n" % overrides_literal])

        self._result.grow([
            u"    partialName = %s\n" % symbol,
            u"    if partialName not in partials:\n",
            u"        raise PybarsError('The partial %s could not be found' % partialName)\n",
            u"    inner = partials[partialName]\n",
            u"    scope = Scope(%s, context, root, overrides=overrides)\n" % self._lookup_arg(arg)])
        self._invoke_template("inner", "scope")


class Compiler:

    """A handlebars template compiler.

    The compiler is not threadsafe: you need one per thread because of the
    state in CodeBuilder.
    """

    _handlebars = OMeta.makeGrammar(handlebars_grammar, {}, 'handlebars')
    _builder = CodeBuilder()
    _compiler = OMeta.makeGrammar(compile_grammar, {'builder': _builder})

    def __init__(self):
        self._helpers = {}
        self.template_counter = 1

    def _extract_word(self, source, position):
        """
        Extracts the word that falls at or around a specific position

        :param source:
            The template source as a unicode string
        :param position:
            The position where the word falls

        :return:
            The word
        """
        boundry = re.search(r'{{|{|\s|$', source[:position][::-1])
        start_offset = boundry.end() if boundry.group(0).startswith('{') else boundry.start()

        boundry = re.search(r'}}|}|\s|$', source[position:])
        end_offset = boundry.end() if boundry.group(0).startswith('}') else boundry.start()

        return source[position - start_offset:position + end_offset]

    def _generate_code(self, source):
        """
        Common compilation code shared between precompile() and compile()

        :param source:
            The template source as a unicode string

        :return:
            A tuple of (function, source_code)
        """

        if not isinstance(source, str):
            raise PybarsError("Template source must be a unicode string")

        source = self.whitespace_control(source)

        tree, (position, _) = self._handlebars(source).apply('template')

        if debug:
            print('\nAST')
            print('---')
            print(tree)
            print('')

        if position < len(source):
            line_num = source.count('\n') + 1
            beginning_of_line = source.rfind('\n', 0, position)
            if beginning_of_line == -1:
                char_num = position
            else:
                char_num = position - beginning_of_line
            word = self._extract_word(source, position)
            raise PybarsError("Error at character %s of line %s near %s" % (char_num, line_num, word))

        # Ensure the builder is in a clean state - kinda gross
        self._compiler.globals['builder']._reset()

        output = self._compiler(tree).apply('compile')[0]
        return output

    def whitespace_control(self, source):
        """
        Preprocess source to handle whitespace control and remove extra block
        whitespaces.

        :param source:
            The template source as a unicode string
        :return:
            The processed template source as a unicode string
        """
        cleanup_sub = re.compile(
            # Clean-up whitespace control marks and spaces between blocks tags
            r'(?<={{)~|~(?=}})|(?<=}})[ \t]+(?={{)').sub

        return re.sub(
            # Whitespace control using "~" mark
            r'~}}\s*|\s*{{~|'

            # Whitespace around alone blocks tags that in a line
            r'(?<=\n)([ \t]*{{(#[^{}]+|/[^{}]+|![^{}]+|else|else if [^{}]+)}}[ \t]*)+\r?\n|'

            # Whitespace aroud alone blocks tag on the first line
            r'^([ \t]*{{(#[^{}]+|![^{}]+)}}[ \t]*)+\r?\n|'

            # Whitespace aroud alone blocks tag on the last line
            r'\r?\n([ \t]*{{(/[^{}]+|![^{}]+)}}[ \t]*)+$',
            lambda match: cleanup_sub('', match.group(0).strip()), source)

    def precompile(self, source):
        """
        Generates python source code that can be saved to a file for caching

        :param source:
            The template to generate source for - should be a unicode string

        :return:
            Python code as a unicode string
        """

        return self._generate_code(source).full_code

    def compile(self, source, path=None):
        """Compile source to a ready to run template.

        :param source:
            The template to compile - should be a unicode string

        :return:
            A template function ready to execute
        """

        container = self._generate_code(source)

        def make_module_name(name: str, suffix: Optional[str]=None):
            output = 'pybars._templates.%s' % name
            if suffix:
                output += '_%s' % suffix
            return output

        if not path:
            path = '_template'
            generate_name = True
        else:
            path = path.replace('\\', '/')
            path = path.replace('/', '_')
            mod_name = make_module_name(path)
            generate_name = mod_name in sys.modules

        if generate_name:
            mod_name = make_module_name(path, self.template_counter)
            while mod_name in sys.modules:
                self.template_counter += 1
                mod_name = make_module_name(path, self.template_counter)

        mod = ModuleType(mod_name)
        filename = '%s.py' % mod_name.replace('pybars.', '').replace('.', '/')
        exec(compile(container.full_code, filename, 'exec', dont_inherit=True), mod.__dict__)
        sys.modules[mod_name] = mod
        linecache.getlines(filename, mod.__dict__)

        return mod.__dict__[container.name]

    def template(self, code):
        def _render(context, helpers=None, partials=None, root=None):
            ns = {
                'context': context,
                'helpers': helpers,
                'partials': partials,
                'root': root
            }
            exec(code + '\nresult = render(context, helpers=helpers, partials=partials, root=root)', ns)
            return ns['result']
        return _render
