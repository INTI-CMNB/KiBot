# -*- coding: utf-8 -*-
# Copyright (c) 2022 Salvador E. Tropea
# Copyright (c) 2022 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
import os
import re
import pcbnew

from .gs import GS
from .misc import UI_SMD, UI_VIRTUAL, MOD_THROUGH_HOLE, MOD_SMD, MOD_EXCLUDE_FROM_POS_FILES
from .out_base import BaseOptions, BaseOutput
from .error import KiPlotConfigurationError
from .macros import macros, document, output_class  # noqa: F401
from . import log

logger = log.get_logger()
INF = float('inf')


def do_round(v, dig):
    v = round(v+1e-9, dig)
    return v if dig else int(v)


def to_mm(iu, dig=2):
    """ KiCad Internal Units to millimeters """
    return do_round(iu/pcbnew.IU_PER_MM, dig)


def to_mils(iu, dig=0):
    """ KiCad Internal Units to mils (1/1000 inch) """
    return do_round(iu/pcbnew.IU_PER_MILS, dig)


def to_inches(iu, dig=2):
    """ KiCad Internal Units to inches """
    return do_round(iu/(pcbnew.IU_PER_MILS*1000), dig)


def get_class_index(val, lst):
    """ Used to search in an Eurocircuits class vector.
        Returns the first match that is >= to val. """
    val = to_mm(val, 3)
    for c, v in enumerate(lst):
        if val >= v:
            return c
    return c+1


def get_pattern_class(track, clearance, oar):
    """ Returns the Eurocircuits Pattern class for a track width, clearance and OAR """
    c1 = (0.25, 0.2, 0.175, 0.150, 0.125, 0.1, 0.09)
    c2 = (0.2, 0.15, 0.15, 0.125, 0.125, 0.1, 0.1)
    ct = get_class_index(track, c1)
    cc = get_class_index(clearance, c1)
    co = get_class_index(oar, c2)
    cf = max(ct, max(cc, co))
    return cf + 3


def get_drill_class(via_drill):
    """ Returns the Eurocircuits Drill class for a drill size.
        This is the real (tool) size. """
    c3 = (0.6, 0.45, 0.35, 0.25, 0.2)
    cd = get_class_index(via_drill, c3)
    return chr(ord('A') + cd)


def to_top_bottom(front, bottom):
    """ Returns a text indicating if the feature is in top/bottom layers """
    if front and bottom:
        return "TOP / BOTTOM"
    elif front:
        return "TOP"
    elif bottom:
        return "BOTTOM"
    return "NONE"


def to_smd_tht(smd, tht):
    """ Returns a text indicating if the components are SMD/THT """
    if smd and tht:
        return "SMD + THT"
    elif smd:
        return "SMD"
    elif tht:
        return "THT"
    return "NONE"


def to_top_bottom_color(front, bottom):
    """ Returns a text indicating the top/bottom colors """
    f = front.strip().lower()
    b = bottom.strip().lower()
    if f == b:
        return front.capitalize()
    return "Top: "+front.capitalize()+" / Bottom: "+bottom.capitalize()


def solve_edge_connector(val):
    if val == 'no':
        return ''
    if val == 'bevelled':
        return 'yes, bevelled'
    return val


class ReportOptions(BaseOptions):
    def __init__(self):
        with document:
            self.output = GS.def_global_output
            """ Output file name (%i='report', %x='txt') """
            self.template = 'full'
            """ Name for one of the internal templates (full, simple) or a custom template file """
        super().__init__()
        self._expand_id = 'report'
        self._expand_ext = 'txt'
        self._mm_digits = 2
        self._mils_digits = 0
        self._in_digits = 2

    def config(self, parent):
        super().config(parent)
        if self.template.lower() in ('full', 'simple'):
            self.template = os.path.abspath(os.path.join(os.path.dirname(__file__), 'report_templates',
                                            'report_'+self.template.lower()+'.txt'))
        if not os.path.isfile(self.template):
            raise KiPlotConfigurationError("Missing report template: `{}`".format(self.template))

    def do_replacements(self, line, defined):
        """ Replace ${VAR} patterns """
        for var in re.findall(r'\$\{([^\s\}]+)\}', line):
            if var[0] == '_':
                # Prevent access to internal data
                continue
            units = None
            var_ori = var
            m = re.match(r'^(%[^,]+),(.*)$', var)
            pattern = None
            if m:
                pattern = m.group(1)
                var = m.group(2)
            if var.endswith('_mm'):
                units = to_mm
                digits = self._mm_digits
                var = var[:-3]
            elif var.endswith('_in'):
                units = to_inches
                digits = self._in_digits
                var = var[:-3]
            elif var.endswith('_mils'):
                units = to_mils
                digits = self._mils_digits
                var = var[:-5]
            if var in defined:
                val = defined[var]
                if val == INF:
                    val = 'N/A'
                elif units is not None and isinstance(val, (int, float)):
                    val = units(val, digits)
                if pattern is not None:
                    clear = False
                    if 's' in pattern:
                        val = str(val)
                    else:
                        try:
                            val = float(val)
                        except ValueError:
                            val = 0
                            clear = True
                    rep = pattern % val
                    if clear:
                        rep = ' '*len(rep)
                else:
                    rep = str(val)
                line = line.replace('${'+var_ori+'}', rep)
            else:
                print('Error: Unable to expand `{}`'.format(var))
        return line

    def context_defined_tracks(self, line):
        """ Replace iterator for the `defined_tracks` context """
        text = ''
        for t in sorted(self._track_sizes):
            if not t:
                continue  # KiCad 6
            text += self.do_replacements(line, {'track': t})
        return text

    def context_used_tracks(self, line):
        """ Replace iterator for the `used_tracks` context """
        text = ''
        for t in sorted(self._tracks_m.keys()):
            text += self.do_replacements(line, {'track': t, 'count': self._tracks_m[t],
                                         'defined': 'yes' if t in self._tracks_defined else 'no'})
        return text

    def context_defined_vias(self, line):
        """ Replace iterator for the `defined_vias` context """
        text = ''
        for v in self._via_sizes_sorted:
            text += self.do_replacements(line, {'pad': v[1], 'drill': v[0]})
        return text

    def context_used_vias(self, line):
        """ Replace iterator for the `used_vias` context """
        text = ''
        for v in self._vias_m:
            d = v[1]
            h = v[0]
            aspect = round(self.thickness/d, 1)
            # IPC-2222 Table 9.4
            producibility_level = 'C'
            if aspect < 9:
                if aspect < 5:
                    producibility_level = 'A'
                else:
                    producibility_level = 'B'
            defined = {'pad': v[1], 'drill': v[0]}
            defined['count'] = self._vias[v]
            defined['aspect'] = aspect
            defined['producibility_level'] = producibility_level
            defined['defined'] = 'yes' if (h, d) in self._vias_defined else 'no'
            text += self.do_replacements(line, defined)
        return text

    def context_hole_sizes_no_vias(self, line):
        """ Replace iterator for the `hole_sizes_no_vias` context """
        text = ''
        for d in sorted(self._drills.keys()):
            text += self.do_replacements(line, {'drill': d, 'count': self._drills[d]})
        return text

    def context_stackup(self, line):
        """ Replace iterator for the `stackup` context """
        text = ''
        for s in self._stackup:
            context = {}
            for k in dir(s):
                val = getattr(s, k)
                if k[0] != '_' and not callable(val):
                    context[k] = val if val is not None else ''
            text += self.do_replacements(line, context)
        return text

    @staticmethod
    def is_pure_smd_5(m):
        return m.GetAttributes() == UI_SMD

    @staticmethod
    def is_pure_smd_6(m):
        return m.GetAttributes() & (MOD_THROUGH_HOLE | MOD_SMD) == MOD_SMD

    @staticmethod
    def is_not_virtual_5(m):
        return m.GetAttributes() != UI_VIRTUAL

    @staticmethod
    def is_not_virtual_6(m):
        return not (m.GetAttributes() & MOD_EXCLUDE_FROM_POS_FILES)

    def get_attr_tests(self):
        if GS.ki5():
            return self.is_pure_smd_5, self.is_not_virtual_5
        return self.is_pure_smd_6, self.is_not_virtual_6

    def meassure_pcb(self, board):
        edge_layer = board.GetLayerID('Edge.Cuts')
        x1 = y1 = x2 = y2 = None  ## type: float
        draw_type = 'DRAWSEGMENT' if GS.ki5() else 'PCB_SHAPE'
        for d in board.GetDrawings():
            if d.GetClass() == draw_type and d.GetLayer() == edge_layer:
                if x1 is None:
                    p = d.GetStart()
                    x1 = x2 = p.x
                    y1 = y2 = p.y
                for p in [d.GetStart(), d.GetEnd()]:
                    x2 = max(x2, p.x)
                    y2 = max(y2, p.y)
                    x1 = min(x1, p.x)
                    y1 = min(y1, p.y)
        if x1 is None:
            self.bb_w = self.bb_h = INF
        else:
            self.bb_w = x2-x1
            self.bb_h = y2-y1

    def collect_data(self, board):
        ds = board.GetDesignSettings()
        ###########################################################
        # Board size
        ###########################################################
        # The value returned by ComputeBoundingBox(True) adds the drawing width!
        bb = board.ComputeBoundingBox(True)
        self.bb_w_d = bb.GetWidth()
        self.bb_h_d = bb.GetHeight()
        self.meassure_pcb(board)
        ###########################################################
        # Board thickness
        ###########################################################
        self.thickness = ds.GetBoardThickness()
        ###########################################################
        # Number of layers
        ###########################################################
        self.layers = ds.GetCopperLayerCount()
        ###########################################################
        # Solder mask layers
        ###########################################################
        fmask = board.IsLayerEnabled(board.GetLayerID('F.Mask'))
        bmask = board.IsLayerEnabled(board.GetLayerID('B.Mask'))
        self.solder_mask = to_top_bottom(fmask, bmask)
        ###########################################################
        # Silk screen
        ###########################################################
        fsilk = board.IsLayerEnabled(board.GetLayerID('F.SilkS'))
        bsilk = board.IsLayerEnabled(board.GetLayerID('B.SilkS'))
        self.silk_screen = to_top_bottom(fsilk, bsilk)
        ###########################################################
        # Clearance
        ###########################################################
        self.clearance = ds.GetSmallestClearanceValue()
        # This seems to be bogus:
        # h2h = ds.m_HoleToHoleMin
        ###########################################################
        # Track width (min)
        ###########################################################
        self.track_d = ds.m_TrackMinWidth
        tracks = board.GetTracks()
        self.oar_vias = self.track = INF
        self._vias = {}
        self._tracks_m = {}
        track_type = 'TRACK' if GS.ki5() else 'PCB_TRACK'
        via_type = 'VIA' if GS.ki5() else 'PCB_VIA'
        for t in tracks:
            tclass = t.GetClass()
            if tclass == track_type:
                w = t.GetWidth()
                self.track = min(w, self.track)
                self._tracks_m[w] = self._tracks_m.get(w, 0) + 1
            elif tclass == via_type:
                via = t.Cast()
                via_id = (via.GetDrill(), via.GetWidth())
                self._vias[via_id] = self._vias.get(via_id, 0) + 1
                self.oar_vias = min(self.oar_vias, via_id[1] - via_id[0])
        self.track_min = min(self.track_d, self.track)
        ###########################################################
        # Drill (min)
        ###########################################################
        modules = board.GetModules() if GS.ki5() else board.GetFootprints()
        self._drills = {}
        self._drills_oval = {}
        self.oar_pads = self.pad_drill = INF
        self.slot = INF
        self.top_smd = self.top_tht = self.bot_smd = self.bot_tht = 0
        top_layer = board.GetLayerID('F.Cu')
        bottom_layer = board.GetLayerID('B.Cu')
        is_pure_smd, is_not_virtual = self.get_attr_tests()
        for m in modules:
            layer = m.GetLayer()
            if layer == top_layer:
                if is_pure_smd(m):
                    self.top_smd += 1
                elif is_not_virtual(m):
                    self.top_tht += 1
            elif layer == bottom_layer:
                if is_pure_smd(m):
                    self.bot_smd += 1
                elif is_not_virtual(m):
                    self.bot_tht += 1
            pads = m.Pads()
            for pad in pads:
                dr = pad.GetDrillSize()
                if not dr.x:
                    continue
                self.pad_drill = min(dr.x, self.pad_drill)
                self.pad_drill = min(dr.y, self.pad_drill)
                if dr.x == dr.y:
                    self._drills[dr.x] = self._drills.get(dr.x, 0) + 1
                else:
                    if dr.x < dr.y:
                        m = (dr.x, dr.y)
                    else:
                        m = (dr.y, dr.x)
                    self._drills_oval[m] = self._drills_oval.get(m, 0) + 1
                    self.slot = min(self.slot, m[0])
                    # print('{} @ {}'.format(dr, pad.GetPosition()))
                pad_sz = pad.GetSize()
                oar_x = pad_sz.x - dr.x
                oar_y = pad_sz.y - dr.y
                oar_t = min(oar_x, oar_y)
                if oar_t:
                    self.oar_pads = min(self.oar_pads, oar_t)
        self._vias_m = list(sorted(self._vias.keys()))
        # Via Pad size
        self.via_pad_d = ds.m_ViasMinSize
        self.via_pad = self._vias_m[0][1]
        self.via_pad_min = min(self.via_pad_d, self.via_pad)
        # Via Drill size
        self.via_drill_d = ds.m_ViasMinDrill if GS.ki5() else ds.m_MinThroughDrill
        self.via_drill = self._vias_m[0][0]
        self.via_drill_min = min(self.via_drill_d, self.via_drill)
        # Via Drill size minus 0.1 mm
        self.via_drill_1_d = self.via_drill_d - pcbnew.IU_PER_MM/10
        self.via_drill_1 = self.via_drill - pcbnew.IU_PER_MM/10
        self.via_drill_1_min = self.via_drill_min - pcbnew.IU_PER_MM/10
        # Pad Drill
        # No minimum defined
        self.pad_drill_min = self.pad_drill if GS.ki5() else ds.m_MinThroughDrill
        # Pad Drill size minus 0.1 mm
        self.pad_drill_1 = self.pad_drill_1_min = self.pad_drill - pcbnew.IU_PER_MM/10
        # Drill overall
        self.drill_d = min(self.via_drill_d, self.pad_drill)
        self.drill = min(self.via_drill, self.pad_drill)
        self.drill_min = min(self.via_drill_min, self.pad_drill_min)
        # Drill overall size minus 0.1 mm
        self.drill_1_d = self.drill_d - pcbnew.IU_PER_MM/10
        self.drill_1 = self.drill - pcbnew.IU_PER_MM/10
        self.drill_1_min = self.drill_min - pcbnew.IU_PER_MM/10
        self.top_comp_type = to_smd_tht(self.top_smd, self.top_tht)
        self.bot_comp_type = to_smd_tht(self.bot_smd, self.bot_tht)
        ###########################################################
        # Vias
        ###########################################################
        self.micro_vias = 'yes' if ds.m_MicroViasAllowed else 'no'
        self.blind_vias = 'yes' if ds.m_BlindBuriedViaAllowed else 'no'
        self.uvia_pad = ds.m_MicroViasMinSize
        self.uvia_drill = ds.m_MicroViasMinDrill
        via_sizes = board.GetViasDimensionsList()
        self._vias_defined = set()
        self._via_sizes_sorted = []
        self.oar_vias_d = INF
        for v in sorted(via_sizes, key=lambda x: (x.m_Diameter, x.m_Drill)):
            d = v.m_Diameter
            h = v.m_Drill
            if not d and not h:
                continue  # KiCad 6
            self.oar_vias_d = min(self.oar_vias_d, d - h)
            self._vias_defined.add((h, d))
            self._via_sizes_sorted.append((h, d))
        ###########################################################
        # Outer Annular Ring
        ###########################################################
        self.oar_pads_min = self.oar_pads
        self.oar_d = min(self.oar_vias_d, self.oar_pads)
        self.oar = min(self.oar_vias, self.oar_pads)
        self.oar_min = min(self.oar_d, self.oar)
        self.oar_vias_min = min(self.oar_vias_d, self.oar_vias)
        ###########################################################
        # Eurocircuits class
        # https://www.eurocircuits.com/pcb-design-guidelines-classification/
        ###########################################################
        # Pattern class
        self.pattern_class_min = get_pattern_class(self.track_min, self.clearance, self.oar_min)
        self.pattern_class = get_pattern_class(self.track, self.clearance, self.oar)
        self.pattern_class_d = get_pattern_class(self.track_d, self.clearance, self.oar_d)
        # Drill class
        self.drill_class_min = get_drill_class(self.via_drill_min)
        self.drill_class = get_drill_class(self.via_drill)
        self.drill_class_d = get_drill_class(self.via_drill_d)
        ###########################################################
        # General stats
        ###########################################################
        self._track_sizes = board.GetTrackWidthList()
        self._tracks_defined = set(self._track_sizes)

    def eval_conditional(self, line):
        context = {k: getattr(self, k) for k in dir(self) if k[0] != '_' and not callable(getattr(self, k))}
        res = None
        text = line[2:].strip()
        logger.debug('- Evaluating `{}`'.format(text))
        try:
            res = eval(text, {}, context)
        except Exception as e:
            raise KiPlotConfigurationError('wrong conditional: `{}`\nPython says: `{}`'.format(text, str(e)))
        logger.debug('- Result `{}`'.format(res))
        return res

    def do_template(self, template_file, output_file):
        text = ''
        logger.debug("Report template: `{}`".format(template_file))
        with open(template_file, "rt") as f:
            skip_next = False
            for line in f:
                if skip_next:
                    skip_next = False
                    continue
                done = False
                if line[0] == '#':
                    if line.startswith('#?'):
                        skip_next = not self.eval_conditional(line)
                        done = True
                        line = ''
                    elif ':' in line:
                        context = line[1:].split(':')[0]
                        logger.debug("- Report context: `{}`".format(context))
                        name = 'context_'+context
                        if hasattr(self, name):
                            # Contexts are members called context_*
                            line = getattr(self, name)(line[len(context)+2:])
                            done = True
                        else:
                            raise KiPlotConfigurationError("Unknown context: `{}`".format(context))
                if not done:
                    # Just replace using any data member (_* excluded)
                    line = self.do_replacements(line, self.__dict__)
                text += line
        logger.debug("Report output: `{}`".format(output_file))
        with open(output_file, "wt") as f:
            f.write(text)

    def get_targets(self, out_dir):
        return [self._parent.expand_filename(out_dir, self.output)]

    def run(self, fname):
        self.pcb_material = GS.global_pcb_material
        self.solder_mask_color = GS.global_solder_mask_color
        self.solder_mask_color_top = GS.global_solder_mask_color_top
        self.solder_mask_color_bottom = GS.global_solder_mask_color_bottom
        self.solder_mask_color_text = to_top_bottom_color(GS.global_solder_mask_color_top, GS.global_solder_mask_color_bottom)
        self.silk_screen_color = GS.global_silk_screen_color
        self.silk_screen_color_top = GS.global_silk_screen_color_top
        self.silk_screen_color_bottom = GS.global_silk_screen_color_bottom
        self.silk_screen_color_text = to_top_bottom_color(GS.global_silk_screen_color_top, GS.global_silk_screen_color_bottom)
        self.pcb_finish = GS.global_pcb_finish
        self.edge_connector = solve_edge_connector(GS.global_edge_connector)
        self.castellated_pads = GS.global_castellated_pads
        self.edge_plating = GS.global_edge_plating
        self.copper_thickness = GS.global_copper_thickness
        self.impedance_controlled = GS.global_impedance_controlled
        self.stackup = 'yes' if GS.stackup else ''
        self._stackup = GS.stackup if GS.stackup else []
        self.collect_data(GS.board)
        self.do_template(self.template, fname)


@output_class
class Report(BaseOutput):  # noqa: F821
    """ Design report
        Generates a report about the design.
        Mainly oriented to be sent to the manufacturer or check PCB details. """
    def __init__(self):
        super().__init__()
        with document:
            self.options = ReportOptions
            """ [dict] Options for the `report` output """
