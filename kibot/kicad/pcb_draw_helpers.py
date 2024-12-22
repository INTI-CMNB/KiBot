# -*- coding: utf-8 -*-
# Copyright (c) 2024 Salvador E. Tropea
# Copyright (c) 2024 Instituto Nacional de Tecnología Industrial
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)
# Helper functions to draw on a BOARD object
from ..gs import GS
import pcbnew
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


def draw_text(g, x, y, text, h, w, layer, bold=False, alignment=GR_TEXT_HJUSTIFY_LEFT):
    nt = pcbnew.PCB_TEXT(GS.board)
    nt.SetText(text)
    nt.SetBold(bold)
    nt.SetTextX(x)
    nt.SetTextY(y+h)
    nt.SetLayer(layer)
    nt.SetTextWidth(w)
    nt.SetTextHeight(h)
    nt.SetHorizJustify(alignment)
    nt.SetVertJustify(GR_TEXT_VJUSTIFY_CENTER)
    g.AddItem(nt)
    GS.board.Add(nt)
    return nt, nt.GetTextBox().GetWidth()


def draw_poly(g, points, layer, filled=False, line_w=10000):
    assert points or len(points) < 3, "A polygon requires at least 3 points"
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


def get_text_width(text, w=10000, bold=False):
    nt = pcbnew.PCB_TEXT(GS.board)
    nt.SetText(text)
    nt.SetBold(bold)
    nt.SetTextWidth(w)
    width = nt.GetTextBox().GetWidth()
    return width
