# -*- coding: utf-8 -*-
# Copyright (c) 2020-2026 Salvador E. Tropea
# Copyright (c) 2020-2026 Instituto Nacional de Tecnología Industrial
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)
from .error import KiPlotConfigurationError
from .out_any_drill import AnyDrill
from .gs import GS
from .macros import macros, document, output_class  # noqa: F401
from . import log

logger = log.get_logger()

ZF = {'DECIMAL_FORMAT': GS.DZF_DECIMAL,
      'SUPPRESS_LEADING': GS.DZF_SUPPRESS_LEADING,
      'SUPPRESS_TRAILING': GS.DZF_SUPPRESS_TRAILING,
      'KEEP_ZEROS': GS.DZF_KEEP_ZEROS}
ZF_CLI = {'DECIMAL_FORMAT': 'decimal',
          'SUPPRESS_LEADING': 'suppressleading',
          'SUPPRESS_TRAILING': 'suppresstrailing',
          'KEEP_ZEROS': 'keep'}


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
            """ number of digits for integer part of coordinates (0 is auto).
                Doesn't apply to DECIMAL_FORMAT.
                Default is 3 and currently can't be configured from the GUI, avoid using it.
                Not supported on KiCad 11+ """
            self.right_digits = 0
            """ number of digits for mantissa part of coordinates (0 is auto).
                Doesn't apply to DECIMAL_FORMAT.
                Default is 3 and currently can't be configured from the GUI, avoid using it.
                Not supported on KiCad 11+ """
            self.route_mode_for_oval_holes = True
            """ Use route command for oval holes (G00), otherwise use G85 """
        self._ext = 'drl'

    def is_default_digits(self):
        return ((self.left_digits == 0 and self.right_digits == 0) or  # Using default
                (self.left_digits == 3 and self.right_digits == 3) or  # User matched the default
                self.zeros_format == 'DECIMAL_FORMAT')                 # Using decimal point

    def _configure_writer(self, board):
        self._unified_output = self.pth_and_npth_single_file
        if GS.ki11:
            return None, False
        if GS.ki10 and self.is_default_digits():
            options = ['--format', 'excellon',
                       '--excellon-units', 'mm' if self.metric_units else 'in',
                       '--excellon-zeros-format', ZF_CLI[self.zeros_format],
                       '--excellon-oval-format', 'route' if self.route_mode_for_oval_holes else 'alternate',
                       '--drill-origin', 'plot' if self.use_aux_axis_as_origin else 'absolute']
            if not self.pth_and_npth_single_file:
                options.append('--excellon-separate-th')
            if self.minimal_header:
                options.append('--excellon-min-header')
            if self.mirror_y_axis:
                options.append('--excellon-mirror-y')
            return options, True
        # KiCad <10 or left_digits/right_digits
        drill_writer = GS.pn.EXCELLON_WRITER(board)
        offset = GS.get_aux_origin() if self.use_aux_axis_as_origin else GS.get_absolute_origin()
        drill_writer.SetOptions(self.mirror_y_axis, self.minimal_header, GS.p2v_k7(offset), self.pth_and_npth_single_file)
        drill_writer.SetRouteModeForOvalHoles(self.route_mode_for_oval_holes)
        drill_writer.SetFormat(self.metric_units, ZF[self.zeros_format], self.left_digits, self.right_digits)
        return drill_writer, False

    def run_with_kipy(self, output_dir, gen_map):
        if not self.is_default_digits():
            raise KiPlotConfigurationError("left/right digits not supported")
        # Origin
        dot = GS.kp.proto.board.board_jobs_pb2.DrillOrigin
        origin = dot.DO_PLOT if self.use_aux_axis_as_origin else dot.DO_ABSOLUTE
        # Map file
        map_format = GS.PLOT_FMT_TO_DMF[self._map_type if gen_map else '']
        # Report
        if self._report:
            drill_report_file = self.expand_filename(output_dir, self._report, 'drill_report', 'txt')
            logger.debug("Generating drill report: "+drill_report_file)
        else:
            drill_report_file = ''
        # Units
        utp = GS.kp.proto.common.types.enums_pb2.Units
        units = utp.U_MM if self.metric_units else utp.U_INCH
        # Zeros format
        res = GS.board.export_drill_excellon(
            output_dir,
            origin=origin,
            map_format=map_format,
            report_filename=drill_report_file,
            units=units,
            zeros_format=ZF[self.zeros_format],
            route_oval_holes=self.route_mode_for_oval_holes,
            combine_pth_npth=self.pth_and_npth_single_file,
            minimal_header=self.minimal_header,
            mirror_y=self.mirror_y_axis)
        self.check_job_ok(res)
        return None


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
