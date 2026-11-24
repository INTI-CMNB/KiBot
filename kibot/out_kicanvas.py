# -*- coding: utf-8 -*-
# Copyright (c) 2024 Salvador E. Tropea
# Copyright (c) 2024 Instituto Nacional de Tecnología Industrial
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)
import requests
import os
from .error import KiPlotConfigurationError
from .gs import GS
from .kiplot import load_sch, load_board
from .out_base import VariantOptions
from .macros import macros, document, output_class  # noqa: F401
from . import log

logger = log.get_logger()
VALID_SOURCE = {'schematic', 'pcb', 'project'}
SCRIPT_NAME = 'kicanvas.js'
JS_TEST = """
function ready()
{
 try
   {
    var xmlhttp = new XMLHttpRequest();
    xmlhttp.open('GET', 'fname', false);
    xmlhttp.send();
   }
 catch (error)
   {
    if (window.location.protocol === 'file:')
      {
       document.getElementById('no_file_access').style.display = 'block';
      }
    throw(error);
   }
}

window.addEventListener('DOMContentLoaded', ready);
"""


class KiCanvasOptions(VariantOptions):
    def __init__(self):
        with document:
            self.source = 'schematic'
            """ *[string|list(string)] [schematic,pcb,project] Source to display """
            self.local_script = True
            """ *Download the script and use a copy """
            self.title = ''
            """ Text used to replace the sheet title. %VALUE expansions are allowed.
                If it starts with `+` the text is concatenated """
            self.url_script = 'https://kicanvas.org/kicanvas/kicanvas.js'
            """ URL for the KiCanvas script """
            self.controls = 'full'
            """ [full,basic,none] Which controls are displayed """
            self.download = True
            """ Show the download button """
            self.overlay = True
            """ Show the overlay asking to click """
        super().__init__()
        self._expand_ext = 'html'
        self._expand_id = 'kicanvas'

    def config(self, parent):
        super().config(parent)
        self.source = self.force_list(self.source, lower_case=True)
        for s in self.source:
            if s not in VALID_SOURCE:
                raise KiPlotConfigurationError(f'Invalid source `{s}` must be any of: {", ".join(VALID_SOURCE)}')

    def get_html_name(self, out_dir):
        return os.path.join(out_dir, self.expand_filename_sch(self._parent.output))

    def _get_targets(self, out_dir, only_index=False):
        files = [self.get_html_name(out_dir)]
        if only_index:
            return files
        if self.local_script:
            files.append(os.path.join(out_dir, SCRIPT_NAME))
        for s in self.source:
            if s == 'pcb' and GS.pcb_fname:
                files.append(os.path.join(out_dir, GS.pcb_fname))
            elif s == 'schematic' and GS.sch_file:
                files.extend(GS.sch.file_names_variant(out_dir))
            elif s == 'project' and (GS.sch_file or GS.pcb_file):
                files.extend(GS.copy_project_names(GS.sch_file or GS.pcb_file, ref_dir=out_dir))
        return files

    def get_targets(self, out_dir):
        return self._get_targets(out_dir)

    def get_navigate_targets(self, out_dir):
        """ Targets for the navigate results, just the index """
        return self._get_targets(out_dir, True)

    def save_pcb(self, out_dir):
        out_pcb = os.path.join(out_dir, GS.pcb_fname)
        if self._pcb_saved:
            return out_pcb
        self._pcb_saved = True
        self.set_title(self.title)
        self.filter_pcb_components(do_3D=True)
        logger.debug('Saving PCB to '+out_pcb)
        GS.board.Save(out_pcb)
        self.unfilter_pcb_components(do_3D=True)
        self.restore_title()
        return out_pcb

    def save_sch(self, out_dir):
        if self._sch_saved:
            return
        self._sch_saved = True
        self.set_title(self.title, sch=True)
        logger.debug('Saving Schematic to '+out_dir)
        GS.sch.save_variant(out_dir)
        self.restore_title(sch=True)

    def run(self, out_dir):
        # We declare _any_related=True because we don't know if the PCB/SCH are needed until the output is configured.
        # Now that we know it we can load the PCB and/or SCH.
        for s in self.source:
            if s == 'pcb':
                load_board()
            elif s == 'schematic':
                load_sch()
            else:
                load_sch()
                load_board()
                GS.check_pro()
        # Now that we loaded the needed stuff we can do the parent run
        super().run(out_dir)
        # Download KiCanvas
        if self.local_script:
            logger.debug(f'Downloading the script from `{self.url_script}`')
            try:
                r = requests.get(self.url_script, allow_redirects=True)
            except Exception as e:
                raise KiPlotConfigurationError(f'Failed to download the KiCanvas script from `{self.url_script}`: '+str(e))
            dest = os.path.join(out_dir, SCRIPT_NAME)
            logger.debug(f'Saving the script to `{dest}`')
            GS.write_to_file(r.content, dest)
            script_src = SCRIPT_NAME
        else:
            script_src = self.url_script
        # Generate all pages
        self._sch_saved = self._pcb_saved = False
        for s in self.source:
            # Save the PCB/SCH/Project
            if s == 'pcb':
                self.save_pcb(out_dir)
            elif s == 'schematic':
                self.save_sch(out_dir)
            else:
                self.save_sch(out_dir)
                GS.copy_project(self.save_pcb(out_dir))
        # Create the HTML file
        full_name = self.get_html_name(out_dir)
        logger.debug(f'Creating KiCanvas HTML: {full_name}')
        controlslist = []
        if not self.download:
            controlslist.append('nodownload')
        if not self.overlay:
            controlslist.append('nooverlay')
        controlslist = f' controlslist="{",".join(controlslist)}"' if controlslist else ''
        with GS.create_file(full_name) as f:
            f.write('<!DOCTYPE HTML>\n')
            f.write('<html lang="en">\n')
            f.write('  <body>\n')
            f.write(f'    <script type="module" src="{script_src}"></script>\n')
            # Message to inform we can't read the local files
            f.write('    <div id="no_file_access" style="display: none; ">\n')
            f.write("      <span>The browser can't read local files. Enable it to continue."
                    " I.e. use <i>--allow-file-access-from-files</i> on Chrome</span>\n")
            f.write('    </div>\n')
            # End of message
            f.write(f'    <kicanvas-embed controls="{self.controls}"{controlslist}>\n')
            fname = None
            for s in self.source:
                if s == 'pcb':
                    f.write(f'      <kicanvas-source src="{GS.pcb_fname}"></kicanvas-source>\n')
                    fname = GS.pcb_fname
                elif s == 'schematic':
                    GS.sch_dir
                    for s in sorted(GS.sch.all_sheets, key=lambda x: x.sheet_path_h):
                        fname = os.path.relpath(s.fname, GS.sch_dir)
                        f.write(f'      <kicanvas-source src="{fname}"></kicanvas-source>\n')
                else:
                    f.write(f'      <kicanvas-source src="{GS.pro_fname}"></kicanvas-source>\n')
                    fname = GS.pro_fname
            f.write('    </kicanvas-embed>\n')
            # Add test to check if we can read the files
            f.write('    <script>\n')
            f.write(JS_TEST.replace('fname', fname))
            f.write('    </script>\n')
            # End of test
            f.write('  </body>\n')
            f.write('</html>\n')


@output_class
class KiCanvas(BaseOutput):  # noqa: F821
    """ KiCanvas
        Generates an interactive web page to browse the schematic and/or PCB.
        Note that this tool is in alpha stage, so be ready to face some issues.
        Also note that most browsers won't allow Java Script to read local files,
        needed to load the SCH/PCB. So you must use a web server or enable the
        access to local files. In the case of Google Chrome you can use the
        `--allow-file-access-from-files` command line option.
        For more information visit the [KiCanvas web](https://github.com/theacodes/kicanvas)
    """
    def __init__(self):
        super().__init__()
        self._category = ['PCB/docs', 'Schematic/docs']
        self._any_related = True
        with document:
            self.output = GS.def_global_output
            """ *Filename for the output (%i=kicanvas, %x=html) """
            self.options = KiCanvasOptions
            """ *[dict={}] Options for the KiCanvas output """

    def config(self, parent):
        super().config(parent)
        if self.get_user_defined('category'):
            # The user specified a category, don't change it
            return
        # Adjust the category according to the selected output/s
        cat = set()
        for s in self.options.source:
            if s == 'pcb':
                cat.add('PCB/docs')
            elif s == 'schematic':
                cat.add('Schematic/docs')
            else:
                cat.add('PCB/docs')
                cat.add('Schematic/docs')
        self.category = list(cat)

    @staticmethod
    def get_conf_examples(name: str, layers):
        outs = BaseOutput.simple_conf_examples(name, 'Web page to browse the schematic and/or PCB', 'Browse')  # noqa: F821
        sources = []
        if GS.sch_file:
            sources.append('schematic')
        if GS.pcb_file:
            sources.append('pcb')
        outs[0]['options'] = {'source': sources}
        return outs

    def get_navigate_targets(self, out_dir):
        return (self.options.get_navigate_targets(out_dir), [os.path.join(GS.get_resource_path('kicanvas'), 'kicanvas.svg')])
