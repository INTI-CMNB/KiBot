# -*- coding: utf-8 -*-
# Copyright (c) 2020-2022 Salvador E. Tropea
# Copyright (c) 2020-2022 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
import os
from tempfile import (NamedTemporaryFile)
# Here we import the whole module to make monkeypatch work
import subprocess
import shutil
from .misc import (PCBDRAW, PCBDRAW_ERR, URL_PCBDRAW, W_AMBLIST, W_UNRETOOL, W_USESVG2, W_USEIMAGICK, PCB_MAT_COLORS,
                   PCB_FINISH_COLORS, SOLDER_COLORS, SILK_COLORS)
from .kiplot import check_script
from .gs import (GS)
from .optionable import Optionable
from .out_base import VariantOptions, BaseOutput
from .macros import macros, document, output_class  # noqa: F401
from . import log

logger = log.get_logger()
SVG2PNG = 'rsvg-convert'
CONVERT = 'convert'


class PcbDrawStyle(Optionable):
    def __init__(self):
        super().__init__()
        with document:
            self.copper = "#285e3a"
            """ color for the copper zones (covered by solder mask) """
            self.board = "#208b47"
            """ color for the board without copper (covered by solder mask) """
            self.silk = "#d5dce4"
            """ color for the silk screen """
            self.pads = "#8b898c"
            """ color for the exposed pads (metal finish) """
            self.outline = "#000000"
            """ color for the outline """
            self.clad = "#cabb3e"
            """ color for the PCB core (not covered by solder mask) """
            self.vcut = "#bf2600"
            """ color for the V-CUTS """
            self.highlight_on_top = False
            """ highlight over the component (not under) """
            self.highlight_style = "stroke:none;fill:#ff0000;opacity:0.5;"
            """ SVG code for the highlight style """
            self.highlight_padding = 1.5
            """ [0,1000] how much the highlight extends around the component [mm] """

    def config(self, parent):
        # Apply global defaults
        # PCB Material
        if GS.global_pcb_material is not None:
            material = GS.global_pcb_material.lower()
            for mat, color in PCB_MAT_COLORS.items():
                if mat in material:
                    self.clad = "#"+color
                    break
        # Solder mask
        if parent.bottom:
            name = GS.global_solder_mask_color_bottom or GS.global_solder_mask_color
        else:
            name = GS.global_solder_mask_color_top or GS.global_solder_mask_color
        if name and name.lower() in SOLDER_COLORS:
            (self.copper, self.board) = SOLDER_COLORS[name.lower()]
        # Silk screen
        if parent.bottom:
            name = GS.global_silk_screen_color_bottom or GS.global_silk_screen_color
        else:
            name = GS.global_silk_screen_color_top or GS.global_silk_screen_color
        if name and name.lower() in SILK_COLORS:
            self.silk = "#"+SILK_COLORS[name.lower()]
        # PCB Finish
        if GS.global_pcb_finish is not None:
            name = GS.global_pcb_finish.lower()
            for nm, color in PCB_FINISH_COLORS.items():
                if nm in name:
                    self.pads = "#"+color
                    break
        super().config(parent)
        self.validate_colors(['board', 'copper', 'board', 'silk', 'pads', 'outline', 'clad', 'vcut'])
        # Not implemented but required
        self.highlight_offset = 0

    def to_dict(self):
        return {k.replace('_', '-'): v for k, v in self.get_attrs_gen()}


class PcbDrawRemap(Optionable):
    """ This class accepts a free form dict.
        No validation is done. """
    def __init__(self):
        super().__init__()

    def config(self, parent):
        pass


def _get_tmp_name(ext):
    with NamedTemporaryFile(mode='w', suffix=ext, delete=False) as f:
        f.close()
    return f.name


def _run_command(cmd, tmp_remap=False, tmp_style=False):
    logger.debug('Executing: '+str(cmd))
    try:
        cmd_output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        logger.error('Failed to run %s, error %d', cmd[0], e.returncode)
        if e.output:
            logger.debug('Output from command: '+e.output.decode())
        exit(PCBDRAW_ERR)
    finally:
        if tmp_remap:
            os.remove(tmp_remap)
        if tmp_style:
            os.remove(tmp_style)
    logger.debug('Output from command:\n'+cmd_output.decode())


class PcbDrawOptions(VariantOptions):
    def __init__(self):
        with document:
            self.style = PcbDrawStyle
            """ [string|dict] PCB style (colors). An internal name, the name of a JSON file or the style options """
            self.libs = Optionable
            """ [list(string)=[]] List of libraries """
            self.placeholder = False
            """ Show placeholder for missing components """
            self.remap = PcbDrawRemap
            """ [dict|None] Replacements for PCB references using components (lib:component) """
            self.no_drillholes = False
            """ Do not make holes transparent """
            self.bottom = False
            """ Render the bottom side of the board (default is top side) """
            self.mirror = False
            """ Mirror the board """
            self.highlight = Optionable
            self.highlight = Optionable
            self.show_components = Optionable
            """ [list(string)|string=none] [none,all] List of components to draw, can be also a string for none or all.
                The default is none """
            self.vcuts = False
            """ Render V-CUTS on the Cmts.User layer """
            self.warnings = 'visible'
            """ [visible,all,none] Using visible only the warnings about components in the visible side are generated """
            self.dpi = 300
            """ [10,1200] Dots per inch (resolution) of the generated image """
            self.format = 'svg'
            """ [svg,png,jpg] Output format. Only used if no `output` is specified """
            self.output = GS.def_global_output
            """ Name for the generated file """
        super().__init__()

    def config(self, parent):
        # Pre-parse the bottom option
        if 'bottom' in self._tree:
            bot = self._tree['bottom']
            if isinstance(bot, bool):
                self.bottom = bot
        super().config(parent)
        # Libs
        if isinstance(self.libs, type):
            self.libs = None
        else:
            self.libs = ','.join(self.libs)
        # Highlight
        if isinstance(self.highlight, type):
            self.highlight = None
        else:
            self.highlight = ','.join(self.highlight)
        # Filter
        if isinstance(self.show_components, type):
            self.show_components = ''
        elif isinstance(self.show_components, str):
            if self.variant or self.dnf_filter:
                logger.warning(W_AMBLIST + 'Ambiguous list of components to show `{}` vs variant/filter'.
                               format(self.show_components))
            if self.show_components == 'none':
                self.show_components = ''
            else:
                self.show_components = None
        else:
            self.show_components = ','.join(self.show_components)
        # Remap
        if isinstance(self.remap, type):
            self.remap = None
        elif isinstance(self.remap, PcbDrawRemap):
            self.remap = self.remap._tree
        # Style
        if isinstance(self.style, type):
            # Apply the global defaults
            style = PcbDrawStyle()
            style.config(self)
            self.style = style.to_dict()
        elif isinstance(self.style, PcbDrawStyle):
            self.style = self.style.to_dict()
        self._expand_id = 'bottom' if self.bottom else 'top'
        self._expand_ext = self.format

    def _create_remap(self):
        with NamedTemporaryFile(mode='w', delete=False) as f:
            f.write('{\n')
            first = True
            for k, v in self.remap.items():
                if first:
                    first = False
                else:
                    f.write(',\n')
                f.write('  "{}": "{}"'.format(k, v))
            f.write('\n}\n')
            f.close()
            return f.name

    def _create_style(self):
        with NamedTemporaryFile(mode='w', delete=False) as f:
            f.write('{\n')
            first = True
            for k, v in self.style.items():
                if first:
                    first = False
                else:
                    f.write(',\n')
                if isinstance(v, str):
                    f.write('  "{}": "{}"'.format(k, v))
                elif isinstance(v, bool):
                    f.write('  "{}": {}'.format(k, str(v).lower()))
                else:
                    f.write('  "{}": {}'.format(k, v))
            f.write('\n}\n')
            f.close()
            return f.name

    def _append_output(self, cmd, output):
        svg = None
        if self.format == 'svg':
            cmd.append(output)
        else:
            # PNG and JPG outputs are unreliable
            if shutil.which(SVG2PNG) is None:
                logger.warning(W_UNRETOOL + '`{}` not installed, using unreliable PNG/JPG conversion'.format(SVG2PNG))
                logger.warning(W_USESVG2 + 'If you experiment problems install `librsvg2-bin` or equivalent')
                cmd.append(output)
            elif shutil.which(CONVERT) is None:
                logger.warning(W_UNRETOOL + '`{}` not installed, using unreliable PNG/JPG conversion'.format(CONVERT))
                logger.warning(W_USEIMAGICK + 'If you experiment problems install `imagemagick` or equivalent')
                cmd.append(output)
            else:
                svg = _get_tmp_name('.svg')
                cmd.append(svg)
        return svg

    def get_targets(self, out_dir):
        return [self._parent.expand_filename(out_dir, self.output)]

    def run(self, name):
        super().run(name)
        check_script(PCBDRAW, URL_PCBDRAW, '0.6.0')
        # Base command with overwrite
        cmd: list[str] = [PCBDRAW]
        # Add user options
        tmp_style = None
        if self.style:
            if isinstance(self.style, str):
                cmd.extend(('-s', self.style))
            else:
                tmp_style = self._create_style()
                cmd.extend(('-s', tmp_style))
        if self.libs:
            cmd.extend(('-l', self.libs))
        if self.placeholder:
            cmd.append('--placeholder')
        if self.no_drillholes:
            cmd.append('--no-drillholes')
        if self.bottom:
            cmd.append('-b')
        if self.mirror:
            cmd.append('--mirror')
        if self.highlight:
            cmd.extend(('-a', self.highlight))
        if self.show_components is not None:
            to_add = ','.join(self.get_fitted_refs())
            if self.show_components and to_add:
                self.show_components += ','
            self.show_components += to_add
            cmd.extend(('-f', self.show_components))
        if self.vcuts:
            cmd.append('-v')
        if self.warnings == 'visible':
            cmd.append('--no-warn-back')
        elif self.warnings == 'none':
            cmd.append('--silent')
        if self.dpi:
            cmd.extend(('--dpi', str(self.dpi)))
        if self.remap:
            tmp_remap = self._create_remap()
            cmd.extend(('-m', tmp_remap))
        else:
            tmp_remap = None
        # The board & output
        cmd.append(GS.pcb_file)
        svg = self._append_output(cmd, name)
        # Execute and inform is successful
        _run_command(cmd, tmp_remap, tmp_style)
        if svg is not None:
            # Manually convert the SVG to PNG
            png = _get_tmp_name('.png')
            _run_command([SVG2PNG, '-d', str(self.dpi), '-p', str(self.dpi), svg, '-o', png], svg)
            cmd = [CONVERT, '-trim', png]
            if self.format == 'jpg':
                cmd += ['-quality', '85%']
            cmd.append(name)
            _run_command(cmd, png)


@output_class
class PcbDraw(BaseOutput):  # noqa: F821
    """ PcbDraw - Beautiful 2D PCB render
        Exports the PCB as a 2D model (SVG, PNG or JPG).
        Uses configurable colors.
        Can also render the components if the 2D models are available """
    def __init__(self):
        super().__init__()
        with document:
            self.options = PcbDrawOptions
            """ [dict] Options for the `pcbdraw` output """

    def get_dependencies(self):
        files = super().get_dependencies()
        if isinstance(self.options.style, str) and os.path.isfile(self.options.style):
            files.append(self.options.style)
        return files
