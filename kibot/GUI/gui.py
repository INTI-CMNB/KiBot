# -*- coding: utf-8 -*-
# Copyright (c) 2024 Salvador E. Tropea
# Copyright (c) 2024 Instituto Nacional de Tecnologïa Industrial
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)
#
# Graphic User Interface
from copy import deepcopy
import os
import platform
import sys
import tempfile
import threading
import webbrowser
import yaml
from .. import __version__, __copyright__, __url__, __email__
from .. import log
from ..config_reader import get_doc_lines
from ..gs import GS
from ..kiplot import config_output, load_board, load_sch, load_config, reset_config, generate_outputs
from ..misc import BASE_HELP, W_LANGNOTA
from ..pre_base import BasePreFlight
from ..registrable import RegOutput, Group, GroupEntry, RegFilter, RegVariant
from .data_types import edit_dict, create_new_optionable
from .gui_helpers import (move_sel_up, move_sel_down, remove_item, pop_error, get_client_data, pop_info, ok_cancel,
                          set_items, get_selection, init_vars, choose_from_list, add_abm_buttons, input_label_and_text,
                          set_button_bitmap, pop_confirm)
from .gui_inject import create_id, InjectDialog
from . import gui_setups
from . import gui_helpers as gh
from .gui_log import start_gui_log, stop_gui_log, EVT_WX_LOG_EVENT

logger = log.get_logger()

import wx
import wx.lib.newevent
# Do it before any wx thing is called
app = wx.App()
if hasattr(app, "GTKSuppressDiagnostics"):
    app.GTKSuppressDiagnostics()
if hasattr(wx, "APP_ASSERT_SUPPRESS"):
    app.SetAssertMode(wx.APP_ASSERT_SUPPRESS)
if hasattr(wx, "DisableAsserts"):
    wx.DisableAsserts()
if hasattr(wx, "GetLibraryVersionInfo"):
    WX_VERSION = wx.GetLibraryVersionInfo()  # type: wx.VersionInfo
    WX_VERSION = (WX_VERSION.Major, WX_VERSION.Minor, WX_VERSION.Micro)
else:
    # old kicad used this (exact version doesn't matter)
    WX_VERSION = (3, 0, 2)

# ################################################
# i18n
# ################################################
# Define _() as wx.GetTranslation
import builtins
builtins.__dict__['_'] = wx.GetTranslation
# Add ../locale as a place to look for catalogs
wx.Locale.AddCatalogLookupPathPrefix(os.path.join(os.path.dirname(__file__), '..', 'locale'))
# Select the language
lang = os.environ.get('LANG', 'C')[:2]
from .gui_config import lang_domain, sup_lang
selected_language = sup_lang.get(lang, wx.LANGUAGE_DEFAULT)
# Avoid a nasty dialog (GUI people!!!) by asking if available
if wx.Locale.IsAvailable(selected_language):
    locale = wx.Locale(selected_language)
    # Add KiBot domain
    if locale.IsOk():
        locale.AddCatalog(lang_domain)
    else:
        locale = None
elif lang != 'C':
    name = wx.Locale.GetLanguageName(selected_language)
    logger.warning(W_LANGNOTA+f'Error setting the current locale ({lang}: {name}), please install it')
# ################################################

OK_CHAR = '\U00002714'
# NOT_OK_CHAR = '\U0000274C'
NOT_OK_CHAR = '\U00002717'
TARGETS_ORDER = [_("Sort by priority"), _("Declared"), _("Selected"), _("Invert selection")]
ORDER_PRIORITY = 0
ORDER_DECLARED = 1
ORDER_SELECTED = 2
ORDER_INVERT = 3
max_label = 200
def_text = 200
COLORS = {"Y": wx.YELLOW, "R": wx.RED, "C": wx.CYAN, "r": wx.Colour("violet red")}
wxFinishEvent, EVT_WX_FINISH_EVENT = wx.lib.newevent.NewEvent()
wxProgressEvent, EVT_WX_PROGRESS_EVENT = wx.lib.newevent.NewEvent()
init_vars()


def do_gui(cfg_file, targets, invert_targets, skip_pre, cli_order, no_priority):
    gui_setups.init()
    # Configure all outputs
    # Note that this will load the schematic and/or PCB if needed
    for o in RegOutput.get_outputs():
        config_output(o)
    # Check that we have some global options
    if GS.globals_tree is None:
        # Nope, we didn't load a config, so go for defaults
        glb = GS.set_global_options_tree({})
        glb.config(None)
    dlg = MainDialog(cfg_file, targets, invert_targets, skip_pre, cli_order, no_priority)
    dlg.ShowModal()
    dlg.Destroy()
    gui_setups.save_setups()


# ##########################################################################
# # Class MainDialog
# # The main dialog for the GUI
# ##########################################################################

class MainDialog(InjectDialog):
    def __init__(self, cfg_file, targets, invert_targets, skip_pre, cli_order, no_priority):
        InjectDialog.__init__(self, None, title='KiBot '+__version__, name='main_dialog',
                              style=wx.DEFAULT_DIALOG_STYLE | wx.DIALOG_NO_PARENT | wx.STAY_ON_TOP | wx.BORDER_DEFAULT)

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.notebook = wx.Notebook(self, id=create_id('ID_MAIN_NOTEBOOK'))
        main_sizer.Add(self.notebook, gh.SIZER_FLAGS_1)

        # Pages for the notebook
        self.main = MainPanel(self.notebook, self, cfg_file, targets, invert_targets, skip_pre, cli_order, no_priority,
                              'introduction.html')
        self.notebook.AddPage(self.main, _("Main"))
        self.outputs = OutputsPanel(self.notebook, 'configuration/outputs.html')
        self.outputs.SetToolTip(_("Defined outputs.\nThings you can generate pressing the Run button"))
        self.notebook.AddPage(self.outputs, _("Outputs"))
        self.groups = GroupsPanel(self.notebook, 'configuration/outputs.html#grouping-outputs')
        self.groups.SetToolTip(_("Groups of outputs.\n"
                                 "This makes easier to run some and exclude others.\n"
                                 "A group can contain another group."))
        self.notebook.AddPage(self.groups, _("Groups"))
        self.preflights = PreflightsPanel(self.notebook, 'configuration/preflight.html')
        self.preflights.SetToolTip(_("Tasks executed before generating outputs.\n"
                                     "I.e. run the DRC and or ERC."))
        self.notebook.AddPage(self.preflights, _("Preflights"))
        self.filters = FiltersPanel(self.notebook, 'configuration/filters.html')
        self.filters.SetToolTip(_("Defined filters.\n"
                                  "Used to include or exclude certain components.\n"
                                  "Some filters can apply transformations to components."))
        self.notebook.AddPage(self.filters, _("Filters"))
        self.variants = VariantsPanel(self.notebook, 'configuration/filters.html#supported-variants')
        self.variants.SetToolTip(_("Assembly variants for your project.\n"
                                   "Same PCB for different products."))
        self.notebook.AddPage(self.variants, _("Variants"))
        self.about = AboutPanel(self.notebook, 'credits.html')
        self.notebook.AddPage(self.about, _("About"))

        # Buttons
        but_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.but_help = wx.Button(self, wx.ID_HELP, name='main.help')
        but_sizer.Add(self.but_help, gh.SIZER_FLAGS_0_NO_EXPAND)
        # Save config
        self.but_save = wx.Button(self, label=_("Save config"), id=create_id('ID_SAVE'))
        self.but_save.Disable()
        self.but_save.SetToolTip(_("Save the current state to the `Config file' (Main tab)"))
        set_button_bitmap(self.but_save, wx.ART_FILE_SAVE)
        but_sizer.Add(self.but_save, gh.SIZER_FLAGS_0_NO_EXPAND)
        # Edit globals
        self.but_globals = wx.Button(self, label=_("Globals"), id=create_id('ID_GLOBALS'))
        set_button_bitmap(self.but_globals, "gtk-edit")
        self.but_globals.SetToolTip(_("Global configuration options, applies to all outputs"))
        but_sizer.Add(self.but_globals, gh.SIZER_FLAGS_0_NO_EXPAND)
        # Recent
        self.but_recent = wx.Button(self, label=_("Recent"), id=create_id('ID_RECENT'))
        self.but_recent.SetToolTip(_("Recently used setups.\n"
                                     "Files and directories recently used"))
        but_sizer.Add(self.but_recent, gh.SIZER_FLAGS_0_NO_EXPAND)
        # Warnings
        self.but_warn = wx.Button(self, label=_("Warnings"), id=create_id('ID_WARNINGS'))
        self.but_warn.SetToolTip(_("Warnings issued on this run.\n"
                                   "Note that they are reported just once.\n"
                                   "Here are all the issued warnings"))
        set_button_bitmap(self.but_warn, wx.ART_WARNING)
        but_sizer.Add(self.but_warn, gh.SIZER_FLAGS_0_NO_EXPAND)
        #
        # Separator
        #
        but_sizer.Add((50, 0), gh.SIZER_FLAGS_1_NO_BORDER)
        # Run
        self.but_generate = wx.Button(self, label=_("Run"), id=create_id('ID_GENERATE'))
        self.but_generate.SetToolTip(_("Run preflights and generate the outputs (targets)"))
        set_button_bitmap(self.but_generate, wx.ART_EXECUTABLE_FILE)
        # Setting the generate button as default interferes with list boxes on GTK
        # They convert the RETURN key to a double-click event, but, somehow, it also triggers the default button
        # self.but_generate.SetDefault()
        but_sizer.Add(self.but_generate, gh.SIZER_FLAGS_0_NO_EXPAND)
        # Cancel
        self.but_cancel = wx.Button(self, id=wx.ID_CANCEL, label=_("Cancel"))
        but_sizer.Add(self.but_cancel, gh.SIZER_FLAGS_0_NO_EXPAND)
        main_sizer.Add(but_sizer, gh.SIZER_FLAGS_0_NO_BORDER)

        self.SetSizer(main_sizer)
        main_sizer.Fit(self)
        self.Centre(wx.BOTH)

        self.edited = False

        # Connect Events
        self.but_help.Bind(wx.EVT_BUTTON, self.OnHelp)
        self.but_save.Bind(wx.EVT_BUTTON, self.OnSave)
        self.but_generate.Bind(wx.EVT_BUTTON, self.OnGenerateOuts)
        self.but_globals.Bind(wx.EVT_BUTTON, self.OnGlobals)
        self.but_recent.Bind(wx.EVT_BUTTON, self.OnRecent)
        self.but_warn.Bind(wx.EVT_BUTTON, self.OnWarnings)
        self.but_cancel.Bind(wx.EVT_BUTTON, self.OnExit)
        self.Bind(wx.EVT_CLOSE, self.OnExit)

        self.flag = False

    def ask_save(self):
        res = pop_confirm(_('The configuration is changed, save?'))
        if res == wx.CANCEL:
            return False
        if res == wx.YES:
            self.OnSave(None)
            if self.edited:
                # Something went wrong, give the user a chance to retry saving
                return False
        return True

    def OnRecent(self, event):
        s = gui_setups.get_valid_setups(self.get_setup())
        if not s:
            pop_error(_('No recent runs'))
            return
        if len(s) == 1:
            if pop_confirm(_('Only one recent use with `{}`, use it?').format(os.path.basename(s[0].config))) == wx.YES:
                self.apply_setup(s[0])
            return
        setup = choose_from_list(self, s, what=_("setup"), search_on=[os.path.basename(i.config) for i in s])
        if setup is not None:
            self.apply_setup(setup)

    def apply_setup(self, s):
        # Do we need to save changes?
        cur_cfg_file = self.main.get_cfg_file()
        if s.config != cur_cfg_file and self.edited and not self.ask_save():
            return
        # Apply it
        if self.main.apply_setup(s):
            # Make this one the more recent
            self.add_setup()

    def OnExit(self, event):
        if self.edited and not self.ask_save():
            return
        self.EndModal(wx.ID_OK)

    def refresh_cfg(self):
        """ Refresh panels after loading a new config """
        self.outputs.refresh_lbox()
        self.refresh_groups()
        self.preflights.refresh_lbox()
        self.filters.refresh_lbox()
        self.variants.refresh_lbox()

    def refresh_groups(self):
        self.groups.refresh_groups()

    def mark_edited(self):
        if not self.edited:
            self.but_save.Enable(True)
        self.edited = True

    def check_save(self):
        if not self.edited:
            return wx.YES
        res = pop_confirm(_('Configuration changed, save?'))
        if res == wx.YES:
            self.OnSave(None)
        return res

    def OnGlobals(self, event):
        obj = GS.set_global_options_tree(GS.globals_tree)
        if edit_dict(self, obj, None, None, title=_("Global options")):
            self.mark_edited()
            GS.globals_tree = obj._tree
        logger.debug(f'Global options after editing: {GS.globals_tree}')

    def OnWarnings(self, event):
        if not logger.warn_cnt:
            pop_info(_("No warnings"))
            return
        dlg = ShowWarnsDialog(self, logger.warn_hash.keys())
        dlg.ShowModal()
        dlg.Destroy()

    def relpath(self, path):
        return os.path.relpath(path, self.cwd) if path else path

    def get_setup(self):
        self.cwd = os.getcwd()
        return gui_setups.Setup(self.relpath(self.main.get_cfg_file()), os.getcwd(), self.relpath(GS.out_dir),
                                self.relpath(GS.pcb_file), self.relpath(GS.sch_file))

    def add_setup(self):
        gui_setups.add_setup(self.get_setup())

    def OnGenerateOuts(self, event):
        if not self.outputs.lbox.GetCount() and not self.preflights.lbox.GetCount():
            pop_error(_('Please add outputs and/or preflights first'))
            return
        # Check the output is writable (wrong from CLI?)
        try:
            testfile = tempfile.TemporaryFile(dir=GS.out_dir)
            testfile.close()
        except OSError as e:
            e.filename = GS.out_dir
            pop_error(_('Invalid destination dir:\n')+str(e))
            return
        self.add_setup()
        logger.debug('Starting targets generation from the GUI')
        logger.debug(f'- Working dir: {os.getcwd()}')
        logger.debug(f'- Destination dir: {GS.out_dir}')
        targets = self.main.targets_lbox.GetStrings()
        logger.debug(f'- Targets: {targets}')
        invert_sel, cli_order, no_priority = self.main.split_sort_mode()
        logger.debug(f'- Invert selected: {invert_sel}')
        logger.debug(f'- CLI order: {cli_order}')
        logger.debug(f'- No priority: {no_priority}')
        skip_pre = self.main.skippre_lbox.GetStrings()
        if not skip_pre:
            skip_pre = None
        elif 'all' in skip_pre:
            skip_pre = 'all'
        else:
            skip_pre = ','.join(skip_pre)
        logger.debug(f'- Skip preflights: {skip_pre}')
        try:
            # Clear the done flag so outputs gets generated again
            RegOutput.reset_done()
            # Open a dialog to collect the messages and block the GUI while running
            dlg = RunControlDialog(self, targets, invert_sel, skip_pre, cli_order, no_priority)
            dlg.ShowModal()
            dlg.Destroy()
        except SystemExit:
            pass

    def OnSave(self, event):
        cfg_file = self.main.get_cfg_file()
        if not cfg_file:
            cfg_file = self.main.choose_new_cfg()
            if not cfg_file:
                return
        self.add_setup()
        tree = {'kibot': {'version': 1}}
        # TODO: Should we delegate it to the class handling it?
        # Globals
        if GS.globals_tree:
            tree['globals'] = GS.globals_tree
        # We use the List Box items because they are sorted like the user wants
        # Filters
        if self.filters.lbox.GetCount():
            tree['filters'] = [o._tree for o in get_client_data(self.filters.lbox)]
        # Variants
        if self.variants.lbox.GetCount():
            tree['variants'] = [o._tree for o in get_client_data(self.variants.lbox)]
        # Groups: skipping outputs added from the output itself
        if self.groups.lbox.GetCount():
            grp_lst = []
            for grp in get_client_data(self.groups.lbox):
                items = [g.item for g in grp.items if g.is_from_top()]
                if items:
                    grp_lst.append({'name': grp.name, 'outputs': items})
            if grp_lst:
                tree['groups'] = grp_lst
        # Preflights
        if self.preflights.lbox.GetCount():
            res = {}
            for o in get_client_data(self.preflights.lbox):
                res.update(o._tree)
            tree['preflight'] = res
        # Outputs
        if self.outputs.lbox.GetCount():
            tree['outputs'] = [o._tree for o in get_client_data(self.outputs.lbox)]
        if os.path.isfile(cfg_file):
            logger.debug(f'Creating back-up for {cfg_file}')
            os.rename(cfg_file, os.path.join(os.path.dirname(cfg_file), '.'+os.path.basename(cfg_file)+'~'))
        logger.debug(f'Saving config to {cfg_file}')
        with open(cfg_file, 'wt') as f:
            f.write(yaml.dump(tree, sort_keys=False))
        self.edited = False
        self.but_save.Disable()
        # When we disable the button nothing is focused, so things like ESC stops working
        self.notebook.SetFocus()

    def OnHelp(self, event):
        current_panel = self.notebook.GetCurrentPage()
        webbrowser.open(BASE_HELP+current_panel.help_domain)


# ##########################################################################
# # class DictPanel
# # Base class for the outputs and filters ABMs
# ##########################################################################

class DictPanel(wx.Panel):
    def __init__(self, parent, help):
        wx.Panel.__init__(self, parent, name=self.dict_type+'.panel')
        self.can_remove_first_level = True
        self.help_domain = help

        # All the widgets
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        #  List box + buttons
        abm_sizer = wx.BoxSizer(wx.HORIZONTAL)
        #   List box
        list_sizer = wx.BoxSizer(wx.VERTICAL)
        self.lbox = wx.ListBox(self, choices=[], style=wx.LB_SINGLE)
        self.refresh_lbox()
        list_sizer.Add(self.lbox, gh.SIZER_FLAGS_1)
        abm_sizer.Add(list_sizer, gh.SIZER_FLAGS_1_NO_BORDER)
        #   Buttons at the right
        abm_sizer.Add(add_abm_buttons(self, id=self.dict_type), gh.SIZER_FLAGS_0_NO_EXPAND)
        main_sizer.Add(abm_sizer, gh.SIZER_FLAGS_1_NO_BORDER)

        self.SetSizer(main_sizer)
        self.Layout()

        # Connect Events
        self.lbox.Bind(wx.EVT_LISTBOX_DCLICK, self.OnItemDClick)
        self.but_up.Bind(wx.EVT_BUTTON, self.OnUp)
        self.but_down.Bind(wx.EVT_BUTTON, self.OnDown)
        self.but_add.Bind(wx.EVT_BUTTON, self.OnAdd)
        self.but_remove.Bind(wx.EVT_BUTTON, self.OnRemove)

    def mark_edited(self):
        self.Parent.Parent.mark_edited()

    def OnItemDClick(self, event):
        index, string, obj = get_selection(self.lbox)
        if obj is None:
            return False
        self.editing = obj
        self.pre_edit(obj)
        name = self.dict_type+'.'+obj.type
        if edit_dict(self, obj, None, None, title=self.dict_type.capitalize()+" "+str(obj), validator=self.validate,
                     can_remove=self.can_remove_first_level, name=name):
            self.mark_edited()
            self.lbox.SetString(index, str(obj))
            return True
        return False

    def pre_edit(self, obj):
        pass

    def validate(self, obj):
        if not obj.name:
            pop_error(_('You must provide a name for the ')+self.dict_type)
            return False
        same_name = next((o for o in get_client_data(self.lbox) if o.name == obj.name), None)
        if same_name is not None and same_name != self.editing:
            pop_error(_('The `{}` name is already used by {}').format(obj.name, same_name))
            return False
        return True

    def OnUp(self, event):
        if move_sel_up(self.lbox):
            self.mark_edited()

    def OnDown(self, event):
        if move_sel_down(self.lbox):
            self.mark_edited()

    def OnAdd(self, event):
        kind = self.choose_type()
        if kind is None:
            return
        # Create a new object of the selected type
        self.editing = obj = self.new_obj(kind)
        name = self.dict_type+'.'+kind
        if edit_dict(self, obj, None, None, title=_("New")+' '+kind+' '+self.dict_type, validator=self.validate,
                     force_changed=True, can_remove=self.can_remove_first_level, name=name):
            self.lbox.Append(str(obj), obj)
            self.mark_edited()
            self.add_obj(obj)

    def OnRemove(self, event):
        if remove_item(self.lbox, confirm=_('Are you sure you want to remove the `{}` ')+_(self.dict_type)+'?',
                       callback=self.remove_obj):
            self.mark_edited()


# ##########################################################################
# # Class MainPanel
# # Panel containing the main options (paths, targets, etc.)
# ##########################################################################

class MainPanel(wx.Panel):
    def __init__(self, parent, main, cfg_file, targets, invert_targets, skip_pre, cli_order, no_priority, help):
        wx.Panel.__init__(self, parent)
        self.main = main
        self.help_domain = help

        # All the widgets
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Paths
        paths_sizer = wx.StaticBoxSizer(wx.VERTICAL, self, _('Paths'))
        self.path_w = paths_sizer.GetStaticBox()
        self.path_w.SetToolTip(_("Files and directories used for the Run"))
        cwd = os.getcwd()
        if not os.path.isdir(GS.out_dir):
            os.makedirs(GS.out_dir)
        self.wd_sizer, self.wd_input, _d = self.add_path(paths_sizer, _('Working dir'), cwd, 'ID_CWD',
                                                         _("All execution is performed here"), self.OnChangeCWD, is_dir=True)
        self.old_cwd = cwd
        if cfg_file:
            cfg_file = os.path.abspath(cfg_file)
        self.cf_sizer, self.cf_input, self_ren_but = self.add_path(paths_sizer, _('Config file'), cfg_file, 'ID_CFG_FILE',
                                                                   _("YAML file for the configuration"), self.OnChangeCfg,
                                                                   rename=self.OnChangeName)
        self.old_cfg = cfg_file
        out_dir = os.path.abspath(GS.out_dir)
        self.de_sizer, self.de_input, _d = self.add_path(paths_sizer, _('Destination'), out_dir, 'ID_DEST',
                                                         _("Base directory to store the results"), self.OnChangeOutDir,
                                                         is_dir=True)
        self.old_out_dir = out_dir
        sch = GS.sch_file if GS.sch_file is not None else ''
        self.sch_sizer, self.sch_input, _d = self.add_path(paths_sizer, _('Schematic'), sch, 'ID_SCH',
                                                           _("Schematic used, usually the top-level"), self.OnChangeSCH)
        pcb = GS.pcb_file if GS.pcb_file is not None else ''
        self.pcb_sizer, self.pcb_input, _d = self.add_path(paths_sizer, _('PCB'), pcb, 'ID_PCB',
                                                           _("PCB used for the generated outputs"), self.OnChangePCB)

        # Targets
        targets_sizer = wx.StaticBoxSizer(wx.VERTICAL, self, _('Targets'))
        self.targets_w = targets_sizer.GetStaticBox()
        self.targets_w.SetToolTip(_("What is generated by the Run button"))
        self.add_targets(targets_sizer, self.targets_w, targets, invert_targets, cli_order, no_priority)

        # Skip preflights
        skippre_sizer = wx.StaticBoxSizer(wx.VERTICAL, self, _('Skip preflights'))
        self.skippre_w = skippre_sizer.GetStaticBox()
        self.skippre_w.SetToolTip(_("Preflights that will be skipped.\n"
                                    "Leave it empty to run all preflights.\n"
                                    "Include the `all' name to skip all."))
        self.add_skippre(skippre_sizer, self.skippre_w, self.solve_skip_pre(skip_pre))

        # Targets & Skip pre
        lboxes_sizer = wx.BoxSizer(wx.HORIZONTAL)
        lboxes_sizer.Add(targets_sizer, gh.SIZER_FLAGS_1)
        lboxes_sizer.Add(skippre_sizer, gh.SIZER_FLAGS_1)

        # Paths on top of (Targets & Skip pre)
        main_sizer.Add(paths_sizer, gh.SIZER_FLAGS_0)
        main_sizer.Add(lboxes_sizer, gh.SIZER_FLAGS_1)

        self.SetSizer(main_sizer)
        self.Layout()

        # Connect Events
        # Targets
        self.but_up_targets.Bind(wx.EVT_BUTTON, self.OnUpTargets)
        self.but_down_targets.Bind(wx.EVT_BUTTON, self.OnDownTargets)
        self.but_add_targets.Bind(wx.EVT_BUTTON, self.OnAddTargets)
        self.but_remove_targets.Bind(wx.EVT_BUTTON, self.OnRemoveTargets)
        self.invert_targets_input.Bind(wx.EVT_CHOICE, self.OnChangeSortMode)
        # Skip preflights
        self.but_up_skippre.Bind(wx.EVT_BUTTON, self.OnUpSkippre)
        self.but_down_skippre.Bind(wx.EVT_BUTTON, self.OnDownSkippre)
        self.but_add_skippre.Bind(wx.EVT_BUTTON, self.OnAddSkippre)
        self.but_remove_skippre.Bind(wx.EVT_BUTTON, self.OnRemoveSkippre)

    def choose_new_cfg(self):
        dlg = wx.FileDialog(self, _("Save to file:"), ".", "", "YAML (*.kibot.yaml)|*.kibot.yaml", wx.FD_SAVE)
        if dlg.ShowModal() != wx.ID_OK:
            return None
        cfg_file = dlg.GetPath()
        dlg.Destroy()
        name, ext = os.path.splitext(cfg_file)
        if not ext:
            cfg_file = name+'.kibot.yaml'
        if os.path.isfile(cfg_file):
            # Confirm overwrite
            if pop_confirm(os.path.basename(cfg_file)+_(' already exists, overwrite?')) != wx.YES:
                return None
        wx.CallAfter(self.change_cfg, cfg_file)
        return cfg_file

    def change_cfg(self, cfg):
        self.cf_input.SetPath(cfg)
        self.Parent.Parent.mark_edited()

    def OnChangeName(self, event):
        self.choose_new_cfg()

    def revert_cfg(self, reload=False):
        self.cf_input.SetPath(self.old_cfg)
        if reload:
            reset_config()
            load_config(self.old_cfg)

    def apply_changed_config(self, new_cfg):
        try:
            log.start_recording_error_msgs()
            reset_config()
            load_config(new_cfg)
        except SystemExit:
            return False
        finally:
            # Inform any error issued by logger.error
            msgs = log.stop_recording_error_msgs()
            if msgs:
                pop_error(msgs)
        return True

    def load_new_config(self):
        # Should we save the current?
        res = self.main.check_save()
        if res == wx.CANCEL:
            # Cancelled, revert
            wx.CallAfter(self.revert_cfg)
            return
        # Check the file is there, shouldn't be necessary
        new_cfg = self.cf_input.GetPath()
        if not self.check_changed_filename(new_cfg, _('config')):
            wx.CallAfter(self.revert_cfg)
            return
        # Try loading it
        if not self.apply_changed_config(new_cfg):
            wx.CallAfter(self.revert_cfg, reload=True)
            return
        self.old_cfg = new_cfg
        self.main.refresh_cfg()

    def OnChangeCfg(self, event):
        wx.CallAfter(self.load_new_config)

    def revert_pcb(self, reload=False):
        """ Revert the selected PCB """
        if not GS.pcb_file:
            self.pcb_input.SetPath('')
            return
        self.pcb_input.SetPath(GS.pcb_file)
        if reload:
            load_board(forced=True)

    def apply_changed_pcb(self, new_pcb):
        try:
            log.start_recording_error_msgs()
            load_board(new_pcb, forced=True)
            GS.set_pcb(new_pcb)
        except SystemExit:
            return False
        finally:
            # Inform any error issued by logger.error
            msgs = log.stop_recording_error_msgs()
            if msgs:
                pop_error(msgs)
        return True

    def check_changed_filename(self, name, kind):
        if not os.path.isfile(name):
            pop_error(_("The selected {} is not a file!\n{}").format(kind, name))
            return False
        if not os.access(name, os.R_OK):
            pop_error(_("No permission to read the selected {}!\n{}").format(kind, name))
            return False
        return True

    def check_changed_dirname(self, name, kind):
        if not os.path.isdir(name):
            pop_error(_("The selected {} is not a directory!\n{}").format(kind, name))
            return False
        if not os.access(name, os.R_OK | os.X_OK):
            pop_error(_("No permission to access the selected {}!\n{}").format(kind, name))
            return False
        return True

    def OnChangePCB(self, event):
        new_pcb = self.pcb_input.GetPath()
        if not self.check_changed_filename(new_pcb, _('PCB')):
            # Wrong file name, revert it
            wx.CallAfter(self.revert_pcb)
            return
        if not self.apply_changed_pcb(new_pcb):
            # The PCB failed to load, revert the file name and make sure we have a valid one in memory
            wx.CallAfter(self.revert_pcb, reload=True)
            return
        # Success
        if GS.sch is None:
            # Try using the corresponding SCH
            new_sch = GS.pcb_no_ext+'.kicad_sch'
            if os.path.isfile(new_sch):
                try:
                    load_sch(new_sch, forced=True)
                    GS.set_sch(new_sch)
                    self.sch_input.SetPath(new_sch)
                except SystemExit:
                    GS.sch = None

    def revert_sch(self, reload=False):
        """ Revert the selected PCB """
        if not GS.sch_file:
            self.sch_input.SetPath('')
            return
        self.sch_input.SetPath(GS.sch_file)
        if reload:
            load_sch(forced=True)

    def apply_changed_sch(self, new_sch):
        try:
            log.start_recording_error_msgs()
            load_sch(new_sch, forced=True)
            GS.set_sch(new_sch)
        except SystemExit:
            return False
        finally:
            # Inform any error issued by logger.error
            msgs = log.stop_recording_error_msgs()
            if msgs:
                pop_error(msgs)
        return True

    def check_changed_sch(self, new_sch):
        if not os.path.isfile(new_sch):
            pop_error(_("The selected schematic is not a file!"))
            return False
        if not os.access(new_sch, os.R_OK):
            pop_error(_("No permission to read the selected schematic!"))
            return False
        return True

    def OnChangeSCH(self, event):
        new_sch = self.sch_input.GetPath()
        if not self.check_changed_filename(new_sch, _('schematic')):
            wx.CallAfter(self.revert_sch)
            return
        if not self.apply_changed_sch(new_sch):
            # The sch failed to load, revert the file name
            wx.CallAfter(self.revert_sch, reload=True)
            return
        # Success
        if GS.board is None:
            # Try using the corresponding PCB
            new_pcb = GS.sch_no_ext+'.kicad_pcb'
            if os.path.isfile(new_pcb):
                try:
                    load_board(new_pcb, forced=True)
                    GS.set_pcb(new_pcb)
                    self.pcb_input.SetPath(new_pcb)
                except SystemExit:
                    GS.board = None

    def check_changed_outdir(self, name):
        if not os.path.isdir(name):
            # Doesn't exist, try to create it
            try:
                os.makedirs(name)
            except Exception:
                pass
        if not self.check_changed_dirname(name, _('destination dir')):
            return False
        # A more strict check, trying to actually write there
        try:
            testfile = tempfile.TemporaryFile(dir=name)
            testfile.close()
        except OSError as e:
            e.filename = name
            pop_error(_('Invalid destination dir:\n')+str(e))
            return False
        return True

    def OnChangeOutDir(self, event):
        new_out_dir = self.de_input.GetPath()
        if self.check_changed_outdir(new_out_dir):
            self.old_out_dir = GS.out_dir = new_out_dir
        else:
            self.de_input.SetPath(self.old_out_dir)

    def OnChangeCWD(self, event):
        new_cwd = self.wd_input.GetPath()
        if not self.check_changed_dirname(new_cwd, _('working dir')):
            self.wd_input.SetPath(self.old_cwd)
            return
        try:
            os.chdir(new_cwd)
            self.old_cwd = new_cwd
        except OSError as e:
            pop_error(_('Invalid working dir:\n')+str(e))
            self.wd_input.SetPath(self.old_cwd)

    def OnUpTargets(self, event):
        move_sel_up(self.targets_lbox)

    def OnDownTargets(self, event):
        move_sel_down(self.targets_lbox)

    def OnRemoveTargets(self, event):
        remove_item(self.targets_lbox)
        self.update_targets_hint()

    def OnAddTargets(self, event):
        selected = set(self.targets_lbox.GetStrings())
        available = [o.name for o in RegOutput.get_outputs() if o.name not in selected]
        if not available:
            pop_error(_('No outputs available to add'))
            return
        outs = choose_from_list(self, available, what=_("output"), multiple=True, search_on=available)
        if not outs:
            return
        self.targets_lbox.Append(outs)
        self.update_targets_hint()

    def OnUpSkippre(self, event):
        move_sel_up(self.skippre_lbox)

    def OnDownSkippre(self, event):
        move_sel_down(self.skippre_lbox)

    def OnRemoveSkippre(self, event):
        remove_item(self.skippre_lbox)
        self.update_pre_hint()

    def OnAddSkippre(self, event):
        selected = set(self.skippre_lbox.GetStrings())
        available = [o for o in BasePreFlight.get_in_use_names() if o not in selected]
        if 'all' not in selected:
            available.append('all')
        if not available:
            pop_error(_('No preflights available to add'))
            return
        preflights = choose_from_list(self, available, what=_("preflight"), multiple=True, search_on=available)
        if not preflights:
            return
        self.skippre_lbox.Append(preflights)
        self.update_pre_hint()

    def add_targets(self, sizer, window, targets, invert_targets, cli_order, no_priority):
        # Sort mode
        invert_targets_sizer = wx.BoxSizer(wx.HORIZONTAL)
        ttip = (_("Sort order and how to interpret the list.\n"
                  "Sort by priority: uses the output priority, that you can adjust.\n"
                  "Declared: is the order in which they are declared (see Outputs tab).\n"
                  "Selected: is the order you see in the list.\n"
                  "Invert selection: the list says which ones are excluded (declared order)"))
        new_label = wx.StaticText(window, label=_('Generation order'), size=wx.Size(max_label, -1), style=wx.ALIGN_RIGHT)
        new_label.SetToolTip(ttip)
        self.invert_targets_input = wx.Choice(window, choices=TARGETS_ORDER)
        self.invert_targets_input.SetToolTip(ttip)
        self.invert_targets_input.SetSelection(self.solve_sort_mode(invert_targets, cli_order, no_priority))
        invert_targets_sizer.Add(new_label, gh.SIZER_FLAGS_0_NO_EXPAND)
        invert_targets_sizer.Add(self.invert_targets_input, gh.SIZER_FLAGS_1_NO_EXPAND)
        sizer.Add(invert_targets_sizer, gh.SIZER_FLAGS_0)
        # ABM
        abm_sizer = wx.BoxSizer(wx.HORIZONTAL)
        list_sizer = wx.BoxSizer(wx.VERTICAL)
        self.targets_lbox = wx.ListBox(window, choices=targets, size=wx.Size(def_text, -1),
                                       style=wx.LB_NEEDED_SB | wx.LB_SINGLE)
        self.targets_lbox.SetToolTip(_("List of outputs that will be generated by the Run button.\n"
                                       "Leave it empty to generate all possible outputs."))
        list_sizer.Add(self.targets_lbox, gh.SIZER_FLAGS_1)
        self.target_hint = wx.StaticText(window, label=self.get_targets_hint())
        list_sizer.Add(self.target_hint, wx.SizerFlags().Expand().CentreVertical().Border(wx.LEFT))
        self.sort_hint = wx.StaticText(window, label=self.get_sort_hint())
        list_sizer.Add(self.sort_hint, wx.SizerFlags().Expand().CentreVertical().Border(wx.LEFT | wx.BOTTOM))
        abm_sizer.Add(list_sizer, gh.SIZER_FLAGS_1_NO_BORDER)
        abm_sizer.Add(add_abm_buttons(self, window), gh.SIZER_FLAGS_0_NO_EXPAND)
        sizer.Add(abm_sizer, gh.SIZER_FLAGS_1_NO_BORDER)
        self.but_up_targets = self.but_up
        self.but_down_targets = self.but_down
        self.but_add_targets = self.but_add
        self.but_remove_targets = self.but_remove

    def add_skippre(self, sizer, window, skip_pre):
        #   ABM
        abm_sizer = wx.BoxSizer(wx.HORIZONTAL)
        list_sizer = wx.BoxSizer(wx.VERTICAL)
        self.skippre_lbox = wx.ListBox(window, choices=skip_pre, size=wx.Size(def_text, -1),
                                       style=wx.LB_NEEDED_SB | wx.LB_SINGLE)
        list_sizer.Add(self.skippre_lbox, gh.SIZER_FLAGS_1)
        self.pre_hint = wx.StaticText(window, label=self.get_pre_hint())
        list_sizer.Add(self.pre_hint, wx.SizerFlags().Expand().CentreVertical().Border(wx.LEFT | wx.BOTTOM))
        abm_sizer.Add(list_sizer, gh.SIZER_FLAGS_1_NO_BORDER)
        abm_sizer.Add(add_abm_buttons(self, window), gh.SIZER_FLAGS_0_NO_EXPAND)
        sizer.Add(abm_sizer, gh.SIZER_FLAGS_1_NO_BORDER)
        self.but_up_skippre = self.but_up
        self.but_down_skippre = self.but_down
        self.but_add_skippre = self.but_add
        self.but_remove_skippre = self.but_remove

    def solve_skip_pre(self, skip_pre):
        return [] if skip_pre is None else skip_pre.split(',')

    def solve_sort_mode(self, invert_targets, cli_order, no_priority):
        return ORDER_INVERT if invert_targets else (ORDER_SELECTED if cli_order else (ORDER_DECLARED if no_priority else
                                                                                      ORDER_PRIORITY))

    def split_sort_mode(self):
        sel = self.invert_targets_input.GetSelection()
        invert_targets = cli_order = no_priority = False
        if sel == ORDER_INVERT:
            invert_targets = True
        elif sel == ORDER_SELECTED:
            cli_order = True
        elif sel == ORDER_DECLARED:
            no_priority = True
        return invert_targets, cli_order, no_priority

    def get_cfg_file(self):
        return self.cf_input.GetPath()

    def get_pcb_file(self):
        return self.pcb_input.GetPath()

    def get_sch_file(self):
        return self.sch_input.GetPath()

    def get_out_dir(self):
        return self.de_input.GetPath()

    def get_targets_hint(self):
        items = self.targets_lbox.GetCount()
        sort_mode = self.invert_targets_input.GetSelection()
        if sort_mode == ORDER_INVERT:
            # Inverted selection
            if not items:
                return _('No target targets will be generated')
            if items == 1:
                return _('Will generate all but one target')
            return str(items)+_(' targets not generated')
        # Regular selection
        if not items:
            return _('All available targets will be generated')
        if items == 1:
            return _('Will generate just one target')
        return str(items)+_(' targets selected')

    def update_targets_hint(self):
        self.target_hint.SetLabel(self.get_targets_hint())

    def get_sort_hint(self):
        sort_mode = self.invert_targets_input.GetSelection()
        if sort_mode == ORDER_INVERT or sort_mode == ORDER_PRIORITY:
            return _('Generation by priority')
        if sort_mode == ORDER_SELECTED:
            return _('Generation in the above order')
        return _('Generation in the "Outputs" order')

    def update_sort_hint(self):
        self.sort_hint.SetLabel(self.get_sort_hint())

    def get_pre_hint(self):
        items = self.skippre_lbox.GetCount()
        if not items:
            return _('All preflights will be applied')
        if self.skippre_lbox.FindString('all') == wx.NOT_FOUND:
            if items == 1:
                return _('All but one preflight will be applied')
            return str(items)+_(' preflights skipped')
        return _('No preflight will be applied')

    def update_pre_hint(self):
        self.pre_hint.SetLabel(self.get_pre_hint())

    def OnChangeSortMode(self, event):
        self.update_targets_hint()
        self.update_sort_hint()

    def add_path(self, sizer, label, value, id, ttip, on_change=None, is_dir=False, rename=None):
        window = self.path_w
        li_sizer = wx.BoxSizer(wx.HORIZONTAL)
        new_label = wx.StaticText(window, label=label, size=wx.Size(max_label, -1), style=wx.ALIGN_RIGHT)
        new_label.SetToolTip(ttip)
        if False:
            new_input = wx.TextCtrl(window, size=wx.Size(def_text, -1))
            new_input.Value = value
        else:
            if is_dir:
                new_input = wx.DirPickerCtrl(window, message=label, size=wx.Size(def_text, -1), style=wx.DIRP_DIR_MUST_EXIST,
                                             id=create_id(id))
                if on_change:
                    # This works as expected only if FLP_USE_TEXTCTRL is disabled
                    # Otherwise we get partial changes
                    new_input.Bind(wx.EVT_DIRPICKER_CHANGED, on_change)
            else:
                # Validator are useless here
                new_input = wx.FilePickerCtrl(window, message=label, size=wx.Size(def_text, -1), id=create_id(id),
                                              style=wx.FLP_OPEN | wx.FLP_FILE_MUST_EXIST)
                if on_change:
                    # This works as expected only if FLP_USE_TEXTCTRL is disabled
                    # Otherwise we get partial changes
                    new_input.Bind(wx.EVT_FILEPICKER_CHANGED, on_change)
            new_input.SetPath(value)
            new_input.SetToolTip(ttip)
        li_sizer.Add(new_label, gh.SIZER_FLAGS_0_NO_EXPAND)
        li_sizer.Add(new_input, gh.SIZER_FLAGS_1_NO_EXPAND)
        if rename is not None:
            but_rename = wx.Button(window, label=_("Rename"))
            but_rename.SetToolTip(_("Changes the name of the configuration file"))
            set_button_bitmap(but_rename, "gtk-edit")
            li_sizer.Add(but_rename, gh.SIZER_FLAGS_0)
            but_rename.Bind(wx.EVT_BUTTON, rename)
        else:
            but_rename = None
        sizer.Add(li_sizer, gh.SIZER_FLAGS_1_NO_BORDER)
        return li_sizer, new_input, but_rename

    def apply_setup(self, s):
        # Check we got usable file names
        if not (self.check_changed_filename(s.pcb, _('PCB')) and self.check_changed_filename(s.schematic, _('schematic')) and
                self.check_changed_filename(s.config, _('config')) and self.check_changed_dirname(s.cwd, _('working dir')) and
                self.check_changed_outdir(s.dest)):
            return False
        # All seems to be ok, apply it
        self.cf_input.SetPath(s.config)
        if not self.apply_changed_config(s.config):
            wx.CallAfter(self.revert_cfg, reload=True)
            return False
        self.pcb_input.SetPath(s.pcb)
        if not self.apply_changed_pcb(s.pcb):
            wx.CallAfter(self.revert_cfg, reload=True)
            wx.CallAfter(self.revert_pcb, reload=True)
            return False
        self.sch_input.SetPath(s.schematic)
        if not self.apply_changed_sch(s.schematic):
            wx.CallAfter(self.revert_cfg, reload=True)
            wx.CallAfter(self.revert_pcb, reload=True)
            wx.CallAfter(self.revert_sch, reload=True)
            return False
        # Allow a fail here without reverting all the others
        self.wd_input.SetPath(s.cwd)
        try:
            os.chdir(s.cwd)
            self.old_cwd = s.cwd
        except OSError as e:
            pop_error(_('Invalid working dir:\n')+str(e))
            self.wd_input.SetPath(self.old_cwd)
        self.de_input.SetPath(s.dest)
        GS.out_dir = s.dest
        return True


# ##########################################################################
# # Class OutputsPanel
# # Panel containing the outputs ABM
# ##########################################################################

class OutputsPanel(DictPanel):
    def __init__(self, parent, help):
        self.dict_type = "output"
        super().__init__(parent, help)

    def refresh_lbox(self):
        set_items(self.lbox, RegOutput.get_outputs())   # Populate the listbox

    def pre_edit(self, obj):
        self.grps_before = set(obj.groups)

    def add_obj(self, obj):
        logger.debug(f'Adding output {obj}')
        RegOutput.add_output(obj)

    def remove_obj(self, obj):
        RegOutput.remove_output(obj)

    def OnItemDClick(self, event):
        if super().OnItemDClick(event):
            obj = self.editing
            # Adjust the groups involved
            grps_after = set(obj.groups)
            changed = False
            # - Added
            for g in grps_after-self.grps_before:
                RegOutput.add_out_to_group(obj, g)
                changed = True
            # - Removed
            for g in self.grps_before-grps_after:
                RegOutput.remove_out_from_group(obj, g)
                changed = True
            if changed:
                self.Parent.Parent.refresh_groups()

    def choose_type(self):
        return choose_from_list(self, list(RegOutput.get_registered().keys()), _('output type'))

    def new_obj(self, kind):
        # Create a new object of the selected type
        obj = RegOutput.get_class_for(kind)()
        # Create a unique name for it
        n = 1
        while n:
            name = _('new')+f'_{kind}_{n}'
            if RegOutput.get_output(name) is None:
                break
            n += 1
        # Create an object for this kind
        obj.type = kind
        desc = get_doc_lines(obj)[1].strip()
        if desc[-1] == '.':
            desc = desc[:-1]
        obj._tree = {'name': name, 'comment': desc}
        # This will load the needed schematic and/or PCB
        config_output(obj)
        return obj

    def OnAdd(self, event):
        if not GS.sch_file:
            pop_error(_('Please first select a schematic'))
            return
        if not GS.pcb_file:
            pop_error(_('Please first select a PCB'))
            return
        super().OnAdd(event)


# ##########################################################################
# # class GroupsPanel
# # Panel containing the groups ABM
# ##########################################################################

class GroupsPanel(wx.Panel):
    def __init__(self, parent, help):
        wx.Panel.__init__(self, parent, name='groups')
        self.help_domain = help

        # All the widgets
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        #  List box + buttons
        abm_sizer = wx.BoxSizer(wx.HORIZONTAL)
        #   List box
        list_sizer = wx.BoxSizer(wx.VERTICAL)
        self.lbox = wx.ListBox(self, choices=[], style=wx.LB_SINGLE)
        self.refresh_groups()
        list_sizer.Add(self.lbox, gh.SIZER_FLAGS_1)
        abm_sizer.Add(list_sizer, gh.SIZER_FLAGS_1_NO_BORDER)
        #   Buttons at the right
        abm_sizer.Add(add_abm_buttons(self, id='groups'), gh.SIZER_FLAGS_0_NO_EXPAND)
        main_sizer.Add(abm_sizer, gh.SIZER_FLAGS_1_NO_BORDER)

        self.SetSizer(main_sizer)
        self.Layout()

        # Connect Events
        self.lbox.Bind(wx.EVT_LISTBOX_DCLICK, self.OnItemDClick)   # Mouse double click, on GTK also RETURN key
        self.but_up.Bind(wx.EVT_BUTTON, self.OnUp)
        self.but_down.Bind(wx.EVT_BUTTON, self.OnDown)
        self.but_add.Bind(wx.EVT_BUTTON, self.OnAdd)
        self.but_remove.Bind(wx.EVT_BUTTON, self.OnRemove)

    def refresh_groups(self):
        groups = list(RegOutput.get_groups_struct().values())
        for g in groups:
            g.update_out()
        set_items(self.lbox, groups)

    def mark_edited(self):
        self.Parent.Parent.mark_edited()

    def edit_group(self, group, is_new=False):
        group_names = [g.name for g in get_client_data(self.lbox)]
        used_names = set(group_names+[o.name for o in RegOutput.get_outputs()])
        position = self.lbox.Selection
        if not is_new:
            del group_names[position]
            # Avoid messing with the actual group
            group = deepcopy(group)
        dlg = EditGroupDialog(self, group, used_names, group_names, is_new)
        res = dlg.ShowModal()
        if res == wx.ID_OK:
            new_name = dlg.name_text.Value
            lst_objs = get_client_data(dlg.lbox)
            if is_new:
                new_grp = RegOutput.add_group(new_name, lst_objs)
                self.lbox.Append(str(new_grp), new_grp)
            else:
                new_grp = RegOutput.replace_group(group.name, new_name, lst_objs)
                self.lbox.SetString(position, str(new_grp))
                self.lbox.SetClientData(position, new_grp)
            new_grp.update_out()
            self.mark_edited()
        dlg.Destroy()

    def OnItemDClick(self, event):
        self.edit_group(self.lbox.GetClientData(self.lbox.Selection))

    def OnUp(self, event):
        if move_sel_up(self.lbox):
            self.mark_edited()

    def OnDown(self, event):
        if move_sel_down(self.lbox):
            self.mark_edited()

    def OnAdd(self, event):
        self.edit_group(Group(_('new_group'), []), is_new=True)

    def OnRemove(self, event):
        if remove_item(self.lbox, confirm=_('Are you sure you want to remove the `{}` group?')):
            self.mark_edited()


# ##########################################################################
# # class EditGroupDialog
# # Dialog to edit one group
# ##########################################################################

class EditGroupDialog(InjectDialog):
    """ Edit a group, can be a new one """
    def __init__(self, parent, group, used_names, group_names, is_new):
        self.initialized = False
        base_id = 'edit_group'
        InjectDialog.__init__(self, parent, title=_("Add/Edit group"), name=base_id,
                              style=wx.DEFAULT_DIALOG_STYLE | wx.STAY_ON_TOP | wx.BORDER_DEFAULT)

        # All the widgets
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        #  Group name
        ttip = _("Name for the group. Must be unique and different from any output.")
        _d, self.name_text, grp_name_sizer = input_label_and_text(self, _("Group name"), group.name, ttip, -1,
                                                                  style=wx.TE_PROCESS_ENTER, id=base_id+'.name')
        main_sizer.Add(grp_name_sizer, gh.SIZER_FLAGS_0_NO_BORDER)
        #  Static Box with the ABM
        sb_sizer = wx.StaticBoxSizer(wx.VERTICAL, self, _("Outputs and groups"))
        sb = sb_sizer.GetStaticBox()
        #   List box + buttons
        abm_sizer = wx.BoxSizer(wx.HORIZONTAL)
        #    List box
        list_sizer = wx.BoxSizer(wx.VERTICAL)
        self.lbox = wx.ListBox(sb, choices=[], style=wx.LB_SINGLE, id=create_id('edit_group.lbox'))
        self.lbox.SetToolTip(_("Outputs and groups that belongs to this group"))
        set_items(self.lbox, group.items)   # Populate the listbox
        list_sizer.Add(self.lbox, gh.SIZER_FLAGS_1)
        abm_sizer.Add(list_sizer, gh.SIZER_FLAGS_1_NO_BORDER)
        #    Buttons at the right
        abm_buts = add_abm_buttons(self, sb, add_add=True, add_add_ttip=_("Add a group to this group"),
                                   add_ttip=_("Add one or more outputs to the group"), id=base_id)
        self.abm_buts = abm_buts
        abm_sizer.Add(abm_buts, gh.SIZER_FLAGS_0_NO_EXPAND)
        sb_sizer.Add(abm_sizer, gh.SIZER_FLAGS_1_NO_BORDER)
        main_sizer.Add(sb_sizer, gh.SIZER_FLAGS_1)
        #  Status
        status_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.status_text = wx.StaticText(self, label=_("OK"), style=wx.ST_NO_AUTORESIZE)
        status_sizer.Add(self.status_text, gh.SIZER_FLAGS_1)
        main_sizer.Add(status_sizer, gh.SIZER_FLAGS_0_NO_BORDER)
        #  OK/Cancel
        main_sizer.Add(ok_cancel(self, domain=base_id), gh.SIZER_FLAGS_0)

        self.SetSizer(main_sizer)  # Size hints comes from the main_sizer
        main_sizer.Fit(self)       # Ask the main_sizer to make the dialog big enough
        self.Layout()
        self.Centre(wx.BOTH)

        # Connect Events
        self.Bind(wx.EVT_CHAR_HOOK, self.OnKey)
        self.name_text.Bind(wx.EVT_TEXT, self.ValidateName)
        self.lbox.Bind(wx.EVT_KEY_UP, self.OnKey)
        self.but_up.Bind(wx.EVT_BUTTON, self.OnUp)
        self.but_down.Bind(wx.EVT_BUTTON, self.OnDown)
        self.but_add.Bind(wx.EVT_BUTTON, self.OnAdd)
        self.but_add_add.Bind(wx.EVT_BUTTON, self.OnAddG)
        self.but_remove.Bind(wx.EVT_BUTTON, self.OnRemove)

        self.initialized = True

        self.used_names = used_names
        self.group_names = group_names
        self.valid_list = bool(len(group.items))
        self.is_new = is_new
        self.original_name = group.name
        self.input_is_normal = True
        self.normal_bkg = self.name_text.GetBackgroundColour()
        self.red = wx.Colour(0xFF, 0x40, 0x40)
        self.green = wx.Colour(0x40, 0xFF, 0x40)

        self.status_text.SetForegroundColour(wx.Colour(0, 0, 0))
        self.valid_name = True
        self.ok = True
        self.status_txt = ''
        self.eval_status()

    def update_status(self):
        if self.ok:
            self.status_text.SetLabel(OK_CHAR+' '+self.status_txt)
            self.status_text.SetBackgroundColour(self.green)
            self.but_ok.Enable()
        else:
            self.status_text.SetLabel(NOT_OK_CHAR+' '+self.status_txt)
            self.status_text.SetBackgroundColour(self.red)
            self.but_ok.Disable()

    def set_status(self, ok, msg=None):
        if msg is None:
            msg = 'Ok'
        if ok == self.ok and msg == self.status_txt:
            return
        self.ok = ok
        self.status_txt = msg
        self.update_status()

    def eval_status(self):
        if not self.valid_name:
            self.set_status(False, _('name ')+self.name_why)
        elif not self.valid_list:
            self.set_status(False, _('no outputs selected'))
        else:
            self.set_status(True)

    def is_valid_name(self, name):
        if not name:
            return False, _("is empty")
        if name[0] == '_':
            return False, _("starts with underscore")
        if self.is_new:
            if name in self.used_names:
                return False, _("already used")
            return True, None
        # Not new
        if name == self.original_name:
            # Same name
            return True, None
        if name in self.used_names:
            return False, _("already used")
        return True, None

    def ValidateName(self, event):
        """ Called by the TextCtrl On Text """
        if not self.initialized:
            return
        cur_name = self.name_text.Value
        self.valid_name, self.name_why = self.is_valid_name(cur_name)
        self.eval_status()

    def OnKey(self, event):
        """ Called by the dialog OnCharHook and from the listbox OnKeyUp """
        if event.GetKeyCode() == wx.WXK_RETURN and self.valid_name and self.valid_list:
            self.EndModal(wx.ID_OK)
        else:
            # Not our key, continue processing it
            event.Skip()

    def OnUp(self, event):
        move_sel_up(self.lbox)

    def OnDown(self, event):
        move_sel_down(self.lbox)

    def OnAdd(self, event):
        selected = {i.out for i in get_client_data(self.lbox)}
        available = {str(o): o for o in RegOutput.get_outputs() if o not in selected}
        available_names = [o.name for o in RegOutput.get_outputs() if o not in selected]
        if not available:
            pop_error(_('No outputs available to add'))
            return
        outs = choose_from_list(self, list(available.keys()), what=_("output"), multiple=True, search_on=available_names)
        if not outs:
            return
        for out in outs:
            o = available[out]
            i = GroupEntry(o.name, out=o)
            self.lbox.Append(str(i), i)
        self.valid_list = True
        self.eval_status()
        # Adjust the size to fit the new items
        size = self.GetClientSize()
        lb_size = self.lbox.BestSize+self.abm_buts.GetSize()
        if lb_size.Width > size.Width:
            size.Width = lb_size.Width
            self.SetClientSize(size)

    def OnAddG(self, event):
        if not self.group_names:
            pop_error(_('No groups available to add'))
            return
        groups = choose_from_list(self, self.group_names, what=_('group'), multiple=True)
        if not groups:
            return
        for g in groups:
            i = GroupEntry(g)
            self.lbox.Append(str(i), i)
        self.valid_list = True
        self.eval_status()

    def OnRemove(self, event):
        index, string, obj = get_selection(self.lbox)
        if obj is None:
            # Nested group, can be only from the top-level definition
            return
        # Not defined in "groups" section
        if not obj.is_from_top():
            pop_info(_('This entry is from the `groups` option.\nRemove it from the output'))
            return
        # Also defined in an output
        if obj.is_from_output():
            # Also defined in an output
            obj.from_top = False
            pop_info(_('This entry was also defined in the `groups` option.\nNow removed from the `groups` section.'))
            self.lbox.SetString(index, str(obj))
            return
        remove_item(self.lbox)
        self.valid_list = bool(self.lbox.GetCount())
        self.eval_status()


# ##########################################################################
# # class FiltersPanel
# # Panel containing the filters ABM
# ##########################################################################

class FiltersPanel(DictPanel):
    def __init__(self, parent, help):
        self.dict_type = "filter"
        super().__init__(parent, help)

    def refresh_lbox(self):
        set_items(self.lbox, [f for f in RegOutput.get_filters().values() if not f.name.startswith('_')])

    def choose_type(self):
        return choose_from_list(self, list(RegFilter.get_registered().keys()), _('filter type'))

    def add_obj(self, obj):
        RegOutput.add_filter(obj)

    def remove_obj(self, obj):
        RegOutput.remove_filter(obj)

    def new_obj(self, kind):
        # Create a new object of the selected type
        cls = RegFilter.get_class_for(kind)
        desc = get_doc_lines(cls)[0].strip()
        if desc[-1] == '.':
            desc = desc[:-1]
        obj = create_new_optionable(cls, None, extra={'name': 'new_filter', 'type': kind, 'comment': desc})
        return obj


# ##########################################################################
# # class VariantsPanel
# # Panel containing the filters ABM
# ##########################################################################

class VariantsPanel(DictPanel):
    def __init__(self, parent, help):
        self.dict_type = "variant"
        super().__init__(parent, help)

    def refresh_lbox(self):
        set_items(self.lbox, list(RegOutput.get_variants().values()))

    def choose_type(self):
        return choose_from_list(self, list(RegVariant.get_registered().keys()), _('variant type'))

    def add_obj(self, obj):
        RegOutput.add_variant(obj)

    def remove_obj(self, obj):
        RegOutput.remove_variant(obj)

    def new_obj(self, kind):
        # Create a new object of the selected type
        obj = RegVariant.get_class_for(kind)()
        obj.type = kind
        obj._tree = {'name': _('new_variant')}
        obj.config(None)
        return obj


# ##########################################################################
# # class PreflightsPanel
# # Panel containing the filters ABM
# ##########################################################################

class PreflightsPanel(DictPanel):
    def __init__(self, parent, help):
        self.dict_type = "preflight"
        super().__init__(parent, help)
        self.can_remove_first_level = False

    def refresh_lbox(self):
        BasePreFlight.configure_all()
        items = list(BasePreFlight.get_in_use_objs())
        set_items(self.lbox, items)

    def choose_type(self):
        used = set(BasePreFlight.get_in_use_names())
        available = sorted([name for name in BasePreFlight.get_registered().keys() if name not in used])
        return choose_from_list(self, available, _('preflight'))

    def add_obj(self, obj):
        BasePreFlight.add_preflight(obj)

    def remove_obj(self, obj):
        BasePreFlight.remove_preflight(obj)

    def new_obj(self, kind):
        # Create a new object of the selected type
        obj = BasePreFlight.get_object_for(kind)
        obj.config(None)
        return obj

    def OnAdd(self, event):
        if not GS.sch_file:
            pop_error(_('Please first select a schematic'))
            return
        if not GS.pcb_file:
            pop_error(_('Please first select a PCB'))
            return
        super().OnAdd(event)


# ##########################################################################
# # class RunControlDialog
# # A dialog to monitor the targets generation
# ##########################################################################

class RunControlDialog(InjectDialog):
    def __init__(self, parent, targets, invert_sel, skip_pre, cli_order, no_priority):
        InjectDialog.__init__(self, parent, title=_('Generating targets'),
                              style=wx.DEFAULT_DIALOG_STYLE | wx.STAY_ON_TOP | wx.BORDER_DEFAULT)

        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Text from the logs
        self.txt = wx.TextCtrl(self, size=wx.Size(920, 480), style=wx.TE_MULTILINE | wx.TE_READONLY)
        main_sizer.Add(self.txt, gh.SIZER_FLAGS_1)

        # Buttons
        but_sizer = wx.BoxSizer(wx.HORIZONTAL)
        # Stop
        self.but_stop = wx.Button(self, label=_("Stop"))
        set_button_bitmap(self.but_stop, wx.ART_QUIT)
        but_sizer.Add(self.but_stop, gh.SIZER_FLAGS_0_NO_EXPAND)
        # Close
        self.but_close = wx.Button(self, label=_("Close"))
        self.but_close.Disable()
        set_button_bitmap(self.but_close, wx.ART_CLOSE)
        but_sizer.Add(self.but_close, gh.SIZER_FLAGS_0_NO_EXPAND)
        main_sizer.Add(but_sizer, gh.SIZER_FLAGS_0_NO_BORDER)

        self.SetSizer(main_sizer)
        main_sizer.Fit(self)
        self.Centre(wx.BOTH)

        self.Bind(EVT_WX_LOG_EVENT, self.OnLogEvent)
        self.Bind(EVT_WX_FINISH_EVENT, self.OnFinish)
        self.Bind(wx.EVT_CLOSE, self.OnExit)
        self.but_close.Bind(wx.EVT_BUTTON, self.OnExit)
        self.but_stop.Bind(wx.EVT_BUTTON, self.OnStop)

        start_gui_log(self)
        self.thread = threading.Thread(target=self.generate_outputs,
                                       args=(targets, invert_sel, skip_pre, cli_order, no_priority))
        GS.reset_stop_flag()
        self.thread.start()
        self.running = True

    def generate_outputs(self, targets, invert_sel, skip_pre, cli_order, no_priority):
        try:
            generate_outputs(targets, invert_sel, skip_pre, cli_order, no_priority)
        except SystemExit:
            pass
        # Notify we finished, not sure if an event is an overkill, but is safe
        wx.PostEvent(self, wxFinishEvent())

    def OnStop(self, event):
        if not self.running:
            # Nothing to stop
            return
        # Just a flag asking to stop
        GS.set_stop_flag()
        # Give feadback to the user
        self.txt.SetDefaultStyle(wx.TextAttr(wx.Colour('orange')))
        self.txt.AppendText(_("Waiting to finish this target to stop ...\n"))
        # Avoid more stop requests
        self.but_stop.Disable()

    def OnFinish(self, event):
        # Called when we finished generating the targets
        self.but_close.Enable()
        self.but_stop.Disable()
        self.running = False
        self.txt.SetDefaultStyle(wx.TextAttr(wx.Colour('orange')))
        self.txt.AppendText(_("Finished\n"))

    def OnExit(self, event):
        """ Stop catching log messages """
        if self.running:
            # Avoid exiting while we still working
            pop_error(_("Still generating targets, please wait"))
            return
        stop_gui_log()
        self.EndModal(wx.ID_OK)

    def OnLogEvent(self, event):
        msg = event.message.strip("\r")+"\n"
        old = None
        if msg[0] == '\033':
            color = COLORS[msg[1]]
            msg = msg[2:]
            old = self.txt.GetDefaultStyle()
            self.txt.SetDefaultStyle(wx.TextAttr(color))
        self.txt.AppendText(msg)
        if old is not None:
            self.txt.SetDefaultStyle(old)
        # print(msg)
        event.Skip()


# ##########################################################################
# # class ShowWarnsDialog
# # A dialog to monitor the targets generation
# ##########################################################################

class ShowWarnsDialog(InjectDialog):
    def __init__(self, parent, warns):
        InjectDialog.__init__(self, parent, title=_('Collected warnings'),
                              style=wx.DEFAULT_DIALOG_STYLE | wx.STAY_ON_TOP | wx.BORDER_DEFAULT)

        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Text from the logs
        self.txt = wx.TextCtrl(self, size=wx.Size(920, 480), style=wx.TE_MULTILINE | wx.TE_READONLY)
        main_sizer.Add(self.txt, gh.SIZER_FLAGS_1)
        self.txt.SetDefaultStyle(wx.TextAttr(wx.YELLOW))
        for w in warns:
            self.txt.AppendText(w+'\n')

        # Buttons
        main_sizer.Add(ok_cancel(self, no_cancel=True), gh.SIZER_FLAGS_0)

        self.SetSizer(main_sizer)
        main_sizer.Fit(self)
        self.Centre(wx.BOTH)


# ##########################################################################
# # class SplashScreen
# # A dialog to inform the user we are already running
# # Note: the wxPython examples from the Wiki are useless
# ##########################################################################

class SplashScreen(InjectDialog):
    def __init__(self, target, args):
        InjectDialog.__init__(self, None, style=wx.DIALOG_NO_PARENT | wx.STAY_ON_TOP | wx.BORDER_NONE, name='splash')

        main_sizer = wx.BoxSizer(wx.VERTICAL)

        bitmap = wx.Bitmap(name=os.path.join(GS.get_resource_path('images'), 'splash.png'), type=wx.BITMAP_TYPE_PNG)
        main_sizer.Add(wx.StaticBitmap(self, bitmap=bitmap), gh.SIZER_FLAGS_1_NO_BORDER)
        self.text = wx.StaticText(self)
        main_sizer.Add(self.text, gh.SIZER_FLAGS_0)

        self.SetSizer(main_sizer)
        main_sizer.Fit(self)
        self.Centre(wx.BOTH)

        self.Bind(EVT_WX_FINISH_EVENT, self.OnFinish)
        self.Bind(EVT_WX_PROGRESS_EVENT, self.OnProgress)

        self.target = target
        self.args = args
        self.stop = False
        self.thread = threading.Thread(target=self.run_target)
        self.thread.start()

    def run_target(self):
        log.start_recording_error_msgs()
        try:
            self.target(self.args, self.progress)
        except Exception:
            self.stop = True
        self.msgs = log.stop_recording_error_msgs()
        wx.PostEvent(self, wxFinishEvent())

    def progress(self, msg):
        evt = wxProgressEvent()
        evt.msg = msg
        wx.PostEvent(self, evt)

    def OnProgress(self, event):
        self.text.SetLabel(event.msg)

    def OnFinish(self, event):
        # Inform any error issued by logger.error
        if self.msgs:
            logger.error(self.msgs)
            pop_error(self.msgs)
        elif self.stop:
            pop_error(_('Fatal error, exiting'))
        # Close the dialog
        self.EndModal(wx.ID_OK)
        if self.stop:
            exit(1)


def show_splash(target, args):
    InjectDialog.initialize(args.gui_inject)
    dlg = SplashScreen(target, args)
    dlg.ShowModal()
    dlg.Destroy()


# ##########################################################################
# # Class AboutPanel
# # Panel containing the main options (paths, targets, etc.)
# ##########################################################################

class AboutPanel(wx.Panel):
    def __init__(self, parent, help):
        wx.Panel.__init__(self, parent)
        self.help_domain = help

        # All the widgets
        self.sizer = main_sizer = wx.BoxSizer(wx.VERTICAL)

        bitmap = wx.Bitmap(name=os.path.join(GS.get_resource_path('images'), 'about.png'), type=wx.BITMAP_TYPE_PNG)
        main_sizer.Add(wx.StaticBitmap(self, bitmap=bitmap), gh.SIZER_FLAGS_1_NO_BORDER)
        self.add_line(__copyright__)
        self.add_line(_('Version: ')+__version__)
        self.add_line('Python: '+sys.version)
        self.add_line(_('Platform: ')+platform.platform().replace('-', ' '))
        self.add_line('KiCad: '+GS.kicad_version)
        self.add_line('URL: '+__url__)
        self.add_line('e-mail: '+__email__)

        self.SetSizer(main_sizer)
        self.Layout()

    def add_line(self, msg):
        txt = wx.StaticText(self, label=msg, style=wx.ALIGN_CENTRE_HORIZONTAL)
        self.sizer.Add(txt, gh.SIZER_FLAGS_0)
