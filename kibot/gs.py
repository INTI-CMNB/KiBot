# -*- coding: utf-8 -*-
# Copyright (c) 2020-2022 Salvador E. Tropea
# Copyright (c) 2020-2022 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
from __future__ import annotations
import os
try:
    import pcbnew
except ImportError:
    # This is caught by __main__, ignore the error here
    class pcbnew(object):  # type:ignore[no-redef]
        pass
from datetime import datetime, date
from sys import exit
from .misc import EXIT_BAD_ARGS, W_DATEFORMAT, KICAD_VERSION_5_99
from .log import get_logger

logger = get_logger(__name__)


class GS(object):
    """
    Class to keep the global settings.
    Is a static class, just a placeholder for some global variables.
    """
    # PCB name and useful parts
    pcb_file = None      # /.../dir/pcb.kicad_pcb  ## type: str
    pcb_no_ext = None    # /.../dir/pcb  ## type: str
    pcb_dir = None       # /.../dir  ## type: str
    pcb_basename = None  # pcb  ## type: str
    # SCH name and useful parts
    sch_file = None      # /.../dir/file.sch  ## type: str
    sch_no_ext = None    # /.../dir/file  ## type: str
    sch_dir = None       # /.../dir  ## type: str
    sch_basename = None  # file  ## type: str
    # Main output dir
    out_dir = None       ## type: str
    out_dir_in_cmd_line = False
    filter_file = None
    board = None
    sch = None
    debug_enabled = False
    debug_level = 0
    kibot_version = None
    n = datetime.now()
    kicad_version = ''        ## type: str
    kicad_conf_path = None    ## type: str
    kicad_share_path = None   ## type: str
    kicad_dir = 'kicad'       ## type: str
    kicad_plugins_dirs = []   ## type: list[str]
    pro_ext = '.pro'          ## type: str
    work_layer = 'Rescue'     ## type: str
    # KiCad version: major*1e6+minor*1e3+patch
    kicad_version_n = 0
    kicad_version_major = 0
    kicad_version_minor = 0
    kicad_version_patch = 0
    # Data from the SCH because it doesn't have a Python API
    sch_title = None          ## type: str
    sch_date = None           ## type: str
    sch_rev = None            ## type: str
    sch_comp = None           ## type: str
    sch_com = [None]*9
    # Data from the board title block
    pcb_title = None          ## type: str
    pcb_date = None           ## type: str
    pcb_rev = None            ## type: str
    pcb_comp = None           ## type: str
    pcb_com = [None]*9
    # Current variant/s
    variant = None
    # All the outputs
    outputs = None
    # Name for the output we are generating
    current_output = None    ## type: str
    # Global defaults
    #  This is used as default value for classes supporting "output" option
    def_global_output = '%f-%i%I%v.%x'
    #  This value will overwrite GS.def_global_output if defined
    #  Classes supporting global "output" option must call super().__init__()
    #  after defining its own options to allow Optionable do the overwrite.
    global_from_cli = {}
    global_output = None
    global_dir = None
    global_variant = None
    global_units = None
    solved_global_variant = None
    global_kiauto_wait_start = None
    global_kiauto_time_out_scale = None
    global_opts_class = None  ## type: globals
    global_3D_model_field = '_3D_model'
    global_date_time_format = None  ## type: str
    global_date_format = None  ## type: str
    global_time_format = None  ## type: str
    global_time_reformat = None
    global_pcb_material = None
    global_solder_mask_color = None  ## type: str
    global_solder_mask_color_top = None  ## type: str
    global_solder_mask_color_bottom = None  ## type: str
    global_silk_screen_color = None  ## type: str
    global_silk_screen_color_top = None  ## type: str
    global_silk_screen_color_bottom = None  ## type: str
    global_pcb_finish = None
    global_copper_thickness = None
    global_edge_connector = None
    global_castellated_pads = None
    global_edge_plating = None
    global_impedance_controlled = None
    test_boolean = True
    stackup = None

    @staticmethod
    def set_sch(name):
        if name:
            name = os.path.abspath(name)
            GS.sch_file = name
            GS.sch_basename = os.path.splitext(os.path.basename(name))[0]
            GS.sch_no_ext = os.path.splitext(name)[0]
            GS.sch_dir = os.path.dirname(name)

    @staticmethod
    def set_pcb(name):
        if name:
            name = os.path.abspath(name)
            GS.pcb_file = name
            GS.pcb_basename = os.path.splitext(os.path.basename(name))[0]
            GS.pcb_no_ext = os.path.splitext(name)[0]
            GS.pcb_dir = os.path.dirname(name)

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
                dt = date.fromisoformat(d)
            except ValueError as e:
                logger.warning(W_DATEFORMAT+"Trying to reformat {} time, but not in ISO format ({})".format(what, d))
                logger.warning(W_DATEFORMAT+"Problem: {}".format(e))
                return d
            return dt.strftime(GS.global_date_format)
        return d

    @staticmethod
    def get_pcb_comment(title_block, num):
        if GS.ki6():
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
    def get_modules():
        if GS.ki6():
            return GS.board.GetFootprints()
        return GS.board.GetModules()

    @staticmethod
    def get_modules_board(board):
        if GS.ki6():
            return board.GetFootprints()
        return board.GetModules()

    @staticmethod
    def get_aux_origin():
        if GS.board is None:
            return (0, 0)
        if GS.ki6():
            settings = GS.board.GetDesignSettings()
            return settings.GetAuxOrigin()
        return GS.board.GetAuxOrigin()

    @staticmethod
    def get_center(m):
        if GS.ki5():
            return m.GetCenter()
        return m.GetPosition()

    @staticmethod
    def get_fp_size(m):
        if GS.ki5():
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
        if units == 'millimeters':
            return 1.0/pcbnew.IU_PER_MM
        if units == 'mils':
            return 1.0/pcbnew.IU_PER_MILS
        # Inches
        return 0.001/pcbnew.IU_PER_MILS

    @staticmethod
    def ki6():
        return GS.kicad_version_n >= KICAD_VERSION_5_99

    @staticmethod
    def ki5():
        return GS.kicad_version_n < KICAD_VERSION_5_99

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
        GS.pcb_date = GS.format_date(title_block.GetDate(), GS.pcb_file, 'PCB')
        GS.pcb_title = title_block.GetTitle()
        if not GS.pcb_title:
            GS.pcb_title = GS.pcb_basename
        GS.pcb_rev = title_block.GetRevision()
        GS.pcb_comp = title_block.GetCompany()
        for num in range(9):
            GS.pcb_com[num] = GS.get_pcb_comment(title_block, num)
        logger.debug("PCB title: `{}`".format(GS.pcb_title))
        logger.debug("PCB date: `{}`".format(GS.pcb_date))
        logger.debug("PCB revision: `{}`".format(GS.pcb_rev))
        logger.debug("PCB company: `{}`".format(GS.pcb_comp))
        for num in range(4 if GS.ki5() else 9):
            logger.debug("PCB comment {}: `{}`".format(num+1, GS.pcb_com[num]))

    @staticmethod
    def check_pcb():
        if not GS.pcb_file:
            logger.error('No PCB file found (*.kicad_pcb), use -b to specify one.')
            exit(EXIT_BAD_ARGS)

    @staticmethod
    def check_sch():
        if not GS.sch_file:
            logger.error('No SCH file found (*.sch), use -e to specify one.')
            exit(EXIT_BAD_ARGS)

    @staticmethod
    def load_board():
        """ Will be replaced by kiplot.py """
        assert False

    @staticmethod
    def load_sch():
        """ Will be replaced by kiplot.py """
        assert False
