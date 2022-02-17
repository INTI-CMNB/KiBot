# -*- coding: utf-8 -*-
# Copyright (c) 2021 Salvador E. Tropea
# Copyright (c) 2021 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
import os
import re
import sys
from subprocess import run, PIPE
from .error import KiPlotConfigurationError
from .misc import FAILED_EXECUTE, W_EMPTREP, W_BADCHARS
from .optionable import Optionable
from .pre_base import BasePreFlight
from .macros import macros, document, pre_class  # noqa: F401
from . import log

logger = log.get_logger()


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

    def config(self, parent):
        super().config(parent)
        if not self.tag:
            raise KiPlotConfigurationError("No tag to replace specified ({})".format(str(self._tree)))
        self.tag = self.tag_delimiter + re.escape(self.tag) + self.tag_delimiter


class Base_ReplaceOptions(Optionable):
    """ PCB/SCH replacement options """
    def __init__(self):
        super().__init__()
        with document:
            self.date_command = ''
            """ Command to get the date to use in the PCB.\\
                ```git log -1 --format='%as' -- $KIBOT_PCB_NAME```\\
                Will return the date in YYYY-MM-DD format.\\
                ```date -d @`git log -1 --format='%at' -- $KIBOT_PCB_NAME` +%Y-%m-%d_%H-%M-%S```\\
                Will return the date in YYYY-MM-DD_HH-MM-SS format.\\
                Important: on KiCad 6 the title block data is optional.
                This command will work only if you have a date in the PCB/Schematic """
            self.replace_tags = TagReplaceBase
            """ [dict|list(dict)] Tag or tags to replace """

    def config(self, parent):
        super().config(parent)
        if isinstance(self.replace_tags, type):
            self.replace_tags = []
        elif isinstance(self.replace_tags, TagReplaceBase):
            self.replace_tags = [self.replace_tags]


class Base_Replace(BasePreFlight):  # noqa: F821
    """ [dict] Replaces tags in the PCB/schematic. I.e. to insert the git hash or last revision date """
    def __init__(self, name, value):
        super().__init__(name, value)
        self._context = ''  # PCB/SCH

    @classmethod
    def get_example(cls):
        """ Returns a YAML value for the example config """
        return ("\n    date_command: \"git log -1 --format='%as' -- $KIBOT_{}_NAME\""
                "\n    replace_tags:"
                "\n      - tag: '@git_hash@'"
                "\n        command: 'git log -1 --format=\"%h\" $KIBOT_{}_NAME'"
                "\n        before: 'Git hash: <'"
                "\n        after: '>'\n".format(cls._context, cls._context))

    def replace(self, file):
        logger.debug('Applying replacements to `{}`'.format(file))
        with open(file, 'rt') as f:
            content = f.read()
        os.environ['KIBOT_' + type(self)._context + '_NAME'] = file
        o = self._value
        for r in o.replace_tags:
            text = r.text
            if not text:
                cmd = ['/bin/bash', '-c', r.command]
                result = run(cmd, stdout=PIPE, stderr=PIPE, universal_newlines=True)
                if result.returncode:
                    logger.error('Failed to execute:\n{}\nreturn code {}'.format(r.command, result.returncode))
                    sys.exit(FAILED_EXECUTE)
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
        os.rename(file, file + '-bak')
        with open(file, 'wt') as f:
            f.write(content)
