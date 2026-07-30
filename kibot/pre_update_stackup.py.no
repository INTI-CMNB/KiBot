# -*- coding: utf-8 -*-
# Copyright (c) 2024 Salvador E. Tropea
# Copyright (c) 2024 Instituto Nacional de Tecnología Industrial
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)
from collections import OrderedDict
from .error import KiPlotConfigurationError
from .gs import GS
from .kiplot import load_board
from .misc import W_UPSTKUPTOO
from .macros import macros, document, pre_class  # noqa: F401
from . import log
import pcbnew
logger = log.get_logger()


def add_line(x1l, x2l, yl, table_layer, line_w, g):
    nl = pcbnew.PCB_SHAPE(GS.board)
    pos = nl.GetStart()
    pos.x = x1l
    pos.y = yl
    nl.SetStart(pos)
    pos = nl.GetEnd()
    pos.x = x2l
    pos.y = yl
    nl.SetEnd(pos)
    nl.SetLayer(table_layer)
    nl.SetWidth(line_w)
    g.AddItem(nl)
    GS.board.Add(nl)


def add_row_texts(ref_cell, columns_x, y, table_layer, g):
    row_cels = []
    # Make a row
    for c in range(7):
        # Create a cell
        nt = pcbnew.PCB_TEXT(GS.board)
        nt.SetAttributes(ref_cell)
        nt.SetText('bogus')
        pos = nt.GetPosition()
        pos.x = columns_x[c]
        pos.y = y
        nt.SetPosition(pos)
        nt.SetLayer(table_layer)
        g.AddItem(nt)
        GS.board.Add(nt)
        row_cels.append(nt)
    return row_cels


def update_table_group(g):
    updated = False
    # Sort the items by position
    items = sorted(g.GetItems(), key=lambda x: (x.GetY(), x.GetX()))
    # Separate the text elements
    texts = OrderedDict()
    for item in items:
        if isinstance(item, pcbnew.PCB_TEXT):
            texts.setdefault(item.GetY(), []).append(item)
    # Separate the lines
    hlines = []
    vlines = []
    for item in items:
        if isinstance(item, pcbnew.PCB_SHAPE):
            start = item.GetStart()
            end = item.GetEnd()
            if start.x == end.x:
                vlines.append(item)
            else:
                hlines.append(item)
    # Get the size of the table
    rows = len(texts)
    columns = len(next(iter(texts.values())))
    if columns != 7:
        raise KiPlotConfigurationError(f'Stackup should have 7 columns, not {columns}')
    if len(vlines) != 8:
        raise KiPlotConfigurationError(f'The table should contain 8 vertical lines, not {len(vlines)}')
    if rows < 3:
        raise KiPlotConfigurationError("Stackup with just 1 layer isn't supported")
    if len(hlines) != rows+1:
        raise KiPlotConfigurationError(f'The table should contain {rows+1} horizontal lines, not {len(hlines)}')
    stackup_rows = rows-1
    logger.debug(f'- {stackup_rows} stackup rows (+header)')
    columns_x = None
    rows_y = []
    # Sanity check
    for y, txts in texts.items():
        if columns_x is None:
            # Memorize the X for each column
            columns_x = tuple(t.GetX() for t in txts)
            column_names = tuple(t.GetText() for t in txts)
            table_layer = txts[0].GetLayer()
        else:
            # Check the columns has the same X coordinate
            ref_cell = txts[0]
            if len(txts) != len(columns_x):
                raise KiPlotConfigurationError('Not all rows has the same number of columns')
            if not all((txt.GetX() == col for txt, col in zip(txts, columns_x))):
                raise KiPlotConfigurationError('Column items not aligned')
        rows_y.append(y)
        if not all((t.GetY() == y for t in txts)):
            raise KiPlotConfigurationError('Row items not aligned')
    logger.debug(f'- Column names: {column_names}')
    logger.debug(f'- Column positions: {columns_x}')
    logger.debug(f'- Row positions: {rows_y}')
    header_height = rows_y[1]-rows_y[0]
    row_height = rows_y[2]-rows_y[1]
    logger.debug(f'- Header height: {header_height}')
    logger.debug(f'- Row height: {row_height}')
    prev_y = rows_y[1]
    for y in rows_y[2:]:
        if y-prev_y != row_height:
            raise KiPlotConfigurationError('Not all rows has the same height')
        prev_y = y
    # Here we know we have a 7 columns table with at least 2 layers + header
    # We also know all columns and rows are aligned and all layer rows has the same height
    new_rows = len(GS.stackup)+1
    # Check if we need to adjust the size
    if new_rows != rows:
        # We have new layers/One or more layers removed
        # Make the rows smaller/bigger
        added_layers = new_rows-rows
        if added_layers > 0:
            logger.debug(f'- Adding {added_layers} layer/s')
        else:
            logger.debug(f'- Removing {-added_layers} layer/s')
        total_h = header_height+row_height*stackup_rows
        aspect = header_height/row_height
        new_row_height = round(total_h/(aspect+stackup_rows+added_layers))
        new_header_height = round(new_row_height*aspect)
        logger.debug(f'- New header height: {new_header_height}')
        logger.debug(f'- New row height: {new_row_height}')
        scale = new_row_height/row_height
        font_aspect = ref_cell.GetTextHeight()/ref_cell.GetTextWidth()*scale
        logger.debug(f'- Aspect ratio for the font: {font_aspect}')
        # Check if we are creating too small/tall fonts
        do_warn = False
        if font_aspect < 0.67:
            msg = 'Shrinking'
            do_warn = True
        elif font_aspect > 1.33:
            msg = 'Enlarging'
            do_warn = True
        if do_warn:
            logger.warning(f'{W_UPSTKUPTOO}{msg} the stackup table font too much,'
                           ' please consider manually inserting it again')
        # Scale and move the text
        y = rows_y[0]
        ref_line = hlines[0]
        yl = ref_line.GetStart().y
        x1l = ref_line.GetStart().x
        x2l = ref_line.GetEnd().x
        line_w = ref_line.GetWidth()
        first = True
        for txts, hline in zip(texts.values(), hlines[1:]):
            for t in txts:
                t.SetTextHeight(int(t.GetTextHeight()*scale))
                pos = t.GetPosition()
                pos.y = y
                t.SetPosition(pos)
            if first:
                first = False
                y += new_header_height
                yl += new_header_height
            else:
                y += new_row_height
                yl += new_row_height
            # Move the corresponding line
            pos = hline.GetStart()
            pos.y = yl
            hline.SetStart(pos)
            pos = hline.GetEnd()
            pos.y = yl
            hline.SetEnd(pos)
        if added_layers > 0:
            # Add the new rows
            for _ in range(added_layers):
                # Add this row
                rows_y.append(y)
                texts[y] = add_row_texts(ref_cell, columns_x, y, table_layer, g)
                y += new_row_height
                yl += new_row_height
                # Add a line
                add_line(x1l, x2l, yl, table_layer, line_w, g)
        else:
            # Remove the extra rows
            for ln in hlines[added_layers:]:
                GS.board.Delete(ln)
            for r in rows_y[added_layers:]:
                for txt in texts[r]:
                    GS.board.Delete(txt)
    # Collect the data for thew new table
    layers = []
    for layer in GS.stackup:
        # 'Layer Name', 'Type', 'Material', 'Thickness (mm)', 'Color', 'Epsilon R', 'Loss Tangent'
        id = GS.board.GetLayerID(layer.name)
        is_silk = id in (pcbnew.F_SilkS, pcbnew.B_SilkS)
        is_mask = id in (pcbnew.F_Mask, pcbnew.B_Mask)
        name = GS.board.GetLayerName(id) if id >= 0 else layer.name.split()[0].capitalize()
        type = layer.type
        material = layer.material if layer.material is not None else ('Not specified' if is_silk or is_mask else '')
        thickness = str(layer.thickness/1000 if layer.thickness else 0)+' mm'
        color = layer.color if layer.color is not None else ('Not specified' if is_silk or is_mask or id < 0 else '')
        epsilon_r = layer.epsilon_r if layer.epsilon_r is not None else (3.3 if is_mask else 1)
        loss_tangent = layer.loss_tangent if layer.loss_tangent else 0
        layers.append((name, type, material, thickness, color, str(epsilon_r), str(loss_tangent)))
    # Replace the cells
    for r, (y, new_row) in enumerate(zip(rows_y[1:], layers)):
        row = texts[y]
        for c, (cell, new_txt) in enumerate(zip(row, new_row)):
            old_txt = cell.GetText()
            if old_txt != new_txt:
                cell.SetText(new_txt)
                logger.debug(f'- Replacing cell {r+1},{c+1} `{old_txt}` -> `{new_txt}`')
                updated = True
    return updated


def update_table():
    logger.debug('Stackup table')
    # Look for the Stackup Table group
    for g in GS.board.Groups():
        if g.GetName() == 'group-boardStackUp':
            # Found the group
            return update_table_group(g)
    logger.non_critical_error("Trying to update the stackup table, but couldn't find it")
    return False


@pre_class
class Update_Stackup(BasePreFlight):  # noqa: F821
    """ Update Stackup
        Update the information in the Stackup Table.
        Starting with KiCad 7 you can paste a block containing board information using
        *Place* -> *Stackup Table*. But this information is static, so if
        you modify anything related to it the block will be obsolete.
        This preflight tries to refresh the information """
    def __init__(self):
        super().__init__()
        self._pcb_related = True
        with document:
            self.update_stackup = False
            """ Enable this preflight """

    def v2str(self, v):
        return pcbnew.StringFromValue(self.pcb_iu, self.pcb_units, v, True)

    def apply(self):
        if not GS.ki7:
            raise KiPlotConfigurationError('The `update_stackup` preflight needs KiCad 7 or newer')
        load_board()
        if not GS.stackup:
            raise KiPlotConfigurationError('Unable to find the stackup information')
        # Collect the information
        if update_table():
            GS.save_pcb()
