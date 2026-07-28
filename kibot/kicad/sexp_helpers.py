# -*- coding: utf-8 -*-
# Copyright (c) 2021-2025 Salvador E. Tropea
# Copyright (c) 2021-2025 Instituto Nacional de Tecnología Industrial
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)
from .error import SchError
from ..error import KiPlotConfigurationError
from .sexpdata import Symbol, Sep, SExpData, load
# Sections we must separate to make it readable
# TO_SEPARATE = {'kicad_pcb', 'general', 'title_block', 'layers', 'setup', 'pcbplotparams', 'net_class', 'module',
#                'kicad_sch', 'lib_symbols', 'symbol', 'sheet', 'sheet_instances', 'symbol_instances'}


def _symbol(name, content=None):
    if content is None:
        return [Symbol(name)]
    return [Symbol(name)] + content


class Point(object):
    def __init__(self, items):
        super().__init__()
        self.x = _check_float(items, 1, 'x coord')
        self.y = _check_float(items, 2, 'y coord')

    @staticmethod
    def parse(items):
        return Point(items)


class Color(object):
    def __init__(self, items=None):
        super().__init__()
        if items:
            self.r = _check_integer(items, 1, 'red color')
            self.g = _check_integer(items, 2, 'green color')
            self.b = _check_integer(items, 3, 'blue color')
            # Sheet sheet.fill.color is float ...
            self.a = _check_float(items, 4, 'alpha color')
        else:
            self.r = self.g = self.b = self.a = 0

    @staticmethod
    def parse(items):
        return Color(items)

    def write(self):
        return _symbol('color', [self.r, self.g, self.b, self.a])


def make_separated(sexp):
    """ Add separators to make the file more readable """
    if not isinstance(sexp, list):
        return sexp
    if not isinstance(sexp[0], Symbol):  # or sexp[0].value() not in TO_SEPARATE: sometimes produces huge lines
        return sexp
    separated = []
    for s in sexp:
        separated.append(make_separated(s))
        if isinstance(s, list):
            separated.append(Sep())
    return separated


def load_sexp_file(fname):
    with open(fname, 'rt') as fh:
        error = None
        try:
            ki_file = load(fh)
        except SExpData as e:
            error = str(e)
        if error:
            raise KiPlotConfigurationError(error)
    return ki_file


def _check_is_symbol_list(e, allow_orphan_symbol=()):
    # Each entry is a list
    if not isinstance(e, list):
        if isinstance(e, Symbol):
            name = e.value()
            if name in allow_orphan_symbol:
                return name
            raise SchError('Orphan symbol `{}`'.format(e.value()))
        else:
            raise SchError('Orphan data `{}`'.format(e))
    # The first element is a symbol
    if not isinstance(e[0], Symbol):
        raise SchError('Orphan data `{}`'.format(e[0]))
    return e[0].value()


def _check_len(items, pos, name):
    if len(items) < pos+1:
        raise SchError('Missing argument {} in `{}`'.format(pos, name))
    return items[pos]


def _check_len_total(items, num, name):
    if len(items) != num:
        raise SchError('Wrong number of attributes for {} `{}`'.format(name, items))


def _check_symbol(items, pos, name):
    value = _check_len(items, pos, name)
    if not isinstance(value, Symbol):
        raise SchError('{} is not a Symbol `{}` ({})'.format(name, value, type(value)))
    return value.value()


def _check_hide(items, pos, name):
    # hide alone as a symbol or (hide yes/no)
    value = _check_len(items, pos, name)
    name += ' hide'
    if isinstance(value, list):
        hide = _check_symbol(value, 0, name)
        if hide != 'hide':
            raise SchError(f'Found Symbol `{hide}` when `hide` expected')
        return _get_yes_no(value, 1, name)
    value = _check_symbol(items, pos, name)
    if value != 'hide':
        raise SchError(f'Found Symbol `{value}` when `hide` expected')
    return True


def _check_integer(items, pos, name):
    value = _check_len(items, pos, name)
    if not isinstance(value, int):
        raise SchError('{} is not an integer `{}`'.format(name, value))
    return value


def _check_float(items, pos, name):
    value = _check_len(items, pos, name)
    if not isinstance(value, (float, int)):
        raise SchError('{} is not a float `{}`'.format(name, value))
    return value


def _check_floats(items, pos, name):
    value = _check_len(items, pos, name)
    if not isinstance(value, (float, int)):
        raise SchError('{} is not a float `{}`'.format(name, value))
    return items[pos:]


def _check_str(items, pos, name):
    value = _check_len(items, pos, name)
    if not isinstance(value, str):
        raise SchError('{} is not a string `{}`'.format(name, value))
    return value


def _check_relaxed(items, pos, name):
    value = _check_len(items, pos, name)
    if isinstance(value, str):
        return value
    if isinstance(value, Symbol):
        return value.value()
    if isinstance(value, (float, int)):
        return str(value)
    raise SchError('{} is not a string, Symbol or number `{}`'.format(name, value))


def _check_symbol_value(items, pos, name, sym):
    value = _check_len(items, pos, name)
    if not isinstance(value, list) or not isinstance(value[0], Symbol) or value[0].value() != sym:
        raise SchError('Missing `{}` in `{}`'.format(sym, name))
    return value


def _check_symbol_float(items, pos, name, sym):
    name += ' ' + sym
    values = _check_symbol_value(items, pos, name, sym)
    return _check_float(values, 1, name)


def _check_symbol_int(items, pos, name, sym):
    name += ' ' + sym
    values = _check_symbol_value(items, pos, name, sym)
    return _check_integer(values, 1, name)


def _check_symbol_str(items, pos, name, sym):
    name += ' ' + sym
    values = _check_symbol_value(items, pos, name, sym)
    return _check_str(values, 1, name)


def _get_offset(items, pos, name):
    value = _check_symbol_value(items, pos, name, 'offset')
    return _check_float(value, 1, 'offset')


def _get_yes_no(items, pos, name):
    sym = _check_symbol(items, pos, name)
    return sym == 'yes'


def _get_yes_no_maybe_alone(items, pos, name):
    # ATTRIBUTE alone used to indicate "yes"
    if len(items) < pos+1:
        return True
    sym = _check_symbol(items, pos, name)
    return sym == 'yes'


def _get_id(items, pos, name):
    value = _check_symbol_value(items, pos, name, 'id')
    return _check_integer(value, 1, 'id')


def _get_at(items, pos, name):
    value = _check_symbol_value(items, pos, name, 'at')
    angle = 0
    if len(value) > 3:
        angle = _check_float(value, 3, 'at angle')
    return _check_float(value, 1, 'at x'), _check_float(value, 2, 'at y'), angle


def _get_xy(items):
    if len(items) != 3:
        raise SchError('Point definition with wrong args (`{}`)'.format(items))
    return Point.parse(items)


def _get_points(items):
    points = []
    for i in items[1:]:
        i_type = _check_is_symbol_list(i)
        if i_type == 'xy':
            points.append(_get_xy(i))
        else:
            raise SchError('Unknown points attribute `{}`'.format(i))
    return points


def _get_pin_groups(items):
    groups = []
    for i in items[1:]:
        if not isinstance(i, list):
            raise SchError(f'Pin group contains a group that is not a list `{i}`')
        groups.append(i)
    return groups


def _get_size(items, pos, name):
    value = _check_symbol_value(items, pos, name, 'size')
    return _get_xy(value)


def _get_symbol_name(items):
    """ Check if items is a list and starts with a symbol, return its name, otherwise None """
    return None if not isinstance(items, list) or not isinstance(items[0], Symbol) else items[0].value()
