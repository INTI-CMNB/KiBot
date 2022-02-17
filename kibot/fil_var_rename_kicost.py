# -*- coding: utf-8 -*-
# Copyright (c) 2020-2021 Salvador E. Tropea
# Copyright (c) 2020-2021 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
# The algorithm is from KiCost project (https://github.com/xesscorp/KiCost)
"""
Implements the kicost.VARIANT:FIELD=VALUE renamer to get FIELD=VALUE when VARIANT is in use.
It applies the KiCost concept of variants (a regex to match the VARIANT)
Can be configured, by default is what KiCost does.
"""
from __future__ import annotations
import re
from .gs import GS
from .macros import macros, document, filter_class  # noqa: F401
from . import log
from .fil_base import BaseFilter

logger = log.get_logger()


@filter_class
class Var_Rename_KiCost(BaseFilter):  # noqa: F821
    """ Var_Rename_KiCost
        This filter implements the kicost.VARIANT:FIELD=VALUE renamer to get FIELD=VALUE when VARIANT is in use.
        It applies the KiCost concept of variants (a regex to match the VARIANT).
        The internal `_var_rename_kicost` filter emulates the KiCost behavior """
    def __init__(self):
        super().__init__()
        self._is_transform = True
        with document:
            self.prefix = 'kicost.'
            """ A mandatory prefix. Is not case sensitive """
            self.separator = ':'
            """ Separator used between the variant and the field name """
            self.variant = ''
            """ Variant regex to match the VARIANT part.
                When empty the currently selected variant is used """
            self.variant_to_value = False
            """ Rename fields matching the variant to the value of the component """

    def config(self, parent):
        super().config(parent)
        if not self.separator:
            self.separator = ':'
        self.prefix = self.prefix.lower()
        self._l_prefix = len(self.prefix)

    def filter(self, comp):
        """ Look for fields containing PREFIX VARIANT:FIELD used to change fields according to the variant """
        variant = self.variant
        if not variant:
            if not GS.variant:
                # No variant in use, nothing to do
                return
            if len(GS.variant) == 1:
                variant = GS.variant[0]
            else:
                variant = '('+'|'.join(GS.variant)+')'
        var_re = re.compile(variant, re.IGNORECASE)
        for name, value in comp.get_user_fields():
            name = name.strip().lower()
            # Remove the prefix
            if self._l_prefix:
                if name.startswith(self.prefix):
                    name = name[self._l_prefix:]
                else:
                    # Doesn't match the prefix
                    continue
            # Apply the separator
            res = name.split(self.separator)
            if len(res) == 2:
                # Successfully separated
                f_variant = res[0].lower()
                f_field = res[1].lower()
                if var_re.match(f_variant):
                    # Variant matched
                    if GS.debug_level > 2:
                        logger.debug('ref: {} {}: {} -> {}'.
                                     format(comp.ref, f_field, comp.get_field_value(f_field), value))
                    comp.set_field(f_field, value)
            elif self.variant_to_value and var_re.match(name):
                # The field matches the variant and the user wants to change the value
                if GS.debug_level > 2:
                    logger.debug('ref: {} value: {} -> {}'.format(comp.ref, comp.value, value))
                comp.set_field('value', value)
