# -*- coding: utf-8 -*-
# Copyright (c) 2020-2025 Salvador E. Tropea
# Copyright (c) 2020-2025 Instituto Nacional de Tecnología Industrial
# Copyright (c) 2018 John Beard
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)
# Adapted from: https://github.com/johnbeard/kiplot
"""
Main KiBot code
"""
from copy import deepcopy
from collections import OrderedDict
import gzip
import os
import re
from sys import path as sys_path
from shutil import which, copy2
from subprocess import run, PIPE, STDOUT, Popen, CalledProcessError
from glob import glob
from importlib.util import spec_from_file_location, module_from_spec

from .bom.columnlist import ColumnList
from .gs import GS
from .registrable import RegOutput
from .misc import (PLOT_ERROR, CORRUPTED_PCB, EXIT_BAD_ARGS, CORRUPTED_SCH, version_str2tuple,
                   EXIT_BAD_CONFIG, WRONG_INSTALL, UI_SMD, UI_VIRTUAL, TRY_INSTALL_CHECK, MOD_SMD, MOD_THROUGH_HOLE,
                   MOD_VIRTUAL, W_PCBNOSCH, W_NONEEDSKIP, W_WRONGCHAR, name2make, W_TIMEOUT, W_KIAUTO, W_VARSCH,
                   NO_SCH_FILE, NO_PCB_FILE, W_VARPCB, NO_YAML_MODULE, WRONG_ARGUMENTS, FAILED_EXECUTE, W_VALMISMATCH,
                   MOD_EXCLUDE_FROM_POS_FILES, MOD_EXCLUDE_FROM_BOM, MOD_BOARD_ONLY, hide_stderr, W_MAXDEPTH, DONT_STOP,
                   W_BADREF, try_decode_utf8, MISSING_FILES, KICAD_VERSION_9_0_1)
from .error import PlotError, KiPlotConfigurationError, config_error, KiPlotError
from .config_reader import CfgYamlReader
from .pre_base import BasePreFlight
from .dep_downloader import register_deps
import kibot.dep_downloader as dep_downloader
from .kicad.v5_sch import Schematic, SchFileError, SchError, SchematicField
from .kicad.v6_sch import SchematicV6, SchematicComponentV6
from .kicad.config import KiConfError, KiConf, expand_env
from . import log
INTERNAL_FIELDS = {'reference', 'value', 'footprint', 'datasheet', 'description'}

logger = log.get_logger()
# Cache to avoid running external many times to check their versions
script_versions = {}
actions_loaded = False
needed_imports = {}

try:
    import yaml
except ImportError:
    log.init()
    GS.exit_with_error(['No yaml module for Python, install python3-yaml', TRY_INSTALL_CHECK], NO_YAML_MODULE)


def cased_path(path):
    r = glob(re.sub(r'([^:/\\])(?=[/\\]|$)|\[', r'[\g<0>]', path))
    return r and r[0] or path


def try_register_deps(mod, name):
    if mod.__doc__:
        try:
            data = yaml.safe_load(mod.__doc__)
        except yaml.YAMLError as e:
            config_error([f'While loading plug-in `{name}`:', "Error loading YAML "+str(e)])
        register_deps(name, data)


def _import(name, path):
    # Python 3.4+ import mechanism
    spec = spec_from_file_location("kibot."+name, path)
    mod = module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except ImportError as e:
        GS.exit_with_error(('Unable to import plug-ins: '+str(e),
                            'Make sure you used `--no-compile` if you used pip for installation',
                            'Python path: '+str(sys_path)), WRONG_INSTALL)
    try_register_deps(mod, name)


def _load_actions(path, load_internals=False, progress=None):
    logger.debug("Importing from "+path)
    lst = glob(os.path.join(path, 'out_*.py')) + glob(os.path.join(path, 'pre_*.py'))
    lst += glob(os.path.join(path, 'var_*.py')) + glob(os.path.join(path, 'fil_*.py'))
    if load_internals:
        lst += [os.path.join(path, 'globals.py')]
    for p in sorted(lst):
        name = os.path.splitext(os.path.basename(p))[0]
        msg = "Importing "+name
        logger.debug('- '+msg)
        if progress:
            progress(msg)
        _import(name, p)


def load_actions(progress=None):
    """ Load all the available outputs and preflights """
    global actions_loaded
    if actions_loaded:
        return
    actions_loaded = True
    try_register_deps(dep_downloader, 'global')
    from kibot.mcpyrate import activate
    # activate.activate()
    _load_actions(os.path.abspath(os.path.dirname(__file__)), True, progress)
    home = os.environ.get('HOME')
    if home:
        dir = os.path.join(home, '.config', 'kiplot', 'plugins')
        if os.path.isdir(dir):
            _load_actions(dir)
        dir = os.path.join(home, '.config', 'kibot', 'plugins')
        if os.path.isdir(dir):
            _load_actions(dir)
    # de_activate in old mcpy
    if 'deactivate' in activate.__dict__:
        logger.debug('Deactivating macros')
        activate.deactivate()


def extract_errors(text):
    in_error = in_warning = False
    msg = ''
    for line in text.split('\n'):
        line += '\n'
        if line[0] == ' ' and (in_error or in_warning):
            msg += line
        else:
            if in_error:
                in_error = False
                logger.error(msg.rstrip())
            elif in_warning:
                in_warning = False
                logger.warning(W_KIAUTO+msg.rstrip())
        if line.startswith('ERROR:'):
            in_error = True
            msg = line[6:]
        elif line.startswith('WARNING:'):
            in_warning = True
            msg = line[8:]
    if in_error:
        in_error = False
        logger.error(msg.rstrip())
    elif in_warning:
        in_warning = False
        logger.warning(W_KIAUTO+msg.rstrip())


def debug_output(res):
    if res:
        logger.debug('- Output from command: '+res)


def _run_command(command, change_to):
    return run(command, check=True, stdout=PIPE, stderr=STDOUT, cwd=change_to)


def run_command(command, change_to=None, just_raise=False, use_x11=False, err_msg=None, err_lvl=FAILED_EXECUTE):
    logger.debug('- Executing: '+GS.pasteable_cmd(command))
    if change_to is not None:
        logger.debug('- CWD: '+change_to)
    try:
        if use_x11 and not GS.on_windows:
            logger.debug('Using Xvfb to run the command')
            from xvfbwrapper import Xvfb
            with Xvfb(width=640, height=480, colordepth=24):
                res = _run_command(command, change_to)
        else:
            res = _run_command(command, change_to)
    except CalledProcessError as e:
        if just_raise:
            raise
        if err_msg is not None:
            err_msg = err_msg.format(ret=e.returncode)
        GS.exit_with_error(err_msg, err_lvl, e)
    msg = try_decode_utf8(res.stdout, 'output from command', logger)
    debug_output(msg)
    return msg.rstrip()


def exec_with_retry(cmd, exit_with=None):
    cmd_str = GS.pasteable_cmd(cmd)
    logger.debug('Executing: '+cmd_str)
    if GS.debug_level > 2:
        logger.debug('Command line: '+str(cmd))
    retry = 2
    while retry:
        result = run(cmd, stdout=PIPE, stderr=PIPE, universal_newlines=True)
        ret = result.returncode
        retry -= 1
        if ret != 16 and (ret > 0 and ret < 128 and retry):
            # 16 is KiCad crash
            logger.debug('Failed with error {}, retrying ...'.format(ret))
        else:
            extract_errors(result.stderr)
            err = '> '+result.stderr.replace('\n', '\n> ')
            logger.debug('Output from command:\n'+err)
            if 'Timed out' in err:
                logger.warning(W_TIMEOUT+'Time out detected, on slow machines or complex projects try:')
                logger.warning(W_TIMEOUT+'`kiauto_time_out_scale` and/or `kiauto_wait_start` global options')
            if exit_with is not None and ret:
                GS.exit_with_error(cmd[0]+' returned '+str(ret), exit_with)
            return ret


def load_board(pcb_file=None, forced=False):
    if GS.board is not None and not forced:
        # Already loaded
        return GS.board
    import pcbnew
    if not pcb_file:
        GS.check_pcb()
        pcb_file = GS.pcb_file
    try:
        with hide_stderr():
            board = pcbnew.LoadBoard(pcb_file)
        if board is None:
            # KiCad 9 doesn't stop and returns None
            raise OSError
        if GS.global_work_layer and board.GetLayerID(GS.global_work_layer) < 0:
            raise KiPlotConfigurationError(f"Unknown layer used for the global `work_layer` option"
                                           f" (`{GS.global_work_layer}`)")

        if GS.global_invalidate_pcb_text_cache == 'yes' and GS.ki6:
            # Workaround for unexpected KiCad behavior:
            # https://gitlab.com/kicad/code/kicad/-/issues/14360
            logger.debug('Current PCB text variables cache: {}'.format(board.GetProperties().items()))
            logger.debug('Removing cached text variables')
            board.SetProperties(pcbnew.MAP_STRING_STRING())
            # Save the PCB, so external tools also gets the reset, i.e. panelize, see #652
            GS.save_pcb(pcb_file, board)
        if BasePreFlight.get_option('check_zone_fills'):
            GS.fill_zones(board)
        if GS.global_units and GS.ki6:
            # In KiCad 6 "dimensions" has units.
            # The default value is DIM_UNITS_MODE_AUTOMATIC.
            # But this has a meaning only in the GUI where you have default units.
            # So now we have global.units and here we patch the board.
            if GS.kicad_version_n < KICAD_VERSION_9_0_1:
                UNIT_NAME_TO_INDEX = {'millimeters': pcbnew.DIM_UNITS_MODE_MILLIMETRES,
                                      'inches': pcbnew.DIM_UNITS_MODE_INCHES,
                                      'mils': pcbnew.DIM_UNITS_MODE_MILS}
            else:
                UNIT_NAME_TO_INDEX = {'millimeters': pcbnew.DIM_UNITS_MODE_MM,
                                      'inches': pcbnew.DIM_UNITS_MODE_INCH,
                                      'mils': pcbnew.DIM_UNITS_MODE_MILS}
            forced_units = UNIT_NAME_TO_INDEX[GS.global_units]
            for dr in board.GetDrawings():
                if dr.GetClass().startswith('PCB_DIM_') and dr.GetUnitsMode() == pcbnew.DIM_UNITS_MODE_AUTOMATIC:
                    dr.SetUnitsMode(forced_units)
                    dr.Update()
        if GS.ki8 and not GS.ki9:
            # KiCad 8.0.2 crazyness: hidden text affects scaling, even when not plotted
            # So a PRL can affect the plot mechanism
            # https://gitlab.com/kicad/code/kicad/-/issues/17958
            # https://gitlab.com/kicad/code/kicad/-/commit/8184ed64e732ed0812831a13ebc04bd12e8d1d19
            board.SetElementVisibility(pcbnew.LAYER_HIDDEN_TEXT, False)
        GS.board = board
    except OSError as e:
        GS.exit_with_error(['Error loading PCB file. Corrupted?', str(e)], CORRUPTED_PCB)
    assert board is not None
    logger.debug("Board loaded")
    return board


def ki_conf_error(e):
    GS.exit_with_error(('At line {} of `{}`: {}'.format(e.line, e.file, e.msg),
                        'Line content: `{}`'.format(e.code.rstrip())), EXIT_BAD_CONFIG)


def load_any_sch(file, project, fatal=True, extra_msg=None):
    if file[-9:] == 'kicad_sch':
        sch = SchematicV6()
        load_libs = False
    else:
        sch = Schematic()
        load_libs = True
    try:
        sch.load(file, project)
        if load_libs:
            sch.load_libs(file)
        if GS.debug_level > 1:
            logger.debug('Schematic dependencies: '+str(sch.get_files()))
    except SchFileError as e:
        if extra_msg is not None:
            logger.error(extra_msg)
        GS.exit_with_error(('At line {} of `{}`: {}'.format(e.line, e.file, e.msg),
                            'Line content: `{}`'.format(e.code)), CORRUPTED_SCH if fatal else DONT_STOP)
    except SchError as e:
        if extra_msg is not None:
            logger.error(extra_msg)
        GS.exit_with_error(('While loading `{}`'.format(file), str(e)), CORRUPTED_SCH if fatal else DONT_STOP)
    except KiConfError as e:
        ki_conf_error(e)
    return sch


def load_sch(sch_file=None, forced=False):
    if GS.sch is not None and not forced:  # Already loaded
        return
    if not sch_file:
        GS.check_sch()
        sch_file = GS.sch_file
    GS.sch = load_any_sch(sch_file, os.path.splitext(os.path.basename(sch_file))[0])


def create_component_from_footprint(m, ref, env):
    c = SchematicComponentV6()
    c.f_ref = c.ref = ref
    c.name = m.GetValue()
    c.sheet_path_h = c.sheet_path = c.lib = ''
    c.project = GS.sch_basename
    c.id = m.m_Uuid.AsString() if hasattr(m, 'm_Uuid') else ''
    # Basic fields
    # Reference
    f = SchematicField()
    f.name = 'Reference'
    f.value = ref
    f.number = 0
    c.add_field(f)
    # Value
    f = SchematicField()
    f.name = 'Value'
    f.value = c.name
    f.number = 1
    c.add_field(f)
    # Footprint
    f = SchematicField()
    f.name = 'Footprint'
    lib = m.GetFPID()
    f.value = lib.GetUniStringLibId()
    f.number = 2
    c.add_field(f)
    # Datasheet
    f = SchematicField()
    f.name = 'Datasheet'
    f.value = '~'
    f.number = 3
    c.add_field(f)
    # Other fields
    copy_fields(c, m, env)
    c._solve_fields(None)
    try:
        c.split_ref()
    except SchError:
        # Unusable ref, discard it
        logger.warning(f'{W_BADREF}Not including component `{ref}` in filters because it has a malformed reference '
                       f'@ PCB {GS.module_position(m)}')
        c = None
    return c


class PadProperty(object):
    pass


def expand_footprint_fields(fields, env):
    extra_env = {k.upper() if k.lower() in INTERNAL_FIELDS else k: v for k, v in fields.items()}
    new_fields = {}
    for k, v in fields.items():
        new_value = v
        depth = 1
        used_extra = [False]
        while depth < GS.MAXDEPTH:
            new_value = expand_env(new_value, env, extra_env, used_extra=used_extra)
            if not used_extra[0]:
                break
            depth += 1
            if depth == GS.MAXDEPTH:
                logger.warning(W_MAXDEPTH+'Too much nested variables replacements, possible loop ({})'.format(v))
        # Remove extra spaces as we did with the schematic values
        new_fields[k] = new_value.strip()
    return new_fields


def copy_fields(c, m, env):
    real_fields = GS.get_fields(m)
    expanded_fields = expand_footprint_fields(real_fields, env)
    for name, value in real_fields.items():
        if c.is_field(name.lower()):
            # Already there
            old = c.get_field_value(name)
            if value and old != value and old != expanded_fields[name]:
                logger.warning(f"{W_VALMISMATCH}{name} field mismatch for `{c.ref}` (SCH: `{old}` PCB: `{value}`)")
                c.set_field(name, value)
        else:
            # New one
            logger.debug(f'Adding {name} field to {c.ref} ({value})')
            c.set_field(name, value)


def get_all_components(collapse=True):
    load_sch()
    comps = GS.sch.get_components(collapse=collapse)
    get_board_comps_data(comps)
    return comps


def get_board_comps_data(comps):
    """ Add information from the PCB to the list of components from the schematic.
        Note that we do it every time the function is called to reset transformation filters like rot_footprint. """
    if not GS.pcb_file:
        return
    load_board()
    comps_hash = {c.ref: c for c in comps}
    # Get the KiCad variables for fields
    KiConf.init(GS.sch_file)
    env = KiConf.kicad_env
    env.update(GS.load_pro_variables())
    for m in GS.get_modules():
        ref = m.GetReference()
        attrs = m.GetAttributes()
        c = comps_hash.get(ref)
        if c is None:
            if not (attrs & MOD_BOARD_ONLY) and not ref.startswith('KiKit_'):
                logger.warning(W_PCBNOSCH+f'`{ref}` component in board, but not in schematic')
            if not GS.global_include_components_from_pcb:
                # v1.6.3 behavior
                continue
            # Create a component for this so we can include/exclude it using filters
            c = create_component_from_footprint(m, ref, env)
            if c is None:
                continue
            comps.append(c)
        if c.has_pcb_info:
            # We already got this reference and filled the PCB info, this is another copy
            c = deepcopy(c)
            comps.append(c)
        new_value = m.GetValue()
        if new_value != c.value and '${' not in c.value:
            logger.warning(f"{W_VALMISMATCH}Value field mismatch for `{ref}` (SCH: `{c.value}` PCB: `{new_value}`)")
        c.value = new_value
        c.bottom = m.IsFlipped()
        c.footprint_rot = m.GetOrientationDegrees()
        center = GS.get_center(m)
        c.footprint_x = center.x
        c.footprint_y = center.y
        (c.footprint_w, c.footprint_h) = GS.get_fp_size(m)
        c.has_pcb_info = True
        c.pad_properties = {}
        if GS.global_use_pcb_fields:
            copy_fields(c, m, env)
        # Net
        net_name = set()
        net_class = set()
        for pad in m.Pads():
            net_name.add(pad.GetNetname())
            net_class.add(pad.GetNetClassName())
        c.net_name = ','.join(net_name)
        c.net_class = ','.join(net_class)
        if GS.ki5:
            # KiCad 5
            if attrs == UI_SMD:
                c.smd = True
            elif attrs == UI_VIRTUAL:
                c.virtual = True
            else:
                c.tht = True
        else:
            # KiCad 6
            if attrs & MOD_SMD:
                c.smd = True
            if attrs & MOD_THROUGH_HOLE:
                c.tht = True
            if attrs & MOD_VIRTUAL == MOD_VIRTUAL:
                c.virtual = True
            if attrs & MOD_EXCLUDE_FROM_POS_FILES:
                c.in_pos = False
            # The PCB contains another flag for the BoM
            # I guess it should be in sync, but: why should somebody want to unsync it?
            if attrs & MOD_EXCLUDE_FROM_BOM:
                c.in_bom_pcb = False
            if attrs & MOD_BOARD_ONLY:
                c.in_pcb_only = True
            look_for_type = (not c.smd) and (not c.tht)
            for pad in m.Pads():
                p = PadProperty()
                center = pad.GetCenter()
                p.x = center.x
                p.y = center.y
                p.fab_property = pad.GetProperty()
                p.net = pad.GetNetname()
                p.net_class = pad.GetNetClassName()
                p.has_hole = pad.HasHole()
                name = pad.GetNumber()
                c.pad_properties[name] = p
                # Try to figure out if this is THT or SMD when not specified
                if look_for_type:
                    if p.has_hole:
                        # At least one THT, stop looking
                        c.tht = True
                        look_for_type = False
                    elif name:
                        # We have pad a valid pad, assume this is all SMD and keep looking
                        c.smd = True


def expand_comp_fields(c, env):
    extra_env = {f.name.upper() if f.name.lower() in INTERNAL_FIELDS else f.name: f.value for f in c.fields}
    for f in c.fields:
        new_value = f.value
        depth = 1
        used_extra = [False]
        while depth < GS.MAXDEPTH:
            new_value = expand_env(new_value, env, extra_env, used_extra=used_extra)
            if not used_extra[0]:
                break
            depth += 1
            if depth == GS.MAXDEPTH:
                logger.warning(W_MAXDEPTH+'Too much nested variables replacements, possible loop ({})'.format(f.value))
        if new_value != f.value:
            c.set_field(f.name, new_value)


def expand_fields(comps, dont_copy=False):
    if not dont_copy:
        new_comps = deepcopy(comps)
        for n_c, c in zip(new_comps, comps):
            n_c.original_copy = c
    KiConf.init(GS.sch_file)
    env = KiConf.kicad_env
    env.update(GS.load_pro_variables())
    for c in comps:
        expand_comp_fields(c, env)
    return comps


def preflight_checks(skip_pre, targets):
    logger.debug("Preflight checks")
    BasePreFlight.configure_all()
    if skip_pre is not None:
        if skip_pre == 'all':
            logger.debug("Skipping all preflight actions")
            return
        else:
            skip_list = skip_pre.split(',')
            for skip in skip_list:
                if skip == 'all':
                    GS.exit_with_error('All can\'t be part of a list of actions '
                                       'to skip. Use `--skip all`', EXIT_BAD_ARGS)
                else:
                    if not BasePreFlight.is_registered(skip):
                        GS.exit_with_error(f'Unknown preflight `{skip}`', EXIT_BAD_ARGS)
                    o_pre = BasePreFlight.get_preflight(skip)
                    if not o_pre:
                        logger.warning(W_NONEEDSKIP + '`{}` preflight is not in use, no need to skip'.format(skip))
                    else:
                        logger.debug('Skipping `{}`'.format(skip))
                        o_pre.disable()
    BasePreFlight.run_enabled(targets)


def get_output_dir(o_dir, obj, dry=False):
    # outdir is a combination of the config and output
    outdir = os.path.realpath(os.path.abspath(obj.expand_dirname(os.path.join(GS.out_dir, o_dir))))
    # Create directory if needed
    logger.debug("Output destination: {}".format(outdir))
    if not dry:
        os.makedirs(outdir, exist_ok=True)
    return outdir


def config_output(out, dry=False, dont_stop=False):
    if out._configured:
        return True
    try:
        # Should we load the PCB?
        if not dry:
            if out.is_pcb():
                load_board()
            if out.is_sch():
                load_sch()
        ok = True
        out.config(None)
    except (KiPlotConfigurationError, PlotError) as e:
        msg = "In section '"+out.name+"' ("+out.type+"): "+str(e)
        GS.exit_with_error(msg, DONT_STOP if dont_stop else EXIT_BAD_CONFIG)
        ok = False
    except SystemExit:
        if not dont_stop:
            raise
        GS.errors_ignored = True
        ok = False
    return ok


def get_output_targets(output, parent):
    out = RegOutput.get_output(output)
    if out is None:
        GS.exit_with_error(f'Unknown output `{output}` selected in {parent}', WRONG_ARGUMENTS)
    config_output(out)
    out_dir = get_output_dir(out.dir, out, dry=True)
    files_list = out.get_targets(out_dir)
    return files_list, out_dir, out


def run_output(out, dont_stop=False):
    if out._done:
        return
    if GS.global_set_text_variables_before_output and hasattr(out.options, 'variant'):
        pre = BasePreFlight.get_preflight('set_text_variables')
        if pre:
            pre._variant = out.options.variant
            pre.apply()
            load_board()
    GS.current_output = out.name
    try:
        out.run(get_output_dir(out.dir, out))
        out._done = True
    except KiPlotConfigurationError as e:
        msg = "In section '"+out.name+"' ("+out.type+"): "+str(e)
        if dont_stop:
            logger.error(msg)
            GS.errors_ignored = True
        else:
            config_error(msg)
    except (PlotError, KiPlotError, SchError) as e:
        msg = "In output `"+str(out)+"`: "+str(e)
        GS.exit_with_error(msg, DONT_STOP if dont_stop else PLOT_ERROR)
    except KiConfError as e:
        ki_conf_error(e)
    except SystemExit:
        if not dont_stop:
            raise
        GS.errors_ignored = True


def configure_and_run(tree, out_dir, msg):
    out = RegOutput.get_class_for(tree['type'])()
    out.set_tree(tree)
    config_output(out)
    logger.debug(msg)
    out.run(out_dir)
    return out


def look_for_output(name, op_name, parent, valids):
    out = RegOutput.get_output(name)
    if out is None:
        raise KiPlotConfigurationError('Unknown output `{}` selected in {}'.format(name, parent))
    config_output(out)
    if out.type not in valids:
        raise KiPlotConfigurationError('`{}` must be {} type, not {}'.format(op_name, valids, out.type))
    return out


def _generate_outputs(targets, invert, skip_pre, cli_order, no_priority, dont_stop):
    logger.debug("Starting outputs for board {}".format(GS.pcb_file))
    # Make a list of target outputs
    n = len(targets)
    if n == 0:
        # No targets means all
        if invert:
            # Skip all targets
            logger.debug('Skipping all outputs')
        else:
            targets = [out for out in RegOutput.get_outputs() if out.run_by_default]
    else:
        # Check we got a valid list of outputs
        unknown = next(filter(lambda x: not RegOutput.is_output_or_group(x), targets), None)
        if unknown:
            GS.exit_with_error(f'Unknown output/group `{unknown}`', EXIT_BAD_ARGS)
        # Check for CLI+invert inconsistency
        if cli_order and invert:
            GS.exit_with_error("CLI order and invert options can't be used simultaneously", EXIT_BAD_ARGS)
        # Expand groups
        logger.debug('Outputs before groups expansion: {}'.format(targets))
        try:
            targets = RegOutput.solve_groups(targets, 'command line')
        except KiPlotConfigurationError as e:
            config_error(str(e))
        logger.debug('Outputs after groups expansion: {}'.format(targets))
        # Now convert the list of names into a list of output objects
        if cli_order:
            # Add them in the same order found at the command line
            targets = [RegOutput.get_output(name) for name in targets]
        else:
            # Add them in the declared order
            new_targets = []
            if invert:
                # Invert the selection
                for out in RegOutput.get_outputs():
                    if (out.name not in targets) and out.run_by_default:
                        new_targets.append(out)
                    else:
                        logger.debug('Skipping `{}` output'.format(out.name))
            else:
                # Normal list
                for out in RegOutput.get_outputs():
                    if out.name in targets:
                        new_targets.append(out)
                    else:
                        logger.debug('Skipping `{}` output'.format(out.name))
            targets = new_targets
    logger.debug('Outputs before preflights: {}'.format([t.name for t in targets]))
    # Run the preflights
    preflight_checks(skip_pre, targets)
    logger.debug('Outputs after preflights: {}'.format([t.name for t in targets]))
    if not cli_order and not no_priority:
        # Sort by priority
        targets = sorted(targets, key=lambda o: o.priority, reverse=True)
        logger.debug('Outputs after sorting: {}'.format([t.name for t in targets]))
    # Configure and run the outputs
    for out in targets:
        if GS.get_stop_flag():
            break
        if config_output(out, dont_stop=dont_stop):
            logger.info('- '+str(out))
            run_output(out, dont_stop)


def generate_outputs(targets, invert, skip_pre, cli_order, no_priority, dont_stop=False):
    setup_resources()
    prj = None
    if GS.global_restore_project:
        # Memorize the project content to restore it at exit
        prj = GS.read_pro()
    try:
        _generate_outputs(targets, invert, skip_pre, cli_order, no_priority, dont_stop)
    finally:
        # Restore the project file
        GS.write_pro(prj)


def adapt_file_name(name):
    if not name.startswith('/usr'):
        name = os.path.relpath(name)
    name = name.replace(' ', r'\ ')
    if '$' in name:
        logger.warning(W_WRONGCHAR+'Wrong character in file name `{}`'.format(name))
    return name


def gen_global_targets(f, pre_targets, out_targets, type):
    extra_targets = []
    pre = 'pre_'+type
    out = 'out_'+type
    all = 'all_'+type
    if pre_targets:
        f.write('{}:{}\n\n'.format(pre, pre_targets))
        extra_targets.append(pre)
    if out_targets:
        f.write('{}:{}\n\n'.format(out, out_targets))
        extra_targets.append(out)
    if pre_targets or out_targets:
        tg = ''
        if pre_targets:
            tg = ' '+pre
        if out_targets:
            tg += ' '+out
        f.write('{}:{}\n\n'.format(all, tg))
        extra_targets.append(all)
    return extra_targets


def get_pre_targets(targets, dependencies, is_pre):
    pcb_targets = sch_targets = ''
    BasePreFlight.configure_all()
    prefs = BasePreFlight.get_in_use_objs()
    try:
        for pre in prefs:
            tg = pre.get_targets()
            if not tg:
                continue
            name = pre.type
            targets[name] = [adapt_file_name(fn) for fn in tg]
            dependencies[name] = [adapt_file_name(fn) for fn in pre.get_dependencies()]
            is_pre.add(name)
            if pre.is_sch():
                sch_targets += ' '+name
            if pre.is_pcb():
                pcb_targets += ' '+name
    except KiPlotConfigurationError as e:
        config_error("In preflight '"+name+"': "+str(e))
    return pcb_targets, sch_targets


def get_out_targets(outputs, ori_names, targets, dependencies, comments, no_default):
    pcb_targets = sch_targets = ''
    try:
        for out in outputs:
            name = name2make(out.name)
            ori_names[name] = out.name
            tg = out.get_targets(out.expand_dirname(os.path.join(GS.out_dir, out.dir)))
            if not tg:
                continue
            targets[name] = [adapt_file_name(fn) for fn in tg]
            dependencies[name] = [adapt_file_name(fn) for fn in out.get_dependencies()]
            if out.comment:
                comments[name] = out.comment
            if not out.run_by_default:
                no_default.add(name)
            if out.is_sch():
                sch_targets += ' '+name
            if out.is_pcb():
                pcb_targets += ' '+name
    except KiPlotConfigurationError as e:
        config_error("In output '"+name+"': "+str(e))
    return pcb_targets, sch_targets


def generate_makefile(makefile, cfg_file, outputs, kibot_sys=False):
    cfg_file = os.path.relpath(cfg_file)
    logger.info('- Creating makefile `{}` from `{}`'.format(makefile, cfg_file))
    with open(makefile, 'wt') as f:
        f.write('#!/usr/bin/make\n')
        f.write('# Automatically generated by KiBot from `{}`\n'.format(cfg_file))
        fname = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src', 'kibot'))
        if kibot_sys or not os.path.isfile(fname):
            fname = 'kibot'
        f.write('KIBOT?={}\n'.format(fname))
        dbg = ''
        if GS.debug_level > 0:
            dbg = '-'+'v'*GS.debug_level
        f.write('DEBUG?={}\n'.format(dbg))
        f.write('CONFIG={}\n'.format(cfg_file))
        if GS.sch_file:
            f.write('SCH={}\n'.format(os.path.relpath(GS.sch_file)))
        if GS.pcb_file:
            f.write('PCB={}\n'.format(os.path.relpath(GS.pcb_file)))
        f.write('DEST={}\n'.format(os.path.relpath(GS.out_dir)))
        f.write('KIBOT_CMD=$(KIBOT) $(DEBUG) -c $(CONFIG) -e $(SCH) -b $(PCB) -d $(DEST)\n')
        f.write('LOGFILE?=kibot_error.log\n')
        f.write('\n')
        # Configure all outputs
        for out in outputs:
            config_output(out)
        # Get all targets and dependencies
        targets = OrderedDict()
        dependencies = OrderedDict()
        comments = {}
        ori_names = {}
        is_pre = set()
        no_default = set()
        # Preflights
        pre_pcb_targets, pre_sch_targets = get_pre_targets(targets, dependencies, is_pre)
        # Outputs
        out_pcb_targets, out_sch_targets = get_out_targets(outputs, ori_names, targets, dependencies, comments, no_default)
        # all target
        f.write('#\n# Default target\n#\n')
        f.write('all: '+' '.join(filter(lambda x: x not in no_default, targets.keys()))+'\n\n')
        extra_targets = ['all']
        # PCB/SCH specific targets
        f.write('#\n# SCH/PCB targets\n#\n')
        extra_targets.extend(gen_global_targets(f, pre_sch_targets, out_sch_targets, 'sch'))
        extra_targets.extend(gen_global_targets(f, pre_pcb_targets, out_pcb_targets, 'pcb'))
        # Generate the output targets
        f.write('#\n# Available targets (outputs)\n#\n')
        for name, target in targets.items():
            f.write(name+': '+' '.join(target)+'\n\n')
        # Generate the output dependencies
        f.write('#\n# Rules and dependencies\n#\n')
        if GS.debug_enabled:
            kibot_cmd = '\t$(KIBOT_CMD)'
            log_action = ''
        else:
            kibot_cmd = '\t@$(KIBOT_CMD)'
            log_action = ' 2>> $(LOGFILE)'
        skip_all = ','.join(is_pre)
        for name, dep in dependencies.items():
            if name in comments:
                f.write('# '+comments[name]+'\n')
            dep.append(cfg_file)
            f.write(' '.join(targets[name])+': '+' '.join(dep)+'\n')
            if name in is_pre:
                skip = filter(lambda n: n != name, is_pre)
                f.write('{} -s {} -i{}\n\n'.format(kibot_cmd, ','.join(skip), log_action))
            else:
                f.write('{} -s {} "{}"{}\n\n'.format(kibot_cmd, skip_all, ori_names[name], log_action))
        # Mark all outputs as PHONY
        f.write('.PHONY: '+' '.join(extra_targets+list(targets.keys()))+'\n')


def guess_ki6_sch(schematics):
    schematics = list(filter(lambda x: x.endswith('.kicad_sch'), schematics))
    if len(schematics) == 1:
        return schematics[0]
    if len(schematics) == 0:
        return None
    for fname in schematics:
        with open(fname, 'rt') as f:
            text = f.read()
        if 'sheet_instances' in text:
            return fname
    return None


def avoid_mixing_5_and_6(sch, kicad_sch):
    GS.exit_with_error(['Found KiCad 5 and KiCad 6+ files, make sure the whole project uses one version',
                        'KiCad 5:  '+os.path.basename(sch),
                        'KiCad 6+: '+os.path.basename(kicad_sch)], EXIT_BAD_CONFIG)


def solve_schematic(base_dir, a_schematic=None, a_board_file=None, config=None, sug_e=True):
    schematic = a_schematic
    if not schematic and a_board_file:
        base = os.path.splitext(a_board_file)[0]
        sch = os.path.join(base_dir, base+'.sch')
        kicad_sch = os.path.join(base_dir, base+'.kicad_sch')
        found_sch = os.path.isfile(sch)
        found_kicad_sch = os.path.isfile(kicad_sch)
        if found_sch and found_kicad_sch:
            avoid_mixing_5_and_6(sch, kicad_sch)
        if found_sch:
            schematic = sch
        elif GS.ki6 and found_kicad_sch:
            schematic = kicad_sch
    if not schematic:
        schematics = glob(os.path.join(base_dir, '*.sch'))
        if GS.ki6:
            schematics += glob(os.path.join(base_dir, '*.kicad_sch'))
        if len(schematics) == 1:
            schematic = schematics[0]
            logger.info('Using SCH file: '+os.path.relpath(schematic))
        elif len(schematics) > 1:
            # Look for a schematic with the same name as the config
            if config:
                if config[0] == '.':
                    # Unhide hidden config
                    config = config[1:]
                # Remove any extension
                last_split = None
                while '.' in config and last_split != config:
                    last_split = config
                    config = os.path.splitext(config)[0]
                # Try KiCad 5
                sch = os.path.join(base_dir, config+'.sch')
                found_sch = os.path.isfile(sch)
                # Try KiCad 6
                kicad_sch = os.path.join(base_dir, config+'.kicad_sch')
                found_kicad_sch = os.path.isfile(kicad_sch)
                if found_sch and found_kicad_sch:
                    avoid_mixing_5_and_6(sch, kicad_sch)
                if found_sch:
                    schematic = sch
                elif GS.ki6 and found_kicad_sch:
                    schematic = kicad_sch
            if not schematic:
                # Look for a schematic with a PCB and/or project
                for sch in schematics:
                    base = os.path.splitext(sch)[0]
                    if (os.path.isfile(os.path.join(base_dir, base+'.pro')) or
                       os.path.isfile(os.path.join(base_dir, base+'.kicad_pro')) or
                       os.path.isfile(os.path.join(base_dir, base+'.kicad_pcb'))):
                        schematic = sch
                        break
                else:
                    # No way to select one, just take the first
                    if GS.ki6:
                        schematic = guess_ki6_sch(schematics)
                    if not schematic:
                        schematic = schematics[0]
            msg = ' if you want to use another use -e option' if sug_e else ''
            logger.warning(W_VARSCH + 'More than one SCH file found in `'+base_dir+'`.\n'
                           '  Using '+schematic+msg+'.')
    if schematic and not os.path.isfile(schematic):
        GS.exit_with_error("Schematic file not found: "+schematic, NO_SCH_FILE)
    if schematic:
        schematic = os.path.abspath(schematic)
        logger.debug('Using schematic: `{}`'.format(schematic))
        logger.debug('Real schematic name: `{}`'.format(cased_path(schematic)))
    else:
        logger.debug('No schematic file found')
    return schematic


def check_board_file(board_file):
    if board_file and not os.path.isfile(board_file):
        GS.exit_with_error("Board file not found: "+board_file, NO_PCB_FILE)


def solve_board_file(base_dir, a_board_file=None, sug_b=True):
    schematic = GS.sch_file
    board_file = a_board_file
    if not board_file and schematic:
        pcb = os.path.join(base_dir, os.path.splitext(schematic)[0]+'.kicad_pcb')
        if os.path.isfile(pcb):
            board_file = pcb
    if not board_file:
        board_files = glob(os.path.join(base_dir, '*.kicad_pcb'))
        if len(board_files) == 1:
            board_file = board_files[0]
            logger.info('Using PCB file: '+os.path.relpath(board_file))
        elif len(board_files) > 1:
            board_file = board_files[0]
            msg = ' if you want to use another use -b option' if sug_b else ''
            logger.warning(W_VARPCB + 'More than one PCB file found in `'+base_dir+'`.\n'
                           '  Using '+board_file+msg+'.')
    check_board_file(board_file)
    if board_file:
        logger.debug('Using PCB: `{}`'.format(board_file))
        logger.debug('Real PCB name: `{}`'.format(cased_path(board_file)))
    else:
        logger.debug('No PCB file found')
    return board_file


def solve_project_file():
    if GS.pcb_file:
        pro_name = GS.pcb_no_ext+GS.pro_ext
        if os.path.isfile(pro_name):
            return pro_name
    if GS.sch_file:
        pro_name = GS.sch_no_ext+GS.pro_ext
        if os.path.isfile(pro_name):
            return pro_name
    return None


def look_for_used_layers():
    from .layer import Layer
    Layer.reset()
    layers = set()
    components = {}
    # Look inside the modules
    for m in GS.get_modules():
        layer = m.GetLayer()
        components[layer] = components.get(layer, 0)+1
        for gi in m.GraphicalItems():
            layers.add(gi.GetLayer())
        for pad in m.Pads():
            for id in pad.GetLayerSet().Seq():
                layers.add(id)
    # All drawings in the PCB
    for e in GS.board.GetDrawings():
        layers.add(e.GetLayer())
    # Zones
    for e in list(GS.board.Zones()):
        layers.add(e.GetLayer())
    # Tracks and vias
    via_type = 'VIA' if GS.ki5 else 'PCB_VIA'
    for e in GS.board.GetTracks():
        if e.GetClass() == via_type:
            for id in e.GetLayerSet().Seq():
                layers.add(id)
        else:
            layers.add(e.GetLayer())
    # Now filter the pads and vias potential layers
    declared_layers = {la._id for la in Layer.solve('all')}
    layers = sorted(declared_layers.intersection(layers))
    logger.debug('- Detected layers: {}'.format(layers))
    layers = Layer.solve(layers)
    for la in layers:
        la.components = components.get(la._id, 0)
    return layers


def discover_files(dest_dir):
    """ Look for schematic and PCBs at the dest_dir.
        Return the name of the example file to generate. """
    GS.pcb_file = None
    GS.sch_file = None
    # Check if we have useful files
    fname = os.path.join(dest_dir, 'kibot_generated.kibot.yaml')
    GS.set_sch(solve_schematic(dest_dir, sug_e=False))
    GS.set_pcb(solve_board_file(dest_dir, sug_b=False))
    GS.set_pro(solve_project_file())
    return fname


def load_config(plot_config):
    if not plot_config:
        return []
    cr = CfgYamlReader()
    outputs = None
    try:
        # The Python way ...
        with gzip.open(plot_config, mode='rt') as cf_file:
            try:
                outputs = cr.read(cf_file)
            except KiPlotConfigurationError as e:
                config_error(str(e))
    except OSError:
        pass
    if outputs is None:
        with open(plot_config) as cf_file:
            try:
                outputs = cr.read(cf_file)
            except KiPlotConfigurationError as e:
                config_error(str(e))
    return outputs


def yaml_dump(f, tree):
    if version_str2tuple(yaml.__version__) < (3, 14):
        f.write(yaml.dump(tree))
    else:
        # sort_keys was introduced after 3.13
        f.write(yaml.dump(tree, sort_keys=False))


def register_xmp_import(name, definitions=None):
    """ Register an import we need for an example """
    global needed_imports
    assert name not in needed_imports
    needed_imports[name] = definitions


def check_we_cant_use(o):
    """ Check if the output doesn't have what it needs, i.e. no PCB and this is PCB related """
    return ((not (o.is_pcb() and GS.pcb_file) and
             not (o.is_sch() and GS.sch_file) and
             not (o.is_any() and (GS.pcb_file or GS.sch_file))) or
            ((o.is_pcb() and o.is_sch()) and (not GS.pcb_file or not GS.sch_file)))


def generate_one_example(dest_dir, types):
    """ Generate a example config for dest_dir """
    fname = discover_files(dest_dir)
    # Abort if none
    if not GS.pcb_file and not GS.sch_file:
        return None
    # Reset the board and schematic
    GS.board = None
    GS.sch = None
    # Create the config
    with open(fname, 'wt') as f:
        logger.info('- Creating {} example configuration'.format(fname))
        f.write("# This is a working example.\n")
        f.write("# For a more complete reference use `--example`\n")
        f.write('kibot:\n  version: 1\n\n')
        # Outputs
        outs = RegOutput.get_registered()
        # List of layers
        layers = []
        if GS.pcb_file:
            load_board(GS.pcb_file)
            layers = look_for_used_layers()
        if GS.sch_file:
            load_sch()
        # Filter some warnings
        fil = [{'number': 1007},  # No information for a component in a distributor
               {'number': 1015},  # More than one component in a search for a distributor
               {'number': 58},    # Missing project file
               {'number': 107},   # Stencil.side auto, we always use it for the example
               ]
        glb = {'filters': fil}
        yaml_dump(f, {'global': glb})
        f.write('\n')
        # A helper for the internal templates
        global needed_imports
        needed_imports = {}
        # All the preflights
        preflights = {}
        for n in sorted(BasePreFlight.get_registered().keys()):
            o = BasePreFlight.get_object_for(n)
            if types and n not in types:
                logger.debug('- {}, not selected (PCB: {} SCH: {})'.format(n, o.is_pcb(), o.is_sch()))
                continue
            if check_we_cant_use(o):
                logger.debug('- {}, skipped (PCB: {} SCH: {})'.format(n, o.is_pcb(), o.is_sch()))
                continue
            tree = o.get_conf_examples(n, layers)
            if tree:
                logger.debug('- {}, generated'.format(n))
                preflights.update(tree)
            else:
                logger.debug('- {}, nothing to do'.format(n))
        # All the outputs
        outputs = []
        for n, cls in OrderedDict(sorted(outs.items())).items():
            o = cls()
            if types and n not in types:
                logger.debug('- {}, not selected (PCB: {} SCH: {})'.format(n, o.is_pcb(), o.is_sch()))
                continue
            if check_we_cant_use(o):
                logger.debug('- {}, skipped (PCB: {} SCH: {})'.format(n, o.is_pcb(), o.is_sch()))
                continue
            tree = cls.get_conf_examples(n, layers)
            if tree:
                logger.debug('- {}, generated'.format(n))
                outputs.extend(tree)
            else:
                logger.debug('- {}, nothing to do'.format(n))
        global_defaults = None
        if needed_imports:
            imports = []
            for n, d in sorted(needed_imports.items()):
                if n == 'global':
                    global_defaults = d
                    continue
                content = {'file': n}
                if d:
                    content['definitions'] = d
                imports.append(content)
            yaml_dump(f, {'import': imports})
            f.write('\n')
        if preflights:
            yaml_dump(f, {'preflight': preflights})
            f.write('\n')
        if outputs:
            yaml_dump(f, {'outputs': outputs})
        else:
            return None
        if global_defaults:
            f.write('\n...\n')
            yaml_dump(f, {'definitions': global_defaults})
    return fname


def reset_config():
    # Outputs, groups, filters and variants
    RegOutput.reset()
    # Preflights
    BasePreFlight.reset()


def generate_targets(config_file):
    """ Generate all possible targets for the configuration file """
    # Reset the board and schematic
    GS.board = None
    GS.sch = None
    # Reset the list of outputs and preflights
    reset_config()
    # Read the config file
    cr = CfgYamlReader()
    with open(config_file) as cf_file:
        cr.read(cf_file)
    # Do all the job
    generate_outputs([], False, None, False, False, dont_stop=True)


def _walk(path, depth):
    """ Recursively list files and directories up to a certain depth """
    depth -= 1
    try:
        with os.scandir(path) as p:
            for entry in p:
                yield entry.path
                if entry.is_dir() and depth > 0:
                    yield from _walk(entry.path, depth)
    except Exception as e:
        logger.debug(f'Skipping {path} because {e}')


def setup_fonts(source):
    if not os.path.isdir(source):
        logger.debug('No font resources dir')
        return
    dest = os.path.expanduser('~/.fonts/')
    installed = False
    for f in glob(os.path.join(source, '*.ttf')) + glob(os.path.join(source, '*.otf')):
        fname = os.path.basename(f)
        fdest = os.path.join(dest, fname)
        if os.path.isfile(fdest):
            logger.debug('Font {} already installed'.format(fname))
            continue
        logger.info('Installing font {}'.format(fname))
        if not os.path.isdir(dest):
            os.makedirs(dest)
        copy2(f, fdest)
        installed = True
    if installed:
        run_command(['fc-cache'])


def setup_colors(source):
    if not os.path.isdir(source):
        logger.debug('No color resources dir')
        return
    if not GS.kicad_conf_path:
        return
    dest = os.path.join(GS.kicad_conf_path, 'colors')
    for f in glob(os.path.join(source, '*.json')):
        fname = os.path.basename(f)
        fdest = os.path.join(dest, fname)
        if os.path.isfile(fdest):
            logger.debug('Color {} already installed'.format(fname))
            continue
        logger.info('Installing color {}'.format(fname))
        if not os.path.isdir(dest):
            os.makedirs(dest)
        copy2(f, fdest)


def setup_resources():
    if not GS.global_resources_dir:
        logger.debug('No resources dir')
        return
    setup_fonts(os.path.join(GS.global_resources_dir, 'fonts'))
    setup_colors(os.path.join(GS.global_resources_dir, 'colors'))


def generate_examples(start_dir, dry, types):
    if not start_dir:
        start_dir = '.'
    else:
        if not os.path.isdir(start_dir):
            GS.exit_with_error(f'Invalid dir {start_dir} to quick start', WRONG_ARGUMENTS)
    # Set default global options
    glb = GS.set_global_options_tree({})
    glb.config(None)
    # Install the resources
    setup_resources()
    # Look for candidate dirs
    k_files_regex = re.compile(r'([^/]+)\.(kicad_pro|pro)$')
    candidates = set()
    for f in _walk(start_dir, 6):
        if k_files_regex.search(f):
            candidates.add(os.path.realpath(os.path.dirname(f)))
    if not candidates:
        GS.exit_with_error(f'No KiCad projects found in `{start_dir}`', MISSING_FILES)
    # Try to generate the configs in the candidate places
    confs = []
    for c in sorted(candidates):
        logger.info('Analyzing `{}` dir'.format(c))
        res = generate_one_example(c, types)
        if res:
            confs.append(res)
        logger.info('')
    confs.sort()
    # Just the configs, not the targets
    if dry:
        return
    # Try to generate all the stuff
    if GS.out_dir_in_cmd_line:
        out_dir = GS.out_dir
    else:
        out_dir = 'Generated'
    for n, c in enumerate(confs):
        conf_dir = os.path.dirname(c)
        if len(confs) > 1:
            subdir = '%03d-%s' % (n+1, conf_dir.replace('/', ',').replace(' ', '_'))
            dest = os.path.join(out_dir, subdir)
        else:
            dest = out_dir
        GS.out_dir = dest
        logger.info('Generating targets for `{}`, destination: `{}`'.format(c, dest))
        os.makedirs(dest, exist_ok=True)
        # Create a log file with all the debug we can
        fl = log.set_file_log(os.path.join(dest, 'kibot.log'))
        old_lvl = GS.debug_level
        GS.debug_level = 10
        # Detect the SCH and PCB again
        discover_files(conf_dir)
        # Generate all targets
        generate_targets(c)
        # Close the debug file
        log.remove_file_log(fl)
        GS.debug_level = old_lvl
        logger.info('')
    # Try to open a browser
    index = os.path.join(GS.out_dir, 'index.html')
    if os.environ.get('DISPLAY') and which('x-www-browser') and os.path.isfile(index):
        Popen(['x-www-browser', index])


def get_columns():
    """ Create a list of valid columns """
    if GS.sch:
        cols = deepcopy(ColumnList.COLUMNS_DEFAULT)
        return (GS.sch.get_field_names(cols), ColumnList.COLUMNS_EXTRA)
    return (ColumnList.COLUMNS_DEFAULT, ColumnList.COLUMNS_EXTRA)


# To avoid circular dependencies: Optionable needs it, but almost everything needs Optionable
GS.load_board = load_board
GS.load_sch = load_sch
GS.exec_with_retry = exec_with_retry
