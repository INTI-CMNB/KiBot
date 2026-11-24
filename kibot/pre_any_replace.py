# -*- coding: utf-8 -*-
# Copyright (c) 2021-2024 Salvador E. Tropea
# Copyright (c) 2021-2024 Instituto Nacional de Tecnología Industrial
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)
import os
import re
from subprocess import run, PIPE
from .error import KiPlotConfigurationError
from .misc import FAILED_EXECUTE, W_EMPTREP, W_BADCHARS, pretty_list
from .optionable import Optionable
from .pre_base import BasePreFlight
from .gs import GS
from .macros import macros, document, pre_class  # noqa: F401
from . import log

logger = log.get_logger()
re_git = re.compile(r'([^a-zA-Z_]|^)(git) ')


class TagReplaceBase(Optionable):
    """ Tags to be replaced """
    def __init__(self):
        super().__init__()
        self._unknown_is_error = True
        with document:
            self.tag = ''
            """ Name of the tag to replace. Use `version` for a tag named `@version@` """
            self.tag_delimiter = '@'
            """ Character used to indicate the beginning and the end of a tag.
                Don't change it unless you really know about KiCad's file formats """
            self.text = ''
            """ Text to insert instead of the tag """
            self.command = ''
            """ Command to execute to get the text, will be used only if `text` is empty """
            self.before = ''
            """ Text to add before the output of `command` """
            self.after = ''
            """ Text to add after the output of `command` """
        self._relax_check = False
        self._tag_example = 'version'

    def config(self, parent):
        super().config(parent)
        if not self.tag:
            raise KiPlotConfigurationError("No tag to replace specified ({})".format(str(self._tree)))
        self.tag = self.tag_delimiter + re.escape(self.tag) + self.tag_delimiter

    def __str__(self):
        txt = self.tag_delimiter+self.tag+self.tag_delimiter
        if self.text:
            txt += f' -> `{self.text}`'
        else:
            txt += f' -> command(`{self.command}`)'
        return txt


class Base_ReplaceOptions(Optionable):
    """ PCB/SCH replacement options """
    def __init__(self):
        super().__init__()
        with document:
            self.date_command = ''
            """ Command to get the date to use in the PCB. |br|
                ```git log -1 --format='%as' -- \"$KIBOT_PCB_NAME\"``` |br|
                Will return the date in YYYY-MM-DD format. |br|
                ```date -d @`git log -1 --format='%at' -- \"$KIBOT_PCB_NAME\"` +%Y-%m-%d_%H-%M-%S``` |br|
                Will return the date in YYYY-MM-DD_HH-MM-SS format. |br|
                Important: on KiCad 6 the title block data is optional.
                This command will work only if you have a date in the PCB/Schematic """
            self.replace_tags = TagReplaceBase
            """ [dict|list(dict)=[]] Tag or tags to replace """


class Base_Replace(BasePreFlight):  # noqa: F821
    @classmethod
    def get_example(cls) -> str:
        """ Returns a YAML value for the example config """
        return ("\n    date_command: 'git log -1 --format=\"%as\" -- \"$KIBOT_{}_NAME\"'"
                "\n    replace_tags:"
                "\n      - tag: '@git_hash@'"
                "\n        command: 'git log -1 --format=\"%h\" \"$KIBOT_{}_NAME\"'"
                "\n        before: 'Git hash: <'"
                "\n        after: '>'".format(cls._context, cls._context))

    def __str__(self):
        res = self.type
        main_value = getattr(self, self.type)
        if len(main_value.replace_tags):
            res += f' ({pretty_list([v.tag for v in main_value.replace_tags])})'
        return res

    def replace(self, file, o):
        logger.debug('Applying replacements to `{}`'.format(file))
        with open(file, 'rt') as f:
            content = f.read()
        os.environ['KIBOT_' + type(self)._context + '_NAME'] = file
        bash_command = None
        for r in o.replace_tags:
            text = r.text
            if not text:
                command = r.command
                if re_git.search(command):
                    git_command = self.ensure_tool('git')
                    command = re_git.sub(r'\1'+git_command+' ', command)
                if not bash_command:
                    bash_command = self.ensure_tool('Bash')
                cmd = [bash_command, '-c', command]
                logger.debugl(2, 'Running: {}'.format(cmd))
                result = run(cmd, stdout=PIPE, stderr=PIPE, universal_newlines=True)
                if result.returncode:
                    GS.exit_with_error('Failed to execute:\n{r.command}\nreturn code {result.returncode}', FAILED_EXECUTE)
                if not result.stdout:
                    logger.warning(W_EMPTREP+"Empty value from `{}` skipping it".format(r.command))
                    continue
                text = result.stdout.strip()
            text = r.before + text + r.after
            if not r._relax_check:
                new_text = re.sub(r'["\\\\\s]', '_', text)
                if new_text != text:
                    logger.warning(W_BADCHARS+"Replace text can't contain double quotes, backslashes or white spaces ({})".
                                   format(text))
                    text = new_text
            logger.debug('- ' + r.tag + ' -> ' + text)
            content = re.sub(r.tag, text, content, flags=re.MULTILINE)
        GS.make_bkp(file)
        with open(file, 'wt') as f:
            f.write(content)
