# -*- coding: utf-8 -*-
# Copyright (c) 2020-2025 Salvador E. Tropea
# Copyright (c) 2020-2025 Instituto Nacional de Tecnología Industrial
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)
"""
KiCad configuration classes.
Reads the KiCad's configuration files.
In particular:
- kicad_common to know about the 'environment' variables
- The `sym-lib-table` files to map library aliases

Notes about coverage:
I'm excluding all the Darwin and Windows code from coverage.
I'm not even sure the values are correct.
"""
import atexit
import csv
from glob import glob
from io import StringIO
import json
import os
import platform
import re
from shutil import copy2
import sys
import sysconfig
from ..error import KiPlotConfigurationError
from ..gs import GS
from .. import log
from ..misc import (W_NOCONFIG, W_NOKIENV, W_NOLIBS, W_NODEFSYMLIB, MISSING_WKS, W_MAXDEPTH, W_3DRESVER, W_LIBTVERSION,
                    W_LIBTUNK, W_MISLIBTAB, EMBED_PREFIX)
from .sexpdata import load, SExpData, Symbol, dumps, Sep
from .sexp_helpers import _check_is_symbol_list, _check_integer, _check_relaxed

# Check python version to determine which version of ConfirParser to import
if sys.version_info.major >= 3:
    import configparser as ConfigParser
else:  # pragma: no cover (Py2)
    # For future Python 2 support
    import ConfigParser

logger = log.get_logger()
SYM_LIB_TABLE = 'sym-lib-table'
FP_LIB_TABLE = 'fp-lib-table'
KICAD_COMMON = 'kicad_common'
SUP_VERSION = 7
reported = set()


class KiConfError(Exception):
    def __init__(self, msg, file, lnum, line):
        super().__init__()
        self.line = lnum
        self.file = file
        self.msg = msg
        self.code = line


def un_quote(val):
    """ Remove optional quotes """
    if val[0] == '"':
        val.replace('\"', '"')
        val = val[1:-1]
    return val


def parse_len_str(val):
    if ':' not in val:
        return val
    pos = val.index(':')
    try:
        c = int(val[:pos])
    except ValueError:
        c = None
        logger.non_critical_error('Malformed 3D alias entry: '+val)
    value = val[pos+1:]
    if c is not None and c != len(value):
        logger.non_critical_error(f'3D alias entry error, expected len {c}, but found {len(value)}')
    return value


def fix_windows(name):
    if not name or name.startswith(EMBED_PREFIX):
        return name
    if not os.path.isfile(name):
        fixed = name.replace('\\', '/')
        if os.path.isfile(fixed):
            logger.debug(f'Fixing windows path: {name} -> {fixed}')
            return fixed
    return name


def is_ci_cd_normal(var):
    # Default docker images doesn't contain the 3D models, so we get this most of the time
    return GS.ci_cd_detected and var.startswith('KICAD') and var.endswith('_3DMODEL_DIR')


def expand_env(val, env, extra_env, used_extra=None):
    """ Expand KiCad environment variables """
    if used_extra is None:
        used_extra = [False]
    used_extra[0] = False
    success = replaced = True
    depth = 0
    ori_val = val
    while success and replaced and depth < GS.MAXDEPTH:
        replaced = False
        depth += 1
        if depth == GS.MAXDEPTH:
            logger.warning(W_MAXDEPTH+'Too much nested variables replacements, possible loop ({})'.format(ori_val))
            success = False
        for var in re.findall(r'\$\{(\S+?)\}', val):
            to_replace = '${'+var+'}'
            if var in env:
                val = val.replace(to_replace, env[var])
                replaced = True
            elif var in extra_env:
                val = val.replace(to_replace, extra_env[var])
                used_extra[0] = True
                replaced = True
            elif GS.global_use_os_env_for_expand and var in os.environ:
                val = val.replace(to_replace, os.environ[var])
                used_extra[0] = True
                replaced = True
            else:
                success = False
                # Note: We can't expand NET_NAME(n)
                if var not in reported and not var.startswith('NET_NAME(') and not is_ci_cd_normal(var):
                    logger.non_critical_error(f'Unable to expand `{var}` in `{val}`')
                    reported.add(var)
    return val


class LibAlias(object):
    """ An entry for the symbol libs table """
    def __init__(self):
        super().__init__()
        self.name = None
        self.legacy = True
        self.uri = None
        self.options = None
        self.descr = None
        self.type = None

    @staticmethod
    def parse(items, env, extra_env):
        s = LibAlias()
        for i in items[1:]:
            i_type = _check_is_symbol_list(i)
            if i_type == 'name':
                s.name = _check_relaxed(i, 1, i_type)
            elif i_type == 'type':
                s.type = _check_relaxed(i, 1, i_type)
            elif i_type == 'uri':
                s.uri = os.path.abspath(expand_env(_check_relaxed(i, 1, i_type), env, extra_env))
            elif i_type == 'options':
                s.options = _check_relaxed(i, 1, i_type)
            elif i_type == 'descr':
                s.descr = _check_relaxed(i, 1, i_type)
            else:
                logger.warning(W_LIBTUNK+'Unknown lib table attribute `{}`'.format(i))
        s.legacy = s.type is not None and s.type != 'Legacy'
        return s

    def __str__(self):
        if not self.name:
            return 'unnamed LibAlias'
        return '`'+self.name+'` -> `'+self.uri+'`'


class KiConf(object):
    """ Class to load and hold all KiCad configuration """
    loaded = False
    config_dir = None
    dirname = None
    sym_lib_dir = None
    template_dir = None
    footprint_dir = None
    models_3d_dir = None
    party_3rd_dir = None
    kicad_env = {}
    lib_aliases = None
    fp_aliases = None
    aliases_3D = {}

    def __init__(self):
        raise AssertionError("KiConf is fully static, no instances allowed")

    def init(fname):
        """ fname is the base project name, any extension is allowed.
            So it can be the main schematic, the PCB or the project. """
        if KiConf.loaded:
            return
        KiConf.dirname = os.path.dirname(fname)
        KiConf.kicad_env['KIPRJMOD'] = KiConf.dirname
        KiConf.load_kicad_common()
        KiConf.load_3d_aliases()
        KiConf.loaded = True
        # Loaded on demand, here to debug
        # KiConf.get_sym_lib_aliases()
        # logger.error(KiConf.lib_aliases)
        # KiConf.get_fp_lib_aliases()
        # logger.error(KiConf.fp_aliases)

    def find_kicad_common():
        """ Looks for kicad_common config file.
            Returns its name or None. """
        cfg = ''
        if GS.kicad_conf_path:
            cfg = os.path.join(GS.kicad_conf_path, KICAD_COMMON)
            if GS.ki6:
                cfg += '.json'
            if os.path.isfile(cfg):
                return cfg
        logger.warning(W_NOCONFIG + 'Unable to find KiCad configuration file ({})'.format(cfg))
        return None

    def _guess_kicad_data_dir(data_dir):
        """ Tries to figure out where libraries are.
            Only used if we failed to find the kicad_common file.
            On modern KiCad (6+) this is always used because KiCad doesn't store the path in kicad_common,
            unless modified by the user. """
        # Give priority to the KICAD_PATH environment variable
        kpath = os.environ.get('KICAD_PATH')
        if kpath and os.path.isdir(kpath):
            dir = os.path.join(kpath, data_dir)
            if os.path.isdir(dir):
                return dir
        # Try to guess according to the OS
        system = platform.system()
        share = os.path.join('share', GS.kicad_dir, data_dir)
        if system == 'Linux':
            scheme_names = sysconfig.get_scheme_names()
            # Try in local dir
            if 'posix_user' in scheme_names:
                dir = os.path.join(sysconfig.get_path('data', 'posix_user'), share)
                if os.path.isdir(dir):
                    return dir
            # Try at system level
            if 'posix_prefix' in scheme_names:
                dir = os.path.join(sysconfig.get_path('data', 'posix_prefix'), share)
                if os.path.isdir(dir):
                    return dir
        elif system == 'Darwin':  # pragma: no cover (Darwin)
            app_data = os.path.join('Library', 'Application Support', GS.kicad_dir, data_dir)
            home = os.environ.get('HOME')
            if home:
                dir = os.path.join(home, app_data)
                if os.path.isdir(dir):
                    return dir
            dir = os.path.join('/', app_data)
            if os.path.isdir(dir):
                return dir
        elif system == 'Windows':  # pragma: no cover (Windows)
            dir = os.path.join('C:', 'Program Files', 'KiCad', share)
            if os.path.isdir(dir):
                return dir
            dir = os.path.join('C:', 'KiCad', share)
            if os.path.isdir(dir):
                return dir
            username = os.environ.get('username')
            dir = os.path.join('C:', 'Users', username, 'Documents', 'KiCad', data_dir)
            if os.path.isdir(dir):
                return dir
        return None

    def guess_symbol_dir():
        if GS.ki5:
            order = ['library', 'symbols']
        else:
            order = ['symbols', 'library']
        guess = KiConf._guess_kicad_data_dir(order[0])
        if guess is None:
            guess = KiConf._guess_kicad_data_dir(order[1])
        return guess

    def guess_footprint_dir():
        if GS.ki5:
            order = ['modules', 'footprints']
        else:
            order = ['footprints', 'modules']
        guess = KiConf._guess_kicad_data_dir(order[0])
        if guess is None:
            guess = KiConf._guess_kicad_data_dir(order[1])
        return guess

    def guess_template_dir():
        return KiConf._guess_kicad_data_dir('template')

    def guess_3d_dir():
        modules3d = os.path.join('modules', 'packages3d')
        if GS.ki5:
            order = [modules3d, '3dmodels']
        else:
            order = ['3dmodels', modules3d]
        guess = KiConf._guess_kicad_data_dir(order[0])
        if guess is None:
            guess = KiConf._guess_kicad_data_dir(order[1])
        return guess

    def guess_user_template_dir():
        system = platform.system()
        if system == 'Linux':
            home = os.environ.get('HOME')
            if home is None:
                return None
            if GS.ki6:
                name = os.path.join(home, '.local', 'share', 'kicad', str(GS.kicad_version_major)+'.0', 'template')
                if os.path.isdir(name):
                    return name
            name = os.path.join(home, 'kicad', 'template')
            if os.path.isdir(name):
                return name
            return None
        elif system == 'Darwin':  # pragma: no cover (Darwin)
            home = os.environ.get('HOME')
            if home is None:
                return None
            name = os.path.join(home, 'Documents', 'kicad', 'template')
            if os.path.isdir(name):
                return name
            return None
        elif system == 'Windows':  # pragma: no cover (Windows)
            username = os.environ.get('username')
            dir = os.path.join('C:', 'Documents and Settings', username, 'My Documents', 'kicad', 'template')
            if os.path.isdir(dir):
                return dir
            dir = os.path.join('C:', 'Users', username, 'Documents', 'kicad', 'template')
            if os.path.isdir(dir):
                return dir
            return None

    def guess_3rd_dir():
        home = os.environ.get('HOME')
        if home is None:
            return None
        return os.path.join(home, '.local', 'share', 'kicad', str(GS.kicad_version_major)+'.0', '3rdparty')

    def load_ki5_env(cfg):
        """ Environment vars from KiCad 5 configuration """
        # Load the "environment variables"
        with open(cfg, 'rt') as f:
            buf = f.read()
        io_buf = StringIO('[Default]\n'+buf)
        cf = ConfigParser.RawConfigParser(allow_no_value=True)
        cf.optionxform = str
        if sys.version_info.major >= 3:
            cf.read_file(io_buf, cfg)
        else:  # pragma: no cover (Py2)
            cf.readfp(io_buf, cfg)
        if 'EnvironmentVariables' not in cf.sections():
            logger.warning(W_NOKIENV + 'KiCad config without EnvironmentVariables section')
        else:
            for k, v in cf.items('EnvironmentVariables'):
                if GS.debug_level > 1:
                    logger.debug('- KiCad var: {}="{}"'.format(k, v))
                KiConf.kicad_env[k] = v

    def load_ki6_env(cfg):
        """ Environment vars from KiCad 6 configuration """
        # Notes about KiCad 6 environment vars:
        # 1) KiCad has some hardcoded internal values
        # 2) Only the values that the user modifies are stored in the config file
        # 3) Any value defined in the environment will have priority over internal definitions
        # It means that we currently don't know the real value unless the user modifies it or defines in the env
        with open(cfg, 'rt') as f:
            data = json.load(f)
        if "environment" in data and 'vars' in data['environment'] and (data['environment']['vars'] is not None):
            for k, v in data['environment']['vars'].items():
                if GS.debug_level > 1:
                    logger.debug('- KiCad var: {}="{}"'.format(k, v))
                KiConf.kicad_env[k] = v
        else:
            logger.warning(W_NOKIENV + 'KiCad config without environment.vars section')

    def _look_env_var(base_name, old, only_old, ki6_diff, no_dir):
        """ Looks for a KiCad variable definition.
            First in the OS environment, then in the config.
            Sync the other source. """
        if not no_dir:
            base_name += '_DIR'
        names = []
        if GS.ki6 and ki6_diff:
            # KiCad 6 specific name goes first when using KiCad 6
            for n in reversed(range(6, GS.kicad_version_major+1)):
                names.append('KICAD{}_{}'.format(n, base_name))
        # KiCad 5 names, allowed even when using KiCad 6
        if not only_old:
            # A KICAD_* is valid
            names.append('KICAD_'+base_name)
        if old:
            # A specific legacy name
            names.append(old)
        ret_val = None
        # Look for the above names
        # The first we find is the one we use, but we export all the ones we found
        for n in names:
            val = None
            # OS environment has more priority
            if n in os.environ:
                val = os.environ[n]
                KiConf.kicad_env[n] = val
                logger.debug('Using {}="{}" (from environment)'.format(n, val))
            # Then the file
            elif n in KiConf.kicad_env:
                val = KiConf.kicad_env[n]
                os.environ[n] = val
                logger.debug('Using {}="{}" (from KiCad config)'.format(n, val))
            if val is not None and ret_val is None:
                ret_val = val
        # Make sure all the versions point to the same place
        # It helps if we are using KiCad 6 but have the KiCad 5 names defined,
        # KiCad will use them, but any mention to the KiCad 6 version won't be
        # valid for KiBot unless we explicitly define it.
        if ret_val is not None:
            for n in names:
                if n not in os.environ or n not in KiConf.kicad_env:
                    os.environ[n] = ret_val
                    KiConf.kicad_env[n] = ret_val
        return ret_val

    def _set_env_var(base_name, val, ki6_diff, no_dir):
        """ Sets the environment and the internal list """
        if not no_dir:
            base_name += '_DIR'
        if GS.ki6 and ki6_diff:
            name = 'KICAD{}_{}'.format(GS.kicad_version_major, base_name)
        else:
            name = 'KICAD_'+base_name
        KiConf.kicad_env[name] = val
        os.environ[name] = val
        logger.debug('Using {}="{}" (guessed)'.format(name, val))

    def _solve_var(name, member, desc, guesser, old=None, only_old=False, ki6_diff=True, only_k6=False, no_dir=False):
        if only_k6 and GS.ki5:
            return
        val = KiConf._look_env_var(name, old, only_old, ki6_diff, no_dir)
        if val is not None:
            setattr(KiConf, member, val)
        else:
            val = guesser()
            if val:
                setattr(KiConf, member, val)
                KiConf._set_env_var(name, val, ki6_diff, no_dir)
                if old:
                    KiConf.kicad_env[old] = val
                    os.environ[old] = val
            else:
                logger.warning(W_NOLIBS + 'Unable to find KiCad '+desc)
        return val

    def load_kicad_common():
        # Try to figure out KiCad configuration file
        cfg = KiConf.find_kicad_common()
        if cfg and os.path.isfile(cfg):
            # Get the environment variables
            logger.debug('Reading KiCad config from `{}`'.format(cfg))
            KiConf.config_dir = os.path.dirname(cfg)
            if GS.ki5:
                # All environment vars should be here
                KiConf.load_ki5_env(cfg)
            else:
                # Only the user defined environment vars are here
                KiConf.load_ki6_env(cfg)
        # Now make sure we have all the needed variables
        KiConf._solve_var('SYMBOL', 'sym_lib_dir', 'libraries', KiConf.guess_symbol_dir)
        KiConf._solve_var('TEMPLATE', 'template_dir', 'templates', KiConf.guess_template_dir)
        KiConf._solve_var('USER_TEMPLATE', 'user_template_dir', 'user templates', KiConf.guess_user_template_dir,
                          ki6_diff=False)
        KiConf._solve_var('FOOTPRINT', 'footprint_dir', 'footprints', KiConf.guess_footprint_dir, old='KISYSMOD')
        KiConf._solve_var('3DMODEL', 'models_3d_dir', '3D models', KiConf.guess_3d_dir, old='KISYS3DMOD', only_old=True)
        KiConf._solve_var('3RD_PARTY', 'party_3rd_dir', '3rd party', KiConf.guess_3rd_dir, only_k6=True, no_dir=True)
        # Export the rest. KiCad2Step needs them
        to_add = {}
        for k, v in KiConf.kicad_env.items():
            if k not in os.environ:
                os.environ[k] = v
                logger.debug('Exporting {}="{}"'.format(k, v))
            m = re.match(r'KICAD(\d+)_(.*)', k)
            if m:
                for n in range(6, GS.kicad_version_major+1):
                    kv = 'KICAD'+str(n)+'_'+m.group(2)
                    if kv not in os.environ and kv not in KiConf.kicad_env and kv not in to_add:
                        os.environ[kv] = v
                        to_add[kv] = v
                        logger.debug('Also exporting {}="{}"'.format(kv, v))
        KiConf.kicad_env.update(to_add)

    def load_lib_aliases(fname, lib_aliases):
        if not os.path.isfile(fname):
            return False
        logger.debug('Loading symbols lib table `{}`'.format(fname))
        version = 0
        with open(fname, 'rt') as f:
            error = None
            try:
                table = load(f)[0]
            except SExpData as e:
                error = str(e)
            if error:
                raise KiPlotConfigurationError('Error loading `{}`: {}'.format(fname, error))
        if not isinstance(table, list) or (table[0].value() != 'sym_lib_table' and table[0].value() != 'fp_lib_table'):
            raise KiPlotConfigurationError('Error loading `{}`: not a library table'.format(fname))
        for e in table[1:]:
            e_type = _check_is_symbol_list(e)
            if e_type == 'version':
                version = _check_integer(e, 1, e_type)
                if version > SUP_VERSION:
                    logger.warning(W_LIBTVERSION+"Unsupported lib table version, loading could fail")
            elif e_type == 'lib':
                alias = LibAlias.parse(e, KiConf.kicad_env, {})
                if GS.debug_level > 1:
                    logger.debug('- Adding lib alias '+str(alias))
                lib_aliases[alias.name] = alias
            else:
                logger.warning(W_LIBTUNK+"Unknown lib table entry `{}`".format(e_type))
        return True

    def load_all_lib_aliases(table_name, sys_dir, pattern):
        # Load the default symbol libs table.
        # This is the list of libraries enabled by the user.
        loaded = False
        lib_aliases = {}
        if KiConf.config_dir:
            conf_dir = KiConf.config_dir
            if 'KICAD_CONFIG_HOME' in KiConf.kicad_env:
                # KiCad 5 unintentionally allows it, is a bug, and won't be fixed:
                # https://forum.kicad.info/t/kicad-config-home-inconsistencies-and-detail/26875
                conf_dir = KiConf.kicad_env['KICAD_CONFIG_HOME']
                logger.debug('Redirecting symbols lib table to '+conf_dir)
            loaded = KiConf.load_lib_aliases(os.path.join(conf_dir, table_name), lib_aliases)
        if not loaded and 'KICAD_TEMPLATE_DIR' in KiConf.kicad_env:
            loaded = KiConf.load_lib_aliases(os.path.join(KiConf.kicad_env['KICAD_TEMPLATE_DIR'], table_name), lib_aliases)
        if not loaded:
            if not GS.ci_cd_detected:
                logger.warning(W_NODEFSYMLIB + 'Missing default symbol library table')
            # No default symbol libs table, try to create one
            if KiConf.sym_lib_dir:
                for f in glob(os.path.join(sys_dir, pattern)):
                    alias = LibAlias()
                    alias.name = os.path.splitext(os.path.basename(f))[0]
                    alias.uri = f
                    if GS.debug_level > 1:
                        logger.debug('Detected lib alias '+str(alias))
                    lib_aliases[alias.name] = alias
        # Load the project's table
        KiConf.load_lib_aliases(os.path.join(KiConf.dirname, table_name), lib_aliases)
        return lib_aliases

    def get_sym_lib_aliases(fname=None):
        if KiConf.lib_aliases is None:
            if fname is None:
                fname = GS.sch_file
            KiConf.init(fname)
            pattern = '*.kicad_sym' if GS.ki6 else '*.lib'
            KiConf.lib_aliases = KiConf.load_all_lib_aliases(SYM_LIB_TABLE, KiConf.sym_lib_dir, pattern)
        return KiConf.lib_aliases

    def get_fp_lib_aliases(fname=None):
        if KiConf.fp_aliases is None:
            if fname is None:
                fname = GS.pcb_file
            KiConf.init(fname)
            KiConf.fp_aliases = KiConf.load_all_lib_aliases(FP_LIB_TABLE, KiConf.footprint_dir, '*.pretty')
        return KiConf.fp_aliases

    def check_fp_lib_table(fname=None):
        if fname is None:
            fname = GS.pcb_file
        KiConf.check_lib_table(fname, FP_LIB_TABLE)

    def check_sym_lib_table(fname=None):
        if fname is None:
            fname = GS.sch_file
        KiConf.check_lib_table(fname, SYM_LIB_TABLE)

    def check_lib_table(fname, table_name):
        KiConf.init(fname)
        if KiConf.config_dir:
            fp_name = os.path.join(KiConf.config_dir, table_name)
            if not os.path.isfile(fp_name):
                # No global fp lib table
                global_fp_name = os.path.join(KiConf.template_dir, table_name) if KiConf.template_dir else None
                if global_fp_name and os.path.isfile(global_fp_name):
                    # Try to copy the template
                    if not GS.ci_cd_detected:
                        logger.warning(f'{W_MISLIBTAB}Missing default system footprint table {table_name},'
                                       ' copying the template')
                    logger.debug(f'Copying {global_fp_name} to {fp_name}')
                    copy2(global_fp_name, fp_name)
                    atexit.register(KiConf.remove_lib_table, fp_name)

    def remove_lib_table(fname):
        if os.path.isfile(fname):
            logger.debug('Removing '+fname)
            os.remove(fname)

    def save_fp_lib_aliases(fname, aliases, is_fp=True):
        logger.debug(f'Writing lib table `{fname}`')
        table = [Symbol('fp_lib_table' if is_fp else 'sym_lib_table'), Sep()]
        for name in sorted(aliases.keys(), key=str.casefold):
            alias = aliases[name]
            cnt = [[Symbol('name'), alias.name],
                   [Symbol('type'), alias.type],
                   [Symbol('uri'), alias.uri]]
            if alias.options is not None:
                cnt.append([Symbol('options'), alias.options])
            if alias.descr is not None:
                cnt.append([Symbol('descr'), alias.descr])
            table.append([Symbol('lib')] + cnt)
            table.append(Sep())
        with open(fname, 'wt') as f:
            f.write(dumps(table))
            f.write('\n')

    def fp_nick_to_path(nick):
        fp_aliases = KiConf.get_fp_lib_aliases()
        alias = fp_aliases.get(str(nick))  # UTF8 -> str
        return alias

    def load_3d_aliases():
        if not KiConf.config_dir:
            return
        fname = os.path.join(KiConf.config_dir, '3d', '3Dresolver.cfg')
        if not os.path.isfile(fname):
            logger.debug('No 3D aliases ({})'.format(fname))
            return
        logger.debug('Loading 3D aliases from '+fname)
        with open(fname) as f:
            reader = csv.reader(f)
            head = next(reader)
            if len(head) != 1 or head[0] != '#V1':
                logger.warning(W_3DRESVER, 'Unsupported 3D resolver version ({})'.format(head))
            for r in reader:
                if len(r) != 3:
                    logger.non_critical_error(f"3D resolver doesn't contain three values ({r})")
                    continue
                name = parse_len_str(r[0])
                value = parse_len_str(r[1])
                # Discard the comment (2)
                logger.debugl(1, '- {}={}'.format(name, value))
                KiConf.aliases_3D[name] = value
        logger.debugl(1, 'Finished loading 3D aliases')

    def fix_page_layout_k6_key(key, data, dest_dir, forced, no_copy_embedded, is_pcb):
        if key in data:
            section = data[key]
            pl = section.get('page_layout_descr_file', None) if not forced else forced
            if pl:
                if pl.startswith(EMBED_PREFIX):
                    if no_copy_embedded:
                        return pl
                    if is_pcb:
                        if GS.pcb_file:
                            from .pcb import get_embedded_file
                            fname = get_embedded_file(GS.pcb_file, pl)
                        else:
                            logger.debug("** Not patching the PCB worksheet because we don't have a PCB")
                            return pl
                    else:
                        if GS.sch:
                            fname = GS.sch.get_embedded_file(pl)
                        else:
                            logger.debug("** Not patching the SCH worksheet because we don't have a SCH")
                            return pl
                else:
                    fname = fix_windows(KiConf.expand_env(pl, ref_dir=GS.pro_dir or (GS.pcb_dir if is_pcb else GS.sch_dir)))
                if os.path.isfile(fname):
                    dest = os.path.join(dest_dir, key+'.kicad_wks')
                    logger.debug(f'Copying {fname} -> {dest}')
                    copy2(fname, dest)
                    data[key]['page_layout_descr_file'] = key+'.kicad_wks'
                    logger.debug(f'Replacing page layout {pl} -> {key}.kicad_wks')
                    return dest
                else:
                    GS.exit_with_error('Missing page layout file: '+fname, MISSING_WKS)
        return None

    def fix_page_layout_k6(project, dry, force_sch, force_pcb, no_copy_embedded):
        # Get the current definitions
        dest_dir = os.path.dirname(project)
        with open(project, 'rt') as f:
            pro_text = f.read()
        data = json.loads(pro_text)
        layouts = [None, None]
        if not dry:
            layouts[1] = KiConf.fix_page_layout_k6_key('pcbnew', data, dest_dir, force_pcb, no_copy_embedded, is_pcb=True)
            layouts[0] = KiConf.fix_page_layout_k6_key('schematic', data, dest_dir, force_sch, no_copy_embedded, is_pcb=False)
            logger.debug(f'Saving modified project to {project}')
            with open(project, 'wt') as f:
                f.write(json.dumps(data, sort_keys=True, indent=2))
        else:
            aux = data.get('schematic', None)
            if aux:
                layouts[0] = fix_windows(KiConf.expand_env(aux.get('page_layout_descr_file', None), ref_dir=dest_dir))
            aux = data.get('pcbnew', None)
            if aux:
                layouts[1] = fix_windows(KiConf.expand_env(aux.get('page_layout_descr_file', None), ref_dir=dest_dir))
        return layouts

    def fix_page_layout_k5(project, dry, force_sch, force_pcb):
        order = 1
        dest_dir = os.path.dirname(project)
        with open(project, 'rt') as f:
            lns = f.readlines()
        is_pcb_new = False
        layouts = [None, None]
        for c, line in enumerate(lns):
            if line.startswith('[pcbnew]'):
                is_pcb_new = True
            if line.startswith('[schematic'):
                is_pcb_new = False
            if line.startswith('PageLayoutDescrFile='):
                fname = line[20:].strip()
                if force_sch and not is_pcb_new:
                    dest = force_sch
                elif force_pcb and is_pcb_new:
                    dest = force_pcb
                elif fname:
                    fname = fix_windows(KiConf.expand_env(fname))
                    if os.path.isfile(fname):
                        dest = os.path.join(dest_dir, str(order)+'.kicad_wks')
                        if not dry:
                            copy2(fname, dest)
                            layouts[is_pcb_new] = dest
                        else:
                            layouts[is_pcb_new] = fname
                        dest = str(order)+'.kicad_wks'
                        order = order+1
                    else:
                        GS.exit_with_error('Missing page layout file: '+fname, MISSING_WKS)
                else:
                    dest = ''
                if dest or fname:
                    logger.debug(f'Replacing page layout {fname} -> {dest}')
                lns[c] = f'PageLayoutDescrFile={dest}\n'
        if not dry:
            logger.debug(f'Saving modified project to {project}')
            with open(project, 'wt') as f:
                lns = f.writelines(lns)
        return layouts

    def fix_page_layout(project, dry=False, force_sch=None, force_pcb=None, no_copy_embedded=False):
        """ When we copy the project the page layouts must be also copied.
            After copying the project to another destination we have wrong relative references to the WKSs.
            We copy these files and patch the project so the files are named in a simple way.
            In addition we can use this function to force the names of the page layouts. """
        if not project:
            return None, None
        KiConf.init(GS.pcb_file or GS.sch_file)
        if GS.ki5:
            return KiConf.fix_page_layout_k5(project, dry, force_sch, force_pcb)
        return KiConf.fix_page_layout_k6(project, dry, force_sch, force_pcb, no_copy_embedded)

    def expand_env(name, used_extra=None, ref_dir=None):
        if used_extra is None:
            used_extra = [False]
        if not name or name.startswith(EMBED_PREFIX):
            return name
        expanded = expand_env(un_quote(name), KiConf.kicad_env, GS.load_pro_variables(), used_extra)
        # Don't try to get the absolute path for something that starts with a variable that we couldn't expand
        if ref_dir is None:
            ref_dir = os.getcwd()
        return expanded if expanded.startswith('${') else os.path.normpath(os.path.join(ref_dir, expanded))


# Avoid circular inclusion
GS.fix_page_layout = KiConf.fix_page_layout
