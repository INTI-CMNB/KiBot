# -*- coding: utf-8 -*-
# Copyright (c) 2022-2024 Salvador E. Tropea
# Copyright (c) 2022-2024 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
import os
from subprocess import CalledProcessError
from .gs import GS
from .kiplot import run_command
from .out_base import VariantOptions
from .pre_base import BasePreFlight
from .macros import macros, document, output_class  # noqa: F401
from . import log

logger = log.get_logger()


def has_repo(git_command, file):
    try:
        run_command([git_command, 'ls-files', '--error-unmatch', file], change_to=os.path.dirname(file), just_raise=True)
    except CalledProcessError:
        logger.debug("File `{}` not inside a repo".format(file))
        return 0
    try:
        res = run_command([git_command, 'log', '--oneline', '--', file], change_to=os.path.dirname(file), just_raise=True)
    except CalledProcessError:
        logger.debug("Failed to get log for `{}`".format(file))
        return 0
    return len(res.split('\n'))


class AnyDiffOptions(VariantOptions):
    def __init__(self):
        with document:
            self.zones = 'global'
            """ [global,fill,unfill,none] How to handle PCB zones. The default is *global* and means that we
                fill zones if the *check_zone_fills* preflight is enabled. The *fill* option always forces
                a refill, *unfill* forces a zone removal and *none* lets the zones unchanged """
        super().__init__()
        self._expand_id = 'diff'
        self._expand_ext = 'pdf'
        self._kiri_mode = False

    def add_zones_ops(self, cmd):
        if self.zones == 'global':
            if BasePreFlight.get_option('check_zone_fills'):
                cmd.extend(['--zones', 'fill'])
        elif self.zones == 'fill':
            cmd.extend(['--zones', 'fill'])
        elif self.zones == 'unfill':
            cmd.extend(['--zones', 'unfill'])

    def add_to_cache(self, name, hash):
        cmd = [self.command, '--no_reader', '--only_cache', '--old_file_hash', hash, '--cache_dir', self.cache_dir]
        if GS.debug_level > 0:
            cmd.append('-'+'v'*GS.debug_level)
        if self._kiri_mode:
            cmd.append('--kiri_mode')
        self.add_zones_ops(cmd)
        if self.incl_file:
            cmd.extend(['--layers', self.incl_file])
        if not hasattr(self, 'only_first_sch_page') or not self.only_first_sch_page:
            cmd.append('--all_pages')
        if GS.debug_enabled:
            cmd.insert(1, '-'+'v'*GS.debug_level)
        cmd.extend([name, name])
        self.name_used_for_cache = name
        run_command(cmd)

    def run_git(self, cmd, cwd=None, just_raise=False):
        if cwd is None:
            cwd = self.repo_dir
        return run_command([self.git_command]+cmd, change_to=cwd, just_raise=just_raise, force_en=True)

    def git_dirty(self, file=None):
        ops = ['status', '--porcelain', '-uno']
        if file is not None:
            ops.append(file)
        return self.run_git(ops)

    def remove_git_worktree(self, name):
        logger.debug('Removing temporal checkout at '+name)
        self.run_git(['worktree', 'remove', '--force', name])

    def write_empty_file(self, name, create_tmp=False):
        base, ext = os.path.splitext(name)
        kind = 'PCB' if ext == '.kicad_pcb' else 'schematic'
        if create_tmp:
            # Use a temporary file
            name = GS.tmp_file(suffix=ext)
            base = os.path.splitext(name)[0]
        to_remove = [name]
        logger.debug('Creating empty '+kind+': '+name)
        with open(name, 'w') as f:
            if ext == '.kicad_sch':
                f.write("(kicad_sch (version 20211123) (generator eeschema))\n")
            elif ext == '.sch':
                f.write("EESchema Schematic File Version 4\nEELAYER 30 0\nEELAYER END\n$Descr A4 11693 8268\n"
                        "$EndDescr\n$EndSCHEMATC\n")
            elif ext == '.kicad_pcb':
                f.write("(kicad_pcb (version 20171130) (host pcbnew 5.1.5))\n")
            else:  # pragma: no cover
                raise AssertionError('Unknown extension')
        if ext == '.sch':
            lib_name = base+'-cache.lib'
            if not os.path.isfile(lib_name):
                logger.debug('Creating dummy cache lib: '+lib_name)
                with open(lib_name, 'w') as f:
                    f.write("EESchema-LIBRARY Version 2.4\n#\n#End Library\n")
                to_remove.append(lib_name)
        return name, to_remove

    def save_layers_incl(self, layers):
        self._solved_layers = layers
        logger.debug('Including layers:')
        txt = ''
        for la in layers:
            logger.debug(f'- {la.layer} ({la.id})')
            txt += str(la.id)+'\n'
        self.incl_file = GS.tmp_file(content=txt, suffix='.lst')
        return self.incl_file
