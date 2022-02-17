# -*- coding: utf-8 -*-
# Copyright (c) 2020-2021 Salvador E. Tropea
# Copyright (c) 2020-2021 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
import os
from sys import (exit)
from .macros import macros, pre_class  # noqa: F401
from .error import (KiPlotConfigurationError)
from .gs import (GS)
from .optionable import Optionable
from .kiplot import check_script, exec_with_retry, load_board, add_extra_options
from .misc import (CMD_PCBNEW_RUN_DRC, URL_PCBNEW_RUN_DRC, DRC_ERROR)
from .pre_base import BasePreFlight
from .log import (get_logger)

logger = get_logger(__name__)


@pre_class
class Run_DRC(BasePreFlight):  # noqa: F821
    """ [boolean=false] Runs the DRC (Distance Rules Check). To ensure we have a valid PCB.
        The report file name is controlled by the global output pattern (%i=drc %x=txt) """
    def __init__(self, name, value):
        super().__init__(name, value)
        if not isinstance(value, bool):
            raise KiPlotConfigurationError('must be boolean')
        self._enabled = value
        self._pcb_related = True
        self._expand_id = 'drc'
        self._expand_ext = 'txt'

    def get_targets(self):
        """ Returns a list of targets generated by this preflight """
        load_board()
        out_pattern = GS.global_output if GS.global_output is not None else GS.def_global_output
        name = Optionable.expand_filename_pcb(self, out_pattern)
        return [os.path.abspath(os.path.join(self.expand_dirname(GS.out_dir), name))]

    def run(self):
        check_script(CMD_PCBNEW_RUN_DRC, URL_PCBNEW_RUN_DRC, '1.4.0')
        output = self.get_targets()[0]
        logger.debug('DRC report: '+output)
        cmd = [CMD_PCBNEW_RUN_DRC, 'run_drc', '-o', output]
        if GS.filter_file:
            cmd.extend(['-f', GS.filter_file])
        if BasePreFlight.get_option('ignore_unconnected'):  # noqa: F821
            cmd.append('-i')
        cmd.extend([GS.pcb_file, self.expand_dirname(GS.out_dir)])
        # If we are in verbose mode enable debug in the child
        cmd, video_remove = add_extra_options(cmd)
        logger.info('- Running the DRC')
        ret = exec_with_retry(cmd)
        if video_remove:
            video_name = os.path.join(self.expand_dirname(GS.out_dir), 'pcbnew_run_drc_screencast.ogv')
            if os.path.isfile(video_name):
                os.remove(video_name)
        if ret:
            if ret > 127:
                ret = -(256-ret)
            if ret < 0:
                logger.error('DRC errors: %d', -ret)
            else:
                logger.error('DRC returned %d', ret)
            exit(DRC_ERROR)
