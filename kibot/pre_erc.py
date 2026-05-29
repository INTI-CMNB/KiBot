# -*- coding: utf-8 -*-
# Copyright (c) 2020-2024 Salvador E. Tropea
# Copyright (c) 2020-2024 Instituto Nacional de Tecnología Industrial
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)
# https://gitlab.com/kicad/code/kicad/-/blob/master/resources/schemas/erc.v1.json?ref_type=heads
import csv
import io
from .pre_any_xrc import ERCOptions, XRC
from .macros import macros, document, pre_class  # noqa: F401
from .gs import GS
from .misc import W_ERC, W_FILXRC, UNITS_2_KICAD
from .log import get_logger
logger = get_logger(__name__)


@pre_class
class ERC(XRC):  # noqa: F821
    """ ERC
        Runs the ERC (Electrical Rules Check). To ensure the schematic is electrically correct.
        You need a valid *sym-lib-table* installed. If not KiBot will try to temporarily install the template.
        This is a replacement for the *run_erc* preflight that needs KiCad 8 or newer """
    def __init__(self):
        super().__init__(ERCOptions)
        self._sch_related = True
        self._expand_id = 'erc'
        self._category = 'Schematic/docs'
        with document:
            self.erc = ERCOptions
            """ [boolean|dict=false] Use a boolean for simple cases or fine-tune its behavior """

    def apply_filters(self, data):
        # Create a dict to translate sheets paths to file names
        self.solve_sheet_paths()
        filters = self._filters.copy()
        if GS.filters:
            filters += GS.filters
            logger.warning(W_FILXRC+'Using filters from the `filters` preflight, move them to `erc`')
        self.c_err = self.c_warn = self.c_tot = 0
        self.c_err_excl = self.c_warn_excl = self.c_tot_excl = 0
        sheets = data.get('sheets', [])
        for sheet in sheets:
            sheet['file_name'] = self.sheet_paths.get(sheet.get('path', ''), 'unknown')
            violations = sheet.get('violations', [])
            for violation in violations:
                severity = violation.get('severity', 'error')
                type = violation.get('type', '')
                # Collect the text using a layout equivalent to the report
                txt = violation.get('description', '')+'\n'
                for item in violation.get('items', []):
                    txt += self.get_item_txt(item)
                # Check if any filter matches this violation
                excluded = violation.get('excluded')
                for f in filters:
                    if type == f.error and f._regex.search(txt):
                        change_to = f.change_to if hasattr(f, 'change_to') else 'ignore'
                        if change_to == 'ignore':
                            if not excluded:
                                violation['excluded'] = True
                                violation['excluded_by_kibot'] = True
                                excluded = True
                        else:
                            violation['excluded'] = False
                            violation['modified_by_kibot'] = True
                            severity = violation['severity'] = change_to
                            excluded = False
                        break
                if excluded:
                    if severity == 'error':
                        self.c_err_excl += 1
                    else:
                        self.c_warn_excl += 1
                    self.c_tot_excl += 1
                else:
                    if severity == 'error':
                        self.c_err += 1
                    else:
                        self.c_warn += 1
                    self.c_tot += 1

    def create_csv(self, data):
        f = io.StringIO()
        writer = csv.writer(f, delimiter=',', lineterminator="\n", quoting=csv.QUOTE_ALL)
        writer.writerow(['Sheet', 'Severity', 'Excluded', 'Type', 'Description', 'Details'])
        sheets = data.get('sheets', [])
        for sheet in sheets:
            violations = sheet.get('violations', [])
            sheet_fname = sheet.get('file_name', '')
            name = sheet.get('path', '')
            if sheet_fname:
                name += f' ({sheet_fname})'
            for violation in violations:
                severity = violation.get('severity', 'error')
                excluded = violation.get('excluded', False)
                type = violation.get('type', '')
                description = violation.get('description', '')
                details = ''
                for item in violation.get('items', []):
                    details += self.get_item_txt(item, indent=0, sep=';')
                writer.writerow([name, severity, excluded, type, description, details[:-1]])
        return f.getvalue()

    def create_html(self, data):
        # HTML Head
        html = self.create_html_top(data)
        # Generate the content
        empty = True
        violations_html = ''
        for sheet in data.get('sheets', []):
            violations = sheet.get('violations', [])
            if not violations:
                continue
            sheet_fname = sheet.get('file_name', '')
            name = sheet.get('path', '')
            if sheet_fname:
                name += f' ({sheet_fname})'
            violations_html += f'<p class="subtitle">Sheet {name}</p>\n'
            violations_html += self.create_html_violations(violations)
            if any(not item.get('excluded', False) for item in violations):
                empty = False
        if empty:
            html += self.create_html_ok()
        html += violations_html + self.create_html_bottom()
        return html

    def create_txt(self, data):
        dt = data.get('date', '??')
        rpt = f"ERC report ({dt}, Encoding UTF8)\n\n"
        for s in data.get('sheets', []):
            path = s.get('path', '')
            rpt += f"***** Sheet {path}\n"
            for v in s.get('violations', []):
                severity = v.get('severity', 'error')
                type = v.get('type', '')
                description = v.get('description', '')
                rpt += f'[{type}]: {description}\n'
                excluded = ' (excluded)' if v.get('excluded') else ''
                rpt += f'    ; {severity}{excluded}\n'
                for item in v.get('items', []):
                    rpt += self.get_item_txt(item)
                rpt += '\n'
        rpt += f" ** ERC messages: {self.c_tot}  Errors {self.c_err}  Warnings {self.c_warn}\n"
        return rpt

    def report(self, kind, count, data):
        if not count:
            return
        logf = logger.error if kind == 'error' else lambda msg: logger.warning(W_ERC+msg)
        logf(f'{count} ERC {kind}s detected')
        for s in data.get('sheets', []):
            path = s.get('path', '')
            for v in s.get('violations', []):
                if v.get('excluded'):
                    continue
                severity = v.get('severity', 'error')
                if severity != kind:
                    continue
                type = v.get('type', '')
                description = v.get('description', '')
                txt = f'({type}) {description}\n'
                for item in v.get('items', []):
                    txt += self.get_item_txt(item)
                txt += f'    Sheet: {path}'
                logf(txt)

    def solve_sheet_paths(self):
        self.sheet_paths = {}
        if not GS.sch:
            return
        for s in GS.sch.all_sheets:
            path = s.sheet_path_h
            if len(path) > 1:
                path += '/'
            self.sheet_paths[path] = s.fname_rel

    def get_command(self, output):
        # No variants here
        cmd = [GS.kicad_cli, 'sch', 'erc', '-o', output, '--format', 'json', '--severity-all',
               '--units', UNITS_2_KICAD[self._units], GS.sch_file]
        return cmd

    @staticmethod
    def get_conf_examples(name, _):
        return XRC.get_conf_examples(name)
