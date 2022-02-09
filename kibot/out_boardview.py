# -*- coding: utf-8 -*-
# Copyright (c) 2021 Salvador E. Tropea
# Copyright (c) 2021 Instituto Nacional de Tecnología Industrial
# Copyright (c) 2018-2020 @whitequark
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
# Adapted from: https://github.com/whitequark/kicad-boardview
import re
from pcbnew import SHAPE_POLY_SET
from .gs import GS
from .optionable import BaseOptions
from .macros import macros, document, output_class  # noqa: F401
from . import log

logger = log.get_logger()


def skip_module(module, tp=False):
    refdes = module.GetReference()
    if refdes == "REF**":
        return True
    if tp and not refdes.startswith("TP"):
        return True
    if not tp and refdes.startswith("TP"):
        return True
    return False


def coord(nanometers):
    milliinches = nanometers * 5 // 127000
    return milliinches


def y_coord(obj, maxy, y):
    if obj.IsFlipped():
        return coord(y)
    else:
        return coord(maxy - y)


def pad_sort_key(pad):
    name = pad.GetName()
    pad_pos = pad.GetPosition()
    if re.match(r"^\d+$", name):
        return (0, int(name), pad_pos.x, pad_pos.y)
    else:
        return (1, name, pad_pos.x, pad_pos.y)


def convert(pcb, brd):
    # Board outline
    outlines = SHAPE_POLY_SET()
    if GS.ki5():
        pcb.GetBoardPolygonOutlines(outlines, "")
        outline = outlines.Outline(0)
        outline_points = [outline.Point(n) for n in range(outline.PointCount())]
    else:
        pcb.GetBoardPolygonOutlines(outlines)
        outline = outlines.Outline(0)
        outline_points = [outline.GetPoint(n) for n in range(outline.GetPointCount())]
    outline_maxx = max(map(lambda p: p.x, outline_points))
    outline_maxy = max(map(lambda p: p.y, outline_points))

    brd.write("0\n")  # unknown

    brd.write("BRDOUT: {count} {width} {height}\n"
              .format(count=len(outline_points) + outline.IsClosed(),
                      width=coord(outline_maxx),
                      height=coord(outline_maxy)))
    for point in outline_points:
        brd.write("{x} {y}\n"
                  .format(x=coord(point.x),
                          y=coord(point.y)))
    if outline.IsClosed():
        brd.write("{x} {y}\n"
                  .format(x=coord(outline_points[0].x),
                          y=coord(outline_points[0].y)))
    brd.write("\n")

    # Nets
    net_info = pcb.GetNetInfo()
    net_items = [net_info.GetNetItem(n) for n in range(1, net_info.GetNetCount())]

    brd.write("NETS: {count}\n"
              .format(count=len(net_items)))
    for net_item in net_items:
        code = net_item.GetNet() if GS.ki5() else net_item.GetNetCode()
        # if net name contains slashes (due to hierarchical sheets), use part after final slash
        name = net_item.GetNetname().rsplit('/', 1)[-1]
        brd.write("{code} {name}\n"
                  .format(code=code,
                          name=name.replace(" ", u"\u00A0")))
    brd.write("\n")

    # Parts
    module_list = GS.get_modules()
    modules = []
    for m in sorted(module_list, key=lambda mod: mod.GetReference()):
        if not skip_module(m):
            modules.append(m)

    brd.write("PARTS: {count}\n".format(count=len(modules)))
    pin_at = 0
    for module in modules:
        module_bbox = module.GetBoundingBox()
        brd.write("{ref} {x1} {y1} {x2} {y2} {pin} {side}\n"
                  .format(ref=module.GetReference(),
                          x1=coord(module_bbox.GetLeft()),
                          y1=y_coord(module, outline_maxy, module_bbox.GetTop()),
                          x2=coord(module_bbox.GetRight()),
                          y2=y_coord(module, outline_maxy, module_bbox.GetBottom()),
                          pin=pin_at,
                          side=1 + module.IsFlipped()))
        pin_at += module.GetPadCount()
    brd.write("\n")

    # Pins
    pads = []
    for m in modules:
        pads_list = m.Pads()
        for pad in sorted(pads_list, key=lambda pad: pad_sort_key(pad)):
            pads.append(pad)

    brd.write("PINS: {count}\n".format(count=len(pads)))
    for pad in pads:
        pad_pos = pad.GetPosition()
        brd.write("{x} {y} {net} {side}\n"
                  .format(x=coord(pad_pos.x),
                          y=y_coord(pad, outline_maxy, pad_pos.y),
                          net=pad.GetNetCode(),
                          side=1 + pad.IsFlipped()))
    brd.write("\n")

    # Nails
    module_list = GS.get_modules()
    testpoints = []
    for m in sorted(module_list, key=lambda mod: mod.GetReference()):
        if not skip_module(m, tp=True):
            pads_list = m.Pads()
            for pad in sorted(pads_list, key=lambda pad: pad_sort_key(pad)):
                testpoints.append((m, pad))

    brd.write("NAILS: {count}\n".format(count=len(testpoints)))
    for module, pad in testpoints:
        pad_pos = pad.GetPosition()
        brd.write("{probe} {x} {y} {net} {side}\n"
                  .format(probe=module.GetReference()[2:],
                          x=coord(pad_pos.x),
                          y=y_coord(pad, outline_maxy, pad_pos.y),
                          net=pad.GetNetCode(),
                          side=1 + pad.IsFlipped()))
    brd.write("\n")


class BoardViewOptions(BaseOptions):
    def __init__(self):
        with document:
            self.output = GS.def_global_output
            """ Filename for the output (%i=boardview, %x=brd) """
        super().__init__()
        self._expand_id = 'boardview'
        self._expand_ext = 'brd'

    def run(self, output):
        with open(output, 'wt') as f:
            convert(GS.board, f)


@output_class
class BoardView(BaseOutput):  # noqa: F821
    """ BoardView
        Exports the PCB in board view format.
        This format allows simple pads and connections navigation, mainly for circuit debug.
        The output can be loaded using Open Board View (https://openboardview.org/) """
    def __init__(self):
        super().__init__()
        with document:
            self.options = BoardViewOptions
            """ [dict] Options for the `boardview` output """
