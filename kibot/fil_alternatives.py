# -*- coding: utf-8 -*-
# Copyright (c) 2026 Salvador E. Tropea
# Copyright (c) 2026 Instituto Nacional de Tecnología Industrial
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)
# Description: Extracts information from the distributor spec and fills fields
from .error import KiPlotConfigurationError
from .misc import pretty_list, W_NONUMBER, W_UNKFLD
# from .gs import GS
from .optionable import Optionable
from .macros import macros, document, filter_class  # noqa: F401
from . import log

logger = log.get_logger()


class AlternativesSymbols(Optionable):
    """ A symbol and the fields to affect """
    def __init__(self):
        super().__init__()
        self._unknown_is_error = True
        with document:
            self.library_link = ''
            """ Full name for the symbol (LIBRARY:SYMBOL) to apply the `fields` """
            self.fields = Optionable
            """ *[list(string_dict)=[]] List of alternatives """
        self._library_link_example = 'Device:R100K'

    def config(self, parent):
        super().config(parent)
        if not self.library_link:
            raise KiPlotConfigurationError(f"Missing or empty `library_link` in alternatives filter ({self._tree})")
        # if not self.fields:
        #     raise KiPlotConfigurationError(f"Missing or empty `fields` in alternatives filter ({self._tree})")

    def __str__(self):
        return self.library_link+' -> '+pretty_list([f.name for f in self.fields])


@filter_class
class Alternatives(BaseFilter):  # noqa: F821
    """ Alternatives
        This filter automatically fills alternative fields for symbols.
        You can have various alternative manufacturers, part numbers, etc.
        The names of the alternative fields are created using the `pattern` option.
        To avoid warnings at least one component in the schematic should define the alternative fields,
        you can leave their value empty. In this way KiBot will know these names are valid even before
        running the filter.
    """
    def __init__(self):
        super().__init__()
        self._is_transform = True
        with document:
            self.pattern = '%f%d'
            """ Pattern used to generate the alternative field.
                %f is the current field name.
                %d is the alternative number """
            self.number_from = 2
            """ First number used for the alternative number (%d)  """
            self.parts = AlternativesSymbols
            """ *[dict|list(dict)=[]] List of symbols to process """

    def config(self, parent):
        super().config(parent)
        if '%d' not in self.pattern:
            logger.warning(W_NONUMBER+"The alternative pattern should contain `%d` ({self.pattern})")
        self._lib_ids = {p.library_link: p for p in self.parts}

    def get_expanded_name(self, name, n):
        res = self.pattern
        res = res.replace('%f', name)
        res = res.replace('%d', str(n))
        return res

    def filter(self, comp):
        # Hay que armar una config e implementarlo
        logger.debug(f'- Match for {comp.ref}')
        # Check if this matches any of the defined rules
        rule = self._lib_ids.get(comp.lib_id)
        if not rule:
            return
        # Add alternatives
        n = self.number_from
        for fields in rule.fields:
            for name, value in fields.items():
                full_name = self.get_expanded_name(name, n)
                if not name.lower() in comp.dfields:
                    logger.warning(W_UNKFLD+f"Defining alternative `{full_name}` for `{comp.ref}`, but it doesn't "
                                   f"have `{name}` field")
                logger.debug(f'  - {full_name} = {value}')
                comp.set_field(full_name, value)
            n += 1
