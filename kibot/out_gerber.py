# -*- coding: utf-8 -*-
# Copyright (c) 2020-2026 Salvador E. Tropea
# Copyright (c) 2020-2026 Instituto Nacional de Tecnología Industrial
# Copyright (c) 2018 John Beard
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)
# Adapted from: https://github.com/johnbeard/kiplot
import os
from .gs import GS
from .kiplot import register_xmp_import
from .misc import FONT_HELP_TEXT
from .optionable import Optionable
from .out_any_layer import AnyLayer, AnyLayerOptions
from .macros import macros, document, output_class  # noqa: F401
from . import log

logger = log.get_logger()
USEFUL_LAYERS = ['F.SilkS', 'B.SilkS', 'F.Mask', 'B.Mask', 'F.Paste', 'B.Paste', 'Edge.Cuts']


class GerberOptions(AnyLayerOptions):
    def __init__(self):
        with document:
            self.use_aux_axis_as_origin = False
            """ Use the auxiliary axis as origin for coordinates """
            self.line_width = 0.1
            """ [0.02,2] Line_width for objects without width [mm] (KiCad 5) """
            self.subtract_mask_from_silk = False
            """ *Subtract the solder mask from the silk screen """
            self.use_protel_extensions = False
            """ *Use legacy Protel file extensions.
                Important: Inner layers numbering is different for KiCad 8 and 9. KiCad 8 starts numbering inner
                layers with 2 and KiCad 9 with 1 """
            self.gerber_precision = 4.6
            """ [4.5;4.6] This is the gerber coordinate format, can be 4.5 or 4.6 """
            self.create_gerber_job_file = True
            """ *Creates a file with information about all the generated gerbers.
                You can use it in gerbview to load all gerbers at once """
            self.gerber_job_file = GS.def_global_output
            """ Name for the gerber job file (%i='job', %x='gbrjob') """
            self.use_gerber_x2_attributes = True
            """ *Use the extended X2 format (otherwise use X1 formerly RS-274X) """
            self.use_gerber_net_attributes = True
            """ *Include netlist metadata """
            self.disable_aperture_macros = False
            """ Disable aperture macros (workaround for buggy CAM software) (KiCad 6) """
        super().__init__()
        # Gerbers are always 1:1
        del self.scaling
        del self.individual_page_scaling
        self._plot_format = GS.PLOT_FORMAT_GERBER
        if GS.global_output is not None:
            self.gerber_job_file = GS.global_output

    def _configure_plot_ctrl(self, po, output_dir):
        super()._configure_plot_ctrl(po, output_dir)
        po.SetSubtractMaskFromSilk(self.subtract_mask_from_silk)
        po.SetUseGerberProtelExtensions(self.use_protel_extensions)
        po.SetGerberPrecision(5 if self.gerber_precision == 4.5 else 6)
        po.SetCreateGerberJobFile(self.create_gerber_job_file)
        po.SetUseGerberX2format(self.use_gerber_x2_attributes)
        po.SetIncludeGerberNetlistInfo(self.use_gerber_net_attributes)
        po.SetUseAuxOrigin(self.use_aux_axis_as_origin)
        po.SetDrillMarksType(0)
        po.SetDisableGerberMacros(self.disable_aperture_macros)
        po.gerber_job_file = self.gerber_job_file

    def read_vals_from_po(self, po):
        super().read_vals_from_po(po)
        # usegerberattributes
        self.use_gerber_x2_attributes = po.GetUseGerberX2format()
        # usegerberextensions
        self.use_protel_extensions = po.GetUseGerberProtelExtensions()
        # usegerberadvancedattributes
        self.use_gerber_net_attributes = po.GetIncludeGerberNetlistInfo()
        # creategerberjobfile
        self.create_gerber_job_file = po.GetCreateGerberJobFile()
        # gerberprecision
        self.gerber_precision = 4.0 + po.GetGerberPrecision()/10.0
        # subtractmaskfromsilk
        self.subtract_mask_from_silk = po.GetSubtractMaskFromSilk()
        # useauxorigin
        self.use_aux_axis_as_origin = po.GetUseAuxOrigin()
        # disableapertmacros
        self.disable_aperture_macros = po.GetDisableGerberMacros()


@output_class
class Gerber(AnyLayer):
    """ Gerber format
        This is the main fabrication format for the PCB.
        This output is what you get from the File/Plot menu in pcbnew. """
    __doc__ += FONT_HELP_TEXT

    def __init__(self):
        super().__init__()
        with document:
            self.options = GerberOptions
            """ *[dict={}] Options for the `gerber` output """
        self._category = 'PCB/fabrication/gerber'

    @staticmethod
    def get_conf_examples(name, layers):
        gb = {}
        outs = [gb]
        # Create a generic version
        gb['name'] = 'gerber_modern'
        gb['comment'] = 'Gerbers in modern format, recommended by the standard'
        gb['type'] = 'gerber'
        gb['dir'] = 'Gerbers_and_Drill'
        gb['layers'] = [AnyLayer.layer2dict(la) for la in layers]
        # Process the templates
        # Filter the list of layers using the ones we are interested on
        useful = GS.get_useful_layers(USEFUL_LAYERS, layers, include_copper=True)
        tpl_layers = []
        for la in useful:
            tpl_layers.append("- layer: '{}'".format(la.layer))
            tpl_layers.append("  suffix: '{}'".format(la.suffix))
            tpl_layers.append("  description: '{}'".format(la.description))
        tpl_layers = '\n      '.join(tpl_layers)
        register_xmp_import('global', {'_KIBOT_MANF_DIR_COMP': 'Manufacturers',
                                       '_KIBOT_GERBER_LAYERS': tpl_layers})
        # Add the list of layers to the templates
        for tpl in ['Elecrow', 'FusionPCB', 'JLCPCB', 'PCBWay']:
            defs = {'_KIBOT_MANF_DIR': os.path.join('Manufacturers', tpl)}
            if tpl == 'JLCPCB':
                if not GS.sch:
                    # We need the schematic for the variant
                    defs['_KIBOT_POS_ENABLED'] = 'false'
                else:
                    defs['_KIBOT_POS_PRE_TRANSFORM'] = "['_kicost_rename', '_rot_footprint']"
                if not GS.sch_file or not Optionable.solve_field_name('_field_lcsc_part', empty_when_none=True):
                    defs['_KIBOT_BOM_ENABLED'] = 'false'
            register_xmp_import(tpl, defs)
        return outs
