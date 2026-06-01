# -*- coding: utf-8 -*-
# Copyright (c) 2020-2023 Salvador E. Tropea
# Copyright (c) 2020-2023 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
import os
from .pre_base import BasePreFlight
from .gs import GS
from .misc import PDF_PCB_PRINT, KICAD_VERSION_7_0_1, MISSING_TOOL, W_DEPR, W_NOLAYERS
from .out_base import VariantOptions
from .macros import macros, document, output_class  # noqa: F401
from .drill_marks import add_drill_marks, DRILL_MARKS_MAP
from .layer import Layer
from . import log

logger = log.get_logger()


class Any_PCB_PrintOptions(VariantOptions):
    def __init__(self):
        with document:
            self.output_name = None
            """ {output} """
            self.scaling = 1.0
            """ *Scale factor (0 means autoscaling). You should disable `plot_sheet_reference` when using it """
            self.plot_sheet_reference = True
            """ *Include the title-block """
            self.monochrome = False
            """ Print in black and white """
            self.separated = False
            """ *Print layers in separated pages """
            self.mirror = False
            """ Print mirrored (X axis inverted). ONLY for KiCad 6 """
            self.hide_excluded = False
            """ Hide components in the Fab layer that are marked as excluded by a variant.
                Affected by global options """
            self.title = ''
            """ Text used to replace the sheet title. %VALUE expansions are allowed.
                If it starts with `+` the text is concatenated """
            self.force_edge_cuts = True
            """ Only useful for KiCad 6 when printing in one page, you can disable the edge here.
                KiCad 5 forces it by default, and you can't control it from config files.
                Same for KiCad 6 when printing to separated pages """
            self.color_theme = '_builtin_classic'
            """ Selects the color theme. Onlyu applies to KiCad 6.
                To use the KiCad 6 default colors select `_builtin_default`.
                Usually user colors are stored as `user`, but you can give it another name """
        add_drill_marks(self)
        super().__init__()
        self.get_targets = self._get_targets

    def config(self, parent):
        super().config(parent)
        self.drill_marks = DRILL_MARKS_MAP[self.drill_marks]

    def filter_components(self):
        if not self.will_filter_pcb_components() and self.title == '':
            return GS.pcb_file
        self.filter_pcb_components()
        self.set_title(self.title)
        # Save the PCB to a temporal dir
        fname, pcb_dir = self.save_tmp_dir_board('pdf_pcb_print')
        self.restore_title()
        self.unfilter_pcb_components()
        self._files_to_remove.append(pcb_dir)
        return fname

    def run(self, output, svg=False):
        super().run(self._layers)
        logger.warning(W_DEPR+'The `pdf_pcb_print` and `svg_pcb_print` outputs are deprecated, use `pcb_print` instead')
        if self._parent.layers == ['all'] and not self._parent.get_user_defined('layers'):
            logger.warning(W_NOLAYERS+f'No layers specified for `{self._parent.name}`, including `all`')
        if GS.ki7 and GS.kicad_version_n < KICAD_VERSION_7_0_1 and self.scaling != 0 and self.scaling != 1.0:
            GS.exit_with_error("Scaled printing is broken in KiCad 7.0.0\n"
                               "Please upgrade KiCad to 7.0.1 or newer", MISSING_TOOL)
        command = self.ensure_tool('KiAuto')
        # Output file name
        cmd = [command, 'export', '--output_name', output]
        if BasePreFlight.get_option('check_zone_fills'):
            cmd.append('-f')
        cmd.extend(['--scaling', str(self.scaling), '--pads', str(self.drill_marks)])
        if not self.plot_sheet_reference:
            cmd.append('--no-title')
        if self.monochrome:
            cmd.append('--monochrome')
        if self.separated:
            cmd.append('--separate')
        if self.mirror:
            cmd.append('--mirror')
        if self.color_theme != '_builtin_classic' and self.color_theme:
            cmd.extend(['--color_theme', self.color_theme])
        if svg:
            cmd.append('--svg')
        board_name = self.filter_components()
        cmd.extend([board_name, os.path.dirname(output)])
        # Add the extra options before the layers (so the output dir is the last option)
        cmd = self.add_extra_options(cmd)
        # Add the layers
        cmd.extend([la.layer for la in self._layers])
        if GS.ki6 and self.force_edge_cuts and not self.separated:
            cmd.append('Edge.Cuts')
        # Execute it
        self.exec_with_retry(cmd, PDF_PCB_PRINT)

    def set_layers(self, layers):
        layers = Layer.solve(layers)
        self._layers = layers
        self._expand_id = '+'.join([la.suffix for la in layers])
