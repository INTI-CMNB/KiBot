# -*- coding: utf-8 -*-
# Copyright (c) 2022-2025 Salvador E. Tropea
# Copyright (c) 2022-2025 Instituto Nacional de Tecnología Industrial
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)
"""
Dependencies:
  - from: KiAuto
    role: mandatory
    command: eeschema_do
    version: 2.0.0
    version_k7: 2.2.8
    version_k8: 2.3.2
    version_k9: 2.3.5
    version_k10: 2.3.9
"""
import os
from .gs import GS
from .kiplot import run_command
from .out_base import VariantOptions
from .misc import FAILED_EXECUTE, MISSING_TOOL
from .macros import macros, document, output_class  # noqa: F401
from . import log
EXTENSIONS = {'classic': ('netlist', 'net'),
              'orcadpcb2': ('orcad', 'net'),
              'allegro': ('allegro', 'txt'),
              'pads': ('pads', 'asc'),
              'cadstar': ('cadstar', 'frp'),
              'spice': ('spice', 'cir'),
              'spicemodel': ('model', 'cir'),
              'kicadxml': ('netlist', 'xml'),
              'ipc': ('IPC-D-356', 'd356'),
              }
NEEDS_K8 = {'orcadpcb2', 'cadstar', 'spice', 'spicemodel', 'kicadxml'}
NEEDS_K9 = {'allegro', 'pads'}
logger = log.get_logger()


class NetlistOptions(VariantOptions):
    def __init__(self):
        with document:
            self.output = GS.def_global_output
            """ *Filename for the output
                - classic: (%i=netlist, %x=net)
                - ipc: (%i=IPC-D-356, %x=d356)
                - orcadpcb2: (%i=orcad, %x=net)
                - allegro: (%i=allegro, %x=txt)
                - pads: (%i=pads, %x=asc)
                - cadstar: (%i=cadstar, %x=frp)
                - spice: (%i=spice, %x=cir)
                - spicemodel: (%i=model, %x=cir)
                - kicadxml: (%i=netlist, %x=xml)
            """
            self.format = 'classic'
            """ *[classic,ipc,orcadpcb2,allegro,pads,cadstar,spice,spicemodel,kicadxml] The `classic` format is the KiCad
                internal format, and is generated from the schematic.
                The `ipc` format is the IPC-D-356 format, useful for PCB testing, is generated from the PCB.
                kicadxml, cadstar, orcadpcb2, spice and spicemodel needs KiCad 8 or newer.
                allegro and pads needs KiCad 9 or newer
                """
        super().__init__()
        self.help_only_sub_pcbs()
        self.get_targets = self._get_targets

    def config(self, parent):
        super().config(parent)
        self._expand_id, self._expand_ext = EXTENSIONS[self.format]
        self._category = 'PCB/fabrication/verification' if self.format == 'ipc' else 'PCB/export'

    def run_cli(self, name, format):
        super().run(name)
        sch_file = self.save_tmp_sch_if_variant()
        cmd = [GS.kicad_cli, 'sch', 'export', 'netlist', '--format', format, '--output', name]
        self.add_kicad_cli_variant(cmd)
        cmd.append(sch_file)
        run_command(cmd)

    def run(self, name):
        if self.format == 'classic' and GS.ki8:
            self.run_cli(name, 'kicadsexpr')
            return
        if self.format in NEEDS_K8:
            if not GS.ki8:
                GS.exit_with_error("`{self.format}` netlist needs KiCad 8+", MISSING_TOOL)
            self.run_cli(name, self.format)
            return
        if self.format in NEEDS_K9:
            if not GS.ki8:
                GS.exit_with_error("`{self.format}` netlist needs KiCad 9+", MISSING_TOOL)
            self.run_cli(name, self.format)
            return
        command = self.ensure_tool('KiAuto')
        super().run(name)
        if self.format == 'ipc':
            command = command.replace('eeschema_do', 'pcbnew_do')
            subcommand = 'ipc_netlist'
            file = self.save_tmp_board_if_variant()
        else:
            subcommand = 'netlist'
            file = self.save_tmp_sch_if_variant()
        # Create the command line
        cmd = self.add_extra_options([command, subcommand, '--output_name', name, file, os.path.dirname(name)])
        # Execute it
        self.exec_with_retry(cmd, FAILED_EXECUTE)


@output_class
class Netlist(BaseOutput):  # noqa: F821
    """ Netlist
        Generates the list of connections for the project.
        The netlist can be generated in the classic format and in IPC-D-356 format,
        useful for board testing """
    def __init__(self):
        super().__init__()
        with document:
            self.options = NetlistOptions
            """ *[dict={}] Options for the `netlist` output """

    @staticmethod
    def get_conf_examples(name, layers):
        gb1 = {}
        gb1['name'] = 'classic_'+name
        gb1['comment'] = 'Schematic netlist in KiCad format'
        gb1['type'] = name
        gb1['dir'] = 'Export'
        gb2 = {}
        gb2['name'] = 'ipc_'+name
        gb2['comment'] = 'IPC-D-356 netlist for testing'
        gb2['type'] = name
        gb2['dir'] = 'Export'
        gb2['options'] = {'format': 'ipc'}
        return [gb1, gb2]
