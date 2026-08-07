# -*- coding: utf-8 -*-
# Copyright (c) 2020-2026 Salvador E. Tropea
# Copyright (c) 2020-2026 Instituto Nacional de Tecnología Industrial
# Copyright (c) 2018 John Beard
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)
# Adapted from: https://github.com/johnbeard/kiplot
import glob
import os
import re
from shutil import move
from .optionable import Optionable
from .out_base import BaseOutput, VariantOptions
from .error import PlotError
from .layer import Layer
from .gs import GS
from .misc import W_NOLAYER, KICAD_VERSION_7_0_1, MISSING_TOOL, AUTO_SCALE, KICAD_VERSION_9_0_1
from .macros import macros, document  # noqa: F401
from . import log

logger = log.get_logger()


FORMAT_EXTENSIONS = {GS.PLOT_FORMAT_HPGL: 'plt',
                     GS.PLOT_FORMAT_GERBER: 'gbr',
                     GS.PLOT_FORMAT_POST: 'ps',
                     GS.PLOT_FORMAT_DXF: 'dxf',
                     GS.PLOT_FORMAT_PDF: 'pdf',
                     GS.PLOT_FORMAT_SVG: 'svg'}


class CustomReport(Optionable):
    def __init__(self):
        super().__init__()
        with document:
            self.output = 'Custom_report.txt'
            """ File name for the custom report """
            self.content = ''
            """ Content for the report. Use ``${basename}`` for the project name without extension.
                Use ``${filename(LAYER)}`` for the file corresponding to LAYER """

    def __str__(self):
        return self.output


class AnyLayerOptions(VariantOptions):
    """ Base class for: DXF, Gerber, HPGL, PDF, PS and SVG """
    def __init__(self):
        with document:
            self.exclude_edge_layer = True
            """ Do not include the PCB edge layer """
            self.plot_sheet_reference = False
            """ *Include the frame and title block. Only available for KiCad 6+ and you get a poor result
                (i.e. always the default worksheet style, also problems expanding text variables).
                The `pcb_print` output can do a better job for PDF, SVG, PS, EPS and PNG outputs """
            self.plot_footprint_refs = True
            """ Include the footprint references """
            self.plot_footprint_values = True
            """ Include the footprint values """
            self.force_plot_invisible_refs_vals = False
            """ Include references and values even when they are marked as invisible.
                Not available on KiCad 9.0.1 and newer """
            self.output = GS.def_global_output
            """ *Output file name, the default KiCad name if empty.
                Important: KiCad will always create the file using its own name and then we can rename it.
                For this reason you must avoid generating two variants at the same directory when one of
                them uses the default KiCad name """
            self.tent_vias = True
            """ Cover the vias. Usable for KiCad versions older than 9.
                Warning: KiCad 8 has a bug that ignores this option. Set it from KiCad GUI """
            self.uppercase_extensions = False
            """ Use uppercase names for the extensions """
            self.inner_extension_pattern = ''
            """ Used to change the Protel style extensions for inner layers.
                The replacement pattern can contain %n for the inner layer number and %N for the layer number.
                Example '.g%n'.
                Important: this numbering is consistent and the first inner layer is %n = 1 and %N = 2. Which
                isn't true for KiCad. KiCad 8 uses 2 for the first inner and KiCad 9 uses 1 """
            self.edge_cut_extension = ''
            """ Used to configure the edge cuts layer extension for Protel mode. Include the dot """
            self.custom_reports = CustomReport
            """ [list(dict)=[]] A list of customized reports for the manufacturer """
            self.sketch_pads_on_fab_layers = False
            r""" Draw only the outline of the pads on the \*.Fab layers (KiCad 6+) """
            self.sketch_pad_numbers = False
            r""" Plot pad numbers on top of sketched pads on the \*.Fab layers (KiCad 11+) """
            self.sketch_pad_line_width = 0.1
            """ Line width for the sketched pads [mm], see `sketch_pads_on_fab_layers` (KiCad 6+)
                Note that this value is currently ignored by KiCad (6.0.9) """
            self.subtract_mask_from_silk = False
            """ *Subtract the solder mask from the silk screen """
            self.scaling = 1
            """ *Scale factor (0 means autoscaling) """
            self.individual_page_scaling = True
            """ Tell KiCad to apply the scaling for each layer as a separated entity.
                Disabling it the pages are coherent and can be superposed """
        super().__init__()

    def config(self, parent):
        super().config(parent)
        self.sketch_pad_line_width = GS.from_mm(self.sketch_pad_line_width)

    def _configure_plot_ctrl(self, po, output_dir):
        logger.debug("Configuring plot controller for output")
        po.SetOutputDirectory(output_dir)
        po.SetPlotFrameRef(self.plot_sheet_reference)
        po.SetPlotReference(self.plot_footprint_refs)
        po.SetPlotValue(self.plot_footprint_values)
        po.SetSubtractMaskFromSilk(self.subtract_mask_from_silk)
        if GS.kicad_version_n < KICAD_VERSION_9_0_1:
            po.SetPlotInvisibleText(self.force_plot_invisible_refs_vals)
        # Edge layer included or not
        GS.SetExcludeEdgeLayer(po, self.exclude_edge_layer)
        po.SetSketchPadsOnFabLayers(self.sketch_pads_on_fab_layers)
        po.SetSketchPadLineWidth(self.sketch_pad_line_width)
        if not GS.ki9:
            # Now controlled for each via
            po.SetPlotViaOnMaskLayer(not self.tent_vias)
        # Only useful for gerber outputs
        po.SetCreateGerberJobFile(False)
        # We'll come back to this on a per-layer basis
        po.SetSkipPlotNPTH_Pads(False)
        # Scaling/Autoscale
        if self._plot_format != GS.PLOT_FORMAT_GERBER:
            if self.scaling == AUTO_SCALE:
                po.SetAutoScale(True)
                po.SetScale(1)
            else:
                po.SetAutoScale(False)
                po.SetScale(self.scaling)

    def compute_name(self, k_filename, output_dir, output, id, suffix):
        if output:
            filename = self.expand_filename(output_dir, output, suffix, os.path.splitext(k_filename)[1][1:])
        else:
            filename = k_filename
        if GS.layer_is_inner(id) and self.inner_extension_pattern:
            ext = self.inner_extension_pattern
            index = GS.inner_layer_index(id)
            ext = ext.replace('%n', str(index))
            ext = ext.replace('%N', str(index+1))
            filename = os.path.splitext(filename)[0]+ext
        if id == GS.Edge_Cuts and self.edge_cut_extension:
            filename = os.path.splitext(filename)[0]+self.edge_cut_extension
        if self.uppercase_extensions:
            filename = os.path.splitext(filename)[0]+os.path.splitext(filename)[1].upper()
        return filename

    def compute_kicad_name(self, kicad_output_base_name, layer):
        extension = self.solve_extension(layer)
        file = kicad_output_base_name+'-'+GS.board.get_layer_name(layer.id).replace('.', '_')+'.'+extension
        if not os.path.isfile(file):
            raise PlotError(f"Missing gerber file `{file}` available: {glob.glob(kicad_output_base_name+'*')}")
        return file

    def plot_layer(self, plot_ctrl, id):
        if GS.ki7 and not self.exclude_edge_layer:
            # In KiCad 7 this is not an option, but we can plot more than one layer
            # Note that this needs KiCad 7.0.1 or newer
            seq = GS.pn.LSEQ()
            seq.push_back(GS.Edge_Cuts)
            seq.push_back(id)
            plot_ctrl.PlotLayers(seq)
            return
        plot_ctrl.PlotLayer()

    def create_custom_reports(self, output_dir, generated):
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

    def run(self, output_dir, layers):
        super().run(output_dir)
        if GS.pn:
            self._run_pn(output_dir, layers)
        else:
            self._run_kp(output_dir, layers)

    def _run_pn(self, output_dir, layers):
        """ pcbnew implementation (KiCad 6 to 10) """
        if GS.ki7 and GS.kicad_version_n < KICAD_VERSION_7_0_1 and not self.exclude_edge_layer:
            GS.exit_with_error("Plotting the edge layer is not supported by KiCad 7.0.0\n"
                               "Please upgrade KiCad to 7.0.1 or newer", MISSING_TOOL)
        if GS.ki10 and self._plot_format == GS.PLOT_FORMAT_HPGL:
            GS.exit_with_error("HPGL format was discontinued on KiCad 10", MISSING_TOOL)
        # Memorize the list of visible layers
        old_visible = GS.board.GetVisibleLayers()
        # Apply the variants and filters
        exclude = self.filter_pcb_components()
        # fresh plot controller
        plot_ctrl = GS.pn.PLOT_CONTROLLER(GS.board)
        # set up plot options for the whole output
        po = plot_ctrl.GetPlotOptions()
        if GS.global_disable_kicad_cross_on_fab and hasattr(po, "SetCrossoutDNPFPsOnFabLayers"):
            po.SetCrossoutDNPFPsOnFabLayers(False)
        self._configure_plot_ctrl(po, output_dir)
        # Gerber Job files aren't automagically created
        # We need to assist KiCad
        create_job = po.GetCreateGerberJobFile()
        if create_job:
            jobfile_writer = GS.pn.GERBER_JOBFILE_WRITER(GS.board)
        plot_ctrl.SetColorMode(True)
        # Plot every layer in the output
        generated = {}
        layers = Layer.solve(layers)
        # Make visible only the layers we need
        # This is very important when scaling, otherwise the results are controlled by the .kicad_prl (See #407)
        if self._plot_format != GS.PLOT_FORMAT_GERBER and not self.individual_page_scaling:
            vis_layers = GS.pn.LSET()
            for la in layers:
                vis_layers.addLayer(la._id)
            GS.board.SetVisibleLayers(vis_layers)
        for la in layers:
            suffix = la.suffix
            desc = la.description
            id = la.id
            if not GS.board.IsLayerEnabled(id):
                logger.warning(W_NOLAYER+f'Layer "{desc}" ({la.suffix}) isn\'t used')
                continue
            if self._plot_format != GS.PLOT_FORMAT_GERBER and self.individual_page_scaling:
                # Only this layer is visible
                vis_layers = GS.pn.LSET()
                vis_layers.addLayer(la._id)
                GS.board.SetVisibleLayers(vis_layers)
            # Set current layer
            plot_ctrl.SetLayer(id)
            # Skipping NPTH is controlled by whether or not this is
            # a copper layer
            is_cu = GS.pn.IsCopperLayer(id)
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
            self.plot_layer(plot_ctrl, id)
            plot_ctrl.ClosePlot()
            if self.output and k_filename != filename:
                os.replace(k_filename, filename)
            if create_job:
                jobfile_writer.AddGbrFile(id, os.path.basename(filename))
            generated[la.layer] = os.path.basename(filename)
        # Create the job file
        if create_job:
            jobfile_writer.CreateJobFile(self.expand_filename(output_dir, po.gerber_job_file, 'job', 'gbrjob'))
        # Custom reports
        self.create_custom_reports(output_dir, generated)
        # Restore the eliminated layers
        if exclude:
            self.unfilter_pcb_components()
        # Restore the list of visible layers
        GS.board.SetVisibleLayers(old_visible)
        self._generated_files = generated

    def _configure_plot_settings(self, plot, layers):
        """ KiPy PlotSettings common to all """
        plot.layers = layers
        if not self.exclude_edge_layer:
            plot.common_layers = [GS.Edge_Cuts]

        plot.plot_reference_designators = self.plot_footprint_refs
        plot.plot_footprint_values = self.plot_footprint_values
        plot.plot_drawing_sheet = self.plot_sheet_reference
        plot.sketch_pads_on_fab_layers = self.sketch_pads_on_fab_layers
        plot.plot_pad_numbers = self.sketch_pad_numbers
        plot.subtract_solder_mask_from_silk = self.subtract_mask_from_silk

        plot.crossout_dnp_footprints_on_fab_layers = False
        plot.hide_dnp_footprints_on_fab_layers = False
        plot.sketch_dnp_footprints_on_fab_layers = False
        if not GS.global_disable_kicad_cross_on_fab:
            if GS.global_kicad_cross_mechanism == 'crossout':
                plot.crossout_dnp_footprints_on_fab_layers = True
            elif GS.global_kicad_cross_mechanism == 'hide':
                plot.hide_dnp_footprints_on_fab_layers = True
            elif GS.global_kicad_cross_mechanism == 'sketch':
                plot.sketch_dnp_footprints_on_fab_layers = True

        kicad_variant = self.kicad_variant_name()
        if kicad_variant:
            plot.variant = kicad_variant

    def _do_extra_rename(self, output_dir, kicad_output_base_name, changed_names, renamed):
        """ KiPy hook called after layers creation, but before removing the output dir """
        return

    def _run_kp(self, output_dir, layers):
        """ KiPy implementation """
        # Validate the layers
        layers = Layer.solve(layers)

        enabled_layers = []
        for la in layers:
            if not GS.is_layer_enabled(la.id):
                logger.warning(W_NOLAYER+f'Layer "{la.description}" ({la.suffix}) isn\'t used')
                continue
            enabled_layers.append(la.id)
        logger.debug(f"List of selected and enabled layers: {enabled_layers}")

        plot = GS.kp.board_jobs.PlotSettings()
        self._configure_plot_settings(plot, enabled_layers)

        # Work in a temporal dir to avoid issues (i.e. overwrite files)
        tmp_dir = GS.mkdtemp(self._parent.type)
        self._files_to_remove.append(tmp_dir)

        try:
            self.filter_pcb_components()
            self._run_export_job(tmp_dir, plot)
            self.unfilter_pcb_components()

            # Rename the files
            board_name_no_ext = GS.pcb_basename
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

            self._do_extra_rename(output_dir, kicad_output_base_name, changed_names, renamed)
        finally:
            self.remove_temporals()

        # Custom reports
        self.create_custom_reports(output_dir, generated)

        self._generated_files = generated

    def solve_extension(self, layer):
        if self._plot_format == GS.PLOT_FORMAT_GERBER and self.use_protel_extensions:
            return layer._protel_extension
        return FORMAT_EXTENSIONS[self._plot_format]

    def get_targets(self, output_dir, layers):
        targets = []
        layers = Layer.solve(layers)
        for la in layers:
            id = la.id
            if not GS.is_layer_enabled(id):
                continue
            k_filename = self.expand_filename(output_dir, '%f-%i.%x', la.suffix, self.solve_extension(la))
            filename = self.compute_name(k_filename, output_dir, self.output, id, la.suffix)
            if GS.debug_level > 2:
                logger.debug('Layer id {} file name {} ({})'.format(id, filename, k_filename))
            targets.append(filename)
        if self._plot_format == GS.PLOT_FORMAT_GERBER and self.create_gerber_job_file:
            targets.append(self.expand_filename(output_dir, self.gerber_job_file, 'job', 'gbrjob'))
        for report in self.custom_reports:
            targets.append(os.path.join(output_dir, report.output))
        return targets

    def read_vals_from_po(self, po):
        # excludeedgelayer
        if GS.ki7:
            if GS.kicad_version_n < KICAD_VERSION_9_0_1:
                self.exclude_edge_layer = not po.GetPlotOnAllLayersSelection().Contains(GS.board.GetLayerID('Edge.Cuts'))
            else:
                id = GS.board.GetLayerID('Edge.Cuts')
                self.exclude_edge_layer = po.GetPlotOnAllLayersSequence().TestLayers(id, id+1) != 1
        else:
            self.exclude_edge_layer = po.GetExcludeEdgeLayer()
        # plotframeref
        self.plot_sheet_reference = po.GetPlotFrameRef()
        # plotreference
        self.plot_footprint_refs = po.GetPlotReference()
        # plotvalue
        self.plot_footprint_values = po.GetPlotValue()
        # plotinvisibletext
        self.force_plot_invisible_refs_vals = po.GetPlotInvisibleText() if GS.kicad_version_n < KICAD_VERSION_9_0_1 else False
        # subtractmaskfromsilk
        self.subtract_mask_from_silk = po.GetSubtractMaskFromSilk()
        # viasonmask
        self.tent_vias = True if GS.ki9 else not po.GetPlotViaOnMaskLayer()
        self.sketch_pads_on_fab_layers = po.GetSketchPadsOnFabLayers()
        self.sketch_pad_line_width = po.GetSketchPadLineWidth()
        # scaleselection
        if self._plot_format != GS.PLOT_FORMAT_GERBER:
            sel = po.GetScaleSelection()
            sel = sel if sel < 0 or sel > 4 else 4
            self.scaling = (AUTO_SCALE, 1.0, 1.5, 2.0, 3.0)[sel]


class AnyLayer(BaseOutput):
    def __init__(self):
        super().__init__()
        with document:
            self.layers = Layer
            """ *[list(dict)|list(string)|string='all'] [all,selected,copper,technical,user,inners,outers,*] List
                of PCB layers to plot """

    def get_targets(self, out_dir):
        return self.options.get_targets(out_dir, self.layers)

    @staticmethod
    def layer2dict(la):
        return {'layer': la.layer, 'suffix': la.suffix, 'description': la.description}

    @staticmethod
    def get_conf_examples(name, layers):
        if name == 'hpgl' and GS.ki10:
            return None
        gb = {}
        outs = [gb]
        name_u = name.upper()
        gb['name'] = 'basic_'+name
        gb['comment'] = 'Individual layers in '+name_u+' format'
        gb['type'] = name
        gb['dir'] = os.path.join('Individual_Layers', name_u)
        gb['layers'] = [AnyLayer.layer2dict(la) for la in layers]
        return outs

    def run(self, output_dir):
        self.options.run(output_dir, self.layers)
