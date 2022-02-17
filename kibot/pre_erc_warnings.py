# -*- coding: utf-8 -*-
# Copyright (c) 2021 Salvador E. Tropea
# Copyright (c) 2021 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
from .macros import macros, pre_class  # noqa: F401
from .error import (KiPlotConfigurationError)
from .pre_base import BasePreFlight


@pre_class
class ERC_Warnings(BasePreFlight):  # noqa: F821
    """ [boolean=false] Option for `run_erc`. ERC warnings are considered errors """
    def __init__(self, name, value):
        super().__init__(name, value)
        if not isinstance(value, bool):
            raise KiPlotConfigurationError('must be boolean')
        self._enabled = value

    @staticmethod
    def get_example():
        """ Returns a YAML value for the example config """
        return 'false'

    def apply(self):
        BasePreFlight._set_option('erc_warnings', self._enabled)  # noqa: F821
