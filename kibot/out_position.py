# -*- coding: utf-8 -*-
# Copyright (c) 2020-2024 Salvador E. Tropea
# Copyright (c) 2020-2024 Instituto Nacional de Tecnología Industrial
# Copyright (c) 2019 Romain Deterre (@rdeterre)
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)
# Adapted from: https://github.com/johnbeard/kiplot/pull/10
import os
from re import compile
from datetime import datetime
from .gs import GS
from .kiplot import run_command
from .misc import UI_SMD, UI_VIRTUAL, MOD_THROUGH_HOLE, MOD_SMD, MOD_EXCLUDE_FROM_POS_FILES
from .optionable import Optionable
from .out_base import VariantOptions
from .error import KiPlotConfigurationError
from .macros import macros, document, output_class  # noqa: F401
from . import log

logger = log.get_logger()
ref_re = compile(r'([^\d]+)([\?\d]+)')
DEFAULT_COLUMNS = ['Ref', 'Val', 'Package', 'PosX', 'PosY', 'Rot', 'Side']


def _ref_key(ref_str):
    """ Splits a reference intro prefix and suffix.
        Helps to sort references in a natural way. """
    m = ref_re.match(ref_str)
    if not m:
        return [ref_str]
    pre, suf = m.groups()
    return [pre, 0 if suf == '?' else int(suf)]


def check_names(top, bot):
    if top == bot:
        raise KiPlotConfigurationError("Asking for two separated files, but both with the same name.\n"
                                       "Try using %i in the name.")


class PosColumns(Optionable):
    """ Which columns we want and its names """
    _default = DEFAULT_COLUMNS

    def __init__(self, id=None, name=None):
        super().__init__()
        self._unknown_is_error = True
        with document:
            self.id = ''
            """ *[Ref,Val,Package,PosX,PosY,Rot,Side] Internal name """
            self.name = ''
            """ Name to use in the output file. The id is used when empty """
        self._id_example = 'Ref'
        self._name_example = 'Reference'
        if id is not None:
            self.id = id
            self.name = name

    def config(self, parent):
        super().config(parent)
        if not self.id:
            raise KiPlotConfigurationError("Missing or empty `id` in columns list ({})".format(str(self._tree)))

    def __str__(self):
        return f'{self.id} -> {self.name}'


class PositionOptions(VariantOptions):
    def __init__(self):
        with document:
            self.format = 'ASCII'
            """ *[ASCII,CSV,GBR] Format for the position file.
                Note that the gerber format (GBR) needs KiCad 7+ and doesn't support most of the options.
                Only the options that explicitly say the format is supported """
            self.separate_files_for_front_and_back = True
            """ *Generate two separated files, one for the top and another for the bottom """
            self.only_smd = True
            """ *Only include the surface mount components """
            self.output = GS.def_global_output
            """ *Output file name (%i='top_pos'|'bottom_pos'|'both_pos', %x='pos'|'csv'|'gbr').
                Important: when using separate files you must use `%i` to differentiate them """
            self.units = 'millimeters'
            """ *[millimeters,inches,mils] Units used for the positions. Affected by global options """
            self.columns = PosColumns
            """ [list(dict)|list(string)] Which columns are included in the output """
            self.right_digits = 4
            """ number of digits for mantissa part of coordinates (0 is auto) """
            self.bottom_negative_x = False
            """ Use negative X coordinates for footprints on bottom layer """
            self.use_aux_axis_as_origin = True
            """ Use the auxiliary axis as origin for coordinates (KiCad default).
                Supported by the gerber format """
            self.include_virtual = False
            """ Include virtual components. For special purposes, not pick & place.
                Note that virtual components is a KiCad 5 concept.
                For KiCad 6+ we replace this concept by the option to exclude from position file """
            self.quote_all = False
            """ When generating the CSV quote all values, even numbers """
            self.separator = ','
            """ CSV Separator. Only used for CSV format.
                Only one character can be specified """
            self.gerber_board_edge = False
            """ Include the board edge in the gerber output """
        super().__init__()
        self._expand_id = 'position'

    def config(self, parent):
        super().config(parent)
        new_columns = []
        for col in self.columns:
            if isinstance(col, str):
                # Just a string, add to the list of used
                new_name = new_col = col
            else:
                new_col = col.id
                new_name = col.name if col.name else new_col
            new_columns.append(PosColumns(new_col, new_name))
        self._columns = new_columns
        self._expand_ext = 'pos' if self.format == 'ASCII' else self.format.lower()
        if len(self.separator) != 1:
            raise KiPlotConfigurationError('The CSV separator must be one character (`{}`)'.format(self.separator))

    def _do_position_plot_ascii(self, output_dir, columns, modulesStr, maxSizes, modules_side):
        topf = None
        botf = None
        bothf = None
        if self.separate_files_for_front_and_back:
            topf_name = self.expand_filename(output_dir, self.output, 'top_pos', 'pos')
            botf_name = self.expand_filename(output_dir, self.output, 'bottom_pos', 'pos')
            check_names(topf_name, botf_name)
            topf = open(topf_name, 'w')
            botf = open(botf_name, 'w')
        else:
            fname = self.expand_filename(output_dir, self.output, 'both_pos', 'pos')
            bothf = open(fname, 'w')

        files = [f for f in [topf, botf, bothf] if f is not None]
        for f in files:
            f.write('### Module positions - created on {} ###\n'.format(datetime.now().strftime("%a %d %b %Y %X %Z")))
            f.write('### Printed by KiBot\n')
            unit = {'millimeters': 'mm', 'inches': 'in', 'mils': 'mils'}[self.units]
            f.write('## Unit = {}, Angle = deg.\n'.format(unit))

        if topf is not None:
            topf.write('## Side : top\n')
        if botf is not None:
            botf.write('## Side : bottom\n')
        if bothf is not None:
            bothf.write('## Side : both\n')

        for f in files:
            f.write('# ')
            for idx, col in enumerate(columns):
                if idx > 0:
                    f.write("   ")
                f.write("{0: <{width}}".format(col, width=maxSizes[idx]))
            f.write('\n')

        # Account for the "# " at the start of the comment column
        maxSizes[0] = maxSizes[0] + 2

        for (m, is_bottom) in zip(modulesStr, modules_side):
            file = bothf if bothf is not None else (botf if is_bottom else topf)
            for idx, col in enumerate(m):
                if idx > 0:
                    file.write("   ")
                file.write("{0: <{width}}".format(col, width=maxSizes[idx]))
            file.write("\n")

        for f in files:
            f.write("## End\n")

        if topf is not None:
            topf.close()
        if botf is not None:
            botf.close()
        if bothf is not None:
            bothf.close()

    def _do_position_plot_csv(self, output_dir, columns, modulesStr, modules_side):
        topf = None
        botf = None
        bothf = None
        if self.separate_files_for_front_and_back:
            topf_name = self.expand_filename(output_dir, self.output, 'top_pos', 'csv')
            botf_name = self.expand_filename(output_dir, self.output, 'bottom_pos', 'csv')
            check_names(topf_name, botf_name)
            topf = open(topf_name, 'w')
            botf = open(botf_name, 'w')
        else:
            bothf = open(self.expand_filename(output_dir, self.output, 'both_pos', 'csv'), 'w')

        files = [f for f in [topf, botf, bothf] if f is not None]

        for f in files:
            f.write(self.separator.join(columns))
            f.write("\n")

        for (m, is_bottom) in zip(modulesStr, modules_side):
            file = bothf if bothf is not None else (botf if is_bottom else topf)
            file.write(self.separator.join('{}'.format(e) for e in m))
            file.write("\n")

        if topf is not None:
            topf.close()
        if botf is not None:
            botf.close()
        if bothf is not None:
            bothf.close()

    @staticmethod
    def is_pure_smd_5(m):
        return m.GetAttributes() == UI_SMD

    @staticmethod
    def is_pure_smd_6(m):
        return m.GetAttributes() & (MOD_THROUGH_HOLE | MOD_SMD | MOD_EXCLUDE_FROM_POS_FILES) == MOD_SMD

    @staticmethod
    def is_not_virtual_5(m):
        return m.GetAttributes() != UI_VIRTUAL

    @staticmethod
    def is_not_virtual_6(m):
        return not (m.GetAttributes() & MOD_EXCLUDE_FROM_POS_FILES)

    @staticmethod
    def get_attr_tests():
        if GS.ki5:
            return PositionOptions.is_pure_smd_5, PositionOptions.is_not_virtual_5
        return PositionOptions.is_pure_smd_6, PositionOptions.is_not_virtual_6

    def get_targets(self, out_dir):
        ext = self._expand_ext
        if self.separate_files_for_front_and_back:
            return [self.expand_filename(out_dir, self.output, 'top_pos', ext),
                    self.expand_filename(out_dir, self.output, 'bottom_pos', ext)]
        return [self.expand_filename(out_dir, self.output, 'both_pos', ext)]

    def run_gerber(self, output_dir):
        if not GS.ki7:
            raise KiPlotConfigurationError("Gerber position needs KiCad 7+")

        pcb_name = self.save_tmp_board_if_variant()
        cmd_base = ['kicad-cli', 'pcb', 'export', 'pos', '--format', 'gerber']
        if self.use_aux_axis_as_origin:
            cmd_base.append('--use-drill-file-origin')
        if self.gerber_board_edge:
            cmd_base.append('--gerber-board-edge')
        cmd_base.append('--side')

        fname = self.expand_filename(output_dir, self.output, 'top_pos', self._expand_ext)
        run_command(cmd_base+['front', '-o', fname, pcb_name])

        fname = self.expand_filename(output_dir, self.output, 'bottom_pos', self._expand_ext)
        run_command(cmd_base+['back', '-o', fname, pcb_name])

    def run(self, fname):
        super().run(fname)
        output_dir = os.path.dirname(fname)
        if self.format == 'GBR':
            self.run_gerber(output_dir)
            return
        self.filter_pcb_components()
        columns = tuple(o.name for o in self._columns)
        conv = GS.unit_name_to_scale_factor(self.units)
        # Format all strings
        comps_hash = self.get_refs_hash_multi()
        modules = []
        modules_side = []
        is_pure_smd, is_not_virtual = self.get_attr_tests()
        quote_char = '"' if self.format == 'CSV' else ''
        quote_char_extra = quote_char if self.quote_all else ''
        x_origin = 0.0
        y_origin = 0.0
        if self.use_aux_axis_as_origin:
            (x_origin, y_origin) = GS.get_aux_origin()
            logger.debug('Using auxiliary origin: x={} y={}'.format(x_origin, y_origin))
        for m in sorted(GS.get_modules(), key=lambda c: _ref_key(c.GetReference())):
            ref = m.GetReference()
            logger.debug('P&P ref: {}'.format(ref))
            value = None
            # Apply any filter or variant data
            if comps_hash:
                c = comps_hash.get(ref, None)
                if c:
                    # Multiple components with the same reference is "normal" for a panel
                    c = c.pop()
                    logger.debug('- fit: {} include: {}'.format(c.fitted, c.included))
                    if not c.fitted or not c.included:
                        continue
                    value = c.value
                    footprint = c.footprint
                    is_bottom = c.bottom
                    rotation = c.footprint_rot
                    # Here we can't use c.footprint_x/y because this doesn't work for panels
                    center = GS.get_center(m)
                    center_x = center.x
                    center_y = center.y
                    if c.pos_offset_x is not None:
                        # Offset from the rotation filter
                        # logger.error(f"{center_x},{center_y} -> {center_x+c.pos_offset_x},{center_y+c.pos_offset_y}")
                        center_x += c.pos_offset_x
                        center_y += c.pos_offset_y
            if value is None:
                value = m.GetValue()
                footprint = str(m.GetFPID().GetLibItemName())  # pcbnew.UTF8 type
                is_bottom = m.IsFlipped()
                rotation = m.GetOrientationDegrees()
                center = GS.get_center(m)
                center_x = center.x
                center_y = center.y
            # If passed check the position options
            if (self.only_smd and is_pure_smd(m)) or (not self.only_smd and (is_not_virtual(m) or self.include_virtual)):
                # KiCad: PLACE_FILE_EXPORTER::GenPositionData() in export_footprints_placefile.cpp
                row = []
                if self.right_digits != 0:
                    float_format = "{{:.{}f}}".format(self.right_digits)
                else:
                    float_format = "{}"
                for col in self._columns:
                    k = col.id
                    if k == 'Ref':
                        row.append(quote_char+ref+quote_char)
                    elif k == 'Val':
                        row.append(quote_char+value+quote_char)
                    elif k == 'Package':
                        row.append(quote_char+footprint+quote_char)
                    elif k == 'PosX':
                        pos_x = (center_x - x_origin) * conv
                        if self.bottom_negative_x and is_bottom:
                            pos_x = -pos_x
                        row.append(quote_char_extra+float_format.format(pos_x, rd=self.right_digits)+quote_char_extra)
                    elif k == 'PosY':
                        row.append(quote_char_extra+float_format.format(-(center_y - y_origin) * conv, rd=self.right_digits) +
                                   quote_char_extra)
                    elif k == 'Rot':
                        row.append(quote_char_extra+float_format.format(rotation, rd=self.right_digits)+quote_char_extra)
                    elif k == 'Side':
                        row.append(quote_char_extra+("bottom" if is_bottom else "top")+quote_char_extra)
                modules.append(row)
                modules_side.append(is_bottom)
            else:
                logger.debug('- pure_smd: {} not_virtual {}'.format(is_pure_smd(m), is_not_virtual(m)))
        # Find max width for all columns
        maxlengths = []
        for col, name in enumerate(columns):
            max_l = len(name)
            for row in modules:
                max_l = max(max_l, len(row[col]))
            maxlengths.append(max_l)
        # Note: the parser already checked the format is ASCII or CSV
        if self.format == 'ASCII':
            self._do_position_plot_ascii(output_dir, columns, modules, maxlengths, modules_side)
        else:  # if self.format == 'CSV':
            self._do_position_plot_csv(output_dir, columns, modules, modules_side)
        self.unfilter_pcb_components()


@output_class
class Position(BaseOutput):  # noqa: F821
    """ Pick & place
        Generates the file with position information for the PCB components, used by the pick and place machine.
        This output is what you get from the 'File/Fabrication output/Footprint position (.pos) file' menu in pcbnew.
        Note that if you need a more customized output you can use the *bom* output, which can include positions. """
    def __init__(self):
        super().__init__()
        with document:
            self.options = PositionOptions
            """ *[dict={}] Options for the `position` output """
        self._category = 'PCB/fabrication/assembly'

    def get_csv_separator(self):
        return self.options.separator

    @staticmethod
    def get_conf_examples(name, layers):
        outs = []
        has_top = False
        has_bottom = False
        for la in layers:
            if la.is_top():
                has_top = la.components
            elif la.is_bottom():
                has_bottom = la.components
        for fmt in ['ASCII', 'CSV']:
            gb = {}
            gb['name'] = 'basic_position_{}'.format(fmt)
            gb['comment'] = 'Components position for Pick & Place'
            gb['type'] = name
            gb['dir'] = 'Position'
            ops = {'format': fmt, 'only_smd': False}
            if not has_top or not has_bottom:
                ops['separate_files_for_front_and_back'] = False
            gb['options'] = ops
            outs.append(gb)
        return outs
