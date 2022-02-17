# -*- coding: utf-8 -*-
# Copyright (c) 2020 Salvador E. Tropea
# Copyright (c) 2020 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
"""
Implements the KiBoM and IBoM filters.
"""
from __future__ import annotations
from re import compile, IGNORECASE
from .optionable import Optionable
from .bom.columnlist import ColumnList
from .gs import GS
from .misc import DNF, DNC
from .macros import macros, document, filter_class  # noqa: F401
from .out_base import BoMRegex
from .fil_base import BaseFilter
from . import log

logger = log.get_logger()


class DNFList(Optionable):
    _default = DNF

#     def __init__(self):
#         super().__init__()


@filter_class
class Generic(BaseFilter):  # noqa: F821
    """ Generic filter
        This filter is based on regular expressions.
        It also provides some shortcuts for common situations.
        Note that matches aren't case sensitive and spaces at the beginning and the end are removed.
        The internal `_mechanical` filter emulates the KiBoM behavior for default exclusions.
        The internal `_kicost_dnp` filter emulates KiCost's `dnp` field """
    def __init__(self):
        super().__init__()
        with document:
            self.invert = False
            """ Invert the result of the filter """
            self.include_only = BoMRegex
            """ [list(dict)] A series of regular expressions used to include parts.
                If there are any regex defined here, only components that match against ANY of them will be included.
                Column/field names are case-insensitive.
                If empty this rule is ignored """
            self.exclude_any = BoMRegex
            """ [list(dict)] A series of regular expressions used to exclude parts.
                If a component matches ANY of these, it will be excluded.
                Column names are case-insensitive  """
            self.keys: tuple[str|list[str],str|list[str]] = DNFList
            """ [string|list(string)=dnf_list] [dnc_list,dnf_list] List of keys to match.
                The `dnf_list` and `dnc_list` internal lists can be specified as strings """
            self.exclude_value = False
            """ Exclude components if their 'Value' is any of the keys """
            self.config_field = 'Config'
            """ Name of the field used to classify components """
            self.config_separators = ' ,'
            """ Characters used to separate options inside the config field """
            self.exclude_config = False
            """ Exclude components containing a key value in the config field.
                Separators are applied """
            self.exclude_field = False
            """ Exclude components if a field is named as any of the keys """
            self.exclude_empty_val = False
            """ Exclude components with empty 'Value' """
            self.exclude_refs: list[str]|None = Optionable
            """ [list(string)] List of references to be excluded.
                Use R* for all references with R prefix """
            self.exclude_all_hash_ref = False
            """ Exclude all components with a reference starting with # """
            self.exclude_virtual = False
            """ KiCad 5: exclude components marked as virtual in the PCB """
            self.exclude_smd = False
            """ KiCad 5: exclude components marked as smd in the PCB """
            self.exclude_tht = False
            """ KiCad 5: exclude components marked as through-hole in the PCB """
        self.add_to_doc('keys', 'Use `dnf_list` for '+str(sorted(DNF)))
        self.add_to_doc('keys', 'Use `dnc_list` for '+str(sorted(DNC)))

    @staticmethod
    def _fix_field(field):
        """ References -> Reference """
        col = field.lower()
        if col == ColumnList.COL_REFERENCE_L:
            col = col[:-1]
        return col

    def config(self, parent):
        super().config(parent)
        # include_only
        if isinstance(self.include_only, type):
            self.include_only = None
        else:
            for r in self.include_only:
                r.column = self._fix_field(r.column)
                r.regex = compile(r.regex, flags=IGNORECASE)
        # exclude_any
        if isinstance(self.exclude_any, type):
            self.exclude_any = None
        else:
            for r in self.exclude_any:
                r.column = self._fix_field(r.column)
                r.regex = compile(r.regex, flags=IGNORECASE)
        # keys
        if isinstance(self.keys, type):
            self.keys = DNF
        elif isinstance(self.keys, str):
            self.keys = DNF if self.keys == 'dnf_list' else DNC
        else:
            # Ensure lowercase
            self.keys = [v.lower() for v in self.keys]
        # Config field must be lowercase
        self.config_field = self.config_field.lower()
        # exclude_refs
        if isinstance(self.exclude_refs, type):
            self.exclude_refs = None

    def test_reg_include(self, c):
        """ Reject components that doesn't match the provided regex.
            So we include only the components that matches any of the regexs. """
        if not self.include_only:  # Nothing to match against, means include all
            return True
        for reg in self.include_only:
            if reg.skip_if_no_field and not c.is_field(reg.column):
                # Skip the check if the field doesn't exist
                continue
            if reg.match_if_field and c.is_field(reg.column):
                return True
            if reg.match_if_no_field and not c.is_field(reg.column):
                return True
            field_value = c.get_field_value(reg.column)
            res = reg.regex.search(field_value)
            if reg.invert:
                res = not res
            if res:
                if GS.debug_level > 1:
                    logger.debug("Including '{ref}': Field '{field}' ({value}) matched '{re}'".format(
                                 ref=c.ref, field=reg.column, value=field_value, re=reg.regex))
                # Found a match
                return True
        # Default, could not find a match
        return False

    def test_reg_exclude(self, c):
        """ Test if this part should be included, based on any regex expressions provided in the preferences """
        if not self.exclude_any:  # Nothing to match against, means don't exclude any
            return False
        for reg in self.exclude_any:
            if reg.skip_if_no_field and not c.is_field(reg.column):
                # Skip the check if the field doesn't exist
                continue
            if reg.match_if_field and c.is_field(reg.column):
                return True
            if reg.match_if_no_field and not c.is_field(reg.column):
                return True
            field_value = c.get_field_value(reg.column)
            res = reg.regex.search(field_value)
            if reg.invert:
                res = not res
            if res:
                if GS.debug_level > 1:
                    logger.debug("Excluding '{ref}': Field '{field}' ({value}) matched '{re}'".format(
                                 ref=c.ref, field=reg.column, value=field_value, re=reg.regex))
                # Found a match
                return True
        # Default, could not find any matches
        return False

    def filter(self, comp):
        exclude = self.invert
        value = comp.value.strip().lower()
        # Exclude components with empty 'Value'
        if self.exclude_empty_val and (value == '' or value == '~'):
            return exclude
        # Exclude all ref == #*
        if self.exclude_all_hash_ref and comp.ref[0] == '#':
            return exclude
        # KiCad 5 PCB classification
        if self.exclude_virtual and comp.virtual:
            return exclude
        if self.exclude_smd and comp.smd:
            return exclude
        if self.exclude_tht and comp.tht:
            return exclude
        # List of references to be excluded
        if self.exclude_refs and (comp.ref in self.exclude_refs or comp.ref_prefix+'*' in self.exclude_refs):
            return exclude
        # All stuff where keys are involved
        if self.keys:
            # Exclude components if their 'Value' is any of the keys
            if self.exclude_value and value in self.keys:
                return exclude
            # Exclude components if a field is named as any of the keys
            if self.exclude_field:
                for k in self.keys:
                    if k in comp.dfields:
                        return exclude
            # Exclude components containing a key value in the config field.
            if self.exclude_config:
                config = comp.get_field_value(self.config_field).strip().lower()
                if self.config_separators:
                    # Try with all the separators
                    for sep in self.config_separators:
                        opts = config.split(sep)
                        # Try with all the extracted values
                        for opt in opts:
                            if opt.strip() in self.keys:
                                return exclude
                else:  # No separator
                    if config in self.keys:
                        return exclude
        # Regular expressions
        if not self.test_reg_include(comp):
            return exclude
        if self.test_reg_exclude(comp):
            return exclude
        return not exclude
