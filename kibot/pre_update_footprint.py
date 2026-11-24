# -*- coding: utf-8 -*-
# Copyright (c) 2020-2024 Salvador E. Tropea
# Copyright (c) 2020-2024 Instituto Nacional de Tecnología Industrial
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)
from .gs import GS
from .kicad.pcb import replace_footprints
from .misc import W_NOFOOTP, pretty_list
from .optionable import Optionable
from .macros import macros, document, pre_class  # noqa: F401
from .log import get_logger

logger = get_logger(__name__)


@pre_class
class Update_Footprint(BasePreFlight):  # noqa: F821
    """ Update Footprint
        Updates footprints from the libs, you must provide one or more
        references to be updated. This is useful to replace logos using freshly created versions """
    def __init__(self):
        super().__init__()
        self._pcb_related = True
        with document:
            self.update_footprint = Optionable
            """ [string|list(string)=''] {comma_sep} One or more component references """

    def __str__(self) -> str:
        return f'{self.type} ({pretty_list(self.update_footprint)})'

    def get_example() -> str:
        """ Returns a YAML value for the example config """
        return "QR1,QR2"

    def apply(self):
        if not self.update_footprint:
            logger.warning(W_NOFOOTP+'Nothing to update in `update_footprint`')
        replace_footprints(GS.pcb_file, dict.fromkeys(self.update_footprint), logger)
