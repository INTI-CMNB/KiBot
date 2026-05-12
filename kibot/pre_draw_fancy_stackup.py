# -*- coding: utf-8 -*-
# Copyright (c) 2024 Nguyen Vincent
# Copyright (c) 2024 Salvador E. Tropea
# Copyright (c) 2024 Instituto Nacional de Tecnología Industrial
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)
# Contributed by Nguyen Vincent (@nguyen-v)
import os
from .error import KiPlotConfigurationError
from .gs import GS
from .kicad.pcb_draw_helpers import draw_rect, draw_line, draw_text, draw_poly, get_text_width
from .kiplot import load_board, get_output_targets, look_for_output
from .layer import Layer
from .optionable import Optionable
from .macros import macros, document, pre_class  # noqa: F401
from .misc import W_NOVIAS, W_STACKUP
from . import log
import pcbnew
logger = log.get_logger()
VALID_COLUMNS = {'material', 'layer', 'thickness', 'dielectric', 'layer_type', 'gerber'}
TITLES = {"drawing": "",  # no title for drawing
          "material": "Material",
          "layer": "Layer",
          "thickness": "Thickness",
          "dielectric": "Dielectric",
          "layer_type": "Type",
          "gerber": "Gerber",
          }


class SUColumnsFancy(Optionable):
    """ A column of data """
    def __init__(self):
        super().__init__()
        self._unknown_is_error = True
        with document:
            self.type = 'drawing'
            """ *[material,layer,thickness,dielectric,layer_type,gerber_extension] Type of column:
                - *material*: the layer material type (e.g. Copper, Prepreg)
                - *layer*: the layer name as seen in KiCad
                - *thickness*: the layer thickness
                - *dielectric*: the dielectric material (e.g. Solder Resist, FR4)
                - *layer_type*: the layer type (e.g. Paste Mask, Legend, Solder Mask, Signal, Dielectric)
                - *gerber_extension*: the file extension of the gerber if provided (e.g. GTP, GTO, GBR, GTL, G1) """
            self.width = 30
            """ *Relative width. Is computed automatically according to the defined group width """

    def __str__(self):
        return f'{self.type} {self.width}'


class DrawFancyStackupOptions(Optionable):
    """ Draw fancy stackup options """
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
            self.layer = 'Cmts.User'
            """ Layer used for the stackup. Only used when the group can't be found.
                Otherwise we use the layer for the first object in the group """
            self.group_name = 'kibot_fancy_stackup'
            """ Name for the group containing the drawings. If KiBot can't find it will create
                a new group at the specified coordinates for the indicated layer """
            self.gerber = ''
            """ *Name of the output used to generate the gerbers. This is needed only when you
                want to include the *gerber* column, containing the gerber file names """
            self.gerber_extension_only = True
            """ *Only display the gerber file extension instead of full gerber name """
            self.draw_stackup = True
            """ *Choose whether to display the stackup drawing or not """
            self.columns = SUColumnsFancy
            """ *[list(dict)|list(string)=?] List of columns to display.
                Can be just the name of the column.
                Available columns are *drawing*, *material*, *layer*, *thickness*, *dielectric*, *layer_type*, *gerber*.
                When empty KiBot will add them in the above order, skipping the *gerber* if not available """
            self.draw_vias = True
            """ Enable drawing vias (thru, blind, buried) in the stackup table"""
            self.drawing_border_spacing = 10
            """ Space (in number of characters) between stackup drawing borders and via drawings """
            self.stackup_to_text_lines_spacing = 3
            """ Space (in number of characters) between stackup drawing and stackup table """
            self.via_width = 4
            """ Width (in number of characters) of a via in the stackup drawing """
            self.via_spacing = 8
            """ Space (in number of characters) between vias in the stackup drawing """
            self.core_extra_spacing_ratio = 2
            """ Extra vertical space given to the core layers """
            self.layer_spacing = 3
            """ Space (in number of characters) between layers on the stackup table/drawing """
            self.column_spacing = 2
            """ Blank space (in number of characters) between columns in the stackup table """
            self.border_thickness = 0.15
            """ Thickness of the borders of stackup drawing and stackup table """
            self.note = ''
            """ Note to write at the bottom of the stackup table. Leave empty if no note is to be written """
        super().__init__()
        self._unknown_is_error = True

    def config(self, parent):
        super().config(parent)
        # Ensure we have a valid layer
        load_board()  # We need the board to know the layer names
        self._layer = Layer.solve(self.layer)[0]._id
        # Solve the columns
        # - Make a list
        def_columns = ['material', 'layer', 'thickness', 'dielectric', 'layer_type']
        if self.gerber:
            def_columns.append('gerber')
        self._columns = Optionable.force_list(self.columns, default=def_columns)
        # - Convert strings
        for c, col in enumerate(self._columns):
            if isinstance(col, str):
                o = SUColumnsFancy()
                o.type = col
                self._columns[c] = o
        # Drawings are only allowed at the left, so they are controlled by "draw_stackup"
        if self.draw_stackup:
            o = SUColumnsFancy()
            o.type = 'drawing'
            self._columns.insert(0, o)
        # - Sanity
        if not self._columns:
            raise KiPlotConfigurationError('No columns provided')


class SULayer:
    def __init__(self):
        self.material = ''
        self.layer = ''
        self.thickness = ''
        self.dielectric = ''
        self.layer_type = ''
        self.gerber = ''

    def __str__(self):
        return f"{self.layer} mat: {self.material} thick: {self.thickness} use: {self.layer_type} type: {self.type}"


def draw_core(g, x, y, w, h, layer, offset, border_w=10000):
    y = y-int(h*0.5)+offset
    h = int(h)
    draw_rect(g, x, y, w, h, layer, line_w=border_w)
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


def draw_prepreg(g, x, y, w, h, layer, offset, border_w=10000):
    y = y-int(h*0.5)+offset
    h = int(h)
    draw_rect(g, x, y, w, h, layer, line_w=border_w)
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


def draw_copper(g, x, y, w, h, layer, offset):
    y = y-int(h*0.5)+offset
    h = int(h)
    draw_rect(g, x, y, w, h, layer, filled=True)


def draw_mask_paste_silk(g, x, y, w, h, layer, offset, border_w=10000):
    y = y-int(h*0.5)+offset
    h = int(h)
    draw_rect(g, x, y, w, h, layer, filled=False, line_w=border_w)


def draw_normal_buried_via(g, x, y, w, h, tlayer, clearance, hole_size):
    draw_rect(g, int(x+clearance), y, int(w/2-clearance-hole_size/2), h, tlayer, filled=True)
    draw_rect(g, int(x+w/2+hole_size/2), y, int(w/2-clearance-hole_size/2), h, tlayer, filled=True)


def draw_microvia(g, x, y, w, h, tlayer, clearance, via_w, hole_size, via_annular_w, copper_cnt, type):
    GS.board.GetCopperLayerCount()
    if type == 'MT':
        left_points = []
        left_points.append((int(x+clearance), y))
        left_points.append((int(x+w/2-hole_size), y))
        left_points.append((int(x+w/2-hole_size/2), y+h))
        left_points.append((int(x+w/2-via_w/4+clearance), y+h))
        draw_poly(g, left_points, tlayer, filled=True)
        right_points = []
        right_points.append((int(via_annular_w+x-clearance), y))
        right_points.append((int(via_annular_w+x-w/2+hole_size), y))
        right_points.append((int(via_annular_w+x-w/2+hole_size/2), y+h))
        right_points.append((int(via_annular_w+x-w/2+via_w/4-clearance), y+h))
        draw_poly(g, right_points, tlayer, filled=True)
        left_filler = []
        left_filler.append((int(x), y))
        left_filler.append((int(x+w/2-via_w/4), y+h))
        left_filler.append((int(x), y+h))
        draw_poly(g, left_filler, tlayer, filled=True)
        right_filler = []
        right_filler.append((int(via_annular_w+x), y))
        right_filler.append((int(via_annular_w+x-w/2+via_w/4), y+h))
        right_filler.append((int(via_annular_w+x), y+h))
        draw_poly(g, right_filler, tlayer, filled=True)
    elif type == 'MB':
        left_points = []
        left_points.append((int(x+clearance), y+h))
        left_points.append((int(x+w/2-hole_size), y+h))
        left_points.append((int(x+w/2-hole_size/2), y))
        left_points.append((int(x+w/2-via_w/4+clearance), y))
        draw_poly(g, left_points, tlayer, filled=True)
        right_points = []
        right_points.append((int(via_annular_w+x-clearance), y+h))
        right_points.append((int(via_annular_w+x-w/2+hole_size), y+h))
        right_points.append((int(via_annular_w+x-w/2+hole_size/2), y))
        right_points.append((int(via_annular_w+x-w/2+via_w/4-clearance), y))
        draw_poly(g, right_points, tlayer, filled=True)
        left_filler = []
        left_filler.append((int(x), y+h))
        left_filler.append((int(x+w/2-via_w/4), y))
        left_filler.append((int(x), y))
        draw_poly(g, left_filler, tlayer, filled=True)
        right_filler = []
        right_filler.append((int(via_annular_w+x), y+h))
        right_filler.append((int(via_annular_w+x-w/2+via_w/4), y))
        right_filler.append((int(via_annular_w+x), y))
        draw_poly(g, right_filler, tlayer, filled=True)
    else:  # MS
        draw_rect(g, int(x+clearance), y, int(w-2*clearance), h, tlayer, filled=True)


def draw_via_column(g, x, y, w, h, tlayer, clearance, hole_size, hoffset):
    draw_rect(g, int(x+clearance), int(y-h/2+hoffset/2), int(w/2-clearance-hole_size/2), h, tlayer, filled=True)
    draw_rect(g, int(x+w/2+hole_size/2), int(y-h/2+hoffset/2), int(w/2-clearance-hole_size/2), h, tlayer, filled=True)


def get_material(la, la_type=''):
    if la_type == "copper" or la_type == "core":
        if la.type:
            return f"{la.type.title()}"
    elif la.material:
        return la.material
    return ''


def get_dielectric(la):
    if la.material:
        return f"{la.material}"
    return ''


def get_type(la, la_type):
    if la_type == "mask":
        return "Solder Mask"
    elif la_type == "silk":
        return "Legend"
    elif la_type == "paste":
        return "Paste Mask"
    elif la_type == "copper":
        copper_type = GS.board.GetLayerType(GS.board.GetLayerID(la.name))
        if copper_type == pcbnew.LT_SIGNAL or copper_type == pcbnew.LT_MIXED:
            return "Signal"
        elif copper_type == pcbnew.LT_POWER:
            return "Plane"
        return "Copper Layer"
    elif la_type == "core":
        return "Dielectric"
    return ''


def get_thickness(la, la_type=''):
    if la.thickness:
        thickness = str((la.thickness)/1000)+'mm'
        if la_type == "copper":
            oz = la.thickness/35
            if int(oz) == oz:
                oz = int(oz)
            return f"{thickness} ({oz:.2f}oz)"
        return thickness
    return ''


def get_name(la):
    if la.name:
        return GS.board.GetLayerName(GS.board.GetLayerID(la.name))
    return ''


def analyze_stackup(ops, gerber):
    stackup = []
    # Temporary storage for paste layers
    f_paste_layer = None
    b_paste_layer = None

    for la in GS.stackup:
        la.id = id = GS.board.GetLayerID(la.name)
        # Create a new Layer object for this iteration
        layer_obj = SULayer()
        layer_obj.type = la.type
        layer_obj.id = la.id

        if id in (pcbnew.F_SilkS, pcbnew.B_SilkS):
            layer_obj.layer = get_name(la)
            layer_obj.dielectric = get_dielectric(la)
            layer_obj.layer_type = get_type(la, "silk")
            layer_obj.draw = draw_mask_paste_silk

        elif id in (pcbnew.F_Mask, pcbnew.B_Mask):
            layer_obj.layer = get_name(la)
            layer_obj.thickness = get_thickness(la)
            layer_obj.dielectric = get_dielectric(la)
            layer_obj.layer_type = get_type(la, "mask")
            layer_obj.draw = draw_mask_paste_silk

        elif id in (pcbnew.F_Paste, pcbnew.B_Paste):
            # Temporarily store the paste layers instead of appending
            layer_obj.layer = get_name(la)
            layer_obj.layer_type = get_type(la, "paste")
            layer_obj.draw = draw_mask_paste_silk
            if id == pcbnew.F_Paste:
                f_paste_layer = layer_obj
            elif id == pcbnew.B_Paste:
                b_paste_layer = layer_obj
            continue  # Skip appending the paste layers for now

        elif la.type == 'copper':
            layer_obj.layer = get_name(la)
            layer_obj.material = get_material(la, "copper")
            layer_obj.thickness = get_thickness(la, "copper")
            layer_obj.layer_type = get_type(la, "copper")
            layer_obj.draw = draw_copper

        elif la.type == 'core':
            layer_obj.material = get_material(la, "core")
            layer_obj.thickness = get_thickness(la)
            layer_obj.dielectric = get_dielectric(la)
            layer_obj.layer_type = get_type(la, "core")
            layer_obj.draw = draw_core

        else:
            layer_obj.material = get_material(la, "core")
            layer_obj.thickness = get_thickness(la)
            layer_obj.dielectric = get_dielectric(la)
            layer_obj.layer_type = get_type(la, "core")
            layer_obj.draw = draw_prepreg

        layer_obj.gbr_name = os.path.basename(gerber.get(la.id, ''))
        layer_obj.gbr_extension = os.path.splitext(layer_obj.gbr_name)[-1][1:].upper() if '.' in layer_obj.gbr_name else ''

        if ops.gerber_extension_only:
            layer_obj.gerber = layer_obj.gbr_extension
        else:
            layer_obj.gerber = layer_obj.gbr_name

        # Append the created layer object to the stackup list
        stackup.append(layer_obj)

    # At the end, append the F_Paste to the top and B_Paste to the bottom if they exist
    if f_paste_layer:
        stackup.insert(0, f_paste_layer)  # Insert F_Paste at the beginning

    if b_paste_layer:
        stackup.append(b_paste_layer)  # Append B_Paste at the end
    return stackup


def measure_table(ops, gerber, via_layer_pairs, stackup, font=None):
    # Set the maximum length of each column to the column title for now
    for c in ops._columns:
        c.title = TITLES[c.type]
        c.max_len = get_text_width(c.title, font=font)
        if c.type == 'gerber' and gerber == {}:
            c.max_len = 0

    col_spacing_width = get_text_width(' ', font=font)*ops.column_spacing

    # Compute maximum width of each column according to stackup data
    for c in ops._columns:
        for layer in stackup:
            bold = (layer.material == "Copper")
            if c.type == 'material':
                c.max_len = max(c.max_len, get_text_width(layer.material, bold=bold, font=font))
            elif c.type == 'layer':
                c.max_len = max(c.max_len, get_text_width(layer.layer, bold=bold, font=font))
            elif c.type == 'thickness':
                c.max_len = max(c.max_len, get_text_width(layer.thickness, bold=bold, font=font))
            elif c.type == 'dielectric':
                c.max_len = max(c.max_len, get_text_width(layer.dielectric, bold=bold, font=font))
            elif c.type == 'layer_type':
                c.max_len = max(c.max_len, get_text_width(layer.layer_type, bold=bold, font=font))
            elif c.type == 'gerber' and gerber != {}:
                c.max_len = max(c.max_len, get_text_width(layer.gerber, bold=bold, font=font))
        if (c.type == 'gerber') and (gerber == {}):
            continue
        else:
            c.max_len += col_spacing_width   # add some space between columns

    # compute stackup drawing length from the vias configuration
    for c in ops._columns:
        if c.type == 'drawing':
            c.width_char = ops.stackup_to_text_lines_spacing + 2*ops.drawing_border_spacing
            if ops.draw_vias:
                c.width_char += (len(via_layer_pairs)-1)*ops.via_spacing
            c.max_len = get_text_width(' ' * c.width_char, font=font)

    # Compute total width of table:
    tot_len = sum(c.max_len for c in ops._columns)

    # Compute the approximate number of characters per column and relative width
    for c in ops._columns:
        if c.type != 'drawing':
            c.width_char = int(c.max_len/get_text_width(' ', font=font))
        c.width = c.max_len/tot_len


def update_drawing_group(g, pos_x, pos_y, width, tlayer, ops, gerber, via_layer_pairs):

    font = None

    for item in g.GetItems():
        if not isinstance(item, pcbnew.PCB_TEXTBOX):
            GS.board.Delete(item)
        else:
            font = item.GetFont()

    # Analyze the stackup
    stackup = analyze_stackup(ops, gerber)
    measure_table(ops, gerber, via_layer_pairs, stackup, font)

    # Draw the stackup
    total_rel_w = sum((c.width for c in ops._columns))  # should be equal to 1

    # Font width must be multiplied by a correcting factor (?)
    font_w = int(10000*width*ops._columns[0].width/total_rel_w/ops._columns[0].max_len)
    col_spacing_width = get_text_width(' ', w=font_w, font=font)*ops.column_spacing

    xpos_x = int(pos_x + col_spacing_width/2)
    draw_w = 0
    draw_width_char = 0
    stack_draw_w = 0
    stack_draw_width_char = 0
    for c in ops._columns:
        c.x = xpos_x
        c.w = int(c.width/total_rel_w*width)
        xpos_x += c.w
        if c.type == 'drawing':
            draw_w = c.w
            draw_width_char = c.width_char
            stack_draw_w = draw_w - int(ops.stackup_to_text_lines_spacing/draw_width_char*draw_w)
            stack_draw_width_char = draw_width_char - ops.stackup_to_text_lines_spacing
    y = pos_y

    # Draw table text
    row_h = ops.layer_spacing*font_w

    core_extra_padding = int(row_h*(ops.core_extra_spacing_ratio-1)/2)

    y += int(row_h/2) + row_h  # space for top rule + column titles
    for layer in stackup:
        layer.width = row_h
        if layer.material == "Core":
            y += core_extra_padding
            layer.width += core_extra_padding
        layer.y = y
        for c in ops._columns:
            bold = (layer.material == "Copper")
            if c.type == 'material':
                draw_text(g, c.x, y, layer.material, font_w, font_w, tlayer, bold, font=font)
            elif c.type == 'layer':
                draw_text(g, c.x, y, layer.layer, font_w, font_w, tlayer, bold, font=font)
            elif c.type == 'thickness':
                draw_text(g, c.x, y, layer.thickness, font_w, font_w, tlayer, bold, font=font)
            elif c.type == 'dielectric':
                draw_text(g, c.x, y, layer.dielectric, font_w, font_w, tlayer, bold, font=font)
            elif c.type == 'layer_type':
                draw_text(g, c.x, y, layer.layer_type, font_w, font_w, tlayer, bold, font=font)
            elif c.type == 'gerber':
                draw_text(g, c.x, y, layer.gerber, font_w, font_w, tlayer, bold, font=font)
        y += row_h
        if layer.material == "Core":
            y += core_extra_padding

    # Get the x-coordinate of the first column
    table_x = pos_x + draw_w
    table_w = width - (table_x - pos_x)
    table_h = y - pos_y

    # Draw invisible box to get repeatable group sizes across runs
    draw_rect(g, pos_x, pos_y, width, table_h, tlayer, line_w=0)

    # Draw table box
    draw_rect(g, table_x, pos_y + row_h, table_w, table_h - row_h, tlayer, line_w=GS.from_mm(ops.border_thickness))

    # Draw text titles
    for c in ops._columns:
        draw_text(g, c.x, int(pos_y + font_w/2), c.title, font_w, font_w, tlayer, font=font)

    # Draw thickness
    ds = GS.board.GetDesignSettings()
    draw_text(g, table_x, int(pos_y + table_h + font_w/2), f"Total thickness: {GS.to_mm(ds.GetBoardThickness())}mm",
              font_w, font_w, tlayer, font=font)

    # Draw note
    if ops.note != '':
        draw_text(g, table_x, int(pos_y + table_h + font_w/2 + 2*font_w),
                  "Note: " + ops.note, font_w, font_w, tlayer, font=font)

    if not ops.draw_stackup:
        return True
    # Draw lines between stackup drawing and table
    for layer in stackup:
        draw_line(g, pos_x+stack_draw_w, layer.y+font_w, table_x, layer.y+font_w, tlayer)

    mat = create_stackup_matrix(stackup, via_layer_pairs, ops.draw_vias)

    via_w = ops.via_width/(stack_draw_width_char)*stack_draw_w
    via_hole_w = via_w/6
    microvia_hole_w = via_w/10
    via_hole_outer_w = via_w/2
    via_annular_w = via_hole_outer_w*1.5
    clearance = via_w/15
    via_sp_w = ops.via_spacing/(stack_draw_width_char)*stack_draw_w
    border_w = ops.drawing_border_spacing/stack_draw_width_char*stack_draw_w

    copper_cnt = 0
    for i, layer in enumerate(stackup):
        if layer.type == 'copper':
            copper_cnt += 1
        x = pos_x
        w = border_w
        init_draw = mat[i][0]
        for j, draw in enumerate(mat[i]):
            if j > 0:
                offset = 0
                if draw == init_draw and j != len(mat[i])-1 and draw == '':
                    if (j % 2) == 0:
                        w += via_sp_w
                elif draw != init_draw or j == len(mat[i])-1:
                    if j == len(mat[i])-1:
                        w += border_w
                    elif draw == 'T' or draw == 'B':  # normal and buried via
                        offset = via_annular_w
                        draw_normal_buried_via(g, x+w-offset/2, int(layer.y + font_w/2), offset, font_w, tlayer, clearance,
                                               via_hole_w)
                    elif draw == 'MT' or draw == 'MB' or draw == 'MS':  # micro-via
                        offset = via_annular_w
                        draw_microvia(g, x+w-offset/2, int(layer.y + font_w/2), offset, font_w, tlayer, clearance, via_w,
                                      microvia_hole_w, via_annular_w, copper_cnt, draw)
                    elif draw == 'M':  # normal and buried via
                        offset = via_hole_outer_w
                        draw_via_column(g, x+w-offset/2, int(layer.y + font_w/2), offset, 2*layer.width-font_w, tlayer,
                                        clearance, via_hole_w, font_w)
                    elif draw == 'MM':  # micro-via
                        offset = via_hole_outer_w
                        draw_via_column(g, x+w-offset/2, int(layer.y + font_w/2), offset, 2*layer.width-font_w, tlayer,
                                        clearance, microvia_hole_w, font_w)
                    w -= offset/2
                    if layer.type == 'copper':
                        layer.draw(g, int(x), int(layer.y), int(w), font_w, tlayer, font_w)
                    elif layer.type == 'core':
                        layer.draw(g, int(x), int(layer.y), int(w), 2*ops.core_extra_spacing_ratio*font_w, tlayer, font_w,
                                   GS.from_mm(ops.border_thickness))
                    elif layer.type == 'prepreg':
                        layer.draw(g, int(x), int(layer.y), int(w), 2*font_w, tlayer, font_w, GS.from_mm(ops.border_thickness))
                    elif layer.id in (pcbnew.F_SilkS, pcbnew.B_SilkS):
                        layer.draw(g, int(x), int(layer.y), int(w), font_w/2, tlayer, font_w, GS.from_mm(ops.border_thickness))
                    elif layer.id in (pcbnew.F_Mask, pcbnew.B_Mask):
                        layer.draw(g, int(x), int(layer.y), int(w), font_w/2, tlayer, font_w, GS.from_mm(ops.border_thickness))
                    elif layer.id in (pcbnew.F_Paste, pcbnew.B_Paste):
                        layer.draw(g, int(x), int(layer.y), int(w), font_w/2, tlayer, font_w, GS.from_mm(ops.border_thickness))
                    x += w + offset
                    w = -offset/2
                    if j < len(mat[i])-1:
                        init_draw = mat[i][j+1]
    return True


def create_stackup_matrix(stackup, via_layer_pairs, draw_vias):
    mat = []  # This will hold the matrix (list of lists)
    i = 0  # Track the current layer index
    before_core = True

    for la in stackup:
        if la.type == 'core':
            before_core = False
        # Create a row with empty strings (instead of zeros or numbers)
        if draw_vias:
            mat_row = [''] * (len(via_layer_pairs) * 2 + 1)
        else:
            mat_row = ['']*3
        th_or_bl = ({GS.VIATYPE_THROUGH, GS.VIATYPE_BLIND, GS.VIATYPE_BURIED} if GS.ki10 else
                    {GS.VIATYPE_THROUGH, GS.VIATYPE_BLIND_BURIED})
        if draw_vias:
            # Loop through each via layer pair
            for j, via_list in enumerate(via_layer_pairs):
                for via in via_list:
                    # Get the via type
                    via_type = via.GetViaType()
                    via_top_layer = get_layer_number(stackup, via.TopLayer())
                    via_bottom_layer = get_layer_number(stackup, via.BottomLayer())

                    # Determine if the current layer corresponds to the top, middle, or bottom of the via
                    if i == via_top_layer:
                        # Top layer of the via
                        if via_type in th_or_bl:
                            mat_row[2 * j + 1] = 'T'
                        elif via_type == GS.VIATYPE_MICROVIA:
                            mat_row[2 * j + 1] = 'MT' if before_core else 'MS'

                    elif i > via_top_layer and i < via_bottom_layer:
                        # Middle layer of the via
                        if via_type in th_or_bl:
                            mat_row[2 * j + 1] = 'M'
                        elif via_type == GS.VIATYPE_MICROVIA:
                            mat_row[2 * j + 1] = 'MM' if la.type != 'copper' else ('MT' if before_core else 'MB')

                    elif i == via_bottom_layer:
                        # Bottom layer of the via
                        if via_type in th_or_bl:
                            mat_row[2 * j + 1] = 'B'
                        elif via_type == GS.VIATYPE_MICROVIA:
                            mat_row[2 * j + 1] = 'MS' if before_core else 'MB'

        # Move to the next layer in the stackup
        i += 1
        mat.append(mat_row)

    return mat  # Return the populated matrix


def get_layer_number(stackup, number):
    copper_num = GS.copper_layer_to_ordinal(number)

    i = 0
    for n, layer in enumerate(stackup):
        if layer.type == 'copper':
            if i == copper_num:
                return n
            i += 1
    logger.warning(W_STACKUP+f"Wrong stack up? (layer id: {number} not found)")
    return n


def update_drawing(ops, parent):
    load_board()
    gerber = look_for_output(ops.gerber, 'gerber', parent, {'gerber'}) if ops.gerber else None
    if gerber:
        targets, _, _ = get_output_targets(ops.gerber, parent)
        gerber_names = {la._id: tg for la, tg in zip(Layer.solve(gerber.layers), targets)}
    else:
        gerber_names = {}
    logger.debug('Drawing stackup')
    # Construct list of vias types
    via_layer_pairs = None
    if ops.draw_vias:
        via_layer_pairs = compute_via_layer_pairs(ops)

    for g in GS.board.Groups():
        if g.GetName() == ops.group_name:
            # Found the group
            x1, y1, x2, y2 = GS.compute_group_boundary(g)
            item = g.GetItems()[0]
            layer = item.GetLayer()
            logger.debug(f'- Found group @{GS.to_mm(x1)},{GS.to_mm(y1)} mm ({GS.to_mm(x2-x1)}x{GS.to_mm(y2-y1)} mm)'
                         f' layer {layer}')
            return update_drawing_group(g, x1, y1, x2-x1, layer, ops, gerber_names, via_layer_pairs)
    g = pcbnew.PCB_GROUP(GS.board)
    g.SetName(ops.group_name)
    GS.board.Add(g)
    units = GS.global_units or 'mm'
    scale = GS.unit_name_to_scale_factor(units)
    width = int(ops.width/scale)
    pos_x = int(ops.pos_x/scale)
    pos_y = int(ops.pos_y/scale)
    logger.debug(f'- Creating group at @{ops.pos_x},{ops.pos_y} {units} (w: {ops.width} {units})')
    return update_drawing_group(g, pos_x, pos_y, width, ops._layer, ops, gerber_names, via_layer_pairs)


def compute_via_layer_pairs(ops):
    # Get the total number of copper layers in the board
    last_layer = GS.board.GetCopperLayerCount() - 1
    # Initialize a list to store the unique vias and their pairs
    via_layer_pairs = []
    # Dictionary to track unique vias: Key is a tuple (via type, top layer, bottom layer), value is the via object
    unique_vias = {}

    # Helper function to check symmetry in the stackup, considering the special case of the back layer being index 31
    def are_layers_symmetric(top1, bottom1, top2, bottom2):
        # Make sure via 1 is "on top" of via 2
        if top1 > top2:
            top1, bottom1, top2, bottom2 = top2, bottom2, top1, bottom1
        # Handle the special case where the back layer index is 31
        if bottom1 == pcbnew.B_Cu:
            bottom1 = last_layer
        if bottom2 == pcbnew.B_Cu:
            bottom2 = last_layer

        # Now check if the layers are symmetric in the stackup
        # Avoid overlap
        return top1 == (last_layer - bottom2) and bottom1 == (last_layer - top2) and bottom1 < top2

    # A set to track vias that have been paired, using their (type, top_layer, bottom_layer) key
    paired_vias = set()

    # Iterate through all vias in the board
    for via in GS.board.GetTracks():
        # Check if the current track is a via
        if not isinstance(via, pcbnew.PCB_VIA):
            continue
        # Extract via details: type, top layer, and bottom layer
        via_type = via.GetViaType()
        top_layer = via.TopLayer()
        bottom_layer = via.BottomLayer()

        # Sort the layers to ensure consistency (for uniqueness checks)
        if top_layer > bottom_layer:
            top_layer, bottom_layer = bottom_layer, top_layer

        # Check if this via is already in the unique_vias dictionary
        via_key = (via_type, top_layer, bottom_layer)

        if via_key in unique_vias:
            # If the via is already unique, ignore it
            continue
        # Try to find a symmetrical pair
        found_pair = False
        for (other_type, other_top, other_bottom), other_via in unique_vias.items():
            # Check if the other via is symmetrical and of the same type
            if other_type == via_type and are_layers_symmetric(top_layer, bottom_layer, other_top, other_bottom):
                # Add the symmetrical pair as a list of two vias
                via_layer_pairs.append([other_via, via])
                paired_vias.add((other_type, other_top, other_bottom))  # Mark the other via as paired
                paired_vias.add(via_key)                                # Mark this via as paired
                found_pair = True
                break

        # If no symmetrical pair is found, store the via for future pairing
        if not found_pair:
            unique_vias[via_key] = via

    if not len(unique_vias):
        if ops.get_user_defined('draw_vias'):
            logger.warning(W_NOVIAS+'No vias detected, disabling the `draw_vias` option')
        ops.draw_vias = False

    # Add remaining unpaired vias as lists of single elements
    for key, remaining_via in unique_vias.items():
        if key not in paired_vias:
            via_layer_pairs.append([remaining_via])

    # Define the priority of via types for sorting
    if GS.ki10:
        VIA_TYPE_PRIORITY = {GS.VIATYPE_THROUGH: 0,         # VIATYPE_THROUGH first
                             GS.VIATYPE_BLIND: 1,           # VIATYPE_BLIND second
                             GS.VIATYPE_BURIED: 2,          # VIATYPE_BURIED third
                             GS.VIATYPE_MICROVIA: 3         # VIATYPE_MICROVIA fourth
                             }
    else:
        VIA_TYPE_PRIORITY = {GS.VIATYPE_THROUGH: 0,         # VIATYPE_THROUGH first
                             GS.VIATYPE_BLIND_BURIED: 1,    # VIATYPE_BLIND_BURIED second
                             GS.VIATYPE_MICROVIA: 2         # VIATYPE_MICROVIA third
                             }

    # Sort the list of via pairs by the via type, top layer, and bottom layer
    via_layer_pairs.sort(key=lambda pair: (VIA_TYPE_PRIORITY[pair[0].GetViaType()],  # First, by via type priority
                                           pair[0].TopLayer(),       # Then, by the top layer (smallest first)
                                           pair[0].BottomLayer()))   # Finally, by the bottom layer (smallest first)
    return via_layer_pairs


@pre_class
class Draw_Fancy_Stackup(BasePreFlight):  # noqa: F821
    """ Draw Fancy Stackup
        Draw the PCB stackup. Needs KiCad 7 or newer.
        To specify the position and size of the drawing you can use two methods.
        You can specify it using the *pos_x*, *pos_y*, *width* and *layer* options.
        But you can also create a group called *kibot_fancy_stackup*. If you don't know how to
        create a group consult :ref:`create_group`. After running this preflight the rectangle
        will contain the stackup.
        Note that the height is not determined by the group height, but by the number
        of layers and spacing between layers. """
    def __init__(self):
        super().__init__()
        self._pcb_related = True
        with document:
            self.draw_fancy_stackup = DrawFancyStackupOptions
            """ [boolean|dict=false] Use a boolean for simple cases or fine-tune its behavior """

    def __str__(self):
        v = self.draw_fancy_stackup
        if isinstance(v, bool):
            return super().__str__()
        return f'{self.type}: {v.enabled} ({[c.type for c in v._columns]})'

    def config(self, parent):
        super().config(parent)
        if isinstance(self.draw_fancy_stackup, bool):
            self._value = DrawFancyStackupOptions()
            self._value.config(self)
        else:
            self._value = self.draw_fancy_stackup

    def apply(self):
        if not GS.ki7:
            raise KiPlotConfigurationError('The `draw_fancy_stackup` preflight needs KiCad 7 or newer')
        if not GS.stackup:
            raise KiPlotConfigurationError('Unable to find the stackup information')
        if update_drawing(self._value, self):
            GS.save_pcb()
