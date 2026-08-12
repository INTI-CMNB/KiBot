# -*- coding: utf-8 -*-
# Copyright (c) 2020-2024 Salvador E. Tropea
# Copyright (c) 2020-2024 Instituto Nacional de Tecnología Industrial
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)
from .gs import GS
from .macros import macros, document, pre_class  # noqa: F401


@pre_class
class Check_Zone_Fills(BasePreFlight):  # noqa: F821
    """ Check Zone Fills
        Zones are filled before doing any operation involving PCB layers.
        The original PCB remains unchanged. If you need to abort when the zone fill
        creates significant changes to a layer use the CheckZoneFill internal template """
    def __init__(self):
        super().__init__()
        with document:
            self.check_zone_fills = False
            """ Enable this preflight """

    def apply(self):
        BasePreFlight._set_option('check_zone_fills', self._enabled)  # noqa: F821

    def get_example():
        return str(GS.check_zone_fills_example).lower()
