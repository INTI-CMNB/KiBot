# -*- coding: utf-8 -*-
# Copyright (c) 2020-2023 Salvador E. Tropea
# Copyright (c) 2020-2023 Instituto Nacional de Tecnología Industrial
# Copyright (c) 2018 John Beard
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
# Adapted from: https://github.com/johnbeard/kiplot
from pcbnew import (PLOT_FORMAT_PDF, FromMM, ToMM)
from .out_any_layer import AnyLayer
from .drill_marks import DrillMarks
from .gs import GS
from .misc import FONT_HELP_TEXT
from .macros import macros, document, output_class  # noqa: F401
from . import log

logger = log.get_logger()


class PDFOptions(DrillMarks):
    def __init__(self):
        super().__init__()
        with document:
            self.line_width = 0.1
            """ [0.02,2] For objects without width [mm] (KiCad 5) """
            self.mirror_plot = False
            """ Plot mirrored """
            self.negative_plot = False
            """ Invert black and white """
        self._plot_format = PLOT_FORMAT_PDF

    def _configure_plot_ctrl(self, po, output_dir):
        super()._configure_plot_ctrl(po, output_dir)
        po.SetMirror(self.mirror_plot)
        if GS.ki5:
            po.SetLineWidth(FromMM(self.line_width))
        po.SetNegative(self.negative_plot)

    def read_vals_from_po(self, po):
        super().read_vals_from_po(po)
        self.mirror_plot = po.GetMirror()
        if GS.ki5:
            self.line_width = ToMM(po.GetLineWidth())
        self.negative_plot = po.GetNegative()


@output_class
class PDF(AnyLayer, DrillMarks):
    """ PDF (Portable Document Format)
        Exports the PCB to the most common exchange format. Suitable for printing.
        Note that this output isn't the best for documating your project.
        This output is what you get from the File/Plot menu in pcbnew.
        The `pcb_print` is usually a better alternative. """
    __doc__ += FONT_HELP_TEXT

    def __init__(self):
        super().__init__()
        with document:
            self.options = PDFOptions
            """ *[dict={}] Options for the `pdf` output """
        self._category = 'PCB/docs'
