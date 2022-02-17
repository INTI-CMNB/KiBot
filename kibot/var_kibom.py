# -*- coding: utf-8 -*-
# Copyright (c) 2020 Salvador E. Tropea
# Copyright (c) 2020 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
"""
Implements the KiBoM variants mechanism.
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
class KiBoM(BaseVariant):  # noqa: F821
    """ KiBoM variant style
        The Config field (configurable) contains a comma separated list of variant directives.
        -VARIANT excludes a component from VARIANT.
        +VARIANT includes the component only if we are using this variant. """
    def __init__(self):
        super().__init__()
        self._def_exclude_filter: str|None = None
        self._def_dnf_filter: str|None = None
        self._def_dnc_filter: str|None = None
        with document:
            self.config_field = 'Config'
            """ Name of the field used to classify components """
            self.variant = Optionable  ## type: list[string]
            """ [string|list(string)=''] Board variant(s) """

    def get_variant_field(self) -> str:
        ''' Returns the name of the field used to determine if the component belongs to the variant '''
        return self.config_field

    def set_def_filters(self, exclude_filter, dnf_filter, dnc_filter):
        """ Filters delegated to the variant """
        self._def_exclude_filter = exclude_filter
        self._def_dnf_filter = dnf_filter
        self._def_dnc_filter = dnc_filter

    def config(self, parent):
        # Now we can let the parent initialize the filters
        super().config(parent)
        # Variants, ensure a lowercase list
        self.variant = [v.lower() for v in self.force_list(self.variant)]
        self.pre_transform = BaseFilter.solve_filter(self.pre_transform, 'pre_transform', is_transform=True)
        # Filters priority:
        # 1) Defined here
        # 2) Delegated from the output format
        # 3) KiBoM default behavior
        # exclude_filter
        if not self._def_exclude_filter:
            self._def_exclude_filter = IFILT_MECHANICAL
        self.exclude_filter = BaseFilter.solve_filter(self.exclude_filter, 'exclude_filter', self._def_exclude_filter)
        # dnf_filter
        if not self._def_dnf_filter:
            self._def_dnf_filter = '_kibom_dnf_'+self.config_field
        self.dnf_filter = BaseFilter.solve_filter(self.dnf_filter, 'dnf_filter', self._def_dnf_filter)
        # dnc_filter
        if not self._def_dnc_filter:
            self._def_dnc_filter = '_kibom_dnc_'+self.config_field
        self.dnc_filter = BaseFilter.solve_filter(self.dnc_filter, 'dnc_filter', self._def_dnc_filter)
        # Config field must be lowercase
        self.config_field = self.config_field.lower()

    def _variant_comp_is_fitted(self, value, config):
        """ Apply the variants to determine if this component will be fitted.
            value: component value (lowercase).
            config: content of the 'Config' field (lowercase). """
        # Variants logic
        opts = config.split(",")
        # Exclude components that match a -VARIANT
        for opt in opts:
            opt = opt.strip()
            # Options that start with '-' are explicitly removed from certain configurations
            if opt.startswith("-") and opt[1:] in self.variant:
                return False
        # Include components that match +VARIANT
        exclusive = False
        for opt in opts:
            # Options that start with '+' are fitted only for certain configurations
            if opt.startswith("+"):
                exclusive = True
                if opt[1:] in self.variant:
                    return True
        # No match
        return not exclusive

    def filter(self, comps):
        GS.variant = self.variant
        comps = super().filter(comps)
        logger.debug("Applying KiBoM style variants `{}`".format(self.name))
        for c in comps:
            if not (c.fitted and c.included):
                # Don't check if we already discarded it
                continue
            value = c.value.lower()
            config = c.get_field_value(self.config_field).lower()
            c.fitted = self._variant_comp_is_fitted(value, config)
            if not c.fitted and GS.debug_level > 2:
                logger.debug('ref: {} value: {} config: {} variant: {} -> False'.
                             format(c.ref, value, config, self.variant))
        return comps
