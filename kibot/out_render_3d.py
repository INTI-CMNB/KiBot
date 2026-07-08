# -*- coding: utf-8 -*-
# Copyright (c) 2021-2026 Salvador E. Tropea
# Copyright (c) 2021-2026 Instituto Nacional de Tecnología Industrial
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)
# KiCad 6/6.0.1 bug: https://gitlab.com/kicad/code/kicad/-/issues/9890 Crash [Fixed in 6.0.2]
# KiCad 10 related bugs:
# https://gitlab.com/kicad/code/kicad/-/work_items/21950 -> we need to patch KiCad to get presets working
# https://gitlab.com/kicad/code/kicad/-/work_items/24599 -> Various options ignored
"""
Dependencies:
  - from: KiAuto
    role: mandatory
    version: 2.3.1
    version_k8: 2.3.2
    version_k9: 2.3.5
    version_k10: 2.3.8
  - from: ImageMagick
    role: Automatically crop images
"""
import json
import re
import os
from .error import KiPlotConfigurationError
from .misc import (RENDER_3D_ERR, PCB_MAT_COLORS, PCB_FINISH_COLORS, SOLDER_COLORS, SILK_COLORS,
                   KICAD_VERSION_6_0_2, MISSING_TOOL, W_INV3DLAYER, W_NEEDSK8, W_NEEDSK6, W_DEPR,
                   G_SILKCOLORS, G_MASKCOLORS, G_PASTECOLORS, FINISH_TO_COLOR, G_FINISHCOLORS,
                   G_BOARDCOLORS, KICAD_VERSION_10_0_3)
from .gs import GS
from .out_base_3d import Base3DOptionsWithHL, Base3D
from .kiplot import run_command
from .macros import macros, document, output_class  # noqa: F401
from . import log

logger = log.get_logger()


def _run_command(cmd):
    return run_command(cmd, err_lvl=RENDER_3D_ERR)


class Render3DOptions(Base3DOptionsWithHL):
    _colors = {'background1': 'bg_color_1',
               'background2': 'bg_color_2',
               'copper': 'copper_color',
               'board': 'board_color',
               'silk': 'silk_color',
               'solder_mask': 'sm_color',
               'solder_paste': 'sp_color'}
    _views = {'top': 'z', 'bottom': 'Z', 'front': 'y', 'rear': 'Y', 'right': 'x', 'left': 'X'}
    _rviews = {v: k for k, v in _views.items()}

    def __init__(self):
        with document:
            self.output = GS.def_global_output
            """ *Name for the generated image file (%i='3D_$VIEW' %x='png'/'jpg') """
            self.format = 'png'
            """ [png,jpg] Output format """
            self.no_tht = False
            """ Used to exclude 3D models for through hole components """
            self.no_smd = False
            """ Used to exclude 3D models for surface mount components """
            self.background1 = "#66667F"
            """ First color for the background gradient """
            self.background2 = "#CCCCE5"
            """ Second color for the background gradient """
            self.board = "#332B16"
            """ Color for the board without copper or solder mask """
            self.copper = "#8b898c"
            """ Color for the copper, both sides """
            self.silk = "#d5dce4"
            """ Color for the silk screen, both sides """
            self.solder_mask = "#208b47"
            """ Color for the solder mask, both sides """
            self.solder_paste = "#808080"
            """ Color for the solder paste """
            self.move_x = 0
            """ *Steps to move in the X axis, positive is to the right.
                Just like pressing the right arrow in the 3D viewer """
            self.move_y = 0
            """ *Steps to move in the Y axis, positive is up.
                Just like pressing the up arrow in the 3D viewer """
            self.rotate_x = 0
            """ *Steps to rotate around the X axis, positive is clockwise.
                Each step is currently 10 degrees. Only for KiCad 6+ """
            self.rotate_y = 0
            """ *Steps to rotate around the Y axis, positive is clockwise.
                Each step is currently 10 degrees. Only for KiCad 6+ """
            self.rotate_z = 0
            """ *Steps to rotate around the Z axis, positive is clockwise.
                Each step is currently 10 degrees. Only for KiCad 6+ """
            self.rotate_degrees = False
            """ Instead of `steps` use degrees for rotations. Only available for KiCad 10+ using CLI"""
            self.pivot_x = 0
            """ Set pivot point relative to the board center in centimeters, X axis. Needs KiCad 10+ using CLI """
            self.pivot_y = 0
            """ Set pivot point relative to the board center in centimeters, Y axis. Needs KiCad 10+ using CLI """
            self.pivot_z = 0
            """ Set pivot point relative to the board center in centimeters, Z axis. Needs KiCad 10+ using CLI """
            self.ray_tracing = False
            """ *Enable the ray tracing. Much better result, but slow, and you'll need to adjust `wait_rt` """
            self.wait_render = -600
            """ Only used for KiCad 9 and older.
                How many seconds we must wait before capturing the render (ray tracing or normal).
                Lamentably KiCad can save an unfinished image. Enlarge it if your image looks partially rendered.
                Use negative values to enable the auto-detect using CPU load.
                In this case the value is interpreted as a time-out. """
            self.wait_ray_tracing = None
            """ {wait_render} """
            self.view = 'top'
            """ *[top,bottom,front,rear,right,left,z,Z,y,Y,x,X] Point of view """
            self.zoom = 0
            """ *Zoom steps. Use positive to enlarge, get closer, and negative to reduce.
                Same result as using the mouse wheel in the 3D viewer.
                Note that KiCad 8 starts with a zoom to fit, so you might not even need it """
            self.width = 1280
            """ Image width (aprox.) """
            self.height = 720
            """ Image height (aprox.) """
            self.orthographic = False
            """ Enable the orthographic projection mode (top view looks flat) """
            self.show_silkscreen = True
            """ Show the silkscreen layers (KiCad 6+) """
            self.show_soldermask = True
            """ Show the solder mask layers (KiCad 6+) """
            self.show_solderpaste = True
            """ Show the solder paste layers (KiCad 6+) """
            self.show_copper_top = True
            """ Show copper on the top layer (KiCad 10+ using CLI) """
            self.show_copper_bottom = True
            """ Show copper on the bottom layer (KiCad 10+ using CLI) """
            self.show_plated_barrels = True
            """ Show plated through holes (KiCad 10+ using CLI) """
            self.show_references = True
            """ Show component references in the silk screen (KiCad 10+ using CLI) """
            self.show_values = True
            """ Show component values in the silk screen (KiCad 10+ using CLI) """
            self.show_zones = True
            """ Show filled areas in zones (KiCad 6 to 9) """
            self.clip_silk_on_via_annulus = True
            """ Clip silkscreen at via annuli (KiCad 6 to 9) """
            self.subtract_mask_from_silk = True
            """ Clip silkscreen at solder mask edges (KiCad 6 to 9) """
            self.auto_crop = False
            """ When enabled the image will be post-processed to remove the empty space around the image.
                In this mode the `background2` is changed to be the same as `background1` """
            self.enable_crop_workaround = False
            """ Some versions of Image Magick (i.e. the one in Debian 11) needs two passes to crop.
                Enable it to force a double pass. It was the default in KiBot 1.7.0 and older """
            self.transparent_background = False
            """ When enabled the image will be post-processed to make the background transparent.
                In this mode the `background1` and `background2` colors are ignored.
                Only available for PNGs """
            self.transparent_background_color = "#00ff00"
            """ Only used for KiCad 9 and older.
                Color used for the chroma key. Adjust it if some regions of the board becomes transparent """
            self.transparent_background_fuzz = 15
            """ [0,100] Chroma key tolerance (percent). Bigger values will remove more pixels.
                Only used for KiCad 9 and older """
            self.realistic = True
            """ When disabled we use the colors of the layers used by the GUI. Needs KiCad 6, 7 or 10+.
                Is emulated on KiCad 8 and 9 """
            self.force_stackup_colors = False
            """ Tell KiCad to use the colors from the stackup. They are better than the unified KiBot colors.
                Needs KiCad 6 or newer """
            self.show_board_body = True
            """ Show the PCB core material. KiCad 6 or newer """
            self.show_comments = False
            """ Show the content of the User.Comments and User.Drawings layer for KiCad 5, 6 and 7.
                On KiCad 8+ this option controls only the User.Comments and you have a separated option for the
                User.Drawings called `show_drawings`
                Note that KiCad 5/6/7 doesn't show it when `realistic` is enabled, but KiCad 8 does it.
                Also note that KiCad 5 ray tracer shows comments outside the PCB, but newer KiCad versions
                doesn't.
                KiCad 10.0.3 ignores them """
            self.show_drawings = False
            """ Show the content of the User.Drawings layer. Only available for KiCad 8 and newer.
                Consult `show_comments` to learn when drawings are visible """
            self.show_eco = False
            """ Show the content of the Eco1.User/Eco2.User layers.
                For KiCad 8 `show_eco1` and `show_eco2` are available.
                Consult `show_comments` to learn when drawings are visible """
            self.show_eco1 = False
            """ Show the content of the Eco1.User layer. KiCad 8 supports individual Eco layer options, for 6 and 7
                use the `show_eco` option.
                Consult `show_comments` to learn when drawings are visible """
            self.show_eco2 = False
            """ Show the content of the Eco1.User layer. KiCad 8 supports individual Eco layer options, for 6 and 7
                use the `show_eco` option.
                Consult `show_comments` to learn when drawings are visible """
            self.show_adhesive = False
            """ Show the content of F.Adhesive/B.Adhesive layers. KiCad 6 or newer """
            self.use_cli = True
            """ Try using `kicad-cli` for KiCad 10+.
                More reliable, but with tons of limitations, see KiCad bugs:
                [21950](https://gitlab.com/kicad/code/kicad/-/work_items/21950)
                [24599](https://gitlab.com/kicad/code/kicad/-/work_items/24599)
                [20126](https://gitlab.com/kicad/code/kicad/-/work_items/20126)
            """

        super().__init__()
        self._expand_ext = 'png'

    def config(self, parent):
        # Apply global defaults
        if GS.global_pcb_material is not None:
            material = GS.global_pcb_material.lower()
            for mat, color in PCB_MAT_COLORS.items():
                if mat in material:
                    self.board = "#"+color
                    break
        # Pre parse the view option
        bottom = False
        if 'view' in self._tree:
            v = self._tree['view']
            bottom = isinstance(v, str) and v == 'bottom'
        # Solder mask
        if bottom:
            name = GS.global_solder_mask_color_bottom or GS.global_solder_mask_color
        else:
            name = GS.global_solder_mask_color_top or GS.global_solder_mask_color
        if name and name.lower() in SOLDER_COLORS:
            (_, self.solder_mask) = SOLDER_COLORS[name.lower()]
            # Add the default opacity (80%)
            self.solder_mask += "D4"
        # Silk screen
        if bottom:
            name = GS.global_silk_screen_color_bottom or GS.global_silk_screen_color
        else:
            name = GS.global_silk_screen_color_top or GS.global_silk_screen_color
        if name and name.lower() in SILK_COLORS:
            self.silk = "#"+SILK_COLORS[name.lower()]
        # PCB finish
        if GS.global_pcb_finish is not None:
            name = GS.global_pcb_finish.lower()
            for nm, color in PCB_FINISH_COLORS.items():
                if nm in name:
                    self.copper = "#"+color
                    break
        # Now we can configure (defaults applied)
        super().config(parent)
        self.validate_colors(list(self._colors.keys())+['transparent_background_color'])
        # View and also add it to the ID
        view = self._views.get(self.view, None)
        if view is not None:
            self.view = view
        self._expand_id += '_'+self._rviews.get(self.view)
        # Sanity checks
        if self.rotate_degrees and not (GS.ki10 and self.use_cli):
            raise KiPlotConfigurationError("KiCad 10 is needed for rotations in degrees")
        if self.transparent_background and self.format != 'png':
            raise KiPlotConfigurationError("Transparent background is only available for PNGs")
        if self.force_stackup_colors and not self.realistic:
            raise KiPlotConfigurationError("Choose to disable `realistic` or enable `force_stackup_colors`, not both")
        self._expand_ext = self.format

    def setup_renderer(self, components, active_components, bottom, name):
        super().setup_renderer(components, active_components)
        self.view = 'Z' if bottom else 'z'
        self.output = name
        return self.expand_filename_both(name, is_sch=False)

    def save_renderer_options(self):
        """ Save the current renderer settings """
        super().save_renderer_options()
        self.old_show_all_components = self._show_all_components
        self.old_view = self.view
        self.old_output = self.output

    def restore_renderer_options(self):
        """ Restore the renderer settings """
        super().restore_renderer_options()
        self._show_all_components = self.old_show_all_components
        self.view = self.old_view
        self.output = self.old_output

    def add_step(self, cmd, steps, ops):
        if steps:
            cmd.extend([ops, str(steps)])

    def add_options(self, cmd):
        # Add user options
        if not self.no_virtual:
            cmd.append('--virtual')
        if self.no_tht:
            cmd.append('--no_tht')
        if self.no_smd:
            cmd.append('--no_smd')
        for color, option in self._colors.items():
            cmd.extend(['--'+option, getattr(self, color)])
        self.add_step(cmd, self.move_x, '--move_x')
        self.add_step(cmd, self.move_y, '--move_y')
        self.add_step(cmd, self.rotate_x, '--rotate_x')
        self.add_step(cmd, self.rotate_y, '--rotate_y')
        self.add_step(cmd, self.rotate_z, '--rotate_z')
        if self.zoom:
            cmd.extend(['--zoom', str(self.zoom)])
        if self.wait_render != 5:
            if self.wait_render < 0:
                self.wait_render = -self.wait_render
                cmd.append('--detect_rt')
            cmd.extend(['--wait_rt', str(self.wait_render), '--use_rt_wait'])
        if self.ray_tracing:
            cmd.append('--ray_tracing')
        if self.orthographic:
            cmd.append('--orthographic')
        if self.view != 'z':
            cmd.extend(['--view', self.view])
        if not self.show_silkscreen:
            cmd.append('--hide_silkscreen')
        if not self.show_soldermask:
            cmd.append('--hide_soldermask')
        if not self.show_solderpaste:
            cmd.append('--hide_solderpaste')
        if not self.show_zones:
            cmd.append('--hide_zones')
        if not self.clip_silk_on_via_annulus:
            cmd.append('--dont_clip_silk_on_via_annulus')
        if not self.subtract_mask_from_silk:
            cmd.append('--dont_substrack_mask_from_silk')
        if not self.realistic:
            cmd.append('--use_layer_colors')
        if self.force_stackup_colors:
            cmd.append('--use_stackup_colors')
        if not self.show_board_body:
            cmd.append('--hide_board_body')
        if self.show_comments:
            cmd.append('--show_comments')
        if self.show_drawings:
            cmd.append('--show_drawings')
        if self.show_eco:
            cmd.append('--show_eco')
        if self.show_eco1:
            cmd.append('--show_eco1')
        if self.show_eco2:
            cmd.append('--show_eco2')
        if self.show_adhesive:
            cmd.append('--show_adhesive')
        if not GS.ki8:
            if (self.show_comments or self.show_drawings or self.show_eco) and self.realistic:
                logger.warning(W_INV3DLAYER+"The comments, drawings and eco layers aren't visible when realistic is enabled")
            if self.show_drawings:
                logger.warning(W_NEEDSK8+"`show_drawings` needs KiCad 8 or newer")
            if self.show_eco1:
                logger.warning(W_NEEDSK8+"`show_eco1` needs KiCad 8 or newer")
            if self.show_eco2:
                logger.warning(W_NEEDSK8+"`show_eco2` needs KiCad 8 or newer")
        if not GS.ki6:
            if self.force_stackup_colors:
                logger.warning(W_NEEDSK6+"`force_stackup_colors` needs KiCad 6 or newer")
            if not self.realistic:
                logger.warning(W_NEEDSK6+"disabling `realistic` needs KiCad 6 or newer")

    def cli_stackup_colors(self):
        logger.debug("Looking for colors for the 3D render from the stack-up")
        colors = []
        # Apply global defaults
        # Board (core)
        if GS.global_pcb_material_color is not None:
            if GS.global_pcb_material_color[0] == '#':
                color = GS.global_pcb_material_color
            else:
                color = G_BOARDCOLORS.get(GS.global_pcb_material_color, '#6d744bd4')
        else:
            color = '#6d744bd4'
        logger.debug(f"- Core {GS.global_pcb_material_color} -> {color}")
        colors.append({'layer': 'board', 'color': color})
        # Solder mask
        name = GS.global_solder_mask_color_bottom or GS.global_solder_mask_color
        color = G_MASKCOLORS[name] if name and name.lower() in G_MASKCOLORS else G_MASKCOLORS['']
        colors.append({'layer': 'soldermask_bottom', 'color': color})
        logger.debug(f"- Solder mask bottom {name} -> {color}")
        name = GS.global_solder_mask_color_top or GS.global_solder_mask_color
        color = G_MASKCOLORS[name] if name and name.lower() in G_MASKCOLORS else G_MASKCOLORS['']
        colors.append({'layer': 'soldermask_top', 'color': color})
        logger.debug(f"- Solder mask top {name} -> {color}")
        # Silk screen
        name = GS.global_silk_screen_color_bottom or GS.global_silk_screen_color
        color = G_SILKCOLORS[name] if name and name.lower() in G_SILKCOLORS else G_SILKCOLORS['']
        colors.append({'layer': 'silkscreen_bottom', 'color': color})
        logger.debug(f"- Silk bottom top {name} -> {color}")
        name = GS.global_silk_screen_color_top or GS.global_silk_screen_color
        color = G_SILKCOLORS[name] if name and name.lower() in G_SILKCOLORS else G_SILKCOLORS['']
        colors.append({'layer': 'silkscreen_top', 'color': color})
        logger.debug(f"- Silk screen top {name} -> {color}")
        # PCB finish
        if GS.global_pcb_finish is not None:
            color_n = FINISH_TO_COLOR.get(GS.global_pcb_finish.lower(), 'copper')
        else:
            color_n = 'copper'
        color = G_FINISHCOLORS[color_n]
        colors.append({'layer': 'copper', 'color': color})
        colors.append({'layer': 'copper_bottom', 'color': color})
        logger.debug(f"- Copper {GS.global_pcb_finish} -> {color} ({color_n})")
        # Solder paste
        if GS.global_solder_paste_color is not None:
            if GS.global_solder_paste_color[0] == '#':
                color = GS.global_solder_paste_color
            else:
                color = G_PASTECOLORS.get(GS.global_solder_paste_color, '#808080ff')
        else:
            color = '#808080ff'
        colors.append({'layer': 'solderpaste', 'color': color})
        logger.debug(f"- Solder paste {GS.global_solder_paste_color} -> {color}")
        return colors

    def cli_gui_colors(self):
        colors = [{'layer': 'board', 'color': self.color_str_to_rgb(self.board)},
                  {'layer': 'copper', 'color': "rgb(200, 52, 52)"},
                  {'layer': 'copper_bottom', 'color': "rgb(77, 127, 196)"},
                  {'layer': 'silkscreen_top', 'color': "rgb(242, 237, 161)"},
                  {'layer': 'silkscreen_bottom', 'color': "rgb(232, 178, 167)"},
                  {'layer': 'soldermask_top', 'color': "rgba(216, 100, 255, 0.400)"},
                  {'layer': 'soldermask_bottom', 'color': "rgba(2, 255, 238, 0.400)"},
                  {'layer': 'solderpaste', 'color': "rgba(180, 160, 154, 0.902)"},
                  ]
        return colors

    def cli_user_colors(self):
        copper = self.color_str_to_rgb(self.copper)
        silk_top = silk_bottom = self.color_str_to_rgb(self.silk)  # TODO: split?
        solder_top = solder_bottom = self.color_str_to_rgb(self.solder_mask)  # TODO: split?
        solder_paste = self.color_str_to_rgb(self.solder_paste)
        colors = [{'layer': 'board', 'color': self.color_str_to_rgb(self.board)},
                  {'layer': 'copper', 'color': copper},
                  {'layer': 'copper_bottom', 'color': copper},  # TODO: split?
                  {'layer': 'silkscreen_top', 'color': silk_top},
                  {'layer': 'silkscreen_bottom', 'color': silk_bottom},
                  {'layer': 'soldermask_top', 'color': solder_top},
                  {'layer': 'soldermask_bottom', 'color': solder_bottom},
                  {'layer': 'solderpaste', 'color': solder_paste},
                  ]
        return colors

    def kicad_cli_cmd(self, command, output):
        view = self._rviews.get(self.view, self.view)
        if view == 'rear':
            view = 'back'
        rx = -(self.rotate_x if self.rotate_degrees else self.rotate_x*10)
        ry = -(self.rotate_y if self.rotate_degrees else self.rotate_y*10)
        rz = -(self.rotate_z if self.rotate_degrees else self.rotate_z*10)
        cmd = [command, 'pcb', 'render',
               '--output', output,
               # -D, --define-var  they come from set_text_variable, no need to define more
               '--width', str(self.width+16),
               '--height', str(self.height+16),
               '--side', view,
               '--background', 'transparent' if self.transparent_background else 'opaque',
               '--quality', 'high' if self.ray_tracing else 'basic',
               '--preset', '_kibot_preset',
               # '--use-board-stackup-colors' conditionally added
               # '--floor' enables options that are already enabled in "high" (ray trace)
               # '--perspective' conditionally added
               # '--zoom' added as Z in --pan
               '--pan', f"{self.move_x},{self.move_y},{self.zoom}",
               '--pivot', f"{self.pivot_x},{self.pivot_y},{self.pivot_z}",
               '--rotate', f"{rx},{ry},{rz}",
               # TODO: --light*
               ]
        # if self.force_stackup_colors:
        #     cmd.append('--use-board-stackup-colors')
        if not self.orthographic:
            cmd.append('--perspective')
        if GS.kicad_version_n >= KICAD_VERSION_10_0_3:
            self.add_kicad_cli_variant(cmd)

        # All the rest of the options are controlled by the preset
        cfg = os.path.join(GS.kicad_conf_path, '3d_viewer.json')
        if not os.path.isfile(cfg):
            old_cfg = {}
        else:
            with open(cfg, 'rt') as f:
                old_cfg = json.load(f)

        # Included layers
        # fp_text is needed for fp_references and fp_values
        # off_board_silk and drawings are not working
        # 3d_axes and bounding_boxes seems to be ignored
        # non_pos_file_models and dnp_models should be filter business
        layers = ['off_board_silk', 'fp_text']
        if self.show_references:
            layers.append('fp_references')
        if self.show_values:
            layers.append('fp_values')
        if self.show_copper_top:
            layers.append('copper')
        if self.show_copper_bottom:
            layers.append('copper_bottom')
        if self.show_plated_barrels:
            layers.append('plated_barrels')
        if not self.no_tht:
            layers.append('th_models')
        if not self.no_smd:
            layers.append('smd_models')
        if not self.no_virtual:
            layers.append('virtual_models')
        if self.show_silkscreen:
            layers.extend(['silkscreen_bottom', 'silkscreen_top'])
        if self.show_soldermask:
            layers.extend(['soldermask_bottom', 'soldermask_top'])
        if self.show_solderpaste:
            layers.append('solderpaste')
        if self.show_board_body:
            layers.append('board')
        if self.show_comments:
            layers.append('user_comments')
        if self.show_drawings:
            layers.append('user_drawings')
        if self.show_eco or self.show_eco1:
            layers.append('user_eco1')
        if self.show_eco or self.show_eco2:
            layers.append('user_eco2')
        if self.show_adhesive:
            layers.append('adhesive')

        # Colors
        if self.force_stackup_colors:
            colors = self.cli_stackup_colors()
        elif not self.realistic:
            colors = self.cli_gui_colors()
        else:
            colors = self.cli_user_colors()
        colors.extend([{"layer": "user_comments", "color": "rgb(217, 217, 217)"},
                       {"layer": "user_drawings", "color": "rgb(217, 217, 217)"},
                       {"layer": "user_eco1", "color": "rgb(179, 26, 26)"},
                       {"layer": "user_eco2", "color": "rgb(179, 26, 26)"},
                       {"layer": "background_bottom", "color": self.color_str_to_rgb(self.background1)},
                       {"layer": "background_top", "color": self.color_str_to_rgb(self.background2)}])

        # Preset
        preset = {'name': '_kibot_preset', 'layers': layers, 'colors': colors}

        # Add our preset
        if 'layer_presets' not in old_cfg:
            old_cfg['layer_presets'] = []
        new_presets = [p for p in old_cfg['layer_presets'] if p.get('name') != '_kibot_preset'] + [preset]
        old_cfg['layer_presets'] = new_presets
        # Save the new config
        with open(cfg, 'wt') as f:
            f.write(json.dumps(old_cfg, sort_keys=True, indent=2))

        return cmd

    def check_kicad_cli_bug(self):
        res = _run_command([GS.kicad_cli, 'pcb', 'render', '--help'])
        # KiCad 9.x and 10.0.0-3 has a bug that always forces --use-board-stackup-colors
        return re.search(r'--use-board-stackup-colors.*default:\s+false', res) is not None

    def run(self, output):
        super().run(output)
        logger.warning(W_DEPR+'This output depends on KiCad version, use `blender_export` instead')
        if GS.ki6 and GS.kicad_version_n < KICAD_VERSION_6_0_2:
            GS.exit_with_error("3D Viewer not supported for KiCad 6.0.0/1\n"
                               "Please upgrade KiCad to 6.0.2 or newer", MISSING_TOOL)
        use_cli = GS.ki10 and self.use_cli and self.check_kicad_cli_bug()
        command = GS.kicad_cli if use_cli else self.ensure_tool('KiAuto')
        if self.transparent_background and not use_cli:
            # Use the chroma key color
            self.background1 = self.background2 = self.transparent_background_color
            convert_command = self.ensure_tool('ImageMagick')
        elif self.auto_crop:
            # Avoid a gradient
            self.background2 = self.background1
            convert_command = self.ensure_tool('ImageMagick')

        # Base command with overwrite
        if use_cli:
            # Using kicad-cli
            cmd = self.kicad_cli_cmd(command, output)
        else:
            cmd = [command, '--rec_w', str(self.width+2), '--rec_h', str(self.height+85),
                   '3d_view', '--output_name', output]
            self.add_options(cmd)
        # The board
        self.apply_show_components()
        board_name = self.filter_components(highlight=set(self.expand_kf_components(self._highlight)))
        self.undo_show_components()
        cmd.append(board_name)
        if use_cli:
            _run_command(cmd)
            if self._files_to_remove:
                self.remove_temporals()
        else:
            cmd.append(os.path.dirname(output))
            # Execute it
            self.exec_with_retry(self.add_extra_options(cmd), RENDER_3D_ERR)
        if self.auto_crop:
            cmd = [convert_command, output, '-trim', '+repage']
            if self.enable_crop_workaround:
                cmd.extend(['-trim', '+repage'])
            cmd.append(output)
            _run_command(cmd)
        if self.transparent_background and not use_cli:
            _run_command([convert_command, output, '-fuzz', str(self.transparent_background_fuzz)+'%', '-transparent',
                          self.color_str_to_rgb(self.transparent_background_color), output])


@output_class
class Render_3D(Base3D):  # noqa: F821
    """ 3D render of the PCB
        Exports the image generated by KiCad's 3D viewer. *Deprecated*
        Use the Blender Export output if you want something with better quality
        and less dependent of the KiCad version """
    def __init__(self):
        super().__init__()
        with document:
            self.options = Render3DOptions
            """ *[dict={}] Options for the `render_3d` output """
        self._category = 'PCB/3D'

    def get_renderer_options(self):
        """ Where are the options for this output when used as a 'renderer' """
        return self.options

    @staticmethod
    def get_conf_examples(name, layers):
        outs = []
        has_top = False
        has_bottom = False
        for la in layers:
            if la.is_top() or la.layer.startswith('F.'):
                has_top = True
            elif la.is_bottom() or la.layer.startswith('B.'):
                has_bottom = True
        if has_top:
            gb = {}
            gb['name'] = 'basic_{}_top'.format(name)
            gb['comment'] = '3D view from top'
            gb['type'] = name
            gb['dir'] = '3D'
            gb['options'] = {'ray_tracing': True, 'orthographic': True}
            outs.append(gb)
            if GS.ki6:
                gb = {}
                gb['name'] = 'basic_{}_30deg'.format(name)
                gb['comment'] = '3D view from 30 degrees'
                gb['type'] = name
                gb['dir'] = '3D'
                gb['output_id'] = '30deg'
                gb['options'] = {'ray_tracing': True, 'rotate_x': 3, 'rotate_z': -2}
                outs.append(gb)
        if has_bottom:
            gb = {}
            gb['name'] = 'basic_{}_bottom'.format(name)
            gb['comment'] = '3D view from bottom'
            gb['type'] = name
            gb['dir'] = '3D'
            gb['options'] = {'ray_tracing': True, 'orthographic': True, 'view': 'bottom'}
            outs.append(gb)
        return outs
