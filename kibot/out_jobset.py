# -*- coding: utf-8 -*-
# Copyright (c) 2025 Salvador E. Tropea
# Copyright (c) 2025 Instituto Nacional de Tecnología Industrial
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)
import os
import re
from .misc import MISSING_FILES, MISSING_TOOL
from .kiplot import run_command
from .gs import GS
from .out_base_3d import Base3DOptions, Base3D
from .macros import macros, document, output_class  # noqa: F401
from . import log

logger = log.get_logger()


class JobSetOptions(Base3DOptions):
    def __init__(self):
        with document:
            self.jobset = ''
            """ *Name of the KiCad jobset file you want to use. Should have `kicad_jobset` extension.
                Leave empty to look for a jobset with the same name as the project """
            self.run_output = ''
            """ *Output to be generated. When empty KiCad runs all possible outputs.
                Here the name can be obtained from the .kicad_jobset file, in JSON format.
                The `outputs` section contains all the defined outputs. Each output has an `id` use it here """
            self.stop_on_error = True
            """ Stop generation when an error is detected """
        super().__init__()

    def run(self, output):
        if not GS.ki9:
            GS.exit_with_error("`jobset` needs KiCad 9+", MISSING_TOOL)
        if not GS.pro_file:
            GS.exit_with_error("Missing project file, must be available in order to run a jobset", MISSING_FILES)
        jobset_file = self.jobset if self.jobset else GS.pro_file.replace('.kicad_pro', '.kicad_jobset')
        if not os.path.isfile(jobset_file):
            GS.exit_with_error(f"Missing jobset file `{jobset_file}`", MISSING_FILES)
        super().run(output)
        # Base command with overwrite
        cmd = [GS.kicad_cli, 'jobset', 'run', '--file', os.path.abspath(jobset_file)]
        if self.run_output:
            cmd.extend(['--output', self.run_output])
        if self.stop_on_error:
            cmd.append('--stop-on-error')
        # The board
        board_name = self.filter_components(also_sch=True)
        cmd.append(board_name.replace('.kicad_pcb', '.kicad_pro'))
        res = run_command(cmd, change_to=output)
        for j in re.findall(r'\| Running job \d+, (.*)', res):
            logger.info('  - '+j)
        self.remove_temporals()


@output_class
class JobSet(Base3D):
    """ KiCad Jobset (batch execution)
        Generates outputs defined in a KiCad jobset file (.kicad_jobset).
        The outputs will be generated using the `dir` directory as base.
        This is provided just for convenience """
    def __init__(self):
        super().__init__()
        with document:
            self.options = JobSetOptions
            """ *[dict={}] Options for the `jobset` output """
        # We need a full project
        self._both_related = True

    @staticmethod
    def get_conf_examples(name, layers):
        if not GS.ki9:
            return None
        jobfile = GS.pro_file.replace('.kicad_pro', '.kicad_jobset')
        if not os.path.isfile(jobfile):
            return None
        gb = {}
        gb['name'] = 'basic_'+name
        gb['comment'] = 'Run KiCad jobset'
        gb['type'] = name
        gb['dir'] = 'Jobset'
        gb['options'] = {'jobset': jobfile}
        return [gb]
