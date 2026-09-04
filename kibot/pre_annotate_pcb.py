# -*- coding: utf-8 -*-
# Copyright (c) 2022-2024 Salvador E. Tropea
# Copyright (c) 2022-2024 Instituto Nacional de Tecnología Industrial
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)
from .error import PlotError
from .gs import GS
from .kiplot import load_sch, load_board
from .misc import W_NOANNO
from .kicad.v5_sch import SchematicComponent
from .optionable import Optionable
from .macros import macros, document, pre_class  # noqa: F401
from .log import get_logger

logger = get_logger(__name__)


class Annotate_PCBOptions(Optionable):
    """ Reference sorting options """
    def __init__(self):
        super().__init__()
        with document:
            self.top_main_axis = 'y'
            """ [x,y] Use this axis as main sorting criteria for the top layer """
            self.top_main_ascending = True
            """ Sort the main axis in ascending order for the top layer.
                For X this is left to right and for Y top to bottom """
            self.top_secondary_ascending = True
            """ Sort the secondary axis in ascending order for the top layer.
                For X this is left to right and for Y top to bottom """
            self.top_start = 1
            """ First number for references at the top layer """
            self.bottom_main_axis = 'y'
            """ [x,y] Use this axis as main sorting criteria for the bottom layer """
            self.bottom_main_ascending = True
            """ Sort the main axis in ascending order for the bottom layer.
                For X this is left to right and for Y top to bottom """
            self.bottom_secondary_ascending = True
            """ Sort the secondary axis in ascending order for the bottom layer.
                For X this is left to right and for Y top to bottom """
            self.bottom_start = 101
            """ First number for references at the bottom layer.
                Use -1 to continue from the last top reference """
            self.use_position_of = 'footprint'
            """ [footprint,reference] Which coordinate is used """
            self.grid = 1.0
            """ Grid size in millimeters """


def granular(val, gran):
    if val > 0:
        return round(round(val/gran+1e-9)*gran, 8)
    return round(round(val/gran-1e-9)*gran, 8)


class ModInfo(object):
    def __init__(self, m, coord_type, grid):
        self.footprint = m
        # Get the reference and separate it in prefix (i.e. R) and suffix (i.e. 10)
        ref = GS.fp_get_reference(m)
        res = SchematicComponent.ref_re.match(ref)
        if not res:
            raise PlotError('Malformed component reference `{}`'.format(ref))
        self.ref_prefix, self.ref_suffix = res.groups()
        self.new_ref_suffix = -1
        # Get the relevant coordinate
        if coord_type == 'footprint':
            pos = GS.fp_get_center(m)
        else:  # Reference
            pos = m.Reference().GetPosition()
        self.x = pos.x
        self.y = pos.y
        # Scale and round the coordinates
        scale = GS.unit_name_to_scale_factor('millimeters')
        self.x = granular(self.x*scale, grid)
        self.y = granular(self.y*scale, grid)
        # Side
        self.is_bottom = m.IsFlipped()
        if self.is_bottom:
            # Mirror the X axis
            self.x = -self.x


def sort_key(ops, obj, top=True):
    main_axis = ops.top_main_axis if top else ops.bottom_main_axis
    main_ascending = ops.top_main_ascending if top else ops.bottom_main_ascending
    secondary_ascending = ops.top_secondary_ascending if top else ops.bottom_secondary_ascending
    if main_axis == 'y':
        if main_ascending:
            if secondary_ascending:
                # Top to bottom, left to right (TBLR)
                return [obj.ref_prefix, obj.y, obj.x]
            else:
                # Top to bottom, right to left (TBRL)
                return [obj.ref_prefix, obj.y, -obj.x]
        else:  # not main_ascending
            if secondary_ascending:
                # Bottom to top, left to right (BTLR)
                return [obj.ref_prefix, -obj.y, obj.x]
            else:
                # Bottom to top, right to left (BTRL)
                return [obj.ref_prefix, -obj.y, -obj.x]
    else:  # main_axis == 'x':
        if main_ascending:
            if secondary_ascending:
                # Left to right, top to bottom (LRTB)
                return [obj.ref_prefix, obj.x, obj.y]
            else:
                # Left to right, bottom to top (LRBT)
                return [obj.ref_prefix, obj.x, -obj.y]
        else:  # not main_ascending
            if secondary_ascending:
                # Right to left, top to bottom (RLTB)
                return [obj.ref_prefix, -obj.x, obj.y]
            else:
                # Right to left, bottom to top (RLBT)
                return [obj.ref_prefix, -obj.x, -obj.y]


@pre_class
class Annotate_PCB(BasePreFlight):  # noqa: F821
    """ Annotate PCB
        Annotates the PCB according to physical coordinates.
        This preflight modifies the PCB and schematic, use it only in revision control environments.
        Used to assign references according to footprint coordinates.
        The project must be fully annotated first """
    def __init__(self):
        super().__init__()
        self._sch_related = True
        self._pcb_related = True
        with document:
            self.annotate_pcb = Annotate_PCBOptions
            """ [dict={}]  Options for the `annotate_pcb` preflight """

    def __str__(self):
        v = self.annotate_pcb
        return f'{self.type} (top: {v.top_main_axis}/{v.top_start} bot: {v.bottom_main_axis}/{v.bottom_start})'

    def get_example():
        """ Returns a YAML value for the example config """
        return ("\n    top_main_axis: y"
                "\n    top_main_ascending: true"
                "\n    top_secondary_ascending: true"
                "\n    top_start: 1"
                "\n    bottom_main_axis: y"
                "\n    bottom_main_ascending: true"
                "\n    bottom_secondary_ascending: true"
                "\n    bottom_start: 101"
                "\n    use_position_of: 'footprint'"
                "\n    grid: 1.0")

    def annotate_ki6(self, changes):
        """ Apply changes to the KiCad 6 schematic """
        for ins in GS.sch.symbol_instances:
            new_ref = changes.get(ins.reference, None)
            if new_ref is not None:
                c = ins.component
                c.set_ref(new_ref)

    def annotate_ki5(self, changes):
        """ Apply changes to the KiCad 5 schematic """
        comps = GS.sch.get_components()
        for c in comps:
            new_ref_suffix = changes.get(c.f_ref, None)
            if new_ref_suffix is not None:
                # Force a new number
                c.ref = c.f_ref = c.ref_prefix+str(new_ref_suffix)
                c.ref_suffix = str(new_ref_suffix)
                # Fix the reference field
                field = next(filter(lambda x: x.number == 0, c.fields), None)
                if field:
                    field.value = c.ref
            # Fix the ARs
            if c.ar:
                for o in c.ar:
                    new_ref_suffix = changes.get(o.ref, None)
                    if new_ref_suffix is not None:
                        o.ref = c.ref_prefix+str(new_ref_suffix)

    def run(self):
        o = self.annotate_pcb
        #
        # PCB part
        #
        load_board()
        logger.debug('- Collecting components')
        modules = []
        for m in GS.get_modules():
            ref = GS.fp_get_reference(m)
            if ref[-1] == '?':
                center = GS.fp_get_center(m)
                scale = GS.unit_name_to_scale_factor('millimeters')
                logger.warning(W_NOANNO+'Missing annotation in component at {},{} mm ({})'.
                               format(center.x*scale, center.y*scale, ref))
            else:
                modules.append(ModInfo(m, o.use_position_of, o.grid))
        modules = sorted(modules, key=lambda x: sort_key(o, x))
        if GS.debug_level > 2:
            logger.debug('- Components:')
            for m in modules:
                logger.debug('  '+str(m.__dict__))
        prefixes = {x.ref_prefix for x in modules}
        logger.debug('- Sorting components')
        for p in sorted(prefixes):
            n = o.top_start
            for m in filter(lambda x: x.ref_prefix == p and not x.is_bottom, modules):
                m.new_ref_suffix = n
                n = n+1
                logger.debug(' - {}{} -> {}{} ({},{})'.format(m.ref_prefix, m.ref_suffix, m.ref_prefix, m.new_ref_suffix, m.x,
                             m.y))
            if o.bottom_start != -1:
                n = o.bottom_start
            for m in filter(lambda x: x.ref_prefix == p and x.is_bottom, modules):
                m.new_ref_suffix = n
                n = n+1
                logger.debug(' - {}{} -> {}{} ({},{})'.format(m.ref_prefix, m.ref_suffix, m.ref_prefix, m.new_ref_suffix, m.x,
                             m.y))
        logger.debug('- Modifying components')
        changes = {}
        for m in modules:
            old_ref = m.ref_prefix+str(m.ref_suffix)
            new_ref = m.ref_prefix+str(m.new_ref_suffix)
            if GS.ki6:
                changes[old_ref] = new_ref
            else:
                changes[old_ref] = m.new_ref_suffix
            m.footprint.SetReference(new_ref)
        logger.debug('- Saving PCB')
        GS.save_pcb()
        #
        # SCH part
        #
        load_sch()
        if not GS.sch:
            return
        logger.debug('- Transferring changes to the schematic')
        if GS.ki5:
            self.annotate_ki5(changes)
        else:
            self.annotate_ki6(changes)
        GS.sch.save()
