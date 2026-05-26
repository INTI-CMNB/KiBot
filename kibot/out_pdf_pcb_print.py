# -*- coding: utf-8 -*-
# Copyright (c) 2020-2023 Salvador E. Tropea
# Copyright (c) 2020-2023 Instituto Nacional de Tecnología Industrial
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)
"""
Dependencies:
  - from: KiAuto
    role: mandatory
    version: 1.6.7
    version_k7: 2.2.8
    version_k8: 2.3.2
    version_k9: 2.3.5
    version_k10: 2.3.7
"""
from .gs import GS
from .out_any_pcb_print import Any_PCB_PrintOptions
from .misc import FONT_HELP_TEXT
from .macros import macros, document, output_class  # noqa: F401
from .layer import Layer
from . import log

logger = log.get_logger()


class PDF_PCB_PrintOptions(Any_PCB_PrintOptions):
    def __init__(self):
        with document:
            self.output = GS.def_global_output
            """ Filename for the output PDF (%i=layers, %x=pdf)"""
        super().__init__()
        self._expand_ext = 'pdf'


@output_class
class PDF_PCB_Print(BaseOutput):  # noqa: F821
    """ PDF PCB Print (Portable Document Format) *Deprecated*
        Exports the PCB to the most common exchange format. Suitable for printing.
        This is the main format to document your PCB.
        This output is what you get from the 'File/Print' menu in pcbnew.
        The `pcb_print` is usually a better alternative. """
    __doc__ += FONT_HELP_TEXT

    def __init__(self):
        super().__init__()
        with document:
            self.options = PDF_PCB_PrintOptions
            """ *[dict={}] Options for the `pdf_pcb_print` output """
            self.layers = Layer
            """ *[list(dict)|list(string)|string='all'] [all,selected,copper,technical,user,inners,outers,*] List
                of PCB layers to include in the PDF """
        self._category = 'PCB/docs'

    def config(self, parent):
        super().config(parent)
        self.options.set_layers(self.layers)
