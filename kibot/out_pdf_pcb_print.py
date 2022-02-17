# -*- coding: utf-8 -*-
# Copyright (c) 2020-2021 Salvador E. Tropea
# Copyright (c) 2020-2021 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
import os
from shutil import copy2, rmtree
from tempfile import mkdtemp
from .pre_base import BasePreFlight
from .error import (KiPlotConfigurationError)
from .gs import (GS)
from .kiplot import check_script, exec_with_retry, add_extra_options
from .misc import (CMD_PCBNEW_PRINT_LAYERS, URL_PCBNEW_PRINT_LAYERS, PDF_PCB_PRINT)
from .out_base import VariantOptions, BaseOutput
from .macros import macros, document, output_class  # noqa: F401
from .layer import Layer
from . import log

logger = log.get_logger()


class PDF_Pcb_PrintOptions(VariantOptions):
    # Mappings to KiCad config values. They should be the same used in drill_marks.py
    _drill_marks_map = {'none': 0, 'small': 1, 'full': 2}

    def __init__(self):
        with document:
            self.output = GS.def_global_output
            """ Filename for the output PDF (%i=layers, %x=pdf)"""
            self.output_name = None
            """ {output} """
            self.scaling = 1.0
            """ Scale factor (0 means autoscaling)"""
            self._drill_marks = 'full'
            """ What to use to indicate the drill places, can be none, small or full (for real scale) """
            self.plot_sheet_reference = True
            """ Include the title-block """
            self.monochrome = False
            """ Print in black and white """
            self.separated = False
            """ Print layers in separated pages """
            self.mirror = False
            """ Print mirrored (X axis inverted). ONLY for KiCad 6 """
            self.hide_excluded = False
            """ Hide components in the Fab layer that are marked as excluded by a variant """
            self.title = ''
            """ Text used to replace the sheet title. %VALUE expansions are allowed.
                If it starts with `+` the text is concatenated """
            self.force_edge_cuts = True
            """ Only useful for KiCad 6 when printing in one page, you can disable the edge here.
                KiCad 5 forces it by default, and you can't control it from config files.
                Same for KiCad 6 when printing to separated pages """
        super().__init__()
        self._expand_ext = 'pdf'

    @property
    def drill_marks(self):
        return self._drill_marks

    @drill_marks.setter
    def drill_marks(self, val):
        if val not in self._drill_marks_map:
            raise KiPlotConfigurationError("Unknown drill mark type: {}".format(val))
        self._drill_marks = val

    def config(self, parent):
        super().config(parent)
        self._drill_marks = PDF_Pcb_PrintOptions._drill_marks_map[self._drill_marks]

    @staticmethod
    def _copy_project(fname):
        pro_name = GS.pcb_file.replace('.kicad_pcb', GS.pro_ext)
        if not os.path.isfile(pro_name):
            return None
        pro_copy = fname.replace('.kicad_pcb', GS.pro_ext)
        logger.debug('Copying project `{}` to `{}`'.format(pro_name, pro_copy))
        copy2(pro_name, pro_copy)
        return pro_copy

    def filter_components(self, board, force_copy):
        if not self._comps and not force_copy:
            return GS.pcb_file, None
        comps_hash = self.get_refs_hash()
        self.cross_modules(board, comps_hash)
        self.remove_paste_and_glue(board, comps_hash)
        if self.hide_excluded:
            self.remove_fab(board, comps_hash)
        # Save the PCB to a temporal dir
        pcb_dir = mkdtemp(prefix='tmp-kibot-pdf_pcb_print-')
        fname = os.path.join(pcb_dir, GS.pcb_basename+'.kicad_pcb')
        logger.debug('Storing filtered PCB to `{}`'.format(fname))
        GS.board.Save(fname)
        # Copy the project: avoids warnings, could carry some options
        self._copy_project(fname)
        self.uncross_modules(board, comps_hash)
        self.restore_paste_and_glue(board, comps_hash)
        if self.hide_excluded:
            self.restore_fab(board, comps_hash)
        return fname, pcb_dir

    def get_targets(self, out_dir):
        return [self._parent.expand_filename(out_dir, self.output)]

    def run(self, output):
        super().run(self._layers)
        check_script(CMD_PCBNEW_PRINT_LAYERS, URL_PCBNEW_PRINT_LAYERS, '1.5.10')
        # Output file name
        cmd = [CMD_PCBNEW_PRINT_LAYERS, 'export', '--output_name', output]
        if BasePreFlight.get_option('check_zone_fills'):
            cmd.append('-f')
        cmd.extend(['--scaling', str(self.scaling), '--pads', str(self._drill_marks)])
        if not self.plot_sheet_reference:
            cmd.append('--no-title')
        if self.monochrome:
            cmd.append('--monochrome')
        if self.separated:
            cmd.append('--separate')
        if self.mirror:
            cmd.append('--mirror')
        self.set_title(self.title)
        board_name, board_dir = self.filter_components(GS.board, self.title != '')
        cmd.extend([board_name, os.path.dirname(output)])
        cmd, video_remove = add_extra_options(cmd)
        # Add the layers
        cmd.extend([la.layer for la in self._layers])
        if GS.ki6() and self.force_edge_cuts and not self.separated:
            cmd.append('Edge.Cuts')
        # Execute it
        ret = exec_with_retry(cmd)
        self.restore_title()
        # Remove the temporal PCB
        if board_dir:
            logger.debug('Removing temporal variant dir `{}`'.format(board_dir))
            rmtree(board_dir)
        if ret:
            logger.error(CMD_PCBNEW_PRINT_LAYERS+' returned %d', ret)
            exit(PDF_PCB_PRINT)
        if video_remove:
            video_name = os.path.join(self.expand_filename_pcb(GS.out_dir), 'pcbnew_export_screencast.ogv')
            if os.path.isfile(video_name):
                os.remove(video_name)

    def set_layers(self, layers):
        layers = Layer.solve(layers)
        self._layers = layers
        self._expand_id = '+'.join([la.suffix for la in layers])


@output_class
class PDF_Pcb_Print(BaseOutput):  # noqa: F821
    """ PDF PCB Print (Portable Document Format)
        Exports the PCB to the most common exchange format. Suitable for printing.
        This is the main format to document your PCB.
        This output is what you get from the 'File/Print' menu in pcbnew. """
    def __init__(self):
        super().__init__()
        with document:
            self.options = PDF_Pcb_PrintOptions
            """ [dict] Options for the `pdf_pcb_print` output """
            self.layers = Layer
            """ [list(dict)|list(string)|string] [all,selected,copper,technical,user]
                List of PCB layers to include in the PDF """

    def config(self, parent):
        super().config(parent)
        # We need layers
        if isinstance(self.layers, type):
            raise KiPlotConfigurationError("Missing `layers` list")
        self.options.set_layers(self.layers)
