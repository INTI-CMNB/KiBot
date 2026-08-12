# -*- coding: utf-8 -*-
# Copyright (c) 2020-2023 Salvador E. Tropea
# Copyright (c) 2020-2023 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
from .gs import GS
from .out_any_layer import AnyLayerOptions
from . import log

logger = log.get_logger()

# Mappings to KiCad values
DRILL_MARKS_MAP = {
                   'none': GS.NO_DRILL_SHAPE,
                   'small': GS.SMALL_DRILL_SHAPE,
                   'full': GS.FULL_DRILL_SHAPE,
                  }
# Mappings from KiCad values
DRILL_MARKS_REV_MAP = {
                       GS.NO_DRILL_SHAPE: 'none',
                       GS.SMALL_DRILL_SHAPE: 'small',
                       GS.FULL_DRILL_SHAPE: 'full',
                      }


def add_drill_marks(self):
    self.drill_marks = 'full'
    self.set_doc('drill_marks', " [string='full'] [none,small,full] What to use to indicate the drill places, can be "
                 "none, small or full (for real scale)")


class DrillMarks(AnyLayerOptions):
    """ This class provides the drill_marks attribute.
        Used by DXF, HPGL, PDF, PS and SVG formats. """
    def __init__(self):
        super().__init__()
        add_drill_marks(self)

    def config(self, parent):
        super().config(parent)
        self.drill_marks = DRILL_MARKS_MAP[self.drill_marks]

    def _configure_plot_ctrl(self, po, output_dir):
        super()._configure_plot_ctrl(po, output_dir)
        # How we draw drill marks
        po.SetDrillMarksType(self.drill_marks)

    def read_vals_from_po(self):
        po = super().read_vals_from_po()
        marks = po.GetDrillMarksType() if GS.pn is not None else po.drill_marks
        self.drill_marks = DRILL_MARKS_REV_MAP[marks]
        return po

    def _configure_plot_settings(self, plot, layers, common_layers):
        """ KiPy plot settings for drill marks """
        super()._configure_plot_settings(plot, layers, common_layers)
        plot.drill_marks = self.drill_marks
