# -*- coding: utf-8 -*-
# Copyright (c) 2022-2025 Salvador E. Tropea
# Copyright (c) 2022-2025 Instituto Nacional de Tecnología Industrial
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)
"""
Dependencies:
  - from: KiAuto
    role: mandatory
    version: 2.1.0
"""
import os
import re
from shutil import copy2
from .gs import GS
from .out_base_3d import Base3DOptionsWithHL, Base3D
from .misc import FAILED_EXECUTE, W_MISSWRL
from .macros import macros, document, output_class  # noqa: F401
from . import log

logger = log.get_logger()


def replace_ext(file, ext):
    file, ext = os.path.splitext(file)
    return file+'.wrl'


# VRML Inline URL parser, adapted from "Gemini 2.5 Pro Preview O5-O6" example
def find_vrml_inline_urls(vrml_content):
    """
    Finds all URLs specified in Inline nodes within VRML content.

    Args:
        vrml_content (str): The string content of the VRML file.

    Returns:
        set: A set of unique URLs found in Inline nodes.
             Returns an empty set if no Inline URLs are found or if there's an issue.
    """
    included_files = set()

    # Regex to find Inline nodes and capture their 'url' field content.
    # This regex tries to be robust for:
    # - Optional DEF names: DEF MyInline Inline { ... }
    # - Whitespace variations
    # - Single URL string: url "filename.wrl"
    # - Multiple URLs in an array: url [ "file1.wrl", "file2.wrl" ]
    # - Other fields within the Inline node
    # - Comments (#) are generally ignored by being outside the core pattern parts or
    #   being consumed by '.*?' if they are inside the Inline block but not part of 'url'.
    #
    # Breakdown of the main regex part for 'url':
    #   url\s+                        # Matches "url" followed by one or more spaces
    #   (?P<url_value>               # Start of a named capture group "url_value"
    #       "[^"]*"                  # Matches a single quoted string (e.g., "file.wrl")
    #       |                        # OR
    #       \[                       # Matches an opening square bracket for an array
    #           (?:                  # Start of a non-capturing group for array elements
    #               \s*              # Optional whitespace
    #               "[^"]*"          # A quoted string (filename)
    #               \s*              # Optional whitespace
    #               ,?               # Optional comma
    #           )*                   # Zero or more such elements
    #       \]                       # Matches a closing square bracket
    #   )                            # End of named capture group "url_value"
    #
    # We use re.DOTALL so that '.' matches newlines, as Inline blocks can span multiple lines.
    # The '.*?' parts are non-greedy to match as little as possible.

    # Regex to find an Inline block and its url field
    # It captures the entire value of the url field (either a single string or an array string)
    # More precise regex for VRML keywords (case-sensitive)
    inline_pattern_strict = re.compile(
        r"Inline\s*\{"          # "Inline" followed by optional space and {
        r".*?"
        r"url\s+"
        r"(?P<url_value>"
        r'"[^"]*"'              # e.g., "model.wrl"
        r"|"
        r"\[[\s\S]*?\]"         # e.g., [ "model1.wrl", "model2.wrl" ], [\s\S] to match any char including newline
        r")"
        r".*?"
        r"\}",
        re.DOTALL  # Use DOTALL for '.*?' to match across newlines
    )

    for match in inline_pattern_strict.finditer(vrml_content):
        url_field_content = match.group("url_value").strip()

        if url_field_content.startswith("["):
            # It's an array, e.g., [ "file1.wrl", "file2.wrl", "path/to/file3.wrl" ]
            # Remove brackets and then find all quoted strings inside
            array_content = url_field_content[1:-1]  # Remove surrounding []
            # Regex to find all quoted strings within the array content
            filenames_in_array = re.findall(r'"([^"]*)"', array_content)
            for fname in filenames_in_array:
                if fname.strip():  # Ensure it's not an empty string if " " was found
                    included_files.add(fname.strip())
        elif url_field_content.startswith('"'):
            # It's a single string, e.g., "file.wrl"
            # Remove surrounding quotes
            filename = url_field_content[1:-1]
            if filename.strip():
                included_files.add(filename.strip())
        # else: Malformed url field, ignore for now

    return included_files


class VRMLOptions(Base3DOptionsWithHL):
    def __init__(self):
        with document:
            self.output = GS.def_global_output
            """ *Filename for the output (%i=vrml, %x=wrl) """
            self.dir_models = 'shapes3D'
            """ Subdirectory used to store the 3D models for the components.
                If you want to create a monolithic file just use '' here.
                Note that the WRL file will contain relative paths to the models """
            self.use_pcb_center_as_ref = True
            """ The center of the PCB will be used as reference point.
                When disabled the `ref_x`, `ref_y` and `ref_units` will be used """
            self.use_aux_axis_as_origin = False
            """ Use the auxiliary axis as origin for coordinates.
                Has more precedence than `use_pcb_center_as_ref` """
            self.ref_x = 0
            """ X coordinate to use as reference when `use_pcb_center_as_ref` and `use_pcb_center_as_ref` are disabled """
            self.ref_y = 0
            """ Y coordinate to use as reference when `use_pcb_center_as_ref` and `use_pcb_center_as_ref` are disabled """
            self.ref_units = 'millimeters'
            """ [millimeters,inches'] Units for `ref_x` and `ref_y` """
            self.model_units = 'millimeters'
            """ [millimeters,meters,deciinches,inches] Units used for the VRML (1 deciinch = 0.1 inches) """
        super().__init__()
        self._expand_id = 'vrml'
        self._expand_ext = 'wrl'

    def get_targets(self, out_dir):
        targets = [self._parent.expand_filename(out_dir, self.output)]
        if self.dir_models:
            # Missing models can be downloaded during the 3D variant filtering
            # Also renamed or disabled.
            # # We will also generate the models
            # dir = os.path.join(out_dir, self.dir_models)
            # filtered = {os.path.join(dir, os.path.basename(replace_ext(m, 'wrl')))
            #    for m in self.list_models(even_missing=True)}
            # targets.extend(list(filtered))
            # So we just add the dir
            targets.append(os.path.join(out_dir, self.dir_models))
        return targets

    def get_pcb_center(self):
        center = GS.board.ComputeBoundingBox(True).Centre()
        return self.to_mm(center.x), self.to_mm(center.y)

    def run(self, name):
        command = self.ensure_tool('KiAuto')
        super().run(name)
        self.apply_show_components()
        board_name = self.filter_components(highlight=set(self.expand_kf_components(self._highlight)), force_wrl=True)
        self.undo_show_components()
        cmd = [command, 'export_vrml', '--output_name', os.path.basename(name), '-U', self.model_units]
        if self.dir_models:
            cmd.extend(['--dir_models', self.dir_models])
        if not self.use_pcb_center_as_ref or GS.ki5 or self.use_aux_axis_as_origin:
            if self.use_aux_axis_as_origin:
                offset = GS.get_aux_origin()
                x = GS.to_mm(offset.x)
                y = GS.to_mm(offset.y)
                units = 'millimeters'
            # KiCad 5 doesn't support using the center, we emulate it
            elif self.use_pcb_center_as_ref and GS.ki5:
                x, y = self.get_pcb_center()
                units = 'millimeters'
            else:
                x = self.ref_x
                y = self.ref_y
                units = self.ref_units
            cmd.extend(['-x', str(x), '-y', str(y), '-u', units])
        dname = os.path.dirname(name)
        cmd.extend([board_name, dname])
        # Execute it
        self.exec_with_retry(self.add_extra_options(cmd), FAILED_EXECUTE)
        # Warn about missing models
        if GS.global_vrml_3d_model_workaround and self.dir_models:
            assert os.path.isfile(name)
            with open(name) as f:
                urls = find_vrml_inline_urls(f.read())
            for f in urls:
                basename = os.path.basename(f)
                fullname = os.path.join(dname, f)
                if not os.path.isfile(fullname):
                    logger.warning(W_MISSWRL+f'Missing component in generated VRML: `{f}`')
                    model = self.used_3d_models.get(basename)
                    if model is None and basename.startswith('kicad_embedded_'):
                        embed_model = GS.get_embed_dir(basename)
                        if os.path.isfile(embed_model):
                            model = embed_model
                    if model is None:
                        logger.warning(W_MISSWRL+f'Nothing known for: `{f}`')
                    else:
                        copy2(model, fullname)
                        logger.warning(W_MISSWRL+f'Replaced using: `{model}`')


@output_class
class VRML(BaseOutput):  # noqa: F821
    """ VRML (Virtual Reality Modeling Language)
        Exports the PCB as a 3D model (WRL file).
        This is intended for rendering, unlike STEP which is intended to be
        an exact mechanic model """
    def __init__(self):
        super().__init__()
        self._category = 'PCB/3D'
        with document:
            self.options = VRMLOptions
            """ *[dict={}] Options for the `vrml` output """

    @staticmethod
    def get_conf_examples(name, layers):
        return Base3D.simple_conf_examples(name, 'PCB in VRML format', '3D')
