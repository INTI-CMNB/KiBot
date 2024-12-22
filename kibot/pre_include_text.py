# -*- coding: utf-8 -*-
# Copyright (c) 2024 Nguyen Vincent
# Copyright (c) 2024 Salvador E. Tropea
# Copyright (c) 2024 Instituto Nacional de Tecnología Industrial
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)
# Contributed by Nguyen Vincent (@nguyen-v)
import os
import re
import pcbnew
from .error import KiPlotConfigurationError
from .gs import GS
from .kiplot import load_board, get_output_targets, look_for_output
from .misc import W_NOMATCHGRP
from .optionable import Optionable
from .registrable import RegOutput
from .macros import macros, document, pre_class  # noqa: F401
from . import log

logger = log.get_logger()

VALID_OUTPUT_TYPES = {'report'}

class IncTextOutputOptions(Optionable):
    """Options for Include Text output"""
    def __init__(self, name=None):
        super().__init__()
        with document:
            self.name = ''
            """*Name of output*"""
        if name is not None:
            self.name = name

    def __str__(self):
        return self.name


class IncludeTextOptions(Optionable):
    """Options for the Include Text preflight"""
    def __init__(self):
        with document:
            self.outputs = IncTextOutputOptions
            """*[list(dict)|list(string)|string=?] List of text-generating outputs."""
            self.enabled = True
            """Enable the check. This is the replacement for the boolean value"""
            self.group_name = 'kibot_text'
            """Name prefix for the group containing the text. The name of the group
                should be <group_name>_X where X is the output name.
                When the output generates more than one TXT use *kibot_table_out[2]*
                to select the second TXT. """
        super().__init__()

    def config(self, parent):
        super().config(parent)
        if isinstance(self.outputs, type):
            self.outputs = [o.name for o in filter(lambda x: x.type in VALID_OUTPUT_TYPES, RegOutput.get_outputs())]
            logger.debug('- Collected outputs: ' + str(self.outputs))
        self._outputs = [IncTextOutputOptions(o) if isinstance(o, str) else o for o in self.outputs]


def update_text_group(g, ops, out, txt_file):
    """Update text in the specified group with the content of the txt_file"""
    if not os.path.isfile(txt_file):
        raise KiPlotConfigurationError(f'Missing `{txt_file}`, create it first.')

    with open(txt_file, 'r', encoding='utf-8') as file:
        content = file.read()

    for item in g.GetItems():
        if isinstance(item, (pcbnew.PCB_TEXT, pcbnew.PCB_TEXTBOX)):
            item.SetText(content)
            logger.debug(f'Updated text in group `{g.GetName()}` with content from `{txt_file}`')


def update_text(ops, parent):
    logger.debug('Starting include text preflight')
    load_board()
    txt_files = []
    txt_name = []
    out_to_txt_mapping = {}

    logger.debug('- Analyzing requested outputs')
    for out in ops._outputs:
        if not out.name:
            raise KiPlotConfigurationError('Output entry without a name')
        txt = look_for_output(out.name, '`include text`', parent, VALID_OUTPUT_TYPES) if out.name else None
        if not txt:
            logger.debug(f'  - {out.name} no TXT file')
            continue
        out._obj = txt
        targets, _, _ = get_output_targets(out.name, parent)

        txt_targets = [file for file in targets if file.endswith('.txt')]
        for file in txt_targets:
            txt_files.append(file)
        for file in txt_targets:
            file_name = os.path.basename(file)
            name_without_ext = os.path.splitext(file_name)[0]
            txt_name.append(name_without_ext)
        out_to_txt_mapping[out.name] = (out, txt_targets)
        logger.debug(f'  - {out.name} -> {txt_targets}')

    group_found = False
    updated = False
    group_prefix = ops.group_name + "_"
    group_prefix_l = len(group_prefix)

    logger.debug('- Scanning board groups')
    for g in GS.board.Groups():
        group_name = g.GetName()
        if not group_name.startswith(group_prefix):
            continue

        group_found = True
        logger.debug(f'  - {group_name}')
        group_suffix = group_name[group_prefix_l:]
        index = 0
        if group_suffix[-1] == ']':
            index = int(group_suffix[-2])-1
            group_suffix = group_suffix[:-3]
            logger.debug(f'    - {group_suffix} index: {index}')
        out, txt = out_to_txt_mapping.get(group_suffix, (None, None))
        if not txt:
            logger.warning(W_NOMATCHGRP+f'No output to handle `{group_name}` found')
            continue
        if index < 0 or index >= len(txt):
            msg = f'index {index+1} is out of range, '+('only one TXT available' if len(txt) == 1 else
                                                        f'must be in the [1,{len(txt)}] range')
            raise KiPlotConfigurationError(msg)
        x1, y1, x2, y2 = GS.compute_group_boundary(g)
        item = g.GetItems()[0]
        layer = item.GetLayer()
        logger.debug(f'    - Found group @{GS.to_mm(x1)},{GS.to_mm(y1)} mm'
                     f' ({GS.to_mm(x2-x1)}x{GS.to_mm(y2-y1)} mm) layer {layer}'
                     f' with name {g.GetName()}')

        update_text_group(g, ops, out, txt[index])
        updated = True

    if not group_found:
        logger.warning(W_NOMATCHGRP + f'No `{ops.group_name}*` groups found, skipping `include_text` preflight')

    return updated


@pre_class
class Include_Text(BasePreFlight):  # noqa: F821
    """Include Text
       Updates PCB text objects with content from TXT files generated by an output.
       Needs KiCad 7 or newer.
       To specify the position and size of the text, create a group called *kibot_text_X*, where
       X should match the name of the output. The group should contain PCB_TEXT or PCB_TEXTBOX
       objects. After running this preflight, the text objects will be updated with the content
       of the TXT file corresponding to the output name."""

    def __init__(self):
        super().__init__()
        self._pcb_related = True
        with document:
            self.include_text = IncludeTextOptions
            """[boolean|dict=false] Use a boolean for simple cases or fine-tune its behavior"""

    def __str__(self):
        v = self.include_text
        if isinstance(v, bool):
            return super().__str__()
        return f'{self.type}: {v.enabled} ({[out.name for out in v._outputs]})'

    def config(self, parent):
        super().config(parent)
        if isinstance(self.include_text, bool):
            self._value = IncludeTextOptions()
            self._value.config(self)
        else:
            self._value = self.include_text

    def apply(self):
        if not GS.ki7:
            raise KiPlotConfigurationError('The `include_text` preflight needs KiCad 7 or newer')
        if update_text(self._value, self):
            GS.save_pcb()