# -*- coding: utf-8 -*-
# Copyright (c) 2022-2024 Salvador E. Tropea
# Copyright (c) 2022-2024 Instituto Nacional de Tecnología Industrial
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)
"""
Dependencies:
  - name: QRCodeGen
    role: mandatory
    python_module: true
    downloader: python
    debian: python3-qrcodegen
"""
import os
from .gs import GS
from .misc import W_NOQR
from .optionable import BaseOptions, Optionable
from .error import KiPlotConfigurationError
from .kicad.pcb import save_pcb_from_sexp
from .kicad.sexpdata import Symbol, dumps, Sep, sexp_iter
from .kicad.sexp_helpers import make_separated, load_sexp_file
from .kicad.v6_sch import DrawRectangleV6, PointXY, Stroke, Fill, SchematicFieldV6, FontEffects
from .macros import macros, document, output_class  # noqa: F401
from . import log
try:
    import qrcodegen
except ImportError:
    qrcodegen = None

logger = log.get_logger()
SHEET_FILE = {'Sheet file', 'Sheetfile'}


def is_symbol(name, sexp):
    return isinstance(sexp, list) and len(sexp) >= 1 and isinstance(sexp[0], Symbol) and sexp[0].value() == name


def is_field(s):
    if GS.ki10:
        # KiCad 10: (property "FieldN" "VALUE"
        # This is like the schematic
        return (is_symbol('property', s) and len(s) > 2 and isinstance(s[1], str) and s[1].startswith('Field') and
                isinstance(s[2], str))
    # KiCad 6 to 9: (fp_text user "VALUE" ...
    return (is_symbol('fp_text', s) and len(s) > 2 and isinstance(s[1], Symbol) and s[1].value() == 'user' and
            isinstance(s[2], str))


def compute_size(qr, is_sch=True, use_mm=True):
    if is_sch:
        qrc = qr._code_sch
        full_size = qr.size_sch
    else:
        qrc = qr._code_pcb
        full_size = qr.size_pcb
    size = qrc.get_size()
    if not is_sch and qr.pcb_negative:
        size += 2
    if use_mm:
        full_size *= 1 if qr.size_units == 'millimeters' else 25.4
        center = round(full_size/2, 2)
        size_rect = round(full_size/size, 2)
    else:
        full_size *= 39.37007874 if qr.size_units == 'millimeters' else 1000
        center = round(full_size/2)
        size_rect = full_size/size
    return qrc, size, full_size, center, size_rect


class QRCodeOptions(Optionable):
    """ A QR code """
    def __init__(self, field=None):
        super().__init__()
        with document:
            self.name = 'QR'
            """ *Name for the symbol/footprint """
            self.text = '%p %r'
            """ *Text to encode as QR """
            self.correction_level = 'low'
            """ [low,medium,quartile,high] Error correction level """
            self.size_sch = 15
            """ *Size of the QR symbol """
            self.size_pcb = 15
            """ *Size of the QR footprint """
            self.size_units = 'millimeters'
            """ [millimeters,inches] Units used for the size """
            self.layer = 'silk'
            """ *[silk,copper] Layer for the footprint """
            self.pcb_negative = False
            """ Generate a negative image for the PCB """
        self._unknown_is_error = True

    def config(self, parent):
        super().config(parent)
        self.layer = 'F.SilkS' if self.layer == 'silk' else 'F.Cu'

    def __str__(self):
        return f'`{self.name} "{self.text}" ({self.size_sch}/{self.size_pcb} {self.size_units}) [{self.layer}]'


class QR_LibOptions(BaseOptions):
    def __init__(self):
        with document:
            self.output = GS.def_global_output
            """ *Filename/dirname for the output library (%i=qr, %x=lib/kicad_sym/pretty).
                You must use %x in the name to get a symbols lib and a footprints lib """
            self.lib = 'QR'
            """ *Short name for the library """
            self.reference = 'QR'
            """ The reference prefix """
            self.use_sch_dir = True
            """ Generate the libs relative to the schematic/PCB dir """
            self.qrs = QRCodeOptions
            """ *[dict|list(dict)=[{}]] QR codes to include in the library """
        super().__init__()
        self._expand_id = 'qr'
        self._expand_ext = 'lib'

    def config(self, parent):
        super().config(parent)
        names = set()
        for qr in self.qrs:
            if qr.name in names:
                raise KiPlotConfigurationError("QR code name `{}` repeated".format(qr.name))
            names.add(qr.name)

    def symbol_k5(self, f, qr):
        # Compute the size
        qrc, size, full_size, center, size_rect = compute_size(qr, use_mm=False)
        # Generate the symbol
        f.write("#\n# {}\n#\n".format(qr.name))
        f.write("DEF {} {} 0 {} N N 1 F N\n".format(qr.name, '#'+self.reference, 0))
        # Reference
        f.write('F0 "{}" {} {} 50 H I L BNN\n'.format('#'+self.reference, -center, center+60))
        # Value
        f.write('F1 "{}" {} {} 50 H I L TNN\n'.format(qr.name, -center, -center))
        # Footprint
        f.write('F2 "{}:{}" 0 150 50 H I C CNN\n'.format(self.lib, qr.name))
        # Datasheet
        f.write('F3 "" 0 0 50 H I C CNN\n')
        # QR information
        f.write('F4 "{}" 0 0 50 H I C CNN "qr_version"\n'.format(qrc.get_version()))
        f.write('F5 "{}" 0 0 50 H I C CNN "qr_size"\n'.format(size))
        ecc = qrc.get_error_correction_level()
        f.write('F6 "{},{}" 0 0 50 H I C CNN "qr_ecc"\n'.format(ecc.ordinal, ecc.formatbits))
        f.write('F7 "{}" 0 0 50 H I C CNN "qr_mask"\n'.format(qrc.get_mask()))
        f.write('F8 "{}" 0 0 50 H I C CNN "qr_text"\n'.format(qr._text_sch.replace('"', '\"')))
        f.write("DRAW\n")
        for y in range(size):
            for x in range(size):
                if qrc.get_module(x, y):
                    x_pos = round(x*size_rect-center)
                    y_pos = round(center-y*size_rect)
                    f.write('S {} {} {} {} 0 0 1 F\n'.format(x_pos, y_pos, round(x_pos+size_rect), round(y_pos+size_rect)))
        f.write("ENDDRAW\n")
        f.write("ENDDEF\n")

    def fp_field(self, center, name, value, layer, id):
        if id == 0:
            pos_y = center+1.25
        else:
            pos_y = -(center+1.25+1.7*(id-1))
        fld = [Symbol('fp_text'), Symbol(name), value]
        fld.append([Symbol('at'), 0, pos_y])
        fld.append([Symbol('layer'), Symbol(layer)])
        if name == 'user':
            fld.append(Symbol('hide'))
        fld.append(Sep())
        font = [Symbol('font')]
        font.append([Symbol('size'), 1, 1])
        font.append([Symbol('thickness'), 0.15])
        fld.append([Symbol('effects'), font])
        fld.append(Sep())
        return fld

    def qr_draw_fp(self, size, size_rect, center, qrc, negative, layer, do_sep=True):
        mod = []
        is_bottom = layer[0] == 'B'
        for y in range(size):
            for x in range(size):
                if qrc.get_module(x-negative, y-negative) ^ negative:
                    x_pos = round(x*size_rect-center, 2)
                    y_pos = round(y*size_rect-center, 2)
                    x_pos2 = round(x_pos+size_rect, 2)
                    y_pos2 = round(y_pos+size_rect, 2)
                    rect = [Symbol('fp_poly')]  # fp_rect not in v5
                    pts = [Symbol('pts')]
                    if is_bottom:
                        y_pos = -y_pos
                        y_pos2 = -y_pos2
                    pts.append([Symbol('xy'), x_pos, y_pos])
                    pts.append([Symbol('xy'), x_pos, y_pos2])
                    pts.append([Symbol('xy'), x_pos2, y_pos2])
                    pts.append([Symbol('xy'), x_pos2, y_pos])
                    rect.append(pts)
                    if layer:
                        rect.append([Symbol('layer'), Symbol(layer)])
                    rect.append([Symbol('width'), 0])
                    mod.append(rect)
                    if do_sep:
                        mod.append(Sep())
        return mod

    def qr_draw_sym(self, size, size_rect, center, qrc, do_sep=True):
        mod = []
        for y in range(size):
            for x in range(size):
                if qrc.get_module(x, y):
                    x_pos = round(x*size_rect-center, 2)
                    y_pos = round(center-y*size_rect, 2)
                    rect = DrawRectangleV6()
                    rect.start = PointXY(x_pos, y_pos)
                    rect.end = PointXY(round(x_pos+size_rect, 2), round(y_pos-size_rect, 2))
                    rect.stroke = Stroke()
                    rect.stroke.width = 0.001
                    rect.fill = Fill()
                    rect.fill.type = 'outline'
                    mod.append(rect.write())
                    if do_sep:
                        mod.append(Sep())
        return mod

    def footprint(self, dir, qr):
        # Compute the size
        qrc, size, full_size, center, size_rect = compute_size(qr, is_sch=False)
        # Generate the footprint
        fname = os.path.join(dir, qr.name+'.kicad_mod')
        mod = [Symbol('module'), Symbol(qr.name)]
        mod.append([Symbol('layer'), Symbol(qr.layer)])
        mod.append([Symbol('tedit'), 0])
        mod.append(Sep())
        attrs = [Symbol('attr')]
        if not GS.ki6:
            # KiCad 5
            attrs.append(Symbol('virtual'))
        else:
            attrs.append(Symbol('exclude_from_pos_files'))
            attrs.append(Symbol('exclude_from_bom'))
            if GS.ki7:
                attrs.append(Symbol('allow_missing_courtyard'))
        mod.append(attrs)
        mod.append(Sep())
        mod.append(self.fp_field(center, 'reference', self.reference+'***', qr.layer, 0))
        mod.append(Sep())
        mod.append(self.fp_field(center, 'value', qr.name, qr.layer, 1))
        mod.append(Sep())
        mod.append(self.fp_field(center, 'user', 'qr_version: '+str(qrc.get_version()), qr.layer, 2))
        mod.append(Sep())
        mod.append(self.fp_field(center, 'user', 'qr_size: '+str(size), qr.layer, 3))
        mod.append(Sep())
        ecc = qrc.get_error_correction_level()
        mod.append(self.fp_field(center, 'user', 'qr_ecc: {},{}'.format(ecc.ordinal, ecc.formatbits), qr.layer, 4))
        mod.append(Sep())
        mod.append(self.fp_field(center, 'user', 'qr_mask: '+str(qrc.get_mask()), qr.layer, 5))
        mod.append(Sep())
        mod.append(self.fp_field(center, 'user', qr._text_pcb, qr.layer, 6))
        mod.append(Sep())
        # The QR itself
        mod.extend(self.qr_draw_fp(size, size_rect, center, qrc, qr.pcb_negative, qr.layer))
        with open(fname, 'wt') as f:
            f.write(dumps(mod))
            f.write('\n')

    def symbol_lib_k5(self, output):
        logger.debug('Creating KiCad 5 symbols library: '+output)
        with open(output, 'wt') as f:
            f.write("EESchema-LIBRARY Version 2.4\n")
            f.write("#encoding utf-8\n")
            for qr in self.qrs:
                logger.debug('Adding symbol: '+qr.name)
                self.symbol_k5(f, qr)
            f.write("#\n#End Library\n")

    def sym_field(self, center, name, value, id):
        if id == 0:
            pos_y = center+1.25
        else:
            pos_y = -(center+1.25+1.7*(id-1))
        f = SchematicFieldV6(name, str(value), id, 0, round(pos_y, 2))
        if id > 1:
            f.effects = FontEffects()
            f.effects.hide = True
        return f.write()+[Sep()]

    def symbol_lib_k6(self, output):
        logger.debug('Creating KiCad 6 symbols library: '+output)
        # Lib header
        lib = [Symbol('kicad_symbol_lib')]
        lib.append([Symbol('version'), 20211014])
        lib.append([Symbol('generator'), Symbol('kibot')])
        lib.append(Sep())
        for qr in self.qrs:
            logger.debug('Adding symbol: '+qr.name)
            # Compute the size
            qrc, size, full_size, center, size_rect = compute_size(qr)
            # Symbol main attributes
            sym = [Symbol('symbol'), qr.name]
            sym.append([Symbol('pin_numbers'), Symbol('hide')])
            sym.append([Symbol('pin_names'), Symbol('hide')])
            sym.append([Symbol('in_bom'), Symbol('no')])
            sym.append([Symbol('on_board'), Symbol('yes')])
            sym.append(Sep())
            # Properties (Fields)
            sym.append(self.sym_field(center, 'Reference', '#'+self.reference, 0))
            sym.append(Sep())
            sym.append(self.sym_field(center, 'Value', qr.name, 1))
            sym.append(Sep())
            sym.append(self.sym_field(center, 'Footprint', self.lib+':'+qr.name, 2))
            sym.append(Sep())
            sym.append(self.sym_field(center, 'Datasheet', '', 3))
            sym.append(Sep())
            sym.append(self.sym_field(center, 'qr_version', qrc.get_version(), 4))
            sym.append(Sep())
            sym.append(self.sym_field(center, 'qr_size', size, 5))
            sym.append(Sep())
            ecc = qrc.get_error_correction_level()
            sym.append(self.sym_field(center, 'qr_ecc', '{},{}'.format(ecc.ordinal, ecc.formatbits), 6))
            sym.append(Sep())
            sym.append(self.sym_field(center, 'qr_mask', qrc.get_mask(), 7))
            sym.append(Sep())
            sym.append(self.sym_field(center, 'qr_text', qr._text_sch, 8))
            sym.append(Sep())
            if GS.ki7:
                sym.append(self.sym_field(center, 'Sim.Enable', "0", 9))
                sym.append(Sep())
            sym.extend(self.qr_draw_sym(size, size_rect, center, qrc))
            lib.append(sym)
            lib.append(Sep())
        with open(output, 'wt') as f:
            f.write(dumps(lib))
            f.write('\n')

    @staticmethod
    def find_layer(sexp, def_layer):
        """ Determine the layer.
            The user could move the footprint to the bottom layer """
        # Look for the polys
        poly = next(filter(lambda s: is_symbol('fp_poly', s), sexp), None)
        if not poly:
            return def_layer
        layer = next(filter(lambda s: is_symbol('layer', s), poly), None)
        if not layer or len(layer) != 2:
            return def_layer
        return layer[1]

    def update_footprint(self, name, sexp, qr):
        logger.debug('- Updating QR footprint: '+name)
        # Compute the size
        qrc, size, full_size, center, size_rect = compute_size(qr, is_sch=False)
        # In which layer are the drawings? (default to the original)
        layer = self.find_layer(sexp, qr.layer)
        if isinstance(layer, Symbol):
            layer = layer.value()
        # Remove old drawing
        sexp[:] = list(filter(lambda s: not is_symbol('fp_poly', s), sexp))
        # Add the new drawings
        sexp.extend(self.qr_draw_fp(size, size_rect, center, qrc, qr.pcb_negative, layer, do_sep=False))
        # Update the fields
        for s in sexp:
            if is_field(s):
                res = s[2].split(':')
                if len(res) > 1:
                    logger.debug('- Updating field `{}`'.format(res[0]))
                    if res[0] == 'qr_version':
                        s[2] = 'qr_version: '+str(qrc.get_version())
                    elif res[0] == 'qr_size':
                        s[2] = 'qr_size: '+str(size)
                    elif res[0] == 'qr_ecc':
                        ecc = qrc.get_error_correction_level()
                        s[2] = 'qr_ecc: {},{}'.format(ecc.ordinal, ecc.formatbits)
                    elif res[0] == 'qr_mask':
                        s[2] = 'qr_mask: '+str(qrc.get_mask())
                elif s[2][0] == ' ':
                    logger.debug('- Updating text `{}`'.format(qr._text_pcb))
                    s[2] = ' '+qr._text_pcb

    def update_footprints(self, known_qrs):
        # Replace known QRs in the PCB
        updated = False
        pcb = load_sexp_file(GS.pcb_file)
        for iter in [sexp_iter(pcb, 'kicad_pcb/module'), sexp_iter(pcb, 'kicad_pcb/footprint')]:
            for s in iter:
                if len(s) < 2:
                    continue
                if isinstance(s[1], Symbol):
                    name = s[1].value().lower()
                else:
                    name = s[1].lower()
                if name in known_qrs:
                    updated = True
                    self.update_footprint(name, s, known_qrs[name])
        # Save the resulting PCB
        if updated:
            save_pcb_from_sexp(pcb, logger)

    def update_symbol(self, name, c_name, sexp, qr):
        logger.debug('- Updating QR symbol: '+name)
        # Compute the size
        qrc, size, full_size, center, size_rect = compute_size(qr)
        # Create the new drawings
        sub_unit_name = c_name+"_1_1"
        sub_unit_sexp = [Symbol('symbol'), sub_unit_name]
        sub_unit_sexp.extend(self.qr_draw_sym(size, size_rect, center, qrc, do_sep=False))
        # Replace the old one
        for s in sexp_iter(sexp, 'symbol'):
            if len(s) >= 2 and isinstance(s[1], str) and s[1] == sub_unit_name:
                s[:] = list(sub_unit_sexp)
        # Update the fields
        for s in sexp:
            if is_symbol('property', s) and len(s) > 2 and isinstance(s[1], str) and isinstance(s[2], str):
                new_val = None
                field = s[1]
                if field == 'qr_version':
                    new_val = str(qrc.get_version())
                elif field == 'qr_size':
                    new_val = str(size)
                elif field == 'qr_ecc':
                    ecc = qrc.get_error_correction_level()
                    new_val = '{},{}'.format(ecc.ordinal, ecc.formatbits)
                elif field == 'qr_mask':
                    new_val = str(qrc.get_mask())
                elif field == 'qr_text':
                    new_val = qr._text_sch
                if new_val is not None:
                    logger.debug('- Updating field `{}` {} -> {}'.format(field, s[2], new_val))
                    s[2] = new_val

    def update_symbols(self, fname, sexp, known_qrs):
        # Replace known QRs in the Schematic
        updated = False
        for s in sexp_iter(sexp, 'kicad_sch/lib_symbols/symbol'):
            if len(s) < 2 or not isinstance(s[1], str):
                continue
            name = s[1].lower()
            c_name = s[1].split(':')[1]
            if name in known_qrs:
                updated = True
                self.update_symbol(name, c_name, s, known_qrs[name])
        # Save the resulting Schematic
        if updated:
            # Make it readable
            separated = make_separated(sexp[0])
            # Create a back-up and save it in the original place
            logger.debug('- Replacing the old SCH')
            GS.make_bkp(fname)
            with open(fname, 'wt') as f:
                f.write(dumps(separated))
                f.write('\n')

    def load_k6_sheets(self, fname, sheets=None):
        logger.debug('- Loading '+fname)
        sheet = load_sexp_file(fname)
        if sheets is None:
            sheets = {}
        sheets[fname] = sheet
        if not is_symbol('kicad_sch', sheet[0]):
            raise KiPlotConfigurationError('No kicad_sch signature in '+fname)
        path = os.path.dirname(fname)
        for s in sexp_iter(sheet, 'kicad_sch/sheet'):
            sub_name = None
            for prop in sexp_iter(s, 'property'):
                if len(prop) > 2 and isinstance(prop[1], str) and isinstance(prop[2], str) and prop[1] in SHEET_FILE:
                    sub_name = prop[2]
            if sub_name is not None:
                sub_name = os.path.abspath(os.path.join(path, sub_name))
                if sub_name not in sheets:
                    self.load_k6_sheets(os.path.join(path, sub_name), sheets)
        return sheets

    def run(self, output):
        global qrcodegen
        if qrcodegen is None:
            qrcodegen = self.ensure_tool('QRCodeGen')
        if not self.get_user_defined('qrs'):
            logger.warning(W_NOQR+'Using a default QR configuration, please provide one')
        # Now we are sure we have qrcodegen
        QR_ECCS = {'low': qrcodegen.QrCode.Ecc.LOW,
                   'medium': qrcodegen.QrCode.Ecc.MEDIUM,
                   'quartile': qrcodegen.QrCode.Ecc.QUARTILE,
                   'high': qrcodegen.QrCode.Ecc.HIGH}
        if self.use_sch_dir:
            self._odir_sch = GS.sch_dir
            self._odir_pcb = GS.pcb_dir
        else:
            self._odir_pcb = self._odir_sch = self._parent.output_dir
        self._expand_ext = 'pretty'
        dir_pretty = os.path.join(self._odir_pcb, self.expand_filename_pcb(self.output))
        self._expand_ext = 'lib' if GS.ki5 else 'kicad_sym'
        sch_output = os.path.join(self._odir_sch, self.expand_filename_sch(self.output))
        if sch_output == dir_pretty:
            raise KiPlotConfigurationError(f'The symbol and footprint outputs are the same, use %x to solve it ({sch_output})')
        # Create the QR codes
        for qr in self.qrs:
            qr._text_sch = self.expand_filename_both(qr.text, make_safe=False)
            qr._code_sch = qrcodegen.QrCode.encode_text(qr._text_sch, QR_ECCS[qr.correction_level])
            qr._text_pcb = self.expand_filename_both(qr.text, is_sch=False, make_safe=False)
            qr._code_pcb = qrcodegen.QrCode.encode_text(qr._text_pcb, QR_ECCS[qr.correction_level])
        # Create the symbols
        if GS.ki5:
            self.symbol_lib_k5(sch_output)
        else:
            self.symbol_lib_k6(sch_output)
        # Create the footprints
        logger.debug('Creating footprints library: '+dir_pretty)
        os.makedirs(dir_pretty, exist_ok=True)
        for qr in self.qrs:
            logger.debug('Adding footprint: '+qr.name)
            self.footprint(dir_pretty, qr)
        # Update the files
        if self._parent._update_mode:
            logger.debug('Updating the PCB and schematic')
            # Create a dict with the known QRs
            known_qrs = {}
            for qr in self.qrs:
                name = self.lib+':'+qr.name
                known_qrs[name.lower()] = qr
            # PCB
            self.update_footprints(known_qrs)
            # Schematic
            if GS.ki6:
                # KiCad 5 reads the lib, but KiCad 6 is more like the PCB
                assert GS.sch_file is not None
                sheets = self.load_k6_sheets(GS.sch_file)
                for k, v in sheets.items():
                    self.update_symbols(k, v, known_qrs)


@output_class
class QR_Lib(BaseOutput):  # noqa: F821
    """ QR_Lib
        Generates a QR code symbol and footprint.
        This output creates a library containing a symbol and footprint for a QR code.
        To refresh the generated symbols and footprints use the `update_qr` preflight.
        The workflow is as follows:
        - Create the symbol and footprints using this output.
        - Use them in your schematic and PCB.
        - To keep them updated add the `update_qr` preflight """
    def __init__(self):
        super().__init__()
        # Make it high priority so it gets created before all the other outputs
        self.priority = 90
        with document:
            self.options = QR_LibOptions
            """ *[dict={}] Options for the `boardview` output """
        self._both_related = True
        self._update_mode = False
        # The help is inherited and already mentions the default priority
        self.fix_priority_help()

    @staticmethod
    def get_conf_examples(name, layers):
        gb = {}
        gb['name'] = 'basic_qr_lib_example'
        gb['comment'] = 'QR code symbol and footprint example'
        gb['type'] = name
        gb['dir'] = 'QR_libs'
        qr1 = {'correction_level': 'medium', 'name': 'QR_data', 'pcb_negative': True}
        qr2 = {'correction_level': 'medium', 'name': 'QR_kibot', 'text': 'https://github.com/INTI-CMNB/KiBot/'}
        gb['options'] = {'qrs': [qr1, qr2], 'use_sch_dir': False}
        return [gb]
