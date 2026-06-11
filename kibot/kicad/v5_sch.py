# -*- coding: utf-8 -*-
# Copyright (c) 2020-2024 Salvador E. Tropea
# Copyright (c) 2020-2024 Instituto Nacional de Tecnología Industrial
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)
"""
KiCad v5 (and older) Schematic format.
A basic implementation of the .sch file format.
Currently oriented to collect the components for the BoM.
"""
# Encapsulate file/line
import re
import os
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom
from datetime import datetime
from copy import deepcopy
from collections import OrderedDict
from .config import KiConf, un_quote
from .error import SchError, SchFileError, SchLibError
from ..gs import GS
from ..misc import (W_BADPOLI, W_POLICOORDS, W_BADSQUARE, W_BADCIRCLE, W_BADARC, W_BADTEXT, W_BADPIN, W_BADCOMP, W_BADDRAW,
                    W_UNKDCM, W_UNKAR, W_ARNOPATH, W_ARNOREF, W_MISCFLD, W_EXTRASPC, W_NOLIB, W_INCPOS, W_NOANNO, W_MISSLIB,
                    W_MISSDCM, W_MISSCMP, W_MISFLDNAME, W_NOENDLIB, W_VALMISMATCH, W_MULTIREF, try_decode_utf8)
from .. import log

logger = log.get_logger()


class LineReader(object):
    def __init__(self, f, file):
        super().__init__()
        self.line = 0
        self.file = file
        self.f = f


class SCHLineReader(LineReader):
    def __init__(self, f, file):
        super().__init__(f, file)

    def get_line(self):
        res = self.f.readline()
        if not res:
            raise SchFileError('Unexpected end of file', '', self)
        self.line += 1
        return res.rstrip()


class LibLineReader(LineReader):
    def __init__(self, f, file):
        super().__init__(f, file)

    def get_line(self):
        res = self.f.readline()
        while res and res[0] == '#':
            if res.startswith('#End Library') or res.startswith('# End Library'):
                return res.rstrip()
            self.line += 1
            res = self.f.readline()
        if not res:
            raise SchLibError('Unexpected end of file', '', self)
        self.line += 1
        return res.rstrip()


class DCMLineReader(LineReader):
    def __init__(self, f, file):
        super().__init__(f, file)

    def readline(self):
        return try_decode_utf8(self.f.readline(), f'line {self.line+1} of file `{self.file}`', logger,
                               GS.global_code_page_fallback)

    def get_line(self):
        res = self.readline()
        while res and res[0] == '#':
            if res.startswith('#End Doc Library'):
                return res.rstrip()
            self.line += 1
            res = self.readline()
        if not res:
            raise SchLibError('Unexpected end of file', '', self)
        self.line += 1
        return res.rstrip()


def _split_space(s):
    res = s.lstrip().split(' ')
    return [a for a in res if a]


class LibComponentField(object):
    """ A field for a component in the library.
        Almost the same as a field in the schematic, but incompatible!!! """
    # F n "text" posx posy dimension orientation visibility hjustify vjustify/italic/bold "name"
    field_re = re.compile(r'F\s*(\d+)\s+'               # 0 Field number
                          r'"((?:[^\\]|(?:\\.))*)"\s+'  # 1 Field value
                          r'(-?\d+)\s+'                 # 2 Pos X
                          r'(-?\d+)\s+'                 # 3 Pos Y
                          r'(\d+)\s+'                   # 4 Dimension
                          r'([HV])\s+'                  # 5 Orientation
                          r'([VI])\s+'                  # 6 Visibility
                          r'([LRCBT])\s+'               # 7 HJustify
                          r'([LRCBT][IN][BN])\s*'       # 8 VJustify+Italic+Bold
                          r'("(?:[^\\]|(?:\\.))*")?')   # 9 Name for user fields
    fiel2_re = re.compile(r'F\s*(\d+)\s+'               # 0 Field number
                          r'"((?:[^\\]|(?:\\.))*)"\s+'  # 1 Field value
                          r'(-?\d+)\s+'                 # 2 Pos X
                          r'(-?\d+)\s+'                 # 3 Pos Y
                          r'(\d+)\s+'                   # 4 Dimension
                          r'([HV])\s+'                  # 5 Orientation
                          r'([VI])\s+'                  # 6 Visibility
                          r'([LRCBT])\s+'               # 7 HJustify
                          # KiCad never uses spaces between "CNN", but can load files with it
                          # Some generators seems to use it see #122
                          r'([LRCBT]\s*[IN]\s*[BN])\s*'  # 8 VJustify+Italic+Bold
                          r'("(?:[^\\]|(?:\\.))*")?')    # 9 Name for user fields

    def __init__(self):
        super().__init__()

    @staticmethod
    def parse(line, lib_name, f):
        m = LibComponentField.field_re.match(line)
        if not m:
            m = LibComponentField.fiel2_re.match(line)
            if not m:
                raise SchLibError('Malformed component field', line, f)
        field = LibComponentField()
        gs = m.groups()
        field.number = int(gs[0])
        field.value = gs[1]
        field.x = int(gs[2])
        field.y = int(gs[3])
        field.size = int(gs[4])
        field.horizontal = gs[5] == 'H'  # H -> True, V -> False
        field.visible = gs[6] == 'V'
        field.hjustify = gs[7]
        field.vjustify = gs[8][0]
        field.italic = gs[8][1] == 'I'
        field.bold = gs[8][2] == 'B'
        if gs[9]:
            field.name = gs[9][1:-1]
        else:
            if field.number > 3:
                logger.warning(W_MISFLDNAME + 'Missing component field name ({} line {})'.format(lib_name, f.line))
                # KiCad falls-back to `FieldN`
                field.name = 'Field'+str(field.number)
            else:
                field.name = ['Reference', 'Value', 'Footprint', 'Datasheet'][field.number]
        return field

    def write(self, f):
        s = 'F'+str(self.number)
        s += ' "{}" {} {} {} '.format(self.value, self.x, self.y, self.size)
        s += 'H' if self.horizontal else 'V'
        s += ' '
        s += 'V' if self.visible else 'I'
        s += ' '+self.hjustify+' '+self.vjustify
        s += 'I' if self.italic else 'N'
        s += 'B' if self.bold else 'N'
        if self.number > 3:
            s += ' "'+self.name+'"'
        f.write(s+'\n')


class DrawPoligon(object):
    pol_re = re.compile(r'P\s+(\d+)\s+'     # 0 Number of points
                        r'(\d+)\s+'         # 1 Sub-part (0 == all)
                        r'([012])\s+'       # 2 Which representation (0 == both) for DeMorgan
                        r'(-?\d+)\s+'       # 3 Thickness (Components from 74xx.lib has polygons with -1000)
                        r'((?:-?\d+\s+)+)'  # 4 The points
                        r'([NFf])')         # 5 Normal, Filled

    def __init__(self):
        super().__init__()

    @staticmethod
    def parse(line):
        m = DrawPoligon.pol_re.match(line)
        if not m:
            logger.warning(W_BADPOLI + 'Unknown polygon definition `{}`'.format(line))
            return None
        pol = DrawPoligon()
        g = m.groups()
        pol.points = int(g[0])
        pol.sub_part = int(g[1])
        pol.convert = int(g[2])
        pol.thickness = int(g[3])
        pol.fill = g[5]
        coords = _split_space(g[4])
        if len(coords) != 2*pol.points:
            logger.warning(W_POLICOORDS + 'Expected {} coordinates and got {} in polygon'.format(2*pol.points, len(coords)))
            pol.points = int(len(coords)/2)
        pol.coords = [int(c) for c in coords]
        return pol

    def write(self, f):
        f.write('P {} {} {} {}'.format(self.points, self.sub_part, self.convert, self.thickness))
        for p in self.coords:
            f.write(' '+str(p))
        f.write(' '+self.fill+'\n')

    def get_rect(self):
        if not self.points:
            return 0, 0, 0, 0, False
        xm = xM = self.coords[0]
        ym = yM = self.coords[1]
        for i in range(1, self.points):
            x = self.coords[i*2]
            y = self.coords[i*2+1]
            xm = min(x, xm)
            xM = max(x, xM)
            ym = min(y, ym)
            yM = max(y, yM)
        return xm, ym, xM, yM, True


class DrawRectangle(object):
    rec_re = re.compile(r'S\s+'
                        r'(-?\d+)\s+'   # 0 Start X
                        r'(-?\d+)\s+'   # 1 Start Y
                        r'(-?\d+)\s+'   # 2 End X
                        r'(-?\d+)\s+'   # 3 End X
                        r'(\d+)\s+'     # 4 Sub-part (0 == all)
                        r'([012])\s+'   # 5 Which representation (0 == both) for DeMorgan
                        r'(\d+)\s+'     # 6 Thickness
                        r'([NFf])')     # 7 Normal, Filled

    def __init__(self):
        super().__init__()

    @staticmethod
    def parse(line):
        m = DrawRectangle.rec_re.match(line)
        if not m:
            logger.warning(W_BADSQUARE + 'Unknown square definition `{}`'.format(line))
            return None
        rec = DrawRectangle()
        g = m.groups()
        rec.start_x = int(g[0])
        rec.start_y = int(g[1])
        rec.end_x = int(g[2])
        rec.end_y = int(g[3])
        rec.sub_part = int(g[4])
        rec.convert = int(g[5])
        rec.thickness = int(g[6])
        rec.fill = g[7]
        return rec

    def write(self, f):
        f.write('S {} {} {} {}'.format(self.start_x, self.start_y, self.end_x, self.end_y))
        f.write(' {} {} {} {}\n'.format(self.sub_part, self.convert, self.thickness, self.fill))

    def get_rect(self):
        xm = min(self.start_x, self.end_x)
        ym = min(self.start_y, self.end_y)
        xM = max(self.start_x, self.end_x)
        yM = max(self.start_y, self.end_y)
        return xm, ym, xM, yM, True


class DrawCircle(object):
    cir_re = re.compile(r'C\s+'
                        r'(-?\d+)\s+'   # 0 Pos X
                        r'(-?\d+)\s+'   # 1 Pos Y
                        r'(\d+)\s+'     # 2 Radius
                        r'(\d+)\s+'     # 3 Sub-part (0 == all)
                        r'([012])\s+'   # 4 Which representation (0 == both) for DeMorgan
                        r'(\d+)\s+'     # 5 Thickness
                        r'([NFf])')     # 6 Normal, Filled

    def __init__(self):
        super().__init__()

    @staticmethod
    def parse(line):
        m = DrawCircle.cir_re.match(line)
        if not m:
            logger.warning(W_BADCIRCLE + 'Unknown circle definition `{}`'.format(line))
            return None
        cir = DrawCircle()
        g = m.groups()
        cir.pos_x = int(g[0])
        cir.pos_y = int(g[1])
        cir.radius = int(g[2])
        cir.sub_part = int(g[3])
        cir.convert = int(g[4])
        cir.thickness = int(g[5])
        cir.fill = g[6]
        return cir

    def write(self, f):
        f.write('C {} {} {}'.format(self.pos_x, self.pos_y, self.radius))
        f.write(' {} {} {} {}\n'.format(self.sub_part, self.convert, self.thickness, self.fill))

    def get_rect(self):
        xm = self.pos_x-self.radius
        ym = self.pos_y-self.radius
        xM = self.pos_x+self.radius
        yM = self.pos_y+self.radius
        return xm, ym, xM, yM, True


class DrawArc(object):
    arc_re = re.compile(r'A\s+'
                        r'(-?\d+)\s+'   # 0 Pos X
                        r'(-?\d+)\s+'   # 1 Pos Y
                        r'(\d+)\s+'     # 2 Radius
                        r'(-?\d+)\s+'   # 3 Start
                        r'(-?\d+)\s+'   # 4 End
                        r'(\d+)\s+'     # 5 Sub-part (0 == all)
                        r'([012])\s+'   # 6 Which representation (0 == both) for DeMorgan
                        r'(\d+)\s+'     # 7 Thickness
                        r'([NFf])\s+'   # 8 Normal, Filled
                        r'(-?\d+)\s+'   # 9 Start Pos X
                        r'(-?\d+)\s+'   # 10 Start Pos Y
                        r'(-?\d+)\s+'   # 11 End Pos X
                        r'(-?\d+)')     # 12 End Pos Y

    def __init__(self):
        super().__init__()

    @staticmethod
    def parse(line):
        m = DrawArc.arc_re.match(line)
        if not m:
            logger.warning(W_BADARC + 'Unknown arc definition `{}`'.format(line))
            return None
        arc = DrawArc()
        g = m.groups()
        arc.pos_x = int(g[0])
        arc.pos_y = int(g[1])
        arc.radius = int(g[2])
        arc.start = int(g[3])
        arc.end = int(g[4])
        arc.sub_part = int(g[5])
        arc.convert = int(g[6])
        arc.thickness = int(g[7])
        arc.fill = g[8]
        arc.start_x = int(g[9])
        arc.start_y = int(g[10])
        arc.end_x = int(g[11])
        arc.end_y = int(g[12])
        return arc

    def write(self, f):
        f.write('A {} {} {}'.format(self.pos_x, self.pos_y, self.radius))
        f.write(' {} {}'.format(self.start, self.end))
        f.write(' {} {} {} {}'.format(self.sub_part, self.convert, self.thickness, self.fill))
        f.write(' {} {} {} {}\n'.format(self.start_x, self.start_y, self.end_x, self.end_y))

    def get_rect(self):
        xm = self.pos_x-self.radius
        ym = self.pos_y-self.radius
        xM = self.pos_x+self.radius
        yM = self.pos_y+self.radius
        return xm, ym, xM, yM, True


class DrawText(object):
    txt_re = re.compile(r'T\s+'
                        r'(\d+)\s+'                  # 0 Orientation (0 horizontal)
                        r'(-?\d+)\s+'                # 1 Pos X
                        r'(-?\d+)\s+'                # 2 Pos Y
                        r'(\d+)\s+'                  # 3 Dimension
                        r'(\d+)\s+'                  # 4 Type?
                        r'(\d+)\s+'                  # 5 Sub-part (0 == all)
                        r'([012])\s+'                # 6 Which representation (0 == both) for DeMorgan
                        r'(\S+|"(?:[^"]|\\")+")\s+'  # 7 Text
                        r'(Normal|Italic)\s+'        # 8 Italic
                        r'([01])\s+'                 # 9 Bold
                        r'([CLR])\s+'                # 10 HJustify
                        r'([CBT])')                  # 11 VJustify

    def __init__(self):
        super().__init__()

    @staticmethod
    def parse(line):
        m = DrawText.txt_re.match(line)
        if not m:
            logger.warning(W_BADTEXT + 'Unknown text definition `{}`'.format(line))
            return None
        txt = DrawText()
        g = m.groups()
        txt.orientation = int(g[0])
        txt.pos_x = int(g[1])
        txt.pos_y = int(g[2])
        txt.size = int(g[3])
        txt.type = int(g[4])
        txt.sub_part = int(g[5])
        txt.convert = int(g[6])
        txt.text = un_quote(g[7])
        txt.italic = g[8] == 'Italic'
        txt.bold = g[9] == '1'
        txt.hjustify = g[10]
        txt.vjustify = g[11]
        return txt

    def write(self, f):
        f.write('T {} {} {} {}'.format(self.orientation, self.pos_x, self.pos_y, self.size))
        f.write(' {} {} {} "{}"'.format(self.type, self.sub_part, self.convert, self.text))
        f.write(' {} {} {} {}\n'.format(['Normal', 'Italic'][self.italic], int(self.bold), self.hjustify, self.vjustify))

    def get_rect(self):
        return 0, 0, 0, 0, False


class Pin(object):
    pin_re = re.compile(r'X\s+'
                        r'(\S+)\s+'         # 0 Name (~ for empty)
                        r'(\S+)\s+'         # 1 "Number" (alphanumeric)
                        r'(-?\d+)\s+'       # 2 Pos X
                        r'(-?\d+)\s+'       # 3 Pos Y
                        r'(\d+)\s+'         # 4 Length
                        r'([RLUD])\s+'      # 5 Direction
                        r'(\d+)\s+'         # 6 Text size for the pin name
                        r'(\d+)\s+'         # 7 Text size for the pin number
                        r'(\d+)\s+'         # 8 Sub-part (0 == all)
                        r'([012])\s+'       # 9 Which representation (0 == both) for DeMorgan
                        r'([IOBTPUWwCEN])'  # 10 Electrical type
                        r'((?:\s+)\S+)?')   # 11 Graphic type
    type2name = {'I': 'input', 'O': 'output', 'B': 'BiDi', 'T': '3state', 'P': 'passive', 'U': 'unspc',
                 'W': 'power_in', 'w': 'power_out', 'C': 'openCol', 'E': 'openEm', 'N': 'NotConnected'}

    def __init__(self):
        super().__init__()

    @staticmethod
    def parse(line):
        m = Pin.pin_re.match(line)
        if not m:
            logger.warning(W_BADPIN + 'Unknown pin definition `{}`'.format(line))
            return None
        pin = Pin()
        g = m.groups()
        pin.name = g[0]
        pin.number = g[1]
        pin.pos_x = int(g[2])
        pin.pos_y = int(g[3])
        pin.len = int(g[4])
        pin.dir = g[5]
        pin.size_name = int(g[6])
        pin.size_num = int(g[7])
        pin.sub_part = int(g[8])
        pin.convert = int(g[9])
        pin.type = g[10]
        pin.gtype = g[11]
        return pin

    def write(self, f):
        f.write('X {} {} {} {}'.format(self.name, self.number, self.pos_x, self.pos_y))
        f.write(' {} {} {} {}'.format(self.len, self.dir, self.size_name, self.size_num))
        f.write(' {} {} {}'.format(self.sub_part, self.convert, self.type))
        if self.gtype:
            f.write(' '+self.gtype)
        f.write('\n')

    def get_rect(self):
        if self.dir == 'U':
            return self.pos_x, self.pos_y, self.pos_x, self.pos_y+self.len, True
        if self.dir == 'D':
            return self.pos_x, self.pos_y-self.len, self.pos_x, self.pos_y, True
        if self.dir == 'R':
            return self.pos_x, self.pos_y, self.pos_x+self.len, self.pos_y, True
        if self.dir == 'L':
            return self.pos_x-self.len, self.pos_y, self.pos_x, self.pos_y, True
        return 0, 0, 0, 0, False


class LibComponent(object):
    def_re = re.compile(r'DEF\s+'
                        r'(\S+)\s+'     # 0 Name
                        r'(\S+)\s+'     # 1 Reference prefix
                        r'(\S+)\s+'     # 2 Unused field (0)
                        r'(-?\d+)\s+'   # 3 Text offset
                        r'([YN])\s+'    # 4 Draw pin number
                        r'([YN])\s+'    # 5 Draw pin name
                        r'(\d+)\s+'     # 6 Unit count
                        r'([LF])\s+'    # 7 Unit is locked
                        r'([NP])')      # 8 Power/Normal

    def __init__(self, line, f, lib_name):
        super().__init__()
        self.dcm = None  # Extra info from the Doc-Lib (DCM) file
        m = self.def_re.match(line)
        if m:
            g = m.groups()
            self.name = g[0]
            self.ref_prefix = g[1]
            self.unused = g[2]
            self.text_offset = int(g[3])
            self.draw_pinnumber = g[4] == 'Y'
            self.draw_pinname = g[5] == 'Y'
            self.unit_count = int(g[6])
            self.units_locked = g[7] == 'L'
            self.is_power = g[8] == 'P'
            if self.name[0] == '~':
                self.name = self.name[1:]
                self.vname = True
            else:
                self.vname = False
            if GS.debug_level > 2:
                logger.debug('- Loading component {} from {}'.format(self.name, lib_name))
        else:
            logger.warning(W_BADCOMP + 'Failed to load component definition: `{}`'.format(line))
            # Mark it as broken
            self.name = None
        self.fields = []
        self.dfields = {}
        self.alias = None
        self.fp_list = []
        self.draw = []
        self.pins = []
        line = f.get_line()
        while not line.startswith('ENDDEF'):
            if len(line) == 0:
                # Skip empty lines
                line = f.get_line()
                continue
            if line[0] == 'F':
                # A field
                field = LibComponentField.parse(line, lib_name, f)
                self.fields.append(field)
                self.dfields[field.name.lower()] = field
            elif line.startswith('ALIAS'):
                self.alias = _split_space(line[6:])
            elif line.startswith('$FPLIST'):
                line = f.get_line()
                while not line.startswith('$ENDFPLIST'):
                    self.fp_list.append(line[1:])
                    line = f.get_line()
            elif line.startswith('DRAW'):
                line = f.get_line()
                while not line.startswith('ENDDRAW'):
                    if line[0] == 'P':
                        self.draw.append(DrawPoligon.parse(line))
                    elif line[0] == 'S':
                        self.draw.append(DrawRectangle.parse(line))
                    elif line[0] == 'C':
                        self.draw.append(DrawCircle.parse(line))
                    elif line[0] == 'A':
                        self.draw.append(DrawArc.parse(line))
                    elif line[0] == 'T':
                        self.draw.append(DrawText.parse(line))
                    elif line[0] == 'X':
                        pin = Pin.parse(line)
                        self.draw.append(pin)
                        self.pins.append(pin)
                    else:
                        logger.warning(W_BADDRAW + 'Unknown draw element `{}`'.format(line))
                    line = f.get_line()
            line = f.get_line()
            self.all_pins = self.pins

    def get_field_value(self, field):
        field = field.lower()
        if field in self.dfields:
            return self.dfields[field].value
        return ''

    def write(self, f, id, cross=False):
        """ cross is used to cross the component (DNF) """
        id = id.replace(':', '_')
        if self.vname:
            id = '~'+id
        f.write('#\n# '+id+'\n#\n')
        f.write('DEF {} {} {} {} {} {} {} {} {}\n'.
                format(id, self.ref_prefix, self.unused, self.text_offset, ['N', 'Y'][self.draw_pinnumber],
                       ['N', 'Y'][self.draw_pinname], self.unit_count, ['F', 'L'][self.units_locked],
                       ['N', 'P'][self.is_power]))
        for field in self.fields:
            field.write(f)
        f.write('$FPLIST\n')
        for fp in self.fp_list:
            f.write(' '+fp+'\n')
        f.write('$ENDFPLIST\n')
        if self.alias:
            f.write('ALIAS '+' '.join(self.alias)+'\n')
        f.write('DRAW\n')
        for dr in self.draw:
            dr.write(f)
        if cross:
            # Generated the crossed stuff
            # logger.debug('Computing size for {}:'.format(id))
            for unit in range(self.unit_count):
                xmt = ymt = 1e6
                xMt = yMt = -1e6
                ok_t = False
                # logger.debug("Unit "+str(unit+1))
                for dr in self.draw:
                    if dr.sub_part != unit + 1 and dr.sub_part != 0:
                        continue
                    xm, ym, xM, yM, ok = dr.get_rect()
                    # logger.debug([dr, xm, ym, xM, yM, ok])
                    if ok:
                        ok_t = True
                        xmt = min(xm, xmt)
                        ymt = min(ym, ymt)
                        xMt = max(xM, xMt)
                        yMt = max(yM, yMt)
                if ok_t:
                    # Cross this component using 2 lines
                    o = DrawPoligon()
                    o.points = 2
                    o.sub_part = unit+1
                    o.convert = 0
                    o.thickness = 30
                    o.fill = 'N'
                    o.coords = [xmt, ymt, xMt, yMt]
                    o.write(f)
                    o.coords = [xmt, yMt, xMt, ymt]
                    o.write(f)
        f.write('ENDDRAW\n')
        f.write('ENDDEF\n')


#     def __repr__(self):
#         s = 'Component('+self.name
#         if self.desc:
#             s += " desc: '{}'".format(self.desc)
#         s += ')'
#         return s


class SymLib(object):
    """ Content from a symbols library """
    def __init__(self):
        super().__init__()
        self.comps = OrderedDict()
        self.alias = {}

    @staticmethod
    def _check_add(o, id, lib, needed, translate):
        if lib is None:
            # From a cache
            if id in translate:
                needed[translate[id]] = o
                return True
            return False
        name = lib+':'+id
        if name in needed:
            needed[name] = o
            return True
        else:
            name = 'None:'+id
            if name in needed:
                needed[name] = o
                return True
        return False

    def load(self, file, lib_alias, needed):
        """ Populates the class, file must exist """
        logger.debug('Loading library `{}`'.format(file))
        with open(file, 'rt') as fh:
            f = LibLineReader(fh, file)
            line = f.get_line()
            if not line.startswith('EESchema-LIBRARY'):
                if file.endswith('kicad_sym'):
                    raise SchLibError('Mixing KiCad 5 and KiCad 6 files is not allowed', line, f)
                raise SchLibError('Missing library signature', line, f)
            line = f.get_line()
            translate = {k.replace(':', '_'): k for k, v in needed.items() if v is None} if lib_alias is None else None
            while not (line.startswith('#End Library') or line.startswith('# End Library')):
                if line.startswith('DEF'):
                    o = LibComponent(line, f, file)
                    if o.name:
                        # Only add components we need
                        if self._check_add(o, o.name, lib_alias, needed, translate):
                            self.comps[o.name] = o
                        if o.alias and lib_alias is not None:
                            for a in o.alias:
                                if self._check_add(o, a, lib_alias, needed, translate):
                                    self.alias[a] = o
                else:
                    raise SchLibError('Unknown library entry', line, f)
                try:
                    line = f.get_line()
                except SchLibError:
                    logger.warning(W_NOENDLIB + 'Library without end of file comment: `{}`'.format(file))
                    break


class DocLibEntry(object):
    def __init__(self, name, f):
        super().__init__()
        self.name = name
        self.desc = None
        self.keys = None
        self.datasheet = None
        line = f.get_line()
        while not line.startswith('$ENDCMP'):
            if line[0] == 'D':
                self.desc = line[2:].lstrip()
            elif line[0] == 'K':
                self.keys = _split_space(line[2:])
            elif line[0] == 'F':
                self.datasheet = line[2:].lstrip()
            else:
                logger.warning(W_UNKDCM + 'Unknown DCM attribute `{}` on line {}'.format(line, f.line))
            line = f.get_line()

    def __repr__(self):
        s = 'DCM('+self.name
        if self.desc:
            s += " desc: '{}'".format(self.desc)
        s += ')'
        return s


class DocLib(object):
    """ Content from a DCM """
    def __init__(self):
        super().__init__()
        self.comps = OrderedDict()

    def load(self, file):
        """ Populates the class, file must exist """
        logger.debug('Loading doc-lib `{}`'.format(file))
        with open(file, 'rb') as fh:
            f = DCMLineReader(fh, file)
            line = f.get_line()
            if not line.startswith('EESchema-DOCLIB'):
                raise SchLibError('Missing DCM signature', line, f)
            line = f.get_line()
            while not line.startswith('#End Doc Library'):
                if line.startswith('$CMP'):
                    o = DocLibEntry(line[5:].lstrip(), f)
                    self.comps[o.name] = o
                    if GS.debug_level > 1:
                        logger.debug('- '+repr(o))
                else:
                    raise SchLibError('Unknown DCM entry', line, f)
                line = f.get_line()


class SchematicField(object):
    # F n "text" orientation posx posy dimension flags hjustify vjustify/italic/bold "name"
    field_re = re.compile(r'F\s*(\d+)\s+"((?:[^\\]|(?:\\.))*)"\s+([HV])\s+(-?\d+)\s+(-?\d+)\s+(\d+)\s+(\d+)'
                          r'\s+([LRCBT])\s+([LRCBT][IN][BN])\s*("(?:[^\\]|(?:\\.))*")?')

    def __init__(self):
        super().__init__()
        self.horizontal = True  # H -> True, V -> False
        self.x = 0
        self.y = 0
        self.size = 50
        self.flags = '0001'
        self.hjustify = 'C'
        self.vjustify = 'C'
        self.italic = False
        self.bold = False

    def visible(self, v):
        v = 0 if v else 1
        self.flags = "%04x" % ((int(self.flags) & 0xFFFE) | v)

    def is_visible(self):
        return not (int(self.flags, 16) and 1)

    def get_height(self):
        """ Font height in mm """
        return self.size*0.0254

    def get_xy(self):
        return self.x*0.0254, -self.y*0.0254

    def set_xy(self, x, y, hjustify=None):
        self.x = int(x/0.0254)
        self.y = -int(y/0.0254)
        if hjustify:
            self.hjustify = hjustify

    @staticmethod
    def parse(line, f):
        m = SchematicField.field_re.match(line)
        if not m:
            raise SchFileError('Malformed component field', line, f)
        field = SchematicField()
        gs = m.groups()
        field.number = int(gs[0])
        field.value = gs[1]
        field.horizontal = gs[2] == 'H'  # H -> True, V -> False
        field.x = int(gs[3])
        field.y = int(gs[4])
        field.size = int(gs[5])
        field.flags = gs[6]
        field.hjustify = gs[7]
        field.vjustify = gs[8][0]
        field.italic = gs[8][1] == 'I'
        field.bold = gs[8][2] == 'B'
        if gs[9]:
            field.name = gs[9][1:-1]
        else:
            if field.number > 3:
                raise SchFileError('Missing component field name', line, f)
            field.name = ['Reference', 'Value', 'Footprint', 'Datasheet'][field.number]
        return field

    def write(self, f):
        f.write('F {} "{}" {}'.format(self.number, self.value, ['V', 'H'][self.horizontal]))
        f.write(' {} {} {} {}'.format(self.x, self.y, self.size, self.flags))
        f.write(' {} {}{}{}'.format(self.hjustify, self.vjustify, ['N', 'I'][self.italic], ['N', 'B'][self.bold]))
        if self.number > 3:
            f.write(' "{}"'.format(self.name))
        f.write('\n')

    def __str__(self):
        return self.name+'='+self.value


class SchematicAltRef():
    def __init__(self):
        super().__init__()
        self.path = None
        self.ref = None
        self.part = None

    @staticmethod
    def parse(line):
        ar = SchematicAltRef()
        res = _split_space(line[3:])
        for r in res:
            if r.startswith('Path='):
                ar.path = r[6:-1]
            elif r.startswith('Ref='):
                ar.ref = r[5:-1]
            elif r.startswith('Part='):
                ar.part = r[6:-1]
            else:
                logger.warning(W_UNKAR + 'Unknown AR field `{}`'.format(r))
        if not ar.path:
            logger.warning(W_ARNOPATH + 'Alternative Reference without path `{}`'.format(line))
        if not ar.ref:
            logger.warning(W_ARNOREF + 'Alternative Reference without reference `{}`'.format(line))
        return ar

    def write(self, f):
        f.write('AR')
        if self.path:
            f.write(' Path="{}"'.format(self.path))
        if self.ref:
            f.write(' Ref="{}"'.format(self.ref))
        if self.part:
            f.write(' Part="{}"'.format(self.part))
        f.write('\n')


class SchematicComponent(object):
    """ Class for a component in the schematic.
        Here are special members currently computed elsehere:
        - fitted: equivalent to 'Exclude from board' but inverted
                  - Solded: only if True
                  - BoM normal: only if True
                  - BoM DNF: only if False
        - included: related to 'Exclude from BoM' but inverted,
                   but also applied to other situations.
                  - Solded: doesn't affected
                  - BoM normal: only if True
                  - BoM DNF: only if True (and fitted is False)
        - fixed: means you can't change it by a replacement without authorization
                 Is just a flag and doesn't affect much.
        - footprint_rot: angle to rotate the part in the pick & place.
        - footprint_x: x position of the part in the pick & place.
        - footprint_y: y position of the part in the pick & place.
        - footprint_w: width of the footprint (pads only).
        - footprint_h: height of the footprint (pads only)
        - qty: amount of this part used.
        - kicad_dnp: is the KiCad v7 DNP flag. If not defined (v5/6) is None and is like False.
        """
    ref_re = re.compile(r'([^\d]+)([\?\d]+)')

    def __init__(self):
        super().__init__()
        self.field_ref = ''
        self.value = ''
        self.footprint = ''
        self.footprint_lib = None
        self.datasheet = ''
        self.desc = ''
        self.fields = []
        self.dfields = {}
        self.fields_bkp = None
        self.dfields_bkp = None
        # Will be computed
        self.fitted = True
        self.included = True
        self.fixed = False
        self.bottom = False
        self.footprint_rot = 0.0
        self.footprint_x = self.footprint_y = 0
        self.footprint_w = self.footprint_h = 0
        self.has_pcb_info = False
        self.qty = 1
        self.annotation_error = False
        self.net_name = self.net_class = ''
        # The following is used by transform variants that creates components derived from another
        self.parent_component = None
        # Position offset i.e. from the rotation filter
        self.pos_offset_x = self.pos_offset_y = None
        # KiCad 5 PCB flags (mutually exclusive)
        self.smd = False
        self.virtual = False
        self.tht = False
        # KiCad 6 SCH flags
        self.in_bom = True          # not Exclude from bill of materials
        self.in_bom_sch = True      # back-up copy
        self.on_board = True        # not Exclude from BoM
        # KiCad 6 PCB flags
        self.in_bom_pcb = True      # not Exclude from bill of materials
        self.in_pos = True          # not Exclude from position files
        self.in_pcb_only = False    # Not in schematic
        # KiCad 7 PCB flags
        self.kicad_dnp = None       # Do Not Populate
        self.kicad_dnp_sch = None   # back-up copy
        # KiCad 10
        self.in_pos_files = None
        self.duplicate_pin_numbers_are_jumpers = None
        # Exclude from simulation is a field Sim.Enable

    def get_field_value(self, field, lower=False):
        if isinstance(field, list):
            res = []
            for f in field:
                f = f.lower()
                val = self.dfields[f].value if f in self.dfields else ''
                res.append(val.lower() if lower else val)
            return res
        field = field.lower()
        if field in self.dfields:
            val = self.dfields[field].value
            return val.lower() if lower else val
        return ''

    def is_field(self, field):
        return field in self.dfields

    def get_free_field_number(self):
        """ Looks for a field number that isn't currently in use """
        max_num = -1
        for f in self.fields:
            if f.number > max_num:
                max_num = f.number
        return max_num+1

    def set_field(self, field, value, visible=None):
        """ Change the value for an existing field.
            Or create a new one (returns True). """
        field_lc = field.lower()
        if field_lc in self.dfields:
            target = self.dfields[field_lc]
            target.value = value
            # Adjust special fields
            if target.number < 4:
                self._solve_fields(LineReader(None, '**Internal**'))
            if visible is not None:
                target.visible(visible)
            return False, target
        f = type(self.fields[0])()
        f.name = field
        f.value = value
        f.number = self.get_free_field_number()
        f.visible(bool(visible))
        if hasattr(self, 'x'):
            f.x = self.x
            f.y = self.y
        self.add_field(f)
        return True, f

    def get_visible_fields(self):
        return [f for f in self.fields if f.is_visible()]

    def get_field_names(self):
        """ List of all the available field names for this component """
        return self.dfields.keys()

    def get_real_field_names(self, names):
        """ Returns the real names, using the lowercase ones """
        return [self.dfields[n].name for n in names]

    def get_user_fields(self):
        """ Returns a list of tuples with the user defined fields (name, value) """
        return [(f.name, f.value) for f in self.fields if f.number > 3]

    def add_field(self, field):
        self.fields.append(field)
        self.dfields[field.name.lower()] = field

    def rename_field(self, old_name, new_name):
        old_name = old_name.lower()
        field = self.dfields[old_name]
        field.name = new_name
        del self.dfields[old_name]
        self.dfields[new_name.lower()] = field

    def back_up_fields(self):
        """ First call makes a back-up of the fields.
            Next calls restores the back-up. """
        if self.fields_bkp:
            # We have a back-up, restore from it
            self.fields = deepcopy(self.fields_bkp)
            self.dfields = {f.name.lower(): f for f in self.fields}
            self._solve_fields(LineReader(None, '**Internal**'))
        else:
            # No back-up. Make one for the next reset
            self.fields_bkp = deepcopy(self.fields)
            self.dfields_bkp = {f.name.lower(): f for f in self.fields_bkp}

    def set_fitted(self, status):
        self.fitted = status
        if self.parent_component:
            self.parent_component.set_fitted(status)

    def set_fixed(self, status):
        self.fixed = status
        if self.parent_component:
            self.parent_component.set_fixed(status)

    def get_parent_ref(self):
        return self.ref if not self.parent_component else self.parent_component.get_parent_ref()

    def _solve_ref(self, path):
        """ Look for the correct reference for this path.
            Returns the default reference if no paths defined.
            Returns the first not empty reference if the current is empty. """
        ref = self.f_ref
        # If the reference is empty try the reference field
        if ref[-1] == '?' and self.field_ref and self.field_ref[-1] != '?':
            ref = self.fields[0].value
        if self.ar:
            path += '/'+self.id
            for o in self.ar:
                if o.path == path and o.ref[-1] != '?':
                    return o.ref
                if ref[-1] == '?' and o.ref[-1] != '?':
                    ref = o.ref
        return ref

    def _solve_fields(self, fr):
        """ Fills the default fields from the fields attribute """
        f = self.fields
        self.field_ref = None
        self.value = None
        self.footprint = None
        self.footprint_lib = None
        self.datasheet = None
        basic = 0
        for f in self.fields:
            if f.number == 0:
                self.field_ref = f.value
                basic += 1
            elif f.number == 1:
                self.value = f.value
                basic += 1
            elif f.number == 2:
                res = f.value.split(':')
                cres = len(res)
                if cres == 1:
                    self.footprint = res[0]
                elif cres == 2:
                    self.footprint_lib = res[0]
                    self.footprint = res[1]
                else:
                    if fr:
                        raise SchFileError('Footprint with more than one colon', f.value, fr)
                    else:
                        raise SchError('Footprint with more than one colon (`{}`)'.format(f.value))
                basic += 1
            elif f.number == 3:
                self.datasheet = f.value
                basic += 1
        if basic < 4:
            ref = getattr(self, "f_ref", self.ref)
            logger.warning(W_MISCFLD + f'Component `{ref}` without the basic fields')

    def _validate(self):
        for field in self.fields:
            cur_val = field.value
            stripped_val = cur_val.strip()
            if len(cur_val) != len(stripped_val):
                logger.warning(W_EXTRASPC + "Field {} of component {} contains extra spaces: `{}` removing them.".
                               format(field.name, self, field.value))
                field.value = stripped_val

    def __str__(self):
        ref = self.ref if self.ref is not None else '??'
        # Add the sub-part id
        # How to know if unit 1 is A?
        if self.unit is not None and self.unit > 1:
            ref += chr(ord('A')+self.unit-1)
        if self.name == self.value:
            return '{} ({})'.format(ref, self.name)
        return '{} ({} {})'.format(ref, self.name, self.value)

    def split_ref(self, f=None):
        m = SchematicComponent.ref_re.match(self.ref)
        if not m:
            pos = f'(@ {self.x},{self.y})' if hasattr(self, 'x') else ''
            if f:
                raise SchFileError(f'Malformed component reference {pos}', self.ref, f)
            else:
                raise SchError(f'Malformed component reference `{self.ref}` {pos}')
        self.ref_prefix, self.ref_suffix = m.groups()

    @staticmethod
    def load(f, project, sheet_path, sheet_path_h, libs, fields, fields_lc):
        # L lib:name reference
        line = f.get_line()
        if not line or line[0] != 'L':
            raise SchFileError('Missing component label', line, f)
        res = _split_space(line[2:])
        if len(res) != 2:
            raise SchFileError('Malformed component label', line, f)
        comp = SchematicComponent()
        comp.project = project
        comp.name, comp.f_ref = res
        res = comp.name.split(':')
        comp.lib = None
        if len(res) == 2:
            comp.name = res[1]
            comp.lib = res[0]
            libs[comp.lib] = None
        else:
            logger.warning(W_NOLIB + "Component `{}` doesn't specify its library".format(comp.name))
        # U N mm time_stamp
        line = f.get_line()
        if line[0] != 'U':
            raise SchFileError('Missing component unit', line, f)
        res = _split_space(line[2:])
        if len(res) != 3:
            raise SchFileError('Malformed component unit', line, f)
        comp.unit = int(res[0])
        comp.unit2 = int(res[1])
        comp.id = res[2]
        # P x y
        line = f.get_line()
        if line[0] != 'P':
            raise SchFileError('Missing component position', line, f)
        res = _split_space(line[2:])
        if len(res) != 2:
            raise SchFileError('Malformed component position', line, f)
        comp.x = int(res[0])
        comp.y = int(res[1])
        # Optional "Alternative References"
        line = f.get_line()
        comp.ar = []
        while line[:2] == 'AR':
            comp.ar.append(SchematicAltRef.parse(line))
            line = f.get_line()
        # F field_number "text" orientation posX posY size Flags (see below) hjustify vjustify/italic/bold "name"
        while line[0] == 'F':
            field = SchematicField.parse(line, f)
            name_lc = field.name.lower()
            # Add to the global collection
            if name_lc not in fields_lc:
                fields.append(field.name)
                fields_lc.add(name_lc)
            # Add to the component
            comp.add_field(field)
            line = f.get_line()
        # Fake 'Part' field
        field = SchematicField()
        field.name = 'part'
        field.value = comp.name
        field.number = -1
        field.visible(False)
        comp.add_field(field)
        # Redundant pos
        if not line.startswith('\t'+str(comp.unit)):
            raise SchFileError('Missing component redundant position', line, f)
        res = _split_space(line[1:])
        if len(res) != 3:
            raise SchFileError('Malformed component redundant position', line, f)
        xr = int(res[1])
        yr = int(res[2])
        if comp.x != xr or comp.y != yr:
            logger.warning(W_INCPOS + 'Inconsistent position for component {} ({},{} vs {},{})'.
                           format(comp.f_ref, comp.x, comp.y, xr, yr))
        # Orientation matrix
        line = f.get_line()
        if line[0] != '\t':
            raise SchFileError('Missing component orientation matrix', line, f)
        res = _split_space(line[1:])
        if len(res) != 4:
            raise SchFileError('Malformed component orientation matrix', line, f)
        comp.matrix = [int(v) for v in res]
        line = f.get_line()
        while not line.startswith('$EndComp'):
            line = f.get_line()
        comp._solve_fields(f)
        comp.ref = comp._solve_ref(sheet_path)
        # Power, ground or power flag
        comp.is_power = comp.ref.startswith('#PWR') or comp.ref.startswith('#FLG')
        if comp.ref[-1] == '?':
            logger.warning(W_NOANNO + 'Component {} is not annotated'.format(comp))
            comp.annotation_error = True
        # Separate the reference in its components
        comp.split_ref(f)
        # Location in the project
        comp.sheet_path = sheet_path
        comp.sheet_path_h = sheet_path_h
        if GS.debug_level > 1:
            logger.debug("- Loaded component {}".format(comp))
        # Report abnormal situations
        comp._validate()
        return comp

    def write(self, f, crossed=False):
        if crossed:
            # Fake lib to reflect fitted status
            lib = 'y' if self.fitted or not self.included else 'n'
            # Fake name using cache style
            name = '{}:{}_{}'.format(lib, self.lib, self.name)
        else:
            name = '{}:{}'.format(self.lib, self.name)
        f.write('$Comp\n')
        f.write('L {} {}\n'.format(name, self.f_ref))
        f.write('U {} {} {}\n'.format(self.unit, self.unit2, self.id))
        f.write('P {} {}\n'.format(self.x, self.y))
        for ar in self.ar:
            ar.write(f)
        for field in self.fields:
            if field.number >= 0:
                field.write(f)
        f.write('\t{} {} {}\n'.format(self.unit, self.x, self.y))
        f.write('\t{} {} {} {}\n'.format(self.matrix[0], self.matrix[1], self.matrix[2], self.matrix[3]))
        f.write('$EndComp\n')


class SchematicConnection(object):
    conn_re = re.compile(r'\s*~\s+(-?\d+)\s+(-?\d+)')

    def __init__(self):
        super().__init__()

    @staticmethod
    def parse(connect, line, f):
        m = SchematicConnection.conn_re.match(line)
        if not m:
            raise SchFileError('Malformed no/connection', line, f)
        c = SchematicConnection()
        c.connect = connect
        c.x = int(m.group(1))
        c.y = int(m.group(2))
        return c

    def write(self, f):
        f.write('{} ~ {} {}\n'.format(['NoConn', 'Connection'][self.connect], self.x, self.y))


class SchematicText(object):
    label_re = re.compile(r'Text\s+(Notes|HLabel|GLabel|Label)\s+(-?\d+)\s+(-?\d+)\s+(\d)\s+(\d+)\s+(\S+)')
    TYPES = ['Notes', 'HLabel', 'GLabel', 'Label']

    def __init__(self):
        super().__init__()

    @staticmethod
    def load(f, line):
        gs = _split_space(line)
        c = len(gs)
        if c < 6 or gs[0] != 'Text' or gs[1] not in SchematicText.TYPES:
            raise SchFileError('Malformed `Text`', line, f)
        text = SchematicText()
        text.type = gs[1]
        try:
            text.x = int(gs[2])
            text.y = int(gs[3])
            text.orient = int(gs[4])
            text.size = int(gs[5])
            offset = 6
            text.shape = None
            if gs[1][0] in 'GH':
                if c < 7:
                    raise SchFileError('Missing `Text` shape', line, f)
                text.shape = gs[6]
                offset += 1
            # New versions adds Italics and Bold, in a different way of course
            text.italic = False
            if c > offset:
                text.italic = gs[offset] == 'Italic'
                offset += 1
            text.thickness = 0
            if c > offset:
                text.thickness = int(gs[offset])
                offset += 1
        except ValueError:
            raise SchFileError('Not a number in `Text`', line, f)
        text.text = f.get_line()
        return text

    def write(self, f):
        f.write('Text {} {} {} {} {}'.format(self.type, self.x, self.y, self.orient, self.size))
        if self.type[0] in 'GH':
            f.write(' '+self.shape)
        f.write(' {} {}\n'.format(['~', 'Italic'][self.italic], self.thickness))
        f.write(self.text+'\n')


class SchematicWire(object):
    WIRE = 0
    WIRE_BUS = 1
    WIRE_DOT = 2
    WIRES = {'Wire': WIRE, 'Bus': WIRE_BUS, 'Notes': WIRE_DOT}
    ENTRY_WIRE = 3
    ENTRY_BUS = 4
    ENTRIES = {'Wire': ENTRY_WIRE, 'Bus': ENTRY_BUS}
    NAMES = ['Wire Wire Line', 'Wire Bus Line', 'Wire Notes Line', 'Entry Wire Line', 'Entry Bus Bus']

    def __init__(self, width=None, style=None, rgb=None):
        super().__init__()
        self.width = width
        self.rgb = rgb
        self.style = style

    @staticmethod
    def load(f, line):
        res = _split_space(line)
        res_l = len(res)
        width = style = rgb = None
        if res_l > 3 and res[0] == 'Wire' and res[1] == 'Notes' and res[2] == 'Line':
            offset = 3
            while offset < res_l:
                if res[offset] == 'width' and res_l > offset+1:
                    width = res[offset+1]
                    offset += 2
                elif res[offset] == 'style' and res_l > offset+1:
                    style = res[offset+1]
                    offset += 2
                elif res[offset].startswith('rgb(') and res_l > offset+2:
                    rgb = res[offset]+' '+res[offset+1]+' '+res[offset+2]
                    offset += 3
                else:
                    raise SchFileError('Malformed wire note', line, f)
        elif res_l != 3:
            raise SchFileError('Malformed wire', line, f)
        wire = SchematicWire(width, style, rgb)
        if res[0] == 'Wire':
            # Wire Wire Line
            # Wire Bus Line
            # Wire Notes Line
            if res[2] != 'Line' or res[1] not in SchematicWire.WIRES:
                raise SchFileError('Malformed wire', line, f)
            wire.type = SchematicWire.WIRES[res[1]]
        else:  # Entry
            # Entry Wire Line
            # Entry Bus Bus
            if (res[2] != 'Bus' and res[2] != 'Line') or res[1] not in SchematicWire.ENTRIES:
                raise SchFileError('Malformed entry', line, f)
            wire.type = SchematicWire.ENTRIES[res[1]]
        line = f.get_line()
        if line[0] != '\t':
            raise SchFileError('Malformed wire', line, f)
        res = _split_space(line[1:])
        if len(res) != 4:
            raise SchFileError('Malformed wire', line, f)
        wire.x = int(res[0])
        wire.y = int(res[1])
        wire.ex = int(res[2])
        wire.ey = int(res[3])
        return wire

    def write(self, f):
        extra = ''
        if self.width is not None:
            extra += ' width '+self.width
        if self.style is not None:
            extra += ' style '+self.style
        if self.rgb is not None:
            extra += ' '+self.rgb
        f.write(SchematicWire.NAMES[self.type]+extra)
        f.write('\n\t{} {} {} {}\n'.format(self.x, self.y, self.ex, self.ey))


class SchematicBitmap(object):
    def __init__(self):
        super().__init__()

    @staticmethod
    def load(f):
        # Position
        line = f.get_line()
        res = _split_space(line)
        if res and res[0] != 'Pos':
            raise SchFileError('Missing bitmap position', line, f)
        if len(res) != 3:
            raise SchFileError('Malformed bitmap position', line, f)
        bmp = SchematicBitmap()
        bmp.x = int(res[1])
        bmp.y = int(res[2])
        # Scale
        line = f.get_line()
        res = _split_space(line)
        if res and res[0] != 'Scale':
            raise SchFileError('Missing bitmap scale', line, f)
        if len(res) != 2:
            raise SchFileError('Malformed bitmap scale', line, f)
        bmp.scale = float(res[1].replace(',', '.'))
        # Data
        line = f.get_line()
        if line != 'Data':
            raise SchFileError('Missing bitmap data', line, f)
        line = f.get_line()
        bmp.data = b''
        while line != 'EndData':
            res = _split_space(line)
            try:
                bmp.data += bytes([int(b, 16) for b in res])
            except ValueError:
                raise SchFileError('Malformed bitmap data', line, f)
            line = f.get_line()
        # End of bitmap
        line = f.get_line()
        if line != '$EndBitmap':
            raise SchFileError('Missing end of bitmap', line, f)
        return bmp

    def write(self, f):
        f.write('$Bitmap\n')
        f.write('Pos {} {}\n'.format(self.x, self.y))
        f.write('Scale {0:.6f}\n'.format(self.scale))
        f.write('Data')
        for c, b in enumerate(self.data):
            if (c % 32) == 0:
                f.write('\n')
            f.write('%02X ' % b)
        f.write('\nEndData\n')
        f.write('$EndBitmap\n')


class SchematicPort(object):
    port_re = re.compile(r'(\d+)\s+"(.*?)"\s+([IOBTU])\s+([RLTB])\s+(-?\d+)\s+(-?\d+)\s+(\d+)$')

    def __init__(self):
        super().__init__()

    @staticmethod
    def parse(line, f):
        m = SchematicPort.port_re.match(line)
        if not m:
            raise SchFileError('Malformed sheet port label', line, f)
        port = SchematicPort()
        res = m.groups()
        port.number = int(res[0])
        port.name = res[1]
        port.form = res[2]
        port.side = res[3]
        port.x = int(res[4])
        port.y = int(res[5])
        port.size = int(res[6])
        return port

    def write(s, f):
        f.write('F{} "{}" {} {} {} {} {}\n'.format(s.number, s.name, s.form, s.side, s.x, s.y, s.size))


class SchematicSheet(object):
    name_re = re.compile(r'"(.*?)"\s+(\d+)$')

    def __init__(self):
        super().__init__()
        self.sheet = None
        self.id = ''
        self.annotation_error = False

    def load_sheet(self, project, parent, sheet_path, sheet_path_h, libs, fields, fields_lc, parent_obj):
        assert self.name
        self.sheet = Schematic()
        parent_obj.all_sheets.append(self.sheet)
        parent_dir = os.path.dirname(parent)
        sheet_path += '/'+self.id
        if len(sheet_path_h) > 1:
            sheet_path_h += '/'
        sheet_path_h += self.name if self.name else 'Unknown'
        self.sheet.load(os.path.join(parent_dir, self.file), project, sheet_path, sheet_path_h, libs, fields, fields_lc,
                        parent_obj)
        return self.sheet

    @staticmethod
    def load(f, parent):
        # Position & Size
        line = f.get_line()
        if line[0] != 'S':
            raise SchFileError('Missing sheet size and position', line, f)
        res = _split_space(line[2:])
        if len(res) != 4:
            raise SchFileError('Malformed sheet size and position', line, f)
        sch = SchematicSheet()
        sch.x = int(res[0])
        sch.y = int(res[1])
        sch.w = int(res[2])
        sch.h = int(res[3])
        # Optional U
        line = f.get_line()
        if line[0] == 'U':
            sch.id = line[2:]
            line = f.get_line()
        # Labels
        sch.labels = []
        sch.name = None
        sch.file = None
        while not line.startswith('$EndSheet'):
            if line[0] != 'F':
                raise SchFileError('Malformed sheet label', line, f)
            if line[1] == '0':
                m = SchematicSheet.name_re.match(line[2:].lstrip())
                if not m:
                    raise SchFileError('Malformed sheet name', line, f)
                sch.name = m.group(1)
                sch.name_size = int(m.group(2))
            elif line[1] == '1' and line[2] == ' ':
                m = SchematicSheet.name_re.match(line[2:].lstrip())
                if not m:
                    raise SchFileError('Malformed sheet file name', line, f)
                sch.file = m.group(1)
                sch.file_size = int(m.group(2))
                if not os.path.isfile(os.path.join(os.path.dirname(parent), sch.file)):
                    raise SchFileError('Missing sub-sheet `{}`'.format(sch.file), line, f)
            else:
                sch.labels.append(SchematicPort.parse(line[1:], f))
            line = f.get_line()
        if not sch.name:
            raise SchFileError('Missing sub-sheet name', 'pos: {},{}'.format(sch.x, sch.y), f)
        if not sch.file:
            raise SchFileError('Missing sub-sheet file name', sch.name, f)
        return sch

    def write(self, f):
        # Fake file name
        file = self.file.replace('/', '_')
        f.write('$Sheet\n')
        f.write('S {} {} {} {}\n'.format(self.x, self.y, self.w, self.h))
        f.write('U {}\n'.format(self.id))
        f.write('F0 "{}" {}\n'.format(self.name, self.name_size))
        f.write('F1 "{}" {}\n'.format(file, self.file_size))
        for label in self.labels:
            label.write(f)
        f.write('$EndSheet\n')


def _path(p):
    if not p.startswith('/'):
        p = '/'+p
    if p[-1] != '/':
        p = p+'/'
    return p


class Schematic(object):
    def __init__(self):
        super().__init__()
        self.dcms = {}
        self.lib_comps = {}
        self.annotation_error = False
        self.max_comments = 4
        self.netlist_version = 'D'

    def _get_title_block(self, f):
        line = f.get_line()
        m = re.match(r'\$Descr (\S+) (\d+) (\d+)( portrait)?', line)
        if not m:
            raise SchFileError('Missing $Descr', line, f)
        self.page_type = m.group(1)
        self.page_width = m.group(2)
        self.page_height = m.group(3)
        self.paper_orientation = None
        if m.group(4):
            self.paper_orientation = m.group(4).strip()
        self.sheet = 1
        self.nsheets = 1
        self.title_block = OrderedDict()
        self.comment = ['']*9
        while True:
            line = f.get_line()
            if line.startswith('$EndDescr'):
                self.title_ori = self.title = self.title_block.get('Title', '')
                self.date = self.title_block.get('Date', '')
                self.revision = self.title_block.get('Rev', '')
                self.company = self.title_block.get('Comp', '')
                for num in range(4):
                    self.comment[num] = self.title_block.get('Comment'+str(num+1), '')
                return
            elif line.startswith('encoding'):
                if line[9:14] != 'utf-8':
                    raise SchFileError('Unsupported encoding', line, f)
            elif line.startswith('Sheet'):
                res = _split_space(line[6:])
                if len(res) != 2:
                    raise SchFileError('Wrong sheet number', line, f)
                self.sheet = int(res[0])
                self.nsheets = int(res[1])
            else:
                m = re.match(r'(\S+)\s+"(.*)"', line)
                if not m:
                    raise SchFileError('Wrong entry in title block', line, f)
                self.title_block[m.group(1)] = m.group(2)

    def load(self, fname, project, sheet_path='', sheet_path_h='/', libs=None, fields=None, fields_lc=None, parent=None):
        """ Load a v5.x KiCad Schematic.
            The caller must be sure the file exists.
            Only the schematics are loaded not the libs. """
        logger.debug("Loading sheet from "+fname)
        self.fname = fname
        if libs is None:
            libs = {}
        self.libs = libs
        if fields is None:
            fields = []
        self.fields = fields
        if fields_lc is None:
            fields_lc = set()
        self.fields_lc = fields_lc
        self.project = project
        self.sheet_path = sheet_path
        self.sheet_path_h = sheet_path_h
        with open(fname, 'rt') as fh:
            f = SCHLineReader(fh, fname)
            line = f.get_line()
            m = re.match(r'EESchema Schematic File Version (\d+)', line)
            if not m:
                raise SchFileError('No eeschema signature', line, f)
            self.version = int(m.group(1))
            line = f.get_line()
            if line.startswith('LIBS'):
                # LIBS is optional and can be skipped
                line = f.get_line()
            m = re.match(r'EELAYER (\d+) (\d+)', line)
            if not m:
                raise SchFileError('Missing EELAYER', line, f)
            self.eelayer_n = int(m.group(1))
            self.eelayer_m = int(m.group(2))
            line = f.get_line()
            if not line.startswith('EELAYER END'):
                raise SchFileError('Missing EELAYER END', line, f)
            # Load the title block
            self._get_title_block(f)
            # Fill in some missing info
            self.date = GS.format_date(self.date, fname, 'SCH')
            if not self.title:
                self.title = os.path.splitext(os.path.basename(fname))[0]
            logger.debug("SCH title: `{}`".format(self.title))
            logger.debug("SCH date: `{}`".format(self.date))
            logger.debug("SCH revision: `{}`".format(self.revision))
            logger.debug("SCH company: `{}`".format(self.company))
            line = f.get_line()
            self.all = []
            self.components = []
            self.conn = []
            self.texts = []
            self.wires = []
            self.bitmaps = []
            self.sheets = []
            while not line.startswith('$EndSCHEMATC'):
                if line.startswith('$Comp'):
                    obj = SchematicComponent.load(f, project, sheet_path, sheet_path_h, libs, fields, fields_lc)
                    if obj.annotation_error:
                        self.annotation_error = True
                    self.components.append(obj)
                elif line.startswith('NoConn'):
                    obj = SchematicConnection.parse(False, line[7:], f)
                    self.conn.append(obj)
                elif line.startswith('Connection'):
                    obj = SchematicConnection.parse(True, line[11:], f)
                    self.conn.append(obj)
                elif line.startswith('Text'):
                    obj = SchematicText.load(f, line)
                    self.texts.append(obj)
                elif line.startswith('Wire') or line.startswith('Entry'):
                    obj = SchematicWire.load(f, line)
                    self.wires.append(obj)
                elif line.startswith('$Bitmap'):
                    obj = SchematicBitmap.load(f)
                    self.bitmaps.append(obj)
                elif line.startswith('$Sheet'):
                    obj = SchematicSheet.load(f, fname)
                    self.sheets.append(obj)
                else:
                    raise SchFileError('Unknown definition', line, f)
                self.all.append(obj)
                line = f.get_line()
            # Load sub-sheets
            self.sub_sheets = []
            if parent is None:
                self.all_sheets = [self]
            for sch in self.sheets:
                sheet = sch.load_sheet(project, fname, sheet_path, sheet_path_h, libs, fields, fields_lc,
                                       self if parent is None else parent)
                if sheet.annotation_error:
                    self.annotation_error = True
                self.sub_sheets.append(sheet)

    def get_files(self):
        """ A list of the names for all the sheets, including this one.
            We avoid repeating the same file. """
        files = {self.fname}
        for sch in self.sheets:
            files.update(sch.sheet.get_files())
        return sorted(files)

    def check_repeated_ref(self, base_c, c):
        """ Check the base and the new component are coherent.
            Note that KiCad enforces it, fields for sub-units are the same.
            This is an integrity check """
        if base_c.value != c.value:
            logger.warning(f"{W_VALMISMATCH}Two components with `{c.ref}` but different value")
        if base_c.footprint != c.footprint:
            logger.warning(f"{W_VALMISMATCH}Two components with `{c.ref}` but different footprint")

    def get_components(self, exclude_power=True, collapse=True):
        """ A list of all the components. """
        if exclude_power:
            components = [c for c in self.components if not c.is_power]
        else:
            components = list(self.components)
        for sch in self.sheets:
            components.extend(sch.sheet.get_components(exclude_power, collapse))
        if collapse:
            # Here we handle: repeated references and sub-units
            # For sub-units we keep one of them
            # For repeated references we increase the "qty"
            if GS.debug_level > 3:
                logger.debug('Before collapse:')
                for c in components:
                    fields = {f.name: f.value for f in c.fields}
                    logger.debug(f'{c}: {c.qty} {fields}')

            new_comps = []
            found_comps = {}
            found_comps_u = {}
            for c in components:
                unit = c.unit or 0
                if c.ref not in found_comps:
                    # First time we see it
                    found_comps_u[c.ref] = {unit: 1}
                    found_comps[c.ref] = c
                    new_comps.append(c)
                    continue
                # We already got this reference, increment the counter for this unit
                known_units = found_comps_u[c.ref]
                known_units[unit] = known_units.get(unit, 0)+1
                self.check_repeated_ref(found_comps[c.ref], c)
            # Adjust the qty member and keep the smaller unit number
            components = []
            for c in new_comps:
                # Reset the PCB info, note that deepcopy of it is really slow
                c.has_pcb_info = False
                c.pad_properties = {}
                units = found_comps_u[c.ref]
                qty = max(units.values())
                if len(units) == 1 and qty == 1:
                    # No need to adjust details
                    components.append(c)
                    continue
                # Adjust details using a copy
                c = deepcopy(c)
                c.qty = qty
                # logger.debug(c.qty)
                if c.qty > 1:
                    logger.warning(W_MULTIREF+f'multiple `{c.ref}` components, not all operations will work')
                c.unit = min(units.keys())
                components.append(c)

            if GS.debug_level > 3:
                logger.debug('After collapse:')
                for c in components:
                    fields = {f.name: f.value for f in c.fields}
                    logger.debug(f'{c}: {c.qty} {fields}')
        components.sort(key=lambda g: g.ref)
        return components

    def get_field_names(self, fields):
        """ Appends the collected field names to the provided names """
        fields_lc = {v.lower() for v in fields}
        for f in self.fields:
            name_lc = f.lower()
            if name_lc not in fields_lc:
                fields.append(f)
                fields_lc.add(name_lc)
        return fields

    def walk_components(self, function, obj):
        for c in self.components:
            function(obj, c)
        for sch in self.sheets:
            sch.sheet.walk_components(function, obj)

    @staticmethod
    def apply_dcm(obj, c):
        dcm = None
        # Look for the DCM specific for the lib
        if c.lib:
            dcm = obj.dcms.get(c.lib)
            if dcm:
                entry = dcm.comps.get(c.name)
                if entry and entry.desc:
                    c.desc = entry.desc
                    if GS.debug_level > 2:
                        logger.debug('Filling desc for {}:{} `{}`'.format(c.lib, c.name, c.desc))

    def load_libs(self, fname):
        aliases = KiConf.get_sym_lib_aliases(fname)
        # Try to find the library paths
        for k in self.libs.keys():
            alias = aliases.get(k)
            if k and alias:
                self.libs[k] = alias.uri
                if GS.debug_level > 1:
                    logger.debug('Using `{}` for library alias `{}`'.format(alias.uri, k))
            else:
                logger.warning(W_MISSLIB + 'Missing library `{}`'.format(k))
        # Create a hash with all the used components
        self.comps_data = {'{}:{}'.format(c.lib, c.name): None for c in self.get_components(exclude_power=False)}
        if GS.debug_level > 1:
            logger.debug("Components before loading: "+str(self.comps_data))
        # Load the libraries and descriptions
        for k, v in self.libs.items():
            if v:
                # Load library
                if os.path.isfile(v):
                    o = SymLib()
                    o.load(v, k, self.comps_data)
                else:
                    logger.warning(W_MISSLIB + 'Missing library `{}` ({})'.format(v, k))
                    o = None
                self.lib_comps[k] = o
                # Load doc-lib
                file = os.path.splitext(v)[0]+'.dcm'
                if os.path.isfile(file):
                    o = DocLib()
                    o.load(file)
                else:
                    o = None
                self.dcms[k] = o
            else:
                # Mark as None if we don't know the file
                self.lib_comps[k] = None
                self.dcms[k] = None
        # Do we have all the components?
        if next((k for k, v in self.comps_data.items() if v is None), None) is not None:
            cache_name = fname.replace('.sch', '-cache.lib')
            if os.path.isfile(cache_name):
                logger.debug("Loading missing components from cache "+cache_name)
                o = SymLib()
                o.load(cache_name, None, self.comps_data)
        if GS.debug_level > 1:
            logger.debug("Components after loading: "+str(self.comps_data))
        # Join the descriptions with the components
        for k in self.libs.keys():
            lib = self.lib_comps[k]
            dcm = self.dcms[k]
            if lib and dcm:
                for name, comp in lib.comps.items():
                    comp.dcm = dcm.comps.get(name)
                    if not comp.dcm and k+':'+name in self.comps_data:
                        logger.warning(W_MISSDCM + 'Missing doc-lib entry for {}:{}'.format(k, name))
                # Also do it for the aliases
                for name, comp in lib.alias.items():
                    comp.dcm = dcm.comps.get(name)
                    if not comp.dcm and k+':'+name in self.comps_data:
                        logger.warning(W_MISSDCM + 'Missing doc-lib entry for {}:{}'.format(k, name))
        # Transfer the descriptions to the instances of the components
        self.walk_components(self.apply_dcm, self)

    def gen_lib(self, name, cross=False):
        """ Dumps all the used components to one library.
            This is like the KiCad cache. """
        with open(name, 'wt') as f:
            f.write('EESchema-LIBRARY Version 2.4\n')
            f.write('#encoding utf-8\n')
            for k, v in self.comps_data.items():
                if v:
                    v.write(f, k, cross=cross)
                else:
                    logger.warning(W_MISSCMP + 'Missing component `{}`'.format(k))
            f.write('#\n#End Library\n')

    def save(self, fname=None, dest_dir=None, base_sheet=None, saved=None):
        """ Save the schematic and its sub-sheets.
            If dest_dir is not None all files are stored in dest_dir (for variants). """
        if base_sheet is None:
            # We are the base sheet
            base_sheet = self
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
        if fname not in saved:
            logger.debug('Saving schematic: `{}`'.format(fname))
            # Keep a back-up of existing files
            if os.path.isfile(fname):
                bkp = fname+'-bak'
                os.replace(fname, bkp)
            with open(fname, 'wt') as f:
                f.write('EESchema Schematic File Version {}\n'.format(self.version))
                f.write('EELAYER {} {}\n'.format(self.eelayer_n, self.eelayer_m))
                f.write('EELAYER END\n')
                f.write('$Descr {} {} {}'.format(self.page_type, self.page_width, self.page_height))
                if self.paper_orientation:
                    f.write(' {}'.format(self.paper_orientation))
                f.write('\n')
                f.write('encoding utf-8\n')
                f.write('Sheet {} {}\n'.format(self.sheet, self.nsheets))
                for k, v in self.title_block.items():
                    f.write('{} "{}"\n'.format(k, v))
                f.write('$EndDescr\n')
                crossed = dest_dir is not None
                for e in self.all:
                    if isinstance(e, SchematicComponent):
                        e.write(f, crossed)
                    else:
                        e.write(f)
                f.write('$EndSCHEMATC\n')
            saved.add(fname)
        # Save sub-sheets
        for c, sch in enumerate(self.sheets):
            file = sch.file
            if dest_dir is not None:
                # Fake file name, forcing a flat structure (all files in dest_dir)
                file = file.replace('/', '_')
            self.sub_sheets[c].save(file, dest_dir, base_sheet, saved)

    def save_variant(self, dest_dir):
        """ Save a modified schematic with crossed components """
        # Currently impossible
        # if not os.path.exists(dest_dir):
        #    os.makedirs(dest_dir)
        lib_yes = os.path.join(dest_dir, 'y.lib')
        lib_no = os.path.join(dest_dir, 'n.lib')
        self.gen_lib(lib_yes)
        self.gen_lib(lib_no, cross=True)
        fname = os.path.basename(self.fname)
        self.save(fname, dest_dir)
        # SymLibTable to use y/n
        with open(os.path.join(dest_dir, 'sym-lib-table'), 'wt') as f:
            f.write('(sym_lib_table\n')
            f.write(' (lib (name y)(type Legacy)(uri ${KIPRJMOD}/y.lib)(options "")(descr ""))\n')
            f.write(' (lib (name n)(type Legacy)(uri ${KIPRJMOD}/n.lib)(options "")(descr ""))\n')
            f.write(')\n')
        return fname

    def get_title(self):
        return self.title_block.get('Title', '')

    def set_title(self, title):
        """ Used only to save a variant """
        old_title = self.title_block.get('Title')
        if title is None:
            del self.title_block['Title']
        else:
            self.title_block['Title'] = title
        return old_title

    def file_names_variant(self, dest_dir):
        """ Returns a list of file names created by save_variant() """
        fnames = [os.path.join(dest_dir, 'y.lib'),
                  os.path.join(dest_dir, 'n.lib'),
                  os.path.join(dest_dir, 'sym-lib-table')]
        # Sub-sheets
        sub_sheets = self.get_files()
        for sch in sub_sheets:
            sch = os.path.basename(sch)
            fnames.append(os.path.join(dest_dir, sch.replace('/', '_')))
        return fnames

    def save_netlist_design(self, root):
        """ Generates the `design` section of the netlist """
        design = SubElement(root, 'design')
        SubElement(design, 'source').text = self.fname
        SubElement(design, 'date').text = datetime.now().strftime("%c")
        SubElement(design, 'tool').text = 'KiBot v'+GS.kibot_version
        order = 1
        is_v5 = self.max_comments == 4
        for s in self.all_sheets:
            sheet = SubElement(design, 'sheet')
            # KiCad v5 numbering is broken
            sheet.set('number', str(order) if is_v5 else s.sheet)
            sheet.set('name', _path(s.sheet_path_h))
            sheet.set('tstamps', _path(s.sheet_path))
            tblock = SubElement(sheet, 'title_block')
            title = SubElement(tblock, 'title')
            if s.title_ori:
                title.text = s.title_ori
            company = SubElement(tblock, 'company')
            if s.company:
                company.text = s.company
            rev = SubElement(tblock, 'rev')
            if s.revision:
                rev.text = s.revision
            dt = SubElement(tblock, 'date')
            if s.date:
                dt.text = s.date
            SubElement(tblock, 'source').text = os.path.basename(s.fname)
            for num in range(s.max_comments):
                com = SubElement(tblock, 'comment')
                com.set('number', str(num+1))
                com.set('value', s.comment[num])
            order += 1

    def save_netlist_components(self, root, comps, excluded, fitted, no_field):
        """ Generates the `components` section of the netlist """
        components = SubElement(root, 'components')
        # Collapse units
        real_comps = []
        tstamps = {}
        for c in comps:
            if c.ref in tstamps:
                tstamps[c.ref] += ' '+c.id
            else:
                tstamps[c.ref] = c.id
                real_comps.append(c)
        for c in real_comps:
            if not excluded and not c.included:
                # Excluded, i.e. virtual
                continue
            if fitted and not c.fitted:
                # DNP
                continue
            comp = SubElement(components, 'comp')
            comp.set('ref', c.ref)
            SubElement(comp, 'value').text = c.value
            if c.footprint:
                SubElement(comp, 'footprint').text = c.footprint
            if len(c.datasheet) and not (self.netlist_version == 'E' and c.datasheet == '~'):
                SubElement(comp, 'datasheet').text = c.datasheet
            user_fields = c.get_user_fields()
            if user_fields:
                fields = SubElement(comp, 'fields')
                for fname, fvalue in user_fields:
                    if fname.lower() in no_field:
                        continue
                    fld = SubElement(fields, 'field')
                    fld.set('name', fname)
                    fld.text = fvalue
            lbs = SubElement(comp, 'libsource')
            lbs.set('lib', c.lib)
            lbs.set('part', c.name)
            lbs.set('description', c.desc)
            # v6 properties
            if self.netlist_version == 'E':
                for fname, fvalue in user_fields:
                    if fname in no_field:
                        continue
                    fld = SubElement(comp, 'property')
                    fld.set('name', fname)
                    fld.set('value', fvalue)
                prop = SubElement(comp, 'property')
                prop.set('name', 'Sheetname')
                prop.set('value', os.path.basename(c.sheet_path_h))
                if hasattr(c, 'parent_sheet'):
                    # Components from the PCB doesn't have "parent_sheet"
                    prop = SubElement(comp, 'property')
                    prop.set('name', 'Sheetfile')
                    prop.set('value', os.path.basename(c.parent_sheet.fname))
            shp = SubElement(comp, 'sheetpath')
            shp.set('names', _path(c.sheet_path_h))
            shp.set('tstamps', _path(c.sheet_path))
            if self.netlist_version == 'D':
                SubElement(comp, 'tstamp').text = tstamps[c.ref].split()[0]
            else:
                SubElement(comp, 'tstamps').text = tstamps[c.ref]

    def save_netlist_libparts(self, root):
        libparts = SubElement(root, 'libparts')
        for k in sorted(self.comps_data.keys()):
            v = self.comps_data[k]
            if not v:
                continue
            ref = v.get_field_value('reference')
            if ref and ref[0] == '#':
                continue
            libpart = SubElement(libparts, 'libpart')
            res = k.split(':')
            cres = len(res)
            if cres == 1:
                libpart.set('lib', '')
                libpart.set('part', res[0])
            elif cres == 2:
                libpart.set('lib', res[0])
                libpart.set('part', res[1])
            if v.alias:
                aliases = SubElement(libpart, 'aliases')
                for alias in v.alias:
                    SubElement(aliases, 'alias').text = alias
            # Description
            desc = None
            if v.dcm and v.dcm.desc:
                desc = v.dcm.desc
            else:
                desc = v.get_field_value('ki_description')
            if desc:
                SubElement(libpart, 'description').text = desc
            # Datatsheet
            datasheet = None
            if v.dcm and v.dcm.datasheet:
                datasheet = v.dcm.datasheet
            else:
                datasheet = v.get_field_value('datasheet')
            if datasheet:
                SubElement(libpart, 'docs').text = datasheet
            # Footprint filters
            fp_list = None
            if v.fp_list:
                fp_list = v.fp_list
            else:
                fp_list = v.get_field_value('ki_fp_filters').split()
            if fp_list:
                fps = SubElement(libpart, 'footprints')
                for fp in fp_list:
                    SubElement(fps, 'fp').text = fp
            # Fields
            flds = SubElement(libpart, 'fields')
            for fld in v.fields:
                if not fld.value or fld.name.startswith('ki_'):
                    continue
                field = SubElement(flds, 'field')
                field.set('name', fld.name)
                field.text = fld.value
            # Pins
            if v.all_pins:
                pins = SubElement(libpart, 'pins')
                for pin in sorted(v.all_pins, key=lambda x: "%10s" % x.number):
                    pn = SubElement(pins, 'pin')
                    pn.set('num', pin.number)
                    name = pin.name
                    if self.netlist_version == 'E' and name == '~':
                        name = ''
                    pn.set('name', name)
                    tp = pin.type
                    if len(tp) == 1:
                        tp = pin.type2name.get(pin.type, 'unknown')
                    pn.set('type', tp)

    def save_netlist(self, fhandle, comps, excluded=False, fitted=True, no_field=()):
        """ This is a partial netlist in XML, only useful for BoMs """
        root = Element("export")
        root.set('version', self.netlist_version)
        # Design section
        self.save_netlist_design(root)
        # Components
        self.save_netlist_components(root, comps, excluded, fitted, no_field)
        # LibParts
        self.save_netlist_libparts(root)
        # Libraries
        libraries = SubElement(root, 'libraries')
        for k, v in self.libs.items():
            lib = SubElement(libraries, 'library')
            lib.set('logical', k)
            SubElement(lib, 'uri').text = v
        # Nets
        # TODO: May be in the future
        SubElement(root, 'nets')
        # Make it look nice
        rough_string = tostring(root, encoding='utf8')
        reparsed = minidom.parseString(rough_string.decode('utf8'))
        fhandle.write(reparsed.toprettyxml(indent="  ", encoding='UTF-8'))
