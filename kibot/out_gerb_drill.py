# -*- coding: utf-8 -*-
# Copyright (c) 2020-2026 Salvador E. Tropea
# Copyright (c) 2020-2026 Instituto Nacional de Tecnología Industrial
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)
from .gs import GS
from .out_any_drill import AnyDrill
from .macros import macros, document, output_class  # noqa: F401
from . import log

logger = log.get_logger()


class Gerb_DrillOptions(AnyDrill):
    def __init__(self):
        super().__init__()
        with document:
            self.precision = 6
            """ [5,6] Decimals used for coordinates """
            self.generate_tenting = False
            """ Generate tenting information. KiCad 10+
                Important: The names of the tenting file can't be controlled """
            # The names are hard to figure out, because the tenting can be controlled by design rules
            # The KiPy API is currently failing to report the generated files
        self._ext = 'gbr'

    def _configure_writer(self, board):
        if GS.ki11:
            return None, False
        if GS.ki10:
            options = ['--format', 'gerber',
                       '--drill-origin', 'plot' if self.use_aux_axis_as_origin else 'absolute',
                       '--gerber-precision', str(self.precision)]
            if self.generate_tenting:
                options.append('--generate-tenting')
            return options, True
        drill_writer = GS.pn.GERBER_WRITER(board)
        drill_writer.SetFormat(self.precision)
        drill_writer.SetOptions(GS.p2v_k7(GS.get_aux_origin() if self.use_aux_axis_as_origin else GS.get_absolute_origin()))
        return drill_writer, False

    def run_with_kipy(self, output_dir, gen_map):
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
        res = GS.board.export_drill_gerber(
            output_dir,
            origin=origin,
            map_format=map_format,
            report_filename=drill_report_file,
            precision=GS.DGP_4_5 if self.precision == 5 else GS.DGP_4_6,
            generate_tenting=self.generate_tenting)
        self.check_job_ok(res)
        return None


@output_class
class Gerb_Drill(BaseOutput):  # noqa: F821
    """ Gerber drill format
        This is the information for the drilling machine in gerber format.
        You can create a map file for documentation purposes.
        This output is what you get from the 'File/Fabrication output/Drill Files' menu in pcbnew. """
    def __init__(self):
        super().__init__()
        self._category = 'PCB/fabrication/drill'
        with document:
            self.options = Gerb_DrillOptions
            """ *[dict={}] Options for the `gerb_drill` output """

    @staticmethod
    def get_conf_examples(name, layers):
        gb = {}
        outs = [gb]
        name_u = name.upper()
        gb['name'] = 'basic_'+name
        gb['comment'] = 'Drill files in '+name_u+' format'
        gb['type'] = name
        gb['dir'] = 'Gerbers_and_Drill'
        gb['options'] = {'map': 'gerber'}
        return outs
