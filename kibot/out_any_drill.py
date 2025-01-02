# -*- coding: utf-8 -*-
# Copyright (c) 2020-2024 Salvador E. Tropea
# Copyright (c) 2020-2024 Instituto Nacional de Tecnología Industrial
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)
import os
import re
from pcbnew import (PLOT_FORMAT_HPGL, PLOT_FORMAT_POST, PLOT_FORMAT_GERBER, PLOT_FORMAT_DXF, PLOT_FORMAT_SVG,
                    PLOT_FORMAT_PDF, wxPoint)
from .optionable import Optionable
from .out_base import VariantOptions
from .gs import GS
from .layer import Layer
from .misc import W_NODRILL
from .macros import macros, document  # noqa: F401
from . import log

logger = log.get_logger()


class DrillMap(Optionable):
    def __init__(self):
        with document:
            self.output = GS.def_global_output
            """ *Name for the map file, KiCad defaults if empty (%i='PTH_drill_map') """
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


class AnyDrill(VariantOptions):
    def __init__(self):
        # Options
        with document:
            self.generate_drill_files = True
            """ Generate drill files. Set to False and choose map format if only map is to be generated """
            self.use_aux_axis_as_origin = False
            """ Use the auxiliary axis as origin for coordinates """
            self.map = DrillMap
            """ [dict|string='None'] [hpgl,ps,gerber,dxf,svg,pdf,None] Format for a graphical drill map.
                Not generated unless a format is specified """
            self.output = GS.def_global_output
            """ *name for the drill file, KiCad defaults if empty (%i='PTH_drill') """
            self.report = DrillReport
            """ [dict|string=''] Name of the drill report. Not generated unless a name is specified """
            self.pth_id = None
            """ [string] Force this replacement for %i when generating PTH and unified files """
            self.npth_id = None
            """ [string] Force this replacement for %i when generating NPTH files """
            self.other_id = None
            """ [string] Force this replacement for <suffix> when generating other layer pair files
                %i='<layer_pair><suffix>'. Note that <layer_pair> is the default name from KiCad.
                By default, suffix = '_drill' """
        super().__init__()
        # Mappings to KiCad values
        self._map_map = {
                         'hpgl': PLOT_FORMAT_HPGL,
                         'ps': PLOT_FORMAT_POST,
                         'gerber': PLOT_FORMAT_GERBER,
                         'dxf': PLOT_FORMAT_DXF,
                         'svg': PLOT_FORMAT_SVG,
                         'pdf': PLOT_FORMAT_PDF,
                         'None': None
                        }
        self._map_ext = {'hpgl': 'plt', 'ps': 'ps', 'gerber': 'gbr', 'dxf': 'dxf', 'svg': 'svg', 'pdf': 'pdf', 'None': None}
        self._unified_output = False
        self.help_only_sub_pcbs()

    def config(self, parent):
        super().config(parent)
        # Solve the map for both cases
        if isinstance(self.map, str):
            map = self.map
            self._map_output = GS.global_output if GS.global_output is not None else GS.def_global_output
        else:
            map = self.map.type
            self._map_output = self.map.output
        self._map_ext = self._map_ext[map]
        self._map = self._map_map[map]
        # Solve the report for both cases
        self._report = self.report.filename if isinstance(self.report, DrillReport) else self.report
        self._expand_id = 'drill'
        self._expand_ext = self._ext

    def solve_id(self, d):
        if not d:
            # Unified
            return self.pth_id if self.pth_id not in [None, 'None'] else 'drill'
        if d[0] == 'N':
            # NPTH
            return self.npth_id if self.npth_id not in [None, 'None'] else d+'_drill'
        elif d[0] == 'P':
            # PTH
            return self.pth_id if self.pth_id not in [None, 'None'] else d+'_drill'

        # Other layer pairs (here we only control the text after the default kicad ID)
        return d + self.other_id if self.other_id not in [None, 'None'] else d+'_drill'

    @staticmethod
    def _get_layer_name(id):
        """ Converts a layer ID into the magical name used by KiCad.
            This is somehow portable because we don't directly rely on the ID. """
        name = Layer.id2def_name(id)
        if name == 'F.Cu':
            return 'front'
        if name == 'B.Cu':
            return 'back'
        m = re.match(r'In(\d+)\.Cu', name)
        if not m:
            return None
        return 'in'+m.group(1)

    @staticmethod
    def _get_drill_groups(unified):
        """ Get the ID for all the generated files.
            It includes buried/blind vias. """
        groups = [''] if unified else ['PTH', 'NPTH']
        via_type = 'VIA' if GS.ki5 else 'PCB_VIA'
        pairs = set()
        for t in GS.board.GetTracks():
            tclass = t.GetClass()
            if tclass == via_type:
                via = t.Cast()
                l1 = AnyDrill._get_layer_name(via.TopLayer())
                l2 = AnyDrill._get_layer_name(via.BottomLayer())
                pair = l1+'-'+l2
                if pair != 'front-back':
                    pairs.add(pair)
        groups.extend(list(pairs))
        return groups

    def get_file_names(self, output_dir):
        """ Returns a dict containing KiCad names and its replacement.
            If no replacement is needed the replacement is empty """
        filenames = {}
        self._configure_writer(GS.board, wxPoint(0, 0))
        files = AnyDrill._get_drill_groups(self._unified_output)
        for d in files:
            kicad_id = '-'+d if d else d
            kibot_id = self.solve_id(d)
            kicad_id_main = kicad_id_map = kicad_id
            if self._ext == 'gbr':
                kicad_id_main += '-drl'
                if not GS.ki8:
                    kicad_id_map = kicad_id_main
            if self.generate_drill_files:
                k_file = self.expand_filename(output_dir, '%f'+kicad_id_main+'.%x', '', self._ext)
                file = ''
                if self.output:
                    file = self.expand_filename(output_dir, self.output, kibot_id, self._ext)
                filenames[k_file] = file
            if self._map is not None:
                k_file = self.expand_filename(output_dir, '%f'+kicad_id_map+'-drl_map.%x', '', self._map_ext)
                file = ''
                if self._map_output:
                    file = self.expand_filename(output_dir, self._map_output, kibot_id+'_map', self._map_ext)
                filenames[k_file] = file
        return filenames

    def run(self, output_dir):
        super().run(output_dir)
        self.filter_pcb_components()
        if self.output:
            output_dir = os.path.dirname(output_dir)
        # dialog_gendrill.cpp:357
        if self.use_aux_axis_as_origin:
            offset = GS.get_aux_origin()
        else:
            offset = wxPoint(0, 0)
        drill_writer = self._configure_writer(GS.board, offset)

        logger.debug("Generating drill files in "+output_dir)
        gen_map = self._map is not None
        if gen_map:
            drill_writer.SetMapFileFormat(self._map)
            logger.debug("Generating drill map type {} in {}".format(self._map, output_dir))
        if not self.generate_drill_files and not gen_map and not self._report:
            logger.warning(W_NODRILL+f"Not generating drill files nor drill maps nor report on `{self._parent.name}`")
        drill_writer.CreateDrillandMapFilesSet(output_dir, self.generate_drill_files, gen_map)
        # Rename the files
        files = self.get_file_names(output_dir)
        for k_f, f in files.items():
            if f:
                logger.debug("Renaming {} -> {}".format(k_f, f))
                os.replace(k_f, f)
        # Generate the report
        if self._report:
            drill_report_file = self.expand_filename(output_dir, self._report, 'drill_report', 'txt')
            logger.debug("Generating drill report: "+drill_report_file)
            drill_writer.GenDrillReportFile(drill_report_file)
        self.unfilter_pcb_components()

    def get_targets(self, out_dir):
        targets = []
        files = self.get_file_names(out_dir)
        for k_f, f in files.items():
            targets.append(f if f else k_f)
        if self._report:
            targets.append(self.expand_filename(out_dir, self._report, 'drill_report', 'txt'))
        return targets
