# -*- coding: utf-8 -*-
# Copyright (c) 2020-2023 Salvador E. Tropea
# Copyright (c) 2020-2023 Instituto Nacional de Tecnología Industrial
# Copyright (c) 2020 @nerdyscout
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)
"""
Dependencies:
  - from: KiAuto
    role: mandatory
    command: eeschema_do
    version: 2.3.6
    version_k10: 2.3.9
"""
from .gs import GS
from .out_any_sch_print import Any_SCH_PrintOptions
from .misc import SVG_SCH_PRINT, FONT_HELP_TEXT, MULTI_SCH_NAME
from .macros import macros, document, output_class  # noqa: F401
from . import log

logger = log.get_logger()


class SVG_SCH_PrintOptions(Any_SCH_PrintOptions):
    def __init__(self):
        with document:
            self.output = GS.def_global_output
            """ Filename for the output SVG (%i=schematic, %x=svg) """
        super().__init__()
        self._expand_ext = 'svg'
        self._exit_error = SVG_SCH_PRINT


@output_class
class SVG_SCH_Print(BaseOutput):  # noqa: F821
    """ SVG Schematic Print
        Exports the schematic in a vectorized graphics format.
        This is a format to document your schematic.
        This output is what you get from the 'File/Plot' menu in eeschema.
        Supports the image replacement using the prefix indicated by the `sch_image_prefix` global variable. """
    __doc__ += MULTI_SCH_NAME+FONT_HELP_TEXT

    def __init__(self):
        super().__init__()
        with document:
            self.options = SVG_SCH_PrintOptions
            """ *[dict={}] Options for the `svg_sch_print` output """
        self._sch_related = True
        self._category = 'Schematic/docs'

    @staticmethod
    def get_conf_examples(name, layers):
        return BaseOutput.simple_conf_examples(name, 'Schematic in SVG format', 'Schematic')  # noqa: F821
