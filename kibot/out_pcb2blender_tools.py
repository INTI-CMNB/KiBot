# -*- coding: utf-8 -*-
# Copyright (c) 2023-2025 Salvador E. Tropea
# Copyright (c) 2023-2025 Instituto Nacional de Tecnología Industrial
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)
# Some code is adapted from: https://github.com/30350n/pcb2blender
from dataclasses import dataclass, field
from enum import IntEnum, Enum
import json
import os
import re
import struct
from typing import List
from .gs import GS
from pcbnew import B_Paste, F_Paste, PCB_TEXT_T, ToMM
if GS.ki6:
    from pcbnew import PAD_PROP_HEATSINK
from .misc import (MOD_THROUGH_HOLE, MOD_SMD, UI_VIRTUAL, W_UNKPCB3DTXT, W_NOPCB3DBR, W_NOPCB3DTL, W_BADPCB3DTXT,
                   W_UNKPCB3DNAME, W_BADPCB3DSTK, MISSING_TOOL)
from .optionable import Optionable
from .out_base import VariantOptions
from .macros import macros, document, output_class  # noqa: F401
from . import log

logger = log.get_logger()


def is_heatsink_pad(pad):
    if not GS.ki6:
        return False
    return pad.GetProperty() == PAD_PROP_HEATSINK


@dataclass
class StackedBoard:
    """ Name and position of a stacked board """
    name: str
    offset: List[float]


@dataclass
class BoardDef:
    """ A sub-PCBs, its bounds and stacked boards """
    name: str
    bounds: List[float]
    stacked_boards: List[StackedBoard] = field(default_factory=list)


class KiCadColor(IntEnum):
    CUSTOM = 0
    GREEN = 1
    RED = 2
    BLUE = 3
    PURPLE = 4
    BLACK = 5
    WHITE = 6
    YELLOW = 7


class SurfaceFinish(IntEnum):
    HASL = 0
    ENIG = 1
    NONE = 2


SURFACE_FINISH_MAP = {
    "ENIG": SurfaceFinish.ENIG,
    "ENEPIG": SurfaceFinish.ENIG,
    "Hard gold": SurfaceFinish.ENIG,
    "ImAu": SurfaceFinish.ENIG,
    "Immersion Gold": SurfaceFinish.ENIG,
    "Immersion Au": SurfaceFinish.ENIG,
    "HT_OSP": SurfaceFinish.NONE,
    "OSP": SurfaceFinish.NONE}


class PadType(Enum):
    UNKNOWN = -1
    THT = 0
    SMD = 1
    CONN = 2
    NPTH = 3


class PadShape(Enum):
    UNKNOWN = -1
    CIRCLE = 0
    RECT = 1
    OVAL = 2
    TRAPEZOID = 3
    ROUNDRECT = 4
    CHAMFERED_RECT = 5
    CUSTOM = 6


class DrillShape(Enum):
    UNKNOWN = -1
    CIRCULAR = 0
    OVAL = 1


class PadFabType(Enum):
    NONE = 0
    BGA = 1
    FIDUCIAL = (2, 3)
    TESTPOINT = 4
    HEATSINK = 5
    CASTELLATED = 6
    MECHANICAL = 7


def sanitized(name):
    """ Replace character that aren't alphabetic by _ """
    return re.sub(r"[\W]+", "_", name)


class PCB2Blender_ToolsOptions(VariantOptions):
    def __init__(self):
        with document:
            self.output = GS.def_global_output
            """ *Filename for the output (%i=pcb2blender, %x=pcb3d) """
            self.board_bounds_create = True
            """ Create the file that informs the size of the used PCB area.
                This is the bounding box reported by KiCad for the PCB edge with 1 mm of margin """
            self.board_bounds_dir = 'layers'
            """ Sub-directory where the bounds file is stored """
            self.board_bounds_file = 'bounds'
            """ Name of the bounds file """
            self.board_bounds_format = 'BIN'
            """ [BIN,TOML] Format for the board bounds file, also sub-boards. Use 'TOML' for 2.17+ """
            self.pads_info_create = True
            """ Create the files containing the PCB pads information """
            self.pads_info_dir = 'pads'
            """ Sub-directory where the pads info files are stored """
            self.pads_info_format = 'BIN'
            """ [BIN,TOML] Format for the pads. Use 'TOML' for 2.17+ """
            self.stackup_create = False
            """ Create a file containing the board stackup """
            self.stackup_file = 'board.yaml'
            """ Name for the stackup file. Use 'stackup' for 2.7+ """
            self.stackup_dir = '.'
            """ Directory for the stackup file. Use 'layers' for 2.7+ """
            self.stackup_format = 'JSON'
            """ [JSON,BIN,TOML] Format for the stackup file. Use 'BIN' for 2.7+ """
            self.sub_boards_create = True
            """ Extract sub-PCBs and their Z axis position """
            self.sub_boards_dir = 'boards'
            """ Directory for the boards definitions """
            self.sub_boards_bounds_file = 'bounds'
            """ File name for the sub-PCBs bounds """
            self.sub_boards_stacked_prefix = 'stacked_'
            """ Prefix used for the stack files """
            self.show_components = Optionable
            """ *[list(string)|string='all'] [none,all,*] List of components to include in the pads list,
                can be also a string for `none` or `all`. Ranges like *R5-R10* are supported """
            self.solder_join_on_heatsink = True
            """ Solder the THT pads with heatsink fabrication attribute """
        super().__init__()
        self._expand_id = 'pcb2blender'
        self._expand_ext = 'pcb3d'

    def config(self, parent):
        super().config(parent)
        self._filters_to_expand = False
        # List of components
        self._show_all_components = False
        if len(self.show_components) == 1 and self.show_components[0] in {'all', 'none'}:
            if self.show_components[0] == 'all':
                self._show_all_components = True
            else:  # if self.show_components[0] == 'none':
                self.show_components = []
        else:  # a list
            self.show_components = self.solve_kf_filters(self.show_components)

    def write_bounds(self, name, format, bounds):
        if format == 'TOML':
            with open(name, 'wt') as f:
                if len(bounds) == 3:
                    f.write(f'offset = {list(bounds)}\n')
                else:
                    f.write(f'top_left = [ {bounds[0]}, {bounds[1]} ]\n')
                    f.write(f'size = [ {bounds[2]}, {bounds[3]} ]\n')
        else:
            with open(name, 'wb') as f:
                # Four/Three big endian float numbers
                f.write(struct.pack("!fff" if len(bounds) == 3 else "!ffff", *bounds))

    def do_board_bounds(self, dir_name):
        if not self.board_bounds_create:
            return
        dir_name = os.path.join(dir_name, self.board_bounds_dir)
        os.makedirs(dir_name, exist_ok=True)
        fname = os.path.join(dir_name, self.board_bounds_file)
        # PCB bounding box using the PCB edge, converted to mm
        bounds = tuple(map(GS.to_mm, GS.get_rect_for(GS.board.ComputeBoundingBox(aBoardEdgesOnly=True))))
        # Apply 1 mm margin (x, y, w, h)
        bounds = (bounds[0]-1, bounds[1]-1, bounds[2]+2, bounds[3]+2)
        self.write_bounds(fname, self.board_bounds_format, bounds)

    @staticmethod
    def is_not_virtual_ki6(m):
        return bool(m.GetAttributes() & (MOD_THROUGH_HOLE | MOD_SMD))

    @staticmethod
    def is_not_virtual_ki5(m):
        return bool(m.GetAttributes() != UI_VIRTUAL)

    def do_pads_info(self, dir_name):
        if not self.pads_info_create:
            return
        dir_name = os.path.join(dir_name, self.pads_info_dir)
        os.makedirs(dir_name, exist_ok=True)
        is_not_virtual = self.is_not_virtual_ki5 if GS.ki5 else self.is_not_virtual_ki6
        for i, footprint in enumerate(GS.get_modules()):
            has_model = len(footprint.Models()) > 0
            is_tht_or_smd = is_not_virtual(footprint)
            value = footprint.GetValue()
            value = value.replace('/', '_')
            reference = footprint.GetReference()
            for j, pad in enumerate(footprint.Pads()):
                if not self.solder_join_on_heatsink and is_heatsink_pad(pad):
                    continue
                name = os.path.join(dir_name, sanitized("{}_{}_{}_{}".format(value, reference, i, j)))
                is_flipped = pad.IsFlipped()
                has_paste = pad.IsOnLayer(B_Paste if is_flipped else F_Paste)
                if self.pads_info_format == 'TOML':
                    with open(name+'.toml', 'wt') as f:
                        f.write(f'position = {list(map(GS.to_mm, pad.GetPosition()))}\n')
                        f.write(f'is_flipped = {str(is_flipped).lower()}\n')
                        f.write(f'has_model = {str(has_model).lower()}\n')
                        f.write(f'is_tht_or_smd = {str(is_tht_or_smd).lower()}\n')
                        f.write(f'has_paste = {str(has_paste).lower()}\n')
                        f.write(f'pad_type = "{PadType(pad.GetAttribute()).name}"\n')
                        f.write(f'shape = "{PadShape(pad.GetShape()).name}"\n')
                        f.write(f'size = {list(map(GS.to_mm, pad.GetSize()))}\n')
                        f.write(f'rotation = {GS.get_pad_orientation_in_radians(pad)}\n')
                        f.write(f'roundness = {pad.GetRoundRectRadiusRatio()}\n')
                        f.write(f'drill_shape = "{DrillShape(pad.GetDrillShape()).name}"\n')
                        f.write(f'drill_size = {list(map(GS.to_mm, pad.GetDrillSize()))}\n')
                        f.write(f'fab_type = "{PadFabType(pad.GetProperty()).name}"\n')
                else:
                    with open(name, 'wb') as f:
                        f.write(struct.pack("!ff????BBffffBff",
                                            *map(GS.to_mm, pad.GetPosition()),
                                            is_flipped,
                                            has_model,
                                            is_tht_or_smd,
                                            has_paste,
                                            pad.GetAttribute(),
                                            pad.GetShape(),
                                            *map(GS.to_mm, pad.GetSize()),
                                            GS.get_pad_orientation_in_radians(pad),
                                            pad.GetRoundRectRadiusRatio(),
                                            pad.GetDrillShape(),
                                            *map(GS.to_mm, pad.GetDrillSize())))

    def parse_kicad_color(self, string):
        if string[0] == "#":
            return KiCadColor.CUSTOM, self.parse_one_color(string, scale=1)[:3]
        else:
            return KiCadColor[string.upper()], (0, 0, 0)

    def do_stackup(self, dir_name):
        if not self.stackup_create or (not GS.global_pcb_finish and not GS.stackup):
            return
        dir_name = os.path.join(dir_name, self.stackup_dir)
        os.makedirs(dir_name, exist_ok=True)
        fname = os.path.join(dir_name, self.stackup_file)
        if self.stackup_format == 'JSON':
            # This is for the experimental "haschtl" fork
            # Create the board_info
            board_info = {}
            if GS.global_pcb_finish:
                board_info['copper_finish'] = GS.global_pcb_finish
            if GS.stackup:
                layers_parsed = []
                for la in GS.stackup:
                    parsed_layer = {'name': la.name, 'type': la.type}
                    if la.color is not None:
                        parsed_layer['color'] = la.color
                    if la.thickness is not None:
                        parsed_layer['thickness'] = la.thickness/1000
                    layers_parsed.append(parsed_layer)
                board_info['stackup'] = layers_parsed
            data = json.dumps(board_info, indent=3)
            logger.debug('Stackup: '+str(data))
            with open(fname, 'wt') as f:
                f.write(data)
        else:  # self.stackup_format == 'BIN'/"TOML":
            # This is for 2.7+
            # Map the surface finish
            if GS.global_pcb_finish:
                surface_finish = SURFACE_FINISH_MAP.get(GS.global_pcb_finish, SurfaceFinish.HASL)
            else:
                surface_finish = SurfaceFinish.NONE
            ds = GS.board.GetDesignSettings()
            thickness_mm = GS.to_mm(ds.GetBoardThickness())
            mask_color, mask_color_custom = self.parse_kicad_color(GS.global_solder_mask_color.upper())
            silks_color, silks_color_custom = self.parse_kicad_color(GS.global_silk_screen_color.upper())
            if self.stackup_format == 'TOML':
                mask_color_custom = [x/255.0 for x in mask_color_custom]
                silks_color_custom = [x/255.0 for x in silks_color_custom]
                with open(fname, 'wt') as f:
                    f.write(f'thickness_mm = {thickness_mm}\n')
                    f.write(f'mask_color = "{mask_color.name}"\n')
                    f.write(f'mask_color_custom = {list(mask_color_custom)}\n')
                    f.write(f'silks_color = "{silks_color.name}"\n')
                    f.write(f'silks_color_custom = {list(silks_color_custom)}\n')
                    f.write(f'surface_finish = "{surface_finish.name}"\n')
            else:
                with open(fname, 'wb') as f:
                    f.write(struct.pack("!fbBBBbBBBb", thickness_mm, mask_color, *mask_color_custom, silks_color,
                                        *silks_color_custom, surface_finish))

    def get_boarddefs(self):
        """ Extract the sub-PCBs and their positions using texts.
            This is the original mechanism and the code is from the plug-in. """
        boarddefs = {}
        tls = {}   # Top Left coordinates
        brs = {}   # Bottom right coordinates
        stacks = {}  # PCB stack relations
        # Collect the information from the texts
        for drawing in GS.board.GetDrawings():
            if drawing.Type() != PCB_TEXT_T:
                continue
            text = drawing.GetText()
            # Only process text starting with PCB3D_
            if not text.startswith("PCB3D_"):
                continue
            # Store the position of the text according to the declared type
            pos = tuple(map(ToMM, drawing.GetPosition()))
            if text.startswith("PCB3D_TL_"):
                tls.setdefault(text[9:], pos)
            elif text.startswith("PCB3D_BR_"):
                brs.setdefault(text[9:], pos)
            elif text.startswith("PCB3D_STACK_"):
                stacks.setdefault(text, pos)
            else:
                logger.warning(W_UNKPCB3DTXT+'Unknown PCB3D mark: `{}`'.format(text))
        # Separate the PCBs
        for name in tls.copy():
            # Look for the Bottom Right corner
            if name in brs:
                # Remove both
                tl_pos = tls.pop(name)
                br_pos = brs.pop(name)
                # Add a definition with the bbox (x, y, w, h)
                boarddef = BoardDef(sanitized(name), (tl_pos[0], tl_pos[1], br_pos[0]-tl_pos[0], br_pos[1]-tl_pos[1]))
                boarddefs[boarddef.name] = boarddef
            else:
                logger.warning(W_NOPCB3DBR+'PCB3D_TL_{} without corresponding PCB3D_BR_{}'.format(name, name))
        for name in brs.keys():
            logger.warning(W_NOPCB3DTL+'PCB3D_BR_{} without corresponding PCB3D_TL_{}'.format(name, name))
        # Solve the stack (relative positions)
        for stack_str in stacks.copy():
            # Extract the parameters
            try:
                other, onto, target, z_offset = stack_str[12:].split("_")
                z_offset = float(z_offset)
            except ValueError:
                onto = ''
            if onto != "ONTO":
                logger.warning(W_BADPCB3DTXT+'Malformed stack marker `{}` must be PCB3D_STACK_other_ONTO_target_zoffset'.
                               format(stack_str))
                continue
            # Check the names and sanity check
            other_name = sanitized(other)    # The name of the current board
            if other_name not in boarddefs and other_name != 'FPNL':
                logger.warning(W_UNKPCB3DNAME+'Unknown `{}` in `{}` valid names are: {}'.
                               format(other_name, stack_str, list(boarddefs)))
                continue
            target_name = sanitized(target)  # The name of the board below
            if target_name not in boarddefs:
                logger.warning(W_UNKPCB3DNAME+'Unknown `{}` in `{}` valid names are: {}'.
                               format(target_name, stack_str, list(boarddefs)))
                continue
            if target_name == other_name:
                logger.warning(W_BADPCB3DSTK+"Can't stack a board onto itself ({})".format(stack_str))
                continue
            # Add this board to the target
            stack_pos = stacks.pop(stack_str)
            target_pos = boarddefs[target_name].bounds[:2]
            stacked = StackedBoard(other_name, (stack_pos[0]-target_pos[0], stack_pos[1]-target_pos[1], z_offset))
            boarddefs[target_name].stacked_boards.append(stacked)
        return boarddefs

    def do_sub_boards(self, dir_name):
        if not self.sub_boards_create:
            return
        dir_name = os.path.join(dir_name, self.sub_boards_dir)
        os.makedirs(dir_name, exist_ok=True)
        boarddefs = self.get_boarddefs()
        logger.debug('Collected board definitions: '+str(boarddefs))
        for boarddef in boarddefs.values():
            subdir = os.path.join(dir_name, boarddef.name)
            os.makedirs(subdir, exist_ok=True)
            self.write_bounds(os.path.join(subdir, self.sub_boards_bounds_file), self.board_bounds_format, boarddef.bounds)
            for stacked in boarddef.stacked_boards:
                self.write_bounds(os.path.join(subdir, self.sub_boards_stacked_prefix+stacked.name),
                                  self.board_bounds_format, stacked.offset)

    def run(self, output):
        super().run(output)
        if GS.ki5:
            GS.exit_with_error("`pcb2blender_tools` needs KiCad 6+", MISSING_TOOL)
        dir_name = os.path.dirname(output)
        self.apply_show_components()
        self.filter_pcb_components(do_3D=True)
        self.do_board_bounds(dir_name)
        self.do_pads_info(dir_name)
        self.do_stackup(dir_name)
        self.do_sub_boards(dir_name)
        self.unfilter_pcb_components(do_3D=True)
        self.undo_show_components()

    def get_targets(self, out_dir):
        # Here we have an interesting case:
        # We are listing the pads, but this needs variants applied.
        # Otherwise a transform filter could invalidate the generated list.
        # So we need to apply the variants.
        self.load_list_components()
        self.apply_show_components()
        self.filter_pcb_components(do_3D=True)
        files = []
        if self.board_bounds_create:
            files.append(os.path.join(out_dir, self.board_bounds_dir, self.board_bounds_file))
        if self.pads_info_create:
            dir_name = os.path.join(out_dir, self.pads_info_dir)
            ext = '.toml' if self.pads_info_format == 'TOML' else ''
            for i, footprint in enumerate(GS.get_modules()):
                value = footprint.GetValue()
                reference = footprint.GetReference()
                for j, pad in enumerate(footprint.Pads()):
                    if not self.solder_join_on_heatsink and is_heatsink_pad(pad):
                        continue
                    files.append(os.path.join(dir_name, sanitized(f"{value}_{reference}_{i}_{j}")+ext))
        if self.stackup_create and (GS.global_pcb_finish or GS.stackup):
            files.append(os.path.join(out_dir, self.stackup_dir, self.stackup_file))
        if self.sub_boards_create:
            dir_name = os.path.join(out_dir, self.sub_boards_dir)
            boarddefs = self.get_boarddefs()
            for boarddef in boarddefs.values():
                subdir = os.path.join(dir_name, boarddef.name)
                files.append(os.path.join(subdir, self.sub_boards_bounds_file))
                for stacked in boarddef.stacked_boards:
                    files.append(os.path.join(subdir, self.sub_boards_stacked_prefix+stacked.name))
            else:
                files.append(dir_name)
        self.unfilter_pcb_components(do_3D=True)
        self.undo_show_components()
        return files


@output_class
class PCB2Blender_Tools(BaseOutput):  # noqa: F821
    """ PCB2Blender Tools
        A bunch of tools used to generate PCB3D files used to export PCBs to Blender.
        Blender is the most important free software 3D render package.
        This output needs KiCad 6 or newer.
        The PCB3D file format is used by the PCB2Blender project (https://github.com/30350n/pcb2blender)
        to import KiCad PCBs in Blender.
        You need to install a Blender plug-in to load PCB3D files.
        The tools in this output are used by internal templates used to generate PCB3D files. """
    def __init__(self):
        super().__init__()
        self._category = 'PCB/3D/Auxiliar'
        with document:
            self.options = PCB2Blender_ToolsOptions
            """ *[dict={}] Options for the `pcb2blender_tools` output """
