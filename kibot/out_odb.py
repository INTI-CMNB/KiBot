# -*- coding: utf-8 -*-
# Copyright (c) 2025 Salvador E. Tropea
# Copyright (c) 2025 Instituto Nacional de Tecnología Industrial
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)
from .gs import GS
from .out_base import VariantOptions
from .misc import MISSING_TOOL, UNITS_2_KICAD
from .kiplot import run_command
from .macros import macros, document, output_class  # noqa: F401
from . import log

logger = log.get_logger()


class ODBOptions(VariantOptions):
    def __init__(self):
        with document:
            self.output = GS.def_global_output
            """ *Filename for the output (%i=odb, %x=zip/tgz/none)
                The extension depends on the compression option.
                Note that for `none` we get a directory, not a file """
            self.compression = 'zip'
            """ *[zip,tgz,none] For *zip* files the structure is at the root.
                *tgz* is gzip compressed tarball, usually smaller than a *zip* file.
                In this case data is inside a directory named *odb*, not the root.
                When using *none* you get a directory containing all the data """
            self.precision = 6
            """ Number of decimals used to represent the values """
            self.units = 'millimeters'
            """ [millimeters,inches] Units used for the positions. Affected by global options.
                Note that when using *mils* as global units this option becomes *inches* """
            self.drawing_sheet = ''
            """ Path to drawing sheet, this overrides any existing project defined sheet when used """
        super().__init__()
        self._expand_id = 'odb'

    def config(self, parent):
        super().config(parent)
        self._expand_ext = '' if self.compression == 'none' else self.compression
        if self.units == 'mils':
            self.units = 'inches'

    def get_targets(self, out_dir):
        return [self.fix_dir_name(self._parent.expand_filename(out_dir, self.output))]

    def fix_dir_name(self, name):
        return name[:-1] if not self._expand_ext and self.output.endswith('.%x') else name

    def run_kicli(self, name):
        board_name = self.save_tmp_board_if_variant()
        cmd = [GS.kicad_cli, 'pcb', 'export', 'odb', '-o', name, '--compression', self.compression, '--units',
               UNITS_2_KICAD[self.units], '--precision', str(int(self.precision))]
        self.add_kicad_cli_variant(cmd)
        if self.drawing_sheet:
            cmd.extend(['--drawing-sheet', self.drawing_sheet])
        cmd.append(board_name)
        run_command(cmd)

    def run_kipy(self, name):
        self.filter_pcb_components()

        kicad_variant = self.kicad_variant_name()
        res = GS.board.export_odb(
            name,
            drawing_sheet=self.drawing_sheet,
            compression=GS.ODB_COMPRESSION[self.compression],
            precision=self.precision,
            units=GS.U_MM if self.units == 'millimeters' else GS.U_INCH,
            variant=kicad_variant if kicad_variant is not None else '')

        self.unfilter_pcb_components()
        self.check_job_ok(res)

    def run(self, name):
        if not GS.ki9:
            GS.exit_with_error("`odb` needs KiCad 9+", MISSING_TOOL)
        name = self.fix_dir_name(name)
        super().run(name)
        if GS.kp is not None:
            self.run_kipy(name)
        else:
            self.run_kicli(name)


@output_class
class ODB(BaseOutput):  # noqa: F821
    """ ODB++
        Exports the PCB in ODB++ format.
        This can be used for fabrication purposes.
        Only available for KiCad 9 and newer """
    def __init__(self):
        super().__init__()
        self._category = ['PCB/export', 'PCB/fabrication']
        with document:
            self.options = ODBOptions
            """ *[dict={}] Options for the `odb` output """

    @staticmethod
    def get_conf_examples(name, layers):
        if not GS.ki9:
            return None
        return BaseOutput.simple_conf_examples(name, 'PCB in ODB++ format', 'Export')  # noqa: F821
