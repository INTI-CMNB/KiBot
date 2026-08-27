# -*- coding: utf-8 -*-
# Copyright (c) 2020-2026 Salvador E. Tropea
# Copyright (c) 2020-2026 Instituto Nacional de Tecnología Industrial
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)
from .gs import GS
from .out_any_drill import AnyDrill
from .macros import macros, document, output_class  # noqa: F401


class Gerb_DrillOptions(AnyDrill):
    def __init__(self):
        super().__init__()
        self._ext = 'gbr'

    def _configure_writer(self, board):
        if GS.ki10:
            options = ['--format', 'gerber',
                       '--drill-origin', 'plot' if self.use_aux_axis_as_origin else 'absolute',
                       '--gerber-precision', '6']  # Currently is always 4.6
            return options, True
        drill_writer = GS.pn.GERBER_WRITER(board)
        # hard coded in UI?
        drill_writer.SetFormat(5)
        drill_writer.SetOptions(GS.p2v_k7(GS.get_aux_origin() if self.use_aux_axis_as_origin else GS.get_absolute_origin()))
        return drill_writer, False


@output_class
class Gerb_Drill(BaseOutput):  # noqa: F821
    """ Gerber drill format
        This is the information for the drilling machine in gerber format.
        You can create a map file for documentation purposes.
        This output is what you get from the 'File/Fabrication output/Drill Files' menu in pcbnew. """
    def __init__(self):
        super().__init__()
        self._category = 'PCB/fabrication/drill'
        with document:
            self.options = Gerb_DrillOptions
            """ *[dict={}] Options for the `gerb_drill` output """

    @staticmethod
    def get_conf_examples(name, layers):
        gb = {}
        outs = [gb]
        name_u = name.upper()
        gb['name'] = 'basic_'+name
        gb['comment'] = 'Drill files in '+name_u+' format'
        gb['type'] = name
        gb['dir'] = 'Gerbers_and_Drill'
        gb['options'] = {'map': 'gerber'}
        return outs
