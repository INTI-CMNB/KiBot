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
            self.mirror_plot = False
            """ Plot mirrored """
            self.negative_plot = False
            """ Invert black and white """
            self.sketch_plot = False
            """ Don't fill objects, just draw the outline (KiCad older than 10) """
            self.scaling = 1
            """ *Scale factor (0 means autoscaling) """
            self.individual_page_scaling = True
            """ Tell KiCad to apply the scaling for each layer as a separated entity.
                Disabling it the pages are coherent and can be superposed (KiCad <11) """
            self.scale_adjust_x = 1.0
            """ Fine grain adjust for the X scale (floating point multiplier) """
            self.scale_adjust_y = 1.0
            """ Fine grain adjust for the Y scale (floating point multiplier) """
            self.width_adjust = 0
            """ This width factor is intended to compensate PS printers/plotters that do not strictly obey line width settings.
                Only used to plot pads and tracks """
            self.a4_output = True
            """ Force A4 paper size """
            self.single_file = False
            """ Plot all the pages to a single file, in a single page (KiCad 11+) """
            self.monochrome = True
            """ Black and white output (KiCad 11+) """
            self.color_theme = '_builtin_classic'
            """ Selects the color theme (KiCad 11+) """
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

    def read_vals_from_po(self):
        po = super().read_vals_from_po()
        if GS.pn is not None:
            self.width_adjust = po.GetWidthAdjust()
            self.scale_adjust_x = po.GetFineScaleAdjustX()
            self.scale_adjust_y = po.GetFineScaleAdjustX()
            self.a4_output = po.GetA4Output()
            if not GS.ki10:
                self.sketch_plot = po.GetPlotMode() == GS.pn.SKETCH
            self.negative_plot = po.GetNegative()
            self.mirror_plot = po.GetMirror()
        else:
            self.mirror_plot = po.mirror
            self.negative_plot = po.negative
            self.scaling = po.scale
            self.monochrome = po.black_and_white
            self.color_theme = po.color_theme
            # TODO: The rest are missing
        return po

    # #########################################################################
    # KiPy implementation
    # #########################################################################

    def _configure_plot_settings(self, plot, layers):
        """ KiPy plot settings specific for gerbers """
        super()._configure_plot_settings(plot, layers)
        plot.mirror = self.mirror_plot
        plot.negative = self.negative_plot
        plot.scale = self.scaling
        plot.black_and_white = self.monochrome
        plot.color_theme = self.color_theme

    def _run_export_job(self, destination, plot):
        if self.single_file:
            page_mode = GS.kp.proto.board.board_jobs_pb2.BoardJobPaginationMode.BJPM_ALL_LAYERS_ONE_PAGE
        else:  # multiple files
            page_mode = GS.kp.proto.board.board_jobs_pb2.BoardJobPaginationMode.BJPM_EACH_LAYER_OWN_FILE
        res = GS.board.export_ps(destination,
                                 plot_settings=plot,
                                 use_global_settings=False,
                                 track_width_correction=self.width_adjust,
                                 x_scale_adjust=self.scale_adjust_x,
                                 y_scale_adjust=self.scale_adjust_y,
                                 force_a4=self.a4_output,
                                 page_mode=page_mode)
        self.check_job_ok(res)


@output_class
class PS(AnyLayer):
    """ PS (Postscript)
        Exports the PCB to a format suitable for printing.
        This output is what you get from the File/Plot menu in pcbnew.
        The `pcb_print` is usually a better alternative.
        Affected by https://gitlab.com/kicad/code/kicad/-/work_items/23275 """
    __doc__ += FONT_HELP_TEXT

    def __init__(self):
        super().__init__()
        with document:
            self.options = PSOptions
            """ *[dict={}] Options for the `ps` output """
        self._category = 'PCB/docs'
