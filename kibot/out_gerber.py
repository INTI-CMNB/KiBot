# -*- coding: utf-8 -*-
# Copyright (c) 2020-2026 Salvador E. Tropea
# Copyright (c) 2020-2026 Instituto Nacional de Tecnología Industrial
# Copyright (c) 2018 John Beard
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)
# Adapted from: https://github.com/johnbeard/kiplot
import glob
import json
import os
from shutil import move
from .error import PlotError
from .gs import GS
from .kiplot import register_xmp_import, run_command
from .layer import Layer
from .misc import FONT_HELP_TEXT, W_NOLAYER, W_GRBJOB
from .optionable import Optionable
from .out_any_layer import AnyLayer, AnyLayerOptions
from .out_base import VariantOptions
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
            """ [0.02,2] Line_width for objects without width [mm] (KiCad 5 only) """
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
            """ Disable aperture macros (workaround for buggy CAM software) (KiCad 6+) """
        super().__init__()
        # Gerbers are always 1:1
        del self.scaling
        del self.individual_page_scaling
        self._plot_format = GS.PLOT_FORMAT_GERBER
        if GS.global_output is not None:
            self.gerber_job_file = GS.global_output

    def _configure_plot_ctrl(self, po, output_dir):
        """ Called by AnyLayerOptions.run to set the plot options """
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
        """ Used to generate an example configuration.
            Called by print_example_options (config_reader.py) """
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

    def compute_kicad_name(self, kicad_output_base_name, layer):
        extension = layer._protel_extension if self.use_protel_extensions else 'gbr'
        file = kicad_output_base_name+'-'+GS.board.get_layer_name(layer.id).replace('.', '_')+'.'+extension
        if not os.path.isfile(file):
            raise PlotError(f"Missing gerber file `{file}` available: {glob.glob(kicad_output_base_name+'*')}")
        return file

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

    def run(self, output_dir, layers):
        """ Gerbers generation using KiPy, for pcbnew we call the AnyLayerOptions implementation """
        if GS.pn is not None:
            super().run(output_dir, layers)
            return
        # Skip AnyLayerOptions altogether, we implement all by CLI
        VariantOptions.run(self, output_dir)

        # Validate the layers
        layers = Layer.solve(layers)

        # Work in a temporal dir to avoid issues (i.e. overwrite files)
        tmp_dir = GS.mkdtemp('gerber')
        self._files_to_remove.append(tmp_dir)

        enabled_layers = []
        for la in layers:
            if not GS.is_layer_enabled(la.id):
                logger.warning(W_NOLAYER+f'Layer "{la.description}" ({la.suffix}) isn\'t used')
                continue
            enabled_layers.append(Layer.id2def_name(la.id))
        logger.debug(f"List of selected and enabled layers: {enabled_layers}")

        # Create the command line
        cmd = [GS.kicad_cli, 'pcb', 'export', 'gerbers', '--output', tmp_dir, '--layers', ','.join(enabled_layers),
               '--precision', str(int((self.gerber_precision-4.0)*10.0))]
        if self.disable_aperture_macros:
            cmd.append('--disable-aperture-macros')
        if not self.exclude_edge_layer:
            cmd.extend(['--common-layers', 'Edge.Cuts'])
        if not self.plot_footprint_refs:
            cmd.append('--exclude-refdes')
        if not self.plot_footprint_values:
            cmd.append('--exclude-value')
        if self.plot_sheet_reference:
            cmd.append('--include-border-title')
        if self.sketch_pads_on_fab_layers:
            cmd.append('--sketch-pads-on-fab-layers')
        if self.sketch_pad_numbers:
            cmd.append('--sketch-pad-numbers')
        if self.subtract_mask_from_silk:
            cmd.append('--subtract-soldermask')
        if self.use_aux_axis_as_origin:
            cmd.append('--use-drill-file-origin')
        if not self.use_gerber_net_attributes:
            cmd.append('--no-netlist')
        if not self.use_gerber_x2_attributes:
            cmd.append('--no-x2')
        if not self.use_protel_extensions:
            cmd.append('--no-protel-ext')
        if not GS.global_disable_kicad_cross_on_fab:
            cmd.append('--crossout-DNP-footprints-on-fab-layers')
        self.add_kicad_cli_variant(cmd)

        try:
            board_name = self.save_tmp_board_if_variant()
            cmd.append(board_name)
            run_command(cmd)

            # Rename the files
            board_name_no_ext = os.path.splitext(os.path.basename(board_name))[0]
            kicad_output_base_name = os.path.join(tmp_dir, board_name_no_ext)
            generated = {}
            renamed = {}
            changed_names = False
            for la in layers:
                id = la.id
                if not GS.is_layer_enabled(id):
                    continue
                suffix = la.suffix
                # desc = la.description
                # Compute the current file name and the one we want
                k_filename = self.compute_kicad_name(kicad_output_base_name, la)
                filename = self.compute_name(k_filename, output_dir, self.output, id, suffix)
                logger.debug(f"Moving {k_filename} -> {filename}")
                move(k_filename, filename)
                filename_no_path = os.path.basename(filename)
                if not changed_names:
                    k_filename_no_path = os.path.basename(k_filename)
                    changed_names = filename_no_path != k_filename_no_path
                generated[la.layer] = filename_no_path
                renamed[os.path.basename(k_filename)] = filename_no_path

            # Gerber Job file is always created
            job_file_name_kicad = kicad_output_base_name+'-job.gbrjob'
            if not os.path.isfile(job_file_name_kicad):
                raise PlotError(f"Missing gerber job file `{job_file_name_kicad}`")
            if self.create_gerber_job_file:
                # Rename it
                job_file_name = self.expand_filename(output_dir, self.gerber_job_file, 'job', 'gbrjob')
                logger.debug(f"{job_file_name_kicad} -> {job_file_name}")
                move(job_file_name_kicad, job_file_name)
                if changed_names:
                    self.rename_files_in_job_file(job_file_name, renamed)
            else:
                # Remove it
                logger.debug(f"Removing {job_file_name_kicad}")
                os.remove(job_file_name_kicad)
        finally:
            self.remove_temporals()

        # Custom reports
        self.create_custom_reports(output_dir, generated)

        self._generated_files = generated


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
