# -*- coding: utf-8 -*-
# Copyright (c) 2020-2025 Salvador E. Tropea
# Copyright (c) 2020-2025 Instituto Nacional de Tecnología Industrial
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)
from pcbnew import PLOT_FORMAT_DXF, SKETCH, FILLED
from .out_any_layer import AnyLayer
from .drill_marks import DrillMarks
from .gs import GS
from .misc import FONT_HELP_TEXT
from .macros import macros, document, output_class  # noqa: F401
if GS.ki6:
    try:
        from pcbnew import DXF_UNITS_MILLIMETERS, DXF_UNITS_INCHES
    except ImportError:
        # KiCad 9.0.1 release ... really?!
        # Using the constant is more problematic than just using hardcoded values, ridiculous
        from pcbnew import DXF_UNITS_MM, DXF_UNITS_INCH
        DXF_UNITS_MILLIMETERS = DXF_UNITS_MM
        DXF_UNITS_INCHES = DXF_UNITS_INCH
else:
    DXF_UNITS_MILLIMETERS = 1
    DXF_UNITS_INCHES = 0


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
        self._plot_format = PLOT_FORMAT_DXF

    def _configure_plot_ctrl(self, po, output_dir):
        super()._configure_plot_ctrl(po, output_dir)
        po.SetDXFPlotPolygonMode(self.polygon_mode)
        # DXF_PLOTTER::DXF_UNITS isn't available
        # According to https://docs.kicad.org/doxygen/classDXF__PLOTTER.html 1 is mm
        po.SetDXFPlotUnits(DXF_UNITS_MILLIMETERS if self.metric_units else DXF_UNITS_INCHES)
        if GS.ki10:
            po.SetDXFPlotMode(SKETCH if self.sketch_plot else FILLED)
        else:
            po.SetPlotMode(SKETCH if self.sketch_plot else FILLED)
        po.SetUseAuxOrigin(self.use_aux_axis_as_origin)

    def read_vals_from_po(self, po):
        super().read_vals_from_po(po)
        self.polygon_mode = po.GetDXFPlotPolygonMode()
        self.metric_units = po.GetDXFPlotUnits() == 1
        self.sketch_plot = po.GetPlotMode() == SKETCH
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
