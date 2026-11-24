# -*- coding: utf-8 -*-
# Copyright (c) 2020-2024 Salvador E. Tropea
# Copyright (c) 2020-2024 Instituto Nacional de Tecnología Industrial
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)
# Description: Implements a filter to rotate footprints.
#              This is inspired in JLCKicadTools by Matthew Lai.
#              See: https://github.com/matthewlai/JLCKicadTools/blob/master/jlc_kicad_tools/cpl_rotations_db.csv
#              I latter added more information from bennymeg/JLC-Plugin-for-KiCad
from math import sin, cos, radians
from re import compile
from .gs import GS
from .optionable import Optionable
from .error import KiPlotConfigurationError
from .macros import macros, document, filter_class  # noqa: F401
from .misc import W_BADANGLE, W_BADOFFSET, DEFAULT_ROTATIONS, DEFAULT_ROT_FIELDS, DEFAULT_OFFSETS, DEFAULT_OFFSET_FIELDS
from . import log
from typing import Optional

logger = log.get_logger()


def get_field_value(comp, field):
    """ Helper to process the footprint field in a special way """
    field = field.lower()
    if field == 'footprint':
        # The databases are created just for the name of the footprint
        return comp.footprint
    if field == 'full footprint':
        # The real 'footprint' field has it
        field = 'footprint'
    return comp.get_field_value(field)


class Regex(Optionable):
    """ Implements the pair column/regex """
    def __init__(self, regex=None, angle: Optional[float] = None, offset_x=None, offset_y=None):
        super().__init__()
        self._unknown_is_error = True
        with document:
            self.field = 'footprint'
            """ Name of field to apply the regular expression.
                Use `_field_lcsc_part` to get the value defined in the global options.
                Use `Footprint` for the name of the footprint without a library.
                Use `Full Footprint` for the name of the footprint including the library """
            self.regex = ''
            """ Regular expression to match """
            self.regexp = None
            """ {regex} """
            self.angle = 0.0
            """ Rotation offset to apply to the matched component """
            self.offset_x = 0.0
            """ X position offset to apply to the matched component """
            self.offset_y = 0.0
            """ Y position offset to apply to the matched component """
            self.apply_angle = True
            """ Apply the angle offset """
            self.apply_offset = True
            """ Apply the position offset """
        if regex is not None:
            self.regex = regex
        if angle is not None:
            self.angle = angle
        if offset_x is not None:
            self.offset_x = offset_x
        if offset_y is not None:
            self.offset_y = offset_y
        self._regex_example = '^TSSOP-'

    def __str__(self):
        res = f'{self.field} matches {self.regex} =>'
        if self.apply_angle:
            res += f' rotate {self.angle}'
        if self.apply_offset:
            res += f' move {self.offset_x},{self.offset_y}'
        return res

    def config(self, parent):
        super().config(parent)
        if not self.field:
            raise KiPlotConfigurationError(f"Missing or empty `field` name ({str(self._tree)})")
        if not self.regex:
            raise KiPlotConfigurationError(f"Missing or empty `regex` for `{self.field}` field")
        # We could be wanting to add a rule to avoid a default change
        # if self.angle == 0.0 and self.offset_x == 0.0 and self.offset_y == 0.0:
        #    raise KiPlotConfigurationError(f"Rule for `{self.field}` field without any adjust")
        self.field = self.solve_field_name(self.field).lower()


class RotFields(Optionable):
    _default = DEFAULT_ROT_FIELDS


class OffsetFields(Optionable):
    _default = DEFAULT_OFFSET_FIELDS


@filter_class
class Rot_Footprint(BaseFilter):  # noqa: F821
    """ Footprint Rotator
        This filter can rotate footprints, used for the positions file generation.
        Some manufacturers use a different rotation than KiCad.
        The `JLCPCB Rotation Offset` and `JLCPCB Position Offset` fields can be used to adjust special cases.
        The internal `_rot_footprint` filter implements the simplest case """
    def __init__(self):
        super().__init__()
        self._is_transform = True
        with document:
            self.extend = True
            """ Extends the internal list of rotations with the one provided.
                Otherwise just use the provided list.
                Note that the provided list has more precedence than the internal list """
            self.negative_bottom = True
            """ Rotation for bottom components is computed via subtraction as `(component rot - angle)` """
            self.invert_bottom = False
            """ Rotation for bottom components is negated, resulting in either: `(- component rot - angle)`
                or when combined with `negative_bottom`, `(angle - component rot)` """
            self.mirror_bottom = False
            """ The original component rotation for components in the bottom is mirrored before applying
                the adjust so you get `(180 - component rot + angle)`. This is used by JLCPCB """
            self.rotations = Optionable
            """ [list(list(string))=[]] A list of pairs regular expression/rotation.
                Footprints matching the regular expression will be rotated the indicated angle.
                The angle matches the matthewlai/JLCKicadTools plugin specs """
            self.offsets = Optionable
            """ [list(list(string))=[]] A list of pairs regular expression/offset.
                Footprints matching the regular expression will be moved the specified offset.
                The offset must be two numbers separated by a comma. The first is the X offset.
                The signs matches the matthewlai/JLCKicadTools plugin specs """
            self.rotations_and_offsets = Regex
            """ [list(dict)=[]] A list of rules to match components and specify the rotation and offsets.
                This is a more flexible version of the `rotations` and `offsets` options.
                Note that this list has more precedence """
            self.skip_bottom = False
            """ Do not rotate components on the bottom """
            self.skip_top = False
            """ Do not rotate components on the top """
            self.rot_fields = RotFields
            """ [string|list(string)] {comma_sep} List of fields that can contain a rotation offset.
                The optional fields can contain a counter-clockwise orientation offset in degrees.
                This concept is from the bennymeg/JLC-Plugin-for-KiCad tool """
            self.offset_fields = OffsetFields
            """ [string|list(string)] {comma_sep} List of fields that can contain a position offset.
                The optional fields can contain a comma separated x,y position offset.
                This concept is from the bennymeg/JLC-Plugin-for-KiCad tool """
            self.bennymeg_mode = True
            """ Implements the `rot_fields` and `offset_fields` in the same way that the bennymeg/JLC-Plugin-for-KiCad tool.
                Note that the computation for bottom rotations is wrong, forcing the user to uses arbitrary rotations.
                The correct computation is `(180 - component rot) + angle` but the plugin does `180 - (component rot + angle)`.
                This option forces the wrong computation for compatibility.
                This option also controls the way offset signs are interpreted. When enabled the offsets matches this plugin,
                when disabled matches the interpretation used by the matthewlai/JLCKicadTools plugin.
                Disabling this option you'll get better algorithms, but loose compatibility with this plugin """

    def config(self, parent):
        super().config(parent)
        self._rot = []
        self._offset = []
        # The main list first
        for v in self.rotations_and_offsets:
            v.regex = compile(v.regex)
            if v.apply_angle:
                self._rot.append(v)
            if v.apply_offset:
                self._offset.append(v)
        # List of rotations
        for r in self.rotations:
            if len(r) != 2:
                raise KiPlotConfigurationError("Each regex/angle pair must contain exactly two values, not {} ({})".
                                               format(len(r), r))
            try:
                angle = float(r[1])
            except ValueError:
                raise KiPlotConfigurationError("The second value in the regex/angle pairs must be a number, not {}".
                                               format(r[1]))
            self._rot.append(Regex(regex=compile(r[0]), angle=angle))
        # List of offsets
        for r in self.offsets:
            if len(r) != 2:
                raise KiPlotConfigurationError("Each regex/offset pair must contain exactly two values, not {} ({})".
                                               format(len(r), r))
            try:
                offset_x = float(r[1].split(",")[0])
                offset_y = float(r[1].split(",")[1])
            except ValueError:
                raise KiPlotConfigurationError("The second value in the regex/offset pairs must be two numbers "
                                               f"separated by a comma, not {r[1]}")
            self._offset.append(Regex(regex=compile(r[0]), offset_x=offset_x, offset_y=offset_y))
        if self.extend:
            for regex_str, angle in DEFAULT_ROTATIONS:
                self._rot.append(Regex(regex=compile(regex_str), angle=angle))
            for regex_str, offset in DEFAULT_OFFSETS:
                self._offset.append(Regex(regex=compile(regex_str), offset_x=offset[0], offset_y=offset[1]))
        if not self._rot and not self._offset:
            raise KiPlotConfigurationError("No rotations and/or offsets provided")
        if GS.debug_level > 2:
            logger.debug('Final rotations list:')
            for r in self._rot:
                logger.debug(r)
            logger.debug('Final offsets list:')
            for r in self._offset:
                logger.debug(r)

    def apply_rotation_angle(self, comp, angle: float, bennymeg_mode=False):
        old_footprint_rot = comp.footprint_rot
        if comp.bottom:
            # Apply adjusts for bottom components
            if bennymeg_mode and self.bennymeg_mode:
                # Compatible with https://github.com/bennymeg/JLC-Plugin-for-KiCad/
                # Currently wrong! The real value is (180-comp.footprint_rot)+angle and not
                #                                     180-(comp.footprint_rot+angle)
                comp.footprint_rot = (comp.footprint_rot + angle) % 360.0
                comp.offset_footprint_rot = old_footprint_rot
                comp.footprint_rot = (540.0 - comp.footprint_rot) % 360.0
            else:
                if self.mirror_bottom:
                    comp.footprint_rot = 180 - comp.footprint_rot
                if self.negative_bottom:
                    comp.footprint_rot -= angle
                else:
                    comp.footprint_rot += angle
                if self.invert_bottom:
                    comp.footprint_rot = -comp.footprint_rot
                comp.offset_footprint_rot = old_footprint_rot
        else:
            comp.footprint_rot += angle
            comp.offset_footprint_rot = old_footprint_rot
        comp.footprint_rot = comp.footprint_rot % 360
        if GS.debug_level > 2:
            logger.debug(f'- rotating {comp.ref} from {old_footprint_rot} to {comp.footprint_rot}')

    def apply_field_rotation(self, comp) -> bool:
        for f in self.rot_fields:
            value = get_field_value(comp, f)
            if value:
                try:
                    angle = float(value)
                except ValueError:
                    logger.warning(f'{W_BADANGLE}Wrong angle `{value}` in {f} field of {comp.ref}')
                    angle = 0
                logger.debugl(2, f'- rotation from field `{f}`: {angle}')
                self.apply_rotation_angle(comp, angle, bennymeg_mode=True)
                return True
        return False

    def apply_rotation(self, comp):
        if self.apply_field_rotation(comp):
            return
        # Try with the regex
        for v in self._rot:
            value = get_field_value(comp, v.field)
            if value and v.regex.search(value):
                logger.debugl(2, f'- matched {v.regex} on field {v.field} with {v.angle} degrees')
                self.apply_rotation_angle(comp, v.angle)
                return
        # No rotation, apply 0 to apply bottom adjusts
        self.apply_rotation_angle(comp, 0)

    def apply_offset_value(self, comp, angle: float, pos_offset_x, pos_offset_y):
        if comp.bottom and self.mirror_bottom:
            logger.debugl(2, '- applying mirror to the offset')
            pos_offset_x = -pos_offset_x
            angle = -angle
        if angle:
            rotation = radians(angle)
            rsin = sin(rotation)
            rcos = cos(rotation)
            comp.pos_offset_x = pos_offset_x * rcos - pos_offset_y * rsin
            comp.pos_offset_y = pos_offset_x * rsin + pos_offset_y * rcos
            logger.debugl(2, f'- rotating offset {angle} degrees: {comp.pos_offset_x}, {comp.pos_offset_y} mm')
        else:
            comp.pos_offset_x = pos_offset_x
            comp.pos_offset_y = pos_offset_y
        # The signs here matches matthewlai/JLCKicadTools offsets because the database comes from this plugin
        comp.pos_offset_x = -GS.from_mm(comp.pos_offset_x)
        comp.pos_offset_y = GS.from_mm(comp.pos_offset_y)
        logger.debugl(2, f'- final offset {comp.pos_offset_x}, {comp.pos_offset_y} KiCad IUs')

    def apply_field_offset(self, comp) -> bool:
        for f in self.offset_fields:
            value = get_field_value(comp, f)
            if value:
                try:
                    pos_offset_x = float(value.split(",")[0])
                    pos_offset_y = float(value.split(",")[1])
                except ValueError:
                    logger.warning(f'{W_BADOFFSET}Wrong offset `{value}` in {f} field of {comp.ref}')
                    return False
                logger.debugl(2, f'- offset from field `{f}`: {pos_offset_x}, {pos_offset_y} mm')
                if self.bennymeg_mode:
                    # Signs here matches bennymeg/JLC-Plugin-for-KiCad because the fields usage comes from it
                    pos_offset_x = -pos_offset_x
                    pos_offset_y = -pos_offset_y
                    angle = comp.offset_footprint_rot
                    logger.debugl(2, f'- changing to {pos_offset_x}, {pos_offset_y} mm to match signs, using angle {angle}')
                else:
                    angle = comp.footprint_rot
                self.apply_offset_value(comp, angle, pos_offset_x, pos_offset_y)
                return True
        return False

    def apply_offset(self, comp):
        if self.apply_field_offset(comp):
            return
        # Try with the regex
        for v in self._offset:
            value = get_field_value(comp, v.field)
            if value and v.regex.search(value):
                logger.debugl(2, f'- matched {v.regex} on field {v.field} with offset {v.offset_x}, {v.offset_y} mm')
                self.apply_offset_value(comp, comp.footprint_rot, v.offset_x, v.offset_y)
                return

    def filter(self, comp):
        """ Apply the rotation """
        if (self.skip_top and not comp.bottom) or (self.skip_bottom and comp.bottom):
            # Component should be excluded
            return
        logger.debugl(2, f'{comp.ref} ({comp.footprint}):')
        self.apply_rotation(comp)
        self.apply_offset(comp)
