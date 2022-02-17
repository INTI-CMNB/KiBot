# -*- coding: utf-8 -*-
# Copyright (c) 2020 Salvador E. Tropea
# Copyright (c) 2020 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
from .error import (KiPlotConfigurationError)
from .macros import macros, pre_class  # noqa: F401
from .pre_base import BasePreFlight


@pre_class
class Check_Zone_Fills(BasePreFlight):  # noqa: F821
    """ [boolean=false] Zones are filled before doing any operation involving PCB layers """
    def __init__(self, name, value):
        super().__init__(name, value)
        if not isinstance(value, bool):
            raise KiPlotConfigurationError('must be boolean')
        self._enabled = value

    def apply(self):
        BasePreFlight._set_option('check_zone_fills', self._enabled)  # noqa: F821
