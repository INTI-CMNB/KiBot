# -*- coding: utf-8 -*-
# Copyright (c) 2020-2021 Salvador E. Tropea
# Copyright (c) 2020-2021 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
"""
Implements the VARIANT:FIELD=VALUE renamer to get FIELD=VALUE when VARIANT is in use.
"""
from __future__ import annotations
from .gs import GS
from .macros import macros, document, filter_class  # noqa: F401
from . import log
from .fil_base import BaseFilter

logger = log.get_logger()


@filter_class
class Var_Rename(BaseFilter):  # noqa: F821
    """ Var_Rename
        This filter implements the VARIANT:FIELD=VALUE renamer to get FIELD=VALUE when VARIANT is in use """
    def __init__(self):
        super().__init__()
        self._is_transform = True
        with document:
            self.separator = ':'
            """ Separator used between the variant and the field name """
            self.variant_to_value = False
            """ Rename fields matching the variant to the value of the component """
            self.force_variant = ''
            """ Use this variant instead of the current variant. Useful for IBoM variants """

    def config(self, parent):
        super().config(parent)
        if not self.separator:
            self.separator = ':'

    def filter(self, comp):
        """ Look for fields containing VARIANT:FIELD used to change fields according to the variant """
        if self.force_variant:
            variants = [self.force_variant]
        else:
            variants = GS.variant
            if not variants:
                # No variant in use, nothing to do
                return
        for variant in variants:
            for name, value in comp.get_user_fields():
                res = name.strip().split(self.separator)
                if len(res) == 2:
                    f_variant = res[0].lower()
                    f_field = res[1].lower()
                    if f_variant == variant:
                        if GS.debug_level > 2:
                            logger.debug('ref: {} {}: {} -> {}'.
                                         format(comp.ref, f_field, comp.get_field_value(f_field), value))
                        comp.set_field(f_field, value)
                elif self.variant_to_value and name.lower() == variant:
                    if GS.debug_level > 2:
                        logger.debug('ref: {} value: {} -> {}'.format(comp.ref, comp.value, value))
                    comp.set_field('value', value)
