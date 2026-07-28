# -*- coding: utf-8 -*-
# Copyright (c) 2020-2023 Salvador E. Tropea
# Copyright (c) 2020-2023 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
# KiCad 6 bug: https://gitlab.com/kicad/code/kicad/-/issues/10075
"""
Dependencies:
  - from: KiAuto
    role: mandatory
    version: 1.6.1
    version_k7: 2.2.8
    version_k8: 2.3.2
    version_k9: 2.3.5
    version_k10: 2.3.9
    command: kicad2step_do
"""
import os
import re
from .error import KiPlotConfigurationError
from .misc import KICAD2STEP_ERR, W_DEPR
from .gs import GS
from .out_base_3d import Base3DOptions, Base3D
from .macros import macros, document, output_class  # noqa: F401
from . import log

logger = log.get_logger()


class STEPOptions(Base3DOptions):
    def __init__(self):
        with document:
            self.metric_units = True
            """ Use metric units instead of inches """
            self.origin = 'grid'
            """ *[grid,drill,*] Determines the coordinates origin. Using grid the coordinates are the same as you have in the
                design sheet.
                The drill option uses the auxiliary reference defined by the user.
                You can define any other origin using the format 'X,Y', i.e. '3.2,-10' """
            self.min_distance = -1
            """ The minimum distance between points to treat them as separate ones (-1 is KiCad default: 0.01 mm) """
            self.output = GS.def_global_output
            """ *Name for the generated STEP file (%i='3D' %x='step') """
            self.subst_models = True
            """ Substitute STEP or IGS models with the same name in place of VRML models """
        # Temporal dir used to store the downloaded files
        self._tmp_dir = None
        super().__init__()
        self._expand_ext = 'step'

    def config(self, parent):
        super().config(parent)
        val = self.origin
        if (val not in ['grid', 'drill']) and (re.match(r'[-\d\.]+\s*,\s*[-\d\.]+\s*$', val) is None):
            raise KiPlotConfigurationError('Origin must be `grid` or `drill` or `X,Y`')

    def run(self, output):
        if GS.ki9:
            logger.warning(W_DEPR+'For KiCad 9 use the `export_3d` output instead of `step`')
        super().run(output)
        command = self.ensure_tool('KiAuto')
        # Make units explicit
        if self.metric_units:
            units = 'mm'
        else:
            units = 'in'
        # Base command with overwrite
        cmd = [command, '-o', output, '-f', '-d', os.path.dirname(output)]
        if GS.debug_level > 0:
            cmd.append('-vv')
        else:
            cmd.append('-v')
        # Add user options
        if self.no_virtual:
            cmd.append('--no-virtual')
        if self.subst_models:
            cmd.append('--subst-models')
        if self.min_distance >= 0:
            cmd.extend(['--min-distance', "{}{}".format(self.min_distance, units)])
        if self.origin == 'drill':
            cmd.append('--drill-origin')
        elif self.origin == 'grid':
            cmd.append('--grid-origin')
        else:
            cmd.extend(['--user-origin', "{}{}".format(self.origin.replace(',', 'x'), units)])
        # The board
        board_name = self.filter_components(force_step=True)
        cmd.append(board_name)
        # Execute it
        self.exec_with_retry(self.add_extra_options(cmd, os.path.dirname(output)), KICAD2STEP_ERR)


@output_class
class STEP(Base3D):
    """ STEP (ISO 10303-21 Clear Text Encoding of the Exchange Structure)
        Exports the PCB as a 3D model with KiAuto.
        This is the most common 3D format for exchange purposes.
        For KiCad 9 use the `export_3d` output, see the `export_3d` output.
        This output is what you get from the 'File/Export/STEP' menu in pcbnew. """
    def __init__(self):
        super().__init__()
        with document:
            self.options = STEPOptions
            """ *[dict={}] Options for the `step` output """
        self._category = 'PCB/3D'

    @staticmethod
    def get_conf_examples(name, layers):
        if GS.ki9:
            return None
        return Base3D.simple_conf_examples(name, '3D model in STEP format', '3D')
