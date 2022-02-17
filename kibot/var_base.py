# -*- coding: utf-8 -*-
# Copyright (c) 2020-2021 Salvador E. Tropea
# Copyright (c) 2020-2021 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
from .registrable import RegVariant
from .optionable import Optionable
from .fil_base import apply_exclude_filter, apply_fitted_filter, apply_fixed_filter, apply_pre_transform
from .macros import macros, document  # noqa: F401


class BaseVariant(RegVariant):
    def __init__(self):
        super().__init__()
        self._unknown_is_error = True
        with document:
            self.name = ''
            """ Used to identify this particular variant definition """
            self.type = ''
            """ Type of variant """
            self.comment = ''
            """ A comment for documentation purposes """
            self.file_id = ''
            """ Text to use as the replacement for %v expansion """
            # * Filters
            self.pre_transform = Optionable
            """ [string|list(string)=''] Name of the filter to transform fields before applying other filters.
                Use '_var_rename' to transform VARIANT:FIELD fields.
                Use '_var_rename_kicost' to transform kicost.VARIANT:FIELD fields.
                Use '_kicost_rename' to apply KiCost field rename rules """
            self.exclude_filter = Optionable
            """ [string|list(string)=''] Name of the filter to exclude components from BoM processing.
                Use '_mechanical' for the default KiBoM behavior """
            self.dnf_filter = Optionable
            """ [string|list(string)=''] Name of the filter to mark components as 'Do Not Fit'.
                Use '_kibom_dnf' for the default KiBoM behavior.
                Use '_kicost_dnp'' for the default KiCost behavior """
            self.dnc_filter = Optionable
            """ [string|list(string)=''] Name of the filter to mark components as 'Do Not Change'.
                Use '_kibom_dnc' for the default KiBoM behavior """

    def get_variant_field(self):
        ''' Returns the name of the field used to determine if the component belongs to the variant '''
        return None

    def filter(self, comps):
        # Apply all the filters
        comps = apply_pre_transform(comps, self.pre_transform)
        apply_exclude_filter(comps, self.exclude_filter)
        apply_fitted_filter(comps, self.dnf_filter)
        apply_fixed_filter(comps, self.dnc_filter)
        return comps
