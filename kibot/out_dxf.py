# -*- coding: utf-8 -*-
# Copyright (c) 2020-2026 Salvador E. Tropea
# Copyright (c) 2020-2026 Instituto Nacional de Tecnología Industrial
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)
from .out_any_layer import AnyLayer
from .drill_marks import DrillMarks
from .gs import GS
from .misc import FONT_HELP_TEXT
from .macros import macros, document, output_class  # noqa: F401


class DXFOptions(DrillMarks):
    def __init__(self):
        super().__init__()
        with document:
            self.use_aux_axis_as_origin = False
            """ Use the auxiliary axis as origin for coordinates """
            self.polygon_mode = True
            """ Plot using the contour, instead of the center line.
                You must disable it to get the dimensions (See https://gitlab.com/kicad/code/kicad/-/issues/11901) """
            self.metric_units = False
            """ Use mm instead of inches """
            self.sketch_plot = False
            """ Don't fill objects, just draw the outline """
        self._plot_format = GS.PLOT_FORMAT_DXF

    def _configure_plot_ctrl(self, po, output_dir):
        super()._configure_plot_ctrl(po, output_dir)
        po.SetDXFPlotPolygonMode(self.polygon_mode)
        po.SetDXFPlotUnits(GS.DXF_UNITS_MILLIMETERS if self.metric_units else GS.DXF_UNITS_INCHES)
        if GS.ki10:
            po.SetDXFPlotMode(GS.pn.SKETCH if self.sketch_plot else GS.pn.FILLED)
        else:
            po.SetPlotMode(GS.pn.SKETCH if self.sketch_plot else GS.pn.FILLED)
        po.SetUseAuxOrigin(self.use_aux_axis_as_origin)

    def read_vals_from_po(self, po):
        super().read_vals_from_po(po)
        self.polygon_mode = po.GetDXFPlotPolygonMode()
        self.metric_units = po.GetDXFPlotUnits() == 1
        plot_mode = po.GetDXFPlotMode() if GS.ki10 else po.GetPlotMode()
        self.sketch_plot = plot_mode == GS.pn.SKETCH
        self.use_aux_axis_as_origin = po.GetUseAuxOrigin()


@output_class
class DXF(AnyLayer):
    """ DXF (Drawing Exchange Format)
        Exports the PCB to 2D mechanical EDA tools (like AutoCAD).
        This output is what you get from the File/Plot menu in pcbnew. """
    __doc__ += FONT_HELP_TEXT

    def __init__(self):
        super().__init__()
        self._category = 'PCB/export'
        with document:
            self.options = DXFOptions
            """ *[dict={}] Options for the `dxf` output """
