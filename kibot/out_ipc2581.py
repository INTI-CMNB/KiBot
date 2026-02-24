# -*- coding: utf-8 -*-
# Copyright (c) 2025 Salvador E. Tropea
# Copyright (c) 2025 Instituto Nacional de Tecnología Industrial
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)
from .gs import GS
from .optionable import Optionable
from .out_base import VariantOptions
from .misc import MISSING_TOOL, UNITS_2_KICAD, W_BADFIELD
from .kiplot import run_command
from .macros import macros, document, output_class  # noqa: F401
from . import log

logger = log.get_logger()


class IPC2581Options(VariantOptions):
    def __init__(self):
        with document:
            self.output = GS.def_global_output
            """ *Filename for the output (%i=IPC-2581, %x=zip/xml)
                The extension depends on the compress option """
            self.compress = True
            """ Compress the XML file as a *zip* file """
            self.precision = 6
            """ Number of decimals used to represent the values """
            self.units = 'millimeters'
            """ [millimeters,inches] Units used for the positions. Affected by global options.
                Note that when using *mils* as global units this option becomes *inches* """
            self.version = 'C'
            """ [B,C] Which implementation of the IPC-2581 standard will be generated """
            self.field_part_number = '_field_part_number'
            """ Name of the field used for the manufacturer part number.
                Use the `field_part_number` global variable to define `_field_part_number` """
            self.field_manufacturer = '_field_manufacturer'
            """ Name of the field used for the manufacturer.
                Use the `field_manufacturer` global variable to define `_field_manufacturer` """
            self.field_dist_part_number = '_field_dist_part_number'
            """ Name of the field used for the distributor part number.
                Use the `field_dist_part_number` global variable to define `_field_dist_part_number` """
            self.field_distributor = '_field_distributor'
            """ Name of the field used for the distributor.
                Use the `field_distributor` global variable to define `_field_distributor` """
            self.field_internal_id = ''
            """ Name of the field used as an internal ID.
                Leave empty to create unique IDs """
        super().__init__()
        self._expand_id = 'IPC-2581'

    def config(self, parent):
        super().config(parent)
        self._expand_ext = 'zip' if self.compress else 'xml'
        if self.units == 'mils':
            self.units = 'inches'
        self._field_part_number = Optionable.solve_field_name(self.field_part_number, empty_when_none=True)
        self._field_manufacturer = Optionable.solve_field_name(self.field_manufacturer, empty_when_none=True)
        self._field_dist_part_number = Optionable.solve_field_name(self.field_dist_part_number, empty_when_none=True)
        self._field_distributor = Optionable.solve_field_name(self.field_distributor, empty_when_none=True)
        self._field_internal_id = Optionable.solve_field_name(self.field_internal_id, empty_when_none=True)
        # Check the fields are valid
        valid = set()
        for m in GS.get_modules():
            valid.update(GS.get_fields(m))
        for c in ('part_number', 'manufacturer', 'dist_part_number', 'distributor', 'internal_id'):
            fld = f'field_{c}'
            val = getattr(self, '_'+fld)
            if val and val not in valid:
                logger.warning(W_BADFIELD+f'Invalid column name `{val}` for `{fld}`. Valid columns are {sorted(valid)}.')

    def get_targets(self, out_dir):
        return [self._parent.expand_filename(out_dir, self.output)]

    def run(self, name):
        if not GS.ki9:
            GS.exit_with_error("`IPC2581` needs KiCad 9+", MISSING_TOOL)
        super().run(name)
        board_name = self.save_tmp_board_if_variant()
        cmd = [GS.kicad_cli, 'pcb', 'export', 'ipc2581', '-o', name, '--units', UNITS_2_KICAD[self.units],
               '--precision', str(int(self.precision)), '--version', self.version]
        if self.compress:
            cmd.append('--compress')
        if self._field_part_number:
            cmd.extend(['--bom-col-mfg-pn', self._field_part_number])
        if self._field_manufacturer:
            cmd.extend(['--bom-col-mfg', self._field_manufacturer])
        if self._field_dist_part_number:
            cmd.extend(['--bom-col-dist-pn', self._field_dist_part_number])
        if self._field_distributor:
            cmd.extend(['--bom-col-dist', self._field_distributor])
        if self._field_internal_id:
            cmd.extend(['--bom-col-int-id', self._field_internal_id])
        cmd.append(board_name)
        run_command(cmd)


@output_class
class IPC2581(BaseOutput):  # noqa: F821
    """ IPC-DPMX (IPC-2581)
        Exports the PCB in the Digital Product Model Exchange IPC format.
        Only available for KiCad 9 and newer.
        The requested fields are optional """
    def __init__(self):
        super().__init__()
        self._category = ['PCB/export', 'PCB/fabrication']
        with document:
            self.options = IPC2581Options
            """ *[dict={}] Options for the `ipc2581` output """

    @staticmethod
    def get_conf_examples(name, layers):
        if not GS.ki9:
            return None
        return BaseOutput.simple_conf_examples(name, 'PCB in IPC-2581 format', 'Export')  # noqa: F821
