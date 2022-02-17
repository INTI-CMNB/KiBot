# -*- coding: utf-8 -*-
# Copyright (c) 2020-2021 Salvador E. Tropea
# Copyright (c) 2020-2021 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
import os
from re import search
from tempfile import NamedTemporaryFile
from subprocess import (check_output, STDOUT, CalledProcessError)
from .misc import (CMD_KIBOM, URL_KIBOM, BOM_ERROR, W_EXTNAME)
from .kiplot import (check_script)
from .gs import (GS)
from .optionable import Optionable, BaseOptions
from .error import KiPlotConfigurationError
from .bom.columnlist import ColumnList
from .macros import macros, document, output_class  # noqa: F401
from .out_base import BaseOutput
from . import log

logger = log.get_logger()

CONFIG_FILENAME = 'config.kibom.ini'


class KiBoMRegex(Optionable):
    """ Implements the pair column/regex """
    def __init__(self):
        super().__init__()
        self._unknown_is_error = True
        with document:
            self.column = ''
            """ Name of the column to apply the regular expression """
            self.regex = ''
            """ Regular expression to match """
            self.field = None
            """ {column} """
            self.regexp = None
            """ {regex} """

    def __str__(self):
        return self.column+'\t'+self.regex


class KiBoMColumns(Optionable):
    """ Information for the BoM columns """
    def __init__(self):
        super().__init__()
        self._unknown_is_error = True
        with document:
            self.field = ''
            """ Name of the field to use for this column """
            self.name = ''
            """ Name to display in the header. The field is used when empty """
            self.join = Optionable
            """ [list(string)|string=''] List of fields to join to this column """
        self._field_example = 'Row'
        self._name_example = 'Line'

    def config(self, parent):
        super().config(parent)
        if not self.field:
            raise KiPlotConfigurationError("Missing or empty `field` in columns list ({})".format(str(self._tree)))
        if isinstance(self.join, type):
            self.join = None
        elif isinstance(self.join, list):
            self.join = '\t'.join(self.join)


class ComponentAliases(Optionable):
    _default = [['r', 'r_small', 'res', 'resistor'],
                ['l', 'l_small', 'inductor'],
                ['c', 'c_small', 'cap', 'capacitor'],
                ['sw', 'switch'],
                ['zener', 'zenersmall'],
                ['d', 'diode', 'd_small'],
                ]

    def __init__(self):
        super().__init__()


class GroupFields(Optionable):
    _default = ['Part', 'Part Lib', 'Value', 'Footprint', 'Footprint Lib']

    def __init__(self):
        super().__init__()


class KiBoMConfig(Optionable):
    """ Implements the .ini options """
    def __init__(self):
        super().__init__()
        with document:
            self.ignore_dnf = True
            """ Exclude DNF (Do Not Fit) components """
            self.html_generate_dnf = True
            """ Generate a separated section for DNF (Do Not Fit) components (HTML only) """
            self.use_alt = False
            """ Print grouped references in the alternate compressed style eg: R1-R7,R18 """
            self.number_rows = True
            """ First column is the row number """
            self.group_connectors = True
            """ Connectors with the same footprints will be grouped together, independent of the name of the connector """
            self.test_regex = True
            """ Each component group will be tested against a number of regular-expressions (see ``). """
            self.merge_blank_fields = True
            """ Component groups with blank fields will be merged into the most compatible group, where possible """
            self.fit_field = 'Config'
            """ Field name used to determine if a particular part is to be fitted (also DNC and variants) """
            self.datasheet_as_link = ''
            """ Column with links to the datasheet (HTML only) """
            self.hide_headers = False
            """ Hide column headers """
            self.hide_pcb_info = False
            """ Hide project information """
            self.ref_separator = ' '
            """ Separator used for the list of references """
            self.digikey_link = Optionable
            """ [string|list(string)=''] Column/s containing Digi-Key part numbers, will be linked to web page (HTML only) """
            self.group_fields = GroupFields
            """ [list(string)] List of fields used for sorting individual components into groups.
                Components which match (comparing *all* fields) will be grouped together.
                Field names are case-insensitive.
                If empty: ['Part', 'Part Lib', 'Value', 'Footprint', 'Footprint Lib'] is used """
            self.component_aliases = ComponentAliases
            """ [list(list(string))] A series of values which are considered to be equivalent for the part name.
                Each entry is a list of equivalen names. Example: ['c', 'c_small', 'cap' ]
                will ensure the equivalent capacitor symbols can be grouped together.
                If empty the following aliases are used:
                - ['r', 'r_small', 'res', 'resistor']
                - ['l', 'l_small', 'inductor']
                - ['c', 'c_small', 'cap', 'capacitor']
                - ['sw', 'switch']
                - ['zener', 'zenersmall']
                - ['d', 'diode', 'd_small'] """
            self.include_only = KiBoMRegex
            """ [list(dict)] A series of regular expressions used to select included parts.
                If there are any regex defined here, only components that match against ANY of them will be included.
                Column names are case-insensitive.
                If empty all the components are included """
            self.exclude_any = KiBoMRegex
            """ [list(dict)] A series of regular expressions used to exclude parts.
                If a component matches ANY of these, it will be excluded.
                Column names are case-insensitive.
                If empty the following list is used:
                - column: References
                ..regex: '^TP[0-9]*'
                - column: References
                ..regex: '^FID'
                - column: Part
                ..regex: 'mount.*hole'
                - column: Part
                ..regex: 'solder.*bridge'
                - column: Part
                ..regex: 'test.*point'
                - column: Footprint
                ..regex 'test.*point'
                - column: Footprint
                ..regex: 'mount.*hole'
                - column: Footprint
                ..regex: 'fiducial' """
            self.columns = KiBoMColumns
            """ [list(dict)|list(string)] List of columns to display.
                Can be just the name of the field """

    @staticmethod
    def _create_minimal_ini():
        """ KiBoM config to get only the headers """
        with NamedTemporaryFile(mode='w', delete=False) as f:
            f.write('[BOM_OPTIONS]\n')
            f.write('output_file_name = %O\n')
            f.write('hide_pcb_info = 1\n')
            f.write('\n[IGNORE_COLUMNS]\n')
            f.write('\n[REGEX_EXCLUDE]\n')
            f.write('Part\t.*\n')
            f.close()
            return f.name

    @staticmethod
    def _get_columns():
        """ Create a list of valid columns """
        if not GS.sch:
            return ColumnList.COLUMNS_DEFAULT
        check_script(CMD_KIBOM, URL_KIBOM, '1.8.0')
        config = None
        csv = None
        columns = None
        try:
            xml = GS.sch_no_ext+'.xml'
            config = os.path.abspath(KiBoMConfig._create_minimal_ini())
            with NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
                csv = f.name
            cmd = [CMD_KIBOM, '--cfg', config, '-d', os.path.dirname(csv), '-s', ',', xml, csv]
            logger.debug('Running: '+str(cmd))
            cmd_output = check_output(cmd, stderr=STDOUT)
            with open(csv, 'rt') as f:
                columns = f.readline().rstrip().split(',')
        except CalledProcessError as e:
            logger.error('Failed to get the column names for `{}`, error {}'.format(xml, e.returncode))
            if e.output:
                logger.debug('Output from command: '+e.output.decode())
            exit(BOM_ERROR)
        finally:
            if config:
                os.remove(config)
            if csv:
                os.remove(csv)
        logger.debug('Output from command:\n'+cmd_output.decode())
        return columns

    def config(self, parent):
        super().config(parent)
        # digikey_link
        if isinstance(self.digikey_link, type):
            self.digikey_link = None
        elif isinstance(self.digikey_link, list):
            self.digikey_link = '\t'.join(self.digikey_link)
        # group_fields
        if isinstance(self.group_fields, type):
            self.group_fields = None
        # component_aliases
        if isinstance(self.component_aliases, type):
            self.component_aliases = None
        else:
            self.component_aliases = ['\t'.join(a) for a in self.component_aliases]
        # include_only
        if isinstance(self.include_only, type):
            self.include_only = None
        else:
            self.include_only = [str(r) for r in self.include_only]
        # exclude_any
        if isinstance(self.exclude_any, type):
            self.exclude_any = None
        else:
            self.exclude_any = [str(r) for r in self.exclude_any]
        # columns
        if isinstance(self.columns, type):
            self.columns = None
            self.col_rename = None
            self.join = None
            self.ignore = None
        else:
            # This is tricky
            # Lower case available columns
            valid_columns = self._get_columns()
            valid_columns_l = {c.lower(): c for c in valid_columns}
            logger.debug("Valid columns: "+str(valid_columns))
            # Create the different lists
            columns = []
            columns_l = {}
            self.col_rename = []
            self.join = []
            for col in self.columns:
                if isinstance(col, str):
                    # Just a string, add to the list of used
                    new_col = col
                else:
                    # A complete entry
                    new_col = col.field
                    # A column rename
                    if col.name:
                        self.col_rename.append(col.field+'\t'+col.name)
                    # Attach other columns
                    if col.join:
                        self.join.append(col.field+'\t'+col.join)
                # Check this is a valid column
                if new_col.lower() not in valid_columns_l:
                    raise KiPlotConfigurationError('Invalid column name `{}`'.format(new_col))
                columns.append(new_col)
                columns_l[new_col.lower()] = new_col
            # Create a list of the columns we don't want
            self.ignore = [c for c in valid_columns_l.keys() if c not in columns_l]
            # And this is the ordered list with the case style defined by the user
            self.columns = columns

    def write_bool(self, attr):
        """ Write a .INI bool option """
        self.f.write('{} = {}\n'.format(attr, '1' if getattr(self, attr) else '0'))

    def write_str(self, attr):
        """ Write a .INI string option """
        val = getattr(self, attr)
        if val:
            self.f.write('{} = {}\n'.format(attr, val))

    def write_vector(self, vector, section):
        """ Write a .INI section filled with a vector of strings """
        if vector:
            self.f.write('\n[{}]\n'.format(section))
            for v in vector:
                self.f.write(v+'\n')

    def save(self, filename):
        """ Create an INI file for KiBoM """
        logger.debug("Saving KiBoM config to `{}`".format(filename))
        with open(filename, 'wt') as f:
            self.f = f
            f.write('[BOM_OPTIONS]\n')
            self.write_bool('ignore_dnf')
            self.write_bool('html_generate_dnf')
            self.write_bool('use_alt')
            self.write_bool('number_rows')
            self.write_bool('group_connectors')
            self.write_bool('test_regex')
            self.write_bool('merge_blank_fields')
            self.write_str('fit_field')
            self.write_str('datasheet_as_link')
            self.write_bool('hide_headers')
            self.write_bool('hide_pcb_info')
            self.write_str('ref_separator')
            self.write_str('digikey_link')
            # Ask to keep the output name
            f.write('output_file_name = %O\n')
            self.write_vector(self.group_fields, 'GROUP_FIELDS')
            self.write_vector(self.include_only, 'REGEX_INCLUDE')
            self.write_vector(self.exclude_any, 'REGEX_EXCLUDE')
            self.write_vector(self.columns, 'COLUMN_ORDER')
            self.write_vector(self.ignore, 'IGNORE_COLUMNS')
            self.write_vector(self.col_rename, 'COLUMN_RENAME')
            self.write_vector(self.join, 'JOIN')
            self.write_vector(self.component_aliases, 'COMPONENT_ALIASES')


class KiBoMOptions(BaseOptions):
    def __init__(self):
        with document:
            self.number = 1
            """ Number of boards to build (components multiplier) """
            self.variant = ''
            """ Board variant(s), used to determine which components
                are output to the BoM. To specify multiple variants,
                with a BOM file exported for each variant, separate
                variants with the ';' (semicolon) character.
                This isn't related to the KiBot concept of variants """
            self.conf = KiBoMConfig
            """ [string|dict] BoM configuration file, relative to PCB.
                You can also define the configuration here, will be stored in `config.kibom.ini` """
            self.separator = ','
            """ CSV Separator """
            self.output = GS.def_global_output
            """ filename for the output (%i=bom)"""
            self.format = 'HTML'
            """ [HTML,CSV,XML,XLSX] format for the BoM """
        super().__init__()
        self._expand_id = 'bom'

    def config(self, parent):
        super().config(parent)
        if isinstance(self.conf, type):
            self.conf = 'bom.ini'
        elif isinstance(self.conf, str):
            if not self.conf:
                self.conf = 'bom.ini'
        else:
            # A configuration
            conf = os.path.abspath(os.path.join(self.expand_filename_sch(GS.out_dir), CONFIG_FILENAME))
            self.conf.save(conf)
            self.conf = conf
        self._expand_ext = self.format.lower()

    def get_targets(self, out_dir):
        if self.output:
            return [self.expand_filename(out_dir, self.output, 'bom', self.format.lower())]
        logger.warning(W_EXTNAME+'{} uses a name generated by the external tool.'.format(self._parent))
        logger.warning(W_EXTNAME+'Please use a name generated by KiBot or specify the name explicitly.')
        return []

    def run(self, name):
        check_script(CMD_KIBOM, URL_KIBOM, '1.8.0')
        format = self.format.lower()
        prj = GS.sch_no_ext
        config = os.path.join(GS.sch_dir, self.conf)
        if self.output:
            force_output = True
            output = name
            output_dir = os.path.dirname(name)
        else:
            force_output = False
            output = os.path.basename(prj)+'.'+format
            output_dir = name
        logger.debug('Doing BoM, format {} prj: {} config: {} output: {}'.format(format, prj, config, output))
        cmd = [CMD_KIBOM,
               '-n', str(self.number),
               '--cfg', config,
               '-s', self.separator,
               '-d', output_dir]
        if GS.debug_enabled:
            cmd.append('-v')
        if self.variant:
            cmd.extend(['-r', self.variant])
        cmd.extend([prj+'.xml', output])
        logger.debug('Running: '+str(cmd))
        try:
            cmd_output = check_output(cmd, stderr=STDOUT)
        except CalledProcessError as e:
            logger.error('Failed to create BoM, error %d', e.returncode)
            if e.output:
                logger.debug('Output from command: '+e.output.decode())
            exit(BOM_ERROR)
        if force_output:
            # When we create the .ini we can control the name.
            # But when the user does it we can trust the settings.
            m = search(r'Saving BOM File: (.*)', cmd_output.decode())
            if m and m.group(1) != output:
                cur = m.group(1)
                logger.debug('Renaming output file: {} -> {}'.format(cur, output))
                os.rename(cur, output)
        logger.debug('Output from command:\n'+cmd_output.decode())


@output_class
class KiBoM(BaseOutput):  # noqa: F821
    """ KiBoM (KiCad Bill of Materials)
        Used to generate the BoM in HTML or CSV format using the KiBoM plug-in.
        For more information: https://github.com/INTI-CMNB/KiBoM
        Note that this output is provided as a compatibility tool.
        We recommend using the `bom` output instead.
        This output is what you get from the 'Tools/Generate Bill of Materials' menu in eeschema. """
    def __init__(self):
        super().__init__()
        with document:
            self.options = KiBoMOptions
            """ [dict] Options for the `kibom` output """
        self._sch_related = True

    def get_dependencies(self):
        files = super().get_dependencies()
        if isinstance(self.options.conf, str):
            files.append(self.options.conf)
        return files
