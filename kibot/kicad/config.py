# -*- coding: utf-8 -*-
# Copyright (c) 2020 Salvador E. Tropea
# Copyright (c) 2020 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
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
from __future__ import annotations
import os
import re
import sys
import json
from io import StringIO
from glob import glob
import platform
import sysconfig
from ..gs import GS
from .. import log
from ..misc import W_NOCONFIG, W_NOKIENV, W_NOLIBS, W_NODEFSYMLIB

# Check python version to determine which version of ConfirParser to import
if sys.version_info.major >= 3:
    import configparser as ConfigParser
else:  # pragma: no cover (Py2)
    # For future Python 2 support
    import ConfigParser  # type:ignore[no-redef]

logger = log.get_logger()
SYM_LIB_TABLE = 'sym-lib-table'
KICAD_COMMON = 'kicad_common'


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


def expand_env(val, env):
    """ Expand KiCad environment variables """
    for var in re.findall(r'\$\{(\S+)\}', val):
        if var in env:
            val = val.replace('${'+var+'}', env[var])
        else:
            logger.error('Unable to expand `{}` in `{}`'.format(var, val))
    return val


class LibAlias(object):
    """ An entry for the symbol libs table """
    libs_re = re.compile(r'\(name\s+(\S+|"(?:[^"]|\\")+")\)\s*\(type\s+(\S+|"(?:[^"]|\\")+")\)'
                         r'\s*\(uri\s+(\S+|"(?:[^"]|\\")+")\)\s*\(options\s+(\S+|"(?:[^"]|\\")+")\)'
                         r'\s*\(descr\s+(\S+|"(?:[^"]|\\")+")\)')

    def __init__(self):
        super().__init__()
        self.name = None
        self.legacy = True
        self.uri = None
        self.options = None
        self.descr = None

    @staticmethod
    def parse(options, cline, env):
        m = LibAlias.libs_re.match(options)
        if not m:
            raise KiConfError('Malformed lib entry', SYM_LIB_TABLE, cline, options)
        lib = LibAlias()
        lib.name = un_quote(m.group(1))
        lib.legacy = m.group(2) == 'Legacy'
        lib.uri = os.path.abspath(expand_env(un_quote(m.group(3)), env))
        lib.options = un_quote(m.group(4))
        lib.descr = un_quote(m.group(5))
        return lib

    def __str__(self):
        if not self.name:
            return 'unnamed LibAlias'
        return '`'+self.name+'` -> `'+self.uri+'`'


class KiConf(object):
    """ Class to load and hold all KiCad configuration """
    loaded = False
    config_dir = None    ## type: str
    dirname = None       ## type: str
    sym_lib_dir = None   ## type: str
    template_dir = None  ## type: str
    kicad_env = {}
    lib_aliases = {}

    def __init__(self):
        assert False, "KiConf is fully static, no instances allowed"

    @staticmethod
    def init(fname: str):
        """ fname is the base project name, any extension is allowed.
            So it can be the main schematic, the PCB or the project. """
        if KiConf.loaded:
            return
        d = os.path.dirname(fname)
        KiConf.dirname = d if d is not None else ""
        KiConf.kicad_env['KIPRJMOD'] = KiConf.dirname
        KiConf.load_kicad_common()
        KiConf.load_all_lib_aliases()
        KiConf.loaded = True

    @staticmethod
    def find_kicad_common():
        """ Looks for kicad_common config file.
            Returns its name or None. """
        cfg = ''
        if GS.kicad_conf_path:
            cfg = os.path.join(GS.kicad_conf_path, KICAD_COMMON)
            if GS.ki6():
                cfg += '.json'
            if os.path.isfile(cfg):
                return cfg
        logger.warning(W_NOCONFIG + 'Unable to find KiCad configuration file ({})'.format(cfg))
        return None

    @staticmethod
    def guess_kicad_data_dir(data_dir: str, env_var: str):
        """ Tries to figure out where libraries are.
            Only used if we failed to find the kicad_common file. """
        dir = os.environ.get(env_var)
        if dir and os.path.isdir(dir):
            return dir
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

    @staticmethod
    def guess_symbol_dir():
        if GS.ki5():
            order = ['library', 'symbols']
        else:
            order = ['symbols', 'library']
        guess = KiConf.guess_kicad_data_dir(order[0], 'KICAD_SYMBOL_DIR')
        if guess is None:
            guess = KiConf.guess_kicad_data_dir(order[1], 'KICAD_SYMBOL_DIR')
        return guess

    @staticmethod
    def guess_footprint_dir():
        if GS.ki5():
            order = ['modules', 'footprints']
        else:
            order = ['footprints', 'modules']
        guess = KiConf.guess_kicad_data_dir(order[0], 'KICAD_FOOTPRINT_DIR')
        if guess is None:
            guess = KiConf.guess_kicad_data_dir(order[1], 'KICAD_FOOTPRINT_DIR')
        return guess

    @staticmethod
    def guess_template_dir():
        return KiConf.guess_kicad_data_dir('template', 'KICAD_TEMPLATE_DIR')

    @staticmethod
    def guess_3d_dir():
        modules3d = os.path.join('modules', 'packages3d')
        if GS.ki5():
            order = [modules3d, '3dmodels']
        else:
            order = ['3dmodels', modules3d]
        guess = KiConf.guess_kicad_data_dir(order[0], 'KISYS3DMOD')
        if guess is None:
            guess = KiConf.guess_kicad_data_dir(order[1], 'KISYS3DMOD')
        return guess

    @staticmethod
    def load_ki5_env(cfg: str):
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

    @staticmethod
    def load_ki6_env(cfg: str):
        """ Environment vars from KiCad 6 configuration """
        with open(cfg, 'rt') as f:
            data = json.load(f)
        if "environment" in data and 'vars' in data['environment'] and (data['environment']['vars'] is not None):
            for k, v in data['environment']['vars'].items():
                if GS.debug_level > 1:
                    logger.debug('- KiCad var: {}="{}"'.format(k, v))
                KiConf.kicad_env[k] = v
        else:
            logger.warning(W_NOKIENV + 'KiCad config without environment.vars section')

    @staticmethod
    def load_kicad_common():
        # Try to figure out KiCad configuration file
        cfg = KiConf.find_kicad_common()
        if cfg and os.path.isfile(cfg):
            logger.debug('Reading KiCad config from `{}`'.format(cfg))
            KiConf.config_dir = os.path.dirname(cfg)
            if GS.ki5():
                KiConf.load_ki5_env(cfg)
            else:
                KiConf.load_ki6_env(cfg)
        if 'KICAD_SYMBOL_DIR' in KiConf.kicad_env:
            KiConf.sym_lib_dir = KiConf.kicad_env['KICAD_SYMBOL_DIR']
        else:
            sym_dir = KiConf.guess_symbol_dir()
            if sym_dir:
                KiConf.kicad_env['KICAD_SYMBOL_DIR'] = sym_dir
                KiConf.sym_lib_dir = sym_dir
                logger.debug('Detected KICAD_SYMBOL_DIR="{}"'.format(sym_dir))
            else:
                logger.warning(W_NOLIBS + 'Unable to find KiCad libraries')
        if 'KICAD_TEMPLATE_DIR' in KiConf.kicad_env:
            KiConf.template_dir = KiConf.kicad_env['KICAD_TEMPLATE_DIR']
        else:
            template_dir = KiConf.guess_template_dir()
            if template_dir:
                KiConf.kicad_env['KICAD_TEMPLATE_DIR'] = template_dir
                KiConf.template_dir = template_dir
                logger.debug('Detected KICAD_TEMPLATE_DIR="{}"'.format(template_dir))
            else:
                logger.warning(W_NOLIBS + 'Unable to find KiCad templates')
        # If we couldn't get KISYS3DMOD from configuration and KISYS3DMOD isn't defined in the environment
        # OR the 3D config dir is missing.
        if (('KISYS3DMOD' not in KiConf.kicad_env and 'KISYS3DMOD' not in os.environ) or
           (cfg is not None and not os.path.isdir(cfg.replace(KICAD_COMMON, '3d')))):
            ki_sys_3d_mod = None
            try:
                ki_sys_3d_mod = KiConf.kicad_env['KISYS3DMOD']
            except KeyError:
                ki_sys_3d_mod = KiConf.guess_3d_dir()
            if ki_sys_3d_mod is not None:
                os.environ['KISYS3DMOD'] = ki_sys_3d_mod
                KiConf.kicad_env['KISYS3DMOD'] = ki_sys_3d_mod
                logger.debug('Exporting KISYS3DMOD="{}"'.format(ki_sys_3d_mod))
            else:
                logger.warning(W_NOLIBS + 'Unable to find KiCad 3D modules')
        # Extra magic variables defined by KiCad 6
        if GS.ki6():
            # Schematic symbols
            aux = os.environ.get('KICAD6_SYMBOL_DIR')
            if aux is None:
                aux = KiConf.kicad_env.get('KICAD_SYMBOL_DIR')
            if aux is not None:
                KiConf.kicad_env['KICAD6_SYMBOL_DIR'] = aux
                logger.debug('Exporting KICAD6_SYMBOL_DIR="{}"'.format(aux))
                os.environ['KICAD6_SYMBOL_DIR'] = aux
            # 3D models
            aux = os.environ.get('KICAD6_3DMODEL_DIR')
            if aux is None:
                aux = KiConf.kicad_env.get('KISYS3DMOD')
            if aux is not None:
                KiConf.kicad_env['KICAD6_3DMODEL_DIR'] = aux
                logger.debug('Exporting KICAD6_3DMODEL_DIR="{}"'.format(aux))
                os.environ['KICAD6_3DMODEL_DIR'] = aux
            # Templates
            aux = os.environ.get('KICAD6_TEMPLATE_DIR')
            if aux is None:
                aux = KiConf.kicad_env.get('KICAD_TEMPLATE_DIR')
            if aux is not None:
                KiConf.kicad_env['KICAD6_TEMPLATE_DIR'] = aux
                logger.debug('Exporting KICAD6_TEMPLATE_DIR="{}"'.format(aux))
                os.environ['KICAD6_TEMPLATE_DIR'] = aux
            # Footprints
            aux = os.environ.get('KICAD6_FOOTPRINT_DIR')
            if aux is None:
                aux = KiConf.guess_footprint_dir()
            if aux is not None:
                KiConf.kicad_env['KICAD6_FOOTPRINT_DIR'] = aux
                logger.debug('Exporting KICAD6_FOOTPRINT_DIR="{}"'.format(aux))
                os.environ['KICAD6_FOOTPRINT_DIR'] = aux

    @staticmethod
    def load_lib_aliases(fname: str):
        if not os.path.isfile(fname):
            return False
        logger.debug('Loading symbols lib table `{}`'.format(fname))
        with open(fname, 'rt') as f:
            line = f.readline().strip()
            if line != '(sym_lib_table':
                raise KiConfError('Symbol libs table missing signature', SYM_LIB_TABLE, 1, line)
            line = f.readline()
            cline = 2
            while line and line[0] != ')':
                m = re.match(r'\s*\(lib\s*(.*)\)', line)
                if m:
                    alias = LibAlias.parse(m.group(1), cline, KiConf.kicad_env)
                    if GS.debug_level > 1:
                        logger.debug('- Adding lib alias '+str(alias))
                    KiConf.lib_aliases[alias.name] = alias
                else:
                    raise KiConfError('Unknown symbol table entry', SYM_LIB_TABLE, cline, line)
                line = f.readline()
                cline += 1
        return True

    @staticmethod
    def load_all_lib_aliases():
        # Load the default symbol libs table.
        # This is the list of libraries enabled by the user.
        loaded = False
        if KiConf.config_dir:
            conf_dir = KiConf.config_dir
            if 'KICAD_CONFIG_HOME' in KiConf.kicad_env:
                # KiCad 5 unintentionally allows it, is a bug, and won't be fixed:
                # https://forum.kicad.info/t/kicad-config-home-inconsistencies-and-detail/26875
                conf_dir = KiConf.kicad_env['KICAD_CONFIG_HOME']
                logger.debug('Redirecting symbols lib table to '+conf_dir)
            loaded = KiConf.load_lib_aliases(os.path.join(conf_dir, SYM_LIB_TABLE))
        if not loaded and 'KICAD_TEMPLATE_DIR' in KiConf.kicad_env:
            loaded = KiConf.load_lib_aliases(os.path.join(KiConf.kicad_env['KICAD_TEMPLATE_DIR'], SYM_LIB_TABLE))
        if not loaded:
            logger.warning(W_NODEFSYMLIB + 'Missing default symbol library table')
            # No default symbol libs table, try to create one
            if KiConf.sym_lib_dir:
                for f in glob(os.path.join(KiConf.sym_lib_dir, '*.lib')):
                    alias = LibAlias()
                    alias.name = os.path.splitext(os.path.basename(f))[0]
                    alias.uri = f
                    if GS.debug_level > 1:
                        logger.debug('Detected lib alias '+str(alias))
                    KiConf.lib_aliases[alias.name] = alias
        # Load the project's table
        KiConf.load_lib_aliases(os.path.join(KiConf.dirname, SYM_LIB_TABLE))

    @staticmethod
    def expand_env(name: str):
        return os.path.abspath(expand_env(un_quote(name), KiConf.kicad_env))
