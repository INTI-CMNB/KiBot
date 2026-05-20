# -*- coding: utf-8 -*-
# Copyright (c) 2022-2024 Salvador E. Tropea
# Copyright (c) 2022-2024 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
"""
Dependencies:
  - name: KiCad PCB/SCH Diff
    version: 2.5.1
    role: mandatory
    github: INTI-CMNB/KiDiff
    command: kicad-diff.py
    pypi: kidiff
    downloader: pytool
    id: KiDiff
  - from: Git
    role: Compare with files in the repo
  - from: KiAuto
    role: Compare schematics
    version: 2.2.0
"""
import datetime
import glob
try:
    # Not available on Windows?!
    import pwd
except Exception:
    pass
import os
from shutil import copy2, rmtree
from subprocess import CalledProcessError
from .error import KiPlotConfigurationError
from .gs import GS
from .kicad.color_theme import load_color_theme
from .kiplot import load_any_sch
from .layer import Layer
from .misc import W_NOTHCMP, W_BADGITREPO, try_decode_utf8
from .out_any_diff import AnyDiffOptions, has_repo
from .macros import macros, document, output_class  # noqa: F401
from . import log

logger = log.get_logger()
HASH_LOCAL = '_local_'
UNDEF_COLOR = '#DBDBDB'
LAYER_COLORS_HEAD = """/* ==============================
   Layer colors
** ============================*/
"""


def get_cur_user():
    try:
        name = pwd.getpwuid(os.geteuid())[4]
        return name.split(',')[0]
    except Exception:
        return 'Local user'


class KiRiOptions(AnyDiffOptions):
    def __init__(self):
        with document:
            self.color_theme = '_builtin_classic'
            """ *Selects the color theme. Only applies to KiCad 6.
                To use the KiCad 6 default colors select `_builtin_default`.
                Usually user colors are stored as `user`, but you can give it another name """
            self.background_color = "#FFFFFF"
            """ Color used for the background of the diff canvas """
            self.max_commits = 0
            """ Maximum number of commits to include. Use 0 for all available commits """
            self.revision = 'HEAD'
            """ Starting point for the commits, can be a branch, a hash, etc.
                Note that this can be a revision-range, consult the gitrevisions manual for more information """
            self.keep_generated = False
            """ *Avoid PCB and SCH images regeneration. Useful for incremental usage """
        super().__init__()
        self.add_to_doc("zones", "Be careful with the *keep_generated* option when changing this setting")
        self._kiri_mode = True

    def config(self, parent):
        super().config(parent)
        self.validate_colors(['background_color'])
        if self.max_commits < 0:
            raise KiPlotConfigurationError(f"Wrong number of commits ({self.max_commits}) must be positive")

    def _get_targets(self, out_dir, only_index=False):
        self.init_tools(out_dir)
        hashes, sch_dirty, pcb_dirty, sch_files = self.collect_hashes()
        if len(hashes) + (1 if sch_dirty or pcb_dirty else 0) < 2:
            return []
        if only_index:
            return [os.path.join(self.cache_dir, 'index.html')]
        files = [os.path.join(self.cache_dir, f) for f in ['index.html', 'blank.svg', 'commits', 'kiri-server', 'project']]
        for h in hashes:
            files.append(os.path.join(self.cache_dir, h[0][:7]))
        if sch_dirty or pcb_dirty:
            files.append(os.path.join(self.cache_dir, HASH_LOCAL))
        return files

    def get_targets(self, out_dir):
        return self._get_targets(out_dir)

    def get_navigate_targets(self, out_dir):
        """ Targets for the navigate results, just the index """
        return self._get_targets(out_dir, True)

    def create_layers_incl(self, layers):
        self.incl_file = None
        if not layers:
            self._solved_layers = None
            return False
        self.save_layers_incl(Layer.solve(layers))
        return True

    def do_cache(self, name, tmp_wd, hash):
        name_copy = os.path.join(tmp_wd, name)
        if not os.path.isfile(name_copy):
            self.write_empty_file(name_copy)
        logger.debug('- Using temporal copy: '+name_copy)
        self.add_to_cache(name_copy, hash[:7])
        return name_copy

    def save_pcb_layers(self, hash):
        subdir = os.path.join(hash[:7], '_KIRI_')
        subdir_layers = os.path.join(self.cache_dir, subdir, 'pcb', 'layer-')
        with open(os.path.join(self.cache_dir, subdir, 'pcb_layers'), 'wt') as f:
            if self._solved_layers:
                for la in self._solved_layers:
                    if os.path.isfile(subdir_layers+('%02d' % la.id)+'.svg'):
                        f.write(str(la.id)+'|'+la.layer+'\n')
            else:
                discard = len(subdir_layers)
                for la in sorted(glob.glob(subdir_layers+'??.svg')):
                    id = int(la[discard:discard+2])
                    f.write(str(id)+'|'+GS.board.GetLayerName(id)+'\n')

    def solve_layer_colors(self):
        # Color theme
        self._color_theme = load_color_theme(self.color_theme)
        if self._color_theme is None:
            raise KiPlotConfigurationError("Unable to load `{}` color theme".format(self.color_theme))
        if self._solved_layers is None:
            return
        # Assign a color if none was defined
        layer_id2color = self._color_theme.layer_id2color
        for la in self._solved_layers:
            if la._id in layer_id2color:
                la.color = layer_id2color[la._id]
            else:
                la.color = UNDEF_COLOR

    def save_sch_sheet(self, hash, name_sch):
        # Load the schematic. Really worth?
        sch = load_any_sch(name_sch, GS.sch_basename, fatal=False, extra_msg=f'Commit: {hash}')
        with open(os.path.join(self.cache_dir, hash[:7], '_KIRI_', 'sch_sheets'), 'wt') as f:
            base_dir = os.path.dirname(name_sch)
            for s in sorted(sch.all_sheets, key=lambda x: x.sheet_path_h):
                fname = s.fname
                no_ext = os.path.splitext(os.path.basename(fname))[0]
                rel_name = os.path.relpath(fname, base_dir)
                if s.sheet_path_h == '/':
                    instance_name = sheet_path = GS.sch_basename
                else:
                    instance_name = os.path.basename(s.sheet_path_h)
                    sheet_path = s.sheet_path_h.replace('/', '-')
                    sheet_path = GS.sch_basename+'-'+sheet_path[1:]
                f.write(f'{no_ext}|{rel_name}||{instance_name}|{sheet_path}\n')

    def save_commits(self, commits):
        with open(os.path.join(self.cache_dir, 'commits'), 'wt') as f:
            for c in commits:
                hash = c[0][:7]
                dt = c[1].split()[0]
                author = c[2]
                desc = c[3]
                sch_changed = c[0] in self.commits_with_changed_sch
                pcb_changed = c[0] in self.commits_with_changed_pcb
                f.write(f'{hash}|{dt}|{author}|{desc}|{sch_changed}|{pcb_changed}\n')

    def save_project_data(self):
        today = datetime.datetime.today().strftime('%Y-%m-%d')
        with open(os.path.join(self.cache_dir, 'project'), 'wt') as f:
            f.write((GS.pro_basename or GS.sch_basename or GS.pcb_basename or 'unknown')+'\n')
            f.write((GS.sch_title or 'No title')+'|'+(GS.sch_rev or '')+'|'+(GS.sch_date or today)+'\n')
            f.write((GS.pcb_title or 'No title')+'|'+(GS.pcb_rev or '')+'|'+(GS.pcb_date or today)+'\n')

    def get_modified_status(self, pcb_file, sch_files):
        res = self.run_git(['log', '--pretty=format:%H', self.revision] + self._max_commits + ['--', pcb_file])
        self.commits_with_changed_pcb = set(res.split())
        res = self.run_git(['log', '--pretty=format:%H', self.revision] + self._max_commits + ['--'] + sch_files)
        self.commits_with_changed_sch = set(res.split())
        if GS.debug_level > 1:
            logger.debug(f'Commits with changes in the PCB: {self.commits_with_changed_pcb}')
            logger.debug(f'Commits with changes in the Schematics: {self.commits_with_changed_sch}')

    def copy_index(self, src_dir, src_index, dst_index):
        with open(src_index, 'rt') as src:
            with open(dst_index, 'wt') as dst:
                for ln in src:
                    ln_stripped = ln.strip()
                    if ln_stripped.startswith('<script src="'):
                        # Embed Java Scripts
                        fn = ln_stripped[13:].split('"')[0]
                        with open(os.path.join(src_dir, fn), 'rt') as f:
                            script = f.read()
                        dst.write('<script>\n')
                        dst.write(script)
                        dst.write('\n</script>\n')
                    elif ln_stripped.startswith('<link rel="stylesheet" href="'):
                        # Embed CSS
                        fn = ln_stripped[29:].split('"')[0]
                        if fn == 'layer_colors.css':
                            # Create the colors
                            script = ''
                            for id, color in self._color_theme.layer_id2color.items():
                                script += f'.layer_color_{id} {{ color: {color[:7]}; }}\n'
                        elif fn == 'kiri.css':
                            # Replace the SVGs using its source
                            script = ''
                            with open(os.path.join(src_dir, fn), 'rt') as f:
                                for lns in f:
                                    if lns.startswith("\t--svg: url('"):
                                        fns = lns[13:].split("'")[0]
                                        with open(os.path.join(src_dir, fns), 'rt') as f:
                                            svg = f.read().strip()
                                        script += "\t--svg: url('data:image/svg+xml;utf8,"+svg+"');\n"
                                    elif lns.startswith('#svg-id { background-color: '):
                                        script += f'#svg-id {{ background-color: {self.background_color}; }}\n'
                                    else:
                                        script += lns
                        else:
                            with open(os.path.join(src_dir, fn), 'rt') as f:
                                script = f.read()
                        dst.write('<style>\n')
                        dst.write(script)
                        dst.write('\n</style>\n')
                    else:
                        dst.write(ln)

    def create_kiri_files(self):
        src_dir = GS.get_resource_path('kiri')
        copy2(os.path.join(src_dir, 'kiri-server'), os.path.join(self.cache_dir, 'kiri-server'))
        web_dir = self.cache_dir
        os.makedirs(web_dir, exist_ok=True)
        copy2(os.path.join(src_dir, 'blank.svg'), os.path.join(web_dir, 'blank.svg'))
        self.copy_index(src_dir, os.path.join(src_dir, 'index.html'), os.path.join(web_dir, 'index.html'))

    def init_tools(self, out_dir):
        self.cache_dir = out_dir
        self.command = self.ensure_tool('KiDiff')
        self.git_command = self.ensure_tool('Git')
        # Only needed for schematic
        self.ensure_tool('KiAuto')

    def collect_hashes(self):
        # Get a list of files for the project
        GS.check_sch()
        sch_files = GS.sch.get_files()
        self.repo_dir = GS.sch_dir
        self.sch_rel_name = self.run_git(['ls-files', '--full-name', GS.sch_file])
        if not self.sch_rel_name:
            raise KiPlotConfigurationError("The schematic must be committed")
        GS.check_pcb()
        self.pcb_rel_name = self.run_git(['ls-files', '--full-name', GS.pcb_file])
        if not self.pcb_rel_name:
            raise KiPlotConfigurationError("The PCB must be committed")
        # Get a list of hashes where we have changes
        self._max_commits = ['-n', str(self.max_commits)] if self.max_commits else []
        cmd = ['log', "--date=format:%Y-%m-%d %H:%M:%S", '--pretty=format:%H | %ad | %an | %s']
        res = self.run_git(cmd + self._max_commits + [self.revision, '--', GS.pcb_file] + sch_files)
        hashes = [r.split(' | ') for r in res.split('\n')]
        sch_dirty = self.git_dirty(GS.sch_file)
        pcb_dirty = self.git_dirty(GS.pcb_file)
        return hashes, sch_dirty, pcb_dirty, sch_files

    def run(self, name):
        self.init_tools(self._parent.output_dir)
        hashes, sch_dirty, pcb_dirty, sch_files = self.collect_hashes()
        # Ensure we have at least 2
        if len(hashes) + (1 if sch_dirty or pcb_dirty else 0) < 2:
            logger.warning(W_NOTHCMP+'Nothing to compare')
            return
        # Get more information about what is changed
        self.get_modified_status(GS.pcb_file, sch_files)
        self.create_layers_incl(self.layers)
        self.solve_layer_colors()
        try:
            git_tmp_wd = None
            try:
                for h in hashes:
                    hash = h[0]
                    dst_dir = os.path.join(self.cache_dir, hash[:7])
                    already_generated = os.path.isdir(dst_dir)
                    if self.keep_generated and already_generated:
                        logger.debug(f'- Images for {hash} already generated')
                        continue
                    if already_generated:
                        rmtree(dst_dir)
                    git_tmp_wd = GS.mkdtemp('kiri-checkout')
                    logger.debug('Checking out '+hash+' to '+git_tmp_wd)
                    self.run_git(['worktree', 'add', '--detach', '--force', git_tmp_wd, hash])
                    try:
                        self.run_git(['submodule', 'update', '--init', '--recursive'], cwd=git_tmp_wd, just_raise=True)
                    except CalledProcessError as e:
                        if b'No url found for submodule' in e.output:
                            # Just an uninitialized submodule, report it and continue, see #888
                            logger.warning(W_BADGITREPO+f"Broken git repo: {e}")
                            msg = try_decode_utf8(e.output, 'output from git command', logger, GS.global_code_page_fallback)
                            logger.warning(W_BADGITREPO+msg)
                        else:
                            raise
                    # Generate SVGs for the schematic
                    name_sch = self.do_cache(self.sch_rel_name, git_tmp_wd, hash)
                    # Generate SVGs for the PCB
                    self.do_cache(self.pcb_rel_name, git_tmp_wd, hash)
                    # List of layers
                    self.save_pcb_layers(hash)
                    # Schematic hierarchy
                    self.save_sch_sheet(hash, name_sch)
                    self.remove_git_worktree(git_tmp_wd)
                    git_tmp_wd = None
            finally:
                if git_tmp_wd:
                    self.remove_git_worktree(git_tmp_wd)
            # Do we have modifications?
            if sch_dirty or pcb_dirty:
                # Include the current files
                dst_dir = os.path.join(self.cache_dir, HASH_LOCAL)
                already_generated = os.path.isdir(dst_dir)
                if self.keep_generated and already_generated:
                    logger.debug(f'- Images for {HASH_LOCAL} already generated')
                else:
                    if already_generated:
                        rmtree(dst_dir)
                    name_sch = self.do_cache(GS.sch_file, GS.sch_dir, HASH_LOCAL)
                    self.save_sch_sheet(HASH_LOCAL, name_sch)
                    self.do_cache(GS.pcb_file, GS.pcb_dir, HASH_LOCAL)
                    self.save_pcb_layers(HASH_LOCAL)
                hashes.insert(0, (HASH_LOCAL, datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S'), get_cur_user(),
                              'Local changes not committed'))
                if pcb_dirty:
                    self.commits_with_changed_pcb.add(HASH_LOCAL)
                if sch_dirty:
                    self.commits_with_changed_sch.add(HASH_LOCAL)
        finally:
            if self.incl_file:
                os.remove(self.incl_file)
        self.create_kiri_files()
        self.save_commits(hashes)
        self.save_project_data()


@output_class
class KiRi(BaseOutput):  # noqa: F821
    """ KiRi
        Generates an interactive web page to browse the schematic and/or PCB differences between git commits.
        Must be applied to a git repository.
        Recursive git submodules aren't supported (submodules inside submodules).
        Note that most browsers won't allow Java Script to read local files,
        needed to load the SCH/PCB. So you must use a web server or enable the
        access to local files. In the case of Google Chrome you can use the
        `--allow-file-access-from-files` command line option.
        This output generates a simple Python web server called `kiri-server` that you can use.
        For more information visit the [KiRi web](https://github.com/leoheck/kiri) """
    def __init__(self):
        super().__init__()
        self._category = ['PCB/docs', 'Schematic/docs']
        self._both_related = True
        with document:
            self.options = KiRiOptions
            """ *[dict={}] Options for the `diff` output """
            self.layers = Layer
            """ *[list(dict)|list(string)|string='all'] [all,selected,copper,technical,user,inners,outers,*] List
                of PCB layers to use. When empty all available layers are used.
                Note that if you want to support adding/removing layers you should specify a list here """

    @staticmethod
    def layer2dict(la):
        return {'layer': la.layer, 'suffix': la.suffix, 'description': la.description}

    @staticmethod
    def get_conf_examples(name, layers):
        outs = []
        git_command = GS.check_tool(name, 'Git')
        if not git_command or not GS.check_tool(name, 'KiDiff'):
            return None
        pcb_commits = has_repo(git_command, GS.pcb_file)
        sch_commits = has_repo(git_command, GS.sch_file)
        if GS.pcb_file and GS.sch_file and pcb_commits and sch_commits and (pcb_commits > 1 or sch_commits > 1):
            ops = KiRiOptions()
            ops.git_command = git_command
            hashes, sch_dirty, pcb_dirty, _ = ops.collect_hashes()
            if sch_dirty or pcb_dirty:
                hashes.append(HASH_LOCAL)
            if len(hashes) < 2:
                return None
            if GS.debug_level > 1:
                logger.debug(f'KiRi get_conf_examples found: {hashes}')
            gb = {}
            gb['name'] = 'basic_{}'.format(name)
            gb['comment'] = 'Interactive diff between commits'
            gb['type'] = name
            gb['dir'] = 'diff'
            gb['layers'] = [KiRi.layer2dict(la) for la in layers]
            # Avoid taking too much time
            gb['options'] = {'max_commits': 4}
            outs.append(gb)
        return outs

    def get_navigate_targets(self, out_dir):
        return (self.options.get_navigate_targets(out_dir),
                [os.path.join(GS.get_resource_path('kiri'), 'images', 'icon.svg')])

    def run(self, name):
        self.options.layers = self.layers
        super().run(name)
