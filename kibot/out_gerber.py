# -*- coding: utf-8 -*-
# Copyright (c) 2020-2026 Salvador E. Tropea
# Copyright (c) 2020-2026 Instituto Nacional de Tecnología Industrial
# Copyright (c) 2018 John Beard
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)
# Adapted from: https://github.com/johnbeard/kiplot
import json
import os
from shutil import move
from .error import PlotError
from .gs import GS
from .kiplot import register_xmp_import
from .misc import FONT_HELP_TEXT, W_GRBJOB
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
            """ Disable aperture macros (workaround for buggy CAM software) (KiCad 6+) """
        super().__init__()
        self._plot_format = GS.PLOT_FORMAT_GERBER
        if GS.global_output is not None:
            self.gerber_job_file = GS.global_output

    def _configure_plot_ctrl(self, po, output_dir):
        """ Called by AnyLayerOptions.run to set the plot options """
        super()._configure_plot_ctrl(po, output_dir)
        po.SetUseGerberProtelExtensions(self.use_protel_extensions)
        po.SetGerberPrecision(5 if self.gerber_precision == 4.5 else 6)
        po.SetCreateGerberJobFile(self.create_gerber_job_file)
        po.SetUseGerberX2format(self.use_gerber_x2_attributes)
        po.SetIncludeGerberNetlistInfo(self.use_gerber_net_attributes)
        po.SetUseAuxOrigin(self.use_aux_axis_as_origin)
        po.SetDrillMarksType(0)
        po.SetDisableGerberMacros(self.disable_aperture_macros)
        po.gerber_job_file = self.gerber_job_file

    def read_vals_from_po(self):
        """ Used to generate an example configuration.
            Called by print_example_options (config_reader.py) """
        po = super().read_vals_from_po()
        if GS.pn is not None:
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
            # useauxorigin
            self.use_aux_axis_as_origin = po.GetUseAuxOrigin()
            # disableapertmacros
            self.disable_aperture_macros = po.GetDisableGerberMacros()
        else:
            self.use_aux_axis_as_origin = po.use_drill_origin
            # TODO: The rest are missing
        return po

    # #########################################################################
    # KiPy implementation
    # #########################################################################

    def _configure_plot_settings(self, plot, layers, common_layers):
        """ KiPy plot settings specific for gerbers """
        super()._configure_plot_settings(plot, layers, common_layers)
        plot.use_drill_origin = self.use_aux_axis_as_origin  # Gerber, DXF, SVG

    def rename_files_in_job_file(self, job_file, renamed):
        with open(job_file, 'rt') as f:
            text = f.read()
        try:
            data = json.loads(text)
        except Exception:
            raise PlotError('Corrupted gerber job file `{job_file}`: {e}')

        if 'FilesAttributes' not in data:
            logger.warning(W_GRBJOB+f'Missing file attributes in gerber job file `{job_file}`')
            return

        for fa in data.get('FilesAttributes'):
            path = fa.get('Path')
            if not path:
                logger.warning(W_GRBJOB+f'Missing path in gerber job file `{job_file}` ({fa})')
                continue
            new_name = renamed.get(path)
            if new_name:
                fa['Path'] = new_name
            else:
                logger.warning(W_GRBJOB+'Unknown gerber file {path} in gerber job file')

        with open(job_file, 'wt') as f:
            f.write(json.dumps(data, indent=2))

    def _do_extra_rename(self, output_dir, kicad_output_base_name, changed_names, renamed):
        """ KiPy: Called after generating all layers and before removing the temporal output dir.
                  Renamed the job file and adjusts it. """
        if not self.create_gerber_job_file:
            return
        job_file_name_kicad = kicad_output_base_name+'-job.gbrjob'
        if not os.path.isfile(job_file_name_kicad):
            raise PlotError(f"Missing gerber job file `{job_file_name_kicad}`")
        # Rename it
        job_file_name = self.expand_filename(output_dir, self.gerber_job_file, 'job', 'gbrjob')
        logger.debug(f"{job_file_name_kicad} -> {job_file_name}")
        move(job_file_name_kicad, job_file_name)
        if changed_names:
            self.rename_files_in_job_file(job_file_name, renamed)

    def _run_export_job(self, destination, plot):
        if self.gerber_precision == 4.5:
            precision = GS.kp.proto.board.board_jobs_pb2.GerberPrecision.GP_5
        else:
            precision = GS.kp.proto.board.board_jobs_pb2.GerberPrecision.GP_6
        res = GS.board.export_gerbers(destination,
                                      plot_settings=plot,
                                      use_board_plot_params=False,
                                      create_gerber_job_file=self.create_gerber_job_file,
                                      include_netlist_attributes=self.use_gerber_net_attributes,
                                      use_x2_format=self.use_gerber_x2_attributes,
                                      disable_aperture_macros=self.disable_aperture_macros,
                                      use_protel_file_extensions=self.use_protel_extensions,
                                      precision=precision)
        self.check_job_ok(res)


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
