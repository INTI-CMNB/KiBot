# -*- coding: utf-8 -*-
# Copyright (c) 2024 Salvador E. Tropea
# Copyright (c) 2024 Instituto Nacional de Tecnología Industrial
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)
# Helper functions to draw on a BOARD object
from ..gs import GS
from math import sin, cos, radians
from .drill_info import get_full_holes_list
import pcbnew
import re
if GS.ki7:
    # Is this change really needed??!!! People doesn't have much to do ...
    GR_TEXT_HJUSTIFY_LEFT = pcbnew.GR_TEXT_H_ALIGN_LEFT
    GR_TEXT_HJUSTIFY_RIGHT = pcbnew.GR_TEXT_H_ALIGN_RIGHT
    GR_TEXT_HJUSTIFY_CENTER = pcbnew.GR_TEXT_H_ALIGN_CENTER
    GR_TEXT_VJUSTIFY_TOP = pcbnew.GR_TEXT_V_ALIGN_TOP
    GR_TEXT_VJUSTIFY_CENTER = pcbnew.GR_TEXT_V_ALIGN_CENTER
    GR_TEXT_VJUSTIFY_BOTTOM = pcbnew.GR_TEXT_V_ALIGN_BOTTOM
else:
    GR_TEXT_HJUSTIFY_LEFT = pcbnew.GR_TEXT_HJUSTIFY_LEFT
    GR_TEXT_HJUSTIFY_RIGHT = pcbnew.GR_TEXT_HJUSTIFY_RIGHT
    GR_TEXT_HJUSTIFY_CENTER = pcbnew.GR_TEXT_HJUSTIFY_CENTER
    GR_TEXT_VJUSTIFY_TOP = pcbnew.GR_TEXT_VJUSTIFY_TOP
    GR_TEXT_VJUSTIFY_CENTER = pcbnew.GR_TEXT_VJUSTIFY_CENTER
    GR_TEXT_VJUSTIFY_BOTTOM = pcbnew.GR_TEXT_VJUSTIFY_BOTTOM

from .. import log

logger = log.get_logger()


def draw_rect(g, x, y, w, h, layer, filled=False, line_w=10000):
    if not line_w:
        draw_line(g, x, y, x, y, layer)
        x += w
        y += h
        draw_line(g, x, y, x, y, layer)
        return
    nl = pcbnew.PCB_SHAPE(GS.board)
    nl.SetShape(1)
    if filled:
        nl.SetFilled(True)
    pos = nl.GetStart()
    pos.x = x
    pos.y = y
    nl.SetStart(pos)
    pos = nl.GetEnd()
    pos.x = x+w
    pos.y = y+h
    nl.SetEnd(pos)
    nl.SetLayer(layer)
    nl.SetWidth(line_w)
    g.AddItem(nl)
    GS.board.Add(nl)


def draw_line(g, x1, y1, x2, y2, layer, line_w=10000):
    nl = pcbnew.PCB_SHAPE(GS.board)
    pos = nl.GetStart()
    pos.x = x1
    pos.y = y1
    nl.SetStart(pos)
    pos = nl.GetEnd()
    pos.x = x2
    pos.y = y2
    nl.SetEnd(pos)
    nl.SetLayer(layer)
    nl.SetWidth(line_w)
    g.AddItem(nl)
    GS.board.Add(nl)


def draw_text(g, x, y, text, h, w, layer, bold=False, alignment=GR_TEXT_HJUSTIFY_LEFT, font=None):
    nt = pcbnew.PCB_TEXT(GS.board)
    nt.SetText(text)

    nt.SetTextX(x)
    nt.SetTextY(y+h)
    nt.SetLayer(layer)
    nt.SetTextWidth(w)
    nt.SetTextHeight(h)
    nt.SetHorizJustify(alignment)
    nt.SetVertJustify(GR_TEXT_VJUSTIFY_CENTER)
    if font:
        # segfault if overbars (~{text}) with custom fonts
        remove_overbars(nt)
        nt.SetFont(font)
    if bold:
        nt.SetBold(bold)

    g.AddItem(nt)
    GS.board.Add(nt)

    return nt, nt.GetTextBox().GetWidth()


def remove_overbars(txt):
    current_text = txt.GetText()

    if current_text:
        cleaned_text = re.sub(r'~\{(.*?)\}', r'\1', current_text)
        txt.SetText(cleaned_text)


def draw_poly(g, points, layer, filled=False, line_w=10000):
    assert points and len(points) > 2, "A polygon requires at least 3 points"
    sps = pcbnew.SHAPE_POLY_SET()
    chain = pcbnew.SHAPE_LINE_CHAIN()
    for (x, y) in points:
        chain.Append(x, y)
    chain.SetClosed(True)
    sps.AddOutline(chain)
    ps = pcbnew.PCB_SHAPE(GS.board, pcbnew.SHAPE_T_POLY)
    ps.SetPolyShape(sps)
    ps.SetLayer(layer)
    ps.SetFilled(filled)
    ps.SetWidth(line_w)
    g.AddItem(ps)
    GS.board.Add(ps)


def get_text_width(text, w=10000, bold=False, font=None):
    nt = pcbnew.PCB_TEXT(GS.board)
    nt.SetText(text)
    if font:
        # segfault if overbars (~{text}) with custom fonts
        remove_overbars(nt)
        nt.SetFont(font)
    nt.SetTextWidth(w)
    nt.SetBold(bold)
    width = nt.GetTextBox().GetWidth()
    return width


def draw_arc(g, x, y, angle_start, angle, radius, layer, line_w=10000):
    # print(f"arc {x} {y}")
    arc = pcbnew.PCB_SHAPE(GS.board, pcbnew.SHAPE_T_ARC)
    arc.SetCenter(GS.p2v_k7(pcbnew.wxPoint(x, y)))

    start_point = pcbnew.wxPoint(0, 0)
    start_point.x = int(x + radius * cos(radians(angle_start)))
    start_point.y = int(y + radius * sin(radians(angle_start)))
    arc.SetStart(GS.p2v_k7(start_point))

    arc.SetArcAngleAndEnd(GS.angle(angle), True)  # KiCad uses deci-degrees internally

    arc.SetLayer(layer)
    arc.SetWidth(line_w)

    g.AddItem(arc)
    GS.board.Add(arc)


def draw_oval(g, x, y, size, orientation, layer, line_w=10000):
    if size.x > size.y:
        size.x, size.y = size.y, size.x
        if orientation < GS.angle(270):
            orientation += GS.angle(90)
        else:
            orientation -= GS.angle(270)

    deltaxy = size.y - size.x
    radius = size.x // 2

    half_height = deltaxy // 2

    corners = [
        pcbnew.wxPoint(-radius, -half_height),
        pcbnew.wxPoint(-radius, half_height),
        pcbnew.wxPoint(0, half_height),
        pcbnew.wxPoint(radius, half_height),
        pcbnew.wxPoint(radius, -half_height),
        pcbnew.wxPoint(0, -half_height)
    ]

    s = pcbnew.SHAPE_SIMPLE()
    for c in corners:
        s.Append(GS.p2v_k7(c))

    s.Rotate(orientation, GS.p2v_k7(pcbnew.wxPoint(0, 0)))

    for i in range(len(corners)):
        corners[i].x = s.CPoint(i).x
        corners[i].y = s.CPoint(i).y
        corners[i].x += int(x)
        corners[i].y += int(y)

    draw_line(g, corners[0].x, corners[0].y, corners[1].x, corners[1].y, layer, line_w)

    draw_arc(g, corners[2].x, corners[2].y, -orientation.AsDegrees(), 180, radius, layer, line_w)

    draw_line(g, corners[3].x, corners[3].y, corners[4].x, corners[4].y, layer, line_w)

    draw_arc(g, corners[5].x, corners[5].y, -orientation.AsDegrees(), -180, radius, layer, line_w)


def draw_drill_map(g, layer, layer_pair_idx, merge_PTH_NPTH=True, group_slots_and_round_holes=True):

    # Draw elements on Edge.Cuts which are not part of footprints
    for item in GS.board.GetDrawings():
        if item.GetLayer() != pcbnew.Edge_Cuts:
            continue
        if isinstance(item, pcbnew.PCB_SHAPE):
            dummy_shape = item.Duplicate()
            dummy_shape.SetLayer(layer)
            g.AddItem(dummy_shape)
            GS.board.Add(dummy_shape)

    # Plot edge cuts in footprints
    for footprint in GS.board.GetFootprints():
        for item in footprint.GraphicalItems():
            if item.GetLayer() != pcbnew.Edge_Cuts:
                continue
            if isinstance(item, pcbnew.PCB_SHAPE):
                dummy_shape = item.Duplicate()
                dummy_shape.SetLayer(layer)
                g.AddItem(dummy_shape)
                GS.board.Add(dummy_shape)

    hole_list, _, _, _ = get_full_holes_list(merge_PTH_NPTH, group_slots_and_round_holes)

    if layer_pair_idx > len(hole_list)-1:
        logger.error(f"Layer pair index {layer_pair_idx} out of range ({len(hole_list)})")

    draw_drill_marks(g, layer, hole_list[layer_pair_idx])


# Draw marker functions reimplemented from
# https://gitlab.com/kicad/code/kicad/-/blob/master/common/plotters/plotter.cpp

def draw_marker_square(g, x, y, radius, layer, line_w=10000):
    r = round(radius / 1.4142)  # Calculate the side's half-length from the radius.
    w = 2 * r  # The width and height of the square.
    draw_rect(g, x - r, y - r, w, w, layer, False, line_w)


def draw_marker_circle(g, x, y, radius, layer, line_w=10000):
    draw_arc(g, x, y, 0, 360, radius, layer, line_w)


def draw_marker_lozenge(g, x, y, radius, layer, line_w=10000):
    points = [
        (x, y + radius),
        (x + radius, y),
        (x, y - radius),
        (x - radius, y),
    ]
    draw_poly(g, points, layer, False, line_w)


def draw_marker_hbar(g, x, y, radius, layer, line_w=10000):
    draw_line(g, x - radius, y, x + radius, y, layer, line_w)


def draw_marker_slash(g, x, y, radius, layer, line_w=10000):
    draw_line(g, x - radius, y - radius, x + radius, y + radius, layer, line_w)


def draw_marker_backslash(g, x, y, radius, layer, line_w=10000):
    draw_line(g, x + radius, y - radius, x - radius, y + radius, layer, line_w)


def draw_marker_vbar(g, x, y, radius, layer, line_w=10000):
    draw_line(g, x, y - radius, x, y + radius, layer, line_w)


def draw_marker(g, x, y, diameter, layer, shape_id, line_w=10000):
    radius = diameter // 2

    marker_patterns = [
        0o003,  # X
        0o100,  # O
        0o014,  # +
        0o040,  # Sq
        0o020,  # Lz
        0o103,  # X O
        0o017,  # X +
        0o043,  # X Sq
        0o023,  # X Lz
        0o114,  # O +
        0o140,  # O Sq
        0o120,  # O Lz
        0o054,  # + Sq
        0o034,  # + Lz
        0o060,  # Sq Lz
        0o117,  # X O +
        0o143,  # X O Sq
        0o123,  # X O Lz
        0o057,  # X + Sq
        0o037,  # X + Lz
        0o063,  # X Sq Lz
        0o154,  # O + Sq
        0o134,  # O + Lz
        0o074,  # + Sq Lz
        0o174,  # O Sq Lz +
        0o163,  # X O Sq Lz
        0o157,  # X O Sq +
        0o137,  # X O Lz +
        0o077,  # X Sq Lz +
        0o177,  # X O Sq Lz +
        0o110,  # O -
        0o104,  # O |
        0o101,  # O /
        0o050,  # Sq -
        0o044,  # Sq |
        0o041,  # Sq /
        0o030,  # Lz -
        0o024,  # Lz |
        0o021,  # Lz /
        0o150,  # O Sq -
        0o144,  # O Sq |
        0o141,  # O Sq /
        0o130,  # O Lz -
        0o124,  # O Lz |
        0o121,  # O Lz /
        0o070,  # Sq Lz -
        0o064,  # Sq Lz |
        0o061,  # Sq Lz /
        0o170,  # O Sq Lz -
        0o164,  # O Sq Lz |
        0o161,  # O Sq Lz /
        0o102,  # \ O
        0o042,  # \ Sq
        0o022,  # \ Lz
        0o142,  # \ O Sq
        0o122,  # \ O Lz
        0o062,  # \ Sq Lz
        0o162,  # \ O Sq Lz
    ]

    if shape_id >= pcbnew.PLOTTER.MARKER_COUNT:
        # Fallback shape
        draw_marker_circle(g, x, y, radius, layer, line_w)
    else:
        # Decode the pattern and draw the corresponding parts
        pat = marker_patterns[shape_id]

        if pat & 0o001:
            draw_marker_slash(g, x, y, radius, layer, line_w)

        if pat & 0o002:
            draw_marker_backslash(g, x, y, radius, layer, line_w)

        if pat & 0o004:
            draw_marker_vbar(g, x, y, radius, layer, line_w)

        if pat & 0o010:
            draw_marker_hbar(g, x, y, radius, layer, line_w)

        if pat & 0o020:
            draw_marker_lozenge(g, x, y, radius, layer, line_w)

        if pat & 0o040:
            draw_marker_square(g, x, y, radius, layer, line_w)

        if pat & 0o100:
            draw_marker_circle(g, x, y, radius, layer, line_w)


def get_marker_best_pen_size(diameter):
    min_size_mm = 0.1
    best_size = max(diameter // 10, min_size_mm*pcbnew.pcbIUScale.IU_PER_MM)
    return int(best_size)


def get_sketch_oval_best_pen_size():
    sketch_line_width_mm = 0.1
    return int(sketch_line_width_mm*pcbnew.pcbIUScale.IU_PER_MM)


def draw_drill_marks(g, layer, hole_list_layer_pair):

    for hole in hole_list_layer_pair:
        pos = hole.m_Hole_Pos
        width = get_marker_best_pen_size(hole.m_Hole_Diameter)
        draw_marker(g, pos.x, pos.y, hole.m_Hole_Diameter, layer, hole.m_Tool_Reference-1, width)

        if hole.m_Hole_Shape != 0:
            width = get_sketch_oval_best_pen_size()
            draw_oval(g, pos.x, pos.y, hole.m_Hole_Size, hole.m_Hole_Orient, layer, width)
