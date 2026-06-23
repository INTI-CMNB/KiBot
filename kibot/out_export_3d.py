# -*- coding: utf-8 -*-
# Copyright (c) 2025 Salvador E. Tropea
# Copyright (c) 2025 Instituto Nacional de Tecnología Industrial
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)
import re
from .error import KiPlotConfigurationError
from .misc import UNITS_2_KICAD, MISSING_TOOL
from .kiplot import run_command
from .gs import GS
from .out_base_3d import Base3DOptions, Base3D
from .macros import macros, document, output_class  # noqa: F401
from . import log

logger = log.get_logger()
BOOLEAN_OPS = ('subst_models', 'cut_vias_in_body', 'fill_all_vias', 'board_only', 'no_board_body', 'no_components',
               'include_tracks', 'include_pads', 'include_zones', 'include_inner_copper', 'include_silkscreen',
               'include_soldermask', 'fuse_shapes')


class Export_3DOptions(Base3DOptions):
    def __init__(self):
        with document:
            self.output = GS.def_global_output
            """ *Name for the generated 3D file (%i='3D' %x='step/glb/stl/xao/brep/ply/u3d/pdf') """
            self.format = 'step'
            """ *[step,glb,stl,xao,brep,ply,u3d,pdf] 3D format used.
                - STEP: ISO 10303-21 Clear Text Encoding of the Exchange Structure
                - GLB: Binary version of the glTF, Graphics Library Transmission Format or GL Transmission Format and formerly
                > known as WebGL Transmissions Format or WebGL TF.
                - STL: 3D printer format, from stereolithography CAD software created by 3D Systems.
                - XAO: XAO (SALOME/Gmsh) format, used for FEM and simulations.
                - BRep: Part of Open CASCADE Technology (OCCT)
                - PLY: Polygon File Format or the Stanford Triangle Format (KiCad 10+).
                - U3D: Universal 3D (ECMA-363) primarily used to embed interactive 3D models into PDF documents. (KiCad 10+)
                - PDF: Portable Document Format with the 3D model (KiCad 10+)
                """
            self.origin = 'grid'
            """ *[grid,drill,center,*] Determines the coordinates origin.
                Using `grid` the coordinates are the same as you have in the design sheet.
                The `drill` option uses the auxiliary reference defined by the user.
                Using `center` you'll get the center of the board as origin.
                You can define any other origin using the format 'X,Y', i.e. '3.2,-10'. Don't put units here.
                The units used here are the ones specified by the `units` option """
            self.units = 'millimeters'
            """ [millimeters,inches,mils] Units used for the custom origin and `min_distance`. Affected by global options """
            self.min_distance = -1
            """ The minimum distance between points to treat them as separate ones (-1 is KiCad default: 0.01 mm).
                The units for this option are controlled by the `units` option """
            self.subst_models = True
            """ Substitute STEP or IGS models with the same name in place of VRML models """
            self.cut_vias_in_body = False
            """ Cut via holes in board body even if conductor layers are not exported """
            self.fill_all_vias = False
            """ Don't cut via holes in conductor layers """
            self.board_only = False
            """ Only generate a board with no components """
            self.no_board_body = False
            """ Exclude board body """
            self.no_components = False
            """ Exclude 3D models for components """
            self.include_tracks = False
            """ Export tracks and vias """
            self.include_pads = False
            """ Export pads """
            self.include_zones = False
            """ Export zones """
            self.include_inner_copper = False
            """ Export elements on inner copper layers """
            self.include_silkscreen = False
            """ Export silkscreen graphics as a set of flat faces """
            self.include_soldermask = False
            """ Export soldermask layers as a set of flat faces """
            self.fuse_shapes = False
            """ Fuse overlapping geometry together """
            self.net_filter = ''
            """ Only include copper items belonging to nets matching this wildcard """
            self.no_optimize_step = False
            """ Do not optimize STEP file (enables writing parametric curves) """
        # Temporal dir used to store the downloaded files
        self._tmp_dir = None
        super().__init__()

    def config(self, parent):
        super().config(parent)
        # Validate and parse the origin
        val = self.origin
        if (val not in ['grid', 'drill']):
            if val == 'center':
                bb = GS.board.ComputeBoundingBox(True)
                center = bb.GetCenter()
                self._user_x = GS.to_mm(center.x)
                self._user_y = GS.to_mm(center.y)
                self._units = 'mm'
            else:
                user_origin = re.match(r'([-\d\.]+)\s*,\s*([-\d\.]+)\s*$', val)
                if user_origin is None:
                    raise KiPlotConfigurationError('Origin must be `grid` or `drill` or `X,Y` (no units here)')
                self._user_x = float(user_origin.group(1))
                self._user_y = float(user_origin.group(2))
        # Adjust the units
        if self.origin != 'center':
            self._units = UNITS_2_KICAD[self.units]
        if self._units == 'mils':
            self._units = 'in'
            self._scale = 0.001
        else:
            self._scale = 1.0
        # The format indicates the extension
        self._expand_ext = self.format

    def run(self, output):
        if not GS.ki9:
            GS.exit_with_error("`export_3d` needs KiCad 9+", MISSING_TOOL)
        if self.format in {'ply', 'u3d', 'pdf'} and not GS.ki10:
            GS.exit_with_error(f"`{self.format}` needs KiCad 10+", MISSING_TOOL)
        super().run(output)
        # Make units explicit
        # Base command with overwrite
        format = self.format if self.format != 'pdf' else '3dpdf'
        cmd = [GS.kicad_cli, 'pcb', 'export', format, '-o', output, '-f']
        # Origin
        if self.origin == 'drill':
            cmd.append('--drill-origin')
        elif self.origin == 'grid':
            cmd.append('--grid-origin')
        else:
            cmd.extend(['--user-origin', f"{self._user_x*self._scale}x{self._user_y*self._scale}{self._units}"])
        if self.min_distance >= 0:
            cmd.extend(['--min-distance', f"{self.min_distance*self._scale}{self._units}"])
        if self.net_filter:
            cmd.extend(['--net-filter', self.net_filter])
        for ops in BOOLEAN_OPS:
            if getattr(self, ops):
                cmd.append('--'+ops.replace('_', '-'))
        if self.format == 'step' and self.no_optimize_step:
            cmd.append('--no-optimize-step')
        if self.no_virtual:
            # Is this correct?
            cmd.append('--no-unspecified')
        self.add_kicad_cli_variant(cmd)
        # The board
        board_name = self.filter_components()
        cmd.append(board_name)
        run_command(cmd)
        if self._files_to_remove:
            self.remove_temporals()


@output_class
class Export_3D(Base3D):
    """ 3D models exports of various formats using KiCad (BREP/GLB/STL/STEP/XAO)
        Exports the PCB as a 3D model using KiCad 9 or newer, using kicad-cli.
        Supported formats include:
        - STEP: ISO 10303-21 Clear Text Encoding of the Exchange Structure
        - GLB: Binary version of the glTF, Graphics Library Transmission Format or GL Transmission Format and formerly
        > known as WebGL Transmissions Format or WebGL TF.
        - STL: 3D printer format, from stereolithography CAD software created by 3D Systems.
        - XAO: XAO (SALOME/Gmsh) format, used for FEM and simulations.
        - BRep: Part of Open CASCADE Technology (OCCT)
        STEP is the most common 3D format for exchange purposes
    """
    # OCCT 7.7 needed, how to detect?
    #   - PLY: Polygon File Format or the Stanford Triangle Format.

    # This adds a cross reference in the "step" index entry so people can find `export_3d`
    _extra_index_pairs = [('step', 'export_3d with kicad-cli')]

    def __init__(self):
        super().__init__()
        with document:
            self.options = Export_3DOptions
            """ *[dict={}] Options for the `export_3d` output """
        self._category = 'PCB/3D'

    @staticmethod
    def get_conf_examples(name, layers):
        if not GS.ki9:
            return None
        outs = []
        for o in ('step', 'glb', 'stl', 'xao', 'brep'):
            gb = {}
            gb['name'] = 'basic_'+name+'_'+o
            gb['comment'] = f'3D model in {o.upper()} format'
            gb['type'] = name
            gb['dir'] = '3D'
            gb['options'] = {'format': o}
            outs.append(gb)
        return outs
