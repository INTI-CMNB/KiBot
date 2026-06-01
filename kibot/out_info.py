# -*- coding: utf-8 -*-
# Copyright (c) 2022 Salvador E. Tropea
# Copyright (c) 2022 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
"""
Dependencies:
  - from: KiAuto
    role: Show KiAuto installation information
    version: 2.0.0
    version_k7: 2.2.8
    version_k8: 2.3.2
    version_k9: 2.3.5
    version_k10: 2.3.9
"""
import os
import sys
from .gs import GS
from .optionable import BaseOptions
from .kiplot import run_command
from .macros import macros, document, output_class  # noqa: F401
from . import log

logger = log.get_logger()


class InfoOptions(BaseOptions):
    def __init__(self):
        with document:
            self.output = GS.def_global_output
            """ *Filename for the output (%i=info, %x=txt) """
            self.environment = 'names'
            """ [names,none,full] List environment variables.
                IMPORTANT: Don't use `full` unless you know you are not leaking sensitive information """
        super().__init__()
        self._expand_id = 'info'
        self._expand_ext = 'txt'
        self._none_related = True
        self.get_targets = self._get_targets

    def run(self, name):
        dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        ret = run_command([os.path.join(dir, 'kibot-check'), '-p'])
        with open(name, 'wt') as f:
            f.write(ret+'\n')
            # Environment
            if self.environment == 'names':
                f.write('\nEnvironment:\n')
                for n in sorted(os.environ.keys()):
                    f.write(n+'\n')
            elif self.environment == 'full':
                f.write('\nEnvironment:\n')
                for n in sorted(os.environ.keys()):
                    f.write(n+'='+os.environ[n]+'\n')
            # KiAuto
            command = self.check_tool('KiAuto')
            if command:
                ret = run_command([command, '--info'])
                f.write('\nKiAuto:\n'+ret+'\n')


@output_class
class Info(BaseOutput):  # noqa: F821
    """ Info
        Records information about the current run.
        It can be used to know more about the environment used to generate the files.
        Please don't rely on the way things are reported, its content could change,
        adding or removing information """
    def __init__(self):
        super().__init__()
        self._category = ['PCB/docs', 'Schematic/docs']
        with document:
            self.options = InfoOptions
            """ *[dict={}] Options for the `info` output """

    @staticmethod
    def get_conf_examples(name, layers):
        return BaseOutput.simple_conf_examples(name, 'Information about the run', '.')  # noqa: F821
