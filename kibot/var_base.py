# -*- coding: utf-8 -*-
# Copyright (c) 2020-2026 Salvador E. Tropea
# Copyright (c) 2020-2026 Instituto Nacional de Tecnología Industrial
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)
# Note: the algorithm used to detect the PCB outline is adapted from KiKit project.
from itertools import chain
import os
from tempfile import TemporaryDirectory
from .registrable import RegVariant
from .optionable import Optionable, PanelOptions
from .fil_base import apply_exclude_filter, apply_fitted_filter, apply_fixed_filter, apply_pre_transform
from .error import KiPlotConfigurationError
from .layer import Layer
from .misc import KIKIT_UNIT_ALIASES
from .gs import GS
from .kiplot import run_command
from .kicad.pcb import PCB
from .macros import macros, document, variant_class  # noqa: F401
from . import log

logger = log.get_logger()


def round_point(point, precision=-4):
    return (round(point[0], precision), round(point[1], precision))


def point_str(point):
    if isinstance(point, tuple):
        return '({} mm, {} mm)'.format(GS.to_mm(point[0]), GS.to_mm(point[1]))
    return '({} mm, {} mm)'.format(GS.to_mm(point.x), GS.to_mm(point.y))


def bbox_str(bbox):
    return point_str(bbox.GetPosition())+'-'+point_str(bbox.GetEnd())


class Edge(object):
    def __init__(self, shape):
        super().__init__()
        self.start = GS.get_start_point(shape)
        self.r_start = round_point(self.start)
        self.end = GS.get_end_point(shape)
        self.r_end = round_point(self.end)
        self.shape = shape
        self.cls = GS.get_shape(shape)
        self.used = False

    def get_other_end(self, point):
        if self.r_start != point:
            return self.start, self.r_start
        return self.end, self.r_end

    def get_bbox(self):
        """ Get the Bounding Box for the shape, without its line width.
            KiKit uses the value in this way. """
        return GS.get_shape_bbox(self.shape)

    def __str__(self):
        return '{} {}-{}'.format(self.cls, point_str(self.start), point_str(self.end))


class SubPCBOptions(PanelOptions):
    def __init__(self):
        super().__init__()
        self._unknown_is_error = True
        with document:
            self.name = ''
            """ *Name for this sub-pcb """
            self.reference = ''
            """ *Use it for the annotations method.
                This is the reference for the `kikit:Board` footprint used to identify the sub-PCB.
                Note that you can use any footprint as long as its position is inside the PCB outline.
                When empty the sub-PCB is specified using a rectangle """
            self.ref_layer = 'Edge.Cuts'
            """ Layer where the PCB outline indicated by `reference` is found.
                So you can use an outline that is not the real PCB contour """
            self.ref = None
            """ {reference} """
            self.tlx = 0
            """ [number|string] The X position of the top left corner for the rectangle that contains the sub-PCB """
            self.top_left_x = None
            """ {tlx} """
            self.tly = 0
            """ [number|string] The Y position of the top left corner for the rectangle that contains the sub-PCB """
            self.top_left_y = None
            """ {tly} """
            self.brx = 0
            """ [number|string] The X position of the bottom right corner for the rectangle that contains the sub-PCB """
            self.bottom_right_x = None
            """ {brx} """
            self.bry = 0
            """ [number|string] The Y position of the bottom right corner for the rectangle that contains the sub-PCB """
            self.bottom_right_y = None
            """ {bry} """
            self.units = 'mm'
            """ [millimeters,inches,mils,mm,cm,dm,m,mil,inch,in] Units used when omitted """
            self.file_id = ''
            """ Text to use as the replacement for %v expansion.
                When empty we use the parent `file_id` plus the `name` of the sub-PCB """
            self.tool = 'internal'
            """ [internal,kikit] Tool used to extract the sub-PCB. """
            self.tolerance = 0
            """ [number|string] Used to enlarge the selected rectangle to include elements outside the board.
                KiCad 5: To avoid rounding issues this value is set to 0.000002 mm when 0 is specified """
            self.strip_annotation = False
            """ Remove the annotation footprint. Note that KiKit will remove all annotations,
                but the internal implementation just the one indicated by `ref`.
                If you need to remove other annotations use an exclude filter """
            self.center_result = True
            """ Move the resulting PCB to the center of the page.
                You can disable it only for the internal tool, KiKit should always do it """
        self._name_example = 'a_sub_pcb'
        self._reference_example = 'BRD1'

    def __str__(self):
        res = self.name+' '
        return res+(self.reference if self.reference else f'({self.tlx},{self.tly}) ({self.brx},{self.bry})')

    def is_zero(self, val):
        return isinstance(val, (int, float)) and val == 0

    def config(self, parent):
        super().config(parent)
        if not self.name:
            raise KiPlotConfigurationError('Sub-PCB without a name')
        self.units = KIKIT_UNIT_ALIASES.get(self.units, self.units)
        if (not self.reference and self.is_zero(self.tlx) and self.is_zero(self.tly) and self.is_zero(self.brx) and
           self.is_zero(self.bry)):
            raise KiPlotConfigurationError('No reference or rectangle specified for {} sub-PCB'.format(self.name))
        self.add_units(('tlx', 'tly', 'brx', 'bry', 'tolerance'), self.units, convert=True)
        if not self._tolerance and GS.ki5:
            # KiCad 5 workaround: rounding issues generate 1 fm of error. So we change to 2 fm tolerance.
            self._tolerance = 2
        # Reference layer
        self._ref_layer = Layer.solve(self.ref_layer or 'Edge.Cuts')[0]._id

    def get_separate_source(self):
        if self.reference:
            src = "annotation; ref: {}".format(self.reference)
            # TODO: add self._ref_layer when https://github.com/yaqwsx/KiKit/pull/846 is available
        else:
            src = "rectangle; tlx: {}; tly: {}; brx: {}; bry: {}".format(self.tlx, self.tly, self.brx, self.bry)
        if self._tolerance:
            src += "; tolerance: {}".format(self.tolerance)
        return src

    def separate_board(self, comps_hash):
        """ Apply the sub-PCB using an external tool and load it into memory """
        # Make sure kikit is available
        command = GS.ensure_tool('global', 'KiKit')
        with TemporaryDirectory(prefix='kibot-separate') as d:
            dest = os.path.join(d, os.path.basename(GS.pcb_file))
            if comps_hash:
                # Memorize the used modules
                old_modules = {GS.fp_get_reference(m) for m in GS.get_modules()}
            # Now do the separation
            cmd = [command, 'separate', '--preserveArcs', '-s', self.get_separate_source()]
            if self.strip_annotation:
                cmd.append('--stripAnnotations')
            cmd.extend([GS.pcb_file, dest])
            # Execute the separate
            run_command(cmd)
            # Load this board
            GS.load_board(dest, forced=True)
            # Now reflect the changes in the list of components
            if comps_hash:
                logger.debug('Removing components outside the sub-PCB')
                # Memorize the used modules
                new_modules = {GS.fp_get_reference(m) for m in GS.get_modules()}
                # Compute the modules we removed
                diff = old_modules - new_modules
                logger.debugl(3, diff)
                # Exclude them from _comps
                for c in diff:
                    cmp = comps_hash[c]
                    if cmp.included:
                        cmp.included = False
                        self._excl_by_sub_pcb.add(c)
                        logger.debugl(2, '- Removing '+c)

    def _remove_items(self, iter):
        """ Remove items outside the rectangle.
            If the item has width (shapes and tracks) we discard it.
            This produces something closer to KiKit. """
        for m in iter:
            with_width = hasattr(m, 'GetWidth')
            if with_width:
                width = m.GetWidth()
                m.SetWidth(0)
            if not self._board_rect.Contains(m.GetBoundingBox()):
                GS.board.Remove(m)
                self._removed.append(m)
            if with_width:
                m.SetWidth(width)

    def _remove_modules(self, iter, comps_hash):
        """ Remove modules outside the rectangle.
            Footprints are added to the list of references to exclude.
            We also check their position, not their BBox. """
        for m in iter:
            ref = GS.fp_get_reference(m)
            if not self._board_rect.Contains(m.GetPosition()) or (self.strip_annotation and ref == self.reference):
                GS.board.Remove(m)
                self._removed.append(m)
                if comps_hash:
                    self._excl_by_sub_pcb.add(ref)

    def remove_outside(self, comps_hash):
        """ Remove footprints, drawings, text and zones outside `_board_rect` rectangle.
            Keep them in a list to restore later. """
        self._removed = []
        self._remove_modules(GS.get_modules(), comps_hash)
        self._remove_items(GS.board.GetDrawings())
        self._remove_items(GS.board.GetTracks())
        self._remove_items(list(GS.board.Zones()))

    def get_pcb_edges(self):
        """ Get a list of PCB shapes from the Edge.Cuts layer.
            Only useful elements are returned. """
        edges = []
        layer_cuts = self._ref_layer
        for edge in chain(GS.board.GetDrawings(), *[m.GraphicalItems() for m in GS.get_modules()]):
            if edge.GetLayer() != layer_cuts or edge.GetClass().startswith('PCB_DIM_') or not GS.is_valid_pcb_shape(edge):
                continue
            edges.append(Edge(edge))
        return edges

    def inform_unconnected(self, edge, point):
        raise KiPlotConfigurationError('Discontinuous PCB outline: {} not connected at {}'.format(edge, point_str(point)))

    def inform_multiple_connect(self, edges, point):
        raise KiPlotConfigurationError('PCB outline error: {}, {} and {} are connected at {}'.
                                       format(edges[0], edges[1], edges[2], point_str(point)))

    def find_contour(self, initial_edge, edges):
        """ Find a list of edges that creates a closed contour and contains initial_edge """
        # Classify the points according to its rounded coordinates
        points = {}
        for e in edges:
            points.setdefault(e.r_start, []).append(e)
            points.setdefault(e.r_end, []).append(e)
        # Look for a closed loop that contains initial_edge
        r_start = initial_edge.r_start
        start = initial_edge.start
        r_end = initial_edge.r_end
        contour = [initial_edge]
        cur_edge = initial_edge
        cur_edge.used = True
        bbox = cur_edge.get_bbox()
        while r_start != r_end:
            e = points.get(r_start, None)
            # We should get 2 points, the one we are using and its connected point
            if e is None or len(e) == 1:
                self.inform_unconnected(cur_edge, start)
            if len(e) > 2:
                self.inform_multiple_connect(e, start)
            cur_edge = e[0] if e[0] != cur_edge else e[1]
            # Sanity check
            assert not cur_edge.used
            # Change to the new segment
            contour.append(cur_edge)
            start, r_start = cur_edge.get_other_end(r_start)
            cur_edge.used = True
            bbox.Merge(cur_edge.get_bbox())
        return contour, bbox

    def search_reference_rect(self, ref):
        """ Search the rectangle that contains the outline pointed by `ref` footprint """
        logger.debug('Looking for the rectangle pointed by `{}`'.format(ref))
        extra_debug = GS.debug_level > 2
        # Find the annotation component
        r = next(filter(lambda m: GS.fp_get_reference(m) == ref, GS.get_modules()), None)
        if r is None:
            raise KiPlotConfigurationError('Missing `{}` component in PCB, used for sub-PCB `{}`'.format(ref, self.name))
        # Find the point it indicates
        point = r.GetPosition()
        if extra_debug:
            logger.debug('- Points to '+point_str(point))
        # Look for the PCB edges
        edges = self.get_pcb_edges()
        # Detect which edge is selected
        sel_edge = next(filter(lambda x: x.shape.HitTest(point), edges), None)
        if sel_edge is None:
            raise KiPlotConfigurationError("The `{}` component doesn't select an object in the PCB edge".format(ref))
        if extra_debug:
            logger.debug('- Segment '+str(sel_edge))
        # Detect a contour containing this edge
        contour, bbox = self.find_contour(sel_edge, edges)
        if extra_debug:
            logger.debug('- BBox '+bbox_str(bbox))
            logger.debug('- Elements:')
            for e in contour:
                logger.debug(' - '+str(e))
        return bbox

    def move_objects(self):
        """ Move all objects by self._moved """
        logger.debug('Moving all PCB elements by '+point_str(self._moved))
        GS.move_board_items(self._moved)

    def center_objects(self):
        """ Move all objects in the PCB so it gets centered """
        # Look for the PCB size
        pcb = PCB.load(GS.pcb_file)
        paper_center_x = GS.from_mm(pcb.paper_w/2)
        paper_center_y = GS.from_mm(pcb.paper_h/2)
        # Compute the offset to make it centered
        self._moved = self._board_rect.GetCenter()
        self._moved.x = paper_center_x-self._moved.x
        self._moved.y = paper_center_y-self._moved.y
        self.move_objects()

    def apply(self, comps_hash):
        """ Apply the sub-PCB selection. """
        self._excl_by_sub_pcb = set()
        self._board_rect = GS.create_eda_rect(self._tlx, self._tly, self._brx, self._bry)
        self._board_rect.Inflate(int(self._tolerance))
        if self.tool == 'internal':
            if self.reference:
                # Get the rectangle containing the board edge pointed by the reference
                self._board_rect = self.search_reference_rect(self.reference)
                self._board_rect.Inflate(int(self._tolerance))
            # Using a rectangle
            self.remove_outside(comps_hash)
            # Center the PCB
            self.center_objects()
        else:
            # Using KiKit:
            self.separate_board(comps_hash)
        # Now mark as excluded all components outside the sub-PCB
        for c in self._excl_by_sub_pcb:
            comps_hash[c].included = False
        # This can't be cloned
        self._board_rect = None

    def unload_board(self, comps_hash):
        # Undo the sub-PCB: just reload the PCB
        GS.load_board(forced=True)

    def restore_removed(self):
        """ Restore the stuff we removed from the board """
        for o in self._removed:
            GS.board.Add(o)

    def restore_moved(self):
        """ Move objects back to their original place """
        self._moved.x = -self._moved.x
        self._moved.y = -self._moved.y
        self.move_objects()

    def revert(self, comps_hash):
        """ Restore the sub-PCB selection. """
        if self.tool == 'internal':
            self.restore_moved()
            self.restore_removed()
        else:
            # Using KiKit:
            self.unload_board(comps_hash)
        # Restore excluded components
        logger.debug('Restoring components outside the sub-PCB')
        for c in self._excl_by_sub_pcb:
            comps_hash[c].included = True


class BasicVariant(RegVariant):
    def __init__(self):
        super().__init__()
        self._unknown_is_error = True
        with document:
            self.name = ''
            """ Used to identify this particular variant definition """
            self.type = ''
            """ Type of variant """
            self.comment = ''
            """ A comment for documentation purposes """
            self.file_id = ''
            """ Text to use as the replacement for %v expansion """
        self._sub_pcb = None

    def get_variant_field(self):
        """ Returns the name of the field used to determine if the component belongs to the variant """
        return None

    def matches_variant(self, text):
        """ This is a generic match mechanism used by variants that doesn't really have a matching mechanism """
        return self.name.lower() == text.lower()

    def fix_doc(self, name, value=None):
        what = '_null'
        if value is None:
            value = ''
            what = "='"+what+"'"
        self.set_doc(name, self.get_doc_simple(name).replace(what, value))


class BaseVariant(BasicVariant):
    def __init__(self):
        super().__init__()
        with document:
            # * Filters
            self.pre_transform = Optionable
            """ [string|list(string)='_null'] Name of the filter to transform fields before applying other filters.
                Use '_var_rename' to transform VARIANT:FIELD fields.
                Use '_var_rename_kicost' to transform kicost.VARIANT:FIELD fields.
                Use '_kicost_rename' to apply KiCost field rename rules """
            self.exclude_filter = Optionable
            """ [string|list(string)='_null'] Name of the filter to exclude components from BoM processing.
                Use '_mechanical' for the default KiBoM behavior """
            self.dnf_filter = Optionable
            """ [string|list(string)='_null'] Name of the filter to mark components as 'Do Not Fit'.
                Use '_kibom_dnf' for the default KiBoM behavior.
                Use '_kicost_dnp'' for the default KiCost behavior """
            self.dnc_filter = Optionable
            """ [string|list(string)='_null'] Name of the filter to mark components as 'Do Not Change'.
                Use '_kibom_dnc' for the default KiBoM behavior """
            self.sub_pcbs = SubPCBOptions
            """ [list(dict)=[]] Used for multi-board workflows as defined by KiKit.
                I don't recommend using it, for detail read
                [this](https://github.com/INTI-CMNB/KiBot/tree/master/docs/1_SCH_2_part_PCBs).
                But if you really need it you can define the sub-PCBs here.
                Then you just use *VARIANT[SUB_PCB_NAME]* instead of just *VARIANT* """

    def filter(self, comps, call_back=None):
        # Apply all the filters
        comps = apply_pre_transform(comps, self.pre_transform)
        apply_exclude_filter(comps, self.exclude_filter)
        apply_fitted_filter(comps, self.dnf_filter)
        apply_fixed_filter(comps, self.dnc_filter)
        return comps
