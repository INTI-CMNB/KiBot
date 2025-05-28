# -*- coding: utf-8 -*-
# Copyright (c) 2022-2024 Salvador E. Tropea
# Copyright (c) 2022-2024 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
"""
Dependencies:
  - name: KiCad PCB/SCH Diff
    version: 2.5.3
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
from hashlib import sha1
from itertools import combinations
import os
import re
from shutil import rmtree, copy2
from subprocess import CalledProcessError
from .error import KiPlotConfigurationError
from .gs import GS
from .kiplot import load_any_sch, run_command, config_output, get_output_dir, run_output
from .layer import Layer
from .misc import DIFF_TOO_BIG, FAILED_EXECUTE
from .registrable import RegOutput
from .out_any_diff import AnyDiffOptions, has_repo
from .macros import macros, document, output_class  # noqa: F401
from . import log

logger = log.get_logger()
STASH_MSG = 'KiBot_Changes_Entry'


class DiffOptions(AnyDiffOptions):
    def __init__(self):
        with document:
            self.output = GS.def_global_output
            """ *Filename for the output (%i=diff_pcb/diff_sch, %x=pdf) """
            self.pcb = True
            """ Compare the PCB, otherwise compare the schematic """
            self.old = 'HEAD'
            """ Reference file. When using git use `HEAD` to refer to the last commit.
                Use `HEAD~` to refer the previous to the last commit.
                As `HEAD` is for the whole repo you can use `KIBOT_LAST-n` to make
                reference to the changes in the PCB/SCH. The `n` value is how many
                changes in the history you want to go back. A 0 is the same as `HEAD`,
                a 1 means the last time the PCB/SCH was changed, etc.
                Use `KIBOT_TAG-n` to search for the last tag skipping `n` tags.
                Important: when using the `checkout` GitHub action you just get the
                last commit. To clone the full repo use `fetch-depth: '0'` """
            self.old_type = 'git'
            """ [git,file,output,multivar] How to interpret the `old` name. Use `git` for a git hash, branch, etc.
                Use `file` for a file name. Use `output` to specify the name of a `pcb_variant`/`sch_variant` output.
                Use `multivar` to specify a reference file when `new_type` is also `multivar` """
            self.new = ''
            """ [string|list(string)] The file you want to compare. Leave it blank for the current PCB/SCH.
                A list is accepted only for the `multivar` type. Consult the `old` option for more information """
            self.new_type = 'current'
            """ [git,file,output,multivar,current] How to interpret the `new` name. Use `git` for a git hash, branch, etc.
                Use `current` for the currently loaded PCB/Schematic.
                Use `file` for a file name. Use `output` to specify the name of a `pcb_variant`/`sch_variant` output.
                Use `multivar` to compare a set of variants, in this mode `new` is the list of outputs for the variants.
                This is an extension of the `output` mode.
                If `old` is also `multivar` then it becomes the reference, otherwise we compare using pairs of variants """
            self.cache_dir = ''
            """ Directory to cache the intermediate files. Leave it blank to disable the cache """
            self.diff_mode = 'red_green'
            """ [red_green,stats,2color] In the `red_green` mode added stuff is green and red when removed.
                The `stats` mode is used to measure the amount of difference. In this mode all
                changes are red, but you can abort if the difference is bigger than certain threshold.
                The '2color' mode is like 'red_green', but you can customize the colors """
            self.fuzz = 5
            """ [0,100] Color tolerance (fuzzyness) for the `stats` mode """
            self.threshold = 0
            """ [0,1000000] Error threshold for the `stats` mode, 0 is no error. When specified a
                difference bigger than the indicated value will make the diff fail.
                KiBot will return error level 29 and the diff generation will be aborted """
            self.dpi = 150
            """ [72,600] Resolution (Dots Per Inch) for the diff images.
                Be careful to flush any cached images if you change it.
                Also be careful with the values, images can become huge """
            self.add_link_id = False
            """ When enabled we create a symlink to the output file with a name that contains the
                git hashes involved in the comparison. If you plan to compress the output don't
                forget to disable the `follow_links` option """
            self.copy_instead_of_link = False
            """ Modifies the behavior of `add_link_id` to create a copy of the file instead of a
                symlink. Useful for some Windows setups """
            self.force_checkout = False
            """ When `old_type` and/or `new_type` are `git` KiBot will checkout the indicated point.
                Before doing it KiBot will stash any change. Under some circumstances git could fail
                to do a checkout, even after stashing, this option can workaround the problem.
                Note that using it you could potentially lose modified files. For more information
                read https://stackoverflow.com/questions/1248029/git-pull-error-entry-foo-not-uptodate-cannot-merge """
            self.use_file_id = False
            """ When creating the link name of an output file related to a variant use the variant
                `file_id` instead of its name """
            self.only_different = False
            """ Only include the pages with differences in the output PDF.
                Note that when no differences are found we get a page saying *No diff* """
            self.only_first_sch_page = False
            """ Compare only the main schematic page (root page).
                Warning: Make sure this page is the page **1** of your schematic """
            self.always_fail_if_missing = False
            """ Always fail if the old/new file doesn't exist. Currently we don't fail if they are from a repo.
                So if you refer to a repo point where the file wasn't created KiBot will use an empty file.
                Enabling this option KiBot will report an error """
            self.color_added = '#00FF00'
            """ Color used for the added stuff in the '2color' mode """
            self.color_removed = '#FF0000'
            """ Color used for the removed stuff in the '2color' mode """
        super().__init__()
        self.add_to_doc("zones", "Be careful with the cache when changing this setting")

    def config(self, parent):
        super().config(parent)
        self._expand_id = 'diff'+('_pcb' if self.pcb else '_sch')
        if self.new_type == 'multivar':
            if len(self.new) < 2:
                raise KiPlotConfigurationError('`new` must contain at least two variants when using the `multivar` type')
        else:
            if len(self.new) > 1:
                raise KiPlotConfigurationError('`new` must be a single string for `{}` type'.format(self.new_type))
            self.new = self.new[0] if len(self.new) else ''
        if self.old_type == 'multivar' and self.new_type != 'multivar':
            raise KiPlotConfigurationError("`old_type` can't be `multivar` when `new_type` isn't (`{}`)".format(self.new_type))
        self.validate_colors(['color_added', 'color_removed'])

    def get_targets(self, out_dir):
        return [self._parent.expand_filename(out_dir, self.output)]

    def get_digest(self, file_path, restart=True):
        logger.debug('Hashing '+file_path)
        if restart:
            self.h = sha1()
        with open(file_path, 'rb') as file:
            while True:
                chunk = file.read(self.h.block_size)
                if not chunk:
                    break
                self.h.update(chunk)
        return self.h.hexdigest()

    def cache_pcb(self, name, force_exist):
        if name:
            if not os.path.isfile(name) and not force_exist:
                raise KiPlotConfigurationError('Missing file to compare: `{}`'.format(name))
        else:
            GS.check_pcb()
            name = GS.pcb_file
        if not os.path.isfile(name):
            if self.always_fail_if_missing:
                raise KiPlotConfigurationError('Missing file to compare: `{}`'.format(name))
            name, to_remove = self.write_empty_file(name, create_tmp=True)
            self._to_remove.extend(to_remove)
        hash = self.get_digest(name)
        self.add_to_cache(name, hash)
        return hash

    def cache_sch(self, name, force_exist):
        if name:
            if not os.path.isfile(name) and not force_exist:
                raise KiPlotConfigurationError('Missing file to compare: `{}`'.format(name))
        else:
            GS.check_sch()
            name = GS.sch_file
        if not os.path.isfile(name):
            if self.always_fail_if_missing:
                raise KiPlotConfigurationError('Missing file to compare: `{}`'.format(name))
            name, to_remove = self.write_empty_file(name, create_tmp=True)
            self._to_remove.extend(to_remove)
        # Schematics can have sub-sheets
        sch = load_any_sch(name, os.path.splitext(os.path.basename(name))[0])
        files = sch.get_files()
        hash = self.get_digest(files[0])
        if len(files) > 1:
            for f in files[1:]:
                hash = self.get_digest(f, restart=False)
        hash = 'sch'+hash
        self.add_to_cache(name, hash)
        return hash

    def cache_file(self, name=None, force_exist=False):
        self.git_hash = 'Current' if not name else 'FILE'
        return self.cache_pcb(name, force_exist) if self.pcb else self.cache_sch(name, force_exist)

    def stash_pop(self, cwd=None):
        # We don't know if we stashed anything (push always returns 0)
        # So we check that the last stash contains our message
        res = self.run_git(['stash', 'list', 'stash@{0}'], cwd)
        if STASH_MSG in res:
            self.run_git(['stash', 'pop', '--index'], cwd)

    def git_submodules(self):
        res = self.run_git(['submodule'])
        reg = re.compile(r'^\s*([\da-z]+)\s+(\S+)\s+')
        subs = []
        for ln in res.split('\n'):
            rm = reg.search(ln)
            if rm:
                subm = os.path.join(self.repo_dir, rm.group(2))
                subs.append(subm)
                if not os.path.isdir(subm):
                    KiPlotConfigurationError('Missing git submodule `{}`'.format(subm))
        logger.debug('Git submodules '+str(subs))
        return subs

    def undo_git_use_stash(self):
        if self.checkedout:
            logger.debug('Restoring point '+self.branch)
            self.run_git(['checkout', '--force', '--recurse-submodules', self.branch])
        if self.stashed:
            logger.debug('Restoring changes')
            self.stash_pop()
            # Do the same for each submodule
            for sub in self.git_submodules():
                self.stash_pop(sub)

    def process_tags(self, num):
        # Get a list of all tags ... and commits (how can I filter it?)
        logger.debug('Looking for git tags')
        res = self.run_git(['rev-list', '--format=format:%D', 'HEAD'])
        if not res:
            return res
        res = res.split('\n')
        commit = ''
        skipped = 0
        for v in res:
            try:
                tag = v[v.index('tag: '):].split(',')[0][4:]
                logger.debugl(2, '- {}/{} tag: {} -> {}'.format(skipped, num, tag, commit))
                if skipped == num:
                    return commit
                skipped += 1
            except ValueError:
                if v.startswith('commit '):
                    commit = v[7:]

    def solve_kibot_magic(self, name, tag):
        # The magic KIBOT_*
        ori = name
        malformed = 'Malformed `{0}` value, must be `{0}-n`, not: {1}'.format(tag, ori)
        name = name[len(tag):]
        # How many changes?
        num = 0
        if len(name):
            if name[0] != '-':
                raise KiPlotConfigurationError(malformed)
            try:
                num = int(name[1:])
            except ValueError:
                raise KiPlotConfigurationError(malformed)
        # Return its hash
        if tag == 'KIBOT_LAST':
            res = self.run_git(['log', '--pretty=format:%H', '--skip='+str(num), '-n', '1', '--', self.file])
        else:  # KIBOT_TAG
            res = self.process_tags(num)
        if not res:
            raise KiPlotConfigurationError("The `{}` doesn't resolve to a valid hash".format(ori))
        logger.debug('- '+res)
        return res

    def solve_git_name(self, name):
        logger.debug('Finding '+name)
        if name.startswith('KIBOT_LAST'):
            return self.solve_kibot_magic(name, 'KIBOT_LAST')
        if name.startswith('KIBOT_TAG'):
            return self.solve_kibot_magic(name, 'KIBOT_TAG')
        return name

    def get_git_point_desc(self, user_name, cwd=None):
        # Are we at a tagged point?
        name = None
        try:
            name = self.run_git(['describe', '--exact-match', '--tags', 'HEAD'], cwd=cwd, just_raise=True)
            if user_name == 'Dirty':
                name += '-dirty'
        except CalledProcessError:
            logger.debug("Not at a tag point")
        if name is None:
            # Are we at the HEAD of a branch?
            branch = self.run_git(['rev-parse', '--abbrev-ref', 'HEAD'], cwd=cwd)
            if branch == 'HEAD':
                # Detached state
                # Try to find the name relative to a tag
                try:
                    name = self.run_git(['describe', '--tags', '--dirty'], cwd=cwd, just_raise=True)
                except CalledProcessError:
                    logger.debug("Can't find a tag name")
                if not name:
                    # Nothing usable, use what the user specified
                    name = user_name
            else:
                # We are at the HEAD of a branch
                name = branch
                # Do we have a tag in this branch
                extra = None
                try:
                    extra = self.run_git(['describe', '--tags', '--abbrev=0', '--dirty'], cwd=cwd, just_raise=True)
                except CalledProcessError:
                    logger.debug("Can't find a tag name")
                if extra:
                    name += '['+extra+']'
                elif user_name == 'Dirty':
                    name += '-dirty'
        return '{}({})'.format(self.run_git(['rev-parse', '--short', 'HEAD'], cwd=cwd), name)

    def cache_git_use_stash(self, name):
        self.stashed = False
        self.checkedout = False
        # Which file
        if self.pcb:
            GS.check_pcb()
            self.file = GS.pcb_file
        else:
            GS.check_sch()
            self.file = GS.sch_file
        # Place where we know we have a repo
        self.repo_dir = os.path.dirname(os.path.abspath(self.file))
        try:
            if name:
                # Save current changes
                logger.debug('Saving current changes')
                self.run_git(['stash', 'push', '-m', STASH_MSG])
                self.stashed = True
                #  Also save the submodules
                self.run_git(['submodule', 'foreach', 'git stash push -m '+STASH_MSG])
                # Find the current branch
                self.branch = self.run_git(['rev-parse', '--abbrev-ref', 'HEAD'])
                if self.branch == 'HEAD':
                    # Detached
                    self.branch = self.run_git(['rev-parse', 'HEAD'])
                logger.debug('Current branch is '+self.branch)
                # Checkout the target
                name_ori = name
                name = self.solve_git_name(name)
                logger.debug('Changing to '+name)
                ops = ['checkout']
                if self.force_checkout:
                    ops.append('--force')
                self.run_git(ops+['--recurse-submodules', name])
                self.checkedout = True
            else:
                name_ori = 'Dirty' if self.git_dirty() else 'HEAD'
            # Populate the cache
            hash = self.cache_file()
            # A short version of the current hash
            self.git_hash = self.get_git_point_desc(name_ori)
        finally:
            self.undo_git_use_stash()
        return hash

    def cache_git(self, name):
        self.stashed = False
        self.checkedout = False
        # Which file
        if self.pcb:
            GS.check_pcb()
            self.file = GS.pcb_file
        else:
            GS.check_sch()
            self.file = GS.sch_file
        # Place where we know we have a repo
        self.repo_dir = os.path.dirname(os.path.abspath(self.file))
        if name:
            # Checkout the target
            name_ori = name
            name = self.solve_git_name(name)
            git_tmp_wd = GS.mkdtemp('diff-checkout')
            logger.debug('Checking out '+name+' to '+git_tmp_wd)
            self.run_git(['worktree', 'add', '--detach', '--force', git_tmp_wd, name])
            self._worktrees_to_remove.append(git_tmp_wd)
            self.run_git(['submodule', 'update', '--init', '--recursive'], cwd=git_tmp_wd)
            name_copy = self.run_git(['ls-files', '--full-name', self.file])
            name_copy = os.path.join(git_tmp_wd, name_copy)
            logger.debug('- Using temporal copy: '+name_copy)
            hash = self.cache_file(name_copy, force_exist=True)
            cwd = git_tmp_wd
        else:
            name_ori = 'Dirty' if self.git_dirty() else 'HEAD'
            # Populate the cache
            hash = self.cache_file()
            cwd = self.repo_dir
        # A short version of the current hash
        self.git_hash = self.get_git_point_desc(name_ori, cwd)
        return hash

    @staticmethod
    def check_output_type(out, must_be):
        if out.type != must_be:
            raise KiPlotConfigurationError('Output `{}` must be `{}` type, not `{}`'.format(out.name, must_be, out.type))

    def cache_output(self, name):
        logger.debugl(2, 'From output `{}`'.format(name))
        out = RegOutput.get_output(name)
        if out is None:
            raise KiPlotConfigurationError('Unknown output `{}`'.format(name))
        self.check_output_type(out, 'pcb_variant' if self.pcb else 'sch_variant')
        config_output(out)
        out_dir = get_output_dir(out.dir, out, dry=True)
        if self.pcb:
            fname = out.get_targets(out_dir)[0]
        else:
            fname = out.get_output_sch_name(out_dir)
        logger.debug('File from output {} is {}'.format(name, fname))
        if not out._done:
            run_output(out)
        res = self.cache_file(fname)
        variant = out.options.variant
        if variant is None:
            self.git_hash = 'no_variant'
        else:
            self.git_hash = variant.file_id if self.use_file_id else variant.name+'_variant'
        return res

    def cache_current(self):
        """ The file as we interpreted it """
        if self.pcb:
            fname, dir_name = self.save_tmp_dir_board('diff')
            self.dirs_to_remove.append(dir_name)
        else:
            if self._comps:
                # We have a variant/filter applied
                dir_name = GS.mkdtemp('diff-variant')
                fname = GS.sch.save_variant(dir_name)
                GS.copy_project_sch(dir_name)
                self.dirs_to_remove.append(dir_name)
            else:
                # Just use the current file
                # Note: The KiCad 7 DNP field needs some filter to be honored
                dir_name = GS.sch_dir
                fname = os.path.basename(GS.sch_file)
        res = self.cache_file(os.path.join(dir_name, fname))
        self.git_hash = 'Current'
        return res

    def cache_obj(self, name, type):
        if type == 'git':
            return self.cache_git(name) if GS.global_git_diff_strategy == 'worktree' else self.cache_git_use_stash(name)
        if type == 'file':
            return self.cache_file(name)
        if type == 'current':
            return self.cache_current()
        return self.cache_output(name)

    def create_layers_incl(self, layers):
        return self.save_layers_incl(Layer.solve(layers)) if self.pcb else None

    def do_compare(self, old, old_type, new, new_type, name, name_ori):
        dir_name = os.path.dirname(name)
        file_name = os.path.basename(name)
        # Populate the cache
        old_hash = self.cache_obj(old, old_type)
        gh1 = self.git_hash
        name_used_for_old = self.name_used_for_cache
        new_hash = self.cache_obj(new, new_type)
        gh2 = self.git_hash
        name_used_for_new = self.name_used_for_cache
        # Compute the diff using the cache
        cmd = [self.command, '--no_reader', '--new_file_hash', new_hash, '--old_file_hash', old_hash,
               '--cache_dir', self.cache_dir, '--output_dir', dir_name, '--output_name', file_name,
               '--diff_mode', self.diff_mode, '--fuzz', str(self.fuzz), '--no_exist_check',
               '--added_2color', self.color_added, '--removed_2color', self.color_removed,
               '--resolution', str(self.dpi)]
        self.add_zones_ops(cmd)
        if self.incl_file:
            cmd.extend(['--layers', self.incl_file])
        if self.threshold:
            cmd.extend(['--threshold', str(self.threshold)])
        if self.only_different:
            cmd.append('--only_different')
        if not self.only_first_sch_page:
            cmd.append('--all_pages')
        cmd.extend([name_used_for_old, name_used_for_new])
        if GS.debug_enabled:
            cmd.insert(1, '-'+'v'*GS.debug_level)
        try:
            run_command(cmd, just_raise=True)
        except CalledProcessError as e:
            if e.returncode == 10:
                GS.exit_with_error('Diff above the threshold', DIFF_TOO_BIG)
            GS.exit_with_error(None, FAILED_EXECUTE, e)
        if self.add_link_id:
            name_comps = os.path.splitext(name_ori)
            extra = '_'+gh1+'-'+gh2
            # Replace things like "origin/main" by "origin_main"
            extra = extra.replace('/', '_')
            target = name_comps[0]+extra+name_comps[1]
            if self.copy_instead_of_link:
                copy2(name, target)
            else:
                if os.path.isfile(target):
                    os.remove(target)
                os.symlink(os.path.basename(name), target)

    def run(self, name):
        self.command = self.ensure_tool('KiDiff')
        self._to_remove = []
        self._worktrees_to_remove = []
        if self.old_type == 'git' or self.new_type == 'git':
            self.git_command = self.ensure_tool('Git')
        if not self.pcb:
            # We need eeschema_do for this
            self.ensure_tool('KiAuto')
        # Solve the cache dir
        self.dirs_to_remove = []
        if not self.cache_dir:
            self.cache_dir = GS.mkdtemp('diff-cache')
            self.dirs_to_remove.append(self.cache_dir)
        self.incl_file = None
        name_ori = name
        try:
            # List of layers
            self.incl_file = self.create_layers_incl(self.layers)
            if self.new_type == 'multivar' and self.old_type != 'multivar':
                # Special case, we generate various files
                base_id = self._expand_id
                for pair in combinations(self.new, 2):
                    logger.debug('Using variants '+str(pair))
                    logger.info(' - {} vs {}'.format(pair[0], pair[1]))
                    self._expand_id = '{}_variants_{}_VS_{}'.format(base_id, pair[0], pair[1])
                    name = self._parent.expand_filename(self._parent.output_dir, self.output)
                    self.do_compare(pair[0], 'output', pair[1], 'output', name, name_ori)
                self._expand_id = base_id
            elif self.new_type == 'multivar' and self.old_type == 'multivar':
                # Special case, we generate various files
                base_id = self._expand_id
                for new_variant in self.new:
                    ref_name = self.old if self.old else 'current'
                    logger.info(' - {} vs {}'.format(ref_name, new_variant))
                    self._expand_id = '{}_variant_{}'.format(base_id, new_variant)
                    name = self._parent.expand_filename(self._parent.output_dir, self.output)
                    self.do_compare(self.old, 'file', new_variant, 'output', name, name_ori)
                self._expand_id = base_id
            else:
                self.do_compare(self.old, self.old_type, self.new, self.new_type, name, name_ori)
        finally:
            # Clean-up
            for d in self.dirs_to_remove:
                rmtree(d)
            if self.incl_file:
                os.remove(self.incl_file)
            for f in self._to_remove:
                os.remove(f)
            # Remove any git worktree that we created
            for w in self._worktrees_to_remove:
                self.remove_git_worktree(w)


@output_class
class Diff(BaseOutput):  # noqa: F821
    """ Diff
        Generates a PDF with the differences between two PCBs or schematics.
        Recursive git submodules aren't supported (submodules inside submodules) """
    def __init__(self):
        super().__init__()
        self._category = ['PCB/docs', 'Schematic/docs']
        self._any_related = True
        with document:
            self.options = DiffOptions
            """ *[dict={}] Options for the `diff` output """
            self.layers = Layer
            """ *[list(dict)|list(string)|string='all'] [all,selected,copper,technical,user,inners,outers,*] List
                of PCB layers to use. When empty all available layers are used.
                If the list is empty all layers will be included.
                Note that if you want to support adding/removing layers you should specify a list here """

    def config(self, parent):
        super().config(parent)
        if self.get_user_defined('category'):
            # The user specified a category, don't change it
            return
        # Adjust the category according to the selected output/s
        self.category = ['PCB/docs' if self.options.pcb else 'Schematic/docs']

    @staticmethod
    def layer2dict(la):
        return {'layer': la.layer, 'suffix': la.suffix, 'description': la.description}

    @staticmethod
    def get_conf_examples(name, layers):
        outs = []
        git_command = GS.check_tool(name, 'Git')
        if GS.pcb_file and has_repo(git_command, GS.pcb_file) > 1:
            gb = {}
            gb['name'] = 'basic_{}_pcb'.format(name)
            gb['comment'] = 'PCB diff between the last two changes'
            gb['type'] = name
            gb['dir'] = 'diff'
            gb['layers'] = [Diff.layer2dict(la) for la in layers]
            gb['options'] = {'old': 'KIBOT_LAST-1', 'old_type': 'git', 'new': 'HEAD', 'new_type': 'git',
                             'cache_dir': os.path.abspath('.cache'), 'add_link_id': True}
            outs.append(gb)
        if GS.sch_file and has_repo(git_command, GS.sch_file) > 1:
            gb = {}
            gb['name'] = 'basic_{}_sch'.format(name)
            gb['comment'] = 'Schematic diff between the last two changes'
            gb['type'] = name
            gb['dir'] = 'diff'
            gb['options'] = {'old': 'KIBOT_LAST-1', 'old_type': 'git', 'new': 'HEAD', 'new_type': 'git',
                             'cache_dir': os.path.abspath('.cache'), 'add_link_id': True, 'pcb': False}
            outs.append(gb)
        return outs

    def run(self, name):
        self.options.layers = self.layers
        super().run(name)
