# -*- coding: utf-8 -*-
# Copyright (c) 2024 Salvador E. Tropea
# Copyright (c) 2024 Instituto Nacional de Tecnología Industrial
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)
# This filter takes ideas from https://github.com/snhobbs/kicad-testpoints by Simon Hobbs
import pcbnew
from copy import deepcopy
from .gs import GS
from .optionable import Optionable
from .misc import MISSING_TOOL
from .macros import macros, document, filter_class  # noqa: F401
from . import log
logger = log.get_logger()


class PadAttribute(Optionable):
    _default = ['testpoint']


@filter_class
class Separate_Pins(BaseFilter):  # noqa: F821
    """ Separate Pins
        This filter can create pseudo-components from pins of the components.
        Is used to create special BoMs to perform electrical checks using nail of beds.
        Use it as a `pre_transform` filter for the `bom` output.
        Important: The pin coordinates aren't affected by the rotation filters.
        Important: Needs KiCad 6 or newer """
    def __init__(self):
        super().__init__()
        self._is_transform = True
        with document:
            self.ref_sep = '.'
            """ Separator used in the reference (i.e. R10.1) """
            self.attribute = PadAttribute
            """ [string|list(string)] [bga,local_fiducial,global_fiducial,testpoint,heatsink,castellated,none] Fabrication
                attribute/s of the included pads """
            self.keep_component = False
            """ If we also keep the original component or we just get the selected pads """

    def config(self, parent):
        super().config(parent)
        if not GS.ki5:
            STR2ATTR = {'bga': pcbnew.PAD_PROP_BGA,
                        'local_fiducial': pcbnew.PAD_PROP_FIDUCIAL_LOCAL,
                        'global_fiducial': pcbnew.PAD_PROP_FIDUCIAL_GLBL,
                        'testpoint': pcbnew.PAD_PROP_TESTPOINT,
                        'heatsink': pcbnew.PAD_PROP_HEATSINK,
                        'castellated': pcbnew.PAD_PROP_CASTELLATED,
                        'none': pcbnew.PAD_PROP_NONE}
            self._attribute = {STR2ATTR[v] for v in self.attribute}

    def filter(self, comp):
        """ Separate the selected pins as pseudo-components """
        if GS.ki5:
            GS.exit_with_error("`separate_pins` needs KiCad 6+", MISSING_TOOL)
        res = []
        if self.keep_component:
            res.append(comp)
        if GS.ki5 or not comp.has_pcb_info:
            # No information from the PCB
            logger.error('No PCB info')
            return res
        id = 1
        for name, v in comp.pad_properties.items():
            if v.fab_property in self._attribute:
                c = deepcopy(comp)
                c.parent_component = comp
                c.ref += self.ref_sep+name
                # Adjust the suffix to be "sort friendly"
                # Currently useless, but could help in the future
                c.ref_suffix = str(int(c.ref_suffix)*100+id)
                c.footprint_x = v.x
                c.footprint_y = v.y
                c.net_name = v.net
                c.net_class = v.net_class
                c.virtual = False
                c.tht = v.has_hole
                c.smd = not v.has_hole
                res.append(c)
        return res
