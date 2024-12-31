# -*- coding: utf-8 -*-
# Copyright (c) 2024 Nguyen Vincent
# Copyright (c) 2024 Salvador E. Tropea
# Copyright (c) 2024 Instituto Nacional de Tecnología Industrial
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)
# Contributed by Nguyen Vincent (@nguyen-v)
# Reimplementation of
# https://gitlab.com/kicad/code/kicad/-/blob/master/pcbnew/exporters/gendrill_file_writer_base.cpp
from ..gs import GS
import pcbnew
from kibot.misc import VIATYPE_THROUGH
from kibot import log

logger = log.get_logger()

PLATED_DICT = {True: 'NPTH',
               False: 'PTH'}

HOLE_SHAPE_DICT = {0: 'Round',
                   1: 'Slot',
                   2: 'Round + Slot'}

if not GS.ki5:
    HOLE_TYPE_DICT = {pcbnew.HOLE_ATTRIBUTE_HOLE_MECHANICAL: 'Mechanical',
                      pcbnew.HOLE_ATTRIBUTE_HOLE_PAD: 'Pad',
                      pcbnew.HOLE_ATTRIBUTE_HOLE_VIA_THROUGH: 'Via',
                      pcbnew.HOLE_ATTRIBUTE_HOLE_VIA_BURIED: 'Via'}


def get_unique_layer_pairs():
    # Collect all vias on the board
    vias = [item for item in GS.board.GetTracks() if isinstance(item, pcbnew.PCB_VIA)]

    # Use a set to store unique layer pairs
    unique_layer_pairs = set()

    for via in vias:
        # Extract layer pairs from the via
        start_layer = via.TopLayer()
        end_layer = via.BottomLayer()

        layer_pair = (start_layer, end_layer)

        via_type = via.GetViaType()

        # Only note blind or buried vias (not through-hole vias)
        if via_type != VIATYPE_THROUGH:
            unique_layer_pairs.add(layer_pair)

    # Start the returned list with the default through-hole layer pair
    layer_pairs = [(pcbnew.F_Cu, pcbnew.B_Cu)]

    # Add each unique layer pair individually to the list
    for layer_pair in unique_layer_pairs:
        layer_pairs.append(layer_pair)

    return layer_pairs


def get_num_layer_pairs(merge_PTH_NPTH=True):

    hole_sets = get_unique_layer_pairs()

    if not merge_PTH_NPTH:

        hole_sets.append((pcbnew.F_Cu, pcbnew.B_Cu))

        hole_list_layer_pair, _ = build_holes_list(
            hole_sets[-1], merge_PTH_NPTH, doing_npth=True, group_slots_and_round_holes=True
        )
        if len(hole_list_layer_pair) == 0:
            hole_sets.pop()

    return len(hole_sets)


def get_full_holes_list(merge_PTH_NPTH=True, group_slots_and_round_holes=True):

    hole_list = []
    tool_list = []

    hole_sets = get_unique_layer_pairs()

    if not merge_PTH_NPTH:
        hole_sets.append((pcbnew.F_Cu, pcbnew.B_Cu))

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

        hole_sets.append((pcbnew.F_Cu, pcbnew.B_Cu))

        hole_list_layer_pair, _ = build_holes_list(
            hole_sets[-1], merge_PTH_NPTH, doing_npth=True, group_slots_and_round_holes=True
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
        top_layer = layer_pair[0] + 1
        bot_layer = layer_pair[1] + 1 if layer_pair[1] != pcbnew.B_Cu else layer_cnt
        return f'L{top_layer} - L{bot_layer}'


def build_holes_list(layer_pair, merge_PTH_NPTH, generate_NPTH_list=True,
                     group_slots_and_round_holes=True):

    # Buffer associated to specific layer pairs
    hole_list_layer_pair = []
    tool_list_layer_pair = []

    assert layer_pair[0] < layer_pair[1], "Invalid layer pair order."

    # Add plated vias to hole_list_layer_pair
    if not generate_NPTH_list:
        for via in GS.board.GetTracks():
            # Check if the current track is a via
            if not isinstance(via, pcbnew.PCB_VIA):
                continue

            hole_sz = via.GetDrillValue()

            if hole_sz == 0:
                continue

            new_hole = pcbnew.HOLE_INFO()
            new_hole.m_ItemParent = via

            if GS.ki5:
                new_hole.m_HoleAttribute = 0
            else:
                if layer_pair == (pcbnew.F_Cu, pcbnew.B_Cu):
                    new_hole.m_HoleAttribute = pcbnew.HOLE_ATTRIBUTE_HOLE_VIA_THROUGH
                else:
                    new_hole.m_HoleAttribute = pcbnew.HOLE_ATTRIBUTE_HOLE_VIA_BURIED

            new_hole.m_Tool_Reference = -1
            new_hole.m_Hole_Orient = GS.angle(0)
            new_hole.m_Hole_Diameter = hole_sz
            new_hole.m_Hole_NotPlated = False
            new_hole.m_Hole_Size.x = new_hole.m_Hole_Size.y = new_hole.m_Hole_Diameter

            new_hole.m_Hole_Shape = 0
            new_hole.m_Hole_Pos = via.GetStart()

            new_hole.m_Hole_Top_Layer = via.TopLayer()
            new_hole.m_Hole_Bottom_Layer = via.BottomLayer()

            if (new_hole.m_Hole_Top_Layer != layer_pair[0]) or \
               (new_hole.m_Hole_Bottom_Layer != layer_pair[1]):
                continue

            hole_list_layer_pair.append(new_hole)

    # Add footprint/pad related PTH to hole_list_layer_pair
    if layer_pair == (pcbnew.F_Cu, pcbnew.B_Cu):
        for footprint in GS.board.GetFootprints():
            for pad in footprint.Pads():

                if not merge_PTH_NPTH:
                    if not generate_NPTH_list and pad.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                        continue

                    if generate_NPTH_list and pad.GetAttribute() != pcbnew.PAD_ATTRIB_NPTH:
                        continue

                if pad.GetDrillSize().x == 0:
                    continue

                new_hole = pcbnew.HOLE_INFO()

                new_hole.m_ItemParent = pad
                new_hole.m_Hole_NotPlated = pad.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH
                if GS.ki5:
                    new_hole.m_HoleAttribute = 0
                else:
                    new_hole.m_HoleAttribute = (pcbnew.HOLE_ATTRIBUTE_HOLE_MECHANICAL if
                                                new_hole.m_Hole_NotPlated else pcbnew.HOLE_ATTRIBUTE_HOLE_PAD)
                new_hole.m_Tool_Reference = -1
                new_hole.m_Hole_Orient = pad.GetOrientation()
                new_hole.m_Hole_Diameter = min(pad.GetDrillSize().x, pad.GetDrillSize().y)
                new_hole.m_Hole_Size = pad.GetDrillSize()
                new_hole.m_Hole_Shape = 1 if (pad.GetDrillShape() != pcbnew.PAD_DRILL_SHAPE_CIRCLE and
                                              pad.GetDrillSize().x != pad.GetDrillSize().y) else 0
                new_hole.m_Hole_Pos = pad.GetPosition()
                new_hole.m_Hole_Top_Layer = pcbnew.F_Cu
                new_hole.m_Hole_Bottom_Layer = pcbnew.B_Cu

                hole_list_layer_pair.append(new_hole)

    if GS.ki5:
        hole_list_layer_pair.sort(key=lambda hole: (
            hole.m_Hole_NotPlated,       # Non-plated holes come after plated holes
            hole.m_Hole_Diameter,        # Increasing diameter
            hole.m_Hole_Shape,           # Circles first, then slots
            hole.m_Hole_Pos.x,           # X position
            hole.m_Hole_Pos.y            # Y position
        ))
    else:
        hole_list_layer_pair.sort(key=lambda hole: (
            hole.m_Hole_NotPlated,       # Non-plated holes come after plated holes
            hole.m_Hole_Diameter,        # Increasing diameter
            hole.m_HoleAttribute,        # Attribute type
            hole.m_Hole_Shape,           # Circles first, then slots
            hole.m_Hole_Pos.x,           # X position
            hole.m_Hole_Pos.y            # Y position
        ))

    last_hole_diameter = -1
    last_not_plated = False
    if GS.ki5:
        last_attribute = 0
    else:
        last_attribute = pcbnew.HOLE_ATTRIBUTE_HOLE_UNKNOWN

    last_hole_shape = -1

    for hole in hole_list_layer_pair:

        if (hole.m_Hole_Diameter != last_hole_diameter or
                hole.m_Hole_NotPlated != last_not_plated or
                hole.m_HoleAttribute != last_attribute or
                (not group_slots_and_round_holes and hole.m_Hole_Shape != last_hole_shape)):

            new_tool = pcbnew.DRILL_TOOL(0, False)

            new_tool.m_Diameter = hole.m_Hole_Diameter
            new_tool.m_Hole_NotPlated = hole.m_Hole_NotPlated
            if not GS.ki5:
                new_tool.m_HoleAttribute = hole.m_HoleAttribute
            new_tool.m_Hole_Shape = hole.m_Hole_Shape  # not present in original implementation
            new_tool.m_TotalCount = 0
            new_tool.m_OvalCount = 0

            tool_list_layer_pair.append(new_tool)

            last_hole_diameter = new_tool.m_Diameter
            last_not_plated = new_tool.m_Hole_NotPlated
            if not GS.ki5:
                last_attribute = new_tool.m_HoleAttribute
            last_hole_shape = new_tool.m_Hole_Shape

        tool_index = len(tool_list_layer_pair)

        if tool_index == 0:
            continue

        hole.m_Tool_Reference = tool_index
        tool_list_layer_pair[-1].m_TotalCount += 1

        if hole.m_Hole_Shape:
            tool_list_layer_pair[-1].m_OvalCount += 1

        if (tool_list_layer_pair[-1].m_OvalCount > 0 and
                tool_list_layer_pair[-1].m_TotalCount > tool_list_layer_pair[-1].m_OvalCount):
            tool_list_layer_pair[-1].m_Hole_Shape = 2  # The tool is associated to both slots and round holes

    return hole_list_layer_pair, tool_list_layer_pair