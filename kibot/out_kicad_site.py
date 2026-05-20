# -*- coding: utf-8 -*-
# Copyright (c) 2026 Salvador E. Tropea
# Copyright (c) 2026 Instituto Nacional de Tecnología Industrial
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)
import os
import shutil
from urllib.parse import urljoin
from .error import KiPlotConfigurationError
from .misc import RENDERERS, INTERNAL_ERROR, W_EXTRAGEN
from .gs import GS
from .kiplot import run_output, get_output_targets
from .optionable import BaseOptions, Optionable
from .out_base import BaseOutput
from .registrable import RegOutput
from .macros import macros, document, output_class  # noqa: F401
from . import log


logger = log.get_logger()


class KiCad_SiteAssembly(Optionable):
    """ An assembly model """
    def __init__(self):
        super().__init__()
        self._unknown_is_error = True
        with document:
            self.name = ''
            """ *Name for the downloadable item """
            self.output = ''
            """ Output that generates it """
        self._item_style = 'assembly model'
        self._name_example = '3D model'
        self._output_example = 'export_glb'

    def config(self, parent):
        super().config(parent)
        if not self.name:
            raise KiPlotConfigurationError(f"Missing or empty `name` in {self._item_style} item ({self._tree})")
        if not self.output:
            raise KiPlotConfigurationError(f"Missing or empty `output` in {self._item_style} item ({self._tree})")
        if not hasattr(self, 'dir'):
            self.dir = ''  # 'assembly'

    def __str__(self):
        return f"{self.name} [{self.output}] -> {self.dir}"


class KiCad_SiteDownload(KiCad_SiteAssembly):
    """ An item to download """
    def __init__(self, name=None, output=None, dir=None):
        super().__init__()
        with document:
            self.dir = ''
            """ Internal directory to store it, leave empty to use the same as the output that generates it """
        self._item_style = 'download'
        if name:
            self.name = name
        if output:
            self.output = output
        if dir:
            self.dir = dir
        self._name_example = 'Schematic (PDF)'
        self._output_example = 'schematic'


class KiCad_SiteDiff(KiCad_SiteDownload):
    """ A diff item """
    def __init__(self):
        super().__init__()
        self._item_style = 'diff'
        self.set_doc('name', '*[string] Name for the diff item')
        self._name_example = 'Schematic diff'
        self._output_example = 'diff_sch'


class KiCad_SiteOptions(BaseOptions):
    def __init__(self):
        with document:
            self.base_url = ''
            """ *Base URL for the generated site. I.e. https://USER.github.io/PROJECT/
                 Without the version part """
            self.title = ''
            """ *Title for the site, leave empty to use the one from `hugo.yaml`.
                %X and KiCad variables are expanded """
            self.version = 'auto'
            """ Version for the generated site. `auto` tries to figure out it.
                Currently it just uses the GITHUB_REF environment variable to detect a tag, otherwise it
                just assumes this is `latest` """
            self.renders = Optionable
            """ [string|list(string)=''] Name of one or more outputs providing images for the PCB """
            self.downloads = KiCad_SiteDownload
            """ [dict|list(dict)=[]] Downloadable resources for releases, not for `latest` """
            self.diffs = KiCad_SiteDiff
            """ [dict|list(dict)=[]] Diff resources, usually one for the PCB and another for the schematic """
            self.ibom = ''
            """ Name of the iBoM output. Use `None` to skip """
            self.bom = ''
            """ Name of the BoM output to use as embedded HTML. Use `None` to skip """
            self.kiri = ''
            """ Name of the KiRi output to use as embedded HTML. Use `None` to skip """
            self.assembly_models = KiCad_SiteAssembly
            """ [dict|list(dict)=[]] 3D assembly models """
            self.force_copy = False
            """ By default we skip the copy to the destination dir if the file is already there and newer.
                Enabling this option we always do the copy """
            self.dest_subdir = 'static'
            """ Subdirectory where the files will be copied inside the destination `dir` """
            self.pcb_first = False
            """ List the PCB first, KiCanvas will show the PCB by default, instead of the schematic """
        super().__init__()

    def config(self, parent):
        super().config(parent)

    def _get_targets(self, out_dir, only_index=False):
        # The config file
        self.dir_name = self._parent.expand_dirname(out_dir)
        self._targets = [os.path.join(self.dir_name, 'config_override.yaml')]
        if only_index:
            return self._targets

        # PCB & Schematic
        self.add_target_name(GS.pcb_file, "kicad")
        for f in GS.sch.get_files():
            rel_name = os.path.relpath(f, GS.sch_dir)
            self.add_target_name(f, os.path.join("kicad", os.path.dirname(rel_name)))
        # Renders
        images, _ = self.solve_renderers(dry_run=True)
        for f in images:
            self.add_target_name(f, "3D")
        # Downloads
        if self.downloads:
            for o in self.downloads:
                file, subdir = self.solve_download(o, dry_run=True)
                self.add_target_name(file, o.dir or subdir)
        # Diffs
        if self.diffs:
            for o in self.diffs:
                file, subdir = self.solve_download(o, kind='Diffs', dry_run=True)
                file = self.add_target_name(file, o.dir or subdir)
        # iBoM
        if self.ibom != 'None':
            out_name = self.get_ibom()
            if out_name:
                file, subdir = self.solve_download(KiCad_SiteDownload(output=out_name), kind='iBoM', dry_run=True)
                self.add_target_name(file, subdir)
        # BoM
        if self.bom != 'None':
            out_name = self.get_bom()
            if out_name:
                file, subdir = self.solve_download(KiCad_SiteDownload(output=out_name), kind='BoM', dry_run=True)
                self.add_target_name(file, subdir)
        # Assembly models
        if self.assembly_models:
            for o in self.assembly_models:
                file, subdir = self.solve_download(o, kind='Assembly model', dry_run=True)
                self.add_target_name(file, o.dir or subdir)

        return self._targets

    def get_targets(self, out_dir):
        return self._get_targets(out_dir)

    def get_navigate_targets(self, out_dir):
        return self._get_targets(out_dir, True)

    def get_simple(self, user_value, check, name, fail=False):
        if user_value:
            return user_value
        out = next(filter(check, RegOutput.get_outputs()), None)
        if out:
            return out.name
        if fail:
            raise KiPlotConfigurationError(f"No {name} output specified and I can't find it, use `None`")

    def add_simple_dep(self, deps, user_value, check, name):
        if user_value == 'None':
            return
        out_name = self.get_simple(user_value, check, name)
        if out_name:
            deps.add(out_name)

    def get_dependencies(self):
        # PCB & Schematic
        deps = {GS.pcb_file}
        if GS.sch:
            deps.update(GS.sch.get_files())
        else:
            deps.add(GS.sch_file)
        # Renders
        _, outs = self.solve_renderers()
        deps.update(outs)
        # Downloads
        deps.update([o.output for o in self.downloads])
        # Diffs
        deps.update([o.output for o in self.diffs])
        # iBoM
        self.add_simple_dep(deps, self.ibom, lambda x: x.type == 'ibom', 'iBoM')
        # BoM
        self.add_simple_dep(deps, self.bom, lambda x: x.type == 'bom' and x.options._format == 'html', 'BoM')
        # KiRi
        self.add_simple_dep(deps, self.kiri, lambda x: x.type == 'kiri', 'KiRi')
        # Assembly models
        deps.update([o.output for o in self.assembly_models])
        return sorted(deps)

    def copy(self, file, dest):
        if not os.path.isfile(file):
            raise KiPlotConfigurationError(f"Missing file `{file}`")

        sub_dest = os.path.join(dest, os.path.basename(file))
        full_dest = os.path.join(self.dir_name, self.dest_subdir, sub_dest)

        # Check if copy is needed
        should_copy = self.force_copy or not os.path.exists(full_dest)
        if not should_copy:
            # If it exists and we aren't forcing, compare timestamps
            if os.path.getmtime(file) > os.path.getmtime(full_dest):
                should_copy = True

        if should_copy:
            os.makedirs(os.path.dirname(full_dest), exist_ok=True)
            logger.debug(f"- Copying {file} -> {full_dest}")
            shutil.copy2(file, full_dest)
        else:
            logger.debug(f"- Skipping {file} (destination is newer or equal) ({full_dest})")

        return sub_dest

    def add_target_name(self, file, dest):
        sub_dest = os.path.join(dest, os.path.basename(file))
        self._targets.append(os.path.join(self.dir_name, self.dest_subdir, sub_dest))

    def run_output(self, out, file):
        if not os.path.exists(file):
            # The target doesn't exist
            if not out._done:
                # The output wasn't created in this run, try running it
                run_output(out)
            if not os.path.exists(file):
                # Still missing, something is wrong
                GS.exit_with_error(f'Unable to generate `{file}` from {out}', INTERNAL_ERROR)

    def solve_renderers(self, dry_run=False):
        if not self.renders:
            # Nothing specified, get all of them
            outs = [o.name for o in filter(lambda x: x.type in RENDERERS, RegOutput.get_outputs())]
            if not outs:
                raise KiPlotConfigurationError('No renderer output found, must be {}'.format(RENDERERS))
        else:
            # Check they are actually usable
            outs = []
            for out_name in self.renders:
                out = RegOutput.get_output(out_name)
                if out is None:
                    raise KiPlotConfigurationError(f'Unknown output `{out_name}`')
                if out.type not in RENDERERS:
                    raise KiPlotConfigurationError(f"Output `{out}` can't be used to render the PCB, must be {RENDERERS}")
                outs.append(out_name)
        logger.debug(f'- List of renderers: {outs}')
        files = []
        for out_name in outs:
            files_list, out_dir, out = get_output_targets(out_name, self._parent)
            logger.debug(f'  - {out_name}: {files_list}')
            for file in files_list:
                if not dry_run:
                    self.run_output(out, file)
                files.append(file)
        return files, outs

    def solve_download(self, o, kind='Download', dry_run=False, with_subdir=True):
        files_list, out_dir, out = get_output_targets(o.output, self._parent)
        subdir = os.path.relpath(out_dir, GS.out_dir)
        cfiles = len(files_list)
        if cfiles == 0:
            raise KiPlotConfigurationError(f"Output `{out}` doesn't generate files")
        fname = files_list[0]
        if cfiles > 1 and kind != 'KiRi':
            logger.warning(W_EXTRAGEN+f"Output `{out}` generates more than one file, using {os.path.basename(fname)}")
        logger.debug(f"- {kind}: `{out}` -> {fname}")
        if not dry_run:
            self.run_output(out, fname)
        return (fname, subdir) if with_subdir else fname

    def add_sch(self):
        cfg = ''
        for f in GS.sch.get_files():
            rel_name = os.path.relpath(f, GS.sch_dir)
            cfg += f'    - "{rel_name}"\n'
            self.copy(f, os.path.join("kicad", os.path.dirname(rel_name)))
        return cfg

    def add_pcb(self):
        self.copy(GS.pcb_file, "kicad")
        return f'    - "{GS.pcb_fname}"\n'

    def add_simple_cfg(self, user_value, check, name, skip=False):
        if user_value == 'None':
            return ''
        out_name = self.get_simple(user_value, check, name, fail=not skip)
        if out_name is None:
            return ''
        file, subdir = self.solve_download(KiCad_SiteDownload(output=out_name), kind=name)
        self.copy(file, subdir)
        return f'  {name.lower()}: "{os.path.join(subdir, os.path.basename(file))}"\n'

    def run(self, dir_name):
        self.dir_name = dir_name
        cfg = ''

        # URL
        if self.version == 'auto':
            github_ref = os.environ.get("GITHUB_REF", "")
            tag = github_ref.replace("refs/tags/", "", 1) if github_ref.startswith("refs/tags/") else "latest"
        else:
            tag = self.version
        url = urljoin(self.base_url+'/', tag)
        cfg += f'baseURL: "{url}"\n'
        if self.title:
            cfg += f'title: "{self.expand_filename_sch(self.title)}"\n'
        cfg += "params:\n"

        # Version
        version = "main" if tag == "latest" else tag
        cfg += f'  version: "{version}"\n'

        # PCB & Schematic
        cfg += "  kicadFiles:\n"
        if self.pcb_first:
            cfg += self.add_pcb()
            cfg += self.add_sch()
        else:
            cfg += self.add_sch()
            cfg += self.add_pcb()

        # Renders
        images, _ = self.solve_renderers()
        if not images:
            raise KiPlotConfigurationError("No `renders` provided, please add at least one output from {RENDERERS}")
        cfg += '  renderDir: "."\n'
        cfg += "  renders:\n"
        for f in images:
            rel_name = os.path.relpath(f, GS.out_dir)
            cfg += f'    - "{rel_name}"\n'
            self.copy(f, os.path.dirname(rel_name))

        # Downloads
        if self.downloads:
            cfg += "  downloads:\n"
            for o in self.downloads:
                cfg += f'    - name: "{o.name}"\n'
                file, subdir = self.solve_download(o)
                file = self.copy(file, o.dir or subdir)
                cfg += f'      path: "{file}"\n'

        # Diffs
        if self.diffs:
            cfg += "  diffs:\n"
            for o in self.diffs:
                cfg += f'    - name: "{o.name}"\n'
                file, subdir = self.solve_download(o, kind='Diffs')
                file = self.copy(file, o.dir or subdir)
                cfg += f'      path: "{file}"\n'

        # iBoM
        cfg += self.add_simple_cfg(self.ibom, lambda x: x.type == 'ibom', 'iBoM')

        # BoM
        cfg += self.add_simple_cfg(self.bom, lambda x: x.type == 'bom' and x.options._format == 'html', 'BoM')

        # KiRi
        cfg += self.add_simple_cfg(self.kiri, lambda x: x.type == 'kiri', 'KiRi', skip=True)

        # Assembly models
        cfg += '  assemblyDir: "."\n'
        if self.assembly_models:
            cfg += "  assemblyModels:\n"
            for o in self.assembly_models:
                cfg += f'    - name: "{o.name}"\n'
                file, subdir = self.solve_download(o, kind='Assembly model')
                if o.dir:
                    subdir = o.dir
                cfg += f'      file: "{os.path.join(subdir, os.path.basename(file))}"\n'
                self.copy(file, subdir)

        fname = os.path.join(dir_name, 'config_override.yaml')
        logger.debug(f'Writing config to: {fname}\n{cfg}')
        with open(fname, 'wt') as f:
            f.write(cfg)


@output_class
class KiCad_Site(BaseOutput):
    """ Hugo KiCad Site helper
        Used to generate web sites for your project
        Use the `dir` option to select the place where the site is generated.
        Currently this output just generates the configuration for the Hugo Theme, for more information visit:
        [Hugo KiCad Site](https://github.com/laenzlinger/hugo-kicad-site) """
    def __init__(self):
        super().__init__()
        with document:
            self.options = KiCad_SiteOptions
            """ *[dict={}] Options for the `kicad_site` output """
        self._category = 'PCB/docs'
        self._both_related = True

    def get_navigate_targets(self, out_dir):
        return self.options.get_navigate_targets(out_dir), None

    def get_dependencies(self):
        return self.options.get_dependencies()
