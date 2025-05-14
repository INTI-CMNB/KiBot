# -*- coding: utf-8 -*-
# Copyright (c) 2020-2025 Salvador E. Tropea
# Copyright (c) 2020-2025 Instituto Nacional de Tecnología Industrial
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)
from contextlib import contextmanager
import os
import re
import json
try:
    import pcbnew
except ImportError:
    # This is caught by __main__, ignore the error here
    class pcbnew(object):
        IU_PER_MM = 1
        IU_PER_MILS = 1
from datetime import datetime
import shlex
from shutil import copy2
from sys import exit, exc_info
import tempfile
from traceback import extract_stack, format_list, print_tb
from .misc import EXIT_BAD_ARGS, W_DATEFORMAT, W_UNKVAR, WRONG_INSTALL, CORRUPTED_PRO, hide_stderr
from .log import get_logger

logger = get_logger(__name__)
if hasattr(pcbnew, 'IU_PER_MM'):
    IU_PER_MM = pcbnew.IU_PER_MM
    IU_PER_MILS = pcbnew.IU_PER_MILS
else:
    IU_PER_MM = pcbnew.pcbIUScale.IU_PER_MM
    IU_PER_MILS = pcbnew.pcbIUScale.IU_PER_MILS
if hasattr(pcbnew, 'DRILL_MARKS_NO_DRILL_SHAPE'):
    NO_DRILL_SHAPE = pcbnew.DRILL_MARKS_NO_DRILL_SHAPE
    SMALL_DRILL_SHAPE = pcbnew.DRILL_MARKS_SMALL_DRILL_SHAPE
    FULL_DRILL_SHAPE = pcbnew.DRILL_MARKS_FULL_DRILL_SHAPE
elif hasattr(pcbnew, 'PCB_PLOT_PARAMS'):
    NO_DRILL_SHAPE = pcbnew.PCB_PLOT_PARAMS.NO_DRILL_SHAPE
    SMALL_DRILL_SHAPE = pcbnew.PCB_PLOT_PARAMS.SMALL_DRILL_SHAPE
    FULL_DRILL_SHAPE = pcbnew.PCB_PLOT_PARAMS.FULL_DRILL_SHAPE
# KiCad 6 uses IUs for SVGs, with option for SVG_Precision
# KiCad 5 uses a very different scale based on inches
# KiCad 7 uses mm
KICAD5_SVG_SCALE = 116930/297002200
# Characters we don't want in a file name
INVALID_CHARS = r'[?%*:|"<>]'


class GS(object):
    """
    Class to keep the global settings.
    Is a static class, just a placeholder for some global variables.
    """
    # PCB name and useful parts
    pcb_file = None      # /.../dir/pcb.kicad_pcb
    pcb_no_ext = None    # /.../dir/pcb
    pcb_dir = None       # /.../dir
    pcb_basename = None  # pcb
    pcb_fname = None     # pcb.kicad_pcb
    pcb_last_dir = None  # dir
    # SCH name and useful parts
    sch_file = None      # /.../dir/file.sch
    sch_no_ext = None    # /.../dir/file
    sch_dir = None       # /.../dir
    sch_last_dir = None  # dir
    sch_basename = None  # file
    sch_fname = None     # file.kicad_sch
    # Project and useful parts
    pro_file = None      # /.../dir/file.kicad_pro (or .pro)
    pro_no_ext = None    # /.../dir/file
    pro_dir = None       # /.../dir
    pro_last_dir = None  # dir
    pro_basename = None  # file
    pro_fname = None     # file.kicad_pro (or .pro)
    pro_ext = '.pro'
    pro_variables = None  # KiCad 6 text variables defined in the project
    pro_bom_settings = None  # KiCad BoM settings from the project
    pro_bom_fmt_settings = None  # KiCad BoM file format options
    pro_bom_export_filename = ''  # KiCad BoM file name, for the extension
    vars_regex = re.compile(r'\$\{([^\}]+)\}')
    # Main output dir
    out_dir = None
    out_dir_in_cmd_line = False
    # Content of the "filters" preflight
    filter_file = None
    filters = None
    board = None
    sch = None
    debug_enabled = False
    debug_level = 0
    kibot_version = None
    n = datetime.now()
    on_windows = False
    on_macos = False
    kicad_version = ''
    kicad_conf_path = None
    kicad_share_path = None
    kicad_dir = 'kicad'
    kicad_plugins_dirs = []
    # KiCad version: major*1e6+minor*1e3+patch
    kicad_version_n = 0
    kicad_version_major = 0
    kicad_version_minor = 0
    kicad_version_patch = 0
    # Data from the SCH because it doesn't have a Python API
    sch_title = None
    sch_date = None
    sch_rev = None
    sch_comp = None
    sch_com = [None]*9
    # Data from the board title block
    pcb_title = None
    pcb_date = None
    pcb_rev = None
    pcb_comp = None
    pcb_com = [None]*9
    # Current variant/s
    variant = None
    # All the outputs
    outputs = None
    # Name for the output we are generating
    current_output = None
    test_boolean = True
    test_number = 5
    stackup = None
    # Preprocessor definitions
    cli_defines = {}
    kikit_units_to_kicad = {'mm': IU_PER_MM, 'cm': 10*IU_PER_MM, 'dm': 100*IU_PER_MM,
                            'm': 1000*IU_PER_MM, 'mil': IU_PER_MILS, 'inch': 1000*IU_PER_MILS,
                            'in': 1000*IU_PER_MILS}
    ci_cd_detected = False
    stop_flag = False
    # Maximum recursive replace
    MAXDEPTH = 20
    #
    # Global defaults
    #
    # Options from command line
    cli_global_defs = {}
    # The variant value, but already solved
    solved_global_variant = None
    # This is used as default value for classes supporting "output" option
    def_global_output = '%f-%i%I%v.%x'
    def_work_layer = 'Margin'
    # The class that controls the global options
    class_for_global_opts = None
    # The last tree we used to configure it
    globals_tree = None
    # Global options
    global_allow_component_ranges = None
    global_always_warn_about_paste_pads = None
    global_cache_3d_resistors = None
    global_castellated_pads = None
    global_colored_tht_resistors = None
    global_copper_thickness = None
    global_cross_footprints_for_dnp = None
    global_dnp_cross_top_layer = None
    global_dnp_cross_bottom_layer = None
    global_cross_no_body = None
    global_csv_accept_no_ref = None
    global_date_format = None
    global_date_time_format = None
    global_default_resistor_tolerance = None
    global_drc_exclusions_workaround = None
    global_dir = None
    global_disable_3d_alias_as_env = None
    global_drill_size_increment = None
    global_edge_connector = None
    global_edge_plating = None
    global_extra_pth_drill = None
    global_field_3D_model = None
    global_field_current = None
    global_field_dist_part_number = None
    global_field_distributor = None
    global_field_lcsc_part = None
    global_field_manufacturer = None
    global_field_package = None
    global_field_part_number = None
    global_field_power = None
    global_field_temp_coef = None
    global_field_tolerance = None
    global_field_voltage = None
    global_hide_excluded = None
    global_git_diff_strategy = None
    global_impedance_controlled = None
    global_invalidate_pcb_text_cache = None
    global_kiauto_time_out_scale = None
    global_kiauto_wait_start = None
    global_layer_defaults = None
    global_include_components_from_pcb = None
    global_use_pcb_fields = None
    #  This value will overwrite GS.def_global_output if defined
    #  Classes supporting global "output" option must call super().__init__()
    #  after defining its own options to allow Optionable do the overwrite.
    global_output = None
    global_pcb_finish = None
    global_pcb_material = None
    global_remove_solder_paste_for_dnp = None
    global_remove_solder_mask_for_dnp = None
    global_remove_adhesive_for_dnp = None
    global_resources_dir = None
    global_restore_project = None
    global_sch_image_prefix = None
    global_set_text_variables_before_output = None
    global_silk_screen_color = None
    global_silk_screen_color_bottom = None
    global_silk_screen_color_top = None
    global_solder_mask_color = None
    global_solder_mask_color_bottom = None
    global_solder_mask_color_top = None
    global_str_yes = None
    global_str_no = None
    global_time_format = None
    global_time_reformat = None
    global_units = None
    global_use_dir_for_preflights = None
    global_use_os_env_for_expand = None
    global_variant = None
    global_vrml_3d_model_workaround = None
    # Only for v7+
    global_allow_blind_buried_vias = None
    global_allow_microvias = None
    global_erc_grid = None
    global_kicad_dnp_applied = None
    global_kicad_dnp_applies_to_3D = None
    global_cross_using_kicad = None
    global_work_layer = None
    pasteable_cmd = shlex.join if hasattr(shlex, 'join') else lambda x: str(x)   # novermin

    @staticmethod
    def set_sch(name):
        if name:
            name = os.path.abspath(name)
            GS.sch_file = name
            GS.sch_fname = os.path.basename(name)
            GS.sch_basename = os.path.splitext(GS.sch_fname)[0]
            GS.sch_no_ext = os.path.splitext(name)[0]
            GS.sch_dir = os.path.dirname(name)
            GS.sch_last_dir = os.path.basename(GS.sch_dir)

    @staticmethod
    def set_pcb(name):
        if name:
            name = os.path.abspath(name)
            GS.pcb_file = name
            GS.pcb_fname = os.path.basename(name)
            GS.pcb_basename = os.path.splitext(GS.pcb_fname)[0]
            GS.pcb_no_ext = os.path.splitext(name)[0]
            GS.pcb_dir = os.path.dirname(name)
            GS.pcb_last_dir = os.path.basename(GS.pcb_dir)

    @staticmethod
    def set_pro(name):
        if name:
            name = os.path.abspath(name)
            GS.pro_file = name
            GS.pro_fname = os.path.basename(name)
            GS.pro_basename = os.path.splitext(GS.pro_fname)[0]
            GS.pro_no_ext = os.path.splitext(name)[0]
            GS.pro_dir = os.path.dirname(name)
            GS.pro_last_dir = os.path.basename(GS.pro_dir)

    @staticmethod
    def load_pro_variables():
        if GS.pro_variables is not None:
            return GS.pro_variables
        if GS.pro_file is None or GS.pro_ext == '.pro':
            return {}
        # Get the text_variables
        with open(GS.pro_file, 'rt') as f:
            pro_text = f.read()
        try:
            data = json.loads(pro_text)
        except Exception:
            GS.exit_with_error('Corrupted project {}'.format(GS.pro_file), CORRUPTED_PRO)
        GS.pro_variables = data.get('text_variables', {})
        logger.debug("Current text variables: {}".format(GS.pro_variables))
        return GS.pro_variables

    @staticmethod
    def load_pro_bom_settings():
        if GS.pro_bom_settings is not None:
            return GS.pro_bom_settings
        if GS.pro_file is None or GS.pro_ext == '.pro':
            return {}
        # Get the bom settings
        with open(GS.pro_file, 'rt') as f:
            pro_text = f.read()
        try:
            data = json.loads(pro_text)
        except Exception:
            GS.exit_with_error('Corrupted project {}'.format(GS.pro_file), CORRUPTED_PRO)
        schematic = data.get('schematic', {})
        GS.pro_bom_settings = schematic.get('bom_settings', {})
        GS.pro_bom_fmt_settings = schematic.get('bom_fmt_settings', {})
        GS.pro_bom_export_filename = schematic.get('bom_export_filename', '')
        logger.debug("Current bom_settings: {}".format(GS.pro_bom_settings))
        return GS.pro_bom_settings

    @staticmethod
    def load_pro_bom_fmt_settings():
        if GS.pro_bom_fmt_settings is None:
            GS.load_pro_bom_settings()
        return GS.pro_bom_fmt_settings

    @staticmethod
    def read_pro():
        if not GS.pro_file:
            return None
        # Note: We use binary mode to preserve the original end of lines
        # Otherwise git could see changes in the file
        with open(GS.pro_file, 'rb') as f:
            pro = f.read()
        prl_name = GS.pro_file[:-3]+'prl'
        prl = None
        if os.path.isfile(prl_name):
            with open(prl_name, 'rb') as f:
                prl = f.read()
        dru_name = GS.pro_file[:-3]+'dru'
        dru = None
        if os.path.isfile(dru_name):
            with open(dru_name, 'rb') as f:
                dru = f.read()
        return (pro, prl, dru)

    @staticmethod
    def write_pro(data):
        if not GS.pro_file or data is None:
            return
        with open(GS.pro_file, 'wb') as f:
            f.write(data[0])
        if data[1] is not None:
            with open(GS.pro_file[:-3]+'prl', 'wb') as f:
                f.write(data[1])
        if data[2] is not None:
            with open(GS.pro_file[:-3]+'dru', 'wb') as f:
                f.write(data[2])

    @staticmethod
    def load_sch_title_block():
        if GS.sch_title is not None:
            return
        assert GS.sch is not None
        GS.sch_title = GS.sch.title
        GS.sch_date = GS.sch.date
        GS.sch_rev = GS.sch.revision
        GS.sch_comp = GS.sch.company
        GS.sch_com = GS.sch.comment

    @staticmethod
    def format_date(d, fname, what):
        if not d:
            return datetime.fromtimestamp(os.path.getmtime(fname)).strftime(GS.global_date_time_format)
        elif GS.global_time_reformat:
            try:
                dt = datetime.fromisoformat(d)
            except ValueError as e:
                logger.warning(W_DATEFORMAT+"Trying to reformat {} time, but not in ISO format ({})".format(what, d))
                logger.warning(W_DATEFORMAT+"Problem: {}".format(e))
                logger.warning(W_DATEFORMAT+"You should enter the date in the title block using YYYY-MM-DD format")
                logger.warning(W_DATEFORMAT+"Then adjust `date_time_format` global variable to your preference")
                return d
            return dt.strftime(GS.global_date_format)
        return d

    @staticmethod
    def get_pcb_comment(title_block, num):
        if GS.ki6:
            # Backward compatibility ... what's this?
            # Also: Maintaining the same numbers used before (and found in the file) is asking too much?
            return title_block.GetComment(num)
        if num == 0:
            return title_block.GetComment1()
        if num == 1:
            return title_block.GetComment2()
        if num == 2:
            return title_block.GetComment3()
        if num == 3:
            return title_block.GetComment4()
        return ''

    @staticmethod
    def p2v_k7(point):
        """ KiCad v7 changed various wxPoint args to VECTOR2I.
            This helper changes the types accordingly """
        if GS.ki8:
            return pcbnew.VECTOR2I(point.x, point.y)
        elif GS.ki7:
            return pcbnew.VECTOR2I(point)
        return point

    def angle(ang):
        if hasattr(pcbnew, 'EDA_ANGLE'):
            # Here we can't use KiCad version because the nasty pcb_transition can be patching it
            return pcbnew.EDA_ANGLE(ang*10, pcbnew.TENTHS_OF_A_DEGREE_T)
        return ang*10

    def angle_as_double(ang):
        if isinstance(ang, float):
            return ang
        # Here we can't use KiCad version because the nasty pcb_transition can be patching it
        return ang.AsDegrees()

    @staticmethod
    def get_modules():
        if GS.ki6:
            return GS.board.GetFootprints()
        return GS.board.GetModules()

    @staticmethod
    def get_modules_board(board):
        if GS.ki6:
            return board.GetFootprints()
        return board.GetModules()

    @staticmethod
    def get_aux_origin():
        if GS.board is None:
            return (0, 0)
        if GS.ki6:
            settings = GS.board.GetDesignSettings()
            return settings.GetAuxOrigin()
        return GS.board.GetAuxOrigin()

    @staticmethod
    def get_center(m):
        if GS.ki5:
            return m.GetCenter()
        return m.GetPosition()

    @staticmethod
    def get_fp_size(m):
        if GS.ki5:
            pads = m.Pads()
            r = pcbnew.EDA_RECT()
            for pad in pads:
                r.Merge(pad.GetBoundingBox())
            rot = m.GetOrientationDegrees()
            if rot == 270 or rot == 90:
                return (r.GetHeight(), r.GetWidth())
            return (r.GetWidth(), r.GetHeight())
        # KiCad 6
        r = m.GetFpPadsLocalBbox()
        return (r.GetWidth(), r.GetHeight())

    @staticmethod
    def unit_name_to_scale_factor(units):
        if units == 'millimeters' or units == 'mm':
            return 1.0/IU_PER_MM
        if units == 'mils':
            return 1.0/IU_PER_MILS
        # Inches
        return 0.001/IU_PER_MILS

#     @staticmethod
#     def unit_name_to_abrev(units):
#         if units == 'millimeters':
#             return 'mm'
#         if units == 'mils':
#             return 'mils'
#         # Inches
#         return 'in'

    @staticmethod
    def to_mm(val):
        return float(val)/IU_PER_MM

    @staticmethod
    def from_mm(val):
        return int(val*IU_PER_MM)

    @staticmethod
    def to_mils(val):
        return val/IU_PER_MILS

#     @staticmethod
#     def to_global_units(val):
#         scale = GS.unit_name_to_scale_factor(GS.global_units)
#         return str(val*scale)+' '+GS.unit_name_to_abrev(GS.global_units)

    @staticmethod
    def make_bkp(fname):
        bkp = fname+'-bak'
        if os.path.isfile(fname):
            os.replace(fname, bkp)

    @staticmethod
    def zones():
        return pcbnew.ZONES() if GS.ki6 else pcbnew.ZONE_CONTAINERS()

    @staticmethod
    def layers_contains(layers, id):
        if GS.ki6:
            return layers.Contains(id)
        return id in layers.Seq()

    @staticmethod
    def zone_get_first_layer(e):
        return e.GetFirstLayer() if GS.ki7 else e.GetLayer()

    @staticmethod
    def footprint_update_local_coords_ki7(fp):
        fp.SetLocalCoord()  # Update the local coordinates

    @staticmethod
    def dummy1(fp):
        """ KiCad 8 doesn't need footprint_update_local_coords """

    @staticmethod
    def expand_text_variables(text, extra_vars=None):
        vars = GS.load_pro_variables()
        new_text = ''
        last = 0
        text_l = len(text)
        for match in GS.vars_regex.finditer(text):
            vname = match.group(1)
            value = vars.get(vname, None)
            if value is None and extra_vars is not None:
                value = extra_vars.get(vname, None)
            if value is None and GS.global_use_os_env_for_expand:
                value = os.environ.get(vname, None)
            if value is None:
                value = '${'+vname+'}'
                logger.warning(W_UNKVAR+"Unknown text variable `{}`".format(vname))
            if match.start():
                new_text += text[last:match.start()]
            new_text += value
            last = match.end()
        if last < text_l:
            new_text += text[last:text_l]
        if new_text != text:
            if GS.debug_level > 3:
                logger.debug('Replacing KiCad text variables: {} -> {}'.format(text, new_text))
        return new_text

    @staticmethod
    def load_pcb_title_block():
        if GS.pcb_title is not None:
            return
        GS.pcb_title = ''
        GS.pcb_date = ''
        GS.pcb_rev = ''
        GS.pcb_comp = ''
        # This is based on InterativeHtmlBom expansion
        title_block = GS.board.GetTitleBlock()
        GS.pcb_date = GS.format_date(GS.expand_text_variables(title_block.GetDate()), GS.pcb_file, 'PCB')
        GS.pcb_title = GS.expand_text_variables(title_block.GetTitle())
        if not GS.pcb_title:
            GS.pcb_title = GS.pcb_basename
        GS.pcb_rev = GS.expand_text_variables(title_block.GetRevision())
        GS.pcb_comp = GS.expand_text_variables(title_block.GetCompany())
        for num in range(9):
            GS.pcb_com[num] = GS.expand_text_variables(GS.get_pcb_comment(title_block, num))
        logger.debug("PCB title: `{}`".format(GS.pcb_title))
        logger.debug("PCB date: `{}`".format(GS.pcb_date))
        logger.debug("PCB revision: `{}`".format(GS.pcb_rev))
        logger.debug("PCB company: `{}`".format(GS.pcb_comp))
        for num in range(4 if GS.ki5 else 9):
            logger.debug("PCB comment {}: `{}`".format(num+1, GS.pcb_com[num]))

    @staticmethod
    def check_pcb():
        if not GS.pcb_file:
            GS.exit_with_error('No PCB file found (*.kicad_pcb), use -b to specify one.', EXIT_BAD_ARGS)

    @staticmethod
    def check_sch():
        if not GS.sch_file:
            GS.exit_with_error('No SCH file found (*.sch), use -e to specify one.', EXIT_BAD_ARGS)

    @staticmethod
    def check_pro():
        if not GS.pro_file:
            GS.exit_with_error('No project file found (*.kicad_pro/*.pro).', EXIT_BAD_ARGS)

    @staticmethod
    def copy_project(new_pcb_name, dry=False):
        pro_name = GS.pro_file
        if pro_name is None or not os.path.isfile(pro_name):
            return None, None, None
        pro_copy = os.path.splitext(new_pcb_name)[0]+GS.pro_ext
        if not dry:
            logger.debug(f'Copying project `{pro_name}` to `{pro_copy}`')
            copy2(pro_name, pro_copy)
        # Also copy the PRL
        prl_name = pro_name[:-3]+'prl'
        prl_copy = None
        if os.path.isfile(prl_name):
            prl_copy = pro_copy[:-3]+'prl'
            if not dry:
                logger.debug(f'Copying project local settings `{prl_name}` to `{prl_copy}`')
                copy2(prl_name, prl_copy)
        # ... and the DRU
        dru_name = pro_name[:-3]+'dru'
        dru_copy = None
        if os.path.isfile(dru_name):
            dru_copy = pro_copy[:-3]+'dru'
            if not dry:
                logger.debug(f'Copying project custom design rules `{dru_name}` to `{dru_copy}`')
                copy2(dru_name, dru_copy)
        return pro_copy, prl_copy, dru_copy

    @staticmethod
    def copy_project_names(pcb_name, ref_dir):
        pro_copy, prl_copy, dru_copy = GS.copy_project(pcb_name, dry=True)
        files = []
        if pro_copy:
            files.append(os.path.join(ref_dir, os.path.basename(pro_copy)))
        if prl_copy:
            files.append(os.path.join(ref_dir, os.path.basename(prl_copy)))
        if dru_copy:
            files.append(os.path.join(ref_dir, os.path.basename(dru_copy)))
        return files

    @staticmethod
    def copy_project_sch(sch_dir):
        """ Copy the project file to the temporal dir """
        ext = GS.pro_ext
        source = GS.pro_file
        prj_file = os.path.join(sch_dir, GS.sch_basename+ext)
        if source is not None and os.path.isfile(source):
            logger.debug('Copying project `{}` to `{}`'.format(source, prj_file))
            copy2(source, prj_file)
            GS.fix_page_layout(prj_file)  # Alias for KiConf.fix_page_layout
        else:
            logger.debug('Creating dummy project file `{}`'.format(prj_file))
            # Create a dummy project file to avoid warnings
            f = open(prj_file, 'wt')
            f.close()

    @staticmethod
    def get_pcb_and_pro_names(name):
        n = os.path.splitext(name)[0]
        if GS.ki5:
            return [name, n+'.pro']
        # All possible names, not just the ones that exist, they could be created in the process
        # When removing we check they actually exist
        return [name, n+'.kicad_pro', n+'.kicad_pro-bak', n+'.kicad_prl', n+'.kicad_prl-bak', n+'.kicad_dru',
                n+'.kicad_dru-bak']

    @staticmethod
    def remove_pcb_and_pro(name):
        """ Used to remove temporal PCB and project files """
        for fn in GS.get_pcb_and_pro_names(name):
            if os.path.isfile(fn):
                os.remove(fn)

    @staticmethod
    def load_board():
        """ Will be repplaced by kiplot.py """
        raise AssertionError()

    @staticmethod
    def exec_with_retry():
        """ Will be repplaced by kiplot.py """
        raise AssertionError()

    @staticmethod
    def load_board_low_level(file):
        with hide_stderr():
            board = pcbnew.LoadBoard(file)
        return board

    @staticmethod
    def load_sch():
        """ Will be repplaced by kiplot.py """
        raise AssertionError()

    @staticmethod
    def get_useful_layers(useful, layers, include_copper=False):
        """ Filters layers selecting the ones from useful """
        from .layer import Layer
        if include_copper:
            # This is a list of layers that we could add
            useful = {la._id for la in Layer.solve(useful)}
            # Now filter the list of layers using the ones we are interested on
            return [la for la in layers if (include_copper and la.is_copper()) or la._id in useful]
        # Similar but keeping the sorting of useful
        use = {la._id for la in layers}
        return [la for la in Layer.solve(useful) if la._id in use]

    @staticmethod
    def ensure_tool(context, name):
        """ Looks for a mandatory dependency """
        return GS.check_tool_dep(context, name, fatal=True)

    @staticmethod
    def check_tool(context, name):
        """ Looks for a dependency """
        return GS.check_tool_dep(context, name, fatal=False)

    @staticmethod
    def reload_project(pro_name):
        if pro_name is None:
            return
        sm = pcbnew.GetSettingsManager()
        sm.UnloadProject(GS.board.GetProject(), False)
        assert sm.LoadProject(pro_name)
        # If we use the old project KiCad SIGSEGV
        GS.board = None

    @staticmethod
    def get_resource_path(name):
        # Try relative to the script
        dir_name = os.path.join(os.path.dirname(__file__), 'resources', name)
        if os.path.isdir(dir_name):
            return dir_name
        # Try using the system level path
        dir_name = os.path.join(os.path.sep, 'usr', 'share', 'kibot', name)
        if os.path.isdir(dir_name):
            return dir_name
        GS.exit_with_error('Missing resource directory `{}`'.format(name), WRONG_INSTALL)

    @staticmethod
    def create_eda_rect(tlx, tly, brx, bry):
        if GS.ki9:
            # TODO: Might be fixed in the release
            return pcbnew.BOX2I(pcbnew.VECTOR2I(tlx, tly), pcbnew.VECTOR2L(brx-tlx, bry-tly))
        if GS.ki7:
            return pcbnew.BOX2I(pcbnew.VECTOR2I(tlx, tly), pcbnew.VECTOR2I(brx-tlx, bry-tly))
        return pcbnew.EDA_RECT(pcbnew.wxPoint(tlx, tly), pcbnew.wxSize(brx-tlx, bry-tly))

    @staticmethod
    def get_rect_for(bound):
        if GS.ki7:
            pos = bound.GetPosition()
            return pcbnew.wxRect(pcbnew.wxPoint(pos.x, pos.y), pcbnew.wxSize(bound.GetWidth(), bound.GetHeight()))
        return bound.getWxRect()

    @staticmethod
    def get_pad_orientation_in_radians(pad):
        return pad.GetOrientation().AsRadians() if GS.ki7 else pad.GetOrientationRadians()

    @staticmethod
    def iu_to_svg(values, svg_precision):
        """ Converts 1 or more values from KiCad internal IUs to the units used for SVGs.
            For tuples we assume the result is SVG coordinates, for 1 value a scale """
        if GS.ki5:
            if isinstance(values, tuple):
                return tuple(int(round(x*KICAD5_SVG_SCALE)) for x in values)
            return values*KICAD5_SVG_SCALE
        if GS.ki7:
            if isinstance(values, tuple):
                return tuple(map(GS.to_mm, values))
            return GS.to_mm(values)
        # KiCad 6
        mult = 10.0 ** (svg_precision - 6)
        if isinstance(values, tuple):
            return tuple(int(round(x*mult)) for x in values)
        return values*mult

    @staticmethod
    def svg_round(val):
        """ KiCad 5/6 uses integers for SVG units, KiCad 7 uses mm and hence floating point """
        if GS.ki7:
            return val
        return int(round(val))

    # @staticmethod
    # def create_wxpoint(x, y):
    #     return pcbnew.wxPoint(x, y)

    @staticmethod
    def is_valid_pcb_shape(g):
        return g.GetShape() != pcbnew.S_SEGMENT or g.GetLength() > 0

    @staticmethod
    def v2p(v):
        if GS.ki7:
            return pcbnew.wxPoint(v.x, v.y)
        return v

    @staticmethod
    def get_start_point(g):
        shape = g.GetShape()
        if GS.ki6:
            if shape == pcbnew.S_CIRCLE:
                # Circle start is circle center
                return GS.v2p(g.GetStart())+pcbnew.wxPoint(g.GetRadius(), 0)
            return GS.v2p(g.GetStart())
        if shape in [pcbnew.S_ARC, pcbnew.S_CIRCLE]:
            return GS.v2p(g.GetArcStart())
        return GS.v2p(g.GetStart())

    @staticmethod
    def get_end_point(g):
        shape = g.GetShape()
        if GS.ki6:
            if shape == pcbnew.S_CIRCLE:
                # This is closed start == end
                return GS.v2p(g.GetStart())+pcbnew.wxPoint(g.GetRadius(), 0)
            if shape == pcbnew.S_RECT:
                # Also closed start == end
                return GS.v2p(g.GetStart())
            return GS.v2p(g.GetEnd())
        if shape == pcbnew.S_ARC:
            return GS.v2p(g.GetArcEnd())
        if shape == pcbnew.S_CIRCLE:
            return GS.v2p(g.GetArcStart())
        return GS.v2p(g.GetEnd())

    @staticmethod
    def get_shape_bbox(s):
        """ Bounding box without the width of the trace """
        width = s.GetWidth()
        s.SetWidth(0)
        bbox = s.GetBoundingBox()
        s.SetWidth(width)
        return bbox

    @staticmethod
    def create_module_element(m):
        if GS.ki8:
            return pcbnew.PCB_SHAPE(m)
        if GS.ki6:
            return pcbnew.FP_SHAPE(m)
        return pcbnew.EDGE_MODULE(m)

    @staticmethod
    def create_track(parent):
        if GS.ki6:
            return pcbnew.PCB_TRACK(parent)
        return pcbnew.TRACK(parent)

    @staticmethod
    def create_puntual_track(parent, position, layer):
        track = GS.create_track(parent)
        track.SetStart(position)
        track.SetEnd(position)
        track.SetLayer(layer)
        track.SetWidth(0)
        parent.Add(track)
        return track

    @staticmethod
    def fill_zones(board, zones=None):
        if zones is None:
            zones = board.Zones()
        pcbnew.ZONE_FILLER(board).Fill(zones)
        board.BuildConnectivity()

    @staticmethod
    def get_kiauto_video_name(cmd):
        """ Compute the name for the video captured by KiAuto """
        command = os.path.basename(cmd[0])[:-3]
        subcommand = next(filter(lambda x: x[0] != '-' and (not x[0].isdigit() or x[1] == 'd'), cmd[1:]))
        if command == 'pcbnew':
            return command+'_'+subcommand+'_screencast.ogv'
        if command == 'eeschema':
            return subcommand+'_'+command+'_screencast.ogv'
        return command+'_screencast.ogv'

    @staticmethod
    def add_extra_options(cmd):
        is_gitlab_ci = 'GITLAB_CI' in os.environ
        video_remove = (not GS.debug_enabled) and is_gitlab_ci
        if GS.debug_enabled:
            cmd.insert(1, '-'+'v'*GS.debug_level)
        if GS.debug_enabled or is_gitlab_ci:
            # Forcing record on GitLab CI/CD (black magic)
            cmd.insert(1, '-r')
        if GS.global_kiauto_time_out_scale:
            cmd.insert(1, str(GS.global_kiauto_time_out_scale))
            cmd.insert(1, '--time_out_scale')
        if GS.global_kiauto_wait_start:
            cmd.insert(1, str(GS.global_kiauto_wait_start))
            cmd.insert(1, '--wait_start')
        return cmd, video_remove

    @staticmethod
    def SetExcludeEdgeLayer(po, exclude_edge_layer):
        if not GS.ki7:
            po.SetExcludeEdgeLayer(exclude_edge_layer)

    @staticmethod
    def SetSvgPrecision(po, svg_precision):
        if GS.ki7:
            po.SetSvgPrecision(svg_precision)
        elif GS.ki6:
            po.SetSvgPrecision(svg_precision, False)
        # No ki5 equivalent

    @staticmethod
    def trace_dump():
        if GS.debug_enabled:
            logger.error('Trace stack:')
            (type, value, traceback) = exc_info()
            if traceback is None:
                print(''.join(format_list(extract_stack()[:-2])))
            else:
                print_tb(traceback)

    @staticmethod
    def exit_with_error(msg, level, run_error=None, hints=None):
        GS.trace_dump()
        if isinstance(msg, (tuple, list)):
            for m in msg:
                logger.error(m)
        elif msg:
            logger.error(msg)
        if run_error:
            if not msg:
                logger.error('Running {} returned {}'.format(run_error.cmd, run_error.returncode))
            if run_error.output:
                out = run_error.output.decode()
                logger.debug('- Output from command: '+out)
                if hints:
                    for h in hints:
                        if h[0] in out:
                            logger.error(h[1])
        if level >= 0:
            exit(level)

    @staticmethod
    def get_shape(shape):
        if GS.ki6:
            return shape.ShowShape()
        return shape.ShowShape(shape.GetShape())

    @staticmethod
    def create_fp_lib(lib_name):
        """ Create a new footprints lib. You must provide a path.
            Doesn't fail if the lib is there.
            .pretty extension is forced. """
        if not lib_name.endswith('.pretty'):
            lib_name += '.pretty'
        # FootprintLibCreate(PATH) doesn't check if the lib is there and aborts (no Python exception) if the directory exists
        # So you must check it first and hence the abstraction is lost.
        # This is why we just use os.makedirs
        os.makedirs(lib_name, exist_ok=True)
        return lib_name

    @staticmethod
    @contextmanager
    def create_file(name, bin=False):
        os.makedirs(os.path.dirname(name), exist_ok=True)
        with open(name, 'wb' if bin else 'w') as f:
            yield f

    @staticmethod
    def write_to_file(content, name):
        with GS.create_file(name, bin=isinstance(content, bytes)) as f:
            f.write(content)

    @staticmethod
    def get_fields(footprint):
        """ Returns a dict with the field/value for the fields in a FOOTPRINT (aka MODULE) """
        if GS.ki8:
            # KiCad 8 defines a special object (PCB_FIELD) and its iterator
            return {f.GetName(): f.GetText() for f in footprint.GetFields()}
        if GS.ki6:
            return footprint.GetProperties()
        # KiCad 5 didn't have fields in the modules
        return {}

    @staticmethod
    def set_fields(footprint, flds):
        """ Sets the fields in a FOOTPRINT (aka MODULE) from a dict """
        if GS.ki8:
            new_fields = [fld for fld in flds.keys() if not footprint.HasField(fld)]
            footprint.SetFields(flds)
            # New fields are added as visible, so we must hide them (OMG!)
            for fld in new_fields:
                footprint.GetFieldByName(fld).SetVisible(False)
        elif GS.ki6:
            footprint.SetProperties(flds)

    @staticmethod
    def get_shown_text(obj, allow_extra_text=True, a_depth=0):
        if GS.ki8:  # 8
            return obj.GetShownText(allow_extra_text, a_depth)
        if GS.ki7:  # 7
            return obj.GetShownText()
        if GS.ki6:  # 6
            return obj.GetShownText(a_depth, allow_extra_text)
        return obj.GetShownText()  # 5

    @staticmethod
    def compute_group_boundary(g):
        x1 = y1 = x2 = y2 = None
        for item in g.GetItems():
            bb = GS.get_shape_bbox(item) if hasattr(item, 'GetWidth') else item.GetBoundingBox()
            start = bb.GetOrigin()
            end = bb.GetEnd()
            if x1 is None:
                x1 = x2 = start.x
                y1 = y2 = start.y
            for p in [start, end]:
                x2 = max(x2, p.x)
                y2 = max(y2, p.y)
                x1 = min(x1, p.x)
                y1 = min(y1, p.y)
        return x1, y1, x2, y2

    @staticmethod
    def compute_pcb_boundary(board):
        edge_layer = board.GetLayerID('Edge.Cuts')
        x1 = y1 = x2 = y2 = None
        for d in board.GetDrawings():
            if d.GetClass() == GS.board_gr_type and d.GetLayer() == edge_layer:
                bb = GS.get_shape_bbox(d)
                start = bb.GetOrigin()
                end = bb.GetEnd()
                if x1 is None:
                    x1 = x2 = start.x
                    y1 = y2 = start.y
                for p in [start, end]:
                    x2 = max(x2, p.x)
                    y2 = max(y2, p.y)
                    x1 = min(x1, p.x)
                    y1 = min(y1, p.y)
        # This is a special case: the PCB edges are in a footprint
        for m in GS.get_modules():
            for gi in m.GraphicalItems():
                if gi.GetClass() == GS.footprint_gr_type and gi.GetLayer() == edge_layer:
                    bb = GS.get_shape_bbox(gi)
                    start = bb.GetOrigin()
                    end = bb.GetEnd()
                    if x1 is None:
                        x1 = x2 = start.x
                        y1 = y2 = start.y
                    for p in [start, end]:
                        x2 = max(x2, p.x)
                        y2 = max(y2, p.y)
                        x1 = min(x1, p.x)
                        y1 = min(y1, p.y)
        return x1, y1, x2, y2

    @staticmethod
    def tmp_file(content=None, prefix=None, suffix=None, dir=None, what=None, a_logger=None, binary=False, indent=False):
        mode = 'wb' if binary else 'wt'
        prefix = 'kibot_'+(prefix if prefix is not None else '')
        with tempfile.NamedTemporaryFile(mode=mode, delete=False, suffix=suffix, prefix=prefix, dir=dir) as f:
            if what is not None:
                if a_logger is None:
                    a_logger = logger
                a_logger.debug(('- ' if indent else '')+f'Writing {what} to {f.name}')
            if content:
                f.write(content)
        return f.name

    @staticmethod
    def mkdtemp(mod):
        return tempfile.mkdtemp(prefix='tmp-kibot-'+mod+'-')

    @staticmethod
    def set_global_options_tree(tree):
        glb = GS.class_for_global_opts()
        glb.set_tree(tree)
        GS.globals_tree = tree
        return glb

    @staticmethod
    def save_pcb(pcb_file=None, board=None):
        if pcb_file is None:
            pcb_file = GS.pcb_file
        if board is None:
            board = GS.board
        GS.make_bkp(pcb_file)
        # KiCad likes to write the project every time we save the PCB
        # But KiCad doesn't read the exclusions, so they get lost
        # As a workaround we restore the project, there is no need to change it
        prj = GS.read_pro()
        board.Save(pcb_file)
        GS.write_pro(prj)

    # Naive stop mechanism, abstracted in case we need something more complex
    @staticmethod
    def reset_stop_flag():
        GS.stop_flag = False

    @staticmethod
    def set_stop_flag():
        GS.stop_flag = True

    @staticmethod
    def get_stop_flag():
        return GS.stop_flag

    @staticmethod
    def move_board_items(vector):
        any((x.Move(vector) for x in GS.get_modules()))
        any((x.Move(vector) for x in GS.board.GetDrawings()))
        any((x.Move(vector) for x in GS.board.GetTracks()))
        any((x.Move(vector) for x in GS.board.Zones()))

    @staticmethod
    def sanitize_file_name(name):
        # sanitize the name to avoid characters illegal in file systems
        if GS.on_windows:
            # Here \ *is* valid
            if len(name) >= 2 and name[0].isalpha() and name[1] == ':':
                # This name starts with a drive letter, : is valid in the first 2
                name = name[:2]+re.sub(INVALID_CHARS, '_', name[2:])
            else:
                name = re.sub(INVALID_CHARS, '_', name)
        else:
            name = name.replace('\\', '/')
            name = re.sub(INVALID_CHARS, '_', name)
        return name

    @staticmethod
    def module_position(m):
        pos = GS.get_center(m)
        return f'({GS.to_mm(pos.x)}, {GS.to_mm(pos.y)}) mm'

    @staticmethod
    def layer_is_inner(id):
        return pcbnew.IsInnerCopperLayer(id) if GS.ki9 else id > pcbnew.F_Cu and id < pcbnew.B_Cu

    @staticmethod
    def inner_layer_index(id):
        return int(id/2-1) if GS.ki9 else id-pcbnew.F_Cu+1

    @staticmethod
    def copper_layer_to_ordinal(n):
        ordinal = pcbnew.CopperLayerToOrdinal(n)
        # Adjust to the current PCB
        if ordinal == pcbnew.CopperLayerToOrdinal(pcbnew.B_Cu):
            ordinal = GS.board.GetCopperLayerCount()-1
        return ordinal

    @staticmethod
    def ordinal_to_copper_layer(n):
        if n == GS.board.GetCopperLayerCount()-1:
            return pcbnew.B_Cu
        if n == 0:
            return pcbnew.F_Cu
        return (n+1)*2

    @staticmethod
    def get_via_width(via):
        if not GS.ki9:
            return via.GetWidth()
        # On KiCad 9 we can have a different width for each layer
        # To potentially support more than 32 layers (and they aren't currently supported) the code became a nightmare
        start = GS.copper_layer_to_ordinal(via.TopLayer())
        end = GS.copper_layer_to_ordinal(via.BottomLayer())
        res = [via.GetWidth(GS.ordinal_to_copper_layer(layer)) for layer in range(start, end+1)]
        return res

    @staticmethod
    def set_via_width(via, w):
        if not GS.ki9:
            return via.SetWidth(w)
        # On KiCad 9 we can have a different width for each layer
        # To potentially support more than 32 layers (and they aren't currently supported) the code became a nightmare
        start = GS.copper_layer_to_ordinal(via.TopLayer())
        end = GS.copper_layer_to_ordinal(via.BottomLayer())
        if not isinstance(w, list):
            w = [w]*(end-start+1)
        for layer, width in zip(range(start, end+1), w):
            via.SetWidth(GS.ordinal_to_copper_layer(layer), width)

    @staticmethod
    def get_embed_dir(fname):
        ki_ver = f'{GS.kicad_version_major}.{GS.kicad_version_minor}'
        if GS.on_windows:
            return os.path.expanduser(os.path.join('~', 'AppData', 'Local', 'KiCad', ki_ver, 'embed', fname))
        return os.path.expanduser(os.path.join('~', '.cache', 'kicad', ki_ver, 'embed', fname))
