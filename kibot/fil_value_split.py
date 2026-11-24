# -*- coding: utf-8 -*-
# Copyright (c) 2023 Salvador E. Tropea
# Copyright (c) 2023 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
# Description: Extracts information from the value field and creates/updates new fields
from .bom.bom import normalize_value
from .bom.units import comp_match, get_decima_point, get_prefix, ParsedValue
from .gs import GS
from .macros import macros, document, filter_class  # noqa: F401
from . import log
from typing import Sequence

logger = log.get_logger()


@filter_class
class Value_Split(BaseFilter):  # noqa: F821
    """ Value Splitter
        This filter extracts information from the value and fills other fields.
        I.e. extracts the tolerance and puts it in the `tolerance` field.
        Usage [example](https://inti-cmnb.github.io/kibot-examples-1/value_split/) """
    def __init__(self):
        super().__init__()
        self._is_transform = True
        with document:
            self.source = 'Value'
            """ Name of the field to use as source of information """
            self.tolerance = 'yes'
            """ [yes,no,soft] Policy for the tolerance.
                yes = overwrite existing value, no = don't touch, soft = copy if not defined """
            self.voltage = 'yes'
            """ [yes,no,soft] Policy for the voltage rating.
                yes = overwrite existing value, no = don't touch, soft = copy if not defined """
            self.package = 'yes'
            """ [yes,no,soft] Policy for the package.
                yes = overwrite existing value, no = don't touch, soft = copy if not defined """
            self.temp_coef = 'yes'
            """ [yes,no,soft] Policy for the temperature coefficient.
                yes = overwrite existing value, no = don't touch, soft = copy if not defined """
            self.power = 'yes'
            """ [yes,no,soft] Policy for the power rating.
                yes = overwrite existing value, no = don't touch, soft = copy if not defined """
            self.replace_source = True
            """ Replace the content of the source field using a normalized representation of the interpreted value """
            self.autoplace = True
            """ Try to figure out the position for the added fields """
            self.autoplace_mechanism = 'bottom'
            """ [bottom,top] Put the new field at the bottom/top of the last field """
            self.visible = False
            """ Make visible the modified fields """

    def do_split(self, c, res, val, attr, policy, field_names: Sequence[str], pattern: str = "{}", units=""):
        if policy != 'no' and field_names and len(field_names) > 0:
            field_name = field_names[0]
            if field_name:
                value = res.get_extra(attr)
                if value and (policy == 'yes' or not c.get_field_value(field_name)):
                    if isinstance(value, float):
                        if int(value) == value:
                            value = int(value)
                        if units:
                            # Change things like 0.125 to 125 m
                            v, pow = get_prefix(value, '')
                            parsed = ParsedValue(v, pow, units)
                            value = str(parsed)
                    value = pattern.format(value)
                    logger.debugl(2, "- {} -> {} = {}".format(val, field_name, value))
                    vis = self.visible if self.visible else None
                    added, f = c.set_field(field_name, value, visible=vis)
                    if added and self.autoplace:
                        self._last_y += self._inc_y
                        f.set_xy(self._last_x, self._last_y, hjustify='L')

    def find_field_position(self, c):
        inc_sign = 1 if self.autoplace_mechanism == 'bottom' else -1
        # Default is the center of the symbol
        self._last_x = c.x
        self._last_y = c.y
        self._inc_y = inc_sign*c.fields[0].get_height()*1.8
        fields = c.get_visible_fields()
        if not fields:
            # No fields, we can't figure out
            return
        # Take the first
        self._last_x, self._last_y = fields[0].get_xy()
        if len(fields) > 1:
            # Look for the bottom/top field
            for f in fields[1:]:
                x, y = f.get_xy()
                if (y > self._last_y and inc_sign > 0) or (y < self._last_y and inc_sign < 0):
                    self._last_x = x
                    self._last_y = y

    def filter(self, comp):
        """ Analyze the `source` field and copy the information to other fields """
        value = comp.get_field_value(self.source)
        if not value:
            return
        res = comp_match(value, comp.ref_prefix, comp.ref)
        if res is None:
            return
        comp.value_sort = res
        if self.autoplace:
            self.find_field_position(comp)
        self.do_split(comp, res, value, 'tolerance', self.tolerance, GS.global_field_tolerance, "{}%")
        self.do_split(comp, res, value, 'voltage_rating', self.voltage, GS.global_field_voltage, units="V")
        self.do_split(comp, res, value, 'size', self.package, GS.global_field_package)
        self.do_split(comp, res, value, 'characteristic', self.temp_coef, GS.global_field_temp_coef)
        self.do_split(comp, res, value, 'power_rating', self.power, GS.global_field_power, units="W")
        if self.replace_source:
            new_value = normalize_value(comp, get_decima_point())
            logger.debug("- {} = {} -> {}".format(self.source, value, new_value))
            comp.set_field(self.source, new_value)
