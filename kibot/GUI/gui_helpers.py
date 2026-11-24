# -*- coding: utf-8 -*-
# Copyright (c) 2024 Salvador E. Tropea
# Copyright (c) 2024 Instituto Nacional de Tecnologïa Industrial
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)
#
# Helper functions to make the GUI code simpler

import difflib
import wx
from . import gui_config
from .gui_inject import create_id, InjectDialog
from .. import log
from typing import Optional

logger = log.get_logger()
# loaded_btns = {}
emp_font = None
SIZER_FLAGS_0 = SIZER_FLAGS_1 = SIZER_FLAGS_0_NO_BORDER = SIZER_FLAGS_1_NO_BORDER = None
SIZER_FLAGS_0_NO_EXPAND = SIZER_FLAGS_1_NO_EXPAND = None
USER_EDITED_COLOR = None


def init_vars():
    global emp_font, SIZER_FLAGS_0, SIZER_FLAGS_1, SIZER_FLAGS_0_NO_BORDER, SIZER_FLAGS_1_NO_BORDER, SIZER_FLAGS_0_NO_EXPAND
    global SIZER_FLAGS_1_NO_EXPAND, USER_EDITED_COLOR
    emp_font = wx.Font(70, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, True)
    SIZER_FLAGS_0 = wx.SizerFlags().Expand().Border(wx.ALL).CentreVertical()
    SIZER_FLAGS_1 = wx.SizerFlags(1).Expand().Border(wx.ALL).CentreVertical()
    SIZER_FLAGS_0_NO_EXPAND = wx.SizerFlags().Border(wx.ALL).CentreVertical()
    SIZER_FLAGS_1_NO_EXPAND = wx.SizerFlags(1).Border(wx.ALL).CentreVertical()
    SIZER_FLAGS_0_NO_BORDER = wx.SizerFlags().Expand().CentreVertical()
    SIZER_FLAGS_1_NO_BORDER = wx.SizerFlags(1).Expand().CentreVertical()
    USER_EDITED_COLOR = wx.Colour(gui_config.USER_EDITED_COLOR)


# def _get_btn_bitmap(bitmap):
#     path = os.path.join(GS.get_resource_path('images'), 'buttons', bitmap)
#     png = wx.Bitmap(path, wx.BITMAP_TYPE_PNG)
#     return wx.BitmapBundle(png)
#
#
# def get_btn_bitmap(name):
#     bitmap = 'btn-'+name+'.png'
#     bmp = loaded_btns.get(bitmap, None)
#     if bmp is None:
#         bmp = _get_btn_bitmap(bitmap)
#         loaded_btns[bitmap] = bmp
#     return bmp


class MessageDialog(InjectDialog):
    def __init__(self, msg, title, icon=None, ok_btn=True, name: Optional[str] = None):
        InjectDialog.__init__(self, None, title=title, name=name,
                              style=wx.DEFAULT_DIALOG_STYLE | wx.STAY_ON_TOP | wx.BORDER_DEFAULT)
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        msg_sizer = wx.BoxSizer(wx.HORIZONTAL)
        if icon is not None:
            sz = self.GetTextExtent('M')*2
            sz.height = -1
            bmp = wx.StaticBitmap(self, bitmap=get_res_bitmap(icon, sz))
            msg_sizer.Add(bmp, SIZER_FLAGS_0)
        if msg:
            txt = wx.StaticText(self, label=msg, style=wx.ALIGN_LEFT)
            msg_sizer.Add(txt, SIZER_FLAGS_1_NO_EXPAND)
        main_sizer.Add(msg_sizer, SIZER_FLAGS_1)
        m_but_sizer = wx.StdDialogButtonSizer()
        if ok_btn:
            m_but_sizer.AddButton(wx.Button(self, wx.ID_OK))
        else:
            but_yes = wx.Button(self, wx.ID_YES)
            but_no = wx.Button(self, wx.ID_NO)
            m_but_sizer.AddButton(but_yes)
            m_but_sizer.AddButton(but_no)
            but_yes.Bind(wx.EVT_BUTTON, self.OnYes)
            but_no.Bind(wx.EVT_BUTTON, self.OnNo)
        m_but_sizer.Realize()
        main_sizer.Add(m_but_sizer, SIZER_FLAGS_0)
        self.SetSizer(main_sizer)
        main_sizer.Fit(self)
        self.Centre(wx.BOTH)
        self.Bind(wx.EVT_CHAR_HOOK, self.OnKeyUP)

    def OnYes(self, event):
        self.EndModal(wx.YES)

    def OnNo(self, event):
        self.EndModal(wx.NO)

    def OnKeyUP(self, event):
        keyCode = event.GetKeyCode()
        if keyCode == wx.WXK_ESCAPE:
            self.EndModal(wx.CANCEL)
        event.Skip()


def MessageBox(msg, title, icon=None, ok_btn=True):
    dlg = MessageDialog(msg, title, icon, ok_btn, name=title)
    res = dlg.ShowModal()
    dlg.Destroy()
    return res


def pop_error(msg):
    logger.error(msg)
    if gui_config.USE_MSGBOX:
        wx.MessageBox(msg, 'Error', wx.OK | wx.ICON_ERROR)
    else:
        MessageBox(msg, 'Error', wx.ART_ERROR)


def pop_confirm(msg):
    if gui_config.USE_MSGBOX:
        # In wxGTK the Yes/No lacks icons, the Yes/No/Cancel is nicer
        return wx.MessageBox(msg, 'Confirm', wx.YES_NO | wx.CANCEL | wx.CANCEL_DEFAULT | wx.ICON_QUESTION)
    return MessageBox(msg, 'Confirm', wx.ART_QUESTION, ok_btn=False)


def pop_info(msg):
    if gui_config.USE_MSGBOX:
        wx.MessageBox(msg, 'Information', wx.OK)
    else:
        MessageBox(msg, 'Information', wx.ART_INFORMATION)


def move_sel_up(box) -> bool:
    """ Helper to move the selection up """
    selection = box.Selection
    if selection == wx.NOT_FOUND or selection < 1:
        return False
    item = box.GetString(selection)
    data = box.GetClientData(selection)
    box.Delete(selection)
    box.Insert(item, selection-1, data)
    box.SetSelection(selection-1)
    return True


def move_sel_down(box) -> bool:
    """ Helper to move the selection down """
    selection = box.Selection
    size = box.Count
    if selection == wx.NOT_FOUND or selection >= size-1:
        return False
    item = box.GetString(selection)
    data = box.GetClientData(selection)
    box.Delete(selection)
    box.Insert(item, selection+1, data)
    box.SetSelection(selection+1)
    return True


def remove_item(lbox, confirm=None, callback=None) -> bool:
    selection = lbox.Selection
    if selection == wx.NOT_FOUND:
        return False
    ok = True
    if confirm is not None:
        name = lbox.GetString(selection)
        msg = confirm.format(name)
        ok = pop_confirm(msg) == wx.YES
    if not ok:
        return False
    if callback is not None:
        callback(lbox.GetClientData(selection))
    lbox.Delete(selection)
    count = lbox.GetCount()
    lbox.SetSelection(min(selection, count-1))
    return True


def ok_cancel(parent, ok_callback=None, no_cancel=False, domain=None, help=False):
    m_but_sizer = wx.StdDialogButtonSizer()
    parent.but_ok = wx.Button(parent, wx.ID_OK, name=domain+'.ok' if domain else wx.ButtonNameStr)
    m_but_sizer.AddButton(parent.but_ok)
    if not no_cancel:
        m_but_sizer.AddButton(wx.Button(parent, wx.ID_CANCEL, name=domain+'.cancel' if domain else wx.ButtonNameStr))
    if help:
        parent.but_help = wx.Button(parent, wx.ID_HELP, name=domain+'.help' if domain else wx.ButtonNameStr)
        m_but_sizer.AddButton(parent.but_help)
    m_but_sizer.Realize()
    if ok_callback:
        parent.but_ok.Bind(wx.EVT_BUTTON, ok_callback)
    return m_but_sizer


def get_emp_font():
    return emp_font


# def get_deemp_font():
#     global deemp_font
#     if deemp_font is None:
#         deemp_font = wx.Font(70, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_NORMAL, False)
#     return deemp_font


def input_label_and_text(parent, lbl, initial, help, txt_w, lbl_w=-1, style=0, id=None):
    sizer = wx.BoxSizer(wx.HORIZONTAL)
    label = wx.StaticText(parent, label=lbl, size=wx.Size(lbl_w, -1), style=wx.ALIGN_RIGHT)
    label.SetToolTip(help)
    input = wx.TextCtrl(parent, value=initial, size=wx.Size(txt_w, -1), style=style, id=create_id(id))
    input.SetToolTip(help)
    sizer.Add(label, SIZER_FLAGS_0)
    sizer.Add(input, SIZER_FLAGS_1)
    return label, input, sizer


def get_client_data(container):
    return [container.GetClientData(n) for n in range(container.GetCount())]


def set_items(lbox, objs):
    """ Set the list box items using the string representation of the objs.
        Keep the objects in the client data """
    if isinstance(objs, list) and len(objs) and isinstance(objs[0], str):
        lbox.SetItems(objs)
        return
    lbox.SetItems([str(o) for o in objs])
    for n, o in enumerate(objs):
        lbox.SetClientData(n, o)


def get_selection(lbox):
    """ Helper to get the current index, string and data for a list box selection """
    index = lbox.Selection
    if index == wx.NOT_FOUND:
        return index, None, None
    return index, lbox.GetString(index), lbox.GetClientData(index)


class ChooseFromList(InjectDialog):
    def __init__(self, parent, items, what, search, l_style, search_on):
        self.all_options = items
        self.search_on = search_on
        if search_on:
            self.translate = dict(zip(search_on, self.all_options))
        title = ('an' if what[0] in 'aeiou' else 'a')+' '+what
        InjectDialog.__init__(self, parent, title="Select "+title, name='choose_'+title, id=create_id('ID_CHOOSE'),
                              style=wx.DEFAULT_DIALOG_STYLE | wx.STAY_ON_TOP | wx.BORDER_DEFAULT)
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        if search:
            self.search = wx.SearchCtrl(self, id=create_id('ID_CHOOSE_SRCH'))
            self.search.SetToolTip('Type here to do an incremental search')
            main_sizer.Add(self.search, SIZER_FLAGS_0)
            self.search.Bind(wx.EVT_TEXT, self.OnText)
            # Take ENTER as a confirmation
            self.search.Bind(wx.EVT_SEARCH, self.OnDClick)
        self.lbox = wx.ListBox(self, style=l_style, id=create_id('ID_CHOOSE_LBX'))
        self.lbox.SetToolTip(f'Available {what}s to select')
        set_items(self.lbox, items)
        main_sizer.Add(self.lbox, SIZER_FLAGS_1)
        main_sizer.Add(ok_cancel(self), SIZER_FLAGS_0)
        self.SetSizer(main_sizer)
        main_sizer.SetSizeHints(self)
        self.lbox.Bind(wx.EVT_LISTBOX_DCLICK, self.OnDClick)
        # Adjust the width to be optimal for the width of the outputs
#         size = self.GetClientSize()
#         lb_size = self.lbox.BestSize
#         if lb_size.Width > size.Width:
#             size.Width = lb_size.Width
#             self.SetClientSize(size)
#         # Done
#         self.Layout()
#         self.Centre(wx.BOTH)

    def OnDClick(self, event):
        self.EndModal(wx.ID_OK)

    def OnText(self, event):
        text = event.GetString()
        text_l = text.lower()
        options = self.search_on or self.all_options
        options = options.copy()
        items = []
        if text in options:
            items.append(text)
            options.remove(text)
        if text_l in options:
            items.append(text_l)
            options.remove(text_l)
        remain = []
        for o in options:
            if o.startswith(text):
                items.append(o)
            else:
                remain.append(o)
        items += [o for o in remain if o.lower().startswith(text_l)]
        for s in difflib.get_close_matches(text, options, n=5, cutoff=0.3):
            if s not in items:
                items.append(s)
        if self.search_on:
            items = [self.translate[v] for v in items]
        set_items(self.lbox, items)
        self.lbox.SetSelection(0)


def choose_from_list(parent, items, what, multiple=False, search_on=None):
    if len(items) == 1:
        return items if multiple else items[0]
    l_style = wx.LB_MULTIPLE if multiple else wx.LB_SINGLE
    dlg = ChooseFromList(parent, items, what, True, l_style, search_on)
    if dlg.ShowModal() == wx.ID_OK:
        is_str = isinstance(items[0], str)
        if multiple:
            if is_str:
                res = [dlg.lbox.GetString(i) for i in dlg.lbox.GetSelections()]
            else:
                res = [dlg.lbox.GetClientData(i) for i in dlg.lbox.GetClientData()]
        else:
            res = dlg.lbox.GetString(dlg.lbox.Selection) if is_str else dlg.lbox.GetClientData(dlg.lbox.Selection)
    else:
        res = None
    dlg.Destroy()
    return res


def get_res_bitmap(resource, size: int = wx.DefaultSize):
    # return wx.BitmapBundle(wx.ArtProvider.GetBitmap(resource))
    return wx.ArtProvider.GetBitmapBundle(resource, size=size)


def set_button_bitmap(btn, resource):
    if isinstance(resource, str):
        if wx.Platform == '__WXGTK__':
            btn.SetBitmap(wx.ArtProvider.GetBitmapBundle(resource, wx.ART_BUTTON))
        return
    btn.SetBitmap(get_res_bitmap(resource))


def add_abm_buttons(self, sb=None, add_add=False, add_add_ttip='', add_ttip=None, id=None):
    """ Buttons for the Add/Remove/Modify actions.
        They are added to `self` inside an `sb` widget """
    if sb is None:
        sb = self
    flags = SIZER_FLAGS_0
    but_sizer = wx.BoxSizer(wx.VERTICAL)
    self.but_up = wx.BitmapButton(sb, style=wx.BU_AUTODRAW, bitmap=get_res_bitmap(wx.ART_GO_UP), id=create_id(id, 'up'))
    self.but_up.SetToolTip("Move the selection up")
    but_sizer.Add(self.but_up, flags)
    self.but_down = wx.BitmapButton(sb, style=wx.BU_AUTODRAW, bitmap=get_res_bitmap(wx.ART_GO_DOWN), id=create_id(id, 'down'))
    self.but_down.SetToolTip("Move the selection down")
    but_sizer.Add(self.but_down, flags)
    self.but_add = wx.BitmapButton(sb, style=wx.BU_AUTODRAW, bitmap=get_res_bitmap(wx.ART_PLUS), id=create_id(id, 'add'))
    self.but_add.SetToolTip(add_ttip or "Add one entry")
    but_sizer.Add(self.but_add, flags)
    if add_add:
        self.but_add_add = wx.BitmapButton(sb, style=wx.BU_AUTODRAW, bitmap=get_res_bitmap(wx.ART_LIST_VIEW),
                                           id=create_id(id, 'add_add'))
        self.but_add_add.SetToolTip(add_add_ttip)
        but_sizer.Add(self.but_add_add, flags)
    self.but_remove = wx.BitmapButton(sb, style=wx.BU_AUTODRAW, bitmap=get_res_bitmap(wx.ART_MINUS),
                                      id=create_id(id, 'remove'))
    self.but_remove.SetToolTip("Remove the entry")
    but_sizer.Add(self.but_remove, flags)
    return but_sizer


def send_relayout_event(window):
    # The selected widget might be bigger, adjust the dialog
    ev = wx.PyCommandEvent(wx.EVT_COLLAPSIBLEPANE_CHANGED.typeId, window.GetId())
    wx.PostEvent(window.GetEventHandler(), ev)
