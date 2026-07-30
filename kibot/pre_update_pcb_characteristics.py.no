# -*- coding: utf-8 -*-
# Copyright (c) 2024 Salvador E. Tropea
# Copyright (c) 2024 Instituto Nacional de Tecnología Industrial
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)
from .error import KiPlotConfigurationError
from .gs import GS
from .kiplot import load_board
from .macros import macros, document, pre_class  # noqa: F401
from . import log
import pcbnew
logger = log.get_logger()


def update_table_group(g, values):
    updated = False
    items = sorted(g.GetItems(), key=lambda x: (x.GetY(), x.GetX()))
    items = [item for item in items if isinstance(item, pcbnew.PCB_TEXT)]
    if len(items) != 23:
        logger.non_critical_error("The board characteristicts group doesn't contain 23 text items")
        return False
    is_msg = True
    msg = None
    id = 0
    # Update the group
    for item in items[1:]:
        if is_msg:
            msg = item.GetText()
        else:
            old_v = item.GetText()
            new_v = values[id]
            if old_v != new_v:
                logger.debug(f'- Setting {msg[:-2]} to {new_v} (was {old_v})')
                item.SetText(new_v)
                updated = True
            id = id+1
        is_msg = not is_msg
    return updated


def update_table(values):
    logger.debug('Board characteristics table')
    # Look for the Board Characteristics group
    for g in GS.board.Groups():
        if g.GetName() == 'group-boardCharacteristics':
            # Found the group
            return update_table_group(g, values)
    logger.non_critical_error("Trying to update the Board Characteristics table, but couldn't find it")
    return False


@pre_class
class Update_PCB_Characteristics(BasePreFlight):  # noqa: F821
    """ Update PCB Characteristics
        Update the information in the Board Characteristics.
        Starting with KiCad 7 you can paste a block containing board information using
        Place* -> *Add Board Characteristics*. But this information is static, so if
        you modify anything related to it the block will be obsolete.
        This preflight tries to refresh the information """
    def __init__(self):
        super().__init__()
        self._pcb_related = True
        with document:
            self.update_pcb_characteristics = False
            """ Enable this preflight """

    def v2str(self, v):
        return pcbnew.StringFromValue(self.pcb_iu, self.pcb_units, v, True)

    def apply(self):
        if not GS.ki7:
            raise KiPlotConfigurationError('The `update_spcb_characteristics` preflight needs KiCad 7 or newer')
        load_board()
        # Collect the information
        YESNO = (GS.global_str_no.capitalize(), GS.global_str_yes.capitalize())
        ds = GS.board.GetDesignSettings()
        self.pcb_units = GS.board.GetUserUnits()
        self.pcb_iu = pcbnew.EDA_IU_SCALE(pcbnew.PCB_IU_PER_MM)
        x1, y1, x2, y2 = GS.compute_pcb_boundary(GS.board)
        if x1 is None:
            bb_w = bb_h = 0
        else:
            bb_w = x2-x1
            bb_h = y2-y1
        values = (str(ds.GetCopperLayerCount()),
                  self.v2str(ds.GetBoardThickness()),
                  self.v2str(bb_w)+' x '+self.v2str(bb_h),
                  '',
                  self.v2str(ds.m_TrackMinWidth)+' / '+self.v2str(ds.m_MinClearance),
                  self.v2str(min(ds.m_MinThroughDrill, ds.m_ViasMinSize)),
                  GS.global_pcb_finish,
                  YESNO[GS.global_impedance_controlled],
                  YESNO[GS.global_castellated_pads],
                  YESNO[GS.global_edge_plating],
                  GS.global_edge_connector.capitalize())
        if update_table(values):
            GS.save_pcb()
