# -*- coding: utf-8 -*-
# Copyright (c) 2020-2024 Salvador E. Tropea
# Copyright (c) 2020-2024 Instituto Nacional de Tecnología Industrial
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)
# Contributors: Leandro Heck (@leoheck)
import os
import re
from .gs import GS
from .error import KiPlotConfigurationError
from .misc import pretty_list
from .optionable import Optionable
from .kiplot import get_output_dir
from .macros import macros, document, pre_class  # noqa: F401
from .log import get_logger

logger = get_logger(__name__)


class FilterOptionsKiBot(Optionable):
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
            """ Error id we want to exclude """
            self.number = 0
            """ Error number we want to exclude """
            self.error_number = None
            """ {number} """
            self.regex = ''
            """ Regular expression to match the text for the error we want to exclude """
            self.regexp = None
            """ {regex} """

    def __str__(self):
        txt = self.filter
        if self.error:
            txt += f' ({self.error})'
        if getattr(self, 'number', None):
            txt += f' ({self.number})'
        if self.regex:
            txt += f' [{self.regex}]'
        return txt


class FilterOptions(FilterOptionsKiBot):
    """ Valid options for a filter entry """
    def __init__(self):
        super().__init__()
        self.add_to_doc('error', 'A name for KiCad 6 or a number for KiCad 5, but always a string')
        self.add_to_doc('number', 'KiCad 5 only')
        self._error_example = 'lib_symbol_issues'


class FiltersOptions(Optionable):
    """ A list of filter entries """
    def __init__(self):
        super().__init__()
        with document:
            self.filters = FilterOptions
            """ [list(dict)=[]] DRC/ERC errors to be ignored """
        self._filter_what = 'DRC/ERC errors'

    def config(self, parent):
        super().config(parent)
        parsed = None
        for f in self.filters:
            where = ' (in `{}` filter)'.format(f.filter) if f.filter else ''
            error = f.error
            if not error:
                if not hasattr(f, 'number') or not f.number:
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
            f._regex = re.compile(regex)
        self._parsed = parsed


@pre_class
class Filters(BasePreFlight, FiltersOptions):  # noqa: F821
    """ Filters
        A list of entries to filter out ERC/DRC messages when using *run_erc*/*run_drc*.
        Avoid using it with the new *erc* and *drc* preflights.
        Note that ignored errors will become KiBot warnings (i.e. `(W058) ...`).
        To farther ignore these warnings use the `filters` option in the `global` section """
    def __init__(self):
        super().__init__()
        self.set_doc('filters', "[list(dict)=[]] One or more filters")

    def __str__(self):
        return super().__str__()+f' ({pretty_list([v.filter for v in self.filters])})'

    def get_example() -> str:
        """ Returns a YAML value for the example config """
        return "\n    - filter: 'Filter description'\n      error: '10'\n      regex: 'Regular expression to match'"

    def apply(self):
        # Create the filters file
        if self.filters:
            our_dir = GS.global_dir if GS.global_use_dir_for_preflights else ''
            o_dir = get_output_dir(our_dir, self)
            GS.filter_file = os.path.join(o_dir, 'kibot_errors.filter')
            GS.filters = self.filters
            with open(GS.filter_file, 'w') as f:
                f.write(self._parsed)
