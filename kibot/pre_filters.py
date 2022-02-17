# -*- coding: utf-8 -*-
# Copyright (c) 2020-2021 Salvador E. Tropea
# Copyright (c) 2020-2021 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
# Contributors: Leandro Heck (@leoheck)
import os
import re
from .gs import GS
from .error import KiPlotConfigurationError
from .optionable import Optionable
from .kiplot import get_output_dir
from .macros import macros, document, pre_class  # noqa: F401
from .pre_base import BasePreFlight
from .log import get_logger

logger = get_logger(__name__)


class FilterOptions(Optionable):
    """ Valid options for a filter entry """
    def __init__(self):
        super().__init__()
        self._unknown_is_error = True
        with document:
            self.filter = ''
            """ Name for the filter, for documentation purposes """
            self.filter_msg = None
            """ {filter} """
            self.error = ''
            """ Error id we want to exclude. A name for KiCad 6 or a number for KiCad 5, but always a string """
            self.number = 0
            """ Error number we want to exclude. KiCad 5 only """
            self.error_number = None
            """ {number} """
            self.regex = 'None'
            """ Regular expression to match the text for the error we want to exclude """
            self.regexp = None
            """ {regex} """


class FiltersOptions(Optionable):
    """ A list of filter entries """
    def __init__(self):
        super().__init__()
        with document:
            self.filters = FilterOptions
            """ [list(dict)] DRC/ERC errors to be ignored """
        self._filter_what = 'DRC/ERC errors'

    def config(self, parent):
        super().config(parent)
        parsed = None
        self.unparsed = None
        if not isinstance(self.filters, type):
            for f in self.filters:
                where = ' (in `{}` filter)'.format(f.filter) if f.filter else ''
                error = f.error
                if not error:
                    if not f.number:
                        raise KiPlotConfigurationError('Missing `error`'+where)
                    error = str(f.number)
                regex = f.regex
                if regex == 'None':
                    raise KiPlotConfigurationError('Missing `regex`'+where)
                comment = f.filter
                logger.debug("Adding {} filter '{}','{}','{}'".format(self._filter_what, comment, error, regex))
                if parsed is None:
                    parsed = ''
                if comment:
                    parsed += '# '+comment+'\n'
                parsed += '{},{}\n'.format(error, regex)
                f.regex = re.compile(regex)
        # If the list is valid make a copy for the warnings filter
        if parsed:
            self.unparsed = self.filters
        self.filters = parsed


@pre_class
class Filters(BasePreFlight):  # noqa: F821
    """ [list(dict)] A list of entries to filter out ERC/DRC messages """
    def __init__(self, name, value):
        f = FiltersOptions()
        f.set_tree({'filters': value})
        f.config(self)
        super().__init__(name, f.filters)

    @staticmethod
    def get_example():
        """ Returns a YAML value for the example config """
        return "\n    - filter: 'Filter description'\n      error: '10'\n      regex: 'Regular expression to match'"

    @classmethod
    def get_doc(cls):
        return cls.__doc__, FilterOptions

    def apply(self):
        # Create the filters file
        if self._value:
            o_dir = get_output_dir('', self)
            GS.filter_file = os.path.join(o_dir, 'kibot_errors.filter')
            with open(GS.filter_file, 'w') as f:
                f.write(self._value)
