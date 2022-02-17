# -*- coding: utf-8 -*-
# Copyright (c) 2020-2021 Salvador E. Tropea
# Copyright (c) 2020-2021 Instituto Nacional de Tecnología Industrial
# Copyright (c) 2018 John Beard
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
# Adapted from: https://github.com/johnbeard/kiplot
import os
import re
from pcbnew import (GERBER_JOBFILE_WRITER, PLOT_CONTROLLER, IsCopperLayer, F_Cu, B_Cu, Edge_Cuts, PLOT_FORMAT_HPGL,
                    PLOT_FORMAT_GERBER, PLOT_FORMAT_POST, PLOT_FORMAT_DXF, PLOT_FORMAT_PDF, PLOT_FORMAT_SVG)
from .optionable import Optionable
from .out_base import BaseOutput, VariantOptions
from .error import PlotError, KiPlotConfigurationError
from .layer import Layer
from .gs import GS
from .misc import W_NOLAYER
from .macros import macros, document  # noqa: F401
from . import log

logger = log.get_logger()


FORMAT_EXTENSIONS = {PLOT_FORMAT_HPGL: 'plt',
                     PLOT_FORMAT_GERBER: 'gbr',
                     PLOT_FORMAT_POST: 'ps',
                     PLOT_FORMAT_DXF: 'dxf',
                     PLOT_FORMAT_PDF: 'pdf',
                     PLOT_FORMAT_SVG: 'svg'}


class CustomReport(Optionable):
    def __init__(self):
        super().__init__()
        with document:
            self.output = 'Custom_report.txt'
            """ File name for the custom report """
            self.content = ''
            """ Content for the report. Use ${basename} for the project name without extension.
                Use ${filename(LAYER)} for the file corresponding to LAYER """


class AnyLayerOptions(VariantOptions):
    """ Base class for: DXF, Gerber, HPGL, PDF, PS and SVG """
    def __init__(self):
        with document:
            self.exclude_edge_layer = True
            """ Do not include the PCB edge layer """
            self.exclude_pads_from_silkscreen = False
            """ Do not plot the component pads in the silk screen (KiCad 5.x only) """
            self.plot_sheet_reference = False
            """ Currently without effect """
            self.plot_footprint_refs = True
            """ Include the footprint references """
            self.plot_footprint_values = True
            """ Include the footprint values """
            self.force_plot_invisible_refs_vals = False
            """ Include references and values even when they are marked as invisible """
            self.output = GS.def_global_output
            """ Output file name, the default KiCad name if empty """
            self.tent_vias = True
            """ Cover the vias """
            self.uppercase_extensions = False
            """ Use uppercase names for the extensions """
            self.inner_extension_pattern = ''
            """ Used to change the Protel style extensions for inner layers.
                The replacement pattern can contain %n for the inner layer number and %N for the layer number.
                Example '.g%n' """
            self.edge_cut_extension = ''
            """ Used to configure the edge cuts layer extension for Protel mode. Include the dot """
            self.custom_reports = CustomReport
            """ [list(dict)] A list of customized reports for the manufacturer """
        super().__init__()

    def config(self, parent):
        super().config(parent)
        if isinstance(self.custom_reports, type):
            self.custom_reports = []

    def _configure_plot_ctrl(self, po, output_dir):
        logger.debug("Configuring plot controller for output")
        po.SetOutputDirectory(output_dir)
        po.SetPlotFrameRef(self.plot_sheet_reference)
        po.SetPlotReference(self.plot_footprint_refs)
        po.SetPlotValue(self.plot_footprint_values)
        po.SetPlotInvisibleText(self.force_plot_invisible_refs_vals)
        po.SetExcludeEdgeLayer(self.exclude_edge_layer)
        if GS.ki5():
            po.SetPlotPadsOnSilkLayer(not self.exclude_pads_from_silkscreen)
        po.SetPlotViaOnMaskLayer(not self.tent_vias)
        # Only useful for gerber outputs
        po.SetCreateGerberJobFile(False)
        # We'll come back to this on a per-layer basis
        po.SetSkipPlotNPTH_Pads(False)

    def filter_components(self, board):
        """  Apply the variants and filters """
        if not self._comps:
            return None
        self.comps_hash = self.get_refs_hash()
        self.cross_modules(board, self.comps_hash)
        return self.remove_paste_and_glue(board, self.comps_hash)

    def unfilter_components(self, board):
        self.uncross_modules(board, self.comps_hash)
        self.restore_paste_and_glue(board, self.comps_hash)

    def compute_name(self, k_filename, output_dir, output, id, suffix):
        if output:
            filename = self.expand_filename(output_dir, output, suffix, os.path.splitext(k_filename)[1][1:])
        else:
            filename = k_filename
        if id > F_Cu and id < B_Cu and self.inner_extension_pattern:
            ext = self.inner_extension_pattern
            ext = ext.replace('%n', str(id))
            ext = ext.replace('%N', str(id+1))
            filename = os.path.splitext(filename)[0]+ext
        if id == Edge_Cuts and self.edge_cut_extension:
            filename = os.path.splitext(filename)[0]+self.edge_cut_extension
        if self.uppercase_extensions:
            filename = os.path.splitext(filename)[0]+os.path.splitext(filename)[1].upper()
        return filename

    def run(self, output_dir, layers):
        super().run(output_dir)
        # fresh plot controller
        plot_ctrl = PLOT_CONTROLLER(GS.board)
        # set up plot options for the whole output
        po = plot_ctrl.GetPlotOptions()
        self._configure_plot_ctrl(po, output_dir)
        # Gerber Job files aren't automagically created
        # We need to assist KiCad
        create_job = po.GetCreateGerberJobFile()
        if create_job:
            jobfile_writer = GERBER_JOBFILE_WRITER(GS.board)
        plot_ctrl.SetColorMode(True)
        # Apply the variants and filters
        exclude = self.filter_components(GS.board)
        # Plot every layer in the output
        generated = {}
        layers = Layer.solve(layers)
        for la in layers:
            suffix = la.suffix
            desc = la.description
            id = la.id
            if not GS.board.IsLayerEnabled(id):
                logger.warning(W_NOLAYER+'Layer "{}" isn\'t used'.format(desc))
                continue
            # Set current layer
            plot_ctrl.SetLayer(id)
            # Skipping NPTH is controlled by whether or not this is
            # a copper layer
            is_cu = IsCopperLayer(id)
            po.SetSkipPlotNPTH_Pads(is_cu)
            # Plot single layer to file
            logger.debug("Opening plot file for layer `{}` format `{}`".format(la, self._plot_format))
            if not plot_ctrl.OpenPlotfile(suffix, self._plot_format, desc):
                # Shouldn't happen
                raise PlotError("OpenPlotfile failed!")  # pragma: no cover (Internal)
            # Compute the current file name and the one we want
            k_filename = plot_ctrl.GetPlotFileName()
            filename = self.compute_name(k_filename, output_dir, self.output, id, suffix)
            logger.debug("Plotting layer `{}` to `{}`".format(la, filename))
            plot_ctrl.PlotLayer()
            plot_ctrl.ClosePlot()
            if self.output:
                os.rename(k_filename, filename)
            if create_job:
                jobfile_writer.AddGbrFile(id, os.path.basename(filename))
            generated[la.layer] = os.path.basename(filename)
        # Create the job file
        if create_job:
            jobfile_writer.CreateJobFile(self.expand_filename(output_dir, po.gerber_job_file, 'job', 'gbrjob'))
        # Custom reports
        regex_fname = re.compile(r'\$\{filename\(.*\)\}')
        for report in self.custom_reports:
            filename = report.output
            content = report.content
            # Replace special white spaces
            content = content.replace('\\r', chr(13))
            content = content.replace('\\n', chr(10))
            content = content.replace('\\t', chr(9))
            # Replace file names, compatible with gerber_zipper_action
            content = content.replace('${basename}', GS.pcb_basename)
            for name, file in generated.items():
                content = content.replace('${filename('+name+')}', file)
            # Replace unused layers
            content = regex_fname.sub('', content)
            # Create the report
            logger.debug('Creating custom report `'+filename+'`')
            with open(os.path.join(output_dir, filename), 'wt') as f:
                f.write(content)
        # Restore the eliminated layers
        if exclude:
            self.unfilter_components(GS.board)

    def solve_extension(self, layer):
        if self._plot_format == PLOT_FORMAT_GERBER and self.use_protel_extensions:
            return layer._protel_extension
        return FORMAT_EXTENSIONS[self._plot_format]

    def get_targets(self, output_dir, layers):
        targets = []
        layers = Layer.solve(layers)
        for la in layers:
            id = la.id
            if not GS.board.IsLayerEnabled(id):
                continue
            k_filename = self.expand_filename(output_dir, '%f-%i.%x', la.suffix, self.solve_extension(la))
            filename = self.compute_name(k_filename, output_dir, self.output, id, la.suffix)
            if GS.debug_level > 2:
                logger.debug('Layer id {} file name {} ({})'.format(id, filename, k_filename))
            targets.append(filename)
        if self._plot_format == PLOT_FORMAT_GERBER and self.create_gerber_job_file:
            targets.append(self.expand_filename(output_dir, self.gerber_job_file, 'job', 'gbrjob'))
        for report in self.custom_reports:
            targets.append(os.path.join(output_dir, report.output))
        return targets

    def read_vals_from_po(self, po):
        # excludeedgelayer
        self.exclude_edge_layer = po.GetExcludeEdgeLayer()
        # plotframeref
        self.plot_sheet_reference = po.GetPlotFrameRef()
        # plotreference
        self.plot_footprint_refs = po.GetPlotReference()
        # plotvalue
        self.plot_footprint_values = po.GetPlotValue()
        # plotinvisibletext
        self.force_plot_invisible_refs_vals = po.GetPlotInvisibleText()
        # viasonmask
        self.tent_vias = not po.GetPlotViaOnMaskLayer()
        if GS.ki5():
            # padsonsilk
            self.exclude_pads_from_silkscreen = not po.GetPlotPadsOnSilkLayer()


class AnyLayer(BaseOutput):
    def __init__(self):
        super().__init__()
        with document:
            self.layers = Layer
            """ [list(dict)|list(string)|string] [all,selected,copper,technical,user]
                List of PCB layers to plot """

    def config(self, parent):
        super().config(parent)
        # We need layers
        if isinstance(self.layers, type):
            raise KiPlotConfigurationError("Missing `layers` list")

    def get_targets(self, out_dir: str):
        return self.options.get_targets(out_dir, self.layers)

    def run(self, output_dir: str):
        self.options.run(output_dir, self.layers)
