# -*- coding: utf-8 -*-
# Copyright (c) 2022-2024 Salvador E. Tropea
# Copyright (c) 2022-2024 Instituto Nacional de Tecnología Industrial
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)
import pcbnew
from .gs import GS
from .kiplot import load_board
from .macros import macros, document, pre_class  # noqa: F401


@pre_class
class Fill_Zones(BasePreFlight):  # noqa: F821
    """ Fill Zones
        Fill all zones again and save the PCB """
    def __init__(self):
        super().__init__()
        self._pcb_related = True
        with document:
            self.fill_zones = False
            """ Enable this preflight """
        # Do it after
        self._priority = 10

    def apply(self):
        load_board()
        pcbnew.ZONE_FILLER(GS.board).Fill(GS.board.Zones())
        GS.save_pcb()
        BasePreFlight._set_option('fill_zones', True)  # noqa: F821
