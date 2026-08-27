# -*- coding: utf-8 -*-
# Copyright (c) 2024 Nguyen Vincent
# Copyright (c) 2024-2026 Salvador E. Tropea
# Copyright (c) 2024-2026 Instituto Nacional de Tecnología Industrial
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)
# Contributed by Nguyen Vincent (@nguyen-v)
# Reimplementation of
# https://gitlab.com/kicad/code/kicad/-/blob/master/pcbnew/exporters/gendrill_file_writer_base.cpp
from ..gs import GS
from kibot import log

logger = log.get_logger()

PLATED_DICT = {True: 'NPTH',
               False: 'PTH'}

# Values for tool usage
HOLE_ROUND = 0
HOLE_SLOT = 1
HOLE_ROUND_SLOT = 2

HOLE_SHAPE_DICT = {HOLE_ROUND: 'Round',
                   HOLE_SLOT: 'Slot',
                   HOLE_ROUND_SLOT: 'Round + Slot'}

HOLE_UNKNOWN = -1
HOLE_MECHANICAL = 0
HOLE_PAD = 1
HOLE_VIA_THROUGH = 2
HOLE_VIA_BURIED = 3

HOLE_TYPE_DICT = {HOLE_MECHANICAL: 'Mechanical',
                  HOLE_PAD: 'Pad',
                  HOLE_VIA_THROUGH: 'Via',
                  HOLE_VIA_BURIED: 'Via'}

FRONT_AND_BACK = (GS.F_Cu, GS.B_Cu)


class HoleInfo(object):
    def __init__(self):
        super().__init__()
        self.m_HoleAttribute = HOLE_VIA_THROUGH
        self.m_Tool_Reference = -1
        self.m_Hole_Orient = GS.angle(0) if GS.ki7 else 0.0
        self.m_Hole_Diameter = 0
        self.m_Hole_NotPlated = False
        self.m_Hole_Size_x = self.m_Hole_Size_y = 0
        self.m_Hole_Shape = HOLE_ROUND
        self.m_Hole_Pos = None
        self.m_Hole_Top_Layer = GS.F_Cu
        self.m_Hole_Bottom_Layer = GS.B_Cu


class ToolInfo(object):
    def __init__(self, hole):
        super().__init__()
        self.m_Diameter = hole.m_Hole_Diameter
        self.m_Hole_NotPlated = hole.m_Hole_NotPlated
        self.m_HoleAttribute = hole.m_HoleAttribute
        self.m_Hole_Shape = hole.m_Hole_Shape  # not present in original implementation
        self.m_TotalCount = 0
        self.m_OvalCount = 0


def get_unique_layer_pairs():
    # Collect all vias on the board
    via_type_key = 'PCB_VIA'

    # Collect all vias on the board
    vias = [item for item in GS.board.GetTracks() if item.GetClass() == via_type_key]

    # Use a set to store unique layer pairs
    unique_layer_pairs = set()

    for via in vias:
        # Extract layer pairs from the via
        start_layer = via.TopLayer()
        end_layer = via.BottomLayer()

        layer_pair = (start_layer, end_layer)

        via_type = via.GetViaType()

        # Only note blind or buried vias (not through-hole vias)
        if via_type != GS.VIATYPE_THROUGH:
            unique_layer_pairs.add(layer_pair)

    # Start the returned list with the default through-hole layer pair
    layer_pairs = [FRONT_AND_BACK]

    # Add each unique layer pair individually to the list
    for layer_pair in sorted(unique_layer_pairs):
        layer_pairs.append(layer_pair)

    return layer_pairs


def get_num_layer_pairs(merge_PTH_NPTH=True):

    hole_sets = get_unique_layer_pairs()

    if not merge_PTH_NPTH:

        hole_sets.append(FRONT_AND_BACK)

        hole_list_layer_pair, _ = build_holes_list(
            hole_sets[-1], merge_PTH_NPTH, generate_NPTH_list=True, group_slots_and_round_holes=True
        )
        if len(hole_list_layer_pair) == 0:
            hole_sets.pop()

    return len(hole_sets)


def get_full_holes_list(merge_PTH_NPTH=True, group_slots_and_round_holes=True):

    hole_list = []
    tool_list = []

    hole_sets = get_unique_layer_pairs()

    if not merge_PTH_NPTH:
        hole_sets.append(FRONT_AND_BACK)

    for i, pair in enumerate(hole_sets):
        doing_npth = not merge_PTH_NPTH and (i == len(hole_sets)-1)

        hole_list_layer_pair, tool_list_layer_pair = build_holes_list(pair, merge_PTH_NPTH, doing_npth,
                                                                      group_slots_and_round_holes)

        if len(hole_list_layer_pair) > 0:
            hole_list.append(hole_list_layer_pair)
            tool_list.append(tool_list_layer_pair)
        elif doing_npth:
            doing_npth = False
            hole_sets.pop()

    return hole_list, tool_list, hole_sets, doing_npth


def get_layer_pair_name(index, use_layer_names=False, merge_PTH_NPTH=True, group_slots_and_round_holes=True):
    hole_sets = get_unique_layer_pairs()

    if not merge_PTH_NPTH:

        hole_sets.append(FRONT_AND_BACK)

        hole_list_layer_pair, _ = build_holes_list(
            hole_sets[-1], merge_PTH_NPTH, generate_NPTH_list=True, group_slots_and_round_holes=True
        )
        if len(hole_list_layer_pair) == 0:
            hole_sets.pop()

    if index > len(hole_sets)-1:
        logger.error(f"Layer pair index {index} out of range ({len(hole_sets)})")

    layer_pair = hole_sets[index]

    if use_layer_names:
        return f'{GS.board.GetLayerName(layer_pair[0])} - {GS.board.GetLayerName(layer_pair[1])}'
    else:
        layer_cnt = GS.board.GetCopperLayerCount()
        if not GS.ki9:
            top_layer = layer_pair[0] + 1
            bot_layer = layer_pair[1] + 1 if layer_pair[1] != GS.B_Cu else layer_cnt
        else:
            top_layer = int(1 if layer_pair[0] == GS.F_Cu else layer_pair[0]/2)
            bot_layer = int(layer_cnt if layer_pair[1] == GS.B_Cu else layer_pair[1]/2)
        return f'L{top_layer} - L{bot_layer}'


def collect_holes_k6(layer_pair, merge_PTH_NPTH, generate_NPTH_list):
    pcbnew = GS.pn
    hole_list_layer_pair = []
    # This is no longer valid on KiCad 9 where micro vias can specify their real top layer
    # assert layer_pair[0] < layer_pair[1], f"Invalid layer pair order {layer_pair[0]} {layer_pair[1]}"

    # Add plated vias to hole_list_layer_pair
    if not generate_NPTH_list:
        for via in GS.board.GetTracks():
            if not isinstance(via, pcbnew.PCB_VIA):
                continue

            hole_sz = via.GetDrillValue()
            if hole_sz == 0:
                continue

            top_layer = via.TopLayer()
            bottom_layer = via.BottomLayer()
            if (top_layer != layer_pair[0]) or (bottom_layer != layer_pair[1]):
                continue

            new_hole = HoleInfo()
            if layer_pair != FRONT_AND_BACK:
                new_hole.m_HoleAttribute = HOLE_VIA_BURIED
            new_hole.m_Hole_Diameter = hole_sz
            new_hole.m_Hole_Size_x = new_hole.m_Hole_Size_y = new_hole.m_Hole_Diameter
            new_hole.m_Hole_Pos = via.GetStart()
            new_hole.m_Hole_Top_Layer = top_layer
            new_hole.m_Hole_Bottom_Layer = bottom_layer

            hole_list_layer_pair.append(new_hole)

    # Add footprint/pad related PTH to hole_list_layer_pair
    if layer_pair == FRONT_AND_BACK:
        for footprint in GS.get_modules():
            for pad in footprint.Pads():

                if not merge_PTH_NPTH:
                    if not generate_NPTH_list and pad.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                        continue

                    if generate_NPTH_list and pad.GetAttribute() != pcbnew.PAD_ATTRIB_NPTH:
                        continue

                if pad.GetDrillSize().x == 0:
                    continue

                npth = pad.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH
                new_hole = HoleInfo()
                new_hole.m_HoleAttribute = HOLE_MECHANICAL if npth else HOLE_PAD
                new_hole.m_Hole_Orient = pad.GetOrientation() if GS.ki7 else GS.angle_as_double(pad.GetOrientation())
                new_hole.m_Hole_Diameter = min(pad.GetDrillSize().x, pad.GetDrillSize().y)
                new_hole.m_Hole_NotPlated = npth
                dsz = pad.GetDrillSize()
                new_hole.m_Hole_Size_x, new_hole.m_Hole_Size_y = dsz.x, dsz.y
                if pad.GetDrillShape() != pcbnew.PAD_DRILL_SHAPE_CIRCLE and pad.GetDrillSize().x != pad.GetDrillSize().y:
                    new_hole.m_Hole_Shape = HOLE_SLOT
                new_hole.m_Hole_Pos = pad.GetPosition()

                hole_list_layer_pair.append(new_hole)

    return hole_list_layer_pair


def build_holes_list(layer_pair, merge_PTH_NPTH, generate_NPTH_list=True, group_slots_and_round_holes=True):
    # Buffer associated to specific layer pairs
    hole_list_layer_pair = collect_holes_k6(layer_pair, merge_PTH_NPTH, generate_NPTH_list)

    hole_list_layer_pair.sort(key=lambda hole: (
        hole.m_Hole_NotPlated,       # Non-plated holes come after plated holes
        hole.m_Hole_Diameter,        # Increasing diameter
        hole.m_HoleAttribute,        # Attribute type
        hole.m_Hole_Shape,           # Circles first, then slots
        hole.m_Hole_Pos.x,           # X position
        hole.m_Hole_Pos.y            # Y position
    ))

    tool_list_layer_pair = []

    last_hole_diameter = -1
    last_not_plated = False
    last_attribute = HOLE_UNKNOWN
    last_hole_shape = -1
    last_tool = None

    # Holes are sorted so we get batches with similar attributes
    for hole in hole_list_layer_pair:
        if (hole.m_Hole_Diameter != last_hole_diameter or hole.m_Hole_NotPlated != last_not_plated or
            hole.m_HoleAttribute != last_attribute or (not group_slots_and_round_holes and
                                                       hole.m_Hole_Shape != last_hole_shape)):
            last_tool = ToolInfo(hole)
            tool_list_layer_pair.append(last_tool)

            last_hole_diameter = last_tool.m_Diameter
            last_not_plated = last_tool.m_Hole_NotPlated
            last_attribute = last_tool.m_HoleAttribute
            last_hole_shape = last_tool.m_Hole_Shape

        hole.m_Tool_Reference = len(tool_list_layer_pair)

        last_tool.m_TotalCount += 1

        if hole.m_Hole_Shape != HOLE_ROUND:
            last_tool.m_OvalCount += 1

        if last_tool.m_OvalCount > 0 and last_tool.m_TotalCount > last_tool.m_OvalCount:
            last_tool.m_Hole_Shape = HOLE_ROUND_SLOT  # The tool is associated to both slots and round holes

    return hole_list_layer_pair, tool_list_layer_pair
