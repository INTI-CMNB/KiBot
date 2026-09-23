# -*- coding: utf-8 -*-
# Copyright (c) 2024 Salvador E. Tropea
# Copyright (c) 2024 Instituto Nacional de Tecnologïa Industrial
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)
#
# Code to do regression tests by injecting actions to the GUI code

import csv
import signal
import wx
from ..gs import GS
from .. import log

logger = log.get_logger()
TIME_OUT = 10
IDLE_ID = wx.EVT_IDLE.typeId
ids = {}
# eventDict = {}
# for name in dir(wx):
#     if name.startswith('EVT_'):
#         evt = getattr(wx, name)
#         if isinstance(evt, wx.PyEventBinder):
#             eventDict[evt.typeId] = name


def convert_to_number(value):
    if value.startswith('wx.'):
        return getattr(wx, value[3:])
    if value == 'True':
        return True
    if value == 'False':
        return False
    if value.startswith('str:'):
        return value[4:]
    try:
        # Convert to integer if possible
        return int(value)
    except ValueError:
        try:
            # Convert to float if possible
            return float(value)
        except ValueError:
            # Return original value if it cannot be converted
            return value


class InjectDialog(wx.Dialog):
    cur_dialog = None
    next_dialog = None
    dialog_stack = []
    lock = False
    enabled = False
    events = []

    def ProcessEvent(self, event):
        if InjectDialog.enabled:
            tp = event.GetEventType()
            # if tp != wx.EVT_UPDATE_UI_RANGE.typeId:
            #    print(f"Processing event: {eventDict[tp]}")
            if tp == IDLE_ID and not InjectDialog.lock:
                self.get_event()
                return True
        return super().ProcessEvent(event)

    @staticmethod
    def initialize(file_name):
        if not file_name:
            InjectDialog.enabled = False
            return
        with open(file_name, newline='') as csvfile:
            reader = csv.reader(csvfile)
            InjectDialog.events = [[convert_to_number(cell) for cell in row] for row in reader]
        InjectDialog.enabled = True

    def exit(self, msg):
        if hasattr(self, 'thread'):
            logger.debug('* Waiting for the other thread to finish ...')
            self.thread.join()
        GS.exit_with_error(msg, 1)

    def ShowModal(self):
        InjectDialog.dialog_stack.append(self.GetName())
        logger.debug(f'* Dialog added {InjectDialog.dialog_stack}')
        return super().ShowModal()

    def Destroy(self):
        # We must wait until Destroy is called, events are processed after EndModal
        InjectDialog.dialog_stack.pop()
        logger.debug(f'* Dialog removed {InjectDialog.dialog_stack}')
        return super().Destroy()

    def get_id(self, name):
        try:
            return ids[name]
        except KeyError:
            self.exit(f"ID `{name}` isn't defined yet")

    def get_event(self):
        self.new_dialog = self.GetName()
        self.first_call = False
        # Initialization of the current dialog
        if not InjectDialog.cur_dialog:
            InjectDialog.cur_dialog = self.new_dialog
            self.first_call = True
        if not InjectDialog.dialog_stack or self.new_dialog != InjectDialog.dialog_stack[-1]:
            # Skip the checks for IDLE sent to parents
            if InjectDialog.next_dialog:
                return
        else:
            # Are we waiting for a particular dialog?
            if InjectDialog.next_dialog:
                if self.new_dialog == InjectDialog.cur_dialog:
                    # No new dialog, keep waiting
                    return
                if self.new_dialog != InjectDialog.next_dialog:
                    self.exit(f'Unexpected dialog: `{self.new_dialog}` (not `{InjectDialog.next_dialog}`)')
                # Found the correct dialog
                InjectDialog.next_dialog = None
                InjectDialog.cur_dialog = self.new_dialog
                logger.debug(f'* Found `{self.new_dialog}` dialog')
                if not InjectDialog.events:
                    InjectDialog.enabled = False
            else:
                # Not waiting, check we didn't get a change
                if self.new_dialog != InjectDialog.cur_dialog:
                    self.exit(f'Unexpected dialog: `{self.new_dialog}`')
        if self.retire_event() and self.next_event_is_wait():
            # We retired an action, we can retire a wait
            self.retire_event()

    def next_event_is_wait(self):
        return len(InjectDialog.events) and InjectDialog.events[0][1] == '_WaitDialog'

    def retire_event(self):
        signal.alarm(0)
        if not InjectDialog.events:
            return False
        e = InjectDialog.events.pop(0)
        # Create a time-out, in case the flow doesn't call us again
        signal.alarm(TIME_OUT)
        id = e[0]
        command = e[1]
        data = e[2:]
        if command[0] == '_':
            return getattr(self, command[1:])(id, data[0] if len(data) == 1 else data)
        # Call member
        o = wx.FindWindowById(self.get_id(id))
        f = getattr(o, command)
        logger.debug(f'* Injecting {id}.{command}{tuple(data)} [{o}]')
        f(*data)
        return True

    # ########################################## #
    # Implementation for the commands in the CSV #
    # ########################################## #

    def SendEvent(self, id, data):
        ev_n = data
        ev_o = getattr(wx, ev_n)
        id_ori = id
        if isinstance(id, str) and id.startswith('name:'):
            o = wx.FindWindowByName(id[5:])
            if o is None:
                self.exit(f'No window named: {id[5:]})')
            id = o.GetId()
        else:
            id = self.get_id(id) if isinstance(id, str) else id
            o = wx.FindWindowById(id)
        event = wx.CommandEvent(ev_o.typeId, id)
        wx.PostEvent(o, event)
        logger.debug(f'* Injecting event {ev_o}({ev_o.typeId}) to {id_ori} [{o}]')
        return True

    def SendText(self, id, data):
        # We must avoid processing events during the simulation
        InjectDialog.lock = True
        sim = wx.UIActionSimulator()
        for v in data:
            sim.Char(ord(v) if isinstance(v, str) else v)
        logger.debug(f'* Injecting text: `{data}`')
        InjectDialog.lock = False
        return True

    def SendKey(self, id, data):
        sim = wx.UIActionSimulator()
        sim.Char(data)
        logger.debug(f'* Injecting key: {data}')
        return True

    def WaitDialog(self, id, data):
        dlg = data
        if self.first_call:
            if self.new_dialog != dlg:
                self.exit(f'Unexpected dialog: {self.new_dialog} (not {dlg})')
            logger.debug(f'* First dialog matched `{dlg}`')
        else:
            InjectDialog.next_dialog = dlg
            logger.debug(f'* Waiting for `{dlg}` dialog')
        return False

    def CheckPath(self, id, data):
        o = wx.FindWindowById(self.get_id(id))
        logger.debug(f'* Checking path from {id} == {data}')
        cur_val = o.GetPath()
        if not cur_val.endswith(data):
            self.exit(f'Wrong path: {cur_val} (expected {data})')

    def ToggleValue(self, id, data):
        o = wx.FindWindowById(self.get_id(id))
        cur_val = o.GetValue()
        o.SetValue(not cur_val)
        logger.debug(f'* Toggle {id} ({cur_val} -> {not cur_val})')


def create_id(name, sub_name=None):
    # We must ask for free IDs, the docs suggest something about negative numbers, but is wrong
    global ids
    if name is None:
        return wx.ID_ANY
    if sub_name is not None:
        name += '.'+sub_name
    try:
        return ids[name]
    except KeyError:
        new_id = wx.Window.NewControlId()
        ids[name] = new_id
        return new_id
