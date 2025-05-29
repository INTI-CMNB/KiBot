# -*- coding: utf-8 -*-
# Copyright (c) 2021-2025 Salvador E. Tropea
# Copyright (c) 2021-2025 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
"""
Dependencies:
  - name: RAR
    url: https://www.rarlab.com/
    url_down: https://www.rarlab.com/download.htm
    help_option: -?
    downloader: rar
    role: Compress in RAR format
    debian: rar
    arch: rar(AUR)
"""
import re
import os
import glob
import sys
from zipfile import ZipFile, ZIP_STORED, ZIP_DEFLATED, ZIP_BZIP2, ZIP_LZMA
from tarfile import open as tar_open
from collections import OrderedDict
from .gs import GS
from .kiplot import config_output, run_output, get_output_targets, run_command
from .misc import WRONG_INSTALL, W_EMPTYZIP, INTERNAL_ERROR, W_NOFILES
from .optionable import Optionable, BaseOptions
from .registrable import RegOutput
from .macros import macros, document, output_class  # noqa: F401
from . import log

logger = log.get_logger()


class FilesListCompress(Optionable):
    def __init__(self):
        super().__init__()
        with document:
            self.source = '*'
            """ *File names to add, wildcards allowed. Use ** for recursive match.
                By default this pattern is applied to the output dir specified with `-d` command line option.
                See the `from_cwd` and `from_output_dir` options """
            self.from_cwd = False
            """ Use the current working directory instead of the dir specified by `-d` """
            self.from_output_dir = False
            """ Use the current directory specified by the output instead of the dir specified by `-d`.
                Note that it only applies when using `from_output` and no `dest` is specified.
                It has more prescedence than `from_cwd` """
            self.from_output = ''
            """ *Collect files from the selected output.
                When used the `source` option is ignored """
            self.filter = '.*'
            """ A regular expression that source files must match """
            self.dest = ''
            """ Destination directory inside the archive, empty means the same of the file """

    def __str__(self):
        txt = self.from_output if self.from_output else self.source
        filter = f' (filter: `{self.filter}`)' if self.filter and self.filter != '.*' else ''
        dest = f' -> {self.dest}' if self.dest else ''
        return txt+filter+dest


class CompressOptions(BaseOptions):
    ZIP_ALGORITHMS = {'auto': ZIP_DEFLATED,
                      'stored': ZIP_STORED,
                      'deflated': ZIP_DEFLATED,
                      'bzip2': ZIP_BZIP2,
                      'lzma': ZIP_LZMA}
    TAR_MODE = {'auto': 'bz2',
                'stored': '',
                'deflated': 'gz',
                'bzip2': 'bz2',
                'lzma': 'xz'}

    def __init__(self):
        with document:
            self.output = GS.def_global_output
            """ *Name for the generated archive (%i=name of the output %x=according to format) """
            self.format = 'ZIP'
            """ *[ZIP,TAR,RAR] Output file format """
            self.compression = 'auto'
            """ [auto,stored,deflated,bzip2,lzma] Compression algorithm. Use auto to let KiBot select a suitable one """
            self.files = FilesListCompress
            """ *[list(dict)=[]] Which files will be included """
            self.move_files = False
            """ Move the files to the archive. In other words: remove the files after adding them to the archive """
            self.remove_files = None
            """ {move_files} """
            self.follow_links = True
            """ Store the file pointed by symlinks, not the symlink """
            self.skip_not_run = False
            """ Skip outputs with `run_by_default: false` """
        super().__init__()

    def config(self, parent):
        super().config(parent)
        if not self.get_user_defined('files'):
            logger.warning(W_EMPTYZIP+'No files provided, creating an empty archive')
        self._expand_id = parent.name
        self._expand_ext = self.solve_extension()

    def create_zip(self, output, files):
        extra = {}
        extra['compression'] = self.ZIP_ALGORITHMS[self.compression]
        if sys.version_info >= (3, 7):
            extra['compresslevel'] = 9
        with ZipFile(output, 'w', **extra) as zip:
            for fname, dest in files.items():
                if dest == '/':
                    # When we move all to / the main dir is stored as / and Python crashes
                    continue
                logger.debug('Adding '+fname+' as '+dest)
                zip.write(fname, dest)

    def create_tar(self, output, files):
        with tar_open(output, 'w:'+self.TAR_MODE[self.compression]) as tar:
            for fname, dest in files.items():
                logger.debug('Adding '+fname+' as '+dest)
                tar.add(fname, dest)

    def create_rar(self, output, files):
        if os.path.isfile(output):
            os.remove(output)
        command = self.ensure_tool('RAR')
        if command is None:
            return
        for fname, dest in files.items():
            logger.debugl(2, 'Adding '+fname+' as '+dest)
            cmd = [command, 'a', '-m5', '-ep', '-ap'+os.path.dirname(dest), output, fname]
            run_command(cmd, err_msg='Failed to invoke rar command, error {ret}', err_lvl=WRONG_INSTALL)

    def solve_extension(self):
        if self.format == 'ZIP':
            return 'zip'
        if self.format == 'RAR':
            return 'rar'
        # TAR
        ext = 'tar'
        sub_ext = self.TAR_MODE[self.compression]
        if sub_ext:
            ext += '.'+sub_ext
        return ext

    def get_files(self, output, no_out_run=False):
        output_real = os.path.realpath(output)
        files = OrderedDict()
        out_dir_cwd = os.getcwd()
        out_dir_default = self.expand_filename_sch(GS.out_dir)
        dirs_list = set()
        for f in self.files:
            # Get the list of candidates
            files_list = None
            output_out_dir = None
            if f.from_output:
                logger.debugl(2, '- From output `{}`'.format(f.from_output))
                files_list, out_dir, out = get_output_targets(f.from_output, self._parent)
                if not out.run_by_default and self.skip_not_run:
                    continue
                output_out_dir = out_dir
                logger.debugl(2, '- List of files: {}'.format(files_list))
                if not no_out_run:
                    extra_files = []
                    for file in files_list:
                        if not os.path.exists(file):
                            # The target doesn't exist
                            if not out._done:
                                # The output wasn't created in this run, try running it
                                run_output(out)
                            if not os.path.exists(file):
                                # Still missing, something is wrong
                                GS.exit_with_error(f'Unable to generate `{file}` from {out}', INTERNAL_ERROR)
                        if os.path.isdir(file):
                            # Popultate output adds the image dirs
                            # Computing its content is complex:
                            # - We must parse the input markdown
                            # - We must configure and use the renderer output to do the file name expansion
                            # This is almost as complex as generating the whole output, so it adds the dir
                            extra_files += glob.glob(os.path.join(file, '**'), recursive=True)
                    if extra_files:
                        files_list += extra_files
                # Add the output dir and all its subdirs
                dirs_list.add(out_dir)
                for fname in files_list:
                    dname = os.path.dirname(fname)
                    d_rel = os.path.relpath(dname, out_dir)
                    if d_rel == '.':
                        # The out_dir is already there
                        continue
                    # Add a subdir
                    if dname not in dirs_list:
                        dirs_list.add(dname)
                        logger.debugl(2, f'- Adding subdir: {dname}')
                    # Compute the subdirs leading to this one
                    while True:
                        d_rel = os.path.dirname(d_rel)
                        if not d_rel:
                            break
                        dname = os.path.join(out_dir, d_rel)
                        if dname not in dirs_list:
                            dirs_list.add(dname)
                            logger.debugl(2, f'- Adding subdir: {dname}')
            else:
                out_dir = out_dir_cwd if f.from_cwd else out_dir_default
                source = f.expand_filename_both(f.source, make_safe=False)
                source_path = os.path.join(out_dir, source)
                files_list = glob.iglob(source_path, recursive=True)
                files_list = [f for f in files_list if os.path.exists(f)]
                if not files_list:
                    logger.warning(W_NOFILES+f"Pattern `{source_path}` expanded to nothing")
                if GS.debug_level > 1:
                    logger.debug('- Pattern {} list of files: {}'.format(source, files_list))
            # Compute the reference dir when no f.dest
            out_dir = out_dir_cwd if f.from_cwd else out_dir_default
            if f.from_output_dir:
                out_dir = output_out_dir
            # Filter and adapt them
            for fname in filter(re.compile(f.filter).match, files_list):
                fname_real = os.path.realpath(fname) if self.follow_links else os.path.abspath(fname)
                # Avoid including the output
                if fname_real == output_real:
                    continue
                # Compute the destination directory inside the archive
                dest = fname
                if f.dest:
                    dest = os.path.join(f.dest, os.path.basename(fname))
                else:
                    dest = os.path.relpath(dest, out_dir)
                files[fname_real] = dest
        return files, list(dirs_list)

    def get_targets(self, out_dir):
        return [self._parent.expand_filename(out_dir, self.output)]

    def get_dependencies(self):
        output = self.get_targets(self.expand_filename_sch(GS.out_dir))[0]
        files, _ = self.get_files(output, no_out_run=True)
        return files.keys()

    def get_categories(self):
        cats = set()
        for f in self.files:
            if f.from_output:
                out = RegOutput.get_output(f.from_output)
                if out is not None:
                    config_output(out)
                    if out.category:
                        cats.update(out.category)
            else:
                cats.add('Compress')
        return list(cats)

    def run(self, output):
        # Output file name
        logger.debug('Collecting files')
        # Collect the files
        files, dirs_outs = self.get_files(output)
        logger.debug('Generating `{}` archive'.format(output))
        if self.format == 'ZIP':
            self.create_zip(output, files)
        elif self.format == 'TAR':
            self.create_tar(output, files)
        elif self.format == 'RAR':
            self.create_rar(output, files)
        if self.move_files:
            dirs = dirs_outs
            for fname in files.keys():
                if os.path.isfile(fname):
                    os.remove(fname)
                    logger.debug('Removing '+fname)
                elif os.path.isdir(fname):
                    dirs.append(fname)
            for d in sorted(dirs, key=lambda x: len(x.split(os.sep)), reverse=True):
                logger.debug('Removing '+d)
                try:
                    os.rmdir(d)
                except OSError as e:
                    if e.errno == 39:
                        logger.debug(' Not empty')
                    else:
                        raise


@output_class
class Compress(BaseOutput):  # noqa: F821
    """ Archiver (files compressor)
        Generates a compressed file containing output files.
        This is used to generate groups of files in compressed file format. """
    def __init__(self):
        super().__init__()
        # Make it low priority so it gets created after all the other outputs
        self.priority = 10
        with document:
            self.options = CompressOptions
            """ *[dict={}] Options for the `compress` output """
        self._none_related = True
        # The help is inherited and already mentions the default priority
        self.fix_priority_help()

    def config(self, parent):
        super().config(parent)
        if self.category is None and self.get_user_defined('options'):
            self.category = self.options.get_categories()

    def get_dependencies(self):
        return self.options.get_dependencies()
