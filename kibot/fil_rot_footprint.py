# -*- coding: utf-8 -*-
# Copyright (c) 2020-2021 Salvador E. Tropea
# Copyright (c) 2020-2021 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
"""
Implements a filter to rotate footprints.
This is inspired in JLCKicadTools by Matthew Lai.
"""
from re import compile
from .gs import GS
from .optionable import Optionable
from .error import KiPlotConfigurationError
from .macros import macros, document, filter_class  # noqa: F401
from . import log
from .fil_base import BaseFilter

logger = log.get_logger()


# Known rotations for JLC
DEFAULT_ROTATIONS = [["^R_Array_Convex_", 90.0],
                     ["^R_Array_Concave_", 90.0],
                     ["^SOT-223", 180.0],
                     ["^SOT-23", 180.0],
                     ["^TSOT-23", 180.0],
                     ["^SOT-353", 180.0],
                     ["^QFN-", 270.0],
                     ["^LQFP-", 270.0],
                     ["^TQFP-", 270.0],
                     ["^SOP-(?!18_)", 270.0],
                     ["^TSSOP-", 270.0],
                     ["^DFN-", 270.0],
                     ["^SOIC-", 270.0],
                     # ["^SOP-18_", 0],
                     ["^VSSOP-10_", 270.0],
                     ["^CP_EIA-3216-18_", 180.0],
                     ["^CP_EIA-3528-15_AVX-H", 180.0],
                     ["^CP_EIA-3528-21_Kemet-B", 180.0],
                     ["^CP_Elec_8x10.5", 180.0],
                     ["^CP_Elec_6.3x7.7", 180.0],
                     ["^CP_Elec_8x6.7", 180.0],
                     ["^CP_Elec_8x10", 180.0],
                     ["^(.*?_|V)?QFN-(16|20|24|28|40)(-|_|$)", 270.0],
                     ["^Bosch_LGA-8_2x2.5mm_P0.65mm_ClockwisePinNumbering", 90.0],
                     ["^PowerPAK_SO-8_Single", 270.0],
                     ["^HTSSOP-28-1EP_4.4x9.7mm*", 270.0],
                     ]


@filter_class
class Rot_Footprint(BaseFilter):  # noqa: F821
    """ Rot_Footprint
        This filter can rotate footprints, used for the positions file generation.
        Some manufacturers use a different rotation than KiCad.
        The internal `_rot_footprint` filter implements the simplest case """
    def __init__(self):
        super().__init__()
        self._is_transform = True
        with document:
            self.extend = True
            """ Extends the internal list of rotations with the one provided.
                Otherwise just use the provided list """
            self.negative_bottom = True
            """ Rotation for bottom components is computed via subtraction as `(component rot - angle)` """
            self.invert_bottom = False
            """ Rotation for bottom components is negated, resulting in either: `(- component rot - angle)`
                or when combined with `negative_bottom`, `(angle - component rot)` """
            self.rotations = Optionable
            """ [list(list(string))] A list of pairs regular expression/rotation.
                Components matching the regular expression will be rotated the indicated angle """
            self.skip_bottom = False
            """ Do not rotate components on the bottom """
            self.skip_top = False
            """ Do not rotate components on the top """

    def config(self, parent):
        super().config(parent)
        self._rot = []
        if isinstance(self.rotations, list):
            for r in self.rotations:
                if len(r) != 2:
                    raise KiPlotConfigurationError("Each regex/angle pair must contain exactly two values, not {} ({})".
                                                   format(len(r), r))
                regex = compile(r[0])
                try:
                    angle = float(r[1])
                except ValueError:
                    raise KiPlotConfigurationError("The second value in the regex/angle pairs must be a number, not {}".
                                                   format(r[1]))
                self._rot.append([regex, angle])
        if self.extend:
            for regex_str, angle in DEFAULT_ROTATIONS:
                self._rot.append([compile(regex_str), angle])
        if not self._rot:
            raise KiPlotConfigurationError("No rotations provided")

    def filter(self, comp):
        """ Apply the rotation """
        if (self.skip_top and not comp.bottom) or (self.skip_bottom and comp.bottom):
            # Component should be excluded
            return
        for regex, angle in self._rot:
            if regex.search(comp.footprint):
                old_angle = comp.footprint_rot
                if self.negative_bottom and comp.bottom:
                    comp.footprint_rot -= angle
                else:
                    comp.footprint_rot += angle
                if self.invert_bottom and comp.bottom:
                    comp.footprint_rot = -comp.footprint_rot
                comp.footprint_rot = comp.footprint_rot % 360
                if GS.debug_level > 2:
                    logger.debug('Rotating ref: {} {}: {} -> {}'.
                                 format(comp.ref, comp.footprint, old_angle, comp.footprint_rot))
                return
