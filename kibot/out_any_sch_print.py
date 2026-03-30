# -*- coding: utf-8 -*-
# Copyright (c) 2020-2026 Salvador E. Tropea
# Copyright (c) 2020-2026 Instituto Nacional de Tecnología Industrial
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)
import os
from .error import KiPlotConfigurationError
from .gs import GS
from .out_base import VariantOptions
from .misc import EMBED_PREFIX
from .macros import macros, document, output_class  # noqa: F401
from . import log

logger = log.get_logger()


# Validator created using Gemini 3.1 Pro
def parse_and_validate_pages(input_string, valid_pages):
    """
    Parses a comma-separated string of numbers and ranges, validates them against
    a set of valid pages, and returns a sorted, comma-separated string of pages.

    Args:
        input_string (str): The string to parse (e.g., "1, 3, 5-7, 10").
        valid_pages (set[int]): A set of allowed integer page numbers.

    Returns:
        str: A comma-separated string of sorted, expanded, and valid pages.

    Raises:
        ValueError: If the input is malformed, contains non-numbers, inverted ranges,
                    or includes pages not in the `valid_pages` set.
        TypeError: If the inputs are not of the expected types.
    """
    input_string = input_string.strip()
    if not input_string:
        return None

    result_pages = set()
    tokens = input_string.split(',')

    min_page = min(valid_pages) if valid_pages else 1
    max_page = max(valid_pages) if valid_pages else 0

    for token in tokens:
        token = token.strip()

        # Catch empty tokens caused by trailing commas or double commas (e.g., "1,,2" or "1,2,")
        if not token:
            raise ValueError("Invalid format: contains empty elements (check for extra commas).")

        # Handle ranges (e.g., "5-8")
        if '-' in token:
            sub_tokens = token.split('-')

            if len(sub_tokens) != 2:
                raise ValueError(f"Invalid range format: '{token}'. Expected 'start-end'.")

            start_str, end_str = sub_tokens[0].strip(), sub_tokens[1].strip()

            # If a string is provided, ensure it's a digit. (Allows empty strings)
            if (start_str and not start_str.isdigit()) or (end_str and not end_str.isdigit()):
                raise ValueError(f"Invalid range values: '{token}'. Boundaries must be integers.")

            # Default to min_page if missing start, max_page if missing end
            start = min_page if not start_str else int(start_str)
            end = max_page if not end_str else int(end_str)

            if start > end:
                raise ValueError(f"Invalid range: '{token}'. Start value cannot be greater than end value.")

            # Expand the range and validate each page
            for page in range(start, end + 1):
                if page not in valid_pages:
                    raise ValueError(f"Page {page} from range '{token}' is not a valid page.")
                result_pages.add(page)

        # Handle single numbers (e.g., "5")
        else:
            if not token.isdigit():
                raise ValueError(f"Invalid page number: '{token}'. Must be a positive integer.")

            page = int(token)
            if page not in valid_pages:
                raise ValueError(f"Page {page} is not a valid page.")

            result_pages.add(page)

    # Sort the deduplicated pages and format back to a comma-separated string
    sorted_pages = sorted(result_pages)
    return ",".join(str(p) for p in sorted_pages)


class Any_SCH_PrintOptions(VariantOptions):
    def __init__(self):
        with document:
            self.monochrome = False
            """ Generate a monochromatic output """
            self.frame = True
            """ *Include the frame and title block """
            self.all_pages = True
            """ Generate with all hierarchical sheets, unless `pages` is specified """
            self.pages = ''
            """ List of comma separarted pages to print. Ranges are allowed i.e.: `3-5` or `3-` or `-3` """
            self.color_theme = ''
            """ Color theme used, this must exist in the KiCad config (KiCad 6) """
            self.background_color = False
            """ Use the background color from the `color_theme` (KiCad 6) """
            self.title = ''
            """ Text used to replace the sheet title. %VALUE expansions are allowed.
                If it starts with `+` the text is concatenated """
            self.sheet_reference_layout = ''
            """ Worksheet file (.kicad_wks) to use. Leave empty to use the one specified in the project.
                This option works only when you print the toplevel sheet of a project and the project
                file is available """
            self.default_font = 'KiCad Font'
            """ Name for the default font. Only for KiCad 9 and newer """
        super().__init__()
        self.add_to_doc('variant', "Not fitted components are crossed")
        self._expand_id = 'schematic'
        # We need the list from the schematic to control the real components
        self._collapse_components = False

    def get_targets(self, out_dir):
        if self.output:
            return [self._parent.expand_filename(out_dir, self.output)]
        return [self._parent.expand_filename(out_dir, '%f.%x')]

    def desc_box(self, box):
        return f"SCH text box @{box.pos_x},{box.pos_y}"

    def config(self, parent):
        super().config(parent)
        try:
            self._pages = parse_and_validate_pages(self.pages, {int(s.sheet) for s in GS.sch.all_sheets})
        except ValueError as e:
            raise KiPlotConfigurationError('Error parsing list of pages: '+str(e))

    def run(self, name):
        super().run(name)
        command = self.ensure_tool('KiAuto')

        # This code has two purposes:
        # 1. Allow specifying a different worksheet
        # 2. Fix \ in the worksheet
        # For this we temporarily adjust the project
        prj = None
        if GS.pro_file and GS.pro_basename == GS.sch_basename:
            ori_wks = ''
            wks = GS.fix_page_layout(GS.pro_file, dry=True)
            # We have a project and is the project for the schematic
            if self.sheet_reference_layout:
                # The user wants a different worksheet
                new_wks = os.path.join(GS.pro_dir, self.sheet_reference_layout)
                if not os.path.isfile(new_wks):
                    raise KiPlotConfigurationError(f'Missing `{new_wks}` worksheet')
            else:
                ori_wks = new_wks = wks[0]
                if ori_wks and not new_wks.startswith(EMBED_PREFIX) and not os.path.isfile(new_wks):
                    raise KiPlotConfigurationError(f'Missing `{new_wks}` worksheet')
            if ori_wks != new_wks:
                prj = GS.read_pro()
                GS.fix_page_layout(GS.pro_file, dry=False, force_sch=os.path.relpath(new_wks, GS.pro_dir))
        elif self.sheet_reference_layout:
            raise KiPlotConfigurationError('Using `sheet_reference_layout` but no project available')

        replaced_images = self.sch_replace_images(GS.sch)
        try:
            if self.title:
                self.set_title(self.title, sch=True)
            sch_file = self.save_tmp_sch_if_variant(force=self.title or replaced_images)
            fmt = 'hpgl' if self._expand_ext == 'plt' else self._expand_ext
            cmd = [command, 'export', '--file_format', fmt, '-o', name]
            if self.monochrome:
                cmd.append('--monochrome')
            if not self.frame:
                cmd.append('--no_frame')
            if self._pages:
                cmd.append('--pages')
                cmd.append(self._pages)
            elif self.all_pages:
                cmd.append('--all_pages')
            if self.color_theme:
                cmd.extend(['--color_theme', self.color_theme])
            if self.background_color:
                cmd.append('--background_color')
            if hasattr(self, '_origin'):
                cmd.extend(['--hpgl_origin', str(self._origin)])
            if hasattr(self, 'pen_size'):
                cmd.extend(['--hpgl_pen_size', str(self.pen_size)])
            if self.default_font:
                cmd.extend(['--default_font', self.default_font])
            cmd.extend([sch_file, os.path.dirname(name)])
            self.exec_with_retry(self.add_extra_options(cmd), self._exit_error)
            if self.title:
                self.restore_title(sch=True)
            if replaced_images:
                self.sch_restore_images(GS.sch)
        finally:
            if prj:
                GS.write_pro(prj)
