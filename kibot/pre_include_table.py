# -*- coding: utf-8 -*-
# Copyright (c) 2024 Nguyen Vincent
# Copyright (c) 2024 Salvador E. Tropea
# Copyright (c) 2024 Instituto Nacional de Tecnología Industrial
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)
# Contributed by Nguyen Vincent (@nguyen-v)
import os
import csv
import re
import pcbnew
from .error import KiPlotConfigurationError
from .gs import GS
from .kicad.pcb_draw_helpers import (draw_rect, draw_line, draw_text, get_text_width,
                                     draw_marker, get_marker_best_pen_size,
                                     GR_TEXT_HJUSTIFY_LEFT, GR_TEXT_HJUSTIFY_RIGHT,
                                     GR_TEXT_HJUSTIFY_CENTER)
from .kiplot import load_board, get_output_targets, look_for_output
from .misc import W_NOMATCHGRP
from .optionable import Optionable
from .registrable import RegOutput
from .macros import macros, document, pre_class  # noqa: F401
from . import log
logger = log.get_logger()
ALIGNMENT = {'left': GR_TEXT_HJUSTIFY_LEFT,
             'center': GR_TEXT_HJUSTIFY_CENTER,
             'right': GR_TEXT_HJUSTIFY_RIGHT}
VALID_OUTPUT_TYPES = {'bom', 'kibom', 'position', 'report', 'excellon'}


class IncTableOutputOptions(Optionable):
    """ Data for a layer """
    def __init__(self, name=None, parent=None):
        super().__init__()
        self._unknown_is_error = True
        with document:
            self.name = ''
            """ *Name of output """
            self.has_header = True
            """ Plot header on the table """
            self.bold_headers = True
            """ Whether or not the headers should be in bold """
            self.vertical_rule_width = 0.1
            """ Width of vertical rules between columns. Use 0 to eliminate it """
            self.horizontal_rule_width = 0.1
            """ Width of vertical rules between rows (doesn't include header)
                Use 0 to eliminate it """
            self.top_rule_width = 0.4
            """ Width of top rule (above header). Use 0 to eliminate it """
            self.bottom_rule_width = 0.4
            """ Width of bottom rule (bottom of table). Use 0 to eliminate it """
            self.header_rule_width = 0.3
            """ Width of rule below header. Use 0 to eliminate it """
            self.border_width = 0.4
            """ Width of border around the table. Use 0 to eliminate it """
            self.column_spacing = 3
            """ Blank space (in number of characters) between columns """
            self.row_spacing = 2
            """ Space (in number of characters) between rows """
            self.text_alignment = 'left'
            """ [left,center,right] Text alignment in the table """
            self.invert_columns_order = False
            """ Invert column order. Useful when inverting PCB texts in PCB Print """
            self.force_font_width = 0
            """ Force the font width (in mm) in the table. Leave empty to compute the
                width automatically from the group width """
            self.is_drill = False
            """ Set to True if the table is a drill table. This will add drill marks
                on the left side of the table """
        if name is not None:
            self.name = name
            self.config(parent)

    def __str__(self):
        v = f'{self.name} ({self.text_alignment}'
        if self.invert_columns_order:
            v += ' inverted'
        if self.has_header:
            v += ' header'
        return v+')'

    def config(self, parent):
        super().config(parent)
        self._text_alignment = ALIGNMENT[self.text_alignment]


class IncludeTableOptions(Optionable):
    """ Include table options """
    def __init__(self):
        with document:
            self.outputs = IncTableOutputOptions
            """ *[list(dict)|list(string)|string=?] List of CSV-generating outputs.
                When empty we include all possible outputs """
            self.enabled = True
            """ Enable the check. This is the replacement for the boolean value """
            self.group_name = 'kibot_table'
            """ Name for the group containing the table. The name of the group
                should be <group_name>_X where X is the output name.
                When the output generates more than one CSV use *kibot_table_out[2]*
                to select the second CSV. Python expressions for slicing are supported,
                for example *kibot_table_out[:10]* would include all elements until the 10th
                element (10th excluded), and *kibot_table_out[2][5:8]* would include the second
                output's elements number 6 to 8 (python indexes start at 0). """
        super().__init__()
        self._unknown_is_error = True

    def config(self, parent):
        super().config(parent)
        if isinstance(self.outputs, type):
            # Nothing specified, look for candidates
            self.outputs = [o.name for o in filter(lambda x: x.type in VALID_OUTPUT_TYPES, RegOutput.get_outputs())]
            logger.debug('- Collected outputs: '+str(self.outputs))
        self._outputs = [IncTableOutputOptions(o, self) if isinstance(o, str) else o for o in self.outputs]


class ITColumns:
    def __init__(self, header='', width=10):
        self.header = header  # Column header name
        self.width = width  # Relative width (default to 10)
        self.data = []  # List to hold data for the column


def update_table_group(g, pos_x, pos_y, width, tlayer, ops, out, csv_file, slice_str=None):
    """Extend the function to handle slicing of rows based on the slice_str."""
    if not os.path.isfile(csv_file):
        raise KiPlotConfigurationError(f'Missing `{csv_file}`, create it first using the `{out.name}` output')

    font = None

    for item in g.GetItems():
        if not isinstance(item, pcbnew.PCB_TEXTBOX):
            GS.board.Delete(item)
        else:
            font = item.GetFont()

    cols = []

    with open(csv_file) as csvfile:
        reader = csv.reader(csvfile, delimiter=out._obj.get_csv_separator())

        # Parse the header if present
        if out.has_header:
            headers = next(reader)
            if out.is_drill:
                cols.append(ITColumns(header='Symbol'))
            for header in headers:
                cols.append(ITColumns(header=header))
        else:
            first_row = next(reader)
            if out.is_drill:
                cols.append(ITColumns())
            for _ in range(len(first_row)):
                cols.append(ITColumns())
            for i, value in enumerate(first_row):
                cols[i].data.append(value)

        # Add the rest of the CSV rows to the column data
        for row in reader:
            if out.is_drill:
                row.insert(0, '   ')  # for the drill symbol we reserve 3 em spaces
            for i, value in enumerate(row):
                if i < len(cols):
                    cols[i].data.append(value)

    # Apply slicing if provided
    if slice_str:
        for col in cols:
            col.data = eval(f"col.data{slice_str}")  # Apply the slicing directly

    if out.invert_columns_order:
        cols.reverse()

    measure_table(cols, out, out.bold_headers, font)

    total_char_w = sum(c.width_char for c in cols)
    total_rel_w = sum((c.width for c in cols))

    font_w = int(10000*width*cols[0].width/total_rel_w/cols[0].max_len) if total_char_w else 0

    if out.force_font_width != 0:
        width = int(width*GS.from_mm(out.force_font_width)/font_w)
        font_w = GS.from_mm(out.force_font_width) if total_char_w else 0

    col_spacing_width = get_text_width(' ', w=font_w, font=font)*out.column_spacing

    xpos_x = int(pos_x + col_spacing_width / 2)
    max_row_data = 0

    # KiCad adds some padding around the texts, we add some padding to align
    # markers with the texts
    marker_padding = font_w/4

    for c in cols:
        c.w = int(c.width / total_rel_w * width)
        c.x = xpos_x
        if out._text_alignment == GR_TEXT_HJUSTIFY_LEFT:
            c.xoffset = 0
            c.xoffset_marker = int(font_w/2 + marker_padding)
        elif out._text_alignment == GR_TEXT_HJUSTIFY_RIGHT:
            c.xoffset = int(c.w - col_spacing_width)
            c.xoffset_marker = int(-font_w/2 - marker_padding)
        elif out._text_alignment == GR_TEXT_HJUSTIFY_CENTER:
            c.xoffset = int(c.w / 2 - col_spacing_width / 2)
            c.xoffset_marker = 0
        xpos_x += c.w
        max_row_data = max(max_row_data, len(c.data))

    y = pos_y
    row_h = out.row_spacing * font_w

    if out.has_header:
        y += int(row_h)
        draw_line(g, pos_x, y, pos_x + width, y, tlayer, line_w=GS.from_mm(out.header_rule_width))
        for c in cols:
            txt, _ = draw_text(g, c.x + c.xoffset, int(pos_y + 0.5 * row_h - font_w), c.header, font_w, font_w,
                               tlayer, bold=out.bold_headers, alignment=out._text_alignment, font=font)

    for i in range(max_row_data - 1):
        rule_y = int(y + (i + 1) * row_h)
        draw_line(g, pos_x, rule_y, pos_x + width, rule_y, tlayer, line_w=GS.from_mm(out.horizontal_rule_width))

    if out.is_drill:
        rule_y = int(y + (max_row_data - 1) * row_h)
        draw_line(g, pos_x, rule_y, pos_x + width, rule_y, tlayer, line_w=GS.from_mm(out.bottom_rule_width))

    table_h = 0
    for i, c in enumerate(cols):
        row_y = int(y + row_h / 2)
        for j, d in enumerate(c.data):
            txt, _ = draw_text(g, c.x + c.xoffset, int(row_y - font_w), d, font_w, font_w,
                               tlayer, alignment=out._text_alignment, font=font)
            if out.is_drill and i == 0 and j != len(c.data)-1:
                marker_w = get_marker_best_pen_size(font_w)
                draw_marker(g, int(c.x + c.xoffset + c.xoffset_marker), int(row_y), font_w, tlayer, j, marker_w)
            row_y += row_h
        table_h = int(max(table_h, row_y - pos_y) - row_h / 2)

    draw_line(g, pos_x, pos_y, pos_x + width, pos_y, tlayer, line_w=GS.from_mm(out.top_rule_width))
    draw_line(g, pos_x, pos_y + table_h, pos_x + width, pos_y + table_h, tlayer, line_w=GS.from_mm(out.bottom_rule_width))

    for n, c in enumerate(cols):
        if n > 0:
            vrule_x = int(c.x - col_spacing_width / 2)
            draw_line(g, vrule_x, pos_y, vrule_x, pos_y + table_h, tlayer, line_w=GS.from_mm(out.vertical_rule_width))

    draw_rect(g, pos_x, pos_y, width, table_h, tlayer, line_w=GS.from_mm(out.border_width))


def measure_table(cols, out, bold_headers, font=None):
    col_spacing_width = get_text_width(' ', font=font)*out.column_spacing

    for c in cols:
        max_data_len = max(get_text_width(d, font=font) for d in c.data) if c.data else 0
        max_data_width_char = max(len(d) for d in c.data) if c.data else 0
        c.max_len = max(get_text_width(c.header, bold=bold_headers, font=font), max_data_len) + col_spacing_width
        c.width_char = max(len(c.header), max_data_width_char) + out.column_spacing

    tot_len = sum(c.max_len for c in cols)

    # Compute relative widths
    for c in cols:
        c.width = c.max_len/tot_len


def update_table(ops, parent, select_output='all', force_index=-1):
    logger.debug('Starting include table preflight')
    load_board()
    csv_files = []
    csv_name = []
    out_to_csv_mapping = {}

    logger.debug('- Analyzing requested outputs')
    for out in ops._outputs:
        if not out.name:
            raise KiPlotConfigurationError('output entry without a name')
        csv = look_for_output(out.name, '`include table`', parent, VALID_OUTPUT_TYPES) if out.name else None
        if not csv:
            logger.debug(f'  - {out.name} no CSV')
            continue
        out._obj = csv
        targets, _, _ = get_output_targets(out.name, parent)

        csv_targets = [file for file in targets if file.endswith('.csv')]
        for file in csv_targets:
            csv_files.append(file)
        for file in csv_targets:
            file_name = os.path.basename(file)
            name_without_ext = os.path.splitext(file_name)[0]
            csv_name.append(name_without_ext)
        out_to_csv_mapping[out.name] = (out, csv_targets)
        logger.debug(f'  - {out.name} -> {csv_targets}')

    group_found = False
    updated = False
    group_prefix = ops.group_name + "_"
    group_prefix_l = len(group_prefix)
    logger.debug('- Scanning board groups')

    for g in GS.board.Groups():
        group_name = g.GetName()
        if not group_name.startswith(group_prefix):
            continue
        group_found = True
        logger.debug('  - ' + group_name)

        # Extract the group suffix and parse optional brackets
        group_suffix = group_name[group_prefix_l:]
        slice_str = None
        index = None

        # Check for number of brackets in the group name
        bracket_matches = re.findall(r'\[.*?\]', group_suffix)

        out, csv = out_to_csv_mapping.get(group_suffix.split('[')[0], (None, None))

        if not csv:
            logger.warning(W_NOMATCHGRP + f'No output to handle `{group_name}` found')
            continue

        # Determine whether or not to skip outputs based on whether they are
        # drill outputs or normal outputs
        if select_output == 'no_drill' and out.is_drill:
            logger.debug(f'  - Skipping drill output: {out.name}')
            continue
        elif select_output == 'drill_only' and not out.is_drill:
            logger.debug(f'  - Skipping non-drill output: {out.name}')
            continue

        if len(bracket_matches) == 2:
            # Two brackets: second is slicing expression
            slice_str = bracket_matches[1]
            index = int(bracket_matches[0][1:-1]) - 1  # First bracket is the index
            group_suffix = re.sub(r'\[.*?\]', '', group_suffix, count=2)  # Remove both brackets
        elif len(bracket_matches) == 1:
            # One bracket: determine if it's an index or a slice
            if len(csv) == 1:
                slice_str = bracket_matches[0]  # Single CSV means it must be a slice
            else:
                index = int(bracket_matches[0][1:-1]) - 1  # Multiple CSVs mean it's an index
            group_suffix = re.sub(r'\[.*?\]', '', group_suffix, count=1)  # Remove the bracket

        logger.debug(f'    - Parsed group_suffix: {group_suffix}, index: {index}, slice_str: {slice_str}')

        # Default index to 0 if csv has only one element
        if index is None:
            index = 0

        if force_index != -1:
            index = force_index

        if index < 0 or index >= len(csv):
            msg = f'Index {index + 1} is out of range for output {out.name}, '
            raise KiPlotConfigurationError(msg)

        x1, y1, x2, y2 = GS.compute_group_boundary(g)
        item = g.GetItems()[0]
        layer = item.GetLayer()
        logger.debug(f'    - Found group @{GS.to_mm(x1)},{GS.to_mm(y1)} mm'
                     f' ({GS.to_mm(x2 - x1)}x{GS.to_mm(y2 - y1)} mm) layer {layer}'
                     f' with name {g.GetName()}')

        update_table_group(g, x1, y1, x2 - x1, layer, ops, out, csv[index], slice_str)

        updated = True

    if not group_found:
        logger.warning(W_NOMATCHGRP + f'No `{ops.group_name}*` groups found, skipping `include_table` preflight')

    return updated


@pre_class
class Include_Table(BasePreFlight):  # noqa: F821
    """ Include Table
        Draws a table in the PCB from data in a CSV generated by an output. Needs KiCad 7 or newer.
        To specify the position and size of the drawing create a group called *kibot_table_X* where
        X should match the name of the output. If you don't know how to create a group consult
        :ref:`create_group`. Consult the `group_name` option for details.
        After running this preflight the rectangle will contain the table with the same name.
        Only the width of the table is important, the height will be adjusted.
        Important: This preflight assumes that a separated KiBot run generated the outputs
        needed for the tables """

    def __init__(self):
        super().__init__()
        self._pcb_related = True
        with document:
            self.include_table = IncludeTableOptions
            """ [boolean|dict=false] Use a boolean for simple cases or fine-tune its behavior """

    def __str__(self):
        v = self.include_table
        if isinstance(v, bool):
            return super().__str__()
        return f'{self.type}: {v.enabled} ({[out.name for out in v._outputs]})'

    def config(self, parent):
        super().config(parent)
        if isinstance(self.include_table, bool):
            self._value = IncludeTableOptions()
            self._value.config(self)
        else:
            self._value = self.include_table

    def apply(self):
        if not GS.ki7:
            raise KiPlotConfigurationError('The `include_table` preflight needs KiCad 7 or newer')
        if update_table(self._value, self):
            GS.save_pcb()
