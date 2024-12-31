# -*- coding: utf-8 -*-
# Copyright (c) 2020-2024 Salvador E. Tropea
# Copyright (c) 2020-2024 Instituto Nacional de Tecnología Industrial
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)
import os
import re
import csv
from pcbnew import (PLOT_FORMAT_HPGL, PLOT_FORMAT_POST, PLOT_FORMAT_GERBER, PLOT_FORMAT_DXF, PLOT_FORMAT_SVG,
                    PLOT_FORMAT_PDF, wxPoint, B_Cu)
from .kicad.drill_info import get_full_holes_list, PLATED_DICT, HOLE_SHAPE_DICT
from .optionable import Optionable
from .out_base import VariantOptions
from .gs import GS
from .layer import Layer
from .misc import W_NODRILL
from .macros import macros, document  # noqa: F401
from . import log

if not GS.ki5:
    from .kicad.drill_info import HOLE_TYPE_DICT

logger = log.get_logger()

if GS.ki5:
    VALID_COLUMNS = [
        "Count",
        "Hole Size",
        "Plated",
        "Hole Shape",
        "Drill Layer Pair",
    ]
else:
    VALID_COLUMNS = [
        "Count",
        "Hole Size",
        "Plated",
        "Hole Shape",
        "Drill Layer Pair",
        "Hole Type",
    ]


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


class DrillOptions(Optionable):
    def __init__(self):
        super().__init__()
        with document:
            self.pth_and_npth_single_file = True
            """ Generate one file for both, plated holes and non-plated holes, instead of two separated files """
            self.group_slots_and_round_holes = True
            """ By default KiCad groups slots and rounded holes if they can be cut from the same tool (same diameter) """
        self._unknown_is_error = True


class DrillTable(DrillOptions):
    def __init__(self):
        super().__init__()
        with document:
            self.output = GS.def_global_output
            """ *Name of the drill table. Not generated unless a name is specified.
                (%i='drill_table' %x='csv') """
            self.units = 'millimeters_mils'
            """ *[millimeters,mils,millimeters_mils,mils_millimeters] Units used for the hole sizes """
            self.columns = []
            """ *[list(dict)|list(string)=?] List of columns to display.
                Each entry can be a dictionary with `field`, `name` or just a string (field name).
                Default fields are: ["Count", "Hole Size", "Plated", "Hole Shape", "Drill Layer Pair", "Hole Type"] """


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
            self.table = DrillTable
            """ [dict|string=''] Name of the drill table. Not generated unless a name is specified """
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
        # Solve the table for both cases
        if isinstance(self.table, str):
            self._table_output = self.table
            self._table_pth_npth_single_file = True
            self._table_group_slots_and_round_holes = True
            self._table_units = 'millimeters_mils'
        else:
            self._table_output = self.table.output
            self._table_pth_npth_single_file = self.table.pth_and_npth_single_file
            self._table_group_slots_and_round_holes = self.table.group_slots_and_round_holes
            self._table_units = self.table.units
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
    def _get_layer_pair_names(layer_pair):
        layer_cnt = GS.board.GetCopperLayerCount()
        top_layer = layer_pair[0] + 1
        bot_layer = layer_pair[1] + 1 if layer_pair[1] != B_Cu else layer_cnt
        return f"(L{top_layer} - L{bot_layer})"

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

    def get_columns_config(self):
        """Process the columns configuration."""
        columns = self.table.columns if isinstance(self.table, DrillTable) else []
        if not columns:
            # Default column configuration based on VALID_COLUMNS
            return [{"field": col, "name": col} for col in VALID_COLUMNS]

        # Process custom columns
        processed_columns = []
        for col in columns:
            if isinstance(col, str):
                # Simple field name
                processed_columns.append({"field": col, "name": col})
            elif isinstance(col, dict):
                # Detailed configuration
                processed_columns.append({
                    "field": col.get("field", ""),
                    "name": col.get("name", col.get("field", "")),
                })
        return processed_columns

    def validate_and_process_columns(self, cols, valid_columns):

        processed_columns = []
        valid_columns_l = {col.lower(): col for col in valid_columns}

        for col in cols:
            if isinstance(col, str):
                # Simple field name
                field = col
                name = col
            elif isinstance(col, dict):
                # Detailed configuration
                field = col.get("field", "")
                name = col.get("name", field)
            else:
                logger.warning(f"Invalid column entry: {col}")

            field_lower = field.lower()
            if field_lower not in valid_columns_l:
                logger.warning(f"Invalid column name `{field}`. Valid columns are: {list(valid_columns_l.values())}")
                continue  # Skip invalid columns

            processed_columns.append({
                "field": valid_columns_l[field_lower],  # Use the original case from the valid columns list
                "name": name,
            })

        if not processed_columns:
            logger.error("No valid columns specified. At least one valid column is required.")

        return processed_columns

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
        if not self.generate_drill_files and not gen_map and not self._report and not self._table_output:
            logger.warning(
                W_NODRILL +
                "Not generating drill files nor drill maps "
                "nor report nor drill table on "
                f"`{self._parent.name}`"
            )
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
        # Generate the drill table
        if self._table_output:

            hole_list, tool_list, hole_sets, npth = get_full_holes_list(self._table_pth_npth_single_file,
                                                                        self._table_group_slots_and_round_holes)

            # Get column configuration

            columns = self.get_columns_config()
            columns = self.validate_and_process_columns(columns, VALID_COLUMNS)

            for i, (tools, layer_pair) in enumerate(zip(tool_list, hole_sets)):

                layer_pair_name = AnyDrill._get_layer_pair_names(layer_pair)

                if npth and i == len(hole_sets)-1:
                    layer_pair_name += '_NPTH'

                csv_file = self.expand_filename(output_dir, self._table_output, f'{layer_pair_name}' + '_drill_table', 'csv')

                logger.debug("Generating drill table: "+csv_file)

                with open(csv_file, mode='w', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)

                    # Write header
                    writer.writerow([col["name"] for col in columns])

                    # Write rows
                    for tool in tools:
                        row = []
                        for col in columns:
                            if col["field"] == "Count":
                                value = (f'{tool.m_TotalCount-tool.m_OvalCount} + {tool.m_OvalCount}' if
                                         tool.m_Hole_Shape == 2 else tool.m_TotalCount)
                            elif col["field"] == "Hole Size":
                                if self._table_units == 'millimeters':
                                    value = f'{GS.to_mm(tool.m_Diameter):.2f}mm'
                                elif self._table_units == 'mils':
                                    value = f'{GS.to_mils(tool.m_Diameter):.2f}mils'
                                elif self._table_units == 'mils_millimeters':
                                    value = f'{GS.to_mils(tool.m_Diameter):.2f}mils ({GS.to_mm(tool.m_Diameter):.2f}mm)'
                                else:
                                    value = f'{GS.to_mm(tool.m_Diameter):.2f}mm ({GS.to_mils(tool.m_Diameter):.2f}mils)'
                            elif col["field"] == "Plated":
                                value = PLATED_DICT[tool.m_Hole_NotPlated]
                            elif col["field"] == "Hole Shape":
                                value = HOLE_SHAPE_DICT[tool.m_Hole_Shape]
                            elif col["field"] == "Drill Layer Pair":
                                value = f'{GS.board.GetLayerName(layer_pair[0])} - {GS.board.GetLayerName(layer_pair[1])}'
                            elif col["field"] == "Hole Type":
                                if not GS.ki5:
                                    value = HOLE_TYPE_DICT[tool.m_HoleAttribute]
                            else:
                                value = ""
                            row.append(value)
                        writer.writerow(row)

                    row = []
                    for col in columns:
                        if col["field"] == "Count":
                            value = f"Total {sum(tool.m_TotalCount for tool in tools)}"
                        else:
                            value = ""
                        row.append(value)
                    writer.writerow(row)

        self.unfilter_pcb_components()

    def get_targets(self, out_dir):
        targets = []
        files = self.get_file_names(out_dir)
        for k_f, f in files.items():
            targets.append(f if f else k_f)
        if self._report:
            targets.append(self.expand_filename(out_dir, self._report, 'drill_report', 'txt'))
        if self._table_output:
            _, _, hole_sets, npth = get_full_holes_list(self._table_pth_npth_single_file,
                                                        self._table_group_slots_and_round_holes)
            for i, layer_pair in enumerate(hole_sets):
                layer_pair_name = AnyDrill._get_layer_pair_names(layer_pair)
                if npth and i == len(hole_sets)-1:
                    layer_pair_name += '_NPTH'
                targets.append(self.expand_filename(out_dir, self._table_output,
                               f'{layer_pair_name}' + '_drill_table', 'csv'))
        return targets
