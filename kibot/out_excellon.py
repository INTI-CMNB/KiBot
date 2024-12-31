# -*- coding: utf-8 -*-
# Copyright (c) 2020-2023 Salvador E. Tropea
# Copyright (c) 2020-2023 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
from pcbnew import EXCELLON_WRITER
from .out_any_drill import AnyDrill
from .gs import GS
from .macros import macros, document, output_class  # noqa: F401

ZF = {'DECIMAL_FORMAT': EXCELLON_WRITER.DECIMAL_FORMAT,
      'SUPPRESS_LEADING': EXCELLON_WRITER.SUPPRESS_LEADING,
      'SUPPRESS_TRAILING': EXCELLON_WRITER.SUPPRESS_TRAILING,
      'KEEP_ZEROS': EXCELLON_WRITER.KEEP_ZEROS}


class ExcellonOptions(AnyDrill):
    def __init__(self):
        super().__init__()
        with document:
            self.metric_units = True
            """ *Use metric units instead of inches """
            self.pth_and_npth_single_file = True
            """ *Generate one file for both, plated holes and non-plated holes, instead of two separated files """
            self.minimal_header = False
            """ Use a minimal header in the file """
            self.mirror_y_axis = False
            """ *Invert the Y axis """
            self.zeros_format = 'DECIMAL_FORMAT'
            """ [DECIMAL_FORMAT,SUPPRESS_LEADING,SUPPRESS_TRAILING,KEEP_ZEROS] How to handle the zeros """
            self.left_digits = 0
            """ number of digits for integer part of coordinates (0 is auto) """
            self.right_digits = 0
            """ number of digits for mantissa part of coordinates (0 is auto) """
            self.route_mode_for_oval_holes = True
            """ Use route command for oval holes (G00), otherwise use G85 """
        self._ext = 'drl'

    def _configure_writer(self, board, offset):
        drill_writer = EXCELLON_WRITER(board)
        drill_writer.SetOptions(self.mirror_y_axis, self.minimal_header, GS.p2v_k7(offset), self.pth_and_npth_single_file)
        drill_writer.SetRouteModeForOvalHoles(self.route_mode_for_oval_holes)
        drill_writer.SetFormat(self.metric_units, ZF[self.zeros_format], self.left_digits, self.right_digits)
        self._unified_output = self.pth_and_npth_single_file
        return drill_writer


@output_class
class Excellon(BaseOutput):  # noqa: F821
    """ Excellon drill format
        This is the main format for the drilling machine.
        You can create a map file for documentation purposes.
        This output is what you get from the 'File/Fabrication output/Drill Files' menu in pcbnew. """
    def __init__(self):
        super().__init__()
        self._category = 'PCB/fabrication/drill'
        with document:
            self.options = ExcellonOptions
            """ *[dict={}] Options for the `excellon` output """

    def get_csv_separator(self):
        return ','

    @staticmethod
    def get_conf_examples(name, layers):
        gb = {}
        outs = [gb]
        name_u = name.upper()
        gb['name'] = 'basic_'+name
        gb['comment'] = 'Drill files in '+name_u+' format'
        gb['type'] = name
        gb['dir'] = 'Gerbers_and_Drill'
        gb['options'] = {'map': 'pdf'}
        return outs
