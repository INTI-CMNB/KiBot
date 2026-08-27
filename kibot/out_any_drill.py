# -*- coding: utf-8 -*-
# Copyright (c) 2020-2026 Salvador E. Tropea
# Copyright (c) 2020-2026 Instituto Nacional de Tecnología Industrial
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)
# Drill table contributed by Nguyen Vincent (@nguyen-v)
import os
import re
import csv
from .error import KiPlotConfigurationError
from .kicad.drill_info import get_full_holes_list, PLATED_DICT, HOLE_SHAPE_DICT, HOLE_TYPE_DICT, HOLE_ROUND_SLOT
from .kiplot import run_command
from .optionable import Optionable
from .out_base import VariantOptions
from .gs import GS
from .layer import Layer
from .misc import W_NODRILL, DONT_STOP
from .macros import macros, document  # noqa: F401
from . import log

logger = log.get_logger()

VALID_COLUMNS = ["Count", "Hole Size", "Plated", "Hole Shape", "Drill Layer Pair", "Hole Type"]
VALID_COLUMNS_L = {c.lower() for c in VALID_COLUMNS}


class DrillMap(Optionable):
    def __init__(self):
        with document:
            self.output = GS.def_global_output
            """ *Name for the map file, KiCad defaults if empty (%i='PTH_drill_map') """
            self.type = 'pdf'
            """ [hpgl,ps,gerber,dxf,svg,pdf] Format for a graphical drill map.
                KiCad 10 doesn't support HPGL """
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
            self.unify_pth_and_npth = 'auto'
            """ [yes,no,auto] Choose whether to unify plated and non-plated
                holes in the same table. If 'auto' is chosen, the setting is copied
                from the `excellon` output's `pth_and_npth_single_file`"""
            self.group_slots_and_round_holes = True
            """ By default KiCad groups slots and rounded holes if they can be cut from the same tool (same diameter) """
        self._unknown_is_error = True


class DrillTableColumns(Optionable):
    """ Column for the drill table """
    _default = VALID_COLUMNS

    def __init__(self):
        super().__init__()
        self._unknown_is_error = True
        with document:
            self.field = ''
            """ *Name of the field to use for this column """
            self.name = ''
            """ *Name to display in the header. The field is used when empty """
        self._field_example = 'Count'

    @staticmethod
    def new(field):
        c = DrillTableColumns()
        c.field = c._name = field
        c._field = field.lower()
        c.validate_field()
        return c

    def __str__(self):
        return self.field if not self.name else f"{self.field} -> {self.name}"

    def validate_field(self):
        if self._field not in VALID_COLUMNS_L:
            raise KiPlotConfigurationError(f"Invalid column name `{self.field}`. Valid columns are: {VALID_COLUMNS}")

    def config(self, parent):
        super().config(parent)
        if not self.field:
            raise KiPlotConfigurationError(f"Missing or empty `field` in columns list ({self._tree})")
        self._field = self.field.lower()
        self.validate_field()
        self._name = self.name or self.field


class DrillTable(DrillOptions):
    def __init__(self):
        super().__init__()
        with document:
            self.output = GS.def_global_output
            """ *Name of the drill table. Not generated unless a name is specified.
                (%i='drill_table' %x='csv') """
            self.units = 'millimeters_mils'
            """ *[millimeters,mils,millimeters_mils,mils_millimeters] Units used for the hole sizes """
            self.columns = DrillTableColumns
            """ *[list(dict)|list(string)] List of columns to display.
                Each entry can be a dictionary with `field`, `name` or just a string (field name) """

    def config(self, parent):
        super().config(parent)
        if not self.columns:
            raise KiPlotConfigurationError("No columns for the drill table ({})".format(str(self._tree)))
        self._columns = [c if isinstance(c, DrillTableColumns) else DrillTableColumns.new(c) for c in self.columns]


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
                Not generated unless a format is specified.
                KiCad 10 doesn't support HPGL """
            self.output = GS.def_global_output
            """ *name for the drill file, KiCad defaults if empty (%i='PTH_drill') """
            self.report = DrillReport
            """ [dict|string=''] Name of the drill report. Not generated unless a name is specified """
            self.table = DrillTable
            """ [dict|string=''] Name of the drill table. Not generated unless a name is specified.
                Important: if the PCB contains no drills the file won't be generated """
            self.pth_id = None
            """ [string] Force this replacement for %i when generating PTH and unified files """
            self.npth_id = None
            """ [string] Force this replacement for %i when generating NPTH files """
        super().__init__()
        # Mappings to KiCad values
        self._map_map = {
                         'hpgl': GS.PLOT_FORMAT_HPGL,
                         'ps': GS.PLOT_FORMAT_POST,
                         'gerber': GS.PLOT_FORMAT_GERBER,
                         'dxf': GS.PLOT_FORMAT_DXF,
                         'svg': GS.PLOT_FORMAT_SVG,
                         'pdf': GS.PLOT_FORMAT_PDF,
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
        if GS.ki10:
            if map == 'hpgl':
                raise KiPlotConfigurationError("KiCad 10+ doesn't support HPGL")
            if map == 'gerber':
                self._map_cli = 'gerberx2'
            else:
                self._map_cli = map
        self._map_type = map
        self._map_ext = self._map_ext[map]
        self._map = self._map_map[map]
        # Solve the report for both cases
        self._report = self.report.filename if isinstance(self.report, DrillReport) else self.report
        # Solve the table for both cases
        if isinstance(self.table, str):
            self._table_output = self.table
            if hasattr(self, 'pth_and_npth_single_file'):
                self._table_unify_pth_and_npth = self.pth_and_npth_single_file
            else:
                self._table_unify_pth_and_npth = False
            self._table_group_slots_and_round_holes = True
            self._table_units = 'millimeters_mils'
        else:
            self._table_output = self.table.output
            if hasattr(self, 'pth_and_npth_single_file') and self.table.unify_pth_and_npth == 'auto':
                self._table_unify_pth_and_npth = self.pth_and_npth_single_file
            else:
                if self.table.unify_pth_and_npth in ["no", "auto"]:
                    self._table_unify_pth_and_npth = False
                else:
                    self._table_unify_pth_and_npth = True
            self._table_group_slots_and_round_holes = self.table.group_slots_and_round_holes
            self._table_units = self.table.units
        self._expand_id = 'drill'
        self._expand_ext = self._ext

    def solve_id(self, d):
        if not d:
            # Unified
            return self.pth_id if self.pth_id is not None else 'drill'
        if d[0] == 'N':
            # NPTH
            return self.npth_id if self.npth_id is not None else d+'_drill'
        elif d[0] == 'P':
            # PTH
            return self.pth_id if self.pth_id is not None else d+'_drill'
        # Other drill pairs
        return d+'_drill'

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
        top_layer = GS.copper_layer_to_ordinal(layer_pair[0])+1
        bot_layer = GS.copper_layer_to_ordinal(layer_pair[1])+1
        return f"(L{top_layer}-L{bot_layer})"

    @staticmethod
    def _get_drill_groups(unified):
        """ Get the ID for all the generated files.
            It includes buried/blind vias. """
        groups = [''] if unified else ['PTH', 'NPTH']
        via_type = 'PCB_VIA'
        pairs = set()
        for t in GS.board.GetTracks():
            tclass = t.GetClass()
            if tclass == via_type:
                via = t.Cast()
                l1i = via.TopLayer()
                l1 = AnyDrill._get_layer_name(l1i)
                l2i = via.BottomLayer()
                l2 = AnyDrill._get_layer_name(l2i)
                if GS.ki10 and l1i > l2i:
                    # KiCad bug https://gitlab.com/kicad/code/kicad/-/work_items/23452
                    aux = l1
                    l1 = l2
                    l2 = aux
                pair = l1+'-'+l2
                if pair != 'front-back':
                    pairs.add(pair)
        groups.extend(list(pairs))
        return groups

    def get_file_names(self, output_dir, just_drills=False, tmp_base=None):
        """ Returns a dict containing KiCad names and its replacement.
            If no replacement is needed the replacement is empty.
            tmp_base is used to specify the `GS.pcb_basename` for a temporal variant.
            I don't really know if variants really apply to drill files, but is currently supported """
        filenames = {}
        self._configure_writer(GS.board, GS.pn.wxPoint(0, 0))
        files = AnyDrill._get_drill_groups(self._unified_output)
        force_rename = tmp_base is not None
        if not force_rename:
            tmp_base = GS.pcb_basename
        for d in files:
            kicad_id = '-'+d if d else d
            kibot_id = self.solve_id(d)
            kicad_id_main = kicad_id_map = kicad_id
            if self._ext == 'gbr':
                kicad_id_main += '-drl'
                if not GS.ki8:
                    kicad_id_map = kicad_id_main
            if self.generate_drill_files or just_drills:
                k_file = self.expand_filename(output_dir, tmp_base+kicad_id_main+'.%x', '', self._ext)
                file = ''
                if self.output:
                    file = self.expand_filename(output_dir, self.output, kibot_id, self._ext)
                elif force_rename:
                    # To get the real name instead of the temporal one
                    file = k_file.replace(tmp_base, GS.pcb_basename)
                filenames[k_file] = file
            if self._map is not None and not just_drills:
                k_file = self.expand_filename(output_dir, tmp_base+kicad_id_map+'-drl_map.%x', '', self._map_ext)
                file = ''
                if self._map_output:
                    file = self.expand_filename(output_dir, self._map_output, kibot_id+'_map', self._map_ext)
                elif force_rename:
                    file = k_file.replace(tmp_base, GS.pcb_basename)
                filenames[k_file] = file
        return filenames

    def look_for_drills(self):
        """ KiCad 10 skips empty gerber files """
        if not GS.ki10 or self._ext != 'gbr':
            return True, True
        # Look for vias, they are PTH
        for t in GS.board.GetTracks():
            tclass = t.GetClass()
            if tclass == 'PCB_VIA':
                found_pth = True
                break
        else:
            found_pth = False
        # Look for pads
        found_npth = False
        for m in GS.board.GetFootprints():
            pads = m.Pads()
            for pad in pads:
                dr = pad.GetDrillSize()
                if dr.x == 0 or dr.y == 0:
                    continue
                is_pth = pad.GetAttribute() != GS.pn.PAD_ATTRIB_NPTH
                if not is_pth:
                    found_npth = True
                if is_pth:
                    found_pth = True
                if found_pth and found_npth:
                    break
            if found_pth and found_npth:
                break
        logger.debug(f"Drills search: PTH {found_pth} NPTH {found_npth}")
        return found_pth, found_npth

    def run(self, output_dir):
        super().run(output_dir)
        self.filter_pcb_components()
        if self.output:
            output_dir = os.path.dirname(output_dir)
        # dialog_gendrill.cpp:357
        if self.use_aux_axis_as_origin:
            offset = GS.get_aux_origin()
        else:
            offset = GS.pn.wxPoint(0, 0)
        drill_writer, use_cli = self._configure_writer(GS.board, offset)

        logger.debug("Generating drill files in "+output_dir)
        gen_map = self._map is not None

        if not self.generate_drill_files and not gen_map and not self._report and not self._table_output:
            logger.warning(
                W_NODRILL +
                "Not generating drill files nor drill maps "
                "nor report nor drill table on "
                f"`{self._parent.name}`"
            )

        if use_cli:
            # Using kicad-cli
            fname = self.save_tmp_board() if self.will_filter_pcb_components() else GS.pcb_file
            odir = output_dir  # if self.generate_drill_files else tempfile.gettempdir()
            # No variant here
            cmd = [GS.kicad_cli, 'pcb', 'export', 'drill', '--output', odir] + drill_writer
            if gen_map:
                logger.debug("Generating drill map type {} in {}".format(self._map, output_dir))
                cmd.extend(['--generate-map', '--map-format', self._map_cli])
            if self._report:
                drill_report_file = self.expand_filename(output_dir, self._report, 'drill_report', 'txt')
                logger.debug("Generating drill report: "+drill_report_file)
                cmd.extend(['--generate-report', '--report-path', drill_report_file])
            run_command(cmd + [fname])
            if self._files_to_remove:
                self.remove_temporals()
            tmp_base = os.path.splitext(os.path.basename(fname))[0]
            if not self.generate_drill_files:
                # We can't prevent kicad-cli from generating them, so just remove them
                files = self.get_file_names(output_dir, tmp_base=tmp_base, just_drills=True)
                for f in files.keys():
                    os.remove(f)
        else:
            # Using Python API
            if gen_map:
                drill_writer.SetMapFileFormat(self._map)
                logger.debug("Generating drill map type {} in {}".format(self._map, output_dir))
            if GS.ki10 and isinstance(drill_writer, GS.pn.GERBER_WRITER):
                # KiCad 10 inconsistency ...
                drill_writer.CreateDrillandMapFilesSet(output_dir, self.generate_drill_files, gen_map, True)
            else:
                drill_writer.CreateDrillandMapFilesSet(output_dir, self.generate_drill_files, gen_map)
            # Generate the report
            if self._report:
                drill_report_file = self.expand_filename(output_dir, self._report, 'drill_report', 'txt')
                logger.debug("Generating drill report: "+drill_report_file)
                if GS.ki10:
                    logger.error("No drill reports until KiCad bug https://gitlab.com/kicad/code/kicad/-/work_items/23268 "
                                 "is fixed")
                else:
                    drill_writer.GenDrillReportFile(drill_report_file)
            tmp_base = None

        # KiCad 10 has a feature: no files generated if the kind of drills is missing
        has_pth, has_npth = self.look_for_drills()

        # Rename the files
        files = self.get_file_names(output_dir, tmp_base=tmp_base)
        for k_f, f in files.items():
            if f:
                logger.debug(f"Renaming {k_f} -> {f}")
                if not os.path.isfile(k_f):
                    is_npth = 'npth' in k_f.lower()
                    if (is_npth and has_npth) or (not is_npth and has_pth):
                        GS.exit_with_error(f"Missing `{k_f}` drill file, KiCad bug? please report", DONT_STOP)
                else:
                    os.replace(k_f, f)
        # Generate the drill table
        if self._table_output:

            hole_list, tool_list, hole_sets, npth = get_full_holes_list(self._table_unify_pth_and_npth,
                                                                        self._table_group_slots_and_round_holes)

            # Get column configuration
            # columns = self.get_columns_config()
            # columns = self.validate_and_process_columns(columns, VALID_COLUMNS)
            columns = self.table._columns

            for i, (tools, layer_pair) in enumerate(zip(tool_list, hole_sets)):

                layer_pair_name = AnyDrill._get_layer_pair_names(layer_pair)

                if npth and i == len(hole_sets)-1:
                    layer_pair_name += '_NPTH'

                csv_file = self.expand_filename(output_dir, self._table_output, f'{layer_pair_name}' + '_drill_table', 'csv')

                logger.debug("Generating drill table: "+csv_file)

                with open(csv_file, mode='w', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)

                    # Write header
                    writer.writerow([col._name for col in columns])

                    # Write rows
                    for tool in tools:
                        row = []
                        for col in columns:
                            if col._field == "count":
                                value = (f'{tool.m_TotalCount-tool.m_OvalCount} + {tool.m_OvalCount}' if
                                         tool.m_Hole_Shape == HOLE_ROUND_SLOT else tool.m_TotalCount)
                            elif col._field == "hole size":
                                if self._table_units == 'millimeters':
                                    value = f'{GS.to_mm(tool.m_Diameter):.2f}mm'
                                elif self._table_units == 'mils':
                                    value = f'{GS.to_mils(tool.m_Diameter):.2f}mils'
                                elif self._table_units == 'mils_millimeters':
                                    value = f'{GS.to_mils(tool.m_Diameter):.2f}mils ({GS.to_mm(tool.m_Diameter):.2f}mm)'
                                else:  # millimeters_mils
                                    value = f'{GS.to_mm(tool.m_Diameter):.2f}mm ({GS.to_mils(tool.m_Diameter):.2f}mils)'
                            elif col._field == "plated":
                                value = PLATED_DICT[tool.m_Hole_NotPlated]
                            elif col._field == "hole shape":
                                value = HOLE_SHAPE_DICT[tool.m_Hole_Shape]
                            elif col._field == "drill layer pair":
                                value = f'{GS.board.GetLayerName(layer_pair[0])} - {GS.board.GetLayerName(layer_pair[1])}'
                            elif col._field == "hole type" and GS.ki6:
                                value = HOLE_TYPE_DICT[tool.m_HoleAttribute]
                            else:
                                value = ""
                            row.append(value)
                        writer.writerow(row)

                    row = []
                    for col in columns:
                        row.append(f"Total {sum(tool.m_TotalCount for tool in tools)}" if col._field == "count" else "")
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
            _, _, hole_sets, npth = get_full_holes_list(self._table_unify_pth_and_npth,
                                                        self._table_group_slots_and_round_holes)
            for i, layer_pair in enumerate(hole_sets):
                layer_pair_name = AnyDrill._get_layer_pair_names(layer_pair)
                if npth and i == len(hole_sets)-1:
                    layer_pair_name += '_NPTH'
                targets.append(self.expand_filename(out_dir, self._table_output,
                               f'{layer_pair_name}' + '_drill_table', 'csv'))
        return targets
