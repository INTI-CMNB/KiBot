# -*- coding: utf-8 -*-
# Copyright (c) 2022-2024 Salvador E. Tropea
# Copyright (c) 2022-2024 Instituto Nacional de Tecnología Industrial
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)
"""
Dependencies:
  - from: KiKit
    role: mandatory
    version: 1.5.1
"""
import collections
from copy import deepcopy
import os
import re
import json
from .error import KiPlotConfigurationError
from .gs import GS
from .kiplot import run_command, config_output, register_xmp_import
from .layer import Layer
from .misc import W_PANELEMPTY, KIKIT_UNIT_ALIASES, W_KEEPTMP
from .optionable import PanelOptions, Optionable
from .out_base import VariantOptions
from .registrable import RegOutput
from .macros import macros, document, output_class  # noqa: F401
from . import log

logger = log.get_logger()


def update_dict(d, u):
    for k, v in u.items():
        if isinstance(v, collections.abc.Mapping):
            d[k] = update_dict(d.get(k, {}), v)
        elif isinstance(v, list) and k in d:
            d[k] = v+d[k]
        else:
            d[k] = v
    return d


class PanelOptionsWithPlugin(PanelOptions):
    def __init__(self):
        with document:
            self.code = ''
            """ Plugin specification (PACKAGE.FUNCTION or PYTHON_FILE.FUNCTION). Used for *plugin* """
            self.arg = ''
            """ Argument to pass to the plugin. Used for *plugin* """
        super().__init__()


class PanelizePage(PanelOptions):
    def __init__(self):
        with document:
            self.type = 'inherit'
            """ *[inherit,custom,A0,A1,A2,A3,A4,A5,A,B,C,D,E,USLetter,USLegal,USLedger,A0-portrait,A1-portrait,A2-portrait,
                 A3-portrait,A4-portrait,A5-portrait,A-portrait,B-portrait,C-portrait,D-portrait,E-portrait,
                 USLetter-portrait,USLegal-portrait,USLedger-portrait] Paper size. The default `inherit` option inherits
                 paper size from the source board. This feature is not supported on KiCAD 5 """
            self.page_size = None
            """ {type} """
            self.size = None
            """ {type} """
            self.anchor = 'mt'
            """ [tl,tr,bl,br,mt,mb,ml,mr,c] Point of the panel to be placed at given position. Can be one of tl, tr, bl, br
                (corners), mt, mb, ml, mr (middle of sides), c (center). The anchors refer to the panel outline """
            self.posx = '50%'
            """ [number|string='50%'] The X position of the panel on the page. Can be expressed as a page size percentage """
            self.pos_x = None
            """ {posx} """
            self.posy = 20
            """ [number|string=20] The Y position of the panel on the page. Can be expressed as a page size percentage """
            self.pos_y = None
            """ {posy} """
            self.width = 297
            """ [number|string=297] Width for the `custom` paper size """
            self.height = 210
            """ [number|string=210] Height for the `custom` paper size """
        super().__init__()

    def config(self, parent):
        super().config(parent)
        self.add_units(('posx', 'posy'), percent=True)
        self.add_units(('width', 'height'))


class PanelizeLayout(PanelOptionsWithPlugin):
    def __init__(self):
        with document:
            self.type = 'grid'
            """ [grid,plugin] In the plugin type only `code` and `arg` are relevant """
            self.hspace = 0
            """ [number|string=0] Specify the horizontal gap between the boards """
            self.vspace = 0
            """ [number|string=0] Specify the vertical gap between the boards """
            self.space = 0
            """ [number|string=0] Specify the gap between the boards, overwrites `hspace` and `vspace` """
            self.rotation = 0
            """ [number|string=0] Rotate the boards before placing them in the panel """
            self.renamenet = 'Board_{n}-{orig}'
            """ A pattern by which to rename the nets. You can use {n} and {orig} to get the board number and original name """
            self.rename_net = None
            """ {renamenet} """
            self.renameref = '{orig}'
            """ A pattern by which to rename the references. You can use {n} and {orig} to get the board number and original
                name """
            self.rename_ref = None
            """ {renameref} """
            self.baketext = True
            """ A flag that indicates if text variables should be substituted or not """
            self.bake_text = None
            """ {baketext} """
            self.rows = 1
            """ *Specify the number of rows of boards in the grid pattern """
            self.cols = 1
            """ *Specify the number of columns of boards in the grid pattern """
            self.alternation = 'none'
            """ [none,rows,cols,rowsCols] Specify alternations of board rotation.
                none: Do not alternate.
                rows: Rotate boards by 180° on every next row.
                cols: Rotate boards by 180° on every next column.
                rowsCols: Rotate boards by 180° based on a chessboard pattern """
            self.vbackbone = 0
            """ [number|string=0] The width of vertical backbone (0 means no backbone). The backbone does not increase the
                spacing of the boards """
            self.v_back_bone = None
            """ {vbackbone} """
            self.hbackbone = 0
            """ [number|string=0] The width of horizontal backbone (0 means no backbone). The backbone does not increase the
                spacing of the boards """
            self.h_back_bone = None
            """ {hbackbone} """
            self.vboneskip = 0
            """ Skip every n vertical backbones. I.e., 1 means place only every other backbone """
            self.v_bone_skip = None
            """ {vboneskip} """
            self.hboneskip = 0
            """ Skip every n horizontal backbones. I.e., 1 means place only every other backbone """
            self.h_bone_skip = None
            """ {hboneskip} """
            self.vbonecut = True
            """ If there are both backbones specified, specifies if there should be a vertical cut where the backbones
                cross """
            self.v_bone_cut = None
            """ {vbonecut} """
            self.hbonecut = True
            """ If there are both backbones specified, specifies if there should be a horizontal cut where the backbones
                cross """
            self.h_bone_cut = None
            """ {hbonecut} """
            self.vbonefirst = 0
            """ Specify first vertical backbone to render """
            self.v_bone_first = None
            """ {vbonefirst} """
            self.hbonefirst = 0
            """ Specify first horizontal backbone to render """
            self.h_bone_first = None
            """ {hbonefirst} """
        super().__init__()

    def config(self, parent):
        super().config(parent)
        if self.get_user_defined('space'):
            self.hspace = self.vspace = self.space
        self.add_units(('vbackbone', 'hbackbone', 'hspace', 'vspace', 'space'))
        self.add_angle(('rotation', ))


class PanelizeTabs(PanelOptionsWithPlugin):
    def __init__(self):
        with document:
            self.type = 'spacing'
            """ *[fixed,spacing,full,annotation,plugin] Fixed: Place given number of tabs on the PCB edge.
                Spacing: Place tabs on the PCB edges based on spacing.
                Full: Create tabs that are full width of the PCB.
                Corner: Create tabs in the corners of the PCB.
                Annotation: Add tabs based on PCB annotations.
                Plugin: Uses an external python function, only `code` and `arg` are relevant """
            self.vwidth = 3
            """ [number|string=3] The width of tabs in the vertical direction. Used for *fixed* and *spacing* """
            self.hwidth = 3
            """ [number|string=3] The width of tabs in the horizontal direction. Used for *fixed* and *spacing* """
            self.width = 3
            """ [number|string=3] The width of tabs in both directions. Overrides both `vwidth` and `hwidth`.
                Used for *fixed*, *spacing*, *corner* and *annotation* """
            self.vcount = 1
            """ Number of tabs in the vertical direction. Used for *fixed* """
            self.hcount = 1
            """ Number of tabs in the horizontal direction. Used for *fixed* """
            self.mindistance = 0
            """ [number|string=0] Minimal spacing between the tabs. If there are too many tabs, their count is reduced.
                Used for *fixed* """
            self.min_distance = None
            """ {mindistance} """
            self.spacing = 10
            """ [number|string=10] The maximum spacing of the tabs. Used for *spacing* """
            self.cutout = 1
            """ [number|string=1] When your design features open pockets on the side, this parameter specifies extra cutout
                depth in order to ensure that a sharp corner of the pocket can be milled. Used for *full* """
            self.patchcorners = True
            """ The full tabs are appended to the nearest flat face of the PCB. If the PCB has sharp corners, you want to
                add patches of substrate to these corners. However, if the PCB has fillet or miter, you don't want to
                apply the patches """
            self.patch_corners = None
            """ {patchcorners} """
            self.tabfootprints = 'kikit:Tab'
            """ The footprint/s used for the *annotation* type. You can specify a list of footprints separated by comma """
            self.tab_footprints = None
            """ {tabfootprints} """
        super().__init__()

    def config(self, parent):
        super().config(parent)
        if self.get_user_defined('width'):
            self.vwidth = self.hwidth = self.width
        self.add_units(('vwidth', 'hwidth', 'width', 'mindistance', 'spacing', 'cutout'))


class PanelizeCuts(PanelOptionsWithPlugin):
    def __init__(self):
        with document:
            self.type = 'none'
            """ *[none,mousebites,vcuts,layer,plugin] Layer: When KiKit reports it cannot perform cuts, you can render the cuts
                into a layer with this option to understand what's going on. Shouldn't be used for the final design """
            self.drill = 0.5
            """ [number|string=0.5] Drill size used for the *mousebites* """
            self.spacing = 0.8
            """ [number|string=0.8] The spacing of the holes used for the *mousebites* """
            self.offset = 0
            """ [number|string=0] Specify the *mousebites* and *vcuts* offset, positive offset puts the cuts into the board,
                negative puts the cuts into the tabs """
            self.prolong = 0
            """ [number|string=0] Distance for tangential prolongation of the cuts (to cut through the internal corner fillets
                caused by milling). Used for *mousebites* and *layer* """
            self.clearance = 0
            """ [number|string=0] Specify clearance for copper around V-cuts """
            self.cutcurves = False
            """ Specify if curves should be approximated by straight cuts (e.g., for cutting tabs on circular boards).
                Used for *vcuts* """
            self.cut_curves = None
            """ {cutcurves} """
            self.linewidth = 0.3
            """ [number|string=0.3] Line width to plot cuts with """
            self.line_width = None
            """ {linewidth} """
            self.textthickness = 0.3
            """ [number|string=0.3] Text thickness for width """
            self.text_thickness = None
            """ {textthickness} """
            self.textsize = 2
            """ [number|string] Text size for vcuts """
            self.text_size = None
            """ {textsize} """
            self.endprolongation = 3
            """ [number|string=3] Prolongation on the end of V-CUT without text """
            self.end_prolongation = None
            """ {endprolongation} """
            self.textprolongation = 3
            """ [number|string=3] Prolongation of the text size of V-CUT """
            self.text_prolongation = None
            """ {textprolongation} """
            self.textoffset = 3
            """ [number|string=3] Text offset from the V-CUT """
            self.text_offset = None
            """ {textoffset} """
            self.template = 'V-CUT'
            """ Text template for the V-CUT """
            self.layer = 'Cmts.User'
            """ Specify the layer to render V-cuts on. Also used for the *layer* type """
        super().__init__()

    def config(self, parent):
        super().config(parent)
        self.add_units(('drill', 'spacing', 'offset', 'prolong', 'clearance', 'linewidth', 'textthickness', 'textsize',
                        'endprolongation', 'textprolongation', 'textoffset'))
        res = Layer.solve(self.layer)
        if len(res) > 1:
            raise KiPlotConfigurationError('Must select only one layer for the V-cuts ({})'.format(self.layer))


class PanelizeFraming(PanelOptionsWithPlugin):
    def __init__(self):
        with document:
            self.type = 'none'
            """ *[none,railstb,railslr,frame,tightframe,plugin] Railstb: Add rails on top and bottom.
            Railslr: Add rails on left and right.
            Frame: Add a frame around the board.
            Tighframe: Add a frame around the board which fills the whole area of the panel -
            the boards have just a milled slot around their perimeter.
            Plugin: Uses an external python function, only `code` and `arg` are relevant """
            self.hspace = 2
            """ [number|string=2] Specify the horizontal space between PCB and the frame/rail """
            self.vspace = 2
            """ [number|string=2] Specify the vertical space between PCB and the frame/rail """
            self.space = 2
            """ [number|string=2] Specify the space between PCB and the frame/rail. Overrides `hspace` and `vspace` """
            self.width = 5
            """ [number|string=5] Specify with of the rails or frame """
            self.fillet = 0
            """ [number|string=0] Specify radius of fillet frame corners """
            self.chamfer = 0
            """ [number|string=0] Specify the size of chamfer frame corners. You can also separately specify `chamferwidth`
                and `chamferheight` to create a non 45 degrees chamfer """
            self.chamferwidth = 0
            """ [number|string] Width of the chamfer frame corners, used for non 45 degrees chamfer """
            self.chamfer_width = None
            """ {chamferwidth} """
            self.chamferheight = 0
            """ [number|string=0] Height of the chamfer frame corners, used for non 45 degrees chamfer """
            self.chamfer_height = None
            """ {chamferheight} """
            self.mintotalheight = 0
            """ [number|string=0] If needed, add extra material to the rail or frame to meet the minimal requested size.
                Useful for services that require minimal panel size """
            self.min_total_height = None
            """ {mintotalheight} """
            self.mintotalwidth = 0
            """ [number|string=0] If needed, add extra material to the rail or frame to meet the minimal requested size.
                Useful for services that require minimal panel size """
            self.min_total_width = None
            """ {mintotalwidth} """
            self.maxtotalheight = 10000
            """ [number|string=10000] Maximal height of the panel """
            self.max_total_height = None
            """ {maxtotalheight} """
            self.maxtotalwidth = 10000
            """ [number|string=10000] Maximal width of the panel """
            self.max_total_width = None
            """ {maxtotalwidth} """
            self.cuts = 'both'
            """ [none,both,v,h] Specify whether to add cuts to the corners of the frame for easy removal.
                Used for *frame* """
            self.slotwidth = 2
            """ [number|string=2] Width of the milled slot for *tightframe* """
            self.slot_width = None
            """ {slotwidth} """
        super().__init__()

    def config(self, parent):
        super().config(parent)
        if self.get_user_defined('space'):
            self.hspace = self.vspace = self.space
        self.add_units(('hspace', 'vspace', 'space', 'width', 'fillet', 'chamfer', 'mintotalwidth', 'mintotalheight',
                        'slotwidth', 'chamferwidth', 'chamferheight'))


class PanelizeTooling(PanelOptionsWithPlugin):
    def __init__(self):
        with document:
            self.type = 'none'
            """ *[none,3hole,4hole,plugin] Add none, 3 or 4 holes to the (rail/frame of) the panel """
            self.hoffset = 0
            """ [number|string=0] Horizontal offset from panel edges """
            self.voffset = 0
            """ [number|string=0] Vertical offset from panel edges """
            self.size = 1.152
            """ [number|string=1.152] Diameter of the holes """
            self.paste = False
            """ If True, the holes are included in the paste layer (therefore they appear on the stencil) """
            self.soldermaskmargin = 0
            """ [number|string=0] Solder mask expansion/margin. Use 1.3mm for JLCPCB """
            self.solder_mask_margin = None
            """ {soldermaskmargin} """
        super().__init__()

    def config(self, parent):
        super().config(parent)
        self.add_units(('hoffset', 'voffset', 'size', 'soldermaskmargin'))


class PanelizeFiducials(PanelOptions):
    def __init__(self):
        with document:
            self.type = 'none'
            """ *[none,3fid,4fid,plugin] Add none, 3 or 4 fiducials to the (rail/frame of) the panel """
            self.hoffset = 0
            """ [number|string=0] Horizontal offset from panel edges """
            self.voffset = 0
            """ [number|string=0] Vertical offset from panel edges """
            self.coppersize = 1
            """ [number|string=1] Diameter of the copper spot """
            self.copper_size = None
            """ {coppersize} """
            self.opening = 1
            """ [number|string=1] Diameter of the solder mask opening """
            self.paste = False
            """ Include the fiducials in the paste layer (therefore they appear on the stencil) """
            self.code = ''
            """ Plugin specification (PACKAGE.FUNCTION or PYTHON_FILE.FUNCTION). Used for *plugin* """
            self.arg = ''
            """ Argument to pass to the plugin. Used for *plugin* """
        super().__init__()

    def config(self, parent):
        super().config(parent)
        self.add_units(('hoffset', 'voffset', 'coppersize', 'opening'))


class PanelizeText(PanelOptions):
    def __init__(self):
        with document:
            self.type = 'none'
            """ *[none,simple] Currently fixed. BTW: don't ask me about this ridiculous default, is how KiKit works """
            self.text = ''
            """ *The text to be displayed. Note that you can escape ; via \\.
                Available variables in text: *date* formats current date as <year>-<month>-<day>,
                *time24* formats current time in 24-hour format,
                *boardTitle* the title from the source board,
                *boardDate* the date from the source board,
                *boardRevision* the revision from the source board,
                *boardCompany* the company from the source board,
                *boardComment1*-*boardComment9* comments from the source board """
            self.anchor = 'mt'
            """ [tl,tr,bl,br,mt,mb,ml,mr,c] Origin of the text. Can be one of tl, tr, bl, br (corners), mt, mb, ml, mr
                (middle of sides), c (center). The anchors refer to the panel outline """
            self.hoffset = 0
            """ [number|string=0] Specify the horizontal offset from anchor. Respects KiCAD coordinate system """
            self.voffset = 0
            """ [number|string=0] Specify the vertical offset from anchor. Respects KiCAD coordinate system """
            self.orientation = 0
            """ [number|string=0] Specify the orientation (angle) """
            self.width = 1.5
            """ [number|string=1.5] Width of the characters (the same parameters as KiCAD uses) """
            self.height = 1.5
            """ [number|string=1.5] Height of the characters (the same parameters as KiCAD uses) """
            self.hjustify = 'center'
            """ [left,right,center] Horizontal justification of the text """
            self.vjustify = 'center'
            """ [top,bottom,center] Vertical justification of the text """
            self.thickness = 0.3
            """ [number|string=0.3] Stroke thickness """
            self.layer = 'F.SilkS'
            """ Specify text layer """
            self.plugin = ''
            """ Specify the plugin that provides extra variables for the text """
        super().__init__()

    def config(self, parent):
        super().config(parent)
        self.add_units(('hoffset', 'voffset', 'width', 'height', 'thickness'))
        self.add_angle(('orientation', ))
        res = Layer.solve(self.layer)
        if len(res) > 1:
            raise KiPlotConfigurationError('Must select only one layer for the text ({})'.format(self.layer))
        if parent.expand_text:
            self.text = parent.expand_filename_both(self.text, is_sch=False, make_safe=False)


class PanelizeCopperfill(PanelOptions):
    def __init__(self):
        with document:
            self.type = 'none'
            """ *[none,solid,hatched,hex] How to fill non-board areas of the panel with copper """
            self.clearance = 0.5
            """ [number|string=0.5] Extra clearance from the board perimeters. Suitable for, e.g., not filling the tabs with
                copper """
            self.edgeclearance = 0.5
            """ [number|string=0.5] Specifies clearance between the fill and panel perimeter """
            self.edge_clearance = None
            """ {edgeclearance} """
            self.layers = Optionable
            """ [string|list(string)='F.Cu,B.Cu'] {comma_sep} List of layers to fill. Can be a comma-separated string.
                Using *all* means all external copper layers """
            self.width = 1
            """ [number|string=1] The width of the hatched strokes """
            self.spacing = 1
            """ [number|string=1] The space between the hatched strokes or hexagons """
            self.orientation = 45
            """ [number|string=45] The orientation of the hatched strokes """
            self.diameter = 7
            """ [number|string=7] Diameter of hexagons """
            self.threshold = 15
            """ Remove fragments smaller than threshold. Expressed as a percentage """
        super().__init__()

    def config(self, parent):
        super().config(parent)
        self.add_units(('width', 'spacing', 'clearance', 'edgeclearance', 'diameter'))
        self.add_angle(('orientation', ))
        self.threshold = str(self.threshold)+'%'
        if len(self.layers) == 1 and self.layers[0] == 'all':
            self.layers = 'all'
        else:
            res = Layer.solve(self.layers)
            self.layers = ','.join([la.layer for la in res])


class PanelizePost(PanelOptions):
    def __init__(self):
        with document:
            self.type = 'auto'
            """ [auto] Currently fixed """
            self.copperfill = False
            """ Fill tabs and frame with copper (e.g., to save etchant or to increase rigidity of flex-PCB panels) """
            self.millradius = 0
            """ [number|string=0] Simulate the milling operation (add fillets to the internal corners).
                Specify mill radius (usually 1 mm). 0 radius disables the functionality """
            self.mill_radius = None
            """ {millradius} """
            self.millradiusouter = 0
            """ [number|string=0] Like `millradius`, but modifies only board outer counter.
                No internal features of the board are affected """
            self.mill_radius_outer = None
            """ {millradiusouter} """
            self.reconstructarcs = False
            """ The panelization process works on top of a polygonal representation of the board.
                This options allows to reconstruct the arcs in the design before saving the panel """
            self.reconstruct_arcs = None
            """ {reconstructarcs} """
            self.refillzones = False
            """ Refill the user zones after the panel is build.
                This is only necessary when you want your zones to avoid cuts in panel """
            self.refill_zones = None
            """ {refillzones} """
            self.script = ''
            """ A path to custom Python file. The file should contain a function kikitPostprocess(panel, args) that
                receives the prepared panel as the kikit.panelize.Panel object and the user-supplied arguments as a
                string - see `scriptarg`. The function can make arbitrary changes to the panel - you can append text,
                footprints, alter labels, etc. The function is invoked after the whole panel is constructed
                (including all other postprocessing). If you try to add a functionality for a common fabrication
                houses via scripting, consider submitting PR for KiKit """
            self.scriptarg = ''
            """ An arbitrary string passed to the user post-processing script specified in script """
            self.script_arg = None
            """ {scriptarg} """
            self.origin = 'tl'
            """ [tl,tr,bl,br,mt,mb,ml,mr,c] Specify if the auxiliary origin and grid origin should be replaced.
                Can be one of tl, tr, bl, br (corners), mt, mb, ml, mr (middle of sides), c (center).
                Empty string does not changes the origin """
            self.dimensions = False
            """ Draw dimensions with the panel size. """
            self.edgewidth = 0.1
            """ [number|string=0.1] Specify line width for the Edge.Cuts of the panel """
            self.edge_width = None
            """ {edgewidth} """
        super().__init__()

    def config(self, parent):
        super().config(parent)
        self.add_units(('millradius', 'edgewidth', 'millradiusouter'))


class PanelizeDebug(PanelOptions):
    def __init__(self):
        with document:
            self.drawPartitionLines = False
            """ Draw partition lines """
            self.drawBackboneLines = False
            """ Draw backbone lines """
            self.drawboxes = False
            """ Draw boxes """
            self.trace = False
            """ Trace """
            self.deterministic = False
            """ Deterministic """
            self.drawtabfail = False
            """ Draw tab fail """
        super().__init__()


class PanelizeSource(PanelOptions):
    def __init__(self):
        with document:
            self.type = 'auto'
            """ *[auto,rectangle,annotation] How we select the area of the PCB used for the panelization.
                *auto* uses all the area reported by KiCad, *rectangle* a specified rectangle and
                *annotation* selects a contour marked by a kikit:Board footprint """
            self.stack = 'inherit'
            """ [inherit,2layer,4layer,6layer] Used to reduce the number of layers used for the panel """
            self.tolerance = 1
            """ [number|string=1] Extra space around the PCB reported size to be included. Used for *auto* and *annotation* """
            self.tlx = 0
            """ [number|string=0] Top left X coordinate of the rectangle used. Used for *rectangle* """
            self.tly = 0
            """ [number|string=0] Top left Y coordinate of the rectangle used. Used for *rectangle* """
            self.brx = 0
            """ [number|string=0] Bottom right X coordinate of the rectangle used. Used for *rectangle* """
            self.bry = 0
            """ [number|string=0] Bottom right Y coordinate of the rectangle used. Used for *rectangle* """
            self.ref = ''
            """ Reference for the kikit:Board footprint used to select the contour. Used for *annotation* """
        super().__init__()

    def config(self, parent):
        super().config(parent)
        self.add_units(('tolerance', 'tlx', 'tly', 'brx', 'bry'))


class PanelizeConfig(PanelOptions):
    def __init__(self):
        with document:
            self.name = ''
            """ A name to identify this configuration. If empty will be the order in the list, starting with 1.
                Don't use just a number or it will be confused as an index """
            self.extends = ''
            """ A configuration to use as base for this one. Use the following format: `OUTPUT_NAME[CFG_NAME]` """
            self.page = PanelizePage
            """ *[dict=null] Sets page size on the resulting panel and position the panel in the page """
            self.layout = PanelizeLayout
            """ *[dict=null] Layout used for the panel """
            self.tabs = PanelizeTabs
            """ *[dict=null] Style of the tabs used to join the PCB copies """
            self.cuts = PanelizeCuts
            """ *[dict=null] Specify how to perform the cuts on the tabs separating the board """
            self.framing = PanelizeFraming
            """ *[dict=null] Specify the frame around the boards """
            self.tooling = PanelizeTooling
            """ *[dict=null] Used to add tooling holes to the (rail/frame of) the panel """
            self.fiducials = PanelizeFiducials
            """ *[dict=null] Used to add fiducial marks to the (rail/frame of) the panel """
            self.text = PanelizeText
            """ [dict=null] Used to add text to the panel """
            self.text2 = PanelizeText
            """ [dict=null] Used to add text to the panel """
            self.text3 = PanelizeText
            """ [dict=null] Used to add text to the panel """
            self.text4 = PanelizeText
            """ [dict=null] Used to add text to the panel """
            self.copperfill = PanelizeCopperfill
            """ [dict=null] Fill non-board areas of the panel with copper """
            self.post = PanelizePost
            """ [dict=null] Finishing touches to the panel """
            self.debug = PanelizeDebug
            """ [dict=null] Debug options """
            self.source = PanelizeSource
            """ [dict=null] Used to adjust details of which part of the PCB is panelized """
            self.expand_text = True
            """ Expand text variables and KiBot %X markers in text objects """
        super().__init__()

    def config(self, parent):
        super().config(parent)
        # Avoid confusing names
        name_is_number = True
        try:
            _ = int(self.name)
        except ValueError:
            name_is_number = False
        if name_is_number:
            raise KiPlotConfigurationError("Don't use a number as name, this can be confused with an index ({})".
                                           format(self.name))

    def __str__(self):
        txt = f'`{self.name}`'
        if self.extends:
            txt += f' (extends: {self.extends})'
        return txt


class PanelizeOptions(VariantOptions):
    _extends_regex = re.compile(r'(.+)\[(.+)\]')

    def __init__(self):
        with document:
            self.output = GS.def_global_output
            """ *Filename for the output (%i=panel, %x=kicad_pcb) """
            self.configs = PanelizeConfig
            """ *[list(dict)|list(string)|string=[]] One or more configurations used to create the panel.
                Use a string to include an external configuration, i.e. `myDefault.json`.
                You can also include a preset using `:name`, i.e. `:vcuts`.
                Use a dict to specify the options using the KiBot YAML file """
            self.title = ''
            """ Text used to replace the sheet title. %VALUE expansions are allowed.
                If it starts with `+` the text is concatenated """
            self.units = 'mm'
            """ [millimeters,inches,mils,mm,cm,dm,m,mil,inch,in] Units used when omitted """
            self.default_angles = 'deg'
            """ [deg,°,rad] Angles used when omitted """
            self.create_preview = False
            """ Use PcbDraw to create a preview of the panel """
            self.copy_vias_on_mask = 'auto'
            """ [auto,yes,no] Copy the GUI option to plot vias on the mask layers from the original PCB to
                the panel. |br|
                This option is a workaround to KiCad 8 not allowing to choose to plot (or not to plot) vias
                on the mask layers using the Python API. So you have to set it in the GUI, but this option
                is lost during panelization. |br|
                Setting this option to *auto* will copy the value for faulty KiCad 8 versions, but won't
                waste time for working KiCad versions """
        super().__init__()
        self._expand_id = 'panel'
        self._expand_ext = 'kicad_pcb'

    def solve_cfg_name(self, cfg):
        """ Find the name of a configuration that isn't yet configured """
        name = cfg.get('name')
        if name:
            return name
        return str(self._tree['configs'].index(cfg)+1)

    def solve_extends(self, tree, level=0, used=None, our_name=None):
        base = tree.get('extends')
        if our_name is None:
            our_name = '{}[{}]'.format(self._parent.name, self.solve_cfg_name(tree))
        if used is None:
            used = {our_name}
        else:
            if our_name in used:
                raise KiPlotConfigurationError('Recursive extends detected in `extends: {}` ({})'.format(base, used))
            used.add(our_name)
        logger.debugl(1, "Extending from "+base)
        # Should be an string
        if not isinstance(base, str):
            raise KiPlotConfigurationError('`extends` must be a string, not {}'.format(type(base)))
        # Extract the output and config names
        m = PanelizeOptions._extends_regex.match(base)
        if m is None:
            raise KiPlotConfigurationError('Malformed `extends` reference: `{}` use OUTPUT_NAME[CFG_NAME]'.format(base))
        out_name, cfg_name = m.groups()
        # Look for the output
        out = RegOutput.get_output(out_name)
        if out is None:
            raise KiPlotConfigurationError('Unknown output `{}` in `extends: {}`'.format(out_name, base))
        # Look for the config
        configs = None
        out_options = out._tree.get('options')
        if out_options:
            configs = out_options.get('configs')
        if configs is None or isinstance(configs, str):
            raise KiPlotConfigurationError("Using `extends: {}` but `{}` hasn't configs to copy". format(base, out_name))
        cfg_name_is_number = True
        try:
            id = int(cfg_name)-1
        except ValueError:
            cfg_name_is_number = False
        if cfg_name_is_number:
            # Using an index, is it valid?
            if id >= len(configs):
                raise KiPlotConfigurationError('Using `extends: {}` but `{}` has {} configs'.
                                               format(base, out_name, len(configs)))
            origin = configs[id]
        else:
            # Using a name
            origin = next(filter(lambda x: 'name' in x and x['name'] == cfg_name, configs), None)
            if origin is None:
                raise KiPlotConfigurationError("Using `extends: {}` but `{}` doesn't define `{}`".
                                               format(base, out_name, cfg_name))
        # Now we have the origin
        # Does it also use extends?
        origin_extends = origin.get('extends')
        if origin_extends:
            origin = self.solve_extends(origin, level=level+1, used=used, our_name=base)
        # Copy the origin, update it and replace the current values
        logger.debugl(1, "{} before applying {}: {}".format(our_name, base, tree))
        logger.debugl(1, "- Should add {}".format(origin))
        new_origin = deepcopy(origin)
        update_dict(new_origin, tree)
        if level:
            tree = deepcopy(tree)
        update_dict(tree, new_origin)
        if not level:
            # Remove the extends, we solved it
            del tree['extends']
        logger.debugl(1, "After apply: {}".format(tree))
        return tree

    def config(self, parent):
        self._parent = parent
        # Look for configs that uses extends
        configs = self._tree.get('configs')
        if configs:
            list(map(self.solve_extends, filter(lambda x: 'extends' in x, configs)))
        super().config(parent)
        self.units = KIKIT_UNIT_ALIASES.get(self.units, self.units)
        if isinstance(self.configs, str):
            self.configs = [self.configs]
        for c, cfg in enumerate(self.configs):
            if isinstance(cfg, str):
                continue
            if not cfg.name:
                cfg.name = str(c+1)

    def create_config(self, cfg):
        cfg_d = {}
        for k, v in cfg.get_attrs_gen():
            if isinstance(v, PanelOptions):
                cfg_d[k] = {ky: va for ky, va in v.get_attrs_gen() if va is not None and v.get_user_defined(ky)}
        js = json.dumps(cfg_d, indent=4)
        logger.debugl(1, js)
        return GS.tmp_file(content=js, suffix='.json', prefix='panel_cfg', what='panel config', a_logger=logger)

    def do_copy_vias_on_mask(self, old, new):
        """ KiCad 8 has a bug that prevents choosing if vias are or aren't plotted in the solder mask layer.
            Only the setting in the PCB file is used, the API is ignored.
            KiKit resets this option, most probably unintentionally.
            So here we read the old PCB and we see if the new one needs to be updated. """
        logger.debug('Copying viasonmask option')
        if not os.path.isfile(new):
            logger.debug(f'Skipped because the output is missing ({new})')
            return
        # Read the old setting
        logger.debug('- Reading the old PCB')
        with open(old) as f:
            old_pcb = f.read()
        pattern = re.compile(r'\(viasonmask (.*)\)')
        match = pattern.search(old_pcb)
        if not match:
            logger.debug("- The old PCB doesn't have the option!")
            return
        old_value = match.group(1)
        logger.debug('- Reading the new PCB')
        with open(new) as f:
            new_pcb = f.read()
        match = pattern.search(new_pcb)
        if not match:
            logger.debug("- The new PCB doesn't have the option!")
            return
        new_value = match.group(1)
        if old_value == new_value:
            logger.debug(f'- No need to change (both {new_value})')
            return
        new_pcb = new_pcb.replace('(viasonmask '+new_value, '(viasonmask '+old_value)
        logger.debug(f'- Saving the panel PCB with `{old_value}`')
        with open(new, 'w') as f:
            f.write(new_pcb)

    def create_preview_file(self, name):
        if not self.create_preview or not os.path.isfile(name):
            return
        img_name = os.path.splitext(name)[0]+'.png'
        tree = {'name': '_temporal_pcbdraw_preview',
                'type': 'pcbdraw',
                'comment': 'Internally created for panel preview',
                'options': {'output': img_name, 'variant': '', 'format': 'png'}}
        out = RegOutput.get_class_for('pcbdraw')()
        out.set_tree(tree)
        config_output(out)
        logger.debug('Loading PCB panel ...')
        board = GS.load_board_low_level(name)
        logger.debug('Creating preview image ...')
        out.options.create_image(img_name, board)
        # KiCad loads the project automagically, so now we have the wrong project loaded
        # We need to unload the current project to load the new one
        # But we also need to reload the PCB, this is ridiculous ...
        GS.reload_project(GS.pro_file)

    def run(self, output):
        cmd_kikit, version = self.ensure_tool_get_ver('KiKit')
        if GS.ki5 and version >= (1, 1, 0):
            raise KiPlotConfigurationError("Installed KiKit doesn't support KiCad 5")
        if not self.get_user_defined('configs'):
            logger.warning(W_PANELEMPTY+'Generating a panel with default options, not very useful')
        super().run(output)
        fname = self.save_tmp_board_if_variant(new_title=self.title, do_3D=True)
        # Create the command
        cmd = [cmd_kikit, 'panelize']  # , '--dump', 'test.json'
        # Add all the configurations
        for cfg in self.configs:
            cmd.append('--preset')
            if isinstance(cfg, str):
                if cfg[0] != ':' and not os.path.isfile(cfg):
                    raise KiPlotConfigurationError('Missing config file: '+cfg)
                cmd.append(cfg)
            else:
                cfg_f = self.create_config(cfg)
                self._files_to_remove.append(cfg_f)
                cmd.append(cfg_f)
        # Add the PCB and output
        cmd.append(fname)
        cmd.append(output)
        remove_tmps = False
        try:
            run_command(cmd)
            self.create_preview_file(output)
            remove_tmps = True
        finally:
            if (self.copy_vias_on_mask == 'auto' and GS.ki8) or self.copy_vias_on_mask == 'yes':
                self.do_copy_vias_on_mask(fname, output)
            if GS.debug_enabled and not remove_tmps:
                if self._files_to_remove:
                    logger.warning(W_KEEPTMP+'Keeping temporal files: '+str(self._files_to_remove))
            else:
                self.remove_temporals()

    def get_targets(self, out_dir):
        pcb_name = self._parent.expand_filename(out_dir, self.output)
        files = [pcb_name]
        if self.create_preview:
            files.append(os.path.splitext(pcb_name)[0]+'.png')
        return files


@output_class
class Panelize(BaseOutput):  # noqa: F821
    """ Panelize
        Creates a panel to fabricate various copies of the PCB at once.
        It currently uses the KiKit tool, which must be available.
        Consult KiKit docs for detailed information.
        [KiKit panelization docs](https://github.com/yaqwsx/KiKit/blob/master/doc/examples.md).
        Current versions of KiKit only support KiCad 6 and my tests using
        KiKit 1.0.5 (the last to support KiCad 5) shown some
        incompatibilities.
        Note that you don't need to specify the units for all distances.
        If they are omitted they are assumed to be `units`.
        The same is valid for angles, using `default_angles` """
    def __init__(self):
        super().__init__()
        with document:
            self.options = PanelizeOptions
            """ *[dict={}] Options for the `Panelize` output """
        self._category = 'PCB/fabrication'

    @staticmethod
    def get_conf_examples(name, layers):
        if not GS.check_tool(name, 'KiKit'):
            return None
        outs = []
        register_xmp_import('PanelDemo_4x4')
        return outs
