# -*- coding: utf-8 -*-
# Copyright (c) 2020 Salvador E. Tropea
# Copyright (c) 2020 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
"""
Implements the IBoM variants mechanism.
"""
from __future__ import annotations
from .optionable import Optionable
from .gs import GS
from .misc import IFILT_MECHANICAL
from .fil_base import BaseFilter
from .var_base import BaseVariant
from .macros import macros, document, variant_class  # noqa: F401
from . import log

logger = log.get_logger()


@variant_class
class IBoM(BaseVariant):  # noqa: F821
    """ IBoM variant style
        The Config field (configurable) contains a value.
        If this value matches with a value in the whitelist is included.
        If this value matches with a value in the blacklist is excluded. """
    def __init__(self):
        super().__init__()
        with document:
            self.variant_field = 'Config'
            """ Name of the field that stores board variant for component """
            self.variants_blacklist = Optionable
            """ [string|list(string)=''] List of board variants to exclude from the BOM """
            self.variants_whitelist = Optionable
            """ [string|list(string)=''] List of board variants to include in the BOM """

    def get_variant_field(self):
        ''' Returns the name of the field used to determine if the component belongs to the variant '''
        return self.variant_field

    def config(self, parent):
        super().config(parent)
        self.pre_transform = BaseFilter.solve_filter(self.pre_transform, 'pre_transform', is_transform=True)
        self.exclude_filter = BaseFilter.solve_filter(self.exclude_filter, 'exclude_filter', IFILT_MECHANICAL)
        self.dnf_filter = BaseFilter.solve_filter(self.dnf_filter, 'dnf_filter')
        self.dnc_filter = BaseFilter.solve_filter(self.dnc_filter, 'dnc_filter')
        self.variants_blacklist = self.force_list(self.variants_blacklist)
        self.variants_whitelist = self.force_list(self.variants_whitelist)

    def skip_component(self, c):
        """ Skip components that doesn't belong to this variant. """
        # Apply variants white/black lists
        if self.variant_field:
            ref_variant = c.get_field_value(self.variant_field).lower()
            # skip components with wrong variant field
            if self.variants_whitelist and ref_variant not in self.variants_whitelist:
                return True
            if self.variants_blacklist and ref_variant and ref_variant in self.variants_blacklist:
                return True
        return False

    def filter(self, comps):
        GS.variant = self.variants_whitelist
        comps = super().filter(comps)
        logger.debug("Applying IBoM style variants `{}`".format(self.name))
        # Make black/white lists case insensitive
        self.variants_whitelist = [v.lower() for v in self.variants_whitelist]
        self.variants_blacklist = [v.lower() for v in self.variants_blacklist]
        # Apply to all the components
        for c in comps:
            logger.debug("{} {} {}".format(c.ref, c.fitted, c.included))
            if not (c.fitted and c.included):
                # Don't check if we already discarded it
                continue
            c.fitted = not self.skip_component(c)
            if not c.fitted and GS.debug_level > 2:
                logger.debug('ref: {} value: {} -> False'.format(c.ref, c.value))
        return comps
