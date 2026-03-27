# -*- coding: utf-8 -*-
# Copyright (c) 2021-2026 Salvador E. Tropea
# Copyright (c) 2021-2026 Instituto Nacional de Tecnología Industrial
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)
"""
KiCad v6/7/8/9/10 Schematic format.
A basic implementation of the .kicad_sch file format.
Currently oriented to collect the components for the BoM and create a variant of the SCH
Documentation: https://dev-docs.kicad.org/en/file-formats/sexpr-schematic/
"""
import base64
from collections import OrderedDict
from copy import deepcopy
import os
import re
from ..gs import GS
from .. import log
from ..misc import W_NOLIB, W_UNKFLD, W_MISSCMP, W_FIELDCONF, EMBED_PREFIX, DONT_STOP, update_dict, W_UUIDSCHISSUE
from .error import SchError
from .sexpdata import load, SExpData, Symbol, dumps, Sep
from .sexp_helpers import (_check_is_symbol_list, _check_len, _check_len_total, _check_symbol, _check_hide, _check_integer,
                           _check_float, _check_str, _check_symbol_value, _check_symbol_float, _check_symbol_int,
                           _check_symbol_str, _get_offset, _get_yes_no, _get_at, _get_size, _get_xy, _get_points,
                           _check_relaxed, Color, _symbol, _check_floats, _get_yes_no_maybe_alone)
from .v5_sch import SchematicComponent, Schematic

logger = log.get_logger()
CROSSED_LIB = 'kibot_crossed'
NO_YES = [Symbol('no'), Symbol('yes')]
version = None
KICAD_7_VER = 20230121
KICAD_8_VER = 20231120
KICAD_10_VER = 20260101
SHEET_FILE = {'Sheet file', 'Sheetfile'}
SHEET_NAME = {'Sheet name', 'Sheetname'}


def path_join(*args):
    # We use os.path.join because it can handle things like xxxx//yyyyy
    res = os.path.join(*args)
    if os.sep != '/':
        # Avoid getting \ on Windows
        res = res.replace(os.sep, '/')
    return res


class UUID_Validator(object):
    known_UUIDs = set()

    def reset():
        UUID_Validator.known_UUIDs = set()

    # TODO: Accept "None"?
    def validate(uuid):
        no_collision = True
        if uuid in UUID_Validator.known_UUIDs:
            # logger.error(f"Collision {uuid}")
            uuid_comps = uuid.split('-')
            assert len(uuid_comps) == 5 and len(uuid_comps[0]) == 8
            variable = int(uuid_comps[0], 16)+1
            uuid = "{0:08x}".format(variable % 0x100000000)+'-'+'-'.join(uuid_comps[1:])
            # Solve collision
            while uuid in UUID_Validator.known_UUIDs:
                variable = variable + 1
                uuid = "{0:08x}".format(variable % 0x100000000)+'-'+'-'.join(uuid_comps[1:])
            # logger.error(f"New UUID {uuid}")
            no_collision = False
        UUID_Validator.known_UUIDs.add(uuid)
        # logger.warning(f"Adding {uuid}")
        return uuid, no_collision


def find_our_project(obj, default, exp_hierarchy):
    """ Look for a project containing our instance """
    if not exp_hierarchy:
        return default
    # The name of the project isn't really important, in fact is useless
    # So we can't trust its value
    for prj, ins in obj.projects:
        for i in ins:
            if i.path == obj.p_path_ori:
                return prj
    raise SchError('Missing project containing `{}`'.format(obj.p_path_ori))


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
        self.color = None
        self.href = None
        self.face = None

    @staticmethod
    def parse_font(items):
        w = h = 1.27
        thickness = color = face = None
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
                elif i_type == 'color':
                    color = Color.parse(i)
                elif i_type == 'face':
                    face = _check_str(i, 1, 'font face')
                elif i_type == 'bold':
                    bold = _get_yes_no(i, 1, i_type)
                elif i_type == 'italic':
                    italic = _get_yes_no(i, 1, i_type)
                else:
                    raise SchError('Unknown font effect attribute `{}`'.format(i))
        return w, h, thickness, bold, italic, color, face

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
                    o.w, o.h, o.thickness, o.bold, o.italic, o.color, o.face = FontEffects.parse_font(i)
                elif i_type == 'justify':
                    o.hjustify, o.vjustify, o.mirror = FontEffects.parse_justify(i)
                elif i_type == 'href':
                    o.href = _check_str(i, 1, 'font effect')
                elif i_type == 'hide':
                    o.hide = _get_yes_no(i, 1, i_type)
                else:
                    raise SchError('Unknown font effect attribute `{}`'.format(i))
        return o

    def write_font(self):
        data = []
        if self.face is not None:
            data.append(_symbol('face', [self.face]))
        data.append(_symbol('size', [self.h, self.w]))
        if self.thickness is not None:
            data.append(_symbol('thickness', [self.thickness]))
        if version < KICAD_8_VER:
            if self.bold:
                data.append(Symbol('bold'))
            if self.italic:
                data.append(Symbol('italic'))
        else:
            if self.bold:
                data.append(_symbol_yn('bold', self.bold))
            if self.italic:
                data.append(_symbol_yn('italic', self.italic))
        if self.color is not None:
            data.append(self.color.write())
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
            if version < KICAD_8_VER:
                data.append(Symbol('hide'))
            else:
                data.append(_symbol_yn('hide', self.hide))
        if self.href is not None:
            data.append(_symbol('href', [self.href]))
        return _symbol('effects', data)


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
        c = self.color
        if version < KICAD_7_VER or c.r+c.g+c.b+c.a != 0:
            data.append(c.write())
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
        self.uuid = None

    @staticmethod
    def parse(items):
        arc = DrawArcV6()
        for c, i in enumerate(items[1:]):
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
            elif i_type == 'uuid':
                arc.uuid = get_uuid(items, c+1, 'arc')
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
        add_uuid(data, self.uuid)
        return _symbol('arc', data)


class DrawCircleV6(object):
    def __init__(self):
        super().__init__()
        self.center = None
        self.radius = 0
        self.stroke = None
        self.fill = None
        self.uuid = None

    @staticmethod
    def parse(items):
        circle = DrawCircleV6()
        for c, i in enumerate(items[1:]):
            i_type = _check_is_symbol_list(i)
            if i_type == 'center':
                circle.center = _get_xy(i)
            elif i_type == 'radius':
                circle.radius = _check_float(i, 1, 'circle radius')
            elif i_type == 'stroke':
                circle.stroke = Stroke.parse(i)
            elif i_type == 'fill':
                circle.fill = Fill.parse(i)
            elif i_type == 'uuid':
                circle.uuid = get_uuid(items, c+1, 'circle')
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
        add_uuid(data, self.uuid)
        return _symbol('circle', data)


class DrawRectangleV6(object):
    def __init__(self):
        super().__init__()
        self.start = None
        self.end = None
        self.stroke = None
        self.fill = None
        self.uuid = None

    @staticmethod
    def parse(items):
        rectangle = DrawRectangleV6()
        for c, i in enumerate(items[1:]):
            i_type = _check_is_symbol_list(i)
            if i_type == 'start':
                rectangle.start = _get_xy(i)
            elif i_type == 'end':
                rectangle.end = _get_xy(i)
            elif i_type == 'stroke':
                rectangle.stroke = Stroke.parse(i)
            elif i_type == 'fill':
                rectangle.fill = Fill.parse(i)
            elif i_type == 'uuid':
                rectangle.uuid = get_uuid(items, c+1, 'rectangle')
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
        add_uuid(data, self.uuid)
        return _symbol('rectangle', data)


class DrawCurve(object):
    """ Qubic Bezier """
    def __init__(self):
        super().__init__()
        self.points = []
        self.stroke = None
        self.fill = None
        self.uuid = None

    @staticmethod
    def parse(items):
        curve = DrawCurve()
        for c, i in enumerate(items[1:]):
            i_type = _check_is_symbol_list(i)
            if i_type == 'pts':
                curve.points = _get_points(i)
            elif i_type == 'stroke':
                curve.stroke = Stroke.parse(i)
            elif i_type == 'fill':
                curve.fill = Fill.parse(i)
            elif i_type == 'uuid':
                curve.uuid = get_uuid(items, c+1, 'bezier')
            else:
                raise SchError('Unknown curve attribute `{}`'.format(i))
        curve.box = Box(curve.points)
        return curve

    def write(self):
        points = [Sep()]
        for p in self.points:
            points.append(_symbol('xy', [p.x, p.y]))
            points.append(Sep())
        data = [Sep(), _symbol('pts', points), Sep()]
        data.extend([self.stroke.write(), Sep()])
        data.extend([self.fill.write(), Sep()])
        add_uuid(data, self.uuid)
        return _symbol('bezier', data)


class DrawPolyLine(object):
    def __init__(self):
        super().__init__()
        self.points = []
        self.stroke = None
        self.fill = None
        self.uuid = None

    @staticmethod
    def parse(items):
        line = DrawPolyLine()
        for c, i in enumerate(items[1:]):
            i_type = _check_is_symbol_list(i)
            if i_type == 'pts':
                line.points = _get_points(i)
            elif i_type == 'stroke':
                line.stroke = Stroke.parse(i)
            elif i_type == 'fill':
                line.fill = Fill.parse(i)
            elif i_type == 'uuid':
                line.uuid = get_uuid(items, c+1, 'polyline')
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
        add_uuid(data, self.uuid)
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


class PinAlternate(object):
    def __init__(self):
        super().__init__()

    @staticmethod
    def parse(items):
        alt = PinAlternate()
        name = 'alternate'
        alt.name = _check_str(items, 1, name+' name')
        alt.type = _check_symbol(items, 2, name+' type')
        alt.gtype = _check_symbol(items, 3, name+' style')
        return alt

    def write(self):
        return _symbol('alternate', [self.name, Symbol(self.type), Symbol(self.gtype)])


def _get_alternate(items, pos, name):
    values = _check_symbol_value(items, pos, name, 'alternate')
    return PinAlternate.parse(values)


class PinV6(object):
    def __init__(self):
        super().__init__()
        self.type = self.gtype = self.name = self.number = ''
        self.pos_x = self.pos_y = self.ang = self.len = 0
        self.name_effects = self.number_effects = None
        self.hide = False
        self.box = Box()
        self.alternate = None

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
            elif i_type == 'alternate':
                # Not documented yet
                pin.alternate = _get_alternate(items, c+3, name)
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
        if self.alternate:
            data.extend([self.alternate.write(), Sep()])
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
        self.effects = FontEffects()
        self.do_not_autoplace = False
        self.show_name = False
        self.private = False
        # KiCad 10 moved it from the "effects"
        self.hide = None

    def visible(self, v):
        self.effects.hide = not v

    def is_visible(self):
        return not self.effects.hide

    def get_height(self):
        """ Font height in mm """
        return self.effects.h

    def get_xy(self):
        return self.x, self.y

    def set_xy(self, x, y, hjustify=None):
        self.x = x
        self.y = y
        if hjustify:
            self.effects.hjustify = hjustify

    @staticmethod
    def parse(items, number):
        field = SchematicFieldV6()
        name = 'field'
        offset = 0
        # KiCad 9 and the never ending story: tons of things went from loose symbols to real attributes,
        # but here a new one is introduced ... and before the important data. OMG!!!
        if isinstance(items[1], Symbol):
            assert items[1].value() == 'private', items[1].value()
            offset = 1
            field.private = True
        field.name = _check_str(items, offset+1, name+' name')
        field.value = _check_str(items, offset+2, name+' value')
        # Default values
        field.number = number
        field.effects = None
        found_at = False
        for c, i in enumerate(items[offset+3:]):
            i_type = _check_is_symbol_list(i)
            if i_type == 'at':
                field.x, field.y, field.ang = _get_at(items, c+offset+3, name)
                found_at = True
            elif i_type == 'effects':
                field.effects = FontEffects.parse(i)
            elif i_type == 'id':
                field.number = _check_integer(i, 1, name+' id')
            elif i_type == 'do_not_autoplace':
                field.do_not_autoplace = _get_yes_no_maybe_alone(i, 1, i_type)
            elif i_type == 'show_name':
                field.show_name = _get_yes_no_maybe_alone(i, 1, i_type)
            elif i_type == 'hide':
                field.hide = _get_yes_no(i, 1, i_type)
            else:
                raise SchError('Unknown property attribute `{}`'.format(i))
        if not found_at:
            raise SchError('Missing position for property `{}`'.format(field.name))
        return field

    def write(self):
        if self.number < 0:
            return None
        data = []
        if self.private:
            data.append(Symbol('private'))
        data.append(self.name)
        data.append(self.value)
        if version < KICAD_7_VER:
            # Removed in KiCad 7
            data.append(_symbol('id', [self.number]))
        data.append(_symbol('at', [self.x, self.y, self.ang]))
        if version < KICAD_10_VER:
            if self.do_not_autoplace:
                data.append(_symbol('do_not_autoplace'))
            if self.show_name:
                data.append(_symbol('show_name'))
        else:
            data.append(_symbol_yn('do_not_autoplace', self.do_not_autoplace))
            data.append(_symbol_yn('show_name', self.show_name))
            if self.hide is not None:
                # Always in this version
                data.append(_symbol_yn('hide', self.hide))
        if self.effects:
            data.extend([Sep(), self.effects.write(), Sep()])
        return _symbol('property', data)


class EmbeddedFile(object):
    @staticmethod
    def load(f):
        if not isinstance(f, list):
            raise SchError('Embedded file is not a list')
        if len(f) < 4:  # name, type, data, checksum
            raise SchError('Truncated embedded file definition (len<4)')
        file = EmbeddedFile()
        name = 'embedded file '
        # Variable list
        for c, i in enumerate(f[1:]):
            i_type = _check_is_symbol_list(i)
            if i_type == 'name':
                file.name = _check_str(i, 1, name+i_type)
            elif i_type == 'type':
                file.type = _check_symbol(i, 1, name+i_type)
            elif i_type == 'data':
                values = _check_symbol_value(f, c+1, name+i_type, i_type)
                file.data = [_check_relaxed(values, i+1, name+i_type) for i, d in enumerate(values[1:])]
            elif i_type == 'checksum':
                # MurMur Hash 3 with Seed=0xABBA2345
                # KiCad devs are really creative! Very hard to verify, useless
                file.checksum = _check_str(i, 1, name+i_type)
            else:
                raise SchError(f'Unknown embedded file attribute `{i}`')
        return file

    def write(self):
        d = []
        # KiCad 9 uses the method used by KiCad 7 images and changed in KiCad 8 ...
        for v in self.data:
            d.append(Symbol(v))
            d.append(Sep())
        data = [Sep(), _symbol('name', [self.name]),
                Sep(), _symbol('type', [Symbol(self.type)]),
                Sep(), _symbol('data', [Sep()] + d),
                Sep(), _symbol('checksum', [self.checksum]), Sep()]
        return _symbol('file', data)


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
        self.exclude_from_sim = None
        self.in_bom = True
        self.on_board = True
        self.in_pos_files = None
        self.duplicate_pin_numbers_are_jumpers = None
        self.is_power = False
        self.unit = 0
        self.unit_name = None
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
        # KiCad 9
        # WTF?!
        self.embedded_fonts = None
        self.embedded_files = []    # I.e. datasheet
        self.embedded_file_names = {}
        # KiCad 10
        self.body_styles = None

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
        field_id = 0
        # Variable list
        for i in c[2:]:
            i_type = _check_is_symbol_list(i)
            vis_obj = None
            if i_type == 'pin_numbers':
                comp.pin_numbers_hide = _check_hide(i, 1, i_type)
            elif i_type == 'body_styles':
                comp.body_styles = [v.value() for v in i[1:]]
            elif i_type == 'pin_names':
                value = _check_len(i, 1, i_type)
                index = 1
                if isinstance(value, list) and isinstance(value[0], Symbol) and value[0].value() == 'offset':
                    comp.pin_names_offset = _get_offset(i, 1, i_type)
                    index = 2
                comp.pin_names_hide = None
                try:
                    comp.pin_names_hide = _check_hide(i, index, i_type)
                except SchError:
                    # Optional
                    pass
            elif i_type == 'exclude_from_sim':
                comp.exclude_from_sim = _get_yes_no(i, 1, i_type)
            elif i_type == 'in_bom':
                comp.in_bom = _get_yes_no(i, 1, i_type)
            elif i_type == 'on_board':
                comp.on_board = _get_yes_no(i, 1, i_type)
            elif i_type == 'in_pos_files':
                comp.in_pos_files = _get_yes_no(i, 1, i_type)
            elif i_type == 'duplicate_pin_numbers_are_jumpers':
                comp.duplicate_pin_numbers_are_jumpers = _get_yes_no(i, 1, i_type)
            elif i_type == 'power':
                # Not yet documented
                comp.is_power = True
            # SYMBOL_PROPERTIES...
            elif i_type == 'property':
                field = SchematicFieldV6.parse(i, field_id)
                field_id += 1
                comp.fields.append(field)
                comp.dfields[field.name.lower()] = field
            # GRAPHIC_ITEMS...
            elif i_type == 'arc':
                vis_obj = DrawArcV6.parse(i)
                comp.draw.append(vis_obj)
            elif i_type == 'circle':
                vis_obj = DrawCircleV6.parse(i)
                comp.draw.append(vis_obj)
            elif i_type == 'bezier':
                # Wrongly documented, not implemented in the GUI 2022/06/10
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
            elif i_type == 'text_box':
                comp.draw.append(TextBox.parse(i, i_type))
            elif i_type == 'embedded_fonts':  # KiCad 9
                # Fonts in a lib component?!
                comp.embedded_fonts = _get_yes_no(i, 1, i_type)
            elif i_type == 'embedded_files':  # KiCad 9
                comp._get_embedded_files(i)
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
            # UNIT_NAMES...
            elif i_type == 'unit_name':
                # Units can have custom labels
                # The format is not documented but as of V7 is:
                # (unit_name "<NAME>")
                comp.unit_name = i[1]
            else:
                raise SchError('Unknown symbol attribute `{}`'.format(i))
            if vis_obj:
                comp.box.union(vis_obj.box)
        return comp

    def _get_embedded_files(self, files):
        if not isinstance(files, list):
            raise SchError('The embedded files is not a list')
        for f in files[1:]:
            obj = EmbeddedFile.load(f)
            self.embedded_files.append(obj)
            self.embedded_file_names[obj.name] = obj

    def assign_crosses(self):
        """ Compute the box for the crossed components """
        name0 = self.name+"_0"
        # Compute the full box for each unit
        for c in range(self.unit_count):
            name = self.name+"_"+str(c+1)
            box = Box()
            units_with_graphs = []
            unit_without_graphs = None
            for unit in self.units:
                # Unit 0 is part of unit 1
                if unit.name.startswith(name) or (c == 0 and unit.name.startswith(name0)):
                    box.union(unit.box)
                    if len(unit.draw):
                        # We can have more than one drawing. This is used for the alternative version
                        units_with_graphs.append(unit)
                    else:
                        unit_without_graphs = unit
            if units_with_graphs:
                for u in units_with_graphs:
                    u.cross_box = box
            elif unit_without_graphs is not None and GS.global_cross_no_body:
                unit_without_graphs.cross_box = box
            # Note: if unit_without_graphs is None is because we are inside a unit and it doesn't have a sub-unit

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

    def write(s, cross):
        lib_id = s.lib_id
        if cross:
            # Fill the cross_box of our sub/units
            s.assign_crosses()
            if s.units:
                # Use an alternative name
                lib_id = CROSSED_LIB+':'+s.name
        sdata = [lib_id]
        if s.body_styles:
            sdata.append(_symbol('body_styles', [Symbol(v) for v in s.body_styles]))
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
        if s.units:
            if s.exclude_from_sim is not None:
                sdata.append(_symbol_yn('exclude_from_sim', s.exclude_from_sim))
            sdata.append(_symbol_yn('in_bom', s.in_bom))
            sdata.append(_symbol_yn('on_board', s.on_board))
            if s.in_pos_files is not None:
                sdata.append(_symbol_yn('in_pos_files', s.in_pos_files))
            if s.duplicate_pin_numbers_are_jumpers is not None:
                sdata.append(_symbol_yn('duplicate_pin_numbers_are_jumpers', s.duplicate_pin_numbers_are_jumpers))
        sdata.append(Sep())
        if s.unit_name is not None:
            sdata.append(_symbol('unit_name', [s.unit_name]))
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
        # Fonts
        if s.embedded_fonts is not None:
            sdata.append(_symbol_yn('embedded_fonts', s.embedded_fonts))
        # - Embedded files (here are the fonts)
        if s.embedded_files:
            files = []
            for f in s.embedded_files:
                files.append(Sep())
                files.append(f.write())
            files.append(Sep())
            sdata.extend([Sep(), _symbol('embedded_files', files), Sep()])
        return _symbol('symbol', sdata)


class Variant(object):
    """ Class used to describe a variant of a component instance """
    def __init__(self):
        super().__init__()
        self.name = None
        self.dnp = None
        self.exclude_from_sim = None
        self.in_bom = None
        self.on_board = None
        self.in_pos_files = None
        self.fields = OrderedDict()

    @staticmethod
    def parse_field(items):
        name = value = None
        nm = 'variant field '
        for i in items[1:]:
            i_type = _check_is_symbol_list(i)
            n = nm+i_type
            if i_type == 'name':
                name = _check_str(i, 1, n)
            elif i_type == 'value':
                value = _check_str(i, 1, n)
            else:
                raise SchError(f'Unknown {nm}attribute `{i}`')
        if name is None:
            raise SchError('Variant field without name')
        if value is None:
            raise SchError(f'Variant field `{name}` without value')
        return name, value

    @staticmethod
    def parse(items):
        o = Variant()
        name = 'variant '
        for i in items[1:]:
            i_type = _check_is_symbol_list(i)
            n = name+i_type
            if i_type == 'name':
                o.name = _check_str(i, 1, n)
            elif i_type == 'dnp':
                o.dnp = _get_yes_no(i, 1, n)
            elif i_type == 'exclude_from_sim':
                o.exclude_from_sim = _get_yes_no(i, 1, n)
            elif i_type == 'in_bom':
                o.in_bom = _get_yes_no(i, 1, n)
            elif i_type == 'on_board':
                o.on_board = _get_yes_no(i, 1, n)
            elif i_type == 'in_pos_files':
                o.in_pos_files = _get_yes_no(i, 1, n)
            elif i_type == 'field':
                name, value = Variant.parse_field(i)
                o.fields[name] = value
            else:
                raise SchError(f'Unknown {name}attribute `{i}`')
        if o.name is None:
            raise SchError('Variant reference without a name')
        return o

    def write(self):
        data = [_symbol('name', [self.name]), Sep()]
        if self.dnp is not None:
            data.append(_symbol_yn('dnp', self.dnp))
        if self.exclude_from_sim is not None:
            data.append(_symbol_yn('exclude_from_sim', self.exclude_from_sim))
        if self.in_bom is not None:
            data.append(_symbol_yn('in_bom', self.in_bom))
        if self.on_board is not None:
            data.append(_symbol_yn('on_board', self.on_board))
        if self.in_pos_files is not None:
            data.append(_symbol_yn('in_pos_files', self.in_pos_files))
        for name, value in self.fields.items():
            data.append(_symbol('field', [Sep(), _symbol('name', [name]), Sep(), _symbol('value', [value]), Sep()]))

        return _symbol('variant', data)

    def __repr__(self):
        str = f'{self.name}'
        if self.dnp is not None:
            str += f' dnp:{self.dnp}'
        if self.exclude_from_sim is not None:
            str += f' exclude_from_sim:{self.exclude_from_sim}'
        if self.in_bom is not None:
            str += f' in_bom:{self.in_bom}'
        if self.on_board is not None:
            str += f' on_board:{self.on_board}'
        if self.in_pos_files is not None:
            str += f' in_pos_files:{self.in_pos_files}'
        for k, v in self.fields.items():
            str += f' {k}={v}'
        return str


class SymbolInstance(object):
    def __init__(self):
        super().__init__()
        # The following two were an experiment in KiCad 6 that prove to be wrong
        self.value = None
        self.footprint = None
        # KiCad 10
        self.variants = OrderedDict()
        # Used to save a version with modified variants, i.e. converting legacy variants
        self.alt_variants = OrderedDict()

    @staticmethod
    def parse(items):
        name = 'symbol instance'
        instances = []
        for c, _ in enumerate(items[1:]):
            v = _check_symbol_value(items, c+1, name, 'path')
            instance = SymbolInstance()
            instance.path = _check_str(v, 1, name+' path')
            instance.reference = _check_symbol_str(v, 2, name, 'reference')
            instance.unit = _check_symbol_int(v, 3, name, 'unit')
            if len(v) > 4:
                for c, i in enumerate(v[4:]):
                    i_type = _check_is_symbol_list(i)
                    if i_type == 'value':
                        # KiCad 6 only
                        instance.value = _check_symbol_str(v, c+4, name, 'value')
                    elif i_type == 'footprint':
                        # KiCad 6 only
                        instance.footprint = _check_symbol_str(v, c+4, name, 'footprint')
                    elif i_type == 'variant':
                        # KiCad 10 (not documented 2026/03/06)
                        variant = Variant.parse(i)
                        instance.variants[variant.name] = variant
            instances.append(instance)
        return instances

    def write(self, alt_variants):
        # alt_variants is used to save it using an alternative set of variants, i.e. when exporting legacy variants
        data = [self.path, Sep(),
                _symbol('reference', [self.reference]),
                _symbol('unit', [self.unit])]
        if self.value is not None:
            data.append(_symbol('value', [self.value]))
        if self.footprint is not None:
            data.append(_symbol('footprint', [self.footprint]))
        variants = self.alt_variants if alt_variants else self.variants
        for v in variants.values():
            data.extend([v.write(), Sep()])
        data.append(Sep())
        return _symbol('path', data)


class SchematicComponentV6(SchematicComponent):
    def __init__(self):
        super().__init__()
        self.pins = OrderedDict()
        self.unit = 1
        self.unit_specified = False
        self.ref = None
        self.local_name = None
        self.fields_autoplaced = False
        self.mirror = None
        self.convert = None
        self.pin_alternates = {}
        self.uuid = self.uuid_ori = ''
        # KiCad v7:
        # Instances classified by project (v7)
        self.projects = None
        # All instances, by path (v7)
        self.all_instances = {}
        # v8
        self.exclude_from_sim = None
        # v10
        self.body_style = None
        self.used_variants = {}

    def set_ref(self, ref):
        self.ref = ref
        # Separate the reference in its components
        self.split_ref()
        self.set_field('Reference', ref)

    def set_value(self, value):
        self.value = value
        self.set_field('Value', value)

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
        self.set_field('Footprint', fp)

    def copy(self):
        """ Make a deep copy, but not for all """
        # Don't copy the links to projects, parent_sheet and library symbol
        projects = self.projects
        parent_sheet = self.parent_sheet
        lib_symbol = self.lib_symbol
        self.projects = self.parent_sheet = self.lib_symbol = None
        # All the rest is copied
        new_c = deepcopy(self)
        new_c.projects = self.projects = projects
        new_c.parent_sheet = self.parent_sheet = parent_sheet
        new_c.lib_symbol = self.lib_symbol = lib_symbol
        return new_c

    @staticmethod
    def get_lib_and_name(comp, i, name):
        comp.lib_id = comp.name = _check_str(i, 1, name+' lib_id')
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

    def load_pin(self, i, name):
        pin_name = _check_str(i, 1, name + 'pin name')
        pin_uuid = get_uuid(i, 2, name)
        self.pins[pin_name] = pin_uuid
        if len(i) > 3:
            # Not documented
            self.pin_alternates[pin_name] = _check_symbol_str(i, 3, name, 'alternate')

    def load_project(self, prj):
        # IMPORTANT!!! The name of the project is bogus, the only important thing is the path
        # In fact the real ID is the first component of the path
        # So we can't use it as a reliable key
        # I.e. if you edit a sheet without a project and then open it from a project ...
        name = _check_str(prj, 1, 'instance project')
        instances = SymbolInstance().parse(prj[1:])
        variants = set()
        for i in instances:
            self.all_instances[i.path] = i
            variants |= i.variants.keys()
        id = [a for a in instances[0].path.split('/') if a][0]
        return name, instances, id, variants

    def load_instances(self, i):
        self.projects = []
        for prj in i[1:]:
            i_type = _check_is_symbol_list(prj)
            if i_type != 'project':
                raise SchError('Found `{}` instead of `project` in symbol instance'.format(i_type))
            name, instances, id, variants = self.load_project(prj)
            self.projects.append((name, instances))
            self.used_variants[id] = variants

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
        field_id = 0

        # Variable list
        for i in c[1:]:
            i_type = _check_is_symbol_list(i)
            if i_type == 'lib_id':
                # First argument is the LIB:NAME
                SchematicComponentV6.get_lib_and_name(comp, i, name)
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
            elif i_type == 'mirror':
                # Not documented
                comp.mirror = _check_symbol(i, 1, name + ' mirror')
            elif i_type == 'unit':
                # This is documented as mandatory, but isn't always there
                comp.unit = _check_integer(i, 1, name+' unit')
                comp.unit_specified = True
            elif i_type == 'body_style':
                # Not documented 2026/02/23
                comp.body_style = _check_integer(i, 1, name+' '+i_type)
            elif i_type == 'convert':
                # Not documented 2022/04/17
                comp.convert = _check_integer(i, 1, name+' convert')
            elif i_type == 'exclude_from_sim':
                comp.exclude_from_sim = _get_yes_no(i, 1, i_type)
            elif i_type == 'in_bom':
                comp.in_bom = _get_yes_no(i, 1, i_type)
            elif i_type == 'on_board':
                comp.on_board = _get_yes_no(i, 1, i_type)
            elif i_type == 'in_pos_files':
                comp.in_pos_files = _get_yes_no(i, 1, i_type)
            elif i_type == 'duplicate_pin_numbers_are_jumpers':
                comp.duplicate_pin_numbers_are_jumpers = _get_yes_no(i, 1, i_type)
            elif i_type == 'dnp':
                comp.kicad_dnp = _get_yes_no(i, 1, i_type)
            elif i_type == 'fields_autoplaced':
                # Not documented
                comp.fields_autoplaced = True
            elif i_type == 'uuid':
                # Ensure we have a unique UUID
                if version < KICAD_8_VER:
                    comp.uuid_ori = _check_symbol(i, 1, name + ' uuid')
                else:
                    comp.uuid_ori = _check_str(i, 1, name + ' uuid')
                comp.uuid, _ = UUID_Validator.validate(comp.uuid_ori)
            # SYMBOL_PROPERTIES...
            elif i_type == 'property':
                field = SchematicFieldV6.parse(i, field_id)
                field_id += 1
                name_lc = field.name.lower()
                if name_lc in comp.dfields:
                    old = comp.dfields[name_lc]
                    if old.value != field.value:
                        logger.warning(W_FIELDCONF+f"Field conflict: {field.name}='{field.value}' vs {old.name}='{old.value}'"
                                       f" (in {comp.fields[0].value})")
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
                comp.load_pin(i, name)
            # KiCad v7+ instances
            elif i_type == 'instances':
                comp.load_instances(i)
                # We should get an instance for us
                p_path = parent.get_full_path()
                ins = comp.all_instances.get(p_path)
                if ins is None:
                    # This is a KiCad bug or the user editing the schematic outside a project
                    # KiCad has numerous bugs when dealing with edition outside a project or using multiple projects on
                    # the same directory
                    logger.warning(W_UUIDSCHISSUE+f"No instance for `{p_path}` using the first")
                    # We take the first, this is what KiCad silently does
                    ins = next(iter(comp.all_instances.items()))[1]
                    # And we pretend this is the correct path
                    ins_p_path = p_path
                else:
                    ins_p_path = ins.path
                comp.variants = ins.variants
                # Memorize its path (v7 style, with parent)
                comp.p_path_ori = p_path
                comp.p_path = parent.get_full_path(False)
                # Translate the instance to the v6 format (remove UUID for / and add the component UUID)
                v6_ins = SymbolInstance()
                v6_ins.path = path_join('/', '/'.join(ins_p_path.split('/')[2:]), comp.uuid_ori)
                v6_ins.reference = ins.reference
                v6_ins.unit = ins.unit
                v6_ins.variants = ins.variants
                v6_ins.alt_variants = ins.alt_variants
                # Add to the root symbol_instances, so we reconstruct it (like in a v6 file)
                parent.root_sheet.symbol_instances.append(v6_ins)
            else:
                raise SchError('Unknown component attribute `{}`'.format(i))
        if not lib_id_found or not at_found:
            raise SchError("Component missing 'lib_id' and/or 'at'")
        if not comp.uuid:
            raise SchError("No UUID for component `{}`, use KiCad to fix it".format(comp))
        # Fake 'Part' field
        field = SchematicFieldV6()
        field.name = 'part'
        field.value = comp.name
        field.number = -1
        field.effects.hide = True
        comp.add_field(field)
        # Memorize the current path, used for expanded hierarchy
        comp.path = parent.sheet_path
        return comp

    def write(self, exp_hierarchy, cross, alt_variants):
        lib_id = self.lib_id
        is_crossed = not (self.fitted or not self.included)
        native_cross = GS.ki7 and GS.global_cross_using_kicad
        dnp = False if native_cross else self.kicad_dnp
        if cross and (self.lib or self.local_name) and is_crossed:
            if native_cross:
                # Just inform KiCad we want to make it DNP
                dnp = True
            else:
                # Use an alternative name
                lib_id = CROSSED_LIB+':'+(self.local_name if self.local_name else self.name)
        data = [_symbol('lib_id', [lib_id]),
                _symbol('at', [self.x, self.y, self.ang])]
        if self.local_name is not None:
            data.insert(0, _symbol('lib_name', [self.local_name]))
        if self.mirror:
            data.append(_symbol('mirror', [Symbol(self.mirror)]))
        if self.unit_specified:
            data.append(_symbol('unit', [self.unit]))
        if self.body_style is not None:
            data.append(_symbol('body_style', [self.body_style]))
        if self.convert is not None:
            data.append(_symbol('convert', [self.convert]))
        data.append(Sep())
        if self.exclude_from_sim is not None:
            data.append(_symbol_yn('exclude_from_sim', self.exclude_from_sim))
        data.append(_symbol_yn('in_bom', self.in_bom))
        data.append(_symbol_yn('on_board', self.on_board))
        if self.in_pos_files is not None:
            data.append(_symbol_yn('in_pos_files', self.in_pos_files))
        if self.duplicate_pin_numbers_are_jumpers is not None:
            data.append(_symbol_yn('duplicate_pin_numbers_are_jumpers', self.duplicate_pin_numbers_are_jumpers))
        if dnp is not None:
            data.append(_symbol_yn('dnp', dnp))
        if self.fields_autoplaced:
            data.append(_symbol('fields_autoplaced'))
        data.append(Sep())
        add_uuid(data, self.uuid)
        for f in self.fields:
            d = f.write()
            if d:
                data.extend([d, Sep()])
        for k, v in self.pins.items():
            pin_data = [k]
            add_uuid(pin_data, v, no_sep=True)
            alternate = self.pin_alternates.get(k, None)
            if alternate:
                pin_data.append(_symbol('alternate', [alternate]))
            data.extend([_symbol('pin', pin_data), Sep()])
        if self.projects is not None:
            prj_data = [Sep()]
            prjname = find_our_project(self, self.project, exp_hierarchy)
            for prj, ins in self.projects:
                if exp_hierarchy and prj != prjname:
                    # For the expanded hierarchy we save only this project
                    continue
                ins_data = [prj, Sep()]
                for i in ins:
                    if exp_hierarchy:
                        if i.path == self.p_path_ori:
                            # Adjust the instance for the expanded hierarchy
                            i = deepcopy(i)
                            i.path = self.p_path
                        else:
                            # Don't store bogus instances
                            continue
                    ins_data.extend([i.write(alt_variants=alt_variants), Sep()])
                prj_data.extend([_symbol('project', ins_data), Sep()])
            data.extend([_symbol('instances', prj_data), Sep()])
        return _symbol('symbol', data)


def _get_uuid(items, pos, where):
    if len(items) < pos+1:
        return None
    values = _check_symbol_value(items, pos, where + ' uuid', 'uuid')
    return _check_symbol(values, 1, where + ' uuid') if version < KICAD_8_VER else _check_relaxed(values, 1, where + ' uuid')


def get_uuid(items, pos, where):
    uuid = _get_uuid(items, pos, where)
    uuid, _ = UUID_Validator.validate(uuid)
    return uuid


def add_uuid(data, uuid, no_sep=False):
    if uuid:
        uuid = uuid if version >= KICAD_8_VER else Symbol(uuid)
        if no_sep:
            data.append(_symbol('uuid', [uuid]))
        else:
            data.extend([_symbol('uuid', [uuid]), Sep()])


class Junction(object):
    @staticmethod
    def parse(items):
        if len(items) != 5:
            _check_len_total(items, 4, 'junction')
        jun = Junction()
        jun.pos_x, jun.pos_y, jun.ang = _get_at(items, 1, 'junction')
        jun.diameter = _check_symbol_float(items, 2, 'junction', 'diameter')
        jun.color = Color.parse(items[3])
        jun.uuid = get_uuid(items, 4, 'junction')
        return jun

    def write(self):
        data = [_symbol('at', [self.pos_x, self.pos_y]),
                _symbol('diameter', [self.diameter]),
                self.color.write(), Sep()]
        add_uuid(data, self.uuid)
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
        if len(items) != 3:
            _check_len_total(items, 2, 'no_connect')
        nocon = NoConnect()
        nocon.pos_x, nocon.pos_y, nocon.ang = _get_at(items, 1, 'no connect')
        nocon.uuid = get_uuid(items, 2, 'no connect')
        return nocon

    def write(self):
        data = [_symbol('at', [self.pos_x, self.pos_y])]
        add_uuid(data, self.uuid, no_sep=True)
        return _symbol('no_connect', data)


class BusEntry(object):
    @staticmethod
    def parse(items):
        if len(items) != 5:
            _check_len_total(items, 4, 'bus entry')
        buse = BusEntry()
        buse.pos_x, buse.pos_y, buse.ang = _get_at(items, 1, 'bus entry')
        buse.size = _get_size(items, 2, 'bus entry')
        buse.stroke = Stroke.parse(items[3])
        buse.uuid = get_uuid(items, 4, 'bus entry')
        return buse

    def write(self):
        data = [_symbol('at', [self.pos_x, self.pos_y]),
                _symbol('size', [self.size.x, self.size.y]), Sep(),
                self.stroke.write(), Sep()]
        add_uuid(data, self.uuid)
        return _symbol('bus_entry', data)


class SchematicWireV6(object):
    @staticmethod
    def parse(items, name):
        if len(items) != 4:
            _check_len_total(items, 3, name)
        wire = SchematicWireV6()
        wire.type = name  # wire, bus, polyline
        wire.points = _get_points(items[1])
        wire.stroke = Stroke.parse(items[2])
        wire.uuid = get_uuid(items, 3, name)
        return wire

    def write(self):
        points = [_symbol('xy', [p.x, p.y]) for p in self.points]
        data = [_symbol('pts', points), Sep(), self.stroke.write(), Sep()]
        add_uuid(data, self.uuid)
        return _symbol(self.type, data)


class SchematicBitmapV6(object):
    @staticmethod
    def parse(items):
        bmp = SchematicBitmapV6()
        bmp.pos_x, bmp.pos_y, bmp.ang = _get_at(items, 1, 'image')
        bmp.scale = None
        bmp.uuid = None
        for c, i in enumerate(items[2:]):
            i_type = _check_is_symbol_list(i)
            if i_type == 'scale':
                bmp.scale = _check_symbol_float(items, c+2, 'image', 'scale')
            elif i_type == 'uuid':
                bmp.uuid = get_uuid(items, c+2, 'image')
            elif i_type == 'data':
                values = _check_symbol_value(items, c+2, 'image data', 'data')
                # v6/7: Symbol v8: String
                bmp.data = [_check_relaxed(values, i+1, 'image data') for i, d in enumerate(values[1:])]
            else:
                raise SchError('Unknown image attribute `{}`'.format(i))
        return bmp

    def write(self):
        d = []
        if version < KICAD_8_VER:
            for v in self.data:
                d.append(Symbol(v))
                d.append(Sep())
        else:
            for v in self.data:
                d.append(v)
                d.append(Sep())
        data = [_symbol('at', [self.pos_x, self.pos_y])]
        if self.scale is not None:
            data.append(_symbol('scale', [self.scale]))
        data.append(Sep())
        add_uuid(data, self.uuid)
        data.extend([_symbol('data', [Sep()] + d), Sep()])
        return _symbol('image', data)


class Group(object):
    @staticmethod
    def parse(items):
        grp = Group()
        grp.uuid = None
        grp.members = None
        grp.lib_id = None
        name = 'group'
        grp.name = _check_str(items, 1, name)
        logger.error(items)
        for c, i in enumerate(items[2:]):
            i_type = _check_is_symbol_list(i)
            if i_type == 'members':
                grp.members = i[1:]
                logger.error(grp.members)
            elif i_type == 'uuid':
                grp.uuid = get_uuid(items, c+2, name)
            elif i_type == 'lib_id':
                grp.lib_id = _check_str(i, 1, name+' '+i_type)
            else:
                raise SchError(f'Unknown `{name}` attribute `{i}`')
        return grp

    def write(self):
        data = [self.name, Sep()]
        add_uuid(data, self.uuid)
        if self.lib_id:
            data.append(_symbol('lib_id', [self.lib_id]))
            data.append(Sep())
        if self.members:
            data.append(_symbol('members', [Sep()] + self.members))
            data.append(Sep())
        return _symbol('group', data)


class Text(object):
    @staticmethod
    def parse(items, name):
        text = Text()
        text.name = name
        text.exclude_from_sim = None
        text.text = _check_str(items, 1, name)
        for c, i in enumerate(items[2:]):
            i_type = _check_is_symbol_list(i)
            if i_type == 'at':
                text.pos_x, text.pos_y, text.ang = _get_at(items, c+2, name)
            elif i_type == 'effects':
                text.effects = _get_effects(items, c+2, name)
            elif i_type == 'uuid':
                text.uuid = get_uuid(items, c+2, name)
            elif i_type == 'exclude_from_sim':
                # KiCad 7.99
                text.exclude_from_sim = _get_yes_no(i, 1, i_type)
            else:
                raise SchError(f'Unknown {name} attribute `{i}`')
        return text

    def write(self):
        data = [self.text]
        if self.exclude_from_sim is not None:
            data.append(_symbol_yn('exclude_from_sim', self.exclude_from_sim))
        data.extend([_symbol('at', [self.pos_x, self.pos_y, self.ang]), Sep(),
                     self.effects.write(), Sep()])
        add_uuid(data, self.uuid)
        return _symbol(self.name, data)


class TextBox(object):
    @staticmethod
    def parse(items, name):
        text = TextBox()
        text.name = name
        text.exclude_from_sim = None
        text.text = _check_str(items, 1, name)
        text.uuid = None
        text.margins = None
        text.stroke = None
        text.span = None  # For table cells
        for c, i in enumerate(items[2:]):
            i_type = _check_is_symbol_list(i)
            if i_type == 'at':
                text.pos_x, text.pos_y, text.ang = _get_at(items, c+2, name)
            elif i_type == 'size':
                text.size = _get_size(items, c+2, name)
            elif i_type == 'stroke':
                text.stroke = Stroke.parse(i)
            elif i_type == 'fill':
                text.fill = Fill.parse(i)
            elif i_type == 'effects':
                text.effects = _get_effects(items, c+2, name)
            elif i_type == 'uuid':
                text.uuid = get_uuid(items, c+2, name)
            elif i_type == 'exclude_from_sim':
                # KiCad 8
                text.exclude_from_sim = _get_yes_no(i, 1, i_type)
            elif i_type == 'margins':
                # KiCad 9
                m1 = _check_float(i, 1, name+' margin 1')
                m2 = _check_float(i, 2, name+' margin 2')
                m3 = _check_float(i, 3, name+' margin 3')
                m4 = _check_float(i, 4, name+' margin 4')
                text.margins = [m1, m2, m3, m4]
            elif i_type == 'span':
                # KiCad 9 cell table
                m1 = _check_integer(i, 1, name+' '+i_type+' 1')
                m2 = _check_integer(i, 2, name+' '+i_type+' 2')
                text.span = [m1, m2]
            else:
                raise SchError(f'Unknown `{name}` attribute `{i}`')
        return text

    def write(self):
        data = [self.text, Sep()]
        if self.exclude_from_sim is not None:
            data.append(_symbol_yn('exclude_from_sim', self.exclude_from_sim))
        data.extend([_symbol('at', [self.pos_x, self.pos_y, self.ang]), _symbol('size', [self.size.x, self.size.y]), Sep()])
        if self.margins is not None:
            data.append(_symbol('margins', self.margins))
        if self.span is not None:
            data.append(_symbol('span', self.span))
        if self.stroke:
            data.extend([self.stroke.write(), Sep()])
        data.extend([self.fill.write(), Sep(),
                     self.effects.write(), Sep()])
        if self.uuid:
            add_uuid(data, self.uuid)
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
        self.name = 'global_label'
        self.length = None   # For netclass_flag

    @classmethod
    def parse(cls, items):
        label = cls()
        label.text = _check_str(items, 1, label.name)
        field_id = 0
        for c, i in enumerate(items[2:]):
            i_type = _check_is_symbol_list(i)
            if i_type == 'shape':
                label.shape = _check_symbol(i, 1, label.name+' '+i_type)
            elif i_type == 'length':
                label.length = _check_float(i, 1, label.name+' '+i_type)
            elif i_type == 'fields_autoplaced':
                label.fields_autoplaced = True
            elif i_type == 'at':
                label.pos_x, label.pos_y, label.ang = _get_at(items, c+2, label.name)
            elif i_type == 'effects':
                label.effects = FontEffects.parse(i)
            elif i_type == 'uuid':
                label.uuid = get_uuid(items, c+2, label.name)
            elif i_type == 'property':
                label.properties.append(SchematicFieldV6.parse(i, field_id))
                field_id += 1
            else:
                raise SchError('Unknown {} attribute `{}`'.format(label.name, i))
        return label

    def write(self):
        data = [self.text]
        if self.length is not None:
            data.append(_symbol('length', [self.length]))
        if self.shape is not None:
            data.append(_symbol('shape', [Symbol(self.shape)]))
        data.append(_symbol('at', [self.pos_x, self.pos_y, self.ang]))
        if self.fields_autoplaced:
            data.append(_symbol('fields_autoplaced', []))
        if self.effects is not None:
            data.extend([Sep(), self.effects.write()])
        data.append(Sep())
        add_uuid(data, self.uuid)
        for p in self.properties:
            data.extend([p.write(), Sep()])
        return _symbol(self.name, data)


class Label(GlobalLabel):
    def __init__(self):
        super().__init__()
        self.name = 'label'


class HierarchicalLabel(GlobalLabel):
    def __init__(self):
        super().__init__()
        self.name = 'hierarchical_label'


class NetClassFlag(GlobalLabel):
    def __init__(self):
        super().__init__()
        self.name = 'netclass_flag'


class HSPin(object):
    """ Hierarchical Sheet Pin """
    # TODO base class with HierarchicalLabel
    @staticmethod
    def parse(items):
        name = 'hierarchical sheet pin'
        if len(items) != 6:
            _check_len_total(items, 5, name)
        pin = HSPin()
        pin.name = _check_str(items, 1, name+' name')
        pin.type = _check_symbol(items, 2, name+' type')
        for c, i in enumerate(items[3:]):
            i_type = _check_is_symbol_list(i)
            if i_type == 'at':
                pin.pos_x, pin.pos_y, pin.ang = _get_at(items, c+3, name)
            elif i_type == 'effects':
                pin.effects = _get_effects(items, c+3, name)
            elif i_type == 'uuid':
                pin.uuid = get_uuid(items, c+3, name)
            else:
                raise SchError(f'Unknown {name} attribute `{i}`')
        return pin

    def write(self):
        data = [self.name,
                Symbol(self.type),
                _symbol('at', [self.pos_x, self.pos_y, self.ang]), Sep(),
                self.effects.write(), Sep()]
        add_uuid(data, self.uuid)
        return _symbol('pin', data)


class SheetInstance(object):
    @staticmethod
    def parse(items):
        name = 'sheet instance'
        instances = []
        for c, _ in enumerate(items[1:]):
            v = _check_symbol_value(items, c+1, name, 'path')
            instance = SheetInstance()
            instance.path = _check_str(v, 1, name+' path')
            instance.page = _check_symbol_str(v, 2, name, 'page')
            instances.append(instance)
        return instances

    def write(self):
        return _symbol('path', [self.path, _symbol('page', [self.page])])


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
        self.uuid = None
        # KiCad v7:
        # Instances classified by project
        self.projects = None
        # All instances, by path (page look-up)
        self.all_instances = {}
        # KiCad 9 attributes
        self.exclude_from_sim = None
        self.in_bom = None
        self.on_board = None
        self.dnp = None
        # KiCad 10 attributes
        self.in_pos_files = None
        self.duplicate_pin_numbers_are_jumpers = None

    def load_project(self, prj):
        name = _check_str(prj, 1, 'instance project')
        instances = SheetInstance().parse(prj[1:])
        for i in instances:
            self.all_instances[i.path] = i.page
        return name, instances

    def load_instances(self, i):
        self.projects = []
        for prj in i[1:]:
            i_type = _check_is_symbol_list(prj)
            if i_type != 'project':
                raise SchError('Found `{}` instead of `project` in sheet instance'.format(i_type))
            self.projects.append(self.load_project(prj))

    @staticmethod
    def parse(items):
        sheet = Sheet()
        field_id = 0
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
                sheet.uuid_ori = _get_uuid(items, c+1, 'sheet')
                sheet.uuid, _ = UUID_Validator.validate(sheet.uuid_ori)
            elif i_type == 'exclude_from_sim':
                sheet.exclude_from_sim = _get_yes_no(i, 1, i_type)
            elif i_type == 'in_bom':
                sheet.in_bom = _get_yes_no(i, 1, i_type)
            elif i_type == 'on_board':
                sheet.on_board = _get_yes_no(i, 1, i_type)
            elif i_type == 'in_pos_files':
                sheet.in_pos_files = _get_yes_no(i, 1, i_type)
            elif i_type == 'duplicate_pin_numbers_are_jumpers':
                sheet.duplicate_pin_numbers_are_jumpers = _get_yes_no(i, 1, i_type)
            elif i_type == 'dnp':
                sheet.dnp = _get_yes_no(i, 1, i_type)
            elif i_type == 'property':
                field = SchematicFieldV6.parse(i, field_id)
                field_id += 1
                sheet.properties.append(field)
                if field.name in SHEET_NAME:
                    sheet.name = field.value
                elif field.name in SHEET_FILE:
                    sheet.file = field.value
                else:
                    logger.warning(W_UNKFLD+"Unknown sheet property `{}` ({})".format(field.name, field.value))
            elif i_type == 'pin':
                sheet.pins.append(HSPin.parse(i))
            elif i_type == 'instances':
                sheet.load_instances(i)
            else:
                raise SchError('Unknown sheet attribute `{}`'.format(i))
        if not sheet.uuid:
            raise SchError("No UUID for sheet `{}`, use KiCad to fix it".format(sheet.name or sheet.file))
        return sheet

    def load_sheet(self, project, parent_file, parent_obj):
        assert self.name
        sheet = SchematicV6()
        self.sheet = sheet
        parent_dir = os.path.dirname(parent_file)
        sheet.sheet_path = path_join(parent_obj.sheet_path, self.uuid)
        sheet.sheet_path_ori = path_join(parent_obj.sheet_path_ori, self.uuid_ori)
        sheet.sheet_path_h = path_join(parent_obj.sheet_path_h, self.name)
        parent_obj.sheet_paths[sheet.sheet_path_ori] = sheet
        sheet.load(os.path.join(parent_dir, self.file), project, parent_obj)
        # self.sheet_paths
        if self.projects is not None:
            # KiCad v7 sheet pages are here
            p_path = parent_obj.get_full_path()
            page = self.all_instances.get(p_path)
            if page is None:
                raise SchError('Missing sheet instance for `{}`'.format(p_path))
            else:
                sheet.sheet = page
                parent_obj.all_sheets.append(sheet)
            # Memorize its path
            self.p_path_ori = p_path
            self.p_path = parent_obj.get_full_path(False)
        return sheet

    def write(self, exp_hierarchy):
        data = [_symbol('at', [self.pos_x, self.pos_y]),
                _symbol('size', [self.w, self.h])]
        if self.exclude_from_sim is not None:
            data.append(_symbol_yn('exclude_from_sim', self.exclude_from_sim))
        if self.in_bom is not None:
            data.append(_symbol_yn('in_bom', self.in_bom))
        if self.on_board is not None:
            data.append(_symbol_yn('on_board', self.on_board))
        if self.in_pos_files is not None:
            data.append(_symbol_yn('in_pos_files', self.in_pos_files))
        if self.duplicate_pin_numbers_are_jumpers is not None:
            data.append(_symbol_yn('duplicate_pin_numbers_are_jumpers', self.duplicate_pin_numbers_are_jumpers))
        if self.dnp is not None:
            data.append(_symbol_yn('dnp', self.dnp))
        if self.fields_autoplaced:
            data.append(_symbol('fields_autoplaced', []))
        data.extend([Sep(), self.stroke.write(), Sep(),
                    self.fill.write(), Sep()])
        add_uuid(data, self.uuid)
        for p in self.properties:
            change_file = exp_hierarchy and p.name in SHEET_FILE
            if change_file:
                p.value = self.flat_file
            data.extend([p.write(), Sep()])
            if change_file:
                p.value = self.file
        for p in self.pins:
            data.extend([p.write(), Sep()])
        if self.projects is not None:
            prj_data = [Sep()]
            sheet = self.sheet
            prjname = find_our_project(self, sheet.project, exp_hierarchy)
            for prj, ins in self.projects:
                if exp_hierarchy and prj != prjname:
                    # For the expanded hierarchy we save only this project
                    continue
                ins_data = [prj, Sep()]
                for i in ins:
                    if exp_hierarchy:
                        if i.path == self.p_path_ori:
                            # Adjust the instance for the expanded hierarchy
                            i = deepcopy(i)
                            i.path = self.p_path
                        else:
                            # Don't store bogus instances
                            continue
                    ins_data.extend([i.write(), Sep()])
                prj_data.extend([_symbol('project', ins_data), Sep()])
            data.extend([_symbol('instances', prj_data), Sep()])
        return _symbol('sheet', data)


class TableBorder(object):
    def __init__(self):
        super().__init__()
        self.external = self.header = True
        self.stroke = None
        self.name = 'border'

    @staticmethod
    def parse(items):
        border = TableBorder()
        for i in items[1:]:
            i_type = _check_is_symbol_list(i)
            if i_type == 'external':
                border.external = _get_yes_no(i, 1, i_type)
            elif i_type == 'header':
                border.header = _get_yes_no(i, 1, i_type)
            elif i_type == 'stroke':
                border.stroke = Stroke.parse(i)
            else:
                raise SchError(f'Unknown {border.name} attribute `{i}`')
        return border

    def write(self):
        data = [Sep(), _symbol_yn('external', self.external), Sep(),
                _symbol_yn('header', self.header), Sep()]
        if self.stroke:
            data.extend([self.stroke.write(), Sep()])
        return _symbol(self.name, data)


class TableSeparator(object):
    def __init__(self):
        super().__init__()
        self.rows = self.cols = True
        self.stroke = None
        self.name = 'separators'

    @staticmethod
    def parse(items):
        sep = TableSeparator()
        for i in items[1:]:
            i_type = _check_is_symbol_list(i)
            if i_type == 'rows':
                sep.rows = _get_yes_no(i, 1, i_type)
            elif i_type == 'cols':
                sep.cols = _get_yes_no(i, 1, i_type)
            elif i_type == 'stroke':
                sep.stroke = Stroke.parse(i)
            else:
                raise SchError(f'Unknown {sep.name} attribute `{i}`')
        return sep

    def write(self):
        data = [Sep(), _symbol_yn('rows', self.rows), Sep(),
                _symbol_yn('cols', self.cols), Sep()]
        if self.stroke:
            data.extend([self.stroke.write(), Sep()])
        return _symbol(self.name, data)


class Table(object):
    def __init__(self):
        super().__init__()
        self.column_count = 1
        self.border = None
        self.separators = None
        self.column_widths = []
        self.row_heights = []
        self.cells = []
        self.name = 'table'
        self.uuid = None

    @staticmethod
    def parse(items):
        tb = Table()
        for c, i in enumerate(items[1:]):
            i_type = _check_is_symbol_list(i)
            if i_type == 'column_count':
                tb.column_count = _check_integer(i, 1, tb.name+' '+i_type)
            elif i_type == 'border':
                tb.border = TableBorder.parse(i)
            elif i_type == 'separators':
                tb.separators = TableSeparator.parse(i)
            elif i_type == 'column_widths':
                tb.column_widths = _check_floats(i, 1, tb.name+' '+i_type)
            elif i_type == 'row_heights':
                tb.row_heights = _check_floats(i, 1, tb.name+' '+i_type)
            elif i_type == 'uuid':
                tb.uuid = get_uuid(items, c+1, tb.name+' '+i_type)
            elif i_type == 'cells':
                tb.cells = []
                for cell in i[1:]:
                    v = _check_symbol(cell, 0, tb.name+' '+i_type)
                    if v != 'table_cell':
                        raise SchError(f'Unknown `cells` element `{v}`')
                    tb.cells.append(TextBox.parse(cell, v))
            else:
                raise SchError(f'Unknown {tb.name} attribute `{i}`')
        return tb

    def write(self):
        data = [Sep(), _symbol('column_count', [self.column_count]), Sep()]
        if self.border:
            data.extend([self.border.write(), Sep()])
        if self.separators:
            data.extend([self.separators.write(), Sep()])
        if self.column_widths:
            data.extend([_symbol('column_widths', self.column_widths), Sep()])
        if self.row_heights:
            data.extend([_symbol('row_heights', self.row_heights), Sep()])
        add_uuid(data, self.uuid)
        if self.cells:
            cells = []
            _add_items(self.cells, cells)
            data.extend([_symbol('cells', cells), Sep()])
        return _symbol(self.name, data)


class RuleArea(object):
    def __init__(self):
        super().__init__()
        self.poly_line = None
        self.name = 'rule_area'

    @staticmethod
    def parse(items):
        o = RuleArea()
        for i in items[1:]:
            i_type = _check_is_symbol_list(i)
            if i_type == 'polyline':
                o.poly_line = DrawPolyLine.parse(i)
            else:
                raise SchError(f'Unknown {o.name} attribute `{i}`')
        return o

    def write(self):
        data = [Sep()]
        if self.poly_line:
            data.extend([self.poly_line.write(), Sep()])
        return _symbol(self.name, data)


# Here because we have all s-expr tools here
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
        layers = [layer]
        n_layers = 1
        layer.name = _check_str(items, 1, name)
        for i in items[2:]:
            i_type = _check_is_symbol_list(i, allow_orphan_symbol=('addsublayer'))
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
            elif i_type == 'addsublayer':
                new_layer = PCBLayer()
                new_layer.name = layer.name
                new_layer.type = layer.type
                layers.append(new_layer)
                layer = new_layer
                n_layers += 1
            else:
                logger.warning('Unknown layer attribute `{}`'.format(i))
        if n_layers > 1:
            for n, layer in enumerate(layers):
                layer.name += ' ({}/{})'.format(n+1, n_layers)
        return layers


def _symbol_yn(name, val):
    return [Symbol(name), NO_YES[val]]


def _add_items(items, sch, sep=False, cross=None, pre_sep=True, exp_hierarchy=None, alt_variants=None):
    if len(items):
        if pre_sep:
            sch.append(Sep())
        args = {}
        if exp_hierarchy is not None:
            args['exp_hierarchy'] = exp_hierarchy
        if alt_variants is not None:
            args['alt_variants'] = alt_variants
        if cross is not None:
            args['cross'] = cross
        for i in items:
            sch.append(i.write(**args))
            sch.append(Sep())
            if sep:
                sch.append(Sep())
        if sep:
            sch.pop()


def _add_items_list(name, items, sch, alt_variants=None):
    if not len(items):
        return
    data = [Sep()]
    for s in items:
        if alt_variants is not None:
            data.append(s.write(alt_variants=alt_variants))
        else:
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
        self.comment_ori = ['']*9
        self.max_comments = 9
        self.title_ori = self.date_ori = self.revision_ori = self.company_ori = None
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
                self.title_ori = _check_str(item, 1, i_type)
                self.title = GS.expand_text_variables(self.title_ori)
            elif i_type == 'date':
                self.date_ori = _check_str(item, 1, i_type)
                self.date = GS.expand_text_variables(self.date_ori)
            elif i_type == 'rev':
                self.revision_ori = _check_str(item, 1, i_type)
                self.revision = GS.expand_text_variables(self.revision_ori)
            elif i_type == 'company':
                self.company_ori = _check_str(item, 1, i_type)
                self.company = GS.expand_text_variables(self.company_ori)
            elif i_type == 'comment':
                index = _check_integer(item, 1, i_type)
                if index < 1 or index > 9:
                    raise SchError('Unsupported comment index {} in title block'.format(index))
                value = _check_str(item, 2, i_type)
                self.comment_ori[index-1] = value
                self.comment[index-1] = GS.expand_text_variables(value)
            else:
                raise SchError('Unsupported entry in title block ({})'.format(item))
        self._fill_missing_title_block()
        logger.debug("SCH title: `{}`".format(self.title_ori))
        logger.debug("SCH date: `{}`".format(self.date_ori))
        logger.debug("SCH revision: `{}`".format(self.revision_ori))
        logger.debug("SCH company: `{}`".format(self.company_ori))

    def _get_lib_symbols(self, comps):
        if not isinstance(comps, list):
            raise SchError('The lib symbols is not a list')
        for c in comps[1:]:
            obj = LibComponent.load(c, self.project)
            self.lib_symbols.append(obj)
            self.lib_symbol_names[obj.lib_id] = obj

    def _get_embedded_files(self, files):
        if not isinstance(files, list):
            raise SchError('The embedded files is not a list')
        for f in files[1:]:
            obj = EmbeddedFile.load(f)
            self.embedded_files.append(obj)
            self.embedded_file_names[obj.name] = obj

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
        data = []
        if self.title_ori:
            data += [_symbol('title', [self.title_ori]), Sep()]
        if self.date_ori:
            data += [_symbol('date', [self.date_ori]), Sep()]
        if self.revision_ori:
            data += [_symbol('rev', [self.revision_ori]), Sep()]
        if self.company_ori:
            data += [_symbol('company', [self.company_ori]), Sep()]
        for num, val in enumerate(self.comment_ori):
            if val:
                data += [_symbol('comment', [num+1, val]), Sep()]
        # If all empty return an empty list
        if not data:
            return data
        return [Sep(), Sep(), _symbol('title_block', [Sep()]+data)]

    def write_lib_symbols(self, cross):
        if GS.ki7 and GS.global_cross_using_kicad:
            # KiCad 7 can cross it by itself
            cross = False
        data = [Sep()]
        for s in self.lib_symbols:
            data.extend([s.write(False), Sep()])
            if cross:
                data.extend([s.write(cross), Sep()])
        return [Sep(), Sep(), _symbol('lib_symbols', data), Sep()]

    def write_lib(self, path, name, comps, do_back_up=False):
        """ Creates a lib path/name containing the specified comps """
        lib = [Symbol('kicad_symbol_lib')]
        # TODO: How do I know which is the valid version? Doesn't match the schematic version!
        lib.append(_symbol('version', [20220914]))
        lib.append(_symbol('generator', [Symbol("KiBot")]))
        lib.append(Sep())
        for s in comps:
            lib.extend([self.lib_symbol_names[name+':'+s].write(False), Sep()])
        # Keep a back-up of existing files
        fname = os.path.join(path, name+'.kicad_sym')
        if do_back_up and os.path.isfile(fname):
            bkp = fname+'-bak'
            os.replace(fname, bkp)
        dirname = os.path.dirname(fname)
        os.makedirs(dirname, exist_ok=True)
        with open(fname, 'wt') as f:
            f.write(dumps(lib))
            f.write('\n')

    def save(self, fname=None, dest_dir=None, base_sheet=None, saved=None, cross=False, exp_hierarchy=False, dry=False,
             alt_variants=False):
        # Switch to the current version
        global version
        version = self.version
        if base_sheet is None:
            # We are the base sheet
            base_sheet = self
            # Copy potentially modified data from components
            for s in self.symbol_instances:
                comp = s.component
                s.reference = comp.ref
                if s.value is not None:
                    s.value = comp.value
                if s.footprint is not None:
                    s.footprint = comp.footprint_lib+':'+comp.footprint if comp.footprint_lib else comp.footprint
        if saved is None:
            # Start memorizing saved files
            saved = set()
        if fname is None:
            # Use our name if none provided
            fname = self.fname
        if dest_dir is None:
            # Save at the same place
            if not os.path.isabs(fname):
                # Use the base sheet as reference
                fname = os.path.join(os.path.dirname(base_sheet.fname), fname)
        else:
            # Save all in dest_dir (variant)
            fname = os.path.join(dest_dir, fname)
        # Save the sheet
        if fname not in saved and not dry:
            sch = [Symbol('kicad_sch')]
            sch.append(_symbol('version', [self.version]))
            if self.version >= KICAD_8_VER:
                sch.append(_symbol('generator', [self.generator]))
            else:
                sch.append(_symbol('generator', [Symbol(self.generator)]))
            if self.generator_version:
                sch.append(_symbol('generator_version', [self.generator_version]))
            sch.append(Sep())
            sch.append(Sep())
            add_uuid(sch, self.uuid, no_sep=True)
            sch.extend(self.write_paper())
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
            # Arcs
            _add_items(self.arcs, sch)
            # Circles
            _add_items(self.circles, sch)
            # Beziers
            _add_items(self.beziers, sch)
            # Rectangles
            _add_items(self.rectangles, sch)
            # Images
            _add_items(self.bitmaps, sch)
            # Text Boxes
            _add_items(self.text_boxes, sch)
            # Texts
            _add_items(self.texts, sch, pre_sep=False)
            # Labels
            _add_items(self.labels, sch)
            # Global Labels
            _add_items(self.glabels, sch)
            # Hierarchical Labels
            _add_items(self.hlabels, sch)
            # Net Class Flags
            _add_items(self.net_class_flags, sch)
            # Tables
            _add_items(self.tables, sch)
            # Tables
            _add_items(self.rule_areas, sch)
            # Symbols
            _add_items(self.symbols, sch, sep=True, cross=cross, exp_hierarchy=exp_hierarchy, alt_variants=alt_variants)
            # Groups (KiCad 10+)
            _add_items(self.groups, sch)
            # Sheets
            _add_items(self.sheets, sch, sep=True, exp_hierarchy=exp_hierarchy)
            # Sheet instances
            instances = self.sheet_instances
            if exp_hierarchy and base_sheet == self:
                # We are saving a expanded hierarchy, so we must fix the root page instances
                instances = deepcopy(self.sheet_instances)
                for ins in instances:
                    ins.path = self.sheet_paths[ins.path].sheet_path
            if base_sheet == self or not exp_hierarchy:
                _add_items_list('sheet_instances', instances, sch)
            # Symbol instances
            if version < KICAD_7_VER:
                instances = self.symbol_instances
                if exp_hierarchy and base_sheet == self:
                    # We are saving a expanded hierarchy, so we must fix the instances
                    instances = deepcopy(self.symbol_instances)
                    for s in instances:
                        c = s.component
                        if c.uuid != c.uuid_ori:
                            # UUID changed to make it different
                            # s.path = path_join(os.path.dirname(s.path), c.uuid)
                            s.path = path_join(c.path, c.uuid)
                if base_sheet == self or not exp_hierarchy:
                    _add_items_list('symbol_instances', instances, sch, alt_variants=False)
            # Fonts
            if self.embedded_fonts is not None:
                sch.append(_symbol_yn('embedded_fonts', self.embedded_fonts))
            # - Embedded files (here are the fonts)
            if self.embedded_files:
                files = []
                for f in self.embedded_files:
                    files.append(Sep())
                    files.append(f.write())
                files.append(Sep())
                sch.extend([Sep(), _symbol('embedded_files', files), Sep()])
            logger.debug('Saving schematic: `{}`'.format(fname))
            # Keep a back-up of existing files
            if os.path.isfile(fname):
                bkp = fname+'-bak'
                os.replace(fname, bkp)
            with GS.create_file(fname) as f:
                f.write(dumps(sch))
                f.write('\n')
        if fname not in saved:
            saved.add(fname)
        for sch in self.sheets:
            if sch.sch:
                sch.sch.save(sch.flat_file if exp_hierarchy else sch.sch.fname_rel, dest_dir, base_sheet, saved, cross=cross,
                             exp_hierarchy=exp_hierarchy, dry=dry, alt_variants=alt_variants)

    def save_variant(self, dest_dir, alt_variants=False):
        fname = os.path.basename(self.fname)
        self.save(fname, dest_dir, cross=True, exp_hierarchy=self.check_exp_hierarchy(), alt_variants=alt_variants)
        return fname

    def file_names_variant(self, dest_dir):
        """ Returns a list of file names created by save_variant() """
        saved = set()
        fname = os.path.basename(self.fname)
        self.save(fname, dest_dir, cross=True, exp_hierarchy=self.check_exp_hierarchy(), dry=True, saved=saved)
        return saved

    def check_exp_hierarchy(self):
        """ Check if we really need to expand the hierarchy """
        # KiCad v6: we can change the value and footprint, but won't work when imported by v7
        # Collect component instances (UUID -> list of instances)
        instances = {}
        for s in self.symbol_instances:
            c_uuid = os.path.basename(s.path)
            instances.setdefault(c_uuid, []).append(s.component)
        # Look for variants in the instances
        for _, l_ins in instances.items():
            if len(l_ins) < 2:
                # 0 or 1 can't be different
                continue
            ref_c = l_ins[0]
            if any((self.compare_component(ref_c, c) for c in l_ins[1:])):
                return True
        # No variant
        return False

    @staticmethod
    def compare_component(r, c):
        """ Returns True if the components need separated instances (are different) """
        if len(r.dfields) != len(c.dfields):
            SchematicV6.log_difference(r, c, 'list of field names {} vs {}'.format(len(r.dfields), len(c.dfields)))
            return True
        for name, field in r.dfields.items():
            if name == 'reference':
                continue
            field2 = c.dfields.get(name)
            if field2 is None:
                SchematicV6.log_difference(r, c, 'field `{}` not in the second'.format(name))
            if field.value != field2.value:
                SchematicV6.log_difference(r, c, '`{}` fields (`{}` != `{}`)'.format(name, field.value, field2.value))
                return True
        if c.fitted != r.fitted:
            SchematicV6.log_difference(r, c, 'fitted status')
            return True
        if c.included != r.included:
            SchematicV6.log_difference(r, c, 'included status')
            return True
        if c.fixed != r.fixed:
            SchematicV6.log_difference(r, c, 'fixed status')
            return True
        if c.fixed != r.fixed:
            SchematicV6.log_difference(r, c, 'fixed status')
            return True
        if c.in_bom != r.in_bom:
            SchematicV6.log_difference(r, c, 'in_bom status')
            return True
        if c.on_board != r.on_board:
            SchematicV6.log_difference(r, c, 'on_board status')
            return True
        if c.in_pos_files != r.in_pos_files:
            SchematicV6.log_difference(r, c, 'in_pos_files status')
            return True
        if c.duplicate_pin_numbers_are_jumpers != r.duplicate_pin_numbers_are_jumpers:
            SchematicV6.log_difference(r, c, 'duplicate_pin_numbers_are_jumpers status')
            return True
        return False

    @staticmethod
    def log_difference(r, c, msg):
        logger.debug('Expanding hierarchy because {} and {} has different {}'.format(r.ref, c.ref, msg))

    def _create_flat_name(self, sch):
        """ Create a unique name that doesn't contain subdirs.
            Is used to save a variant, where we avoid sharing instance data """
        # Store it in the UUID -> name
        # Used to create a human readable sheet path
        self.sheet_names[path_join(self.sheet_path_ori, sch.uuid_ori)] = path_join(self.sheet_path_h, sch.name)
        # Eliminate subdirs
        file = sch.file.replace('/', '_')
        fparts = os.path.splitext(file)
        sch.flat_file = fparts[0]+'_'+str(len(self.sheet_names))+fparts[1]

    def get_title(self):
        return self.title_ori

    def set_title(self, title):
        """ Used only to save a variant """
        old_title = self.title_ori
        self.title_ori = title
        return old_title

    def get_full_path(self, ori=True):
        """ Path using the UUID of the root. Used by v7 """
        path = '/'+self.root_sheet.uuid
        # Avoid returning /UUID/
        if self.sheet_path != '/':
            path += self.sheet_path_ori if ori else self.sheet_path
        return path

    def debug_instances(self):
        """ Debug for the expanded hierarchy """
        logger.debug("Collected sheet instances")
        for s in self.sheet_instances:
            logger.debug(f"- {s.path} -> {s.page}")
        logger.debug("Collected symbol instances")
        for s in sorted(self.symbol_instances, key=lambda x: x.path):
            logger.debug(f"- {s.path} -> {s.reference}")
        logger.debug("Collected sheet paths")
        for p, s in self.sheet_paths.items():
            logger.debug(f"- {p}")
            for sy, c in s.symbol_uuids.items():
                logger.debug(f"  - {sy} -> {c}")

    def get_embedded_file(self, efile):
        name = efile[len(EMBED_PREFIX):]
        if name not in self.embedded_file_names:
            raise SchError(f'Missing embedded file `{efile}`')
        o = self.embedded_file_names[name]
        cache_name = GS.get_embed_dir('kicad_embedded_'+o.checksum+os.path.splitext(name)[1])
        if os.path.isfile(cache_name):
            return cache_name
        # If the embedded file is not in cache then save it to the cache
        elif hasattr(o, 'data'):
            command = GS.check_tool('global', 'ZStd')
            if command is None:
                GS.exit_with_error(f"Can't extract `{name}` embedded file because `zstd` module is not installed,"
                                   " open the schematic using KiCad to populate the cache", DONT_STOP)
            else:
                dirname = GS.get_embed_dir('')
                if not os.path.exists(dirname):
                    os.mkdir(dirname)
                import zstd
                data = zstd.uncompress(base64.b64decode(''.join(o.data)))
                with open(cache_name, 'wb') as f:
                    f.write(data)
                return cache_name
        raise SchError(f'Missing embedded file `{efile}`')

    def load(self, fname, project, parent=None, mapped_uuid=None):  # noqa: C901
        """ Load a v6.x KiCad Schematic.
            The caller must be sure the file exists.
            Only the schematics are loaded not the libs. """
        logger.debug("Loading sheet from "+fname)
        extra_debug = GS.debug_level >= 3
        if parent is None:
            self.fields = ['part']
            self.fields_lc = set(self.fields)
            self.sheet_paths = {'/': self}
            self.lib_symbol_names = {}
            self.sheet_path = self.sheet_path_ori = '/'
            self.sheet_path_h = '/'
            self.sheet_names = {}
            self.all_sheets = []
            self.root_sheet = self
            UUID_Validator.reset()
            self.root_file_path = os.path.dirname(os.path.abspath(fname))
            self.embedded_file_names = {}
            self.used_variants = {}
        else:
            self.fields = parent.fields
            self.fields_lc = parent.fields_lc
            self.sheet_paths = parent.sheet_paths
            self.lib_symbol_names = parent.lib_symbol_names
            # self.sheet_path/_h is set by sch.load_sheet
            self.sheet_names = parent.sheet_names
            self.all_sheets = parent.all_sheets
            self.root_sheet = parent.root_sheet
            self.root_file_path = parent.root_file_path
            self.embedded_file_names = parent.embedded_file_names
            self.used_variants = parent.used_variants
        self.symbol_instances = []
        self.parent = parent
        self.fname = fname
        self.fname_rel = os.path.relpath(fname, self.root_file_path)
        self.project = project
        self.lib_symbols = []
        self.symbols = []
        self.components = []
        self.junctions = []  # Connect
        self.no_conn = []
        self.bus_entry = []
        self.wires = []
        self.arcs = []
        self.circles = []
        self.beziers = []
        self.rectangles = []
        self.bitmaps = []
        self.text_boxes = []
        self.texts = []
        self.labels = []
        self.glabels = []
        self.hlabels = []
        self.net_class_flags = []
        self.groups = []
        self.sheets = []
        self.sheet_instances = []
        self.bus_alias = []
        self.libs = {}  # Just for compatibility with v5 class
        self.symbol_uuids = {}
        self.generator_version = None
        self.embedded_fonts = None
        self.embedded_files = []
        self.tables = []
        self.rule_areas = []
        if not os.path.isfile(fname):
            raise SchError('Missing subsheet: '+fname)
        with open(fname, 'rt') as fh:
            error = None
            try:
                sch = load(fh)[0]
            except SExpData as e:
                error = str(e)
            if error:
                raise SchError(error)
        if not isinstance(sch, list) or sch[0].value() != 'kicad_sch':
            raise SchError('No kicad_sch signature')
        for e in sch[1:]:
            e_type = _check_is_symbol_list(e)
            obj = None
            if e_type == 'version':
                self.version = _check_integer(e, 1, e_type)
                global version
                version = self.version
            elif e_type == 'generator':
                self.generator = _check_relaxed(e, 1, e_type)
            elif e_type == 'generator_version':
                self.generator_version = _check_str(e, 1, e_type)
            elif e_type == 'uuid':
                self.uuid_ori = mapped_uuid or _check_relaxed(e, 1, e_type)
                uuid, _ = UUID_Validator.validate(self.uuid_ori)
                self.id = self.uuid = uuid
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
            elif e_type == 'arc':
                self.arcs.append(DrawArcV6.parse(e))
            elif e_type == 'circle':
                self.circles.append(DrawCircleV6.parse(e))
            elif e_type == 'bezier':
                # KiCad 9
                self.beziers.append(DrawCurve.parse(e))
            elif e_type == 'rectangle':
                self.rectangles.append(DrawRectangleV6.parse(e))
            elif e_type == 'image':
                self.bitmaps.append(SchematicBitmapV6.parse(e))
            elif e_type == 'text_box':
                self.text_boxes.append(TextBox.parse(e, e_type))
            elif e_type == 'text':
                self.texts.append(Text.parse(e, e_type))
            elif e_type == 'label':
                if self.version < KICAD_7_VER:
                    self.labels.append(Text.parse(e, e_type))
                else:
                    self.labels.append(Label.parse(e))
            elif e_type == 'global_label':
                self.glabels.append(GlobalLabel.parse(e))
            elif e_type == 'hierarchical_label':
                self.hlabels.append(HierarchicalLabel.parse(e))
            elif e_type == 'netclass_flag':
                self.net_class_flags.append(NetClassFlag.parse(e))
            elif e_type == 'symbol':
                obj = SchematicComponentV6.load(e, self.project, self)
                update_dict(self.used_variants, obj.used_variants)
                if extra_debug:
                    logger.debug(f"- Loaded {obj} [id {id(obj)}]  UUID {obj.uuid} original UUID {obj.uuid_ori}")
                self.symbols.append(obj)
                self.symbol_uuids[path_join(self.sheet_path_ori, obj.uuid_ori)] = obj
            elif e_type == 'group':
                # New on KiCad 10
                self.groups.append(Group.parse(e))
            elif e_type == 'sheet':
                obj = Sheet.parse(e)
                self.sheets.append(obj)
                self._create_flat_name(obj)
            elif e_type == 'sheet_instances':
                self.sheet_instances = SheetInstance.parse(e)
            elif e_type == 'symbol_instances':  # KiCad 6 only, 7+ moved it to the "symbol"s
                self.symbol_instances = SymbolInstance.parse(e)
            elif e_type == 'embedded_fonts':  # KiCad 9
                self.embedded_fonts = _get_yes_no(e, 1, e_type)
            elif e_type == 'embedded_files':  # KiCad 9
                self._get_embedded_files(e)
            elif e_type == 'table':  # KiCad 9
                self.tables.append(Table.parse(e))
            elif e_type == 'rule_area':  # KiCad 9
                self.rule_areas.append(RuleArea.parse(e))
            else:
                raise SchError('Unknown kicad_sch attribute `{}`'.format(e))
        if not self.title:
            self._fill_missing_title_block()
        # Load sub-sheets
        for sch in self.sheets:
            sch.sch = sch.load_sheet(project, fname, self)
        # Assign the page numbers
        if parent is not None:
            # Here we finished for sub-sheets
            return
        # On the main sheet analyze the sheet and symbol instances
        # Solve the sheet pages: assign the page numbers.
        # KiCad 6: for all pages
        # KiCad 7: only for /, the rest are already assigned
        # We use the page number for the netlist generation
        for i in self.sheet_instances:
            sheet = self.sheet_paths.get(i.path)
            if sheet:
                sheet.sheet = i.page
                self.all_sheets.append(sheet)
        # Debug for the expanded hierarchy
        if extra_debug:
            self.debug_instances()
            logger.debug("Assigning components to instances")
        # Create the components list
        for s in self.symbol_instances:
            # Get a copy of the original symbol
            path = os.path.dirname(s.path)
            try:
                sheet = self.sheet_paths[path]
            except KeyError as e:
                logger.debug("Available UUIDs {}".format(sheet.sheet_paths))
                raise SchError("Error looking for sheet with UUID `{}`".format(path)) from e
            try:
                comp = sheet.symbol_uuids[s.path]
            except KeyError as e:
                logger.debug("Available UUIDs {}".format(sheet.symbol_uuids))
                raise SchError("Error looking for component with UUID `{}`".format(s.path)) from e
            s.component = comp
            # Transfer the instance data
            comp.set_ref(s.reference)
            comp.unit = s.unit
            comp.variants = s.variants
            comp.alt_variants = s.alt_variants
            # Value and footprint were available in v6, but they were just copies, not really used
            if s.value is not None:
                comp.set_value(s.value)
            if s.footprint is not None:
                comp.set_footprint(s.footprint)
            comp.sheet_path = path
            comp.sheet_path_h = self.path_to_human(path)
            comp.sheet_full_path = s.path
            comp.id = comp.uuid
            if s.reference[-1] == '?':
                comp.annotation_error = True
                self.annotation_error = True
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
            if extra_debug:
                logger.debug(f"- {s.path} -> {s.reference} -> {id(comp)} {comp.uuid}")
            # Add it to the list
            self.components.append(comp)
        self.comps_data = self.lib_symbol_names
