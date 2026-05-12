# -*- coding: utf-8 -*-
# Copyright (c) 2025 Salvador E. Tropea
# Copyright (c) 2025 Instituto Nacional de Tecnología Industrial
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)
# Original code by Stefan Schüller
# https://sschueller.github.io/posts/ci-cd-with-kicad-2025/
"""
Dependencies:
  - name: ReportLab
    role: Create a PDF with BoM labels
    python_module: true
    debian: python3-reportlab
    arch: python-reportlab
    downloader: python
"""
import csv
from .error import KiPlotConfigurationError
from .gs import GS
from .kiplot import config_output, run_output, look_for_output, get_output_targets, get_columns
from .optionable import Optionable
from .out_base import VariantOptions
from .macros import macros, document, output_class  # noqa: F401
from . import log

logger = log.get_logger()


class BoMLabelsOptions(VariantOptions):
    def __init__(self):
        super().__init__()
        with document:
            self.output = GS.def_global_output
            """ *Name for the generated PDF (%i=bom_labels %x=pdf) """
            self.bom = ''
            """ *BoM output used for the labels  """
            self.width = 20
            """ Label width in mm """
            self.height = 10
            """ Label height in mm """
            self.margin_x = 2
            """ X margin in mm """
            self.margin_top = 3
            """ Top margin in mm """
            self.header_sep = 3
            """ Distance from header to first line in mm """
            self.line_height = 1.5
            """ Regular line height in mm """
            self.font = "Helvetica-Bold"
            """ Font used for the labels """
            self.font_size_header = 6
            """ Default size of the header font, will be reduced to fit the text """
            self.font_size_rest = 4
            """ Default size of the normal font, will be reduced to fit the text """
            self.rows = 3
            """ How many rows we print, including the header """
        super().__init__()
        self._expand_ext = 'pdf'
        self._expand_id = 'bom_labels'
        self._bom_example = 'bom_labels'

    def run(self, dir_name):
        if not self.bom:
            raise KiPlotConfigurationError('You must specify the name of the output that'
                                           ' generates the BoM for the labels')
        out = look_for_output(self.bom, 'bom', self._parent, {'bom'})
        targets, _, _ = get_output_targets(self.bom, self._parent)
        config_output(out)
        run_output(out)
        self.gen_labels(targets[0], dir_name)

    def gen_labels(self, ori, dest):
        from reportlab.lib.pagesizes import mm
        from reportlab.pdfgen import canvas

        self.ensure_tool('ReportLab')
        page_w = self.width * mm
        page_h = self.height * mm
        margin_x = self.margin_x * mm
        margin_top = self.margin_top * mm
        first_line = (self.margin_top + self.header_sep) * mm
        # Available width for text
        max_text_width = page_w - (2 * margin_x)

        c = canvas.Canvas(dest, pagesize=(page_w, page_h))

        # Read CSV data
        with open(ori, 'r') as f:
            reader = csv.reader(f)
            rows = list(reader)

        if len(rows) < 3:
            raise KiPlotConfigurationError(f'CSV file has only {len(rows)} rows, but we need at least 3 to skip first 2')

        # Skip first 1 row: row 0 (empty) and row 1 (header line)
        data_rows = rows[1:]

        logger.debug(f"Processing {len(data_rows)} data rows (skipped first 2 rows)")

        # Create one page per row
        for row_index, row in enumerate(data_rows):
            # Start new page (don't need c.showPage() for first page, but will add for consistency)
            if row_index > 0:
                c.showPage()

            # Draw first column as header at top in larger font
            if row:  # Check if row has at least one column
                text = str(row[0])
                # Larger font for first column as header
                f_size = self.font_size_header

                # Dynamic Font Scaling for Header
                try:
                    text_w = c.stringWidth(text, self.font, f_size)
                except KeyError:
                    raise KiPlotConfigurationError(f'Unknown font `{self.font}`')
                if text_w > max_text_width:
                    f_size = f_size * (max_text_width / text_w)

                c.setFont(self.font, f_size)
                c.drawString(margin_x, page_h - margin_top, text)

            # Draw separator line
            c.line(margin_x, page_h - margin_top - mm, page_w - margin_x, page_h - margin_top - mm)

            # Draw remaining columns below in smaller font
            c.setFont(self.font, self.font_size_rest)  # Smaller font for other columns
            y_position = page_h - first_line  # Start below separator

            # Start from column 1 (second column)
            for col_index in range(1, min(self.rows, len(row))):  # Limit to self.rows-1 more columns
                text = str(row[col_index])
                f_size = self.font_size_rest

                # Dynamic Font Scaling for Body
                text_w = c.stringWidth(text, self.font, f_size)
                if text_w > max_text_width:
                    f_size = f_size * (max_text_width / text_w)

                c.setFont(self.font, f_size)
                c.drawString(margin_x, y_position, text)
                y_position -= self.line_height * mm

                if y_position < mm:
                    break

        c.save()

    def get_targets(self, out_dir):
        return [self._parent.expand_filename(out_dir, self.output)]

    def __str__(self):
        txt = f'{self.width}x{self.height} mm, {self.rows} rows, {self.bom}'
        return txt


@output_class
class BoM_Labels(BaseOutput):  # noqa: F821
    """ BoM Labels Printer
        Generates a PDF to print labels for the BoM items.
        You can find an explanation [here](https://sschueller.github.io/posts/ci-cd-with-kicad-2025/)
        You need to create a BoM in CSV format containing the fields to be used.
        The first field will be the header, the rest are extra data. """
    def __init__(self):
        super().__init__()
        with document:
            self.options = BoMLabelsOptions
            """ *[dict={}] Options for the `bom_labels` output """
        self._category = ['PCB/docs', 'Schematic/docs']
        self._any_related = True

    def get_dependencies(self):
        files = BaseOutput.get_dependencies(self)  # noqa: F821
        files.append(self.options.bom)
        return files

    @staticmethod
    def get_conf_examples(name, layers):
        if not GS.sch:
            return []
        field = Optionable.solve_field_name('_field_lcsc_part', empty_when_none=True)
        if not field:
            (valid_columns, extra_columns) = get_columns()
            field = 'digikey#'
            if field not in valid_columns:
                return []
        res = BaseOutput.simple_conf_examples(name, 'BoM labels', 'BoM')  # noqa: F821
        res[0]['options'] = {'bom': 'bom_labels'}

        gb = {}
        gb['name'] = 'bom_labels'
        gb['comment'] = 'BoM to Print Labels'
        gb['type'] = 'bom'
        gb['run_by_default'] = False
        gb['dir'] = 'BoM'
        gb['options'] = {'format': 'CSV', 'output': 'bom_labels.%x', 'group_fields': [field], 'sort_style': 'ref',
                         'columns': [field, 'Value', 'Footprint'], 'csv': {'hide_pcb_info': True, 'hide_stats_info': True}}
        res.append(gb)

        return res
