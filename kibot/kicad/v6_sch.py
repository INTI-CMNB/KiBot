# -*- coding: utf-8 -*-
# Copyright (c) 2021 Salvador E. Tropea
# Copyright (c) 2021 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
"""
KiCad v6 Schematic format.
A basic implementation of the .kicad_sch file format.
Currently oriented to collect the components for the BoM.
Documentation: https://dev-docs.kicad.org/en/file-formats/sexpr-schematic/
"""
# Encapsulate file/line
import os
import re
from collections import OrderedDict
from ..gs import GS
from .. import log
from ..misc import W_NOLIB, W_UNKFLD, W_MISSCMP
from .v5_sch import SchError, SchematicComponent, Schematic
from .sexpdata import load, SExpData, Symbol, dumps, Sep

logger = log.get_logger()
CROSSED_LIB = 'kibot_crossed'


def _check_is_symbol_list(e, allow_orphan_symbol=[]):
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
        raise SchError('{} is not a Symbol `{}`'.format(name, value))
    return value.value()


def _check_hide(items, pos, name):
    value = _check_symbol(items, pos, name + ' hide')
    if value != 'hide':
        raise SchError('Found Symbol `{}` when `hide` expected'.format(value))
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


def _check_str(items, pos, name):
    value = _check_len(items, pos, name)
    if not isinstance(value, str):
        raise SchError('{} is not a string `{}`'.format(name, value))
    return value


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


def _get_id(items, pos, name):
    value = _check_symbol_value(items, pos, name, 'id')
    return _check_integer(value, 1, 'id')


def _get_at(items, pos, name):
    value = _check_symbol_value(items, pos, name, 'at')
    angle = 0
    if len(value) > 3:
        angle = _check_float(value, 3, 'at angle')
    return _check_float(value, 1, 'at x'), _check_float(value, 2, 'at y'), angle


class Point(object):
    def __init__(self, items):
        super().__init__()
        self.x = _check_float(items, 1, 'x coord')
        self.y = _check_float(items, 2, 'y coord')

    @staticmethod
    def parse(items):
        return Point(items)


class PointXY(object):
    def __init__(self, x, y):
        super().__init__()
        self.x = x
        self.y = y


class Box(object):
    def __init__(self, points=None):
        self.x1 = self.y1 = self.x2 = self.y2 = 0
        self.set = False
        if points:
            self.x1 = self.x2 = points[0].x
            self.y1 = self.y2 = points[0].y
            for p in points[1:]:
                self.x1 = min(p.x, self.x1)
                self.x2 = max(p.x, self.x2)
                self.y1 = min(p.y, self.y1)
                self.y2 = max(p.y, self.y2)
            self.set = True

    def __str__(self):
        if not self.set:
            return "Box *uninitialized*"
        return "Box({},{} to {},{})".format(self.x1, self.y1, self.x2, self.y2)

    def diagonal(self, inverse=False):
        if inverse:
            return [PointXY(self.x1, self.y2), PointXY(self.x2, self.y1)]
        return [PointXY(self.x1, self.y1), PointXY(self.x2, self.y2)]

    def union(self, b):
        if not self.set:
            self.x1 = b.x1
            self.y1 = b.y1
            self.x2 = b.x2
            self.y2 = b.y2
            self.set = True
        elif b.set:
            self.x1 = min(self.x1, b.x1)
            self.y1 = min(self.y1, b.y1)
            self.x2 = max(self.x2, b.x2)
            self.y2 = max(self.y2, b.y2)


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


class FontEffects(object):
    """ Class used to describe text attributes """
    def __init__(self):
        super().__init__()
        self.hide = False
        self.w = self.h = 1.27
        self.thickness = None
        self.bold = self.italic = False
        self.hjustify = self.vjustify = 'C'
        self.mirror = False

    @staticmethod
    def parse_font(items):
        w = h = 1.27
        thickness = None
        bold = italic = False
        for i in items[1:]:
            if isinstance(i, Symbol):
                name = i.value()
                if name == 'bold':
                    bold = True
                elif name == 'italic':
                    italic = True
                else:
                    raise SchError('Unknown font effect attribute `{}`'.format(name))
            else:  # A list
                i_type = _check_is_symbol_list(i)
                if i_type == 'size':
                    h = _check_float(i, 1, 'font height')
                    w = _check_float(i, 2, 'font width')
                elif i_type == 'thickness':
                    thickness = _check_float(i, 1, 'font thickness')
                else:
                    raise SchError('Unknown font effect attribute `{}`'.format(i))
        return w, h, thickness, bold, italic

    @staticmethod
    def parse_justify(items):
        h = v = 'C'
        mirror = False
        for i in items[1:]:
            if isinstance(i, Symbol):
                name = i.value()
                if name == 'left':
                    h = 'L'
                elif name == 'right':
                    h = 'R'
                elif name == 'top':
                    v = 'T'
                elif name == 'bottom':
                    v = 'B'
                elif name == 'mirror':
                    mirror = True
                else:
                    raise SchError('Unknown font effect attribute `{}`'.format(name))
            else:  # A list
                raise SchError('Unknown font effect attribute `{}`'.format(i))
        return h, v, mirror

    @staticmethod
    def parse(items):
        o = FontEffects()
        for c, i in enumerate(items[1:]):
            if isinstance(i, Symbol):
                # Only hide exists
                o.hide = _check_hide(items, c+1, 'font effect')
            elif isinstance(i, list):
                i_type = _check_is_symbol_list(i)
                if i_type == 'font':
                    o.w, o.h, o.thickness, o.bold, o.italic = FontEffects.parse_font(i)
                elif i_type == 'justify':
                    o.hjustify, o.vjustify, o.mirror = FontEffects.parse_justify(i)
                else:
                    raise SchError('Unknown font effect attribute `{}`'.format(i))
        return o

    def write_font(self):
        data = [_symbol('size', [self.h, self.w])]
        if self.thickness is not None:
            data.append(_symbol('thickness', [self.thickness]))
        if self.bold:
            data.append(Symbol('bold'))
        if self.italic:
            data.append(Symbol('italic'))
        return _symbol('font', data)

    def write_justify(self):
        data = []
        if self.hjustify == 'L':
            data.append(Symbol('left'))
        elif self.hjustify == 'R':
            data.append(Symbol('right'))
        if self.vjustify == 'T':
            data.append(Symbol('top'))
        elif self.vjustify == 'B':
            data.append(Symbol('bottom'))
        if self.mirror:
            data.append(Symbol('mirror'))
        return _symbol('justify', data)

    def write(self):
        data = [self.write_font()]
        if self.hjustify != 'C' or self.vjustify != 'C' or self.mirror:
            data.append(self.write_justify())
        if self.hide:
            data.append(Symbol('hide'))
        return _symbol('effects', data)


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


class Stroke(object):
    def __init__(self):
        super().__init__()
        self.width = 0
        self.type = 'default'
        self.color = Color()

    @staticmethod
    def parse(items):
        stroke = Stroke()
        for i in items[1:]:
            i_type = _check_is_symbol_list(i)
            if i_type == 'width':
                stroke.width = _check_float(i, 1, 'stroke width')
            elif i_type == 'type':
                stroke.type = _check_symbol(i, 1, 'stroke type')
            elif i_type == 'color':
                stroke.color = Color.parse(i)
            else:
                raise SchError('Unknown stroke attribute `{}`'.format(i))
        return stroke

    def write(self):
        data = [_symbol('width', [self.width])]
        data.append(_symbol('type', [Symbol(self.type)]))
        data.append(self.color.write())
        return _symbol('stroke', data)


class Fill(object):
    def __init__(self):
        super().__init__()
        self.type = None
        self.color = None

    @staticmethod
    def parse(items):
        fill = Fill()
        for i in items[1:]:
            i_type = _check_is_symbol_list(i)
            if i_type == 'type':
                fill.type = _check_symbol(i, 1, 'fill type')
            elif i_type == 'color':
                # Not documented, found in sheet.fill
                fill.color = Color.parse(i)
            else:
                raise SchError('Unknown fill attribute `{}`'.format(i))
        return fill

    def write(self):
        data = []
        if self.type is not None:
            data.append(_symbol('type', [Symbol(self.type)]))
        if self.color is not None:
            data.append(self.color.write())
        return _symbol('fill', data)


class DrawArcV6(object):
    def __init__(self):
        super().__init__()
        self.start = None
        self.mid = None
        self.end = None
        self.stroke = None
        self.fill = None

    @staticmethod
    def parse(items):
        arc = DrawArcV6()
        for i in items[1:]:
            i_type = _check_is_symbol_list(i)
            if i_type == 'start':
                arc.start = _get_xy(i)
            elif i_type == 'mid':
                arc.mid = _get_xy(i)
            elif i_type == 'end':
                arc.end = _get_xy(i)
            elif i_type == 'stroke':
                arc.stroke = Stroke.parse(i)
            elif i_type == 'fill':
                arc.fill = Fill.parse(i)
            else:
                raise SchError('Unknown arc attribute `{}`'.format(i))
        arc.box = Box([arc.start, arc.mid, arc.end])
        return arc

    def write(self):
        data = [_symbol('start', [self.start.x, self.start.y])]
        data.append(_symbol('mid', [self.mid.x, self.mid.y]))
        data.append(_symbol('end', [self.end.x, self.end.y]))
        data.append(Sep())
        data.extend([self.stroke.write(), Sep()])
        data.extend([self.fill.write(), Sep()])
        return _symbol('arc', data)


class DrawCircleV6(object):
    def __init__(self):
        super().__init__()
        self.center = None
        self.radius = 0
        self.stroke = None
        self.fill = None

    @staticmethod
    def parse(items):
        circle = DrawCircleV6()
        for i in items[1:]:
            i_type = _check_is_symbol_list(i)
            if i_type == 'center':
                circle.center = _get_xy(i)
            elif i_type == 'radius':
                circle.radius = _check_float(i, 1, 'circle radius')
            elif i_type == 'stroke':
                circle.stroke = Stroke.parse(i)
            elif i_type == 'fill':
                circle.fill = Fill.parse(i)
            else:
                raise SchError('Unknown circle attribute `{}`'.format(i))
        p1 = PointXY(circle.center.x-circle.radius, circle.center.x-circle.radius)
        p2 = PointXY(circle.center.x+circle.radius, circle.center.x+circle.radius)
        circle.box = Box([p1, p2])
        return circle

    def write(self):
        data = [_symbol('center', [self.center.x, self.center.y])]
        data.append(_symbol('radius', [self.radius]))
        data.append(Sep())
        data.extend([self.stroke.write(), Sep()])
        data.extend([self.fill.write(), Sep()])
        return _symbol('circle', data)


class DrawRectangleV6(object):
    def __init__(self):
        super().__init__()
        self.start = None
        self.end = None
        self.stroke = None
        self.fill = None

    @staticmethod
    def parse(items):
        rectangle = DrawRectangleV6()
        for i in items[1:]:
            i_type = _check_is_symbol_list(i)
            if i_type == 'start':
                rectangle.start = _get_xy(i)
            elif i_type == 'end':
                rectangle.end = _get_xy(i)
            elif i_type == 'stroke':
                rectangle.stroke = Stroke.parse(i)
            elif i_type == 'fill':
                rectangle.fill = Fill.parse(i)
            else:
                raise SchError('Unknown rectangle attribute `{}`'.format(i))
        rectangle.box = Box([rectangle.start, rectangle.end])
        return rectangle

    def write(self):
        data = [_symbol('start', [self.start.x, self.start.y])]
        data.append(_symbol('end', [self.end.x, self.end.y]))
        data.append(Sep())
        data.extend([self.stroke.write(), Sep()])
        data.extend([self.fill.write(), Sep()])
        return _symbol('rectangle', data)


class DrawCurve(object):
    """ Qubic Bezier """
    def __init__(self):
        super().__init__()
        self.points = []
        self.stroke = None
        self.fill = None

    @staticmethod
    def parse(items):
        curve = DrawCurve()
        for i in items[1:]:
            i_type = _check_is_symbol_list(i)
            if i_type == 'pts':
                curve.points = _get_points(i)
            elif i_type == 'stroke':
                curve.stroke = Stroke.parse(i)
            elif i_type == 'fill':
                curve.fill = Fill.parse(i)
            else:
                raise SchError('Unknown curve attribute `{}`'.format(i))
        curve.box = Box(curve.points)
        return curve

    def write(self):
        points = [Sep()]
        for p in self.points:
            points.append(_symbol('xy', [p.x, p.y]))
            points.append(Sep())
        data = [_symbol('pts', points), Sep()]
        data.extend([self.stroke.write(), Sep()])
        data.extend([self.fill.write(), Sep()])
        return _symbol('gr_curve', data)


class DrawPolyLine(object):
    def __init__(self):
        super().__init__()
        self.points = []
        self.stroke = None
        self.fill = None

    @staticmethod
    def parse(items):
        line = DrawPolyLine()
        for i in items[1:]:
            i_type = _check_is_symbol_list(i)
            if i_type == 'pts':
                line.points = _get_points(i)
            elif i_type == 'stroke':
                line.stroke = Stroke.parse(i)
            elif i_type == 'fill':
                line.fill = Fill.parse(i)
            else:
                raise SchError('Unknown polyline attribute `{}`'.format(i))
        line.box = Box(line.points)
        return line

    def write(self):
        points = [Sep()]
        for p in self.points:
            points.append(_symbol('xy', [p.x, p.y]))
            points.append(Sep())
        data = [Sep(), _symbol('pts', points), Sep()]
        data.extend([self.stroke.write(), Sep()])
        data.extend([self.fill.write(), Sep()])
        return _symbol('polyline', data)


class DrawTextV6(object):
    def __init__(self):
        super().__init__()
        self.text = None
        self.x = self.y = self.ang = 0
        self.effects = None
        self.box = Box()

    @staticmethod
    def parse(items):
        text = DrawTextV6()
        text.text = _check_str(items, 1, 'text')
        text.x, text.y, text.ang = _get_at(items, 2, 'text')
        text.effects = _get_effects(items, 3, 'text')
        return text

    def write(self):
        data = [self.text, _symbol('at', [self.x, self.y, self.ang]), Sep()]
        data.extend([self.effects.write(), Sep()])
        return _symbol('text', data)


def _get_effects(items, pos, name):
    values = _check_symbol_value(items, pos, name, 'effects')
    return FontEffects.parse(values)


class PinV6(object):
    def __init__(self):
        super().__init__()
        self.type = self.gtype = self.name = self.number = ''
        self.pos_x = self.pos_y = self.ang = self.len = 0
        self.name_effects = self.number_effects = None
        self.hide = False
        self.box = Box()

    @staticmethod
    def parse(items):
        name = 'pin'
        pin = PinV6()
        pin.type = _check_symbol(items, 1, name+' type')
        pin.gtype = _check_symbol(items, 2, name+' style')
        for c, i in enumerate(items[3:]):
            i_type = _check_is_symbol_list(i, allow_orphan_symbol=['hide'])
            if i_type == 'at':
                pin.pos_x, pin.pos_y, pin.ang = _get_at(items, c+3, name)
            elif i_type == 'length':
                pin.len = _check_float(i, 1, name+' length')
            elif i_type == 'hide':
                # Not documented yet
                pin.hide = True
            elif i_type == 'name':
                pin.name = _check_str(i, 1, name+' name')
                pin.name_effects = _get_effects(i, 2, name+' name')
            elif i_type == 'number':
                pin.number = _check_str(i, 1, name+' number')
                pin.number_effects = _get_effects(i, 2, name+' number')
            else:
                raise SchError('Unknown pin attribute `{}`'.format(i))

        if not pin.hide:
            p1 = PointXY(pin.pos_x, pin.pos_y)
            ang = pin.ang % 360
            if ang == 0:
                co = 1
                si = 0
            elif pin.ang == 90:
                co = 0
                si = 1
            elif pin.ang == 180:
                co = -1
                si = 0
            else:  # 270
                co = 0
                si = -1
            p2 = PointXY(pin.pos_x+pin.len*co, pin.pos_y+pin.len*si)
            pin.box = Box([p1, p2])
        return pin

    def write(self):
        data = [Symbol(self.type),
                Symbol(self.gtype),
                _symbol('at', [self.pos_x, self.pos_y, self.ang]),
                _symbol('length', [self.len])]
        if self.hide:
            data.append(Symbol('hide'))
        data.extend([Sep(), _symbol('name', [self.name, self.name_effects.write()]), Sep(),
                    _symbol('number', [self.number, self.number_effects.write()]), Sep()])
        return _symbol('pin', data)


class SchematicFieldV6(object):
    # Fixed ids:
    # 0 Reference
    # 1 Value
    # 2 Footprint
    # 3 Datasheet
    # Reserved names: ki_keywords, ki_description, ki_locked, ki_fp_filters
    def __init__(self, name='', value='', id=0, x=0, y=0, ang=0):
        super().__init__()
        self.name = name
        self.value = value
        self.number = id
        self.x = x
        self.y = y
        self.ang = ang
        self.effects = None
        self.hide = False

    @staticmethod
    def parse(items):
        if len(items) != 6:
            _check_len_total(items, 5, 'property')
        field = SchematicFieldV6()
        field.name = _check_str(items, 1, 'field name')
        field.value = _check_str(items, 2, 'field value')
        field.number = _get_id(items, 3, 'field id')
        field.x, field.y, field.ang = _get_at(items, 4, 'field')
        if len(items) > 5:
            field.effects = _get_effects(items, 5, 'field')
        else:
            field.effects = None
        return field

    def write(self):
        if self.number < 0:
            return None
        data = [self.name, self.value, _symbol('id', [self.number])]
        data.append(_symbol('at', [self.x, self.y, self.ang]))
        if self.effects:
            data.extend([Sep(), self.effects.write(), Sep()])
        return _symbol('property', data)


class LibComponent(object):
    unit_regex = re.compile(r'^(.*)_(\d+)_(\d+)$')
    cross_color = Color()
    cross_stroke = Stroke()
    cross_stroke.width = 0.6
    cross_stroke.color = cross_color
    cross_fill = Fill()
    cross_fill.type = 'none'

    def __init__(self):
        super().__init__()
        self.pin_numbers_hide = None
        self.pin_names_hide = None
        self.pin_names_offset = None
        self.in_bom = False
        self.on_board = False
        self.is_power = False
        self.unit = 0
        self.draw = []
        self.fields = []
        self.dfields = {}
        self.box = Box()
        self.alias = None
        self.dcm = None
        self.fp_list = None
        # This member is used to generate crossed components (DNF).
        # When defined means we need to add a cross in this box and then reset the box.
        self.cross_box = None

    def get_field_value(self, field):
        field = field.lower()
        if field in self.dfields:
            return self.dfields[field].value
        return ''

    @staticmethod
    def load(c, project, parent=None):  # noqa: C901
        if not isinstance(c, list):
            raise SchError('Library component definition is not a list')
        if len(c) < 3:
            raise SchError('Truncated library component definition (len<3)')
        if not isinstance(c[0], Symbol) or c[0].value() != 'symbol':
            raise SchError('Library component definition is of wrong type')
        comp = LibComponent()
        comp.project = project
        # First argument is the LIB:NAME
        comp.lib_id = comp.name = _check_str(c, 1, 'name')
        res = comp.name.split(':')
        comp.lib = None
        if len(res) == 1:
            # Appears valid: https://docs.kicad.org/doxygen/classLIB__ID.html#a195467cfd12903226615d74540ec647a
            # Note: seems to be a locally edited component
            comp.name = res[0]
            comp.lib = ''
        elif len(res) == 2:
            comp.name = res[1]
            comp.lib = res[0]
        else:
            if parent is None:
                logger.warning(W_NOLIB + "Component `{}` with more than one `:`".format(comp.name))
        comp.units = []
        comp.pins = []
        comp.all_pins = []
        comp.unit_count = 1
        # Variable list
        for i in c[2:]:
            i_type = _check_is_symbol_list(i)
            vis_obj = None
            if i_type == 'pin_numbers':
                comp.pin_numbers_hide = _check_hide(i, 1, i_type)
            elif i_type == 'pin_names':
                value = _check_len(i, 1, i_type)
                index = 1
                if isinstance(value, list):
                    comp.pin_names_offset = _get_offset(i, 1, i_type)
                    index = 2
                comp.pin_names_hide = None
                try:
                    comp.pin_names_hide = _check_symbol(i, index, i_type)
                except SchError:
                    # Optional
                    pass
            elif i_type == 'in_bom':
                comp.in_bom = _get_yes_no(i, 1, i_type)
            elif i_type == 'on_board':
                comp.on_board = _get_yes_no(i, 1, i_type)
            elif i_type == 'power':
                # Not yet documented
                comp.is_power = True
            # SYMBOL_PROPERTIES...
            elif i_type == 'property':
                field = SchematicFieldV6.parse(i)
                comp.fields.append(field)
                comp.dfields[field.name.lower()] = field
            # GRAPHIC_ITEMS...
            elif i_type == 'arc':
                vis_obj = DrawArcV6.parse(i)
                comp.draw.append(vis_obj)
            elif i_type == 'circle':
                vis_obj = DrawCircleV6.parse(i)
                comp.draw.append(vis_obj)
            elif i_type == 'gr_curve':
                vis_obj = DrawCurve.parse(i)
                comp.draw.append(vis_obj)
            elif i_type == 'polyline':
                vis_obj = DrawPolyLine.parse(i)
                comp.draw.append(vis_obj)
            elif i_type == 'rectangle':
                vis_obj = DrawRectangleV6.parse(i)
                comp.draw.append(vis_obj)
            elif i_type == 'text':
                comp.draw.append(DrawTextV6.parse(i))
            # PINS...
            elif i_type == 'pin':
                vis_obj = PinV6.parse(i)
                comp.pins.append(vis_obj)
                if parent:
                    parent.all_pins.append(vis_obj)
            # UNITS...
            elif i_type == 'symbol':
                # They use a special naming scheme:
                # 1) A symbol without real units:
                #    - *_0_1 the body
                #    - *_1_1 the pins
                # 2) A symbol with real units:
                #    - Each unit is *_N_* where N is the unit starting from 1
                #    - If the unit has alternative drawing they are *_N_1 and *_N_2
                #    - If the unit doesn't have alternative we have *_N_x x starts from 0
                #      Pins and drawings can be in _N_0 and/or _N_1
                vis_obj = LibComponent.load(i, project, parent=comp if parent is None else parent)
                comp.units.append(vis_obj)
                m = LibComponent.unit_regex.search(vis_obj.lib_id)
                if m is None:
                    raise SchError('Malformed unit id `{}`'.format(vis_obj.lib_id))
                unit = int(m.group(2))
                comp.unit_count = max(unit, comp.unit_count)
            else:
                raise SchError('Unknown symbol attribute `{}`'.format(i))
            if vis_obj:
                comp.box.union(vis_obj.box)
        return comp

    def assign_crosses(self):
        """ Compute the box for the crossed components """
        name0 = self.name+"_0"
        # Compute the full box for each unit
        for c in range(self.unit_count):
            name = self.name+"_"+str(c+1)
            box = Box()
            unit_with_graphs = None
            for unit in self.units:
                # Unit 0 is part of unit 1
                if unit.name.startswith(name) or (c == 0 and unit.name.startswith(name0)):
                    box.union(unit.box)
                    if len(unit.draw):
                        unit_with_graphs = unit
            if unit_with_graphs:
                unit_with_graphs.cross_box = box

    def write_cross(s, sdata):
        """ Add the cross drawing """
        if s.cross_box:
            # Add a cross
            o = DrawPolyLine()
            o.stroke = LibComponent.cross_stroke
            o.fill = LibComponent.cross_fill
            o.points = s.cross_box.diagonal()
            sdata.extend([o.write(), Sep()])
            o.points = s.cross_box.diagonal(True)
            sdata.extend([o.write(), Sep()])
            s.cross_box = None

    def write(s, cross=False):
        lib_id = s.lib_id
        if cross:
            # Fill the cross_box of our sub/units
            s.assign_crosses()
            if s.units:
                # Use an alternative name
                lib_id = CROSSED_LIB+':'+s.name
        sdata = [lib_id]
        if s.is_power:
            sdata.append(_symbol('power', []))
        if s.pin_numbers_hide:
            sdata.append(_symbol('pin_numbers', [Symbol('hide')]))
        if s.pin_names_hide is not None or s.pin_names_offset is not None:
            aux = []
            if s.pin_names_offset is not None:
                aux.append(_symbol('offset', [s.pin_names_offset]))
            if s.pin_names_hide is not None:
                aux.append(Symbol('hide'))
            sdata.append(_symbol('pin_names', aux))
        if s.in_bom:
            sdata.append(_symbol('in_bom', [Symbol('yes')]))
        if s.on_board:
            sdata.append(_symbol('on_board', [Symbol('yes')]))
        sdata.append(Sep())
        # Properties
        for f in s.fields:
            fdata = f.write()
            if fdata is not None:
                sdata.extend([fdata, Sep()])
        # Graphics
        for g in s.draw:
            sdata.extend([g.write(), Sep()])
        s.write_cross(sdata)
        # Pins
        for p in s.pins:
            sdata.extend([p.write(), Sep()])
        # Units
        for u in s.units:
            sdata.extend([u.write(cross), Sep()])
        return _symbol('symbol', sdata)


class SchematicComponentV6(SchematicComponent):
    def __init__(self):
        super().__init__()
        self.in_bom = False
        self.on_board = False
        self.pins = OrderedDict()
        self.unit = 1
        self.unit_specified = False
        self.ref = None
        self.local_name = None

    def set_ref(self, ref):
        self.ref = ref
        # Separate the reference in its components
        m = SchematicComponent.ref_re.match(ref)
        if not m:
            raise SchError('Malformed component reference `{}`'.format(ref))
        self.ref_prefix, self.ref_suffix = m.groups()

    def set_footprint(self, fp):
        res = fp.split(':')
        cres = len(res)
        if cres == 1:
            self.footprint = res[0]
            self.footprint_lib = None
        elif cres == 2:
            self.footprint_lib = res[0]
            self.footprint = res[1]
        else:
            raise SchError('Footprint with more than one colon (`{}`)'.format(fp))

    @staticmethod
    def load(c, project, parent):
        if not isinstance(c, list):
            raise SchError('Component definition is not a list')
        if len(c) < 7:
            raise SchError('Truncated component definition (len<7)')
        if not isinstance(c[0], Symbol) or c[0].value() != 'symbol':
            raise SchError('Component definition is of wrong type')
        comp = SchematicComponentV6()
        comp.project = project
        # The path will be computed by the instance
        # comp.sheet_path_h = parent.sheet_path_h
        comp.parent_sheet = parent
        name = 'component'
        lib_id_found = False
        at_found = False

        # Variable list
        for i in c[1:]:
            i_type = _check_is_symbol_list(i)
            if i_type == 'lib_id':
                # First argument is the LIB:NAME
                comp.lib_id = comp.name = _check_str(i, 1, name + ' lib_id')
                res = comp.name.split(':')
                comp.lib = None
                if len(res) == 1:
                    comp.name = res[0]
                    comp.lib = ''
                elif len(res) == 2:
                    comp.name = res[1]
                    comp.lib = res[0]
                else:
                    logger.warning(W_NOLIB + "Component `{}` with more than one `:`".format(comp.name))
                lib_id_found = True
            elif i_type == 'lib_name':
                # Symbol defined in schematic
                comp.local_name = _check_str(i, 1, name + ' lib_name')
            elif i_type == 'at':
                # 2 The position
                if len(i) > 3:
                    comp.ang = _check_float(i, 3, 'at angle')
                else:
                    comp.ang = 0
                comp.x, comp.y = _check_float(i, 1, 'at x'), _check_float(i, 2, 'at y')
                at_found = True
            elif i_type == 'unit':
                # This is documented as mandatory, but isn't always there
                comp.unit = _check_integer(i, 1, name+' unit')
                comp.unit_specified = True
            elif i_type == 'in_bom':
                comp.in_bom = _get_yes_no(i, 1, i_type)
            elif i_type == 'on_board':
                comp.on_board = _get_yes_no(i, 1, i_type)
            elif i_type == 'uuid':
                comp.uuid = _check_symbol(i, 1, name + ' uuid')
            # SYMBOL_PROPERTIES...
            elif i_type == 'property':
                field = SchematicFieldV6.parse(i)
                name_lc = field.name.lower()
                # Add to the global collection
                if name_lc not in parent.fields_lc:
                    parent.fields.append(field.name)
                    parent.fields_lc.add(name_lc)
                # Add to the component
                comp.add_field(field)
                if field.number == 3:
                    # Reference, Value and Footprint are defined by the instance.
                    # But datasheet must be transferred from this field.
                    comp.datasheet = field.value
            # PINS...
            elif i_type == 'pin':
                pin_name = _check_str(i, 1, name + 'pin name')
                pin_uuid = _get_uuid(i, 2, name)
                comp.pins[pin_name] = pin_uuid
        if not lib_id_found or not at_found:
            raise SchError("Component missing 'lib_id' and/or 'at'")

        # Fake 'Part' field
        field = SchematicFieldV6()
        field.name = 'part'
        field.value = comp.name
        field.number = -1
        comp.add_field(field)
        return comp

    def write(self, cross=False):
        lib_id = self.lib_id
        is_crossed = not(self.fitted or not self.included)
        if cross and (self.lib or self.local_name) and is_crossed:
            # Use an alternative name
            lib_id = CROSSED_LIB+':'+(self.local_name if self.local_name else self.name)
        data = [_symbol('lib_id', [lib_id]),
                _symbol('at', [self.x, self.y, self.ang])]
        if self.unit_specified:
            data.append(_symbol('unit', [self.unit]))
        data.append(Sep())
        if self.in_bom or self.on_board:
            if self.in_bom:
                data.append(_symbol('in_bom', [Symbol('yes')]))
            if self.on_board:
                data.append(_symbol('on_board', [Symbol('yes')]))
            data.append(Sep())
        data.extend([_symbol('uuid', [Symbol(self.uuid)]), Sep()])
        for f in self.fields:
            d = f.write()
            if d:
                data.extend([d, Sep()])
        for k, v in self.pins.items():
            data.extend([_symbol('pin', [k, _symbol('uuid', [Symbol(v)])]), Sep()])
        return _symbol('symbol', data)


def _get_uuid(items, pos, where):
    values = _check_symbol_value(items, pos, where + ' uuid', 'uuid')
    return _check_symbol(values, 1, where + ' uuid')


class Junction(object):
    @staticmethod
    def parse(items):
        _check_len_total(items, 5, 'junction')
        jun = Junction()
        jun.pos_x, jun.pos_y, jun.ang = _get_at(items, 1, 'junction')
        jun.diameter = _check_symbol_float(items, 2, 'junction', 'diameter')
        jun.color = Color.parse(items[3])
        jun.uuid = _get_uuid(items, 4, 'junction')
        return jun

    def write(self):
        data = [_symbol('at', [self.pos_x, self.pos_y]),
                _symbol('diameter', [self.diameter]),
                self.color.write(), Sep(),
                _symbol('uuid', [Symbol(self.uuid)]), Sep()]
        return _symbol('junction', data)


class BusAlias(object):
    @staticmethod
    def parse(items):
        _check_len_total(items, 3, 'bus_alias')
        alias = BusAlias()
        alias.name = _check_str(items, 1, 'bus_alias')
        elems = _check_symbol_value(items, 2, 'bus_alias', 'members')
        alias.members = elems[1:]
        return alias

    def write(self):
        return _symbol('bus_alias', [self.name, _symbol('members', self.members)])


class NoConnect(object):
    @staticmethod
    def parse(items):
        _check_len_total(items, 3, 'no_connect')
        nocon = NoConnect()
        nocon.pos_x, nocon.pos_y, nocon.ang = _get_at(items, 1, 'no connect')
        nocon.uuid = _get_uuid(items, 2, 'no connect')
        return nocon

    def write(self):
        data = [_symbol('at', [self.pos_x, self.pos_y]),
                _symbol('uuid', [Symbol(self.uuid)])]
        return _symbol('no_connect', data)


class BusEntry(object):
    @staticmethod
    def parse(items):
        _check_len_total(items, 5, 'bus entry')
        buse = BusEntry()
        buse.pos_x, buse.pos_y, buse.ang = _get_at(items, 1, 'bus entry')
        values = _check_symbol_value(items, 2, 'bus entry size', 'size')
        buse.size = _get_xy(values)
        buse.stroke = Stroke.parse(items[3])
        buse.uuid = _get_uuid(items, 4, 'bus entry')
        return buse

    def write(self):
        data = [_symbol('at', [self.pos_x, self.pos_y]),
                _symbol('size', [self.size.x, self.size.y]), Sep(),
                self.stroke.write(), Sep(),
                _symbol('uuid', [Symbol(self.uuid)]), Sep()]
        return _symbol('bus_entry', data)


class SchematicWireV6(object):
    @staticmethod
    def parse(items, name):
        _check_len_total(items, 4, name)
        wire = SchematicWireV6()
        wire.type = name  # wire, bus, polyline
        wire.points = _get_points(items[1])
        wire.stroke = Stroke.parse(items[2])
        wire.uuid = _get_uuid(items, 3, name)
        return wire

    def write(self):
        points = [_symbol('xy', [p.x, p.y]) for p in self.points]
        data = [_symbol('pts', points), Sep(), self.stroke.write(), Sep(), _symbol('uuid', [Symbol(self.uuid)]), Sep()]
        return _symbol(self.type, data)


class SchematicBitmapV6(object):
    @staticmethod
    def parse(items):
        bmp = SchematicBitmapV6()
        if len(items) == 5:
            bmp.scale = _check_symbol_float(items, 2, 'image', 'scale')
            index = 3
        else:
            _check_len_total(items, 4, 'image')
            bmp.scale = None
            index = 2
        bmp.pos_x, bmp.pos_y, bmp.ang = _get_at(items, 1, 'image')
        bmp.uuid = _get_uuid(items, index, 'image')
        values = _check_symbol_value(items, index+1, 'image data', 'data')
        bmp.data = [_check_symbol(values, i+1, 'image data') for i, d in enumerate(values[1:])]
        return bmp

    def write(self):
        d = []
        for v in self.data:
            d.append(Symbol(v))
            d.append(Sep())
        data = [_symbol('at', [self.pos_x, self.pos_y]), Sep(),
                _symbol('uuid', [Symbol(self.uuid)]), Sep(),
                _symbol('data', [Sep()] + d), Sep()]
        return _symbol('image', data)


class Text(object):
    @staticmethod
    def parse(items, name):
        _check_len_total(items, 5, name)
        text = Text()
        text.name = name
        text.text = _check_str(items, 1, name)
        text.pos_x, text.pos_y, text.ang = _get_at(items, 2, name)
        text.effects = _get_effects(items, 3, name)
        text.uuid = _get_uuid(items, 4, name)
        return text

    def write(self):
        data = [self.text,
                _symbol('at', [self.pos_x, self.pos_y, self.ang]), Sep(),
                self.effects.write(), Sep(),
                _symbol('uuid', [Symbol(self.uuid)]), Sep()]
        return _symbol(self.name, data)


class GlobalLabel(object):
    def __init__(self):
        super().__init__()
        self.text = ''
        self.shape = None
        self.fields_autoplaced = False
        self.pos_x = self.pos_y = self.ang = 0
        self.effects = None
        self.uuid = None
        self.properties = []

    @staticmethod
    def parse(items):
        label = GlobalLabel()
        label.text = _check_str(items, 1, 'global_label')
        for c, i in enumerate(items[2:]):
            i_type = _check_is_symbol_list(i)
            if i_type == 'shape':
                label.shape = _check_symbol(i, 1, i_type)
            elif i_type == 'fields_autoplaced':
                label.fields_autoplaced = True
            elif i_type == 'at':
                label.pos_x, label.pos_y, label.ang = _get_at(items, c+2, 'global_label')
            elif i_type == 'effects':
                label.effects = FontEffects.parse(i)
            elif i_type == 'uuid':
                label.uuid = _get_uuid(items, c+2, 'global_label')
            elif i_type == 'property':
                label.properties.append(SchematicFieldV6.parse(i))
            else:
                raise SchError('Unknown label attribute `{}`'.format(i))
        return label

    def write(self):
        data = [self.text,
                _symbol('shape', [Symbol(self.shape)]),
                _symbol('at', [self.pos_x, self.pos_y, self.ang])]
        if self.fields_autoplaced:
            data.append(_symbol('fields_autoplaced', []))
        data.extend([Sep(), self.effects.write(), Sep(), _symbol('uuid', [Symbol(self.uuid)]), Sep()])
        for p in self.properties:
            data.extend([p.write(), Sep()])
        return _symbol('global_label', data)


class HierarchicalLabel(object):
    @staticmethod
    def parse(items):
        name = 'hierarchical_label'
        _check_len_total(items, 6, name)
        label = HierarchicalLabel()
        label.text = _check_str(items, 1, name)
        label.shape = _check_symbol(items[2], 1, 'shape')
        label.pos_x, label.pos_y, label.ang = _get_at(items, 3, name)
        label.effects = _get_effects(items, 4, name)
        label.uuid = _get_uuid(items, 5, name)
        return label

    def write(self):
        data = [self.text,
                _symbol('shape', [Symbol(self.shape)]),
                _symbol('at', [self.pos_x, self.pos_y, self.ang]), Sep(),
                self.effects.write(), Sep(),
                _symbol('uuid', [Symbol(self.uuid)]), Sep()]
        return _symbol('hierarchical_label', data)


class HSPin(object):
    """ Hierarchical Sheet Pin """
    # TODO base class with HierarchicalLabel
    @staticmethod
    def parse(items):
        name = 'hierarchical sheet pin'
        _check_len_total(items, 6, name)
        pin = HSPin()
        pin.name = _check_str(items, 1, name+' name')
        pin.type = _check_symbol(items, 2, name+' type')
        pin.pos_x, pin.pos_y, pin.ang = _get_at(items, 3, name)
        pin.effects = _get_effects(items, 4, name)
        pin.uuid = _get_uuid(items, 5, name)
        return pin

    def write(self):
        data = [self.name,
                Symbol(self.type),
                _symbol('at', [self.pos_x, self.pos_y, self.ang]), Sep(),
                self.effects.write(), Sep(),
                _symbol('uuid', [Symbol(self.uuid)]), Sep()]
        return _symbol('pin', data)


class Sheet(object):
    def __init__(self):
        super().__init__()
        self.pos_x = self.pos_y = self.ang = 0
        self.w = self.h = 0
        self.fields_autoplaced = False
        self.stroke = self.fill = self.uuid = None
        self.properties = []
        self.name = self.file = ''
        self.pins = []
        self.sch = None

    @staticmethod
    def parse(items):
        sheet = Sheet()
        for c, i in enumerate(items[1:]):
            i_type = _check_is_symbol_list(i)
            if i_type == 'at':
                sheet.pos_x, sheet.pos_y, sheet.ang = _get_at(items, c+1, 'sheet')
            elif i_type == 'size':
                sheet.w = _check_float(i, 1, 'sheet width')
                sheet.h = _check_float(i, 2, 'sheet height')
            elif i_type == 'fields_autoplaced':
                sheet.fields_autoplaced = True
            elif i_type == 'stroke':
                sheet.stroke = Stroke.parse(i)
            elif i_type == 'fill':
                sheet.fill = Fill.parse(i)
            elif i_type == 'uuid':
                sheet.uuid = _get_uuid(items, c+1, 'sheet')
            elif i_type == 'property':
                field = SchematicFieldV6.parse(i)
                sheet.properties.append(field)
                if field.name == 'Sheet name':
                    sheet.name = field.value
                elif field.name == 'Sheet file':
                    sheet.file = field.value
                else:
                    logger.warning(W_UNKFLD+"Unknown sheet property `{}` ({})".format(field.name, field.value))
            elif i_type == 'pin':
                sheet.pins.append(HSPin.parse(i))
            else:
                raise SchError('Unknown sheet attribute `{}`'.format(i))
        return sheet

    def load_sheet(self, project, parent_file, parent_obj):
        assert self.name
        sheet = SchematicV6()
        self.sheet = sheet
        parent_dir = os.path.dirname(parent_file)
        sheet.sheet_path = os.path.join(parent_obj.sheet_path, self.uuid)
        sheet.sheet_path_h = os.path.join(parent_obj.sheet_path_h, self.name)
        parent_obj.sheet_paths[sheet.sheet_path] = sheet
        sheet.load(os.path.join(parent_dir, self.file), project, parent_obj)
        return sheet

    def write(self, cross=False):
        data = [_symbol('at', [self.pos_x, self.pos_y]),
                _symbol('size', [self.w, self.h])]
        if self.fields_autoplaced:
            data.append(_symbol('fields_autoplaced', []))
        data.extend([Sep(), self.stroke.write(), Sep(),
                    self.fill.write(), Sep(),
                    _symbol('uuid', [Symbol(self.uuid)]), Sep()])
        for p in self.properties:
            change_file = cross and p.name == 'Sheet file'
            if change_file:
                p.value = self.flat_file
            data.extend([p.write(), Sep()])
            if change_file:
                p.value = self.file
        for p in self.pins:
            data.extend([p.write(), Sep()])
        return _symbol('sheet', data)


class SheetInstance(object):
    @staticmethod
    def parse(items):
        name = 'sheet instance'
        instances = []
        for c, i in enumerate(items[1:]):
            v = _check_symbol_value(items, c+1, name, 'path')
            instance = SheetInstance()
            instance.path = _check_str(v, 1, name+' path')
            instance.page = _check_symbol_str(v, 2, name, 'page')
            instances.append(instance)
        return instances

    def write(self):
        return _symbol('path', [self.path, _symbol('page', [self.page])])


class SymbolInstance(object):
    @staticmethod
    def parse(items):
        name = 'symbol instance'
        instances = []
        for c, i in enumerate(items[1:]):
            v = _check_symbol_value(items, c+1, name, 'path')
            instance = SymbolInstance()
            instance.path = _check_str(v, 1, name+' path')
            instance.reference = _check_symbol_str(v, 2, name, 'reference')
            instance.unit = _check_symbol_int(v, 3, name, 'unit')
            instance.value = _check_symbol_str(v, 4, name, 'value')
            instance.footprint = _check_symbol_str(v, 5, name, 'footprint')
            instances.append(instance)
        return instances

    def write(self):
        data = [self.path, Sep(),
                _symbol('reference', [self.reference]),
                _symbol('unit', [self.unit]),
                _symbol('value', [self.value]),
                _symbol('footprint', [self.footprint]), Sep()]
        return _symbol('path', data)


# Here because we have al s-expr tools here
class PCBLayer(object):
    def __init__(self):
        super().__init__()
        self.name = ''
        self.type = ''
        self.color = None
        self.thickness = None
        self.material = None
        self.epsilon_r = None
        self.loss_tangent = None

    @staticmethod
    def parse(items):
        name = 'PCB stackup layer'
        layer = PCBLayer()
        layer.name = _check_str(items, 1, name)
        for c, i in enumerate(items[2:]):
            i_type = _check_is_symbol_list(i)
            tname = name+' '+i_type
            if i_type == 'type':
                layer.type = _check_str(i, 1, tname)
            elif i_type == 'color':
                layer.color = _check_str(i, 1, tname)
            elif i_type == 'thickness':
                layer.thickness = _check_float(i, 1, tname)*1000
            elif i_type == 'material':
                layer.material = _check_str(i, 1, tname)
            elif i_type == 'epsilon_r':
                layer.epsilon_r = _check_float(i, 1, tname)
            elif i_type == 'loss_tangent':
                layer.loss_tangent = _check_float(i, 1, tname)
            else:
                logger.warning('Unknown layer attribute `{}`'.format(i))
        return layer


def _symbol(name, content):
    return [Symbol(name)] + content


def _add_items(items, sch, sep=False, cross=False, pre_sep=True):
    if len(items):
        if pre_sep:
            sch.append(Sep())
        for i in items:
            if cross:
                sch.append(i.write(cross=True))
            else:
                sch.append(i.write())
            sch.append(Sep())
            if sep:
                sch.append(Sep())
        if sep:
            sch.pop()


def _add_items_list(name, items, sch):
    if not len(items):
        return
    data = [Sep()]
    for s in items:
        data.append(s.write())
        data.append(Sep())
    sch.extend([Sep(), _symbol(name, data), Sep()])


class SchematicV6(Schematic):
    def __init__(self):
        super().__init__()
        self.annotation_error = False
        # The title block is optional
        self.date = self.title = self.revision = self.company = ''
        self.comment = ['']*9
        self.max_comments = 9
        self.title_ori = self.date_ori = None
        self.netlist_version = 'E'

    def _fill_missing_title_block(self):
        # Fill in some missing info
        self.date = GS.format_date(self.date, self.fname, 'SCH')
        if not self.title:
            self.title = os.path.splitext(os.path.basename(self.fname))[0]

    def _get_title_block(self, items):
        if not isinstance(items, list):
            raise SchError('The title block is not a list')
        for item in items:
            if not isinstance(item, list) or len(item) < 2 or not isinstance(item[0], Symbol):
                raise SchError('Wrong title block entry ({})'.format(item))
            i_type = item[0].value()
            if i_type == 'title':
                self.title_ori = self.title = _check_str(item, 1, i_type)
            elif i_type == 'date':
                self.date_ori = self.date = _check_str(item, 1, i_type)
            elif i_type == 'rev':
                self.revision = _check_str(item, 1, i_type)
            elif i_type == 'company':
                self.company = _check_str(item, 1, i_type)
            elif i_type == 'comment':
                index = _check_integer(item, 1, i_type)
                if index < 1 or index > 9:
                    raise SchError('Unsupported comment index {} in title block'.format(index))
                value = _check_str(item, 2, i_type)
                self.comment[index-1] = value
            else:
                raise SchError('Unsupported entry in title block ({})'.format(item))
        self._fill_missing_title_block()
        logger.debug("SCH title: `{}`".format(self.title))
        logger.debug("SCH date: `{}`".format(self.date))
        logger.debug("SCH revision: `{}`".format(self.revision))
        logger.debug("SCH company: `{}`".format(self.company))

    def _get_lib_symbols(self, comps):
        if not isinstance(comps, list):
            raise SchError('The lib symbols is not a list')
        for c in comps[1:]:
            obj = LibComponent.load(c, self.project)
            self.lib_symbols.append(obj)
            self.lib_symbol_names[obj.lib_id] = obj

    def path_to_human(self, path):
        """ Converts a UUID path into something we can read """
        if path == '/':
            return path
        res = self.sheet_names[path]
        return res

    def write_paper(self):
        paper_data = [self.paper]
        if self.paper == "User":
            paper_data.extend([self.paper_w, self.paper_h])
        if self.paper_orientation is not None:
            paper_data.append(Symbol(self.paper_orientation))
        return [Sep(), Sep(), _symbol('paper', paper_data)]

    def write_title_block(self):
        data = [Sep()]
        data += [_symbol('title', [self.title_ori]), Sep()]
        data += [_symbol('date', [self.date_ori]), Sep()]
        data += [_symbol('rev', [self.revision]), Sep()]
        data += [_symbol('company', [self.company]), Sep()]
        for num, val in enumerate(self.comment):
            data += [_symbol('comment', [num+1, val]), Sep()]
        return [Sep(), Sep(), _symbol('title_block', data)]

    def write_lib_symbols(self, cross=False):
        data = [Sep()]
        for s in self.lib_symbols:
            data.extend([s.write(), Sep()])
            if cross:
                data.extend([s.write(cross), Sep()])
        return [Sep(), Sep(), _symbol('lib_symbols', data), Sep()]

    def save(self, fname, dest_dir):
        cross = True
        fname = os.path.join(dest_dir, fname)
        sch = [Symbol('kicad_sch')]
        sch.append(_symbol('version', [self.version]))
        sch.append(_symbol('generator', [Symbol(self.generator)]))
        sch.append(Sep())
        sch.append(Sep())
        sch.append(_symbol('uuid', [Symbol(self.uuid)]))
        sch.extend(self.write_paper())
        if self.title_ori is not None:
            sch.extend(self.write_title_block())
        sch.extend(self.write_lib_symbols(cross))
        # Bus aliases
        _add_items(self.bus_alias, sch)
        # Connections (aka Junctions)
        _add_items(self.junctions, sch, pre_sep=(len(self.bus_alias) == 0))
        # No connect
        _add_items(self.no_conn, sch)
        # Bus entry
        _add_items(self.bus_entry, sch)
        # Lines (wire, bus and polyline)
        if self.wires:
            old_type = 'none'
            for e in self.wires:
                if e.type != old_type and old_type != 'wire':
                    sch.append(Sep())
                sch.append(e.write())
                old_type = e.type
                sch.append(Sep())
        # Images
        _add_items(self.bitmaps, sch)
        # Texts
        _add_items(self.texts, sch)
        # Labels
        _add_items(self.labels, sch)
        # Global Labels
        _add_items(self.glabels, sch)
        # Hierarchical Labels
        _add_items(self.hlabels, sch)
        # Symbols
        _add_items(self.symbols, sch, sep=True, cross=cross)
        # Sheets
        _add_items(self.sheets, sch, sep=True, cross=cross)
        # Sheet instances
        _add_items_list('sheet_instances', self.sheet_instances, sch)
        # Symbol instances
        _add_items_list('symbol_instances', self.symbol_instances, sch)
        with open(fname, 'wt') as f:
            f.write(dumps(sch))
            f.write('\n')
        for sch in self.sheets:
            if sch.sch:
                sch.sch.save(sch.flat_file if cross else sch.file, dest_dir)

    def save_variant(self, dest_dir):
        fname = os.path.basename(self.fname)
        self.save(fname, dest_dir)
        return fname

    def _create_flat_name(self, sch):
        """ Create a unique name that doesn't contain subdirs.
            Is used to save a variant, where we avoid sharing instance data """
        # Store it in the UUID -> name
        # Used to create a human readable sheet path
        self.sheet_names[os.path.join(self.sheet_path, sch.uuid)] = os.path.join(self.sheet_path_h, sch.name)
        # Eliminate subdirs
        file = sch.file.replace('/', '_')
        fparts = os.path.splitext(file)
        sch.flat_file = fparts[0]+'_'+str(len(self.sheet_names))+fparts[1]

    def load(self, fname, project, parent=None):  # noqa: C901
        """ Load a v6.x KiCad Schematic.
            The caller must be sure the file exists.
            Only the schematics are loaded not the libs. """
        logger.debug("Loading sheet from "+fname)
        if parent is None:
            self.fields = ['part']
            self.fields_lc = set(self.fields)
            self.sheet_paths = {'/': self}
            self.lib_symbol_names = {}
            self.sheet_path = '/'
            self.sheet_path_h = '/'
            self.sheet_names = {}
        else:
            self.fields = parent.fields
            self.fields_lc = parent.fields_lc
            self.sheet_paths = parent.sheet_paths
            self.lib_symbol_names = parent.lib_symbol_names
            self.sheet_names = parent.sheet_names
            # self.sheet_path is set by sch.load_sheet
        self.parent = parent
        self.fname = fname
        self.project = project
        self.lib_symbols = []
        self.symbols = []
        self.components = []
        self.junctions = []  # Connect
        self.no_conn = []
        self.bus_entry = []
        self.wires = []
        self.bitmaps = []
        self.texts = []
        self.labels = []
        self.glabels = []
        self.hlabels = []
        self.sheets = []
        self.sheet_instances = []
        self.symbol_instances = []
        self.bus_alias = []
        self.libs = {}  # Just for compatibility with v5 class
        # TODO: this assumes we are expanding the schematic to allow variant.
        # This is needed to overcome KiCad 6 limitations (symbol instances only differ in Reference)
        # If we don't want to expand the schematic this member should be shared with the parent
        # TODO: We must fix some UUIDs because now we expanded them.
        self.symbol_uuids = {}
        with open(fname, 'rt') as fh:
            error = None
            try:
                sch = load(fh)[0]
            except SExpData as exception:
                error = str(exception)
            if error:
                raise SchError(error)
        if not isinstance(sch, list) or sch[0].value() != 'kicad_sch':
            raise SchError('No kicad_sch signature')
        for e in sch[1:]:
            e_type = _check_is_symbol_list(e)
            obj = None
            if e_type == 'version':
                self.version = _check_integer(e, 1, e_type)
            elif e_type == 'generator':
                self.generator = _check_symbol(e, 1, e_type)
            elif e_type == 'uuid':
                self.id = self.uuid = _check_symbol(e, 1, e_type)
            elif e_type == 'paper':
                self.paper = _check_str(e, 1, e_type)
                index = 2
                if self.paper == "User":
                    self.paper_w = _check_float(e, 2, 'paper width')
                    self.paper_h = _check_float(e, 3, 'paper height')
                    index += 2
                if len(e) > index:
                    self.paper_orientation = _check_symbol(e, index, 'paper orientation')
                else:
                    self.paper_orientation = None
            elif e_type == 'title_block':
                self._get_title_block(e[1:])
            elif e_type == 'lib_symbols':
                self._get_lib_symbols(e)
            elif e_type == 'bus_alias':
                self.bus_alias.append(BusAlias.parse(e))
            elif e_type == 'junction':
                self.junctions.append(Junction.parse(e))
            elif e_type == 'no_connect':
                self.no_conn.append(NoConnect.parse(e))
            elif e_type == 'bus_entry':
                self.bus_entry.append(BusEntry.parse(e))
            elif e_type == 'bus' or e_type == 'wire' or e_type == 'polyline':
                self.wires.append(SchematicWireV6.parse(e, e_type))
            elif e_type == 'image':
                self.bitmaps.append(SchematicBitmapV6.parse(e))
            elif e_type == 'text':
                self.texts.append(Text.parse(e, e_type))
            elif e_type == 'label':
                self.labels.append(Text.parse(e, e_type))
            elif e_type == 'global_label':
                self.glabels.append(GlobalLabel.parse(e))
            elif e_type == 'hierarchical_label':
                self.hlabels.append(HierarchicalLabel.parse(e))
            elif e_type == 'symbol':
                obj = SchematicComponentV6.load(e, self.project, self)
                if obj.annotation_error:
                    self.annotation_error = True
                self.symbols.append(obj)
                self.symbol_uuids[obj.uuid] = obj
            elif e_type == 'sheet':
                obj = Sheet.parse(e)
                self.sheets.append(obj)
                self._create_flat_name(obj)
            elif e_type == 'sheet_instances':
                self.sheet_instances = SheetInstance.parse(e)
            elif e_type == 'symbol_instances':
                self.symbol_instances = SymbolInstance.parse(e)
            else:
                raise SchError('Unknown kicad_sch attribute `{}`'.format(e))
        if not self.title:
            self._fill_missing_title_block()
        # Load sub-sheets
        for sch in self.sheets:
            sheet = sch.load_sheet(project, fname, self)
            if sheet.annotation_error:
                self.annotation_error = True
            sch.sch = sheet
        # Assign the page numbers
        if parent is None:
            self.all_sheets = []
            for i in self.sheet_instances:
                sheet = self.sheet_paths.get(i.path)
                if sheet:
                    sheet.sheet = i.page
                    self.all_sheets.append(sheet)
        # Create the components list
        for s in self.symbol_instances:
            # Get a copy of the original symbol
            path = os.path.dirname(s.path)
            sheet = self.sheet_paths[path]
            comp_uuid = os.path.basename(s.path)
            comp = sheet.symbol_uuids[comp_uuid]
            # Transfer the instance data
            comp.set_ref(s.reference)
            comp.unit = s.unit
            comp.value = s.value
            comp.set_footprint(s.footprint)
            comp.sheet_path = path
            comp.sheet_path_h = self.path_to_human(path)
            comp.id = comp_uuid
            # Link with its library symbol
            try:
                lib_symbol = self.lib_symbol_names[comp.lib_id]
            except KeyError:
                logger.warning(W_MISSCMP+'Missing component `{}`'.format(comp.lib_id))
                lib_symbol = LibComponent()
            comp.lib_symbol = lib_symbol
            comp.is_power = lib_symbol.is_power
            comp.desc = lib_symbol.get_field_value('ki_description')
            # Now we have all the data
            comp._validate()
            # Add it to the list
            self.components.append(comp)
        self.comps_data = self.lib_symbol_names
