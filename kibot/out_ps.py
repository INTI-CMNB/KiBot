# -*- coding: utf-8 -*-
# Copyright (c) 2020-2026 Salvador E. Tropea
# Copyright (c) 2020-2026 Instituto Nacional de Tecnología Industrial
# Copyright (c) 2018 John Beard
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)
# Adapted from: https://github.com/johnbeard/kiplot
from .out_any_layer import AnyLayer
from .drill_marks import DrillMarks
from .misc import FONT_HELP_TEXT
from .gs import GS
from .macros import macros, document, output_class  # noqa: F401


class PSOptions(DrillMarks):
    def __init__(self):
        super().__init__()
        with document:
            self.line_width = 0.15
            """ [0.02,2] For objects without width [mm] (KiCad 5) """
            self.mirror_plot = False
            """ Plot mirrored """
            self.negative_plot = False
            """ Invert black and white """
            self.sketch_plot = False
            """ Don't fill objects, just draw the outline (KiCad older than 10) """
            self.scale_adjust_x = 1.0
            """ Fine grain adjust for the X scale (floating point multiplier) """
            self.scale_adjust_y = 1.0
            """ Fine grain adjust for the Y scale (floating point multiplier) """
            self.width_adjust = 0
            """ This width factor is intended to compensate PS printers/plotters that do not strictly obey line width settings.
                Only used to plot pads and tracks """
            self.a4_output = True
            """ Force A4 paper size """
        self._plot_format = GS.PLOT_FORMAT_POST

    def _configure_plot_ctrl(self, po, output_dir):
        super()._configure_plot_ctrl(po, output_dir)
        po.SetWidthAdjust(self.width_adjust)
        po.SetFineScaleAdjustX(self.scale_adjust_x)
        po.SetFineScaleAdjustX(self.scale_adjust_y)
        po.SetA4Output(self.a4_output)
        if not GS.ki10:
            po.SetPlotMode(GS.pn.SKETCH if self.sketch_plot else GS.pn.FILLED)
        po.SetNegative(self.negative_plot)
        po.SetMirror(self.mirror_plot)

    def read_vals_from_po(self, po):
        super().read_vals_from_po(po)
        self.width_adjust = po.GetWidthAdjust()
        self.scale_adjust_x = po.GetFineScaleAdjustX()
        self.scale_adjust_y = po.GetFineScaleAdjustX()
        self.a4_output = po.GetA4Output()
        if not GS.ki10:
            self.sketch_plot = po.GetPlotMode() == GS.pn.SKETCH
        self.negative_plot = po.GetNegative()
        self.mirror_plot = po.GetMirror()


@output_class
class PS(AnyLayer):
    """ PS (Postscript)
        Exports the PCB to a format suitable for printing.
        This output is what you get from the File/Plot menu in pcbnew.
        The `pcb_print` is usually a better alternative. """
    __doc__ += FONT_HELP_TEXT

    def __init__(self):
        super().__init__()
        with document:
            self.options = PSOptions
            """ *[dict={}] Options for the `ps` output """
        self._category = 'PCB/docs'
