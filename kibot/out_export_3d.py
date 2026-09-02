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
            """ *Name for the generated 3D file (%i='3D' %x='step/stpz/glb/stl/xao/brep/ply/u3d/pdf') """
            self.format = 'step'
            """ *[step,stpz,glb,stl,xao,brep,ply,u3d,pdf] 3D format used.
                - STEP: ISO 10303-21 Clear Text Encoding of the Exchange Structure
                - STPZ: Compressed STEP (KiCad 10+)
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
            self.no_extra_pad_thickness = False
            """ Disable extra pad thickness (pads will have normal thickness) (KiCad 10+) """
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
                self._user_x, self._user_y = GS.get_pcb_center_mm()
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

    def run_kicli(self, output):
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
        if GS.ki10 and self.no_extra_pad_thickness:
            cmd.append('--no-extra-pad-thickness')
        self.add_kicad_cli_variant(cmd)
        # The board
        board_name = self.filter_components()
        cmd.append(board_name)
        run_command(cmd)
        if self._files_to_remove:
            self.remove_temporals()

    def run_kipy(self, output):
        """ Not currently used, see run() """
        settings = GS.kp.board_jobs.Export3DSettings()
        settings.format = GS.B3D_FORMAT[self.format]
        kicad_variant = self.kicad_variant_name()
        if kicad_variant:
            settings.variant = kicad_variant
        if self.net_filter:
            settings.net_filter = self.net_filter
        # component_filter this is a regular KiBot filter job
        # include_dnp also seems to be a task for KiBot filters
        # Origin
        settings.has_user_origin = settings.use_grid_origin = settings.use_drill_origin = False
        settings.use_pcb_center_origin = False
        scale = self._scale*25.4 if self._units == 'in' else self._scale
        if self.origin == 'drill':
            settings.use_drill_origin = True
        elif self.origin == 'grid':
            settings.use_grid_origin = True
        else:
            settings.has_user_origin = True
            settings.use_defined_origin = True
            settings.origin = GS.kp.geometry.Vector2.from_xy(GS.from_mm(self._user_x*scale), GS.from_mm(self._user_y*scale))
        settings.overwrite = True
        settings.include_unspecified = not self.no_virtual
        settings.substitute_models = self.subst_models
        if self.min_distance >= 0:
            settings.board_outlines_chaining_epsilon = self.min_distance*scale
        settings.board_only = self.board_only
        settings.cut_vias_in_body = self.cut_vias_in_body
        settings.export_board_body = not self.no_board_body
        settings.export_components = not self.no_components
        settings.export_tracks_and_vias = self.include_tracks
        settings.export_pads = self.include_pads
        settings.export_zones = self.include_zones
        settings.export_inner_copper = self.include_inner_copper
        settings.export_silkscreen = self.include_silkscreen
        settings.export_soldermask = self.include_soldermask
        settings.fuse_shapes = self.fuse_shapes
        settings.fill_all_vias = self.fill_all_vias
        settings.optimize_step = not self.no_optimize_step
        settings.extra_pad_thickness = not self.no_extra_pad_thickness
        # vrml_units
        # vrml_model_dir
        # vrml_relative_paths

        with self.do_filter_components():
            res = GS.board.export_3d(output, settings)

        self.check_job_ok(res)

    def run(self, output):
        if not GS.ki9:
            GS.exit_with_error("`export_3d` needs KiCad 9+", MISSING_TOOL)
        if self.format in {'ply', 'u3d', 'pdf', 'stpz'} and not GS.ki10:
            GS.exit_with_error(f"`{self.format}` needs KiCad 10+", MISSING_TOOL)
        super().run(output)
        if False:   # GS.kp is not None:
            # Currently (2026/09/01) there is no advantage in using KiPy because it ends calling kicad-cli anyways
            # Which is worst KiPy fails to save the PCB in memory to a temporal so we always export the unmodified PCB
            # https://gitlab.com/kicad/code/kicad-python/-/work_items/136
            self.run_kipy(output)
        else:
            self.run_kicli(output)


@output_class
class Export_3D(Base3D):
    """ 3D models exports of various formats using KiCad (BREP/GLB/STL/STEP/XAO)
        Exports the PCB as a 3D model using KiCad 9 or newer, using kicad-cli.
        Supported formats include:
        - STEP: ISO 10303-21 Clear Text Encoding of the Exchange Structure
        - STPZ: Compressed STEP files (KiCad 10+)
        - GLB: Binary version of the glTF, Graphics Library Transmission Format or GL Transmission Format and formerly
        > known as WebGL Transmissions Format or WebGL TF.
        - STL: 3D printer format, from stereolithography CAD software created by 3D Systems.
        - XAO: XAO (SALOME/Gmsh) format, used for FEM and simulations.
        - BRep: Part of Open CASCADE Technology (OCCT)
        - PLY: Polygon File Format or the Stanford Triangle Format. (KiCad 10+)
        - U3D: Universal 3D (ECMA-363) primarily used to embed interactive 3D models into PDF documents. (KiCad 10+)
        - PDF: Portable Document Format with the 3D model (KiCad 10+)
        STEP is the most common 3D format for exchange purposes
    """

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
