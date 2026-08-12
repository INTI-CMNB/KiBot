# -*- coding: utf-8 -*-
# Copyright (c) 2020-2026 Salvador E. Tropea
# Copyright (c) 2020-2026 Instituto Nacional de Tecnología Industrial
# Copyright (c) 2018 John Beard
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
# Adapted from: https://github.com/johnbeard/kiplot
from .out_any_layer import AnyLayer
from .drill_marks import DrillMarks
from .gs import GS
from .misc import FONT_HELP_TEXT
from .macros import macros, document, output_class  # noqa: F401
from . import log

logger = log.get_logger()


class PDFOptions(DrillMarks):
    def __init__(self):
        super().__init__()
        with document:
            self.scaling = 1
            """ *Scale factor (0 means autoscaling) """
            self.individual_page_scaling = True
            """ Tell KiCad to apply the scaling for each layer as a separated entity.
                Disabling it the pages are coherent and can be superposed (KiCad <11) """
            self.mirror_plot = False
            """ Plot mirrored """
            self.mirror = None
            """ {mirror_plot} """
            self.negative_plot = False
            """ Invert black and white """
            self.negative = None
            """ {negative_plot} """
            self.exclude_metadata = False
            """ Do not generate metadata from AUTHOR and SUBJECT KiCad variables.
                You can also use the `author` and `subject` options to define the metadata (KiCad 11+) """
            self.author = ''
            """ Override the AUTHOR KiCad variable, used for PDF metadata. (KiCad 11+)
                If blank the KiCad text variable is used """
            self.subject = ''
            """ Override the SUBJECT KiCad variable, used for PDF metadata. (KiCad 11+)
                If blank the KiCad text variable is used """
            self.single_file = False
            """ Plot all the pages to a single file, see `single_page` (KiCad 11+) """
            self.single_page = False
            """ Plot all the layers in a single page when `single_file` is enabled (KiCad 11+) """
            self.front_footprint_property_popups = True
            """ Include footprint property popups for the front side (KiCad 11+) """
            self.back_footprint_property_popups = True
            """ Include footprint property popups for the back side (KiCad 11+) """
            self.monochrome = True
            """ Black and white output (KiCad 11+) """
            self.color_theme = '_builtin_classic'
            """ Selects the color theme (KiCad 11+) """
            self.background_color = ''
            """ Color for the background (KiCad 11+) """
        self._plot_format = GS.PLOT_FORMAT_PDF

    def config(self, parent):
        super().config(parent)
        if self.background_color:
            self.validate_colors(['background_color'])

    def _configure_plot_ctrl(self, po, output_dir):
        super()._configure_plot_ctrl(po, output_dir)
        po.SetMirror(self.mirror_plot)
        po.SetNegative(self.negative_plot)

    def read_vals_from_po(self):
        po = super().read_vals_from_po()
        if GS.pn is not None:
            self.mirror_plot = po.GetMirror()
            self.negative_plot = po.GetNegative()
        else:
            self.mirror_plot = po.mirror
            self.negative_plot = po.negative
            self.scaling = po.scale
            self.monochrome = po.black_and_white
            self.color_theme = po.color_theme
            # TODO: The rest are missing
        return po

    # #########################################################################
    # KiPy implementation
    # #########################################################################

    def _configure_plot_settings(self, plot, layers, common_layers):
        """ KiPy plot settings specific for gerbers """
        super()._configure_plot_settings(plot, layers, common_layers)
        plot.mirror = self.mirror_plot
        plot.negative = self.negative_plot
        plot.scale = self.scaling
        plot.black_and_white = self.monochrome
        plot.color_theme = self.color_theme

    def _run_export_job(self, destination, plot):
        # Three possible modes: one document with one page, one document with multiple pages, multiple documents
        if self.single_file:
            if self.single_page:
                page_mode = GS.kp.proto.board.board_jobs_pb2.BoardJobPaginationMode.BJPM_ALL_LAYERS_ONE_PAGE
                # This isn't intuitive; it's probably a legacy issue.
                single_document = False
            else:
                page_mode = GS.kp.proto.board.board_jobs_pb2.BoardJobPaginationMode.BJPM_EACH_LAYER_OWN_PAGE
                single_document = True
        else:  # multiple files
            page_mode = GS.kp.proto.board.board_jobs_pb2.BoardJobPaginationMode.BJPM_EACH_LAYER_OWN_FILE
            single_document = False

        # Author/Subject override
        old_author = old_subject = None
        if not self.exclude_metadata and (self.author or self.subject):
            project = GS.board.get_project()
            variables = project.get_text_variables()
            if self.author:
                old_author = variables['AUTHOR']
                variables['AUTHOR'] = self.author
            if self.subject:
                old_subject = variables['SUBJECT']
                variables['SUBJECT'] = self.subject
            project.set_text_variables(variables)

        background_color = self.color_str_to_rgb(self.background_color) if self.background_color else ''

        res = GS.board.export_pdf(destination,
                                  plot_settings=plot,
                                  include_metadata=not self.exclude_metadata,
                                  single_document=single_document,
                                  page_mode=page_mode,
                                  background_color=background_color,
                                  front_footprint_property_popups=self.front_footprint_property_popups,
                                  back_footprint_property_popups=self.back_footprint_property_popups)

        # Restore Author/Subject
        if old_author is not None:
            variables['AUTHOR'] = old_author
        if old_subject is not None:
            variables['SUBJECT'] = old_subject
        if old_author is not None or old_subject is not None:
            project.set_text_variables(variables)

        self.check_job_ok(res)


@output_class
class PDF(AnyLayer, DrillMarks):
    """ PDF (Portable Document Format)
        Exports the PCB to the most common exchange format. Suitable for printing.
        Note that this output isn't the best for documating your project.
        This output is what you get from the File/Plot menu in pcbnew.
        The `pcb_print` is usually a better alternative. """
    __doc__ += FONT_HELP_TEXT

    def __init__(self):
        super().__init__()
        with document:
            self.options = PDFOptions
            """ *[dict={}] Options for the `pdf` output """
        self._category = 'PCB/docs'
