# -*- coding: utf-8 -*-
# Copyright (c) 2026 Salvador E. Tropea
# Copyright (c) 2026 Instituto Nacional de Tecnología Industrial
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)
#
# Implementation of the KiCad low level interface for PcbDraw
# - Using SWIG API (pcbnew.py) for KiCad 6 to 10
#
from dataclasses import dataclass, field
from enum import Enum
import tempfile
from typing import Mapping, Tuple
from ..gs import GS
from ..layer import Layer
from .. import log

logger = log.get_logger()
assert GS.pn is not None or GS.kp is not None


@dataclass(frozen=True)
class Point:
    x: float
    y: float


@dataclass(frozen=True)
class Size:
    width: float
    height: float


@dataclass(frozen=True)
class Bounds:
    x: float
    y: float
    width: float
    height: float


class BoardSide(Enum):
    FRONT = "front"
    BACK = "back"


@dataclass(frozen=True)
class Component:
    library: str
    footprint: str
    reference: str
    value: str
    position: Point
    rotation_degrees: float
    side: BoardSide
    properties: Mapping[str, str] = field(default_factory=dict)    # Fields excluding "reference", "value", "footprint"

    def __str__(self):
        return f"{self.reference} {self.value} [{self.library}:{self.footprint}] @ {self.position} on {self.side}"


@dataclass(frozen=True)
class DrillHole:
    position: Point
    orientation_degrees: float
    size: Size


@dataclass(frozen=True)
class BoardData:
    components: Tuple[Component, ...]
    holes: Tuple[DrillHole, ...]
    bounds: Bounds


def load_board_data_pn(board, internal_to_svg, exclude_width) -> BoardData:
    """ Compute the PCB boundaries and collect PCB components and holes.
        All coordinates/sizes are in SVG units.
        KiCad 6: depends on the SVG precision
        KiCad 7+: just mm """
    # Board bounds, only the edge, this isn't the full drawing size
    x1, y1, x2, y2 = GS.compute_pcb_boundary(board, not exclude_width)
    # If the board doesn't have a contour just use the A4 landscape size. Better than 0x0
    if x2-x1 == 0:
        x1 = 0
        x2 = GS.from_mm(297)
    if y2-y1 == 0:
        y1 = 0
        y2 = GS.from_mm(210)
    bounds = Bounds(internal_to_svg(x1), internal_to_svg(y1), internal_to_svg(x2-x1), internal_to_svg(y2-y1))

    # Components and Holes
    components = []
    holes = []
    for m in GS.get_modules_board(board):
        # Component
        # Side
        layer = m.GetLayer()
        if layer == GS.F_Cu:
            side = BoardSide.FRONT
        elif layer == GS.B_Cu:
            side = BoardSide.BACK
        else:
            assert False
        # lib+name
        fpid = m.GetFPID()
        library = str(fpid.GetLibNickname()).strip()
        footprint = str(fpid.GetLibItemName()).strip()
        # Properties
        reference = GS.fp_get_reference(m).strip()
        value = GS.fp_get_value(m).strip()
        properties = GS.get_fields(m)
        # Position
        pos = m.GetPosition()
        position = Point(internal_to_svg(pos.x), internal_to_svg(pos.y))
        rotation_degrees = GS.get_footprint_orientation_in_degrees(m)
        components.append(Component(library=library, footprint=footprint, reference=reference, value=value,
                                    position=position, rotation_degrees=rotation_degrees, side=side,
                                    properties=properties))

        # Holes
        if m.GetPadCount() == 0:
            continue
        for pad in GS.fp_get_pads(m):
            drs = pad.GetDrillSize()
            if drs.x == 0 or drs.y == 0:
                continue
            pos = pad.GetPosition()
            holes.append(DrillHole(position=Point(internal_to_svg(pos[0]), internal_to_svg(pos[1])),
                                   orientation_degrees=GS.get_pad_orientation_in_degrees(pad),
                                   size=Size(internal_to_svg(drs.x), internal_to_svg(drs.y))))

    # Holes from vias
    for track in board.GetTracks():
        if track.GetClass() != 'PCB_VIA':
            continue
        pos = track.GetPosition()
        sz = internal_to_svg(track.GetDrillValue())
        holes.append(DrillHole(position=Point(internal_to_svg(pos[0]), internal_to_svg(pos[1])),
                               orientation_degrees=0.0,
                               size=Size(sz, sz)))

    return BoardData(components, holes, bounds)


def load_board_data_kp(board, internal_to_svg, exclude_width) -> BoardData:
    """ Compute the PCB boundaries and collect PCB components and holes.
        All coordinates/sizes are in SVG units.
        KiCad 6: depends on the SVG precision
        KiCad 7+: just mm """
    # Board bounds, only the edge, this isn't the full drawing size
    x1, y1, x2, y2 = GS.compute_pcb_boundary(board, not exclude_width)
    # If the board doesn't have a contour just use the A4 landscape size. Better than 0x0
    if x2-x1 == 0:
        x1 = 0
        x2 = GS.from_mm(297)
    if y2-y1 == 0:
        y1 = 0
        y2 = GS.from_mm(210)
    bounds = Bounds(internal_to_svg(x1), internal_to_svg(y1), internal_to_svg(x2-x1), internal_to_svg(y2-y1))

    # Components and Holes
    components = []
    holes = []
    for m in GS.get_modules_board(board):
        # Component
        # Side
        if m.layer == GS.F_Cu:
            side = BoardSide.FRONT
        elif m.layer == GS.B_Cu:
            side = BoardSide.BACK
        else:
            assert False
        # lib+name
        library = m.definition.id.library
        footprint = m.definition.id.name
        # Properties
        reference = None
        value = None
        properties = {}
        for p in m.texts_and_fields:
            if not isinstance(p, GS.kp.board_types.Field):
               continue
            if p.name == 'Reference':
               reference = p.text.value
            elif p.name == 'Value':
               value = p.text.value
            else:
               properties[p.name] = p.text.value
        # Position
        position = Point(internal_to_svg(m.position.x), internal_to_svg(m.position.y))
        rotation_degrees = GS.get_footprint_orientation_in_degrees(m)
        components.append(Component(library=library, footprint=footprint, reference=reference, value=value,
                                    position=position, rotation_degrees=rotation_degrees, side=side,
                                    properties=properties))

        # Holes
        pads = m.definition.pads
        if len(pads) == 0:
            continue
        for pad in pads:
            diameter = pad.padstack.drill.diameter
            if diameter.x == 0 or diameter.y == 0:
                continue
            holes.append(DrillHole(position=Point(internal_to_svg(pad.position.x), internal_to_svg(pad.position.y)),
                                   orientation_degrees=GS.get_pad_orientation_in_degrees(pad),
                                   size=Size(internal_to_svg(diameter.x), internal_to_svg(diameter.y))))

    # Holes from vias
    for v in board.get_items(GS.kp.proto.common.types.KiCadObjectType.KOT_PCB_VIA):
        if v.type != GS.kp.proto.board.board_types_pb2.ViaType.VT_THROUGH:
            continue
        sz = internal_to_svg(v.drill_diameter)
        holes.append(DrillHole(position=Point(internal_to_svg(v.position.x), internal_to_svg(v.position.y)),
                               orientation_degrees=0.0,
                               size=Size(sz, sz)))

    return BoardData(components, holes, bounds)


def export_pcb_svg_layers_pn(board, layers, svg_precision):
    pcbnew = GS.pn
    result = {}
    with tempfile.TemporaryDirectory() as tmp:
        pctl = pcbnew.PLOT_CONTROLLER(board)
        popt = pctl.GetPlotOptions()
        popt.SetOutputDirectory(tmp)
        popt.SetScale(1)
        popt.SetMirror(False)
        popt.SetSubtractMaskFromSilk(True)
        popt.SetDrillMarksType(0)  # NO_DRILL_SHAPE
        popt.SetTextMode(pcbnew.PLOT_TEXT_MODE_STROKE)
        if GS.ki7:
            popt.SetSvgPrecision(svg_precision)
        else:  # KiCad 6
            popt.SetSvgPrecision(svg_precision, False)
        for layer in set(layers):
            logger.debug(f"Plotting layer {Layer.id2def_name(layer)}")
            pctl.SetLayer(layer)
            pctl.OpenPlotfile('pcbdraw', pcbnew.PLOT_FORMAT_SVG, 'pcbdraw')
            pctl.SetColorMode(False)
            pctl.PlotLayer()
            pctl.ClosePlot()
            with open(pctl.GetPlotFileName(), 'rb') as f:
                result[layer] = f.read()
    return result


def export_pcb_svg_layers_kp(board, layers, svg_precision):
    page_mode = GS.kp.proto.board.board_jobs_pb2.BoardJobPaginationMode.BJPM_EACH_LAYER_OWN_FILE
    plot = GS.kp.board_jobs.PlotSettings()
    plot.mirror = False
    plot.negative = False
    plot.scale = 1
    plot.black_and_white = True
    plot.use_drill_origin = False
    plot.subtract_solder_mask_from_silk = True
    plot.drill_marks = GS.NO_DRILL_SHAPE
    plot.plot_reference_designators = True
    plot.plot_footprint_values = True

    result = {}
    with tempfile.TemporaryDirectory() as tmp:
        unique_layers = list(set(layers))
        logger.debug(f"Plotting layers: {unique_layers}")
        plot.layers = unique_layers
        res = board.export_svg(tmp,
                               plot_settings=plot,
                               precision=svg_precision,
                               fit_page_to_board=False,
                               page_mode=page_mode)
        if not res.succeeded:
            raise RuntimeError(f"Failed to plot layers: {res.message}")
        for layer, file_name in zip(unique_layers, res.output_paths):
            with open(file_name, 'rb') as f:
                result[layer] = f.read()

    return result


load_board_data = load_board_data_pn if GS.pn is not None else load_board_data_kp
export_pcb_svg_layers = export_pcb_svg_layers_pn if GS.pn is not None else export_pcb_svg_layers_kp
