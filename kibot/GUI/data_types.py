# -*- coding: utf-8 -*-
# Copyright (c) 2024 Salvador E. Tropea
# Copyright (c) 2024 Instituto Nacional de Tecnologïa Industrial
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)
#
# Classes to edit the different data types used for the YAML config
# Each class should provide a suitable widget

from copy import deepcopy
import math
import os
import webbrowser
import wx
from .validators import NumberValidator, LowerCaseValidator
from .gui_helpers import (move_sel_up, move_sel_down, ok_cancel, remove_item, input_label_and_text, get_client_data, set_items,
                          get_selection, get_emp_font, pop_error, add_abm_buttons, get_res_bitmap, pop_confirm,
                          send_relayout_event)
from . import gui_helpers as gh
from .gui_config import USE_DIALOG_FOR_NESTED, TYPE_SEL_RIGHT, SEPARATE_ADVANCED
from .gui_inject import create_id, InjectDialog
from ..error import KiPlotConfigurationError
from ..misc import typeof, try_int, RE_LEN, BASE_HELP_CFG
from ..optionable import Optionable
from .. import log
logger = log.get_logger()
TYPE_PRIORITY = {'list(string_dict)': 120, 'list(dict|string)': 110, 'list(dict)': 100, 'dict_s': 100,
                 'list(list(string))': 90, 'list(string)': 80, 'string_s': 80, 'dict': 60, 'string_dict': 55,
                 'string': 50, 'number': 20, 'boolean': 10}
TYPE_ABREV = {'list(string_dict)': 'LSD', 'list(dict|string)': 'LDS', 'list(dict)': 'LD', 'dict_s': 'LD1',
              'list(list(string))': 'LLS', 'list(string)': 'LS', 'string_s': 'LS1', 'dict': 'D', 'string_dict': 'SD',
              'string': 'S', 'number': 'N', 'boolean': 'B'}
TYPE_EMPTY = {'list(string_dict)': [], 'list(dict|string)': [], 'list(dict)': [], 'list(list(string))': [],
              'list(string)': [], 'string_s': '', 'string_dict': {}, 'string': '', 'number': '', 'boolean': False,
              'dict': {}, 'dict_s': {}}
max_label = 200
def_text = 200
BMP_CLEAR = wx.ART_DELETE
# BMP_CLEAR = wx.ART_CROSS_MARK


def name_remove_end(name, count):
    return '.'.join(name.split('.')[:-count])


class DataTypeBase(object):
    def __init__(self, kind, restriction, default, name):
        self.kind = kind
        self.restriction = restriction
        self.default = self.reset_value = default
        self.is_dict = kind == 'dict' or kind == 'dict_s'
        self.is_list_dict = kind == 'list(dict)' or kind == 'list(dict|string)' or kind == 'dict_s'
        self.is_list = kind.startswith('list(') or kind in {'string_s', 'dict_s'}

    def get_widget(self, obj, window, entry, level, init, value, name, **kwargs):
        self.entry = entry
        entry.edited = False
        help = entry.help
        if self.default is not None:
            help += f'\nDefault: {self.default}'
        e_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.wlabel = wx.StaticText(window, label=self.get_label(entry), size=wx.Size(max_label, -1), style=wx.ALIGN_RIGHT)
        entry.show_status(self.wlabel)
        self.wlabel.SetToolTip(help)
        self.define_input(window, value, init, name)
        self.input.SetToolTip(help)

        e_sizer.Add(self.wlabel, gh.SIZER_FLAGS_0)
        e_sizer.Add(self.input, gh.SIZER_FLAGS_1)
        self.input.Bind(wx.EVT_TEXT, self.OnChange)
        return e_sizer

    def get_restriction_help(self):
        return ''

    def get_label(self, entry):
        return entry.name

    def get_value(self):
        return self.input.Value

    def focus(self):
        self.input.SetFocus()

    def reset(self, get_focus=True):
        self.entry.set_edited(False, self.wlabel)
        self.ori_value = self.input.Value = self.reset_value
        if get_focus:
            self.focus()

    def matches_type(self, data_type):
        return self.kind == data_type

    def update_shown(self, sizer, w, show):
        """ Regular update when all widgets are visible together """
        sizer.Show(w, show)

    def OnChange(self, event):
        self.entry.set_edited(self.input.Value != self.ori_value, self.wlabel)


class DataTypeString(DataTypeBase):
    def define_input(self, window, value, init, name):
        self.input = wx.TextCtrl(window, size=wx.Size(def_text, -1), id=create_id(name))
        if init:
            self.input.SetValue(value)
        self.ori_value = self.input.Value
        self.input.Bind(wx.EVT_TEXT, self.OnChange)

    def get_widget(self, obj, window, entry, level, init, value, name, **kwargs):
        res = super().get_widget(obj, window, entry, level, init, value, name, **kwargs)
        if '{no_case}' in entry.help:
            self.input.SetValidator(LowerCaseValidator(self.input, self.OnChange))
        return res


class DataTypeNumber(DataTypeString):
    def __init__(self, kind, restriction, default, name):
        super().__init__(kind, restriction, default, name)
        self.has_min = False
        self.has_max = False
        if restriction is None:
            restriction = (-math.inf, math.inf)
        else:
            if restriction[0] is None:
                restriction[0] = -math.inf
            else:
                self.has_min = True
            if restriction[1] is None:
                restriction[1] = math.inf
            else:
                self.has_max = True
        self.restriction = restriction
        if not isinstance(default, (int, float)):
            default = 0
        try:
            self.reset_value = str(try_int(default))
        except (TypeError, ValueError):
            logger.error(f'Missing default for {name}')
            self.reset_value = '0'

    def get_widget(self, obj, window, entry, level, init, value, name, **kwargs):
        if init:
            value = str(value)
        sizer = super().get_widget(obj, window, entry, level, init, value, name, **kwargs)
        self.input.SetValidator(NumberValidator(self.input, self.restriction, self.default, self.OnChange))
        return sizer

    def get_label(self, entry):
        if not self.has_min and not self.has_max:
            return entry.name
        return entry.name + f' [{self.restriction[0]},{self.restriction[1]}]'

    def get_restriction_help(self):
        return f'\nRange: {self.restriction[0]} to {self.restriction[1]}'

    def get_value(self):
        val = self.input.Value
        if val == '-' or val == '':
            return self.default
        return try_int(val)


class DataTypeBoolean(DataTypeBase):
    def define_input(self, window, value, init, name):
        self.input = wx.CheckBox(window, id=create_id(name))
        if init:
            self.input.SetValue(value)
        self.ori_value = self.input.Value
        self.input.Bind(wx.EVT_CHECKBOX, self.OnChange)


class DataTypeChoice(DataTypeBase):
    def define_input(self, window, value, init, name):
        self.input = wx.Choice(window, choices=self.restriction, id=create_id(name))
        if init:
            try:
                self.input.SetSelection(self.restriction.index(value))
            except ValueError:
                # New entry
                self.input.SetSelection(0)
        self.ori_value = self.input.Selection
        self.input.Bind(wx.EVT_CHOICE, self.OnChange)

    def get_value(self):
        # Why not GetValue??!!
        return self.restriction[self.input.GetSelection()]

    def reset(self, get_focus=True):
        self.entry.set_edited(False, self.wlabel)
        if self.default is None:
            logger.error(f'Missing default for {self.entry.name}')
        self.reset_value = self.restriction.index(self.default) if self.default is not None else 0
        self.ori_value = self.input.Selection = self.reset_value
        if get_focus:
            self.focus()

    def OnChange(self, event):
        self.entry.set_edited(self.input.Selection != self.ori_value, self.wlabel)


class DataTypeNumberChoice(DataTypeChoice):
    def __init__(self, kind, restriction, default, name):
        super().__init__(kind, restriction, default, name)
        self.restriction = self.restriction[1]
        self.default = str(self.default)

    def define_input(self, window, value, init, name):
        super().define_input(window, str(value), init, name)

    def get_value(self):
        return float(super().get_value())


class DataTypeCombo(DataTypeBase):
    def define_input(self, window, value, init, name):
        self.input = wx.ComboBox(window, choices=[v for v in self.restriction if v != '*'], id=create_id(name))
        if init:
            self.input.SetValue(value)
        self.ori_value = self.input.Value
        self.input.Bind(wx.EVT_TEXT, self.OnChange)


def create_new_optionable(cls, parent, extra=None):
    """ Create an Optionable from the cls class and configure it to get the default values.
        Some objects needs filled values or they fail to be configured, so here we use the docs examples to fill them """
    o = cls()
    # TODO: Is this ok?
    if True:
        # This approach adds the examples to the tree, but then they get marked as defined by user, which is confusing
        # But is the best way because the internal mechanism relies on the values found on the tree
        tree = extra if extra else {}
        for k, v in o.get_attrs_for().items():
            if k.startswith('_') and k.endswith('_example'):
                tree[k[1:-8]] = v
        o.set_tree(tree)
    else:
        # Here we put the examples directly in the members
        for k, v in o.get_attrs_for().items():
            if k.startswith('_') and k.endswith('_example'):
                setattr(o, k[1:-8], v)
    o.config(parent)
    return o


class DataTypeDict(DataTypeBase):
    def get_widget(self, obj, window, entry, level, init, value, name, **kwargs):
        entry.edited = False
        help = entry.help
        lbl = self.get_label(entry)
        # Use the current value only when "init", otherwise use an empty object
        if init:
            self.sub_obj = getattr(obj, entry.name)
            if self.sub_obj is None:
                # This is used by panelize, the sub-options are all "null"
                self.sub_obj = create_new_optionable(entry.cls, obj)
        else:
            self.sub_obj = create_new_optionable(entry.cls, obj)
        # self.ori_value = deepcopy(self.sub_obj._tree)
        self.sub_entries = entry.sub
        self.window = window
        self.entry = entry
        self.obj = obj
        # This option tells the dict can be represented as a string
        self.show_value = kwargs.get('show_value')
        e_sizer = wx.BoxSizer(wx.HORIZONTAL)

        if USE_DIALOG_FOR_NESTED:
            if kwargs.get('force_embedded'):
                # Remove the extra "NAME.dict" at the end
                name_embedded = name_remove_end(name, 2)
                self.embedded = True
                sb_sizer = wx.StaticBoxSizer(wx.VERTICAL, window, lbl)
                sb = sb_sizer.GetStaticBox()
                # TODO: better solution than an extra sizer?
                sep_sizer = wx.BoxSizer(wx.VERTICAL)  # Add some border
                add_widgets(self.sub_obj, entry.sub, sb, sep_sizer, level+1, entry, domain=name_embedded)
                sb_sizer.Add(sep_sizer, gh.SIZER_FLAGS_1)
                e_sizer.Add(sb_sizer, gh.SIZER_FLAGS_1)
                # Which widget will be focused
                self.input = sb
            else:
                self.embedded = False
                self.entry_name = lbl
                self.btn = wx.Button(window, label=self.get_button_label(), id=create_id(name))
                self.btn.SetToolTip('Open a separated dialog for this option')
                e_sizer.Add(self.btn, gh.SIZER_FLAGS_1)
                self.btn.Bind(wx.EVT_BUTTON, self.OnEdit)
                # Which widget will be focused
                self.input = self.btn
                self.domain = name
        else:
            # Collapsible pane version
            self.embedded = True
            cp = wx.CollapsiblePane(window, label=lbl)
            cp.SetToolTip(help)
            # cp.Collapse(False)  # Start expanded

            pane = cp.GetPane()
            pane_sizer = wx.BoxSizer(wx.VERTICAL)

            add_widgets(self.sub_obj, entry.sub, pane, pane_sizer, level+1, domain=name)
            pane.SetSizer(pane_sizer)

            e_sizer.Add(cp, gh.SIZER_FLAGS_1)
            # Which widget will be focused
            self.input = self.pane
        return e_sizer

    def get_button_label(self):
        return "Edit "+self.get_label(self.entry)+(f' ({self.sub_obj})'if self.show_value else '')

    def update_button(self):
        if not hasattr(self, 'btn'):
            return
        self.btn.SetLabel(self.get_button_label())

    def OnEdit(self, event):
        window = self.window.Parent
        if isinstance(window, wx.Notebook):
            window = window.Parent
        if isinstance(window, wx.StaticBox):
            window = window.Parent
        if isinstance(window, wx.ScrolledWindow):
            window = window.Parent
        if edit_dict(window, self.sub_obj, self.sub_entries, self.entry_name, name=self.domain):
            self.entry.set_edited(True)
            self.update_button()

    def reset(self, get_focus=True):
        self.entry.set_edited(False)
        # self.ori_value = {}
        self.sub_obj = create_new_optionable(self.entry.cls, self.obj)
        self.update_button()
        if get_focus:
            self.focus()

    def get_value(self):
        if not self.embedded:
            tree = self.sub_obj._tree
        else:
            tree = {}
            for e in self.sub_entries:
                if e.user_defined:
                    tree[e.name] = e.get_value()
        # logger.error(tree)
        return tree


class InputStringDialog(InjectDialog):
    def __init__(self, window, lbl, title, help, initial='', no_case=False):
        InjectDialog.__init__(self, window, title=title,
                              style=wx.DEFAULT_DIALOG_STYLE | wx.STAY_ON_TOP)
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        _, self.input, inp_sizer = input_label_and_text(self, lbl, initial, help, def_text)
        if no_case:
            self.input.SetValidator(LowerCaseValidator(self.input))
        main_sizer.Add(inp_sizer, gh.SIZER_FLAGS_1)
        main_sizer.Add(ok_cancel(self), gh.SIZER_FLAGS_0)
        self.SetSizer(main_sizer)
        main_sizer.SetSizeHints(self)
        # Make ENTER finish it
        self.Bind(wx.EVT_CHAR_HOOK, self.OnKey)

    def OnKey(self, event):
        """ Called by the dialog OnCharHook """
        if event.GetKeyCode() == wx.WXK_RETURN:
            self.EndModal(wx.ID_OK)
        else:
            # Not our key, continue processing it
            event.Skip()


class DataTypeList(DataTypeBase):
    def get_widget(self, obj, window, entry, level, init, value, name, **kwargs):
        entry.edited = False
        self.label = entry.name
        self.help = entry.help
        self.window = window
        self.entry = entry
        # Check if we have len constraints
        m = RE_LEN.search(entry.help)
        self.len_restriction = int(m.group(1)) if m else 0

        main_sizer = wx.StaticBoxSizer(wx.VERTICAL, window, entry.name)
        self.sp = main_sizer.GetStaticBox()
        entry.show_status(self.sp)
        abm_sizer = wx.BoxSizer(wx.HORIZONTAL)

        list_sizer = wx.BoxSizer(wx.VERTICAL)
        self.lbox = wx.ListBox(self.sp, choices=[], size=wx.Size(def_text, -1), style=wx.LB_NEEDED_SB | wx.LB_SINGLE,
                               id=create_id(name))
        if init:
            try:
                self.set_items(obj, entry.name, value)
            except Exception:
                logger.error(f'{entry.name} {getattr(obj, entry.name)}')
                raise
        self.ori_value = self.get_value()
        self.lbox.SetToolTip(self.help)
        list_sizer.Add(self.lbox, gh.SIZER_FLAGS_1)

        abm_sizer.Add(list_sizer, gh.SIZER_FLAGS_1_NO_BORDER)
        # Make the name uniform, not accurate
        but_name = name_remove_end(name, 1)+'.dict'
        self.path_name = but_name
        abm_sizer.Add(add_abm_buttons(self, self.sp, id=but_name), gh.SIZER_FLAGS_0_NO_EXPAND)
        main_sizer.Add(abm_sizer, gh.SIZER_FLAGS_1_NO_BORDER)

        self.but_up.Bind(wx.EVT_BUTTON, self.OnUp)
        self.but_down.Bind(wx.EVT_BUTTON, self.OnDown)
        self.but_add.Bind(wx.EVT_BUTTON, lambda event: self.pre_edit_item())
        self.but_remove.Bind(wx.EVT_BUTTON, self.OnRemove)

        self.lbox.Bind(wx.EVT_LISTBOX_DCLICK, self.OnDClick)

        self.update_add_remove()
        return main_sizer

    def OnDClick(self, event):
        index, string, obj = get_selection(self.lbox)
        if index == wx.NOT_FOUND:
            return
        self.edit_item(string, obj, index)

    def create_edit_title(self, index):
        if index == -1:
            return f'New {self.label} entry'
        return f'Edit {self.label} entry {index+1}'

    def mark_edited(self):
        cur_value = self.get_value()
        self.entry.set_edited(cur_value != self.ori_value, self.sp)
        self.update_add_remove()

    def update_add_remove(self):
        if not self.len_restriction:
            return
        count = self.lbox.GetCount()
        if count >= self.len_restriction:
            self.but_add.Disable()
        if count <= self.len_restriction:
            self.but_remove.Disable()

    def focus(self):
        self.lbox.SetFocus()

    def reset(self, get_focus=True):
        self.entry.set_edited(False, self.sp)
        self.lbox.SetItems([])
        if get_focus:
            self.focus()

    def pre_edit_item(self):
        if self.len_restriction and self.lbox.GetCount() >= self.len_restriction:
            return
        self.edit_item()

    def OnUp(self, event):
        if move_sel_up(self.lbox):
            self.mark_edited()

    def OnDown(self, event):
        if move_sel_down(self.lbox):
            self.mark_edited()

    def OnRemove(self, event):
        if self.len_restriction and self.lbox.GetCount() <= self.len_restriction:
            return
        remove_item(self.lbox)
        self.mark_edited()


class DataTypeListString(DataTypeList):
    def set_items(self, obj, member, value):
        # The value is more reliable for a string. I.e. filters are solved and become objects
        self.lbox.SetItems(value)

    def edit_item(self, string='', obj=None, index=-1):
        ori = string
        dlg = InputStringDialog(self.window, self.label, self.create_edit_title(index), self.help, initial=string,
                                no_case='{no_case}' in self.entry.help)
        res = dlg.ShowModal()
        if res == wx.ID_OK:
            if index == -1:
                self.lbox.Append(dlg.input.Value)
                self.mark_edited()
            elif ori != dlg.input.Value:
                self.lbox.SetString(index, dlg.input.Value)
                self.mark_edited()
        dlg.Destroy()

    def get_value(self):
        return [self.lbox.GetString(n) for n in range(self.lbox.GetCount())]


class DataTypeListStringSingular(DataTypeString, DataTypeListString):
    def get_widget(self, obj, window, entry, level, init, value, name, **kwargs):
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        if isinstance(value, str):
            # If we get a plain string promote it to a list
            # Note that this comes from the tree, before config
            value = [value]
        assert isinstance(value, list), type(value)
        # A list box
        self.use_str = False   # Force list behavior for get_value (used by string list init)
        sizer_lbox = DataTypeListString.get_widget(self, obj, window, entry, level, init, value, name, **kwargs)
        items = len(value)
        if items <= 1:
            # Singular version, switch to a string
            value = value[0] if items else ''
            self.use_str = True
        # A text box
        sizer_str = DataTypeBase.get_widget(self, obj, window, entry, level, init and self.use_str, value, name, **kwargs)
        #   Add a button to make the string plural
        self.but_plural = wx.BitmapButton(window, style=wx.BU_AUTODRAW, bitmap=get_res_bitmap(wx.ART_PLUS))
        self.but_plural.SetToolTip("Add more entries")
        self.but_plural.Bind(wx.EVT_BUTTON, self.MakePlural)
        if not items:
            # We need at least one to promote it to a list
            self.but_plural.Disable()
        sizer_str.Add(self.but_plural, wx.SizerFlags().Border(wx.RIGHT).Center())
        # Add both widgets and enable the best for the current value
        main_sizer.Add(sizer_lbox, gh.SIZER_FLAGS_1_NO_BORDER)
        main_sizer.Add(sizer_str, gh.SIZER_FLAGS_1_NO_BORDER)
        main_sizer.Show(sizer_lbox if self.use_str else sizer_str, False)
        self.sizer_lbox = sizer_lbox
        self.sizer_str = sizer_str
        self.main_sizer = main_sizer
        return main_sizer

    def OnChange(self, event):
        """ Enable the 'plural' button only when we have something """
        super().OnChange(event)
        self.but_plural.Enable(len(self.input.Value) != 0)

    def update_shown(self, sizer, w, show):
        """ Apply the global visibility and then adjust which sub-widget is visible """
        sizer.Show(w, show)
        self.main_sizer.Show(self.sizer_lbox, not self.use_str)
        self.main_sizer.Show(self.sizer_str, self.use_str)

    def switch_to_text(self, do_it=True, get_focus=True):
        """ Make the input text visible and hide the list box """
        self.main_sizer.Show(self.sizer_lbox, not do_it)
        self.main_sizer.Show(self.sizer_str, do_it)
        if get_focus:
            if do_it:
                self.input.SetFocus()
            else:
                self.lbox.SetFocus()
        send_relayout_event(self.window)
        self.use_str = do_it

    def MakePlural(self, event):
        """ Switch to the list box if the user needs more items """
        cur_val = self.input.Value
        if not cur_val:
            # It shouldn't happen, we disable the button
            return
        # Promote this value to a list
        self.lbox.SetItems([cur_val])
        self.edit_item()
        # Check if we have 2 items
        if self.lbox.GetCount() != 2:
            return
        # Ok, we had a value and added another, switch to the list
        self.switch_to_text(False)

    def OnRemove(self, event):
        """ Change to text input if we reduce the list to 1 item """
        super().OnRemove(event)
        # If we reduced the list to one value switch to a input box
        items = self.lbox.GetCount()
        if items > 1:
            return
        self.input.Value = self.lbox.GetString(0) if items else ''
        self.switch_to_text()

    def reset(self, get_focus=True):
        """ Clear the input value and show the text input """
        DataTypeBase.reset(self, False)  # Don't focus here, we will focus the correct widget in switch_to_text
        self.switch_to_text(True, get_focus)

    def get_value(self):
        """ Here we return the optimal, Optionable can promote strings """
        return self.input.Value if self.use_str else DataTypeListString.get_value(self)

    def matches_type(self, data_type):
        return data_type == 'string' or data_type == 'list(string)'


class DataTypeListDict(DataTypeList):
    def set_items(self, obj, member, value):
        val = getattr(obj, member)
        if val is None or isinstance(val, type):
            val = []
        set_items(self.lbox, val)

    def edit_item(self, string='', obj=None, index=-1):
        if obj is None:
            obj = create_new_optionable(self.entry.cls, self.entry.obj)
        res = edit_dict(self.window.Parent, obj, self.entry.sub, self.entry.name, self.create_edit_title(index),
                        force_changed=True, name=self.path_name)
        if res:
            if index == -1:
                self.lbox.Append(str(obj), obj)
            else:
                self.lbox.SetString(index, str(obj))
            self.entry.set_edited(True)

    def get_value(self):
        return [v._tree for v in get_client_data(self.lbox)]


class DataTypeListDictSingular(DataTypeDict, DataTypeListDict):
    def get_widget(self, obj, window, entry, level, init, value, name, **kwargs):
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        if isinstance(value, dict):
            # If we get a plain string promote it to a list
            # Note that this comes from the tree, before config
            value = [value]
        assert isinstance(value, list), type(value)
        # A list box
        self.use_dict = False   # Force list behavior for get_value (used by string list init)
        sizer_lbox = DataTypeListDict.get_widget(self, obj, window, entry, level, init, value, name, **kwargs)
        items = len(value)
        if items <= 1:
            # Singular version, switch to a dict
            self.use_dict = True
            init_dict = init and items
            if items:
                # DataTypeDict.get_widget will get the value from the real object, but this is a list
                # So here we temporarily change it to the only element in the list and use it
                old_value = getattr(obj, entry.name)
                setattr(obj, entry.name, value[0])
        else:
            init_dict = False
        # A dict editor
        kwargs['force_embedded'] = False
        kwargs['show_value'] = True
        single_name = name[:-2]  # .dict_s -> .dict
        sizer_dict = DataTypeDict.get_widget(self, obj, window, entry, level, init_dict, value, single_name, **kwargs)
        if init_dict:
            # Revert the temporal singular
            setattr(obj, entry.name, old_value)
        #   Add a button to make the string plural
        self.but_plural = wx.BitmapButton(window, style=wx.BU_AUTODRAW, bitmap=get_res_bitmap(wx.ART_PLUS))
        self.but_plural.SetToolTip("Add more entries")
        self.but_plural.Bind(wx.EVT_BUTTON, self.MakePlural)
        sizer_dict.Add(self.but_plural, wx.SizerFlags().Border(wx.RIGHT).Center())
        # Add both widgets and enable the best for the current value
        main_sizer.Add(sizer_lbox, gh.SIZER_FLAGS_1_NO_BORDER)
        main_sizer.Add(sizer_dict, gh.SIZER_FLAGS_1_NO_BORDER)
        main_sizer.Show(sizer_lbox if self.use_dict else sizer_dict, False)
        self.sizer_lbox = sizer_lbox
        self.sizer_dict = sizer_dict
        self.main_sizer = main_sizer
        return main_sizer

    def switch_to_dict(self, do_it=True, get_focus=True):
        """ Make the input text visible and hide the list box """
        self.main_sizer.Show(self.sizer_lbox, not do_it)
        self.main_sizer.Show(self.sizer_dict, do_it)
        if get_focus:
            if do_it:
                self.input.SetFocus()
            else:
                self.lbox.SetFocus()
        send_relayout_event(self.window)
        self.use_dict = do_it

    def MakePlural(self, event):
        """ Switch to the list box if the user needs more items """
        # Promote the value used for the dict to a list
        # TODO: what about embedded ones?
        set_items(self.lbox, [self.sub_obj])
        self.edit_item()
        # Check if we have 2 items
        if self.lbox.GetCount() != 2:
            return
        # Ok, we had a value and added another, switch to the list
        self.switch_to_dict(False)

    def OnRemove(self, event):
        """ Change to text input if we reduce the list to 1 item """
        super().OnRemove(event)
        # If we reduced the list to one value switch to a input box
        items = self.lbox.GetCount()
        if items > 1:
            return
        # Copy the only remaining item in the list to the dict
        self.sub_obj = self.lbox.GetClientData(0)
        self.switch_to_dict()

    def update_shown(self, sizer, w, show):
        """ Apply the global visibility and then adjust which sub-widget is visible """
        sizer.Show(w, show)
        self.main_sizer.Show(self.sizer_lbox, not self.use_dict)
        self.main_sizer.Show(self.sizer_dict, self.use_dict)

    def reset(self, get_focus=True):
        """ Clear the input value and show the text input """
        DataTypeDict.reset(self, False)  # Don't focus here, we will focus the correct widget in switch_to_dict
        self.switch_to_dict(True, get_focus)

    def get_value(self):
        """ Here we return the optimal, Optionable can promote strings """
        return DataTypeDict.get_value(self) if self.use_dict else DataTypeListDict.get_value(self)

    def matches_type(self, data_type):
        return data_type == 'dict' or data_type == 'list(dict)'


class DummyForDictOrString(object):
    def __init__(self, member, initial, cls, parent):
        logger.debug(f'Creating {member} = {initial} for class {cls}')
        if initial is None:
            setattr(self, member, create_new_optionable(cls, parent))
            self._tree = {}  # Start indicating isn't from user
        else:
            setattr(self, member, initial)
            self._tree = {member: initial if isinstance(initial, str) else initial._tree}

    def get_attrs_gen(self):
        return filter(lambda k: k[0][0] != '_', vars(self).items())

    def reconfigure(self, tree):
        self._tree = tree
        k, v = tuple(tree.items())[0]
        if isinstance(v, str):
            setattr(self, k, v)
        else:
            obj = getattr(self, k)
            obj.reconfigure(v)


class DataTypeListDictOrString(DataTypeListDict):
    def edit_item(self, string='', obj=None, index=-1):
        name = self.entry.name
        str_cls = get_class_for('string', self.restriction)
        valids = [str_cls('string', self.restriction, self.default, name),
                  DataTypeDict('dict', self.restriction, self.default, name)]
        new_obj = DummyForDictOrString(name, obj, self.entry.cls, self.entry.obj)
        new_obj._parent = self.entry.obj._parent
        new_entry = DataEntry(name, valids, None, self.help, False, new_obj, 0, self.entry)
        # Copy the entries
        new_entry.sub = deepcopy(self.entry.sub)
        # But link them to the new_entry
        for e in new_entry.sub:
            e.parent = new_entry
        new_entry.cls = self.entry.cls
        res = edit_dict(self.window.Parent, new_obj, [new_entry], name, self.create_edit_title(index), force_changed=True,
                        name=self.path_name)
        if res:
            new_val = getattr(new_obj, name)
            if index == -1:
                self.lbox.Append(str(new_val), new_val)
            else:
                self.lbox.SetString(index, str(new_val))
                self.lbox.SetClientData(index, new_val)
            self.mark_edited()

    def set_items(self, obj, member, value):
        val = getattr(obj, member)
        if val is None or isinstance(val, type):
            val = []
        self.lbox.SetItems([str(o) for o in val])
        for n, o in enumerate(val):
            self.lbox.SetClientData(n, o)

    def get_value(self):
        return [v if isinstance(v, str) else v._tree for v in get_client_data(self.lbox)]

    def matches_type(self, data_type):
        return data_type == 'list(dict)' or data_type == 'list(string)'


class StringPair(object):
    def __init__(self, key=None, value=None):
        if key is None:
            self.key = 'new_key'
            self.value = 'new_value'
            self._tree = {}  # Start indicating isn't from user
        else:
            self.key = key
            self.value = value
            self._tree = {'key': key, 'value': value}

    def config(self, name):
        self.key = self._tree.get('key', self.key)
        self.value = self._tree.get('value', self.value)
        if not self.key:
            raise KiPlotConfigurationError("The `key` can't be empty")

    def __repr__(self):
        return f'{self.key} -> {self.value}'


class DataTypeStringDict(DataTypeList):
    """ Class to edit a pair key/value
        Behaves like an Optionable """
    def set_items(self, obj, member, value):
        val = getattr(obj, member)
        if val is None or isinstance(val, type):
            val = {}
        set_items(self.lbox, [StringPair(k, v) for k, v in val.items()])

    def edit_item(self, string='', obj=None, index=-1):
        new_obj = StringPair() if obj is None else obj
        new_entries = [DataEntry('key', [DataTypeString('string', None, '', 'key')], None, self.help, False, new_obj, 0),
                       DataEntry('value', [DataTypeString('string', None, '', 'value')], None, self.help, False, new_obj, 0)]
        res = edit_dict(self.window.Parent, new_obj, new_entries, self.entry.name, self.create_edit_title(index))
        if res:
            if index == -1:
                self.lbox.Append(str(new_obj), new_obj)
            else:
                self.lbox.SetString(index, str(new_obj))
            self.entry.set_edited(True)

    def get_value(self):
        return {v.key: v.value for v in get_client_data(self.lbox)}


class DummyForList(object):
    def __init__(self, member, initial):
        setattr(self, member, initial)
        self._tree = {}  # Start indicating isn't from user


class DataTypeListListString(DataTypeListDict):
    def edit_item(self, string='', obj=None, index=-1):
        # Here we create a dummy object with a data member named with the same name as the list
        # We then use the "dict" edition
        name = self.entry.name
        valids = [DataTypeListString('list(string)', self.restriction, self.default, name)]
        new_obj = DummyForList(name, [] if obj is None else obj)
        new_entries = [DataEntry(name, valids, None, self.help, False, new_obj, 0)]
        res = edit_dict(self.window.Parent, new_obj, new_entries, self.entry.name, self.create_edit_title(index))
        if res:
            new_val = getattr(new_obj, name)
            # logger.error(new_val)
            if index == -1:
                self.lbox.Append(str(new_val), new_val)
            else:
                self.lbox.SetString(index, str(new_val))
                self.lbox.SetClientData(index, new_val)
            self.mark_edited()

    def get_value(self):
        return get_client_data(self.lbox)


# ##################################################################################################
#  End of DataType* classes
# ##################################################################################################


class EditDict(InjectDialog):
    """ Dialog for a group of options """
    def __init__(self, parent, o, title, data_tree=None, validator=None, can_remove=True, w_name=''):
        # Generated code
        InjectDialog.__init__(self, parent, title=title, name=w_name,
                              style=wx.STAY_ON_TOP | wx.BORDER_DEFAULT | wx.CAPTION)  # wx.RESIZE_BORDER
        self.parent = parent
        self.obj = o
        self.validator = validator
        # Main sizer
        b_sizer = wx.BoxSizer(wx.VERTICAL)
        # Output widgets sizer
        middle_sizer = wx.BoxSizer(wx.HORIZONTAL)
        # This is the area for the output widgets
        self.scrollWindow = wx.ScrolledWindow(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.VSCROLL)
        self.scrollWindow.SetScrollRate(15, 15)

        # Main widgets area, scrollable
        self.scrl_sizer = wx.BoxSizer(wx.VERTICAL)
        self.data_type_tree = get_data_type_tree(o.__class__(), o) if data_tree is None else data_tree
        add_widgets(o, self.data_type_tree, self.scrollWindow, self.scrl_sizer, can_remove=can_remove, domain=w_name)
        self.scrollWindow.SetSizer(self.scrl_sizer)
        self.compute_scroll_hints()
        self.scrl_sizer.Fit(self.scrollWindow)
        self.scrollWindow.SetAutoLayout(True)
        middle_sizer.Add(self.scrollWindow, gh.SIZER_FLAGS_1)
        # Add the outputs are to the main sizer
        b_sizer.Add(middle_sizer, gh.SIZER_FLAGS_1)

        # Standard Ok/Cancel button
        b_sizer.Add(ok_cancel(self, self.OnOK, domain=w_name, help=True), gh.SIZER_FLAGS_0)

        # Resize things when the collapsible panes change their state
        self.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, self.OnResize)
        # Help for the dict
        self.but_help.Bind(wx.EVT_BUTTON, self.OnHelp)

        # Add the main sizer to the dialog
        self.SetSizer(b_sizer)
        b_sizer.SetSizeHints(self)

        # Auto doesn't work here, we want to adjust the size hints before
        # self.SetAutoLayout(True)
        # b_sizer.Fit(self)

        self.Layout()
        self.Centre(wx.BOTH)
        self.old_size = self.GetSize()

        self.delta = self.old_size-self.GetClientRect().Size
        # self.SetMinSize(wx.Size(100,100))

    def compute_scroll_hints(self):
        """ Adjust the scroller size hints according to the content and the display """
        maxDisplayArea = wx.Display().GetClientArea()
        max_usable_height = maxDisplayArea.Height - 200
        max_usable_width = maxDisplayArea.Width
        min_scroller_size = wx.Size(min(self.scrl_sizer.MinSize.width, max_usable_width),
                                    min(self.scrl_sizer.MinSize.height, max_usable_height))
        self.scrollWindow.SetSizeHints(min_scroller_size, wx.Size(min_scroller_size.width, -1))

    def OnHelp(self, event):
        name = self.GetName()
        name = name.replace('.dict', '')
        path = name.split('.')
        help = None
        if path[0] in {'output', 'preflight', 'filter', 'variant'}:
            if len(path) == 2:
                help = os.path.join(BASE_HELP_CFG, path[0]+'s', path[1]+'.html')
            else:
                help = os.path.join(BASE_HELP_CFG, path[0]+'s', self.obj.__class__.__name__+'.html')
        if help:
            webbrowser.open(help)
        else:
            logger.debug(f'Unknown help domain {name} {path}')

    def OnResize(self, event):
        self.compute_scroll_hints()
        sizer = self.GetSizer()
        sizer.Layout()
        # Not working ... why?
        # The window doesn't shrink pass some values, the returned values are OK, but the window is bigger in the screen
        new_size = sizer.MinSize+self.delta
        # logger.error(f'Before SetSize({new_size}): {self.Size} MinSize: {self.MinSize} MinClientSize: {self.MinClientSize}')
        # logger.error(f'{self.GetEffectiveMinSize()} {self.GetBestSize()}')
        self.SetMinSize(new_size)
        self.SetSize(new_size)
        # self.Layout()
        # self.Fit()
        # logger.error(f'After SetSize({new_size}): {self.Size} MinSize: {self.MinSize} MinClientSize: {self.MinClientSize}')
        # logger.error(f'{self.GetEffectiveMinSize()} {self.GetBestSize()}')
        # logger.error(f'{sizer.Size}')

    def OnOK(self, event):
        self.changed, retry = self.update_values()
        if not retry:
            self.EndModal(wx.ID_OK)

    def update_values(self):
        tree = {}
        for entry in self.data_type_tree:
            if entry.skip:
                tree['type'] = self.obj.type
                continue
            value = entry.get_value()
            if value is not None:
                tree[entry.name] = value
        if self.obj._tree == tree:
            logger.debug(f'Not modified {tree}')
            return False, False
        logger.debug(f'Updating {self.obj} {type(self.obj)} {tree}')
        # First try using a dummy
        dummy = deepcopy(self.obj)
        try:
            dummy.reconfigure(tree)
        except KiPlotConfigurationError as e:
            logger.debug(f'Error configuring: {e}')
            pop_error(str(e))
            # Ask to retry, the user can use Cancel because the original object isn't changed
            return True, True
        # Perform extra validations, i.e. usable name
        if self.validator:
            if not self.validator(dummy):
                return True, True
        # Ok, the configuration is valid, configure the real object
        self.obj.reconfigure(tree)
        logger.debug(f'New state: {dict(self.obj.get_attrs_gen())}')
        # Transfer the new state to be the "original"
        for entry in self.data_type_tree:
            entry.update_value()
        return True, False


def edit_dict(parent_dialog, obj, entries, entry_name, title=None, validator=None, force_changed=False, can_remove=True,
              name=None):
    if title is None:
        title = parent_dialog.GetTitle()+' | '+entry_name
    if name is None:
        name = 'edit_dict.'+parent_dialog.GetName()
        if entry_name:
            name += '.'+entry_name
    dlg = EditDict(parent_dialog, obj, title, entries, validator, can_remove, name)
    changed = dlg.ShowModal() == wx.ID_OK and (dlg.changed or force_changed)
    dlg.Destroy()
    return changed


def get_class_for(kind, rest):
    """ Return a class suitable to edit data of the *kind* type. """
    if kind == 'string':
        if rest is not None:
            if '*' in rest:
                return DataTypeCombo
            return DataTypeChoice
        return DataTypeString
    elif kind == 'number':
        if rest and rest[0] == 'C':
            return DataTypeNumberChoice
        return DataTypeNumber
    elif kind == 'boolean':
        return DataTypeBoolean
    elif kind == 'string_dict':
        return DataTypeStringDict
    elif kind == 'dict':
        return DataTypeDict
    elif kind == 'list(string)':
        return DataTypeListString
    elif kind == 'string_s':
        return DataTypeListStringSingular
    elif kind == 'list(dict)':
        return DataTypeListDict
    elif kind == 'dict_s':
        return DataTypeListDictSingular
    elif kind == 'list(dict|string)':
        return DataTypeListDictOrString
    elif kind == 'list(list(string))':
        return DataTypeListListString
    elif kind == 'list(string_dict)':
        # return DataTypeListStringDict
        return DataTypeListString  # This is fake, but nobody seems to be using the GUI
    logger.error(f'Not implemented: {kind}')
    raise AssertionError()


class WidgetsSizer(wx.Panel):
    def __init__(self, parent, entries, parent_entry, obj, level, domain, extra_args, advanced=False):
        wx.Panel.__init__(self, parent)

        sizer = wx.BoxSizer(wx.VERTICAL)
        for entry in entries:
            if not entry.skip and (entry.is_basic ^ advanced):
                entry.add_widgets(obj, self, sizer, level, domain, extra_args)
                entry.parent = parent_entry

        self.SetSizer(sizer)
        self.Layout()


def add_widgets(obj, entries, window, sizer, level=0, parent=None, can_remove=True, domain='unknown'):
    if isinstance(obj, type):
        logger.error(f'- !!! {obj.__dict__} {type(obj)}')
        return

    # Compute the len for the largest label
    font = wx.StaticText(window).GetFont()
    dc = wx.ScreenDC()
    dc.SetFont(font)
    dc_emp = wx.ScreenDC()
    dc_emp.SetFont(get_emp_font())
    global max_label
    cur_max = max_label
    # TODO: GetTextExtent failing on bold!!!
    max_label = max((int(dc_emp.GetTextExtent(e.get_label()).width*1.15) if e.is_basic else
                    dc.GetTextExtent(e.get_label()).width for e in entries))
    # This is also wrong:
    # max2 = max((window.GetFullTextExtent(e.name, (get_emp_font() if e.is_basic else None)) for e in entries))
    # Size for input boxes
    global def_text
    def_text = dc.GetTextExtent('M'*40).width

    # logger.error(f'{obj._tree}')
    n_entries = sum((1 for e in entries if not e.skip))
    n_entries_basic = sum((1 for e in entries if not e.skip and not e.is_basic))
    extra_args = {}
    if n_entries == 1:
        extra_args['force_embedded'] = True
    if not can_remove:
        extra_args['dont_remove_first_level'] = True
    if SEPARATE_ADVANCED and n_entries_basic and (n_entries - n_entries_basic):
        # Use a separated panel for basic and advanced
        notebook = wx.Notebook(window, id=create_id(domain+'.notebook'))
        basic = WidgetsSizer(notebook, entries, parent, obj, level, domain, extra_args)
        advanced = WidgetsSizer(notebook, entries, parent, obj, level, domain, extra_args, advanced=True)
        notebook.AddPage(basic, "Basic")
        notebook.AddPage(advanced, "Advanced")
        sizer.Add(notebook, gh.SIZER_FLAGS_1_NO_BORDER)
    else:
        # Basic and advanced options together
        for entry in entries:
            if not entry.skip:
                entry.add_widgets(obj, window, sizer, level, domain, extra_args)
                entry.parent = parent
    max_label = cur_max


class DataEntry(object):
    """ Class to represent one data value to be edited """
    def __init__(self, name, valids, def_val, help, is_basic, obj, level, parent=None, ori_def_val=None):
        self.name = name
        self.valids = valids
        self.def_val = def_val
        self.ori_def_val = ori_def_val
        self.help = '\n'.join((ln.strip() for ln in help.splitlines(True)))
        self.is_dict = any((x.is_dict for x in valids))
        self.is_list_dict = any((x.is_list_dict for x in valids))
        self.is_basic = is_basic
        self.selected = 0
        self.edited = False
        self.obj = obj
        self.skip = self.name == 'type' and level == 0
        self.select_data_type(obj, level)
        self.parent = parent

    def select_data_type(self, obj, level=0):
        # Solve the current value
        user_value = obj._tree.get(self.name)
        if user_value is not None:
            # The user provided a value
            self.user_defined = True
            if isinstance(user_value, (dict, list)):
                # For complex data types we get the configured value
                # They will extract data from the tree
                self.ori_val = getattr(obj, self.name)
            else:
                # If the data is simple, get it from the tree, so the user sees the same found in the YAML
                self.ori_val = user_value
        else:
            # No user provided value
            self.user_defined = False
            # Get the current value in the object
            self.ori_val = getattr(obj, self.name)
            selected, _ = self.get_used_data_type(self.ori_val)
            # Is this usable?
            if self.ori_val is None or isinstance(self.ori_val, type) or selected == -1:
                # Nope, use the default
                self.ori_val = self.def_val
        self.user_defined_ori = self.user_defined
        self.selected, data_type = self.get_used_data_type(self.ori_val)
        if self.selected == -1:  # I.e. optionable not used and hence is None
            self.selected = 0
            try:
                self.ori_val = TYPE_EMPTY[self.valids[0].kind]
            except KeyError:
                logger.error(f'{self.name}: {self.valids[0].kind}')
                raise
        logger.debug(f'{" "*level*2}- {self.name} ori:{self.ori_val} user:{self.user_defined} {data_type} sel:{self.selected}')

    def get_label(self):
        return self.valids[0].get_label(self)

    def show_status(self, label):
        if self.is_basic:
            label.SetFont(get_emp_font())
        if self.user_defined:
            label.SetForegroundColour(gh.USER_EDITED_COLOR)
        else:
            label.SetForegroundColour(self.ori_fore_color)

    def get_used_data_type(self, value):
        data_type = typeof(value, Optionable)
        if isinstance(value, list) and len(value) == 0:
            return next((c for c, v in enumerate(self.valids) if v.is_list), -1), data_type
        return next((c for c, v in enumerate(self.valids) if v.matches_type(data_type)), -1), data_type

    def add_widgets(self, obj, window, sizer, level, domain, extra_args):
        """ Add a widget for each possible data type.
            Also add a control to change the data type.
            Here we bind the entry to the real object, during creation we just got a template (the class) """
        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        is_first = True
        if obj != self.obj:
            # This is common for lists
            self.select_data_type(obj)
            self.obj = obj
        self.widgets = []
        self.dont_remove_first_level = extra_args.get('dont_remove_first_level')
        id_name_base = domain+'.'+self.name
        for c, valid in enumerate(self.valids):
            id_name = id_name_base+'.'+valid.kind
            logger.debugl(2, f'Using id: {id_name}')
            if is_first:
                if len(self.valids) > 1:
                    # Choice to select the data type when multiple are allowed
                    sel = wx.Choice(window, choices=[TYPE_ABREV[v.kind] for v in self.valids],
                                    size=wx.Size(int(def_text/8), -1), id=create_id(id_name_base+'.choices'))
                    sel.SetSelection(self.selected)
                    sel.Bind(wx.EVT_CHOICE, self.OnChoice)
                else:
                    # Just a hint abou the data type
                    sel = wx.StaticText(window, label=TYPE_ABREV[valid.kind], size=wx.Size(60, -1),
                                        style=wx.ALIGN_CENTER)
                # Button to clear the data, and remove it from the YAML
                if not (level == 0 and self.dont_remove_first_level):
                    clr = wx.BitmapButton(window, bitmap=get_res_bitmap(BMP_CLEAR), id=create_id(id_name_base+'.kill'))
                    clr.SetToolTip(f'Reset {self.name}')
                    clr.Bind(wx.EVT_BUTTON, self.OnRemove)
                else:
                    clr = None
                self.ori_fore_color = sel.GetForegroundColour()
                if not TYPE_SEL_RIGHT:
                    flgs = wx.SizerFlags().Border(wx.RIGHT).Center()
                    self.sizer.Add(sel, flgs)
                    if clr:
                        self.sizer.Add(clr, flgs)
                self.sel_widget = sel
                self.clr_widget = clr
            is_selected = c == self.selected
            e_sizer = valid.get_widget(obj, window, self, level, is_selected, self.ori_val, id_name, **extra_args)
            self.sizer.Add(e_sizer, gh.SIZER_FLAGS_1_NO_BORDER)
            self.widgets.append(e_sizer)
            if not is_selected:
                self.sizer.Show(e_sizer, False)
            is_first = False
        if TYPE_SEL_RIGHT:
            flgs = wx.SizerFlags().Border(wx.LEFT).Center()
            self.sizer.Add(sel, flgs)
            if clr:
                self.sizer.Add(clr, flgs)
        if self.user_defined:
            sel.SetForegroundColour(gh.USER_EDITED_COLOR)
        elif clr:
            clr.Disable()
        self.set_sel_tooltip()
        sizer.Add(self.sizer, gh.SIZER_FLAGS_0_NO_BORDER)
        self.parent_sizer = sizer
        self.window = window

    def set_edited(self, edited, widget=None):
        new_user_defined = edited or self.user_defined_ori
        self.edited = edited
        if new_user_defined == self.user_defined:
            changed_status = False
        else:
            self.user_defined = new_user_defined
            self.sel_widget.SetForegroundColour(gh.USER_EDITED_COLOR if new_user_defined else self.ori_fore_color)
            if self.clr_widget:
                self.clr_widget.Enable(new_user_defined)
            if widget:
                self.show_status(widget)
            changed_status = True
        # We always try to notify our parent, even if this isn't a change from our point of view.
        # This is needed when we have default values that correspond to a tree={} and our parent need to know that the user
        # modified these values.
        if self.parent_embedded():
            self.parent.set_edited(new_user_defined)
        return changed_status

    def parent_embedded(self):
        if self.parent is None:
            return False
        dt = self.parent.valids[self.parent.selected]
        if not dt.is_dict:
            return False
        return dt.embedded

    def get_value(self):
        return self.valids[self.selected].get_value() if self.user_defined else None

    def update_value(self):
        if not self.user_defined or not self.edited:
            return
        self.ori_val = self.get_value()

    def set_sel_tooltip(self):
        if len(self.valids) == 1:
            sel_tooltip = f'{TYPE_ABREV[self.valids[0].kind]}: {self.valids[0].kind}'
        else:
            sel_tooltip = ''
            for c, valid in enumerate(self.valids):
                sel_tooltip += ('→' if c == self.selected else '   ') + f' {TYPE_ABREV[valid.kind]}: {valid.kind}\n'
            sel_tooltip = sel_tooltip[:-1]
        self.sel_widget.SetToolTip(sel_tooltip)

    def OnChoice(self, event):
        """ A new data type was selected.
            Hide the current widget and show the new one """
        self.sizer.Show(self.widgets[self.selected], False)
        self.selected = self.sel_widget.GetSelection()
        self.sizer.Show(self.widgets[self.selected], True)
        # Show isn't supposed to be recursive ... but we need to adjust this
        sel_dt = self.valids[self.selected]
        if sel_dt.is_dict and sel_dt.embedded:
            for e in sel_dt.sub_entries:
                e.update_shown()
        self.set_sel_tooltip()
        send_relayout_event(self.window)

    def update_shown(self):
        for c, w in enumerate(self.widgets):
            self.valids[c].update_shown(self.sizer, w, c == self.selected)

    def OnRemove(self, event):
        if pop_confirm(f'Remove the data from {self.name}?') == wx.YES:
            self.user_defined_ori = False
            sel_dt = self.valids[self.selected]
            # Reset the selected data
            sel_dt.reset()
            # Sync
            self.ori_val = sel_dt.get_value()


def adapt_default(val, name):
    if val is None:
        pass
    elif val[0] == "'" and val[-1] == "'":
        val = val[1:-1]
    elif val == '[]':
        val = []
    elif val == '{}':
        val = {}
    elif val == '[{}]':
        val = [{}]
    elif val == 'true':
        val = True
    elif val == 'false':
        val = False
    elif val[0] in {'-', '1', '2', '3', '4', '5', '6', '7', '8', '9', '0'}:
        val = float(val)
    elif val == '?':
        # Means we don't know because this is filled by the config()
        return None
    elif val == 'null':
        # Explicit None
        return None
    else:
        logger.error(f'Unknown default data type `{val}` for `{name}`')
    return val


def join_lists(valid, extra):
    # When we have things like list(dict)|list(string) in practice it means list(dict|string)
    # So here we apply this conversion
    list_index = None
    new_valid = []
    new_extra = []
    for c, (v, e) in enumerate(zip(valid, extra)):
        if v.startswith('list('):
            if list_index is None:
                # First list
                list_index = c
                v = v[:-1]
            else:
                # We have another list
                kind = v[5:-1]
                new_valid[list_index] += '|'+kind
                if e is not None:
                    assert new_extra[list_index] is None
                    new_extra[list_index] = e
                continue
        new_valid.append(v)
        new_extra.append(e)
    if list_index is not None:
        new_valid[list_index] += ')'
    # Optimize the list(string)|string, named "string_s"
    try:
        li = new_valid.index('list(string)')
        ls = new_valid.index('string')
        new_valid[li] = 'string_s'
        del new_valid[ls]
        del new_extra[ls]
    except ValueError:
        pass
    # Optimize the list(dict)|dict, named "dict_s"
    try:
        li = new_valid.index('list(dict)')
        ls = new_valid.index('dict')
        new_valid[li] = 'dict_s'
        del new_valid[ls]
        del new_extra[ls]
    except ValueError:
        pass
    return new_valid, new_extra


def get_data_type_tree(template, obj, level=0, parent=None):
    """ Create a tree containing all the DataEntry objects associated to the data in the *obj* output """
    entries = []
    logger.debug(f'{" "*level*2}Starting data tree for {template.__repr__()} '
                 f'(type: {type(template)}) with {obj.__repr__()} as value')
    for k, v in template.get_attrs_gen():
        help, _, is_alias = template.get_doc(k)
        if help is None or is_alias:
            if not is_alias and k != 'type':
                logger.error(k)
            continue
        is_basic = False
        if help[0] == '*':
            help = help[1:]
            is_basic = True
        case = f'{k} = `{v}`'
        valid, extra, ori_def_val, real_help = template.get_valid_types(help)
        def_val = adapt_default(ori_def_val, k)
        valid, extra = join_lists(valid, extra)
        valids = [get_class_for(v, e)(v, e, def_val, k) for v, e in zip(valid, extra)]
        case += f' {extra} """ {help} """'
        assert valids, case
        valids = sorted(valids, key=lambda x: 200-TYPE_PRIORITY[x.kind])
        obj_ref = obj
        if isinstance(obj, list):
            # list(dict)
            if len(obj) == 0:
                obj_ref = template
            else:
                obj_ref = obj[0]
        entry = DataEntry(k, valids, def_val, real_help, is_basic, obj_ref, level, ori_def_val=ori_def_val)
        entry.cls = v if isinstance(v, type) else None
        if entry.is_dict:
            value = getattr(obj, k)
            reference = v()
            # if value is None or isinstance(value, type):
            if not isinstance(value, v):
                # If the current value is different use an empty object
                # I.e. something that can be a string or dict and is currently a string, then use a fresh dict
                value = reference
                logger.debug(f'{" "*level*2}- Using new object for {k}')
            entry.sub = get_data_type_tree(reference, value, level+1, entry)
        elif entry.is_list_dict:
            o = v()
            entry.sub = get_data_type_tree(o, o, level+1)
        entries.append(entry)
    return entries
