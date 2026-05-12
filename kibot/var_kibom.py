# -*- coding: utf-8 -*-
# Copyright (c) 2020-2024 Salvador E. Tropea
# Copyright (c) 2020-2024 Instituto Nacional de Tecnología Industrial
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)
# Description: Implements the KiBoM variants mechanism.
from .optionable import Optionable
from .gs import GS
from .misc import IFILT_MECHANICAL
from .fil_base import BaseFilter
from .macros import macros, document, variant_class  # noqa: F401
from . import log

logger = log.get_logger()


@variant_class
class KiBoM(BaseVariant):  # noqa: F821
    """ KiBoM variant style
        The Config field (configurable) contains a comma separated list of variant directives.
        -VARIANT excludes a component from VARIANT.
        +VARIANT includes the component only if we are using this variant
        Important: Don't confuse this variant style with the `kibom` output. In fact variants
        doesn't apply to `kibom` output because it just uses the internal mechanism of
        KiBom. Use the `bom` output instead, in this case you can use this variant style to
        get similar results to what you get from `kibom` """
    def __init__(self):
        super().__init__()
        with document:
            self.config_field = 'Config'
            """ Name of the field used to classify components """
            self.variant = Optionable
            """ [string|list(string)=[]] {comma_sep} Board variant(s) """
        self.fix_doc('exclude_filter', IFILT_MECHANICAL)
        self.fix_doc('dnf_filter', '_kibom_dnf_CONFIG_FIELD')
        self.fix_doc('dnc_filter', '_kibom_dnc_CONFIG_FIELD')

    def get_variant_field(self):
        """ Returns the name of the field used to determine if the component belongs to the variant """
        return self.config_field

    def clear_filters(self):
        """ Remove any filter """
        self.exclude_filter = self.dnf_filter = self.dnc_filter = self.pre_transform = None

    @staticmethod
    def fix_dnx_filter(name, config_field):
        if isinstance(name, list):
            name = name[0]
        if name.startswith('_kibom_dn') and name.endswith('_CONFIG_FIELD'):
            return name[:11]+config_field
        return name

    def config(self, parent):
        # Now we can let the parent initialize the filters
        super().config(parent)
        # Variants, ensure a lowercase list
        self.variant = [v.lower() for v in self.variant]
        self.pre_transform = BaseFilter.solve_filter(self.pre_transform, 'pre_transform', is_transform=True)
        self.exclude_filter = BaseFilter.solve_filter(self.exclude_filter, 'exclude_filter')
        self.dnf_filter = BaseFilter.solve_filter(self.fix_dnx_filter(self.dnf_filter, self.config_field), 'dnf_filter')
        self.dnc_filter = BaseFilter.solve_filter(self.fix_dnx_filter(self.dnc_filter, self.config_field), 'dnc_filter')
        # Config field must be lowercase
        self.config_field = self.config_field.lower()

    def matches_variant(self, config):
        """ Apply the variants to determine if this component will be fitted.
            config: content of the 'Config' field. """
        # Variants logic
        opts = config.lower().split(",")
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

    def filter(self, comps, call_back=None):
        GS.variant = self.variant
        comps = super().filter(comps)
        logger.debug("Applying KiBoM style variants `{}`".format(self.name))
        for c in comps:
            if not (c.fitted and c.included):
                # Don't check if we already discarded it
                continue
            config = c.get_field_value(self.config_field)
            c.set_fitted(self.matches_variant(config))
            if not c.fitted and GS.debug_level > 2:
                logger.debug('ref: {} config: {} variant: {} -> False'.
                             format(c.ref, config, self.variant))
        return comps
