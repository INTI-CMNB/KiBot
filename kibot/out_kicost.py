# -*- coding: utf-8 -*-
# Copyright (c) 2021 Salvador E. Tropea
# Copyright (c) 2021 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
from __future__ import annotations
import os
from os.path import isfile, abspath, join, dirname
from subprocess import check_output, STDOUT, CalledProcessError
from tempfile import mkdtemp
from shutil import rmtree
from .misc import (CMD_KICOST, URL_KICOST, BOM_ERROR, DISTRIBUTORS, W_UNKDIST, ISO_CURRENCIES, W_UNKCUR, KICOST_SUBMODULE,
                   W_KICOSTFLD, W_MIXVARIANT)
from .error import KiPlotConfigurationError
from .optionable import Optionable
from .gs import GS
from .kiplot import check_script
from .out_base import VariantOptions, BaseOutput
from .macros import macros, document, output_class  # noqa: F401
from .fil_base import FieldRename
from . import log

logger = log.get_logger()
WARNING_MIX = ("Don't use the `kicost_variant` when using internal variants/filters")


class Aggregate(Optionable):
    def __init__(self):
        super().__init__()
        with document:
            self.file = ''
            """ Name of the XML to aggregate """
            self.variant = ' '
            """ Variant for this project """
            self.number = 100
            """ Number of boards to build (components multiplier) """
            self.board_qty = None
            """ {number} """

    def config(self, parent):
        super().config(parent)
        if not self.file:
            raise KiPlotConfigurationError("Missing or empty `file` in aggregate list ({})".format(str(self._tree)))


class KiCostOptions(VariantOptions):
    def __init__(self):
        with document:
            self.output = GS.def_global_output
            """ Filename for the output (%i=kicost, %x=xlsx) """
            self.no_price = False
            """ Do not look for components price. For testing purposes """
            self.no_collapse = False
            """ Do not collapse the part references (collapse=R1-R4) """
            self.show_cat_url = False
            """ Include the catalogue links in the catalogue code """
            self.distributors = Optionable
            """ [string|list(string)] Include this distributors list. Default is all the available """
            self.no_distributors = Optionable
            """ [string|list(string)] Exclude this distributors list. They are removed after computing `distributors` """
            self.currency = Optionable
            """ [string|list(string)=USD] Currency priority. Use ISO4217 codes (i.e. USD, EUR) """
            self.group_fields = Optionable
            """ [string|list(string)] List of fields that can be different for a group.
                Parts with differences in these fields are grouped together, but displayed individually """
            self.split_extra_fields = Optionable
            """ [string|list(string)] Declare part fields to include in multipart split process """
            self.ignore_fields = Optionable
            """ [string|list(string)] List of fields to be ignored """
            self.fields = Optionable
            """ [string|list(string)] List of fields to be added to the global data section """
            self.translate_fields = FieldRename
            """ [list(dict)] Fields to rename (KiCost option, not internal filters) """
            self.kicost_variant = ''
            """ Regular expression to match the variant field (KiCost option, not internal variants) """
            self.aggregate = Aggregate
            """ [list(dict)] Add components from other projects """
            self.number = 100
            """ Number of boards to build (components multiplier) """
            self.board_qty = None
            """ {number} """

        super().__init__()
        self.add_to_doc('variant', WARNING_MIX)
        self.add_to_doc('dnf_filter', WARNING_MIX)
        self._expand_id = 'kicost'
        self._expand_ext = 'xlsx'

    @staticmethod
    def _validate_dis(val):
        val = Optionable.force_list(val)
        for v in val:
            if v not in DISTRIBUTORS:
                logger.warning(W_UNKDIST+'Unknown distributor `{}`'.format(v))
        return val

    @staticmethod
    def _validate_cur(val):
        val = Optionable.force_list(val)
        for v in val:
            if v not in ISO_CURRENCIES:
                logger.warning(W_UNKCUR+'Unknown currency `{}`'.format(v))
        return val

    def config(self, parent):
        super().config(parent)
        if not self.output:
            self.output = '%f.%x'
        self.distributors = self._validate_dis(self.distributors)
        self.no_distributors = self._validate_dis(self.no_distributors)
        self.currency = self._validate_cur(self.currency)
        self.group_fields = Optionable.force_list(self.group_fields)
        self.split_extra_fields = Optionable.force_list(self.split_extra_fields)
        self.ignore_fields = Optionable.force_list(self.ignore_fields)
        self.fields = Optionable.force_list(self.fields)
        # Adapt translate_fields to its use
        if isinstance(self.translate_fields, type):
            self.translate_fields = []
        if self.translate_fields:
            translate_fields = []
            for f in self.translate_fields:
                translate_fields.append(f.field)
                translate_fields.append(f.name)
            self.translate_fields = translate_fields
        # Make sure aggregate is a list
        if isinstance(self.aggregate, type):
            self.aggregate = []

    def get_targets(self, out_dir):
        return [self.expand_filename(out_dir, self.output, self._expand_id, self._expand_ext)]

    @staticmethod
    def add_list_opt(cmd, name, val):
        if val:
            cmd.extend(['--'+name] + val)

    @staticmethod
    def add_bool_opt(cmd, name, val):
        if val:
            cmd.append('--'+name)

    def run(self, name):
        super().run(name)
        net_dir = None
        if self._comps:
            var_fields = set(['variant', 'version'])
            if self.variant and self.variant.type == 'kicost' and self.variant.variant_field not in var_fields:
                # Warning about KiCost limitations
                logger.warning(W_KICOSTFLD+'KiCost variant `{}` defines `variant_field` as `{}`, not supported by KiCost'.
                               format(self.variant, self.variant.variant_field))
            if self.kicost_variant:
                logger.warning(W_MIXVARIANT+'Avoid using KiCost variants and internal variants on the same output')
            # Write a custom netlist to a temporal dir
            net_dir = mkdtemp(prefix='tmp-kibot-kicost-')
            assert net_dir is not None
            netlist = os.path.join(net_dir, GS.sch_basename+'.xml')
            with open(netlist, 'wb') as f:
                GS.sch.save_netlist(f, self._comps, no_field=var_fields)
        else:
            # Make sure the XML is there.
            # Currently we only support the XML mechanism.
            netlist = GS.sch_no_ext+'.xml'
            if not isfile(netlist):
                logger.error('Missing netlist in XML format `{}`'.format(netlist))
                logger.error('You can generate it using the `update_xml` pre-flight')
                exit(BOM_ERROR)
        # Check KiCost is available
        cmd_kicost = abspath(join(dirname(__file__), KICOST_SUBMODULE))
        if not isfile(cmd_kicost):
            check_script(CMD_KICOST, URL_KICOST)
            cmd_kicost = CMD_KICOST
        # Construct the command
        cmd = [cmd_kicost, '-w', '-o', name, '-i', netlist]
        # Add the rest of input files and their variants
        if self.aggregate:
            # More than one project
            for p in self.aggregate:
                cmd.append(p.file)
            cmd.append('--variant')
            # KiCost internally defaults to ' ' as a dummy variant
            cmd.append(self.kicost_variant if self.kicost_variant else ' ')
            for p in self.aggregate:
                cmd.append(p.variant if p.variant else ' ')
            cmd.extend(['--board_qty', str(self.number)])
            for p in self.aggregate:
                cmd.append(str(p.number))
        else:
            # Just this project
            if self.kicost_variant:
                cmd.extend(['--variant', self.kicost_variant])
            if self.number != 100:
                cmd.extend(['--board_qty', str(self.number)])
        # Pass the debug level
        if GS.debug_enabled:
            cmd.append('--debug={}'.format(GS.debug_level))
        # Boolean options
        self.add_bool_opt(cmd, 'no_price', self.no_price)
        self.add_bool_opt(cmd, 'no_collapse', self.no_collapse)
        self.add_bool_opt(cmd, 'show_cat_url', self.show_cat_url)
        # List options
        self.add_list_opt(cmd, 'include', self.distributors)
        self.add_list_opt(cmd, 'exclude', self.no_distributors)
        self.add_list_opt(cmd, 'currency', self.currency)
        self.add_list_opt(cmd, 'group_fields', self.group_fields)
        self.add_list_opt(cmd, 'split_extra_fields', self.split_extra_fields)
        self.add_list_opt(cmd, 'ignore_fields', self.ignore_fields)
        self.add_list_opt(cmd, 'fields', self.fields)
        # Field translation
        if self.translate_fields:
            cmd.append('--translate_fields')
            cmd.extend(self.translate_fields)
        # Run the command
        logger.debug('Running: '+str(cmd))
        try:
            cmd_output = check_output(cmd, stderr=STDOUT)
            cmd_output_dec = cmd_output.decode()
        except CalledProcessError as e:
            logger.error('Failed to create costs spreadsheet, error %d', e.returncode)
            if e.output:
                logger.debug('Output from command: '+e.output.decode())
            exit(BOM_ERROR)
        finally:
            if net_dir:
                logger.debug('Removing temporal variant dir `{}`'.format(net_dir))
                rmtree(net_dir)
        logger.debug('Output from command:\n'+cmd_output_dec+'\n')


@output_class
class KiCost(BaseOutput):  # noqa: F821
    """ KiCost (KiCad Cost calculator)
        Generates a spreadsheet containing components costs.
        For more information: https://github.com/INTI-CMNB/KiCost
        This output is what you get from the KiCost plug-in (eeschema). """
    def __init__(self):
        super().__init__()
        self._sch_related = True
        with document:
            self.options = KiCostOptions
            """ [dict] Options for the `kicost` output """
