# -*- coding: utf-8 -*-
# Copyright (c) 2022 Salvador E. Tropea
# Copyright (c) 2022 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
import re
import os
import glob
from .gs import GS
from .error import KiPlotConfigurationError
from .kiplot import config_output, get_output_dir, run_output, run_command
from .misc import MISSING_TOOL, WRONG_INSTALL, WRONG_ARGUMENTS, INTERNAL_ERROR, W_NOTPDF, MISSING_FILES, W_NOMATCH
from .optionable import Optionable, BaseOptions
from .registrable import RegOutput
from .create_pdf import create_pdf_from_pages
from .macros import macros, document, output_class  # noqa: F401
from . import log

logger = log.get_logger()


class FilesListPDFUnite(Optionable):
    def __init__(self):
        super().__init__()
        with document:
            self.source = '*.pdf'
            """ *File names to add, wildcards allowed. Use ** for recursive match.
                By default this pattern is applied to the output dir specified with `-d` command line option.
                See the `from_cwd` option """
            self.from_cwd = False
            """ Use the current working directory instead of the dir specified by `-d` """
            self.from_output = ''
            """ *Collect files from the selected output.
                When used the `source` option is ignored """
            self.filter = r'.*\.pdf'
            """ A regular expression that source files must match """

    def __str__(self):
        txt = self.from_output if self.from_output else self.source
        filter = f' (filter: `{self.filter}`)' if self.filter and self.filter != '.*' else ''
        return txt+filter


class PDFUniteOptions(BaseOptions):
    def __init__(self):
        with document:
            self.output = GS.def_global_output
            """ *Name for the generated PDF (%i=name of the output %x=pdf) """
            self.outputs = FilesListPDFUnite
            """ *[list(dict)=[]] Which files will be included """
            self.use_external_command = False
            """ Use the `pdfunite` tool instead of PyPDF2 Python module """
        super().__init__()
        self._expand_ext = 'pdf'
        self.get_targets = self._get_targets

    def config(self, parent):
        super().config(parent)
        if not self.outputs:
            KiPlotConfigurationError('Nothing to join')
        self._expand_id = parent.name

    def get_files(self, output, no_out_run=False):
        output_real = os.path.realpath(output)
        files = []
        out_dir_cwd = os.getcwd()
        out_dir_default = self.expand_filename_pcb(GS.out_dir)
        for f in self.outputs:
            # Get the list of candidates
            files_list = None
            if f.from_output:
                out = RegOutput.get_output(f.from_output)
                if out is not None:
                    config_output(out)
                    files_list = out.get_targets(get_output_dir(out.dir, out, dry=True))
                else:
                    GS.exit_with_error(f'Unknown output `{f.from_output}` selected in {self._parent}', WRONG_ARGUMENTS)
                if not no_out_run:
                    for file in files_list:
                        if not os.path.isfile(file):
                            # The target doesn't exist
                            if not out._done:
                                # The output wasn't created in this run, try running it
                                run_output(out)
                            if not os.path.isfile(file):
                                # Still missing, something is wrong
                                GS.exit_with_error('Unable to generate `{file}` from {out}', INTERNAL_ERROR)
            else:
                out_dir = out_dir_cwd if f.from_cwd else out_dir_default
                source = f.expand_filename_both(f.source, make_safe=False)
                files_list = glob.iglob(os.path.join(out_dir, source), recursive=True)
            # Filter and adapt them
            old_len = len(files)
            for fname in filter(re.compile(f.filter).match, files_list):
                fname_real = os.path.realpath(fname)
                # Avoid including the output
                if fname_real == output_real:
                    continue
                files.append(fname_real)
            if len(files) == old_len:
                logger.warning(W_NOMATCH+'No match found for `{}`'.format(f.from_output if f.from_output else f.source))
        return files

    def get_dependencies(self):
        output = self.get_targets(self.expand_filename_pcb(GS.out_dir))[0]
        files = self.get_files(output, no_out_run=True)
        return files

    def run_external(self, files, output):
        cmd = ['pdfunite']+files+[output]
        try:
            run_command(cmd, err_msg='Failed to invoke pdfunite command, error {ret}', err_lvl=WRONG_INSTALL)
        except FileNotFoundError:
            GS.exit_with_error('Missing `pdfunite` command, install it (poppler-utils)', MISSING_TOOL)

    def run(self, output):
        # Output file name
        logger.debug('Collecting files')
        # Collect the files
        files = self.get_files(output)
        for fn in files:
            with open(fn, 'rb') as f:
                sig = f.read(4)
                if sig != b'%PDF':
                    logger.warning(W_NOTPDF+'Joining a non PDF file `{}`, will most probably fail'.format(fn))
        if len(files) < 2:
            GS.exit_with_error(f'At least two files must be joined ({files})', MISSING_FILES)
        logger.debug('Generating `{}` PDF'.format(output))
        if os.path.isfile(output):
            os.remove(output)
        if self.use_external_command:
            self.run_external(files, output)
        else:
            create_pdf_from_pages(files, output)


@output_class
class PDFUnite(BaseOutput):  # noqa: F821
    """ PDF joiner
        Generates a new PDF from other outputs.
        This is just a PDF joiner, using `pdfunite` from Poppler Utils. """
    def __init__(self):
        super().__init__()
        with document:
            self.options = PDFUniteOptions
            """ *[dict={}] Options for the `pdfunite` output """
        self._none_related = True

    def get_dependencies(self):
        return self.options.get_dependencies()
