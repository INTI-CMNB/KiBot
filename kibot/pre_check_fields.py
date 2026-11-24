# -*- coding: utf-8 -*-
# Copyright (c) 2024-2025 Salvador E. Tropea
# Copyright (c) 2024-2025 Instituto Nacional de Tecnología Industrial
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)
import re
from .error import KiPlotConfigurationError
from .fil_base import BaseFilter
from .kiplot import load_sch
from .misc import CHECK_FIELD, W_CHKFLD, pretty_list
from .optionable import Optionable
from .gs import GS
from .macros import macros, document, pre_class  # noqa: F401
from . import log

logger = log.get_logger()
OPERATIONS = {'>': lambda v, r: v > r,
              '<': lambda v, r: v < r,
              '=': lambda v, r: v == r,
              '<=': lambda v, r: v <= r,
              '>=': lambda v, r: v >= r}


class FieldCheck(Optionable):
    """ Condition to apply to a field """
    def __init__(self):
        super().__init__()
        self._unknown_is_error = True
        with document:
            self.field = ''
            """ *Name of field to check.
                 The `*` name is a special case. Is used to check for extra fields. In this case you must have a
                 rule for each allowed field name and then a rule containing `*` as name. The `severity_missing`
                 is applied if the component contains extra fields """
            self.regex = ''
            """ *Regular expression to match the field content. Note that technically we do a search, not a match """
            self.regexp = None
            """ {regex} """
            self.severity = 'error'
            """ [error,warning,info,skip,continue] Default severity applied to various situations.
                The *error* will stop execution.
                The *warning* and *info* will generate a message and continue with the rest of the tests.
                In the *skip* case we jump to the next component.
                Use *continue* to just skip this test and apply the rest
                """
            self.severity_missing = 'continue'
            """ [error,warning,info,skip,continue,default] What to do if the field isn't defined.
                Default means to use the *severity* option """
            self.severity_no_match = 'default'
            """ [error,warning,info,skip,continue,default] What to do when the regex doesn't match.
                Default means to use the *severity* option """
            self.severity_no_number = 'default'
            """ [error,warning,info,skip,continue,default] What to do if we don't get a number for a *numeric_condition*.
                Default means to use the *severity* option """
            self.severity_fail_condition = 'default'
            """ [error,warning,info,skip,continue,default] What to do when the *numeric_condition* isn't met.
                Default means to use the *severity* option """
            self.numeric_condition = 'none'
            """ [>,>=,<,<=,=,none] Convert the group 1 of the regular expression to a number and apply this operation
                to the *numeric_reference* value """
            self.numeric_reference = 0
            """ Value to compare using *numeric_condition* """
            self.exclude_filter = Optionable
            """ [string|list(string)='_null'] Name of the filter to exclude components from processing """
        self._field_example = 'temperature'

    def __str__(self):
        txt = f'`{self.field}` matched to `{self.regex}`'
        if self.numeric_condition != 'none':
            txt += f' {self.numeric_condition} {self.numeric_reference}'
        txt += f' [{self.severity}]'
        return txt

    def config(self, parent):
        super().config(parent)
        if not self.field:
            raise KiPlotConfigurationError(f"Missing field name ({self._tree})")
        try:
            self._regex = re.compile(self.regex)
        except re.error as e:
            raise KiPlotConfigurationError(f'Wrong regular expression: `{self.regex}` ({e})')
        if self.numeric_condition != 'none' and self._regex.groups < 1:
            raise KiPlotConfigurationError(f'No groups in regular expression: `{self.regex}`')
        self.exclude_filter = BaseFilter.solve_filter(self.exclude_filter, 'exclude_filter')


@pre_class
class Check_Fields(BasePreFlight):  # noqa: F821
    """ Check Fields
        Checks to apply to the schematic fields.
        You can define conditions that must be met by the fields.
        The checks are applied to every component in the schematic.
        When an error is hit execution is stopped.
        One use is to check that all components are suitable for a temperature range.
        In this case a field must declare the temperature range """
    def __init__(self):
        super().__init__()
        with document:
            self.check_fields = FieldCheck
            """ [dict|list(dict)=[]] One or more check rules """

    @classmethod
    def get_example(cls) -> str:
        """ Returns a YAML value for the example config """
        return ("\n    - field: 'temperature'\n"
                r"      regex: '(-?\d+).+?(?:-?\d+).*'"
                "\n      numeric_condition: '<='"
                "\n      numeric_reference: -10")

    def apply_severity(self, check, severity, msg):
        if severity == 'default':
            severity = check.severity
        if severity == 'error':
            GS.exit_with_error(msg, CHECK_FIELD)
        elif severity == 'warning':
            logger.warning(W_CHKFLD+msg)
        elif severity == 'info':
            logger.info(msg)
        return severity == 'skip'

    def __str__(self) -> str:
        return f'{self.type} ({[v.field for v in self.check_fields]})'

    def run(self):
        load_sch()
        if not GS.sch:
            return
        comps = GS.sch.get_components()
        for c in comps:
            checked_fields = {'reference', 'value', 'footprint', 'datasheet', 'description', 'part'}
            for check in self.check_fields:
                # Skip it if this check has an exclude filter and the component is excluded
                if check.exclude_filter and check.exclude_filter.filter(c):
                    continue
                field = check.field.lower()
                if field == '*':
                    # Special case. This is a check for extra fields
                    difference = c.get_real_field_names(set(c.get_field_names()) - checked_fields)
                    if difference and self.apply_severity(check, check.severity_missing,
                                                          f'{c.ref} extra fields: {pretty_list(list(difference))}'):
                        break
                    continue
                checked_fields.add(field)
                if not c.is_field(field):
                    # No field with this name
                    if self.apply_severity(check, check.severity_missing, f'{c.ref} missing field `{check.field}`'):
                        break
                else:
                    v = c.get_field_value(field)
                    match = check._regex.search(v)
                    if not match:
                        if self.apply_severity(check, check.severity_no_match,
                                               f"{c.ref} field `{check.field}` doesn't match `{check.regex}` ({v})"):
                            break
                    elif check.numeric_condition != 'none':
                        matched = match.group(1)
                        try:
                            matched = float(matched)
                        except ValueError:
                            if self.apply_severity(check, check.severity_no_number,
                                                   f"{c.ref} field `{check.field}` matched `{matched}`, but isn't a number"):
                                break
                            else:
                                continue
                        if not OPERATIONS[check.numeric_condition](matched, check.numeric_reference):
                            if self.apply_severity(check, check.severity_fail_condition, f"{c.ref} field `{check.field}` "
                                                   f"fails {matched} {check.numeric_condition} {check.numeric_reference}"):
                                break
