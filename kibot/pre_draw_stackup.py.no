# -*- coding: utf-8 -*-
# Copyright (c) 2024-2025 Salvador E. Tropea
# Copyright (c) 2024-2025 Instituto Nacional de Tecnología Industrial
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)
import os
from .error import KiPlotConfigurationError
from .gs import GS
from .kicad.pcb_draw_helpers import draw_rect, draw_line, draw_text
from .kiplot import load_board, get_output_targets, look_for_output
from .misc import KICAD_VERSION_9_0_1
from .layer import Layer
from .optionable import Optionable
from .macros import macros, document, pre_class  # noqa: F401
from . import log
import pcbnew
logger = log.get_logger()
VALID_COLUMNS = {'gerber', 'drawing', 'description', 'thickness'}


class SUColumns(Optionable):
    """ A column of data """
    def __init__(self):
        super().__init__()
        self._unknown_is_error = True
        with document:
            self.type = 'drawing'
            """ *[gerber,drawing,description,thickness] Type of column:
                - *gerber*: the file names for the gerber files.
                  Is usable only when a gerber output is provided.
                - *drawing*: the drawings for each layer.
                - *description*: the description for each layer.
                - *thickness*: just displays the total stackup height """
            self.separator = ' '
            """ *Text used as separator, usually one or more spaces """
            self.width = 10
            """ *Relative width. We first compute the total width and then distribute it according
                to the relative width of each column. The absolute width depends on the area
                assigned for the whole drawing """
            self.side = 'auto'
            """ [auto,right,left] Side for the dimension used for the *thickness* type.
                When using *auto* the side is detected looking for a *drawing* column """

    def __str__(self):
        return f'{self.type} {self.width} {self.side}'


class DrawStackupOptions(Optionable):
    """ Draw stackup options """
    def __init__(self):
        with document:
            self.enabled = True
            """ Enable the check. This is the replacement for the boolean value """
            self.pos_x = 19
            """ X position in the PCB. The units are defined by the global *units* variable.
                Only used when the group can't be found """
            self.pos_y = 100
            """ Y position in the PCB. The units are defined by the global *units* variable.
                Only used when the group can't be found """
            self.width = 120
            """ Width for the drawing. The units are defined by the global *units* variable.
                Only used when the group can't be found """
            self.height = 100
            """ Height for the drawing. The units are defined by the global *units* variable.
                Only used when the group can't be found """
            self.layer = 'Cmts.User'
            """ Layer used for the stackup. Only used when the group can't be found.
                Otherwise we use the layer for the first object in the group """
            self.group_name = 'kibot_stackup'
            """ Name for the group containing the drawings. If KiBot can't find it will create
                a new group at the specified coordinates for the indicated layer """
            self.border = 0.1
            """ Line width for the border box. Use 0 to eliminate it """
            self.gerber = ''
            """ *Name of the output used to generate the gerbers. This is needed only when you
                want to include the *gerber* column, containing the gerber file names """
            self.columns = SUColumns
            """ *[list(dict)|list(string)=?] List of columns to display.
                Can be just the name of the column.
                Available columns are *gerber*, *drawing*, *thickness* and *description*.
                When empty KiBot will add them in the above order, skipping the *gerber* if not available """
        super().__init__()
        self._unknown_is_error = True

    def config(self, parent):
        super().config(parent)
        # Ensure we have a valid layer
        load_board()  # We need the board to know the layer names
        self._layer = Layer.solve(self.layer)[0]._id
        # Solve the columns
        # - Make a list
        def_columns = ['drawing', 'thickness', 'description']
        if self.gerber:
            def_columns.insert(0, 'gerber')
        self._columns = Optionable.force_list(self.columns, default=def_columns)
        # - Convert strings
        for c, col in enumerate(self._columns):
            if isinstance(col, str):
                o = SUColumns()
                o.type = col
                if o.type == 'thickness':
                    o.width = 5
                self._columns[c] = o
        # - Sanity
        if not self._columns:
            raise KiPlotConfigurationError('No columns provided')


def draw_core(g, x, y, w, h, layer):
    y = y+int(h*0.1)
    h = int(h*0.8)
    draw_rect(g, x, y, w, h, layer)
    # 45 degrees /
    xend = x+w
    while x < xend:
        x2 = x+h
        y2 = y
        if x2 > xend:
            x2 = xend
            y2 = y+h-(x2-x)
        draw_line(g, x, y+h, x2, y2, layer)
        x += h


def draw_prepreg(g, x, y, w, h, layer):
    y = y+int(h*0.25)
    h = int(h*0.5)
    draw_rect(g, x, y, w, h, layer)
    # 45 degrees \.
    xstart = x
    x += w
    while x > xstart:
        x2 = x-h
        y2 = y
        if x2 < xstart:
            x2 = xstart
            y2 = y+h-(x-x2)
        draw_line(g, x, y+h, x2, y2, layer)
        x -= h


def draw_copper(g, x, y, w, h, layer):
    y = y+int(h*0.4)
    h = int(h*0.2)
    draw_rect(g, x, y, w, h, layer, filled=True)


def draw_mask(g, x, y, w, h, layer):
    y = y+int(h*0.45)
    h = int(h*0.1)
    xend = x+w
    while x < xend:
        w = 2*h
        if x+w > xend:
            w = xend-x
        draw_rect(g, x, y, w, h, layer, filled=True)
        x += 4*h


def get_er_tan(la):
    txt = ''
    if la.epsilon_r:
        txt += f" ϵᵣ {la.epsilon_r}"
    if la.loss_tangent:
        txt += f" tanδ {la.loss_tangent}"
    return txt


def get_dielectric_text(tp, la):
    txt = tp
    if la.material:
        txt += ' '+la.material
    if la.thickness:
        thickness = str(int(la.thickness))+' µm'
        txt += f" {thickness}"
    return txt+get_er_tan(la)


def get_mask_text(la):
    txt = la.type
    if la.color:
        txt += f": {la.color}"
    if la.material:
        txt += f" {la.material}"
    return txt+get_er_tan(la)


def get_copper_text(la):
    txt = "Copper"
    if la.thickness:
        thickness = str(int(la.thickness))+' µm'
        oz = la.thickness/35
        if int(oz) == oz:
            oz = int(oz)
        txt += f" ({thickness}/{oz} oz)"
    return txt


def draw_thickness(g, x, y, w, font_h, first, last, layer, right=True):
    if right:
        x1 = int(x+0.1*w)
        h = -int(w*0.5)
    else:
        x1 = int(x+0.9*w)
        h = int(w*0.5)
    y1 = int(y+(first+0.5)*font_h)
    y2 = int(y+(last+0.5)*font_h)
    dim = pcbnew.PCB_DIM_ALIGNED(GS.board, pcbnew.PCB_DIM_ALIGNED_T)
    dim.SetLayer(layer)
    pos = dim.GetStart()
    pos.x = x1
    pos.y = y1
    dim.SetStart(pos)
    pos = dim.GetEnd()
    pos.x = x1
    pos.y = y2
    dim.SetEnd(pos)
    ds = GS.board.GetDesignSettings()
    dim.SetOverrideTextEnabled(True)
    dim.SetOverrideText(GS.to_mm(ds.GetBoardThickness()))
    dim.SetHeight(h)
    if GS.kicad_version_n < KICAD_VERSION_9_0_1:
        dim.SetUnitsMode(pcbnew.DIM_UNITS_MODE_MILLIMETRES)
    else:
        dim.SetUnitsMode(pcbnew.DIM_UNITS_MODE_MM)
    dim.Update()
    g.AddItem(dim)
    GS.board.Add(dim)


def update_drawing_group(g, pos_x, pos_y, width, height, tlayer, border, gerber, cols):
    # Purge all content
    for item in g.GetItems():
        GS.board.Delete(item)
    # Analyze the stackup
    stackup = []
    sep_gbr = sep_desc = ' '
    col_draw = -1
    col_thick = -1
    for n, c in enumerate(cols):
        if c.type == 'description':
            sep_desc = c.separator
        elif c.type == 'gerber':
            sep_gbr = c.separator
        elif c.type == 'drawing':
            col_draw = n
        elif c.type == 'thickness':
            col_thick = n
    first_height = last_height = None
    for index, la in enumerate(GS.stackup):
        la.id = id = GS.board.GetLayerID(la.name)
        if first_height is None and la.thickness:
            first_height = index
        if la.thickness:
            last_height = index
        is_paste = False
        if id in (pcbnew.F_SilkS, pcbnew.B_SilkS):
            la.draw = draw_mask
            text = get_mask_text(la)
        elif id in (pcbnew.F_Mask, pcbnew.B_Mask):
            la.draw = draw_mask
            text = get_mask_text(la)
        elif id in (pcbnew.F_Paste, pcbnew.B_Paste):
            is_paste = True
            la.draw = draw_mask
            text = la.type
        elif la.type == 'copper':
            la.draw = draw_copper
            text = get_copper_text(la)
        elif la.type == 'core':
            la.draw = draw_core
            text = get_dielectric_text("CORE", la)
        else:
            la.draw = draw_prepreg
            text = get_dielectric_text("Prepreg", la)
        la.description = sep_desc+text+sep_desc
        la.gerber_name = sep_gbr+os.path.basename(gerber.get(la.id, ''))+sep_gbr
        if is_paste:
            continue
        stackup.append(la)
    # Move the paste and measure texts
    max_len_desc = 0
    max_len_gerber = 0
    for la in GS.stackup:
        if la.id == pcbnew.F_Paste:
            stackup.insert(0, la)
        elif la.id == pcbnew.B_Paste:
            stackup.append(la)
        max_len_desc = max(max_len_desc, len(la.description))
        max_len_gerber = max(max_len_gerber, len(la.gerber_name))
    # Compute sizes
    layers = len(GS.stackup)
    logger.debug(f'- Rendering {layers} layers')
    row_h = int(height/layers)
    logger.debug(f'- Row height {GS.to_mm(row_h)} mm')
    total_rel_w = sum((c.width for c in cols))
    xpos_x = pos_x
    for c in cols:
        c.x = xpos_x
        c.w = int(c.width/total_rel_w*width)
        c.max_txt_w = 0
        c.font_w = 0
        if c.type == 'description':
            c.font_w = int(c.w/max_len_desc)
        elif c.type == 'gerber':
            c.font_w = int(c.w/max_len_gerber)
        xpos_x += c.w
    y = pos_y
    # Draw it
    draw_rect(g, pos_x, pos_y, width, height, tlayer, line_w=GS.from_mm(border))
    for la in stackup:
        for c in cols:
            if c.type == 'drawing':
                if la.draw is not None:
                    la.draw(g, c.x, y, c.w, row_h, tlayer)
            elif c.type == 'description':
                la.desc_o, w = draw_text(g, c.x, y, la.description, int(row_h/2), c.font_w, tlayer)
                c.max_txt_w = max(c.max_txt_w, w)
            elif c.type == 'gerber':
                la.gbr_o, w = draw_text(g, c.x, y, la.gerber_name, int(row_h/2), c.font_w, tlayer)
                c.max_txt_w = max(c.max_txt_w, w)
        y += row_h
    if first_height != last_height:
        for c in cols:
            if c.type == 'thickness':
                right = col_thick >= col_draw if c.side == 'auto' else c.side == 'right'
                draw_thickness(g, c.x, pos_y, c.w, row_h, first_height, last_height, tlayer, right)
    # The text is proportional, not monospaced, so we must adjust it
    for c in cols:
        if c.font_w:
            c.font_w = int(c.w/c.max_txt_w*c.font_w)
    for la in stackup:
        for c in cols:
            if c.type == 'description':
                la.desc_o.SetTextWidth(c.font_w)
            elif c.type == 'gerber':
                la.gbr_o.SetTextWidth(c.font_w)
    return True


def update_drawing(ops, parent):
    load_board()
    gerber = look_for_output(ops.gerber, 'gerber', parent, {'gerber'}) if ops.gerber else None
    if gerber:
        targets, _, _ = get_output_targets(ops.gerber, parent)
        gerber_names = {la._id: tg for la, tg in zip(Layer.solve(gerber.layers), targets)}
    else:
        gerber_names = {}
    logger.debug('Drawing stackup')
    # Look for the Stackup Table group
    for g in GS.board.Groups():
        if g.GetName() == ops.group_name:
            # Found the group
            x1, y1, x2, y2 = GS.compute_group_boundary(g)
            item = g.GetItems()[0]
            layer = item.GetLayer()
            logger.debug(f'- Found group @{GS.to_mm(x1)},{GS.to_mm(y1)} mm ({GS.to_mm(x2-x1)}x{GS.to_mm(y2-y1)} mm)'
                         f' layer {layer}')
            return update_drawing_group(g, x1, y1, x2-x1, y2-y1, layer, ops.border, gerber_names, ops._columns)
    g = pcbnew.PCB_GROUP(GS.board)
    g.SetName(ops.group_name)
    GS.board.Add(g)
    units = GS.global_units or 'mm'
    scale = GS.unit_name_to_scale_factor(units)
    width = int(ops.width/scale)
    height = int(ops.height/scale)
    pos_x = int(ops.pos_x/scale)
    pos_y = int(ops.pos_y/scale)
    logger.debug(f'- Creating group at @{ops.pos_x},{ops.pos_y} {units} ({ops.width}x{ops.height} {units})')
    return update_drawing_group(g, pos_x, pos_y, width, height, ops._layer, ops.border, gerber_names, ops._columns)


@pre_class
class Draw_Stackup(BasePreFlight):  # noqa: F821
    """ Draw Stackup
        Draw the PCB stackup. Needs KiCad 7 or newer.
        To specify the position and size of the drawing you can use two methods.
        You can specify it using the *pos_x*, *pos_y*, *width*, *height* and *layer* options.
        But you can also create a group called *kibot_stackup*. If you don't know how to
        create a group consult :ref:`create_group`. After running this preflight the rectangle
        will contain the stackup """
    def __init__(self):
        super().__init__()
        self._pcb_related = True
        with document:
            self.draw_stackup = DrawStackupOptions
            """ [boolean|dict=false] Use a boolean for simple cases or fine-tune its behavior """

    def __str__(self):
        v = self.draw_stackup
        if isinstance(v, bool):
            return super().__str__()
        return f'{self.type}: {v.enabled} ({[c.type for c in v._columns]})'

    def config(self, parent):
        super().config(parent)
        if isinstance(self.draw_stackup, bool):
            self._value = DrawStackupOptions()
            self._value.config(self)
        else:
            self._value = self.draw_stackup

    def apply(self):
        if not GS.ki7:
            raise KiPlotConfigurationError('The `draw_stackup` preflight needs KiCad 7 or newer')
        if not GS.stackup:
            raise KiPlotConfigurationError('Unable to find the stackup information')
        if update_drawing(self._value, self):
            GS.save_pcb()
