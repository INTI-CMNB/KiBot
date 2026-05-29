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
    version_k10: 2.3.9
"""
import os
from .gs import GS
from .out_any_pcb_print import Any_PCB_PrintOptions
from .kicad.patch_svg import patch_svg_file
from .kicad.pcb import PCB
from .misc import FONT_HELP_TEXT
from .macros import macros, document, output_class  # noqa: F401
from .layer import Layer
from . import log

logger = log.get_logger()


class SVG_PCB_PrintOptions(Any_PCB_PrintOptions):
    def __init__(self):
        with document:
            self.output = GS.def_global_output
            """ *Filename for the output SVG (%i=layers, %x=svg)"""
            self.enable_ki6_page_fix = True
            """ Enable workaround for KiCad 6 bug #11033 """
            self.enable_ki5_page_fix = True
            """ Enable workaround for KiCad 5 bug """
        super().__init__()
        self._expand_ext = 'svg'

    def run(self, output):
        super().run(output, svg=True)
        if (GS.ki6 and self.enable_ki6_page_fix) or (GS.ki5 and self.enable_ki5_page_fix):
            # KiCad 6.0.2 bug: https://gitlab.com/kicad/code/kicad/-/issues/11033
            o = self._parent
            out_files = o.get_targets(o.expand_dirname(os.path.join(GS.out_dir, o.dir)))
            is_portrait = PCB.load(GS.pcb_file).paper_portrait
            for file in out_files:
                patch_svg_file(file, is_portrait=is_portrait)


@output_class
class SVG_PCB_Print(BaseOutput):  # noqa: F821
    """ SVG PCB Print (Scalable Vector Graphics) *Deprecated*
        Exports the PCB to the scalable vector graphics format.
        This output is what you get from the 'File/Print' menu in pcbnew.
        The `pcb_print` is usually a better alternative. """
    __doc__ += FONT_HELP_TEXT

    def __init__(self):
        super().__init__()
        with document:
            self.options = SVG_PCB_PrintOptions
            """ *[dict={}] Options for the `pdf_pcb_print` output """
            self.layers = Layer
            """ *[list(dict)|list(string)|string='all'] [all,selected,copper,technical,user,inners,outers,*] List
                of PCB layers to include in the PDF """
        self._category = 'PCB/docs'

    def config(self, parent):
        super().config(parent)
        self.options.set_layers(self.layers)
