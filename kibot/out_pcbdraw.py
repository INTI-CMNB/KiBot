# -*- coding: utf-8 -*-
# Copyright (c) 2020-2026 Salvador E. Tropea
# Copyright (c) 2020-2026 Instituto Nacional de Tecnología Industrial
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)
"""
Dependencies:
  - from: RSVG
    role: Create PNG, JPG and BMP images
  - from: ImageMagick
    role: Create JPG and BMP images
  - from: LXML
    role: mandatory
  - name: numpy
    python_module: true
    debian: python3-numpy
    arch: python-numpy
    downloader: python
    role: Automatically adjust SVG margin
"""
PROFILE_PLOT = False
if PROFILE_PLOT:
    import cProfile
import os
from subprocess import CalledProcessError
# Here we import the whole module to make monkeypatch work
from .error import KiPlotConfigurationError
from .kiplot import load_sch, get_board_comps_data, run_command
from .misc import (PCBDRAW_ERR, PCB_MAT_COLORS, PCB_FINISH_COLORS, SOLDER_COLORS, SILK_COLORS, W_PCBDRAW)
from .gs import GS
from .layer import Layer
from .optionable import Optionable
from .out_base import VariantOptions, PcbMargin
from .macros import macros, document, output_class  # noqa: F401
from . import log


logger = log.get_logger()


def mm2ki(val: float) -> int:
    return int(val * 1000000)


def pcbdraw_warnings(tag, msg):
    logger.warning('{}({}) {}'.format(W_PCBDRAW, tag, msg))


def _run_command(cmd):
    try:
        run_command(cmd, err_lvl=PCBDRAW_ERR, just_raise=True)
    except CalledProcessError as e:
        output = e.stdout or e.stderr
        if '--unlimited' in output.decode():
            cmd.remove('--unlimited')
            return run_command(cmd, err_lvl=PCBDRAW_ERR)


class PcbDrawStyle(Optionable):
    def __init__(self):
        super().__init__()
        with document:
            self.copper = "#285e3a"
            """ *Color for the copper zones (covered by solder mask) """
            self.board = "#208b47"
            """ *Color for the board without copper (covered by solder mask) """
            self.silk = "#d5dce4"
            """ *Color for the silk screen """
            self.pads = "#8b898c"
            """ *Color for the exposed pads (metal finish) """
            self.outline = "#000000"
            """ *Color for the outline """
            self.clad = "#cabb3e"
            """ *Color for the PCB core (not covered by solder mask) """
            self.vcut = "#bf2600"
            """ Color for the V-CUTS """
            self.highlight_on_top = False
            """ Highlight over the component (not under) """
            self.highlight_style = "stroke:none;fill:#ff0000;opacity:0.5;"
            """ SVG code for the highlight style """
            self.highlight_padding = 1.5
            """ [0,1000] How much the highlight extends around the component [mm] """

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


class PcbDrawResistorRemap(Optionable):
    """ Reference -> New value """
    def __init__(self):
        super().__init__()
        with document:
            self.ref = ''
            """ *Reference for the resistor to change """
            self.reference = None
            """ {ref} """
            self.val = ''
            """ *Value to use for `ref` """
            self.value = None
            """ {val} """
        self._ref_example = 'R1'
        self._val_example = '10k'

    def config(self, parent):
        super().config(parent)
        if not self.ref or not self.val:
            raise KiPlotConfigurationError("The resistors remapping must specify a `ref` and a `val`")

    def __str__(self):
        return f'{self.ref} -> {self.val}'


class PcbDrawRemapComponents(Optionable):
    """ Reference -> Library + Footprint """
    def __init__(self):
        super().__init__()
        with document:
            self.ref = ''
            """ *Reference for the component to change """
            self.reference = None
            """ {ref} """
            self.lib = ''
            """ *Library to use """
            self.library = None
            """ {lib} """
            self.comp = ''
            """ *Component to use (from `lib`) """
            self.component = None
            """ {comp} """
        self._ref_example = 'D1'
        self._lib_example = 'LEDs'
        self._comp_example = 'LED-5MM_green'

    def config(self, parent):
        super().config(parent)
        if not self.ref or not self.lib or not self.comp:
            raise KiPlotConfigurationError("The component remapping must specify a `ref`, a `lib` and a `comp`")

    def __str__(self):
        return f'{self.ref} -> {self.lib}:{self.comp}'


class PcbDrawLibs(Optionable):
    _default = ['KiCAD-base']


class PcbDrawOptions(VariantOptions):
    def __init__(self):
        with document:
            self.style = PcbDrawStyle
            """ *[string|dict={}] PCB style (colors). An internal name, the name of a JSON file or the style options """
            self.libs = PcbDrawLibs
            """ [list(string)] List of libraries """
            self.placeholder = False
            """ Show placeholder for missing components """
            self.remap = Optionable
            """ [string_dict|string='None'] (DEPRECATED) Replacements for PCB references using specified components
                (lib:component). Use `remap_components` instead """
            self.remap_components = PcbDrawRemapComponents
            """ [list(dict)=[]] Replacements for PCB references using specified components.
                Replaces `remap` with type check """
            self.no_drillholes = False
            """ Do not make holes transparent """
            self.bottom = False
            """ *Render the bottom side of the board (default is top side) """
            self.mirror = False
            """ *Mirror the board """
            self.highlight = Optionable
            """ [list(string)=[]] List of components to highlight. Filter expansion is also allowed here,
                see `show_components` """
            self.show_components = Optionable
            """ *[list(string)|string='none'] [none,all,*] List of components to draw, can be also a string for none or all.
                The default is none.
                There two ways of using this option, please consult the `add_to_variant` option.
                You can use `_kf(FILTER)` as an element in the list to get all the components that pass the filter.
                You can even use `_kf(FILTER1;FILTER2)` to concatenate filters """
            self.add_to_variant = True
            """ The `show_components` list is added to the list of components indicated by the variant (fitted and not
                excluded).
                This is the old behavior, but isn't intuitive because the `show_components` meaning changes when a variant
                is used. In this mode you should avoid using `show_components` and variants.
                To get a more coherent behavior disable this option, and `none` will always be `none`.
                Also `all` will be what the variant says """
            self.vcuts = False
            """ Render V-CUTS on the `vcuts_layer` layer """
            self.vcuts_layer = 'Cmts.User'
            """ Layer to render the V-CUTS, only used when `vcuts` is enabled.
                Note that any other content from this layer will be included """
            self.warnings = 'visible'
            """ [visible,all,none] Using visible only the warnings about components in the visible side are generated """
            self.dpi = 300
            """ [10,1200] Dots per inch (resolution) of the generated image """
            self.format = 'svg'
            """ *[svg,png,jpg,bmp] Output format. Only used if no `output` is specified """
            self.output = GS.def_global_output
            """ *Name for the generated file """
            self.margin = PcbMargin
            """ [number|dict=0] Margin around the generated image [mm].
                Using a number the margin is the same in the four directions """
            self.outline_width = 0.15
            """ [0,10] Width of the trace to draw the PCB border [mm].
                Note this also affects the drill holes """
            self.show_solderpaste = True
            """ Show the solder paste layers """
            self.show_copper = True
            """ Show tracks and zones """
            self.resistor_remap = PcbDrawResistorRemap
            """ [list(dict)=[]] List of resistors to be remapped. You can change the value of the resistors here """
            self.resistor_flip = Optionable
            """ [string|list(string)=''] {comma_sep} List of resistors to flip its bands """
            self.size_detection = 'kicad_edge'
            """ [kicad_edge,kicad_all,svg_paths] Method used to detect the size of the resulting image.
                The `kicad_edge` method uses the size of the board as reported by KiCad,
                components that extend beyond the PCB limit will be cropped. You can manually
                adjust the margins to make them visible.
                The `kicad_all` method uses the whole size reported by KiCad. Usually includes extra space.
                The `svg_paths` uses all visible drawings in the image. To use this method you
                must install the `numpy` Python module (may not be available in docker images) """
            self.svg_precision = 4
            """ [3,6] Scale factor used to represent 1 mm in the SVG (KiCad 6).
                The value is how much zeros has the multiplier (1 mm = 10 power `svg_precision` units).
                Note that for an A4 paper Firefox 91 and Chrome 105 can't handle more than 5 """
        super().__init__()
        self.get_targets = self._get_targets

    def config(self, parent):
        self._filters_to_expand = False
        # Pre-parse the bottom option
        if 'bottom' in self._tree:
            bot = self._tree['bottom']
            if isinstance(bot, bool):
                self.bottom = bot
        super().config(parent)
        # V-CUTS layer
        self._vcuts_layer = Layer.solve(self.vcuts_layer or 'Cmts.User')[0]._id
        # Highlight
        self._highlight = self.solve_kf_filters(self.highlight)
        # Margin
        self._margin, self.margin = PcbMargin.solve(self.margin)
        # Filter
        if len(self.show_components) == 1 and self.show_components[0] in {'all', 'none'}:
            if self.show_components[0] == 'none':
                self.show_components = None
            else:  # if self.show_components[0] == 'all':
                # Empty list: means we don't filter
                self.show_components = []
        else:  # A list
            self.show_components = self.solve_kf_filters(self.show_components)
        # Resistors Remap
        self._remap = {}
        if isinstance(self.remap, Optionable):
            for ref, v in self.remap._tree.items():
                if not isinstance(v, str):
                    raise KiPlotConfigurationError("Wrong PcbDraw remap, must be `ref: lib:component` ({}: {})".format(ref, v))
                lib_comp = v.split(':')
                if len(lib_comp) == 2:
                    self._remap[ref] = tuple(lib_comp)
                else:
                    raise KiPlotConfigurationError("Wrong PcbDraw remap, must be `ref: lib:component` ({}: {})".format(ref, v))
        elif isinstance(self.remap, str) and self.remap != 'None':
            raise KiPlotConfigurationError(f"Unknown `{self.remap}` option")
        for mapping in self.remap_components:
            self._remap[mapping.ref] = (mapping.lib, mapping.comp)
        # Style
        if isinstance(self.style, PcbDrawStyle):
            self._style = self.style.to_dict()
        else:
            self._style = self.style
        self._expand_id = 'bottom' if self.bottom else 'top'
        self._expand_ext = self.format

    def setup_renderer(self, components, active_components, bottom, name):
        super().setup_renderer(components, active_components)
        self.add_to_variant = False
        self.bottom = bottom
        self.output = name
        if not self.show_components:
            self.show_components = None
        return self.expand_filename_both(name, is_sch=False)

    def save_renderer_options(self):
        """ Save the current renderer settings """
        super().save_renderer_options()
        self.old_bottom = self.bottom
        self.old_add_to_variant = self.add_to_variant
        self.old_output = self.output

    def restore_renderer_options(self):
        """ Restore the renderer settings """
        super().restore_renderer_options()
        self.bottom = self.old_bottom
        self.add_to_variant = self.old_add_to_variant
        self.output = self.old_output

    def expand_filtered_components(self, components):
        """ Expands references to filters in show_components """
        if not components or not self._filters_to_expand:
            return components
        new_list = []
        if self._comps:
            all_comps = self._comps
        else:
            load_sch()
            all_comps = GS.sch.get_components()
            get_board_comps_data(all_comps)
        # Scan the list to show
        for c in components:
            if isinstance(c, str):
                # A reference, just add it
                new_list.append(c)
                continue
            # A filter, add its results
            ext_list = []
            for ac in all_comps:
                if c.filter(ac):
                    ext_list.append(ac.ref)
            new_list += ext_list
        return new_list

    def build_plot_components(self):
        from .PcbDraw.plot import PlotComponents, ResistorValue
        remapping = self._remap

        def remapping_fun(ref, lib, name):
            if ref in remapping:
                remapped_lib, remapped_name = remapping[ref]
                if name.endswith('.back'):
                    return remapped_lib, remapped_name + '.back'
                else:
                    return remapped_lib, remapped_name
            return lib, name

        resistor_values = {}
        for mapping in self.resistor_remap:
            resistor_values[mapping.ref] = ResistorValue(value=mapping.val)
        for ref in self.resistor_flip:
            field = resistor_values.get(ref, ResistorValue())
            field.flip_bands = True
            resistor_values[ref] = field

        plot_components = PlotComponents(remapping=remapping_fun,
                                         resistor_values=resistor_values,
                                         no_warn_back=self.warnings == 'visible')

        filter_set = None
        show_components = self.expand_filtered_components(self.show_components)
        if self._comps:
            # A variant is applied, filter the DNF components
            all_comps = set(self.get_fitted_refs())
            if self.add_to_variant:
                # Old behavior: components from the variant + show_components
                all_comps.update(show_components)
                filter_set = all_comps
            else:
                # Something more coherent
                if show_components:
                    # The user supplied a list of components
                    # Use only the valid ones, but only if fitted
                    filter_set = set(show_components).intersection(all_comps)
                else:
                    # Empty list means all, but here is all fitted
                    filter_set = all_comps
        else:
            # No variant applied
            if show_components:
                # The user supplied a list of components
                # Note: if the list is empty this means we don't filter
                filter_set = set(show_components)
        if filter_set is not None:
            logger.debug('List of filtered components: '+str(filter_set))
            plot_components.filter = lambda ref: ref in filter_set
        else:
            logger.debug('Using all components')

        if self._highlight:
            highlight_set = set(self.expand_filtered_components(self._highlight))
            plot_components.highlight = lambda ref: ref in highlight_set
        return plot_components

    def create_image(self, name, board):
        self.ensure_tool('LXML')
        from .PcbDraw.plot import PcbPlotter, PlotPaste, PlotPlaceholders, PlotSubstrate, PlotVCuts
        # Select a name and format that PcbDraw can handle
        svg_save_output_name = save_output_name = name
        self.rsvg_command = None
        self.convert_command = None
        # Check we have the tools needed for the output format
        if self.format != 'svg':
            # We need RSVG for anything other than SVG
            self.rsvg_command = self.ensure_tool('RSVG')
            svg_save_output_name = GS.tmp_file(suffix='.svg')
            # We need ImageMagick for anything other than SVG and PNG
            if self.format != 'png':
                self.convert_command = self.ensure_tool('ImageMagick')
                save_output_name = GS.tmp_file(suffix='.png')

        try:
            plotter = PcbPlotter(board, edge_only=self.size_detection == 'kicad_edge', svg_precision=self.svg_precision)
            # Read libs from KiBot resources
            plotter.setup_arbitrary_data_path(GS.get_resource_path('pcbdraw'))
            # Libs indicated by PCBDRAW_LIB_PATH
            plotter.setup_env_data_path()
            # Libs from the user HOME and the system (for pcbdraw)
            plotter.setup_global_data_path()
            logger.debugl(3, 'PcbDraw data path: {}'.format(plotter.data_path))
            plotter.yield_warning = pcbdraw_warnings
            plotter.libs = self.libs
            plotter.render_back = self.bottom
            plotter.mirror = self.mirror
            plotter.margin = self._margin
            if self._style:
                if isinstance(self._style, str):
                    plotter.resolve_style(self._style)
                else:
                    plotter.style = self._style
            plotter.plot_plan = [PlotSubstrate(drill_holes=not self.no_drillholes, outline_width=mm2ki(self.outline_width),
                                 copper=self.show_copper)]
            if self.show_solderpaste:
                plotter.plot_plan.append(PlotPaste())
            if self.vcuts:
                plotter.plot_plan.append(PlotVCuts(layer=self._vcuts_layer))
            # Adjust the show_components option if needed
            if self.add_to_variant:
                # Enable the old behavior
                if self._comps and self.show_components is None:
                    # A variant automatically adds their components
                    # So `none` becomes `all`
                    self.show_components = []
            if self.show_components is not None:
                plotter.plot_plan.append(self.build_plot_components())
            if self.placeholder:
                plotter.plot_plan.append(PlotPlaceholders())
            plotter.compute_bbox = self.size_detection == 'svg_paths'
            # Make sure we can use svgpathtools
            if plotter.compute_bbox:
                self.ensure_tool('numpy')
            # Plot it
            if PROFILE_PLOT:
                logger.error('Start')
                with cProfile.Profile() as pr:
                    image = plotter.plot()
                    pr.print_stats(sort='time')
                    pr.print_stats(sort='cumulative')
                logger.error('End')
            else:
                image = plotter.plot()
        # Most errors are reported as RuntimeError
        # When the PCB can't be loaded we get IOError
        # When the SVG contains errors we get SyntaxError
        except (RuntimeError, SyntaxError, IOError) as e:
            GS.exit_with_error('PcbDraw error: '+str(e), PCBDRAW_ERR)

        # Save the result
        logger.debug('Saving output to '+svg_save_output_name)
        image.write(svg_save_output_name)
        # Do we need to convert to PNG?
        if self.rsvg_command:
            logger.debug('Converting {} -> {}'.format(svg_save_output_name, save_output_name))
            cmd = [self.rsvg_command, '--dpi-x', str(self.dpi), '--dpi-y', str(self.dpi),
                   '--output', save_output_name, '--format', 'png', '--unlimited', svg_save_output_name]
            _run_command(cmd)
            os.remove(svg_save_output_name)
        # Do we need to convert the saved file? (JPG/BMP)
        if self.convert_command is not None:
            logger.debug('Converting {} -> {}'.format(save_output_name, name))
            cmd = [self.convert_command, save_output_name]
            if self.format == 'jpg':
                cmd += ['-quality', '85%']
            cmd.append(name)
            _run_command(cmd)
            os.remove(save_output_name)

    def run(self, name):
        super().run(name)
        # Apply any variant
        self.filter_pcb_components(do_3D=True)
        # Create the image
        self.create_image(name, GS.board)
        # Undo the variant
        self.unfilter_pcb_components(do_3D=True)


@output_class
class PcbDraw(BaseOutput):  # noqa: F821
    """ PcbDraw - Beautiful 2D PCB render
        Exports the PCB as a 2D model (SVG, PNG or JPG).
        Uses configurable colors.
        Can also render the components if the 2D models are available.
        Note that this output is fast for simple PCBs, but becomes useless for huge ones.
        You can easily create very complex PCBs using the `panelize` output.
        In this case you can use other outputs, like `render_3d`, which are slow for small
        PCBs but can handle big ones.
        Also note that `render_3d` using `force_stackup_colors` and `orthographic` will
        produce a better alternative and you don't need 2D models. """
    def __init__(self):
        super().__init__()
        with document:
            self.options = PcbDrawOptions
            """ *[dict={}] Options for the `pcbdraw` output """
        self._category = 'PCB/docs'

    def get_dependencies(self):
        files = super().get_dependencies()
        if isinstance(self.options.style, str) and os.path.isfile(self.options.style):
            files.append(self.options.style)
        return files

    def get_renderer_options(self):
        """ Where are the options for this output when used as a 'renderer' """
        return self.options

    @staticmethod
    def get_conf_examples(name, layers):
        outs = []
        for la in layers:
            is_top = la.is_top()
            is_bottom = la.is_bottom()
            if not is_top and not is_bottom:
                continue
            id = 'top' if is_top else 'bottom'
            for style in ['jlcpcb-green-enig', 'set-blue-enig', 'set-red-hasl']:
                style_2 = style.replace('-', '_')
                for fmt in ['svg', 'png', 'jpg']:
                    gb = {}
                    gb['name'] = 'basic_{}_{}_{}_{}'.format(name, fmt, style_2, id)
                    gb['comment'] = 'PCB 2D render in {} format, using {} style'.format(fmt.upper(), style)
                    gb['type'] = name
                    gb['dir'] = os.path.join('PCB', '2D_render', style_2)
                    ops = {'style': style, 'format': fmt}
                    if is_bottom:
                        ops['bottom'] = True
                    gb['options'] = ops
                    outs.append(gb)
        return outs
