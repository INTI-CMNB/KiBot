# -*- coding: utf-8 -*-
# Copyright (c) 2026 Salvador E. Tropea
# Copyright (c) 2026 Instituto Nacional de Tecnología Industrial
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)
from .misc import UNITS_2_KICAD, MISSING_TOOL
from .kiplot import run_command
from .gs import GS
from .out_base import VariantOptions
from .macros import macros, document, output_class  # noqa: F401
from . import log

logger = log.get_logger()
BOOLEAN_OPS = ('exclude_footprints_without_pads', 'subtract_holes_from_board', 'subtract_holes_from_copper')


class PCB_StatsOptions(VariantOptions):
    def __init__(self):
        with document:
            self.output = GS.def_global_output
            """ *Name for the generated report file (%i='statistics' %x='txt/json') """
            self.format = 'txt'
            """ *[txt,json] Output file format """
            self.units = 'millimeters'
            """ [millimeters,inches] Units used for the values. Affected by global options """
            self.exclude_footprints_without_pads = False
            """ Exclude footprints without pads """
            self.subtract_holes_from_board = False
            """ Subtract holes from the board area """
            self.subtract_holes_from_copper = False
            """ Subtract holes from copper areas """
        super().__init__()
        self._expand_id = 'statistics'

    def config(self, parent):
        super().config(parent)
        # Adjust the units
        self._units = UNITS_2_KICAD[self.units]
        # The format indicates the extension
        self._expand_ext = self.format

    def run(self, output):
        if not GS.ki10:
            GS.exit_with_error("`pcb_stats` needs KiCad 10+", MISSING_TOOL)
        super().run(output)
        # Make units explicit
        # Base command, no variants here
        cmd = [GS.kicad_cli, 'pcb', 'export', 'stats', '-o', output]
        if self.format != 'txt':
            cmd.extend(['--format', self.format])
        for ops in BOOLEAN_OPS:
            if getattr(self, ops):
                cmd.append('--'+ops.replace('_', '-'))
        # The board
        board_name = self.save_tmp_board_if_variant()
        cmd.append(board_name)
        run_command(cmd)
        if self._files_to_remove:
            self.remove_temporals()


@output_class
class PCB_Stats(BaseOutput):  # noqa: F821
    """ PCB statistics
        Generates basic PCB statistics using KiCad 10 or newer.
        Corresponds to what you get in the Inspect -> Show Board Statistics menu """
    def __init__(self):
        super().__init__()
        with document:
            self.options = PCB_StatsOptions
            """ *[dict={}] Options for the `pcb_stats` output """
        self._category = 'PCB/docs'

    @staticmethod
    def get_conf_examples(name, layers):
        if not GS.ki10:
            return None
        return BaseOutput.simple_conf_examples(name, 'PCB Statistics', '')  # noqa: F821
