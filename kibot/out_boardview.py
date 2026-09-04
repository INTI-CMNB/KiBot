# -*- coding: utf-8 -*-
# Copyright (c) 2021-2025 Salvador E. Tropea
# Copyright (c) 2021-2025 Instituto Nacional de Tecnología Industrial
# Copyright (c) 2018-2025 @whitequark
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)
# Adapted from: https://github.com/whitequark/kicad-boardview
import re
from pcbnew import SHAPE_POLY_SET, PAD_SHAPE_CIRCLE
from .gs import GS
from .kiplot import get_all_components
from .out_base import VariantOptions
from .macros import macros, document, output_class  # noqa: F401
from . import log

logger = log.get_logger()


def skip_module(module, tp=False):
    if module.GetPadCount() == 0:
        return True
    refdes = module.Reference().GetText()
    if tp and not refdes.startswith("TP"):
        return True
    if not tp and refdes.startswith("TP"):
        return True
    return False


def coord(nanometers):
    milliinches = nanometers * 5 // 127000
    return milliinches


def y_coord(maxy, y, flipped):
    # Adjust y-coordinate to start from the bottom of the board and account for flipped components
    return coord(maxy - y) if not flipped else coord(y)


def natural_sort_key(s):
    is_blank = s.strip() == ''
    return (is_blank, [int(text) if text.isdigit() else text.casefold()
                       for text in re.compile('([0-9]+)').split(s)])


def convert_brd(pcb, brd, do_sort):
    # Board outline
    # <-- This code can't be a function or we crash pcbnew API
    outlines = SHAPE_POLY_SET()
    if GS.ki5:
        pcb.GetBoardPolygonOutlines(outlines, "")
        outline = outlines.Outline(0)
        outline_points = [outline.Point(n) for n in range(outline.PointCount())]
    else:
        if GS.ki10:
            pcb.GetBoardPolygonOutlines(outlines, True)
        else:
            pcb.GetBoardPolygonOutlines(outlines)
        outline = outlines.Outline(0)
        outline_points = [outline.GetPoint(n) for n in range(outline.GetPointCount())]
    # <-- End
    outline_maxx = max((p.x for p in outline_points))
    outline_maxy = max((p.y for p in outline_points))

    brd.write("0\n")  # unknown

    brd.write("BRDOUT: {count} {width} {height}\n"
              .format(count=len(outline_points) + outline.IsClosed(),
                      width=coord(outline_maxx),
                      height=coord(outline_maxy)))
    for point in outline_points:
        brd.write("{x} {y}\n"
                  .format(x=coord(point.x),
                          y=y_coord(outline_maxy, point.y, False)))
    if outline.IsClosed():
        brd.write("{x} {y}\n"
                  .format(x=coord(outline_points[0].x),
                          y=y_coord(outline_maxy, outline_points[0].y, False)))
    brd.write("\n")

    # Nets
    net_info = pcb.GetNetInfo()
    net_items = [net_info.GetNetItem(n) for n in range(1, net_info.GetNetCount())]

    brd.write("NETS: {count}\n"
              .format(count=len(net_items)))
    for net_item in net_items:
        code = net_item.GetNet() if GS.ki5 else net_item.GetNetCode()
        brd.write("{code} {name}\n"
                  .format(code=code,
                          name=net_item.GetNetname().replace(" ", u"\u00A0")))
    brd.write("\n")

    # Parts
    module_list = GS.get_modules()
    if do_sort:
        module_list = sorted(module_list, key=lambda mod: GS.fp_get_reference(mod))
    modules = []
    for m in module_list:
        if not skip_module(m):
            modules.append(m)

    brd.write("PARTS: {count}\n".format(count=len(modules)))
    pin_at = 0
    for module in modules:
        module_bbox = module.GetBoundingBox()
        flipped = GS.fp_is_bottom(module)
        brd.write("{ref} {x1} {y1} {x2} {y2} {pin} {side}\n"
                  .format(ref=GS.fp_get_reference(module),
                          x1=coord(module_bbox.GetLeft()),
                          y1=y_coord(outline_maxy, module_bbox.GetTop(), flipped),
                          x2=coord(module_bbox.GetRight()),
                          y2=y_coord(outline_maxy, module_bbox.GetBottom(), flipped),
                          pin=pin_at,
                          side=1 + flipped))
        pin_at += module.GetPadCount()
    brd.write("\n")

    # Pins
    pads = []
    for m in modules:
        pads_list = GS.fp_get_pads(m)
        for pad in sorted(pads_list, key=lambda pad: natural_sort_key(pad.GetName())):
            pads.append(pad)

    brd.write("PINS: {count}\n".format(count=len(pads)))
    for pad in pads:
        pad_pos = pad.GetPosition()
        flipped = pad.IsFlipped()
        brd.write("{x} {y} {net} {side}\n"
                  .format(x=coord(pad_pos.x),
                          y=y_coord(outline_maxy, pad_pos.y, flipped),
                          net=pad.GetNetCode(),
                          side=1 + flipped))
    brd.write("\n")

    # Nails
    module_list = GS.get_modules()
    if do_sort:
        module_list = sorted(module_list, key=lambda mod: GS.fp_get_reference(mod))
    testpoints = []
    for m in module_list:
        if not skip_module(m, tp=True):
            pads_list = GS.fp_get_pads(m)
            for pad in sorted(pads_list, key=lambda pad: natural_sort_key(pad.GetName())):
                testpoints.append((m, pad))

    brd.write("NAILS: {count}\n".format(count=len(testpoints)))
    for module, pad in testpoints:
        pad_pos = pad.GetPosition()
        flipped = pad.IsFlipped()
        brd.write("{probe} {x} {y} {net} {side}\n"
                  .format(probe=GS.fp_get_reference(module)[2:],
                          x=coord(pad_pos.x),
                          y=y_coord(outline_maxy, pad_pos.y, flipped),
                          net=pad.GetNetCode(),
                          side=1 + flipped))
    brd.write("\n")


def convert_bvr(pcb, bvr):
    bvr.write("BVRAW_FORMAT_3\n")

    # <-- This code can't be a function or we crash pcbnew API
    outlines = SHAPE_POLY_SET()
    if GS.ki5:
        pcb.GetBoardPolygonOutlines(outlines, "")
        outline = outlines.Outline(0)
        outline_points = [outline.Point(n) for n in range(outline.PointCount())]
    else:
        if GS.ki10:
            pcb.GetBoardPolygonOutlines(outlines, True)
        else:
            pcb.GetBoardPolygonOutlines(outlines)
        outline = outlines.Outline(0)
        outline_points = [outline.GetPoint(n) for n in range(outline.GetPointCount())]
    # <-- End
    max((p.x for p in outline_points))
    outline_maxy = max((p.y for p in outline_points))

    module_list = GS.get_modules()
    modules = []
    for module in module_list:
        if not skip_module(module):
            modules.append(module)

        ref = GS.fp_get_reference(module)
        flipped = GS.fp_is_bottom(module)
        side = "B" if flipped else "T"
        mount = GS.fp_get_mounting_style_str(module)
        pads_list = GS.fp_get_pads(module)

        bvr.write("\n")
        bvr.write(f"PART_NAME {ref}\n")
        bvr.write(f"   PART_SIDE {side}\n")
        bvr.write("   PART_ORIGIN 0.000 0.000\n")
        bvr.write(f"   PART_MOUNT {mount}\n")
        bvr.write("\n")

        for pad in sorted(pads_list, key=lambda pad: natural_sort_key(pad.GetName())):
            pin_num = GS.pad_get_number(pad)
            net = GS.pad_get_net_name(pad)
            pad_bbox = pad.GetBoundingBox()
            pad_size = pad.GetSize()

            x_center = (pad_bbox.GetLeft() + pad_bbox.GetRight()) / 2
            y_center = (pad_bbox.GetTop() + pad_bbox.GetBottom()) / 2
            x = coord(x_center)
            y = y_coord(outline_maxy, y_center, flipped)

            if flipped:
                y = coord(outline_maxy - y_center)

            if pad.GetShape() == PAD_SHAPE_CIRCLE:
                radius = coord(pad_size.x / 1.6)
            else:
                smaller_dimension = min(pad_size.x, pad_size.y)
                radius = coord(smaller_dimension / 1.6)

            bvr.write(f"   PIN_ID {ref}-{pin_num}\n")
            bvr.write(f"      PIN_NUMBER {pin_num}\n")
            bvr.write(f"      PIN_NAME {pin_num}\n")
            bvr.write(f"      PIN_SIDE {side}\n")
            bvr.write(f"      PIN_ORIGIN {x} {y}\n")
            bvr.write(f"      PIN_RADIUS {radius}\n")
            bvr.write(f"      PIN_NET {net}\n")
            bvr.write("      PIN_TYPE 2\n")
            bvr.write("      PIN_COMMENT\n")
            bvr.write("   PIN_END\n")
            bvr.write("\n")

        bvr.write("PART_END\n")
        bvr.write("\n")

        first_point = outline_points[0]
        outline_pts = ""

    for point in outline_points:
        x = coord(point.x)
        y = y_coord(outline_maxy, point.y, False)
        outline_pts += (f"{x} {y} ")

    x = coord(first_point.x)
    y = y_coord(outline_maxy, first_point.y, False)
    outline_pts += (f"{x} {y}")

    bvr.write("OUTLINE_POINTS ")
    bvr.write(outline_pts)


def convert_obdata(pcb, obdata, comps_hash):
    obdata.write("COMPONENTS_DATA_START\n")
    obdata.write("### Component Category Value Comment\n")
    obdata.write("### v = value, p = package, c = manufacturer code, r = rating, m = misc, s = status\n")
    obdata.write("###\n")

    for module in GS.get_modules():
        ref = GS.fp_get_reference(module)
        package = GS.fp_get_lib_and_name(module)
        value = GS.fp_get_value(module)

        package = re.sub(r'^.*:', '', package)

        obdata.write(f"{ref} p {package}\n")
        if comps_hash and ref in comps_hash:
            c = comps_hash[ref]
            if not c.fitted or not c.included:
                obdata.write(f"{ref} s -\n")
            if GS.global_field_part_number:
                for pn in GS.global_field_part_number:
                    mpn = c.get_field_value(pn)
                    if mpn:
                        obdata.write(f"{ref} c {mpn}\n")
        elif GS.ki8 and module.IsDNP():
            obdata.write(f"{ref} s -\n")
        obdata.write(f"{ref} v {value}\n")

    obdata.write("COMPONENTS_DATA_END\n")
    obdata.write("### END")


class BoardViewOptions(VariantOptions):
    def __init__(self):
        with document:
            self.output = GS.def_global_output
            """ *Filename for the output (%i=boardview, %x=brd/brv) """
            self.sorted = True
            """ Sort components by reference. Disable this option to get a file closer to what
                kicad-boardview generates """
            self.format = 'BRD'
            """ [BRD,BVR,OBDATA] Format used for the generated file. The BVR file format is bigger but keeps
                more information, like alphanumeric pin names.
                OBDATA is the OpenBoardData format. You can include the manufacturer part number defining the global
                `field_part_number` variable. Excluded and not fitted components are marked with `-` status """
        super().__init__()
        self._expand_id = 'boardview'
        self._expand_ext = 'brd'
        self.help_only_sub_pcbs()
        self.get_targets = self._get_targets

    def config(self, parent):
        super().config(parent)
        self._expand_ext = self.format.lower()

    def run(self, output):
        super().run(output)
        self.filter_pcb_components()
        with open(output, 'wt') as f:
            if self.format == 'BRD':
                convert_brd(GS.board, f, self.sorted)
            elif self.format == 'OBDATA':
                # We can include the manufacturer part number
                # For this we need the components hash
                if not self._comps:
                    # No variant or filter, get the values
                    self._comps = get_all_components()
                    refs_hash = self.get_refs_hash()
                    self._comps = None
                else:
                    refs_hash = self.get_refs_hash()
                convert_obdata(GS.board, f, refs_hash)
            else:
                convert_bvr(GS.board, f)
        self.unfilter_pcb_components()


@output_class
class BoardView(BaseOutput):  # noqa: F821
    """ BoardView
        Exports the PCB in board view format.
        This format allows simple pads and connections navigation, mainly for circuit debug.
        The output can be loaded using Open Board View (https://openboardview.org/) """
    def __init__(self):
        super().__init__()
        self._category = ['PCB/repair', 'PCB/fabrication/assembly']
        with document:
            self.options = BoardViewOptions
            """ *[dict={}] Options for the `boardview` output """

    @staticmethod
    def get_conf_examples(name, layers):
        return BaseOutput.simple_conf_examples(name, 'Board View export', 'Assembly')  # noqa: F821
