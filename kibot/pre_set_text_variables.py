# -*- coding: utf-8 -*-
# Copyright (c) 2022-2024 Salvador E. Tropea
# Copyright (c) 2022-2024 Instituto Nacional de Tecnología Industrial
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)
"""
Dependencies:
  - from: Git
    role: Find commit hash and/or date
  - from: Bash
    role: Run external commands to create replacement text
"""
import json
import os
import re
from subprocess import run, PIPE
from .error import KiPlotConfigurationError
from .kiplot import load_sch
from .misc import FAILED_EXECUTE, W_EMPTREP, pretty_list
from .optionable import Optionable
from .pre_base import BasePreFlight
from .gs import GS
from .macros import macros, document, pre_class  # noqa: F401
from . import log

logger = log.get_logger()
re_git = re.compile(r'([^a-zA-Z_]|^)(git) ')


class KiCadVariable(Optionable):
    """ KiCad variable definition """
    def __init__(self):
        super().__init__()
        self._unknown_is_error = True
        with document:
            self.name = ''
            """ Name of the variable. The `version` variable will be expanded using `${version}` """
            self.variable = None
            """ {name} """
            self.text = ''
            """ Text to insert instead of the variable """
            self.command = ''
            """ Command to execute to get the text, will be used only if `text` is empty.
                This command will be executed using the Bash shell.
                Be careful about spaces in file names (i.e. use quotes like this "$KIBOT_PCB_NAME").
                The `KIBOT_PCB_NAME` environment variable is the PCB file and the
                `KIBOT_SCH_NAME` environment variable is the schematic file """
            self.before = ''
            """ Text to add before the output of `command` """
            self.after = ''
            """ Text to add after the output of `command` """
            self.expand_kibot_patterns = True
            """ Expand %X patterns in the value to assign to the variable. The context is `schematic` """
            self.expand_in_command = False
            """ Expand %X patterns in the command. The context is `schematic` """
        self._name_example = 'version'

    def __str__(self):
        txt = '${'+self.name+'}'
        if self.text:
            txt += f' -> `{self.text}`'
        else:
            txt += f' -> command(`{self.command}`)'
        return txt

    def config(self, parent):
        super().config(parent)
        if not self.name:
            raise KiPlotConfigurationError("Missing variable name ({})".format(str(self._tree)))


@pre_class
class Set_Text_Variables(BasePreFlight):  # noqa: F821
    """ Set Text Variables
        Defines KiCad 6+ variables.
        They are expanded using `${VARIABLE}`, and stored in the project file.
        This preflight replaces `pcb_replace` and `sch_replace` when using KiCad 6 or newer.
        The KiCad project file is modified.
        You can get text variables containing the names of the schematics sheets enabling the
        `set_text_variables_sheet_title` global option.
        Warning:     don't use `-s all` or this preflight will be skipped """
    def __init__(self):
        super().__init__()
        with document:
            self.set_text_variables = KiCadVariable
            """ [dict|list(dict)=[]] One or more variable definition """
        # Do it before
        self._priority = 90

    def __str__(self):
        if isinstance(self.set_text_variables, list):
            return f'{self.type} ({pretty_list([v.name for v in self.set_text_variables])})'
        return f'{self.type} (not configured)'

    @classmethod
    def get_example(cls):
        """ Returns a YAML value for the example config """
        return ("\n    - name: 'git_hash'"
                "\n      command: 'git log -1 --format=\"%h\" \"$KIBOT_PCB_NAME\"'"
                "\n      before: 'Git hash: <'"
                "\n      after: '>'")

    def apply(self):
        o = self.set_text_variables
        if len(o) == 0:
            return
        if GS.ki5:
            raise KiPlotConfigurationError("The `set_text_variables` preflight is for KiCad 6 or newer")
        pro_name = GS.pro_file
        if not pro_name or not os.path.isfile(pro_name):
            raise KiPlotConfigurationError("Trying to define KiCad 6 variables but the project is missing ({})".
                                           format(pro_name))
        # Get the current definitions
        with open(pro_name, 'rt') as f:
            pro_text = f.read()
        data = json.loads(pro_text)
        text_variables = data.get('text_variables', {})

        # Sheet titles:
        if GS.global_set_text_variables_sheet_title and GS.sch_file:
            load_sch()
            defined = set()
            logger.debugl(2, "Defining sheet title variables")
            for s in GS.sch.all_sheets:
                vname = 'SHEET_TITLE_' + str(s.sheet)
                logger.debugl(2, f"- {vname}={s.title}")
                text_variables[vname] = s.title
                defined.add(str(s.sheet))
            for n in range(GS.global_set_text_variables_sheet_title_min):
                n_str = str(n+1)
                if n_str not in defined:
                    vname = 'SHEET_TITLE_' + n_str
                    logger.debugl(2, f"- {vname}={GS.global_set_text_variables_sheet_title_default}")
                    text_variables[vname] = GS.global_set_text_variables_sheet_title_default

        GS.pro_variables = text_variables
        logger.debug("- Current variables: {}".format(text_variables))
        # Define the requested variables
        if GS.pcb_file:
            os.environ['KIBOT_PCB_NAME'] = GS.pcb_file
        if GS.sch_file:
            os.environ['KIBOT_SCH_NAME'] = GS.sch_file
        bash_command = None
        for r in o:
            text = r.text
            if not text and r.command:
                command = r.command
                if re_git.search(command):
                    git_command = self.ensure_tool('git')
                    command = re_git.sub(r'\1'+git_command.replace('\\', r'\\')+' ', command)
                if r.expand_in_command:
                    command = Optionable.expand_filename_both(self, command, make_safe=False)
                if not bash_command:
                    bash_command = self.ensure_tool('Bash')
                cmd = [bash_command, '-c', command]
                logger.debug('Executing: '+GS.pasteable_cmd(cmd))
                result = run(cmd, stdout=PIPE, stderr=PIPE, universal_newlines=True)
                if result.returncode:
                    msgs = [f'Failed to execute:\n{command}\nreturn code {result.returncode}']
                    if result.stdout:
                        msgs.append(f'stdout:\n{result.stdout}')
                    if result.stderr:
                        msgs.append(f'stderr:\n{result.stderr}')
                    GS.exit_with_error(msgs, FAILED_EXECUTE)
                if not result.stdout:
                    logger.warning(W_EMPTREP+"Empty value from `{}`".format(r.command))
                text = result.stdout.strip()
            text = r.before + text + r.after
            logger.debug('  - ' + r.name + ' -> ' + text)
            text_variables[r.name] = text
        logger.debug("- Expanding %X patterns in variables")
        # Now that we have the variables defined expand the %X patterns (they could use variables)
        for r in o:
            if r.expand_kibot_patterns:
                text = text_variables[r.name]
                new_text = Optionable.expand_filename_both(self, text, make_safe=False)
                if text != new_text:
                    logger.debug('  - ' + r.name + ' -> ' + new_text)
                    text_variables[r.name] = new_text
        logger.debug("- New list of variables: {}".format(text_variables))
        # Store the modified project
        data['text_variables'] = text_variables
        GS.make_bkp(pro_name)
        with open(pro_name, 'wt') as f:
            f.write(json.dumps(data, sort_keys=True, indent=2))
        if GS.board:
            # Force a project and PCB reload
            GS.reload_project(pro_name)
        # Check if we need to force a PCB text variables reset or update
        if GS.global_invalidate_pcb_text_cache == 'auto':
            logger.debug('Forcing PCB text variables reset')
            GS.global_invalidate_pcb_text_cache = 'yes'
        if GS.global_update_pcb_text_cache == 'auto':
            logger.debug('Forcing PCB text variables update')
            GS.global_update_pcb_text_cache = 'yes'
