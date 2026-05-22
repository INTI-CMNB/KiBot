# -*- coding: utf-8 -*-
# Copyright (c) 2020-2023 Salvador E. Tropea
# Copyright (c) 2020-2023 Instituto Nacional de Tecnología Industrial
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)
"""
Dependencies:
  - from: KiAuto
    role: mandatory
    command: eeschema_do
    version: 2.3.6
"""
from .gs import GS
from .out_any_sch_print import Any_SCH_PrintOptions
from .misc import PDF_SCH_PRINT, FONT_HELP_TEXT
from .macros import macros, document, output_class  # noqa: F401
from . import log

logger = log.get_logger()


class PDF_SCH_PrintOptions(Any_SCH_PrintOptions):
    def __init__(self):
        with document:
            self.output = GS.def_global_output
            """ Filename for the output PDF (%i=schematic, %x=pdf)"""
        super().__init__()
        self._expand_ext = 'pdf'
        self._exit_error = PDF_SCH_PRINT
        self._unified_pages = True


@output_class
class PDF_SCH_Print(BaseOutput):  # noqa: F821
    """ PDF Schematic Print (Portable Document Format)
        Exports the schematic to the most common exchange format. Suitable for printing.
        This is the main format to document your schematic.
        This output is what you get from the 'File/Plot' menu in eeschema.
        Supports the image replacement using the prefix indicated by the `sch_image_prefix` global variable """
    __doc__ += FONT_HELP_TEXT

    def __init__(self):
        super().__init__()
        with document:
            self.options = PDF_SCH_PrintOptions
            """ *[dict={}] Options for the `pdf_sch_print` output """
        self._sch_related = True
        self._category = 'Schematic/docs'

    @staticmethod
    def get_conf_examples(name, layers):
        return BaseOutput.simple_conf_examples(name, 'Schematic in PDF format', 'Schematic')  # noqa: F821
