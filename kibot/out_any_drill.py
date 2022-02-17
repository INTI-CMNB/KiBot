# -*- coding: utf-8 -*-
# Copyright (c) 2020-2021 Salvador E. Tropea
# Copyright (c) 2020-2021 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
import os
from pcbnew import (PLOT_FORMAT_HPGL, PLOT_FORMAT_POST, PLOT_FORMAT_GERBER, PLOT_FORMAT_DXF, PLOT_FORMAT_SVG,
                    PLOT_FORMAT_PDF, wxPoint)
from .optionable import (Optionable, BaseOptions)
from .gs import GS
from .macros import macros, document  # noqa: F401
from . import log

logger = log.get_logger()


class DrillMap(Optionable):
    def __init__(self):
        with document:
            self.output = GS.def_global_output
            """ Name for the map file, KiCad defaults if empty (%i='PTH_drill_map') """
            self.type = 'pdf'
            """ [hpgl,ps,gerber,dxf,svg,pdf] Format for a graphical drill map """
        super().__init__()
        self._unknown_is_error = True


class DrillReport(Optionable):
    def __init__(self):
        super().__init__()
        with document:
            self.filename = ''
            """ Name of the drill report. Not generated unless a name is specified.
                (%i='drill_report' %x='txt') """
        self._unknown_is_error = True


class AnyDrill(BaseOptions):
    def __init__(self):
        # Options
        with document:
            self.use_aux_axis_as_origin = False
            """ Use the auxiliary axis as origin for coordinates """
            self.map = DrillMap
            """ [dict|string] [hpgl,ps,gerber,dxf,svg,pdf] Format for a graphical drill map.
                Not generated unless a format is specified """
            self.output = GS.def_global_output
            """ name for the drill file, KiCad defaults if empty (%i='PTH_drill') """
            self.report = DrillReport
            """ [dict|string] Name of the drill report. Not generated unless a name is specified """
            self.pth_id = None
            """ [string] Force this replacement for %i when generating PTH and unified files """
            self.npth_id = None
            """ [string] Force this replacement for %i when generating NPTH files """
        super().__init__()
        # Mappings to KiCad values
        self._map_map = {
                         'hpgl': PLOT_FORMAT_HPGL,
                         'ps': PLOT_FORMAT_POST,
                         'gerber': PLOT_FORMAT_GERBER,
                         'dxf': PLOT_FORMAT_DXF,
                         'svg': PLOT_FORMAT_SVG,
                         'pdf': PLOT_FORMAT_PDF
                        }
        self._map_ext = {'hpgl': 'plt', 'ps': 'ps', 'gerber': 'gbr', 'dxf': 'dxf', 'svg': 'svg', 'pdf': 'pdf'}
        self._unified_output = False

    def config(self, parent):
        super().config(parent)
        # Solve the map for both cases
        if isinstance(self.map, str):
            self.map_ext = self._map_ext[self.map]
            self.map_output = GS.global_output if GS.global_output is not None else GS.def_global_output
            self.map = self._map_map[self.map]
        elif isinstance(self.map, DrillMap):
            self.map_ext = self._map_ext[self.map.type]
            self.map_output = self.map.output
            self.map = self._map_map[self.map.type]
        else:
            self.map = None
        # Solve the report for both cases
        if isinstance(self.report, DrillReport):
            self.report = self.report.filename
        elif not isinstance(self.report, str):
            self.report = None
        self._expand_id = 'drill'
        self._expand_ext = self._ext

    def solve_id(self, d):
        if not d:
            # Unified
            return self.pth_id if self.pth_id is not None else 'drill'
        if d[0] == 'N':
            # NPTH
            return self.npth_id if self.npth_id is not None else d+'_drill'
        # PTH
        return self.pth_id if self.pth_id is not None else d+'_drill'

    def get_file_names(self, output_dir):
        """ Returns a dict containing KiCad names and its replacement.
            If no replacement is needed the replacement is empty """
        filenames = {}
        self._configure_writer(GS.board, wxPoint(0, 0))
        files = [''] if self._unified_output else ['PTH', 'NPTH']
        for d in files:
            kicad_id = '-'+d if d else d
            kibot_id = self.solve_id(d)
            if self._ext == 'gbr':
                kicad_id += '-drl'
            k_file = self.expand_filename(output_dir, '%f'+kicad_id+'.%x', '', self._ext)
            file = ''
            if self.output:
                file = self.expand_filename(output_dir, self.output, kibot_id, self._ext)
            filenames[k_file] = file
            if self.map is not None:
                k_file = self.expand_filename(output_dir, '%f'+kicad_id+'-drl_map.%x', '', self.map_ext)
                file = ''
                if self.map_output:
                    file = self.expand_filename(output_dir, self.map_output, kibot_id+'_map', self.map_ext)
                filenames[k_file] = file
        return filenames

    def run(self, output_dir):
        if self.output:
            output_dir = os.path.dirname(output_dir)
        # dialog_gendrill.cpp:357
        if self.use_aux_axis_as_origin:
            offset = GS.get_aux_origin()
        else:
            offset = wxPoint(0, 0)
        drill_writer = self._configure_writer(GS.board, offset)

        logger.debug("Generating drill files in "+output_dir)
        gen_map = self.map is not None
        if gen_map:
            drill_writer.SetMapFileFormat(self.map)
            logger.debug("Generating drill map type {} in {}".format(self.map, output_dir))
        # We always generate the drill file
        drill_writer.CreateDrillandMapFilesSet(output_dir, True, gen_map)
        # Rename the files
        files = self.get_file_names(output_dir)
        for k_f, f in files.items():
            if f:
                logger.debug("Renaming {} -> {}".format(k_f, f))
                os.rename(k_f, f)
        # Generate the report
        if self.report:
            drill_report_file = self.expand_filename(output_dir, self.report, 'drill_report', 'txt')
            logger.debug("Generating drill report: "+drill_report_file)
            drill_writer.GenDrillReportFile(drill_report_file)

    def get_targets(self, out_dir):
        targets = []
        files = self.get_file_names(out_dir)
        for k_f, f in files.items():
            targets.append(f if f else k_f)
        if self.report:
            targets.append(self.expand_filename(out_dir, self.report, 'drill_report', 'txt'))
        return targets
