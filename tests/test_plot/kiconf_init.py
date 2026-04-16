#!/usr/bin/python3
import os
import sys
import coverage
import logging
import argparse
import re
import pcbnew
from unittest.mock import patch

# Look for the 'utils' module from where the script is running
prev_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if prev_dir not in sys.path:
    sys.path.insert(0, prev_dir)
# One more level for the project
prev_dir = os.path.dirname(prev_dir)
if sys.path[0] != prev_dir:
    try:
        sys.path.remove(prev_dir)
    except ValueError:
        pass
    sys.path.insert(0, prev_dir)

import kibot.log as log
log.set_domain('kibot')
log.warn_all = True
logger = log.init()
logger.setLevel(logging.DEBUG)

# Utils import
from utils import context
from kibot.kicad.config import KiConf
from kibot.gs import GS

GS.debug_level = 3
cov = coverage.Coverage()

parser = argparse.ArgumentParser(description='KiConf tester')
parser.add_argument('--no_conf_path', help='Do not use the configuration path', action='store_true')
parser.add_argument('--patch_get_path', help='Make sysconfig.get_path fail', action='store_true')
args = parser.parse_args()

GS.kicad_version = pcbnew.GetBuildVersion()
try:
    # Debian sid may 2021 mess:
    really_index = GS.kicad_version.index('really')
    GS.kicad_version = GS.kicad_version[really_index+6:]
except ValueError:
    pass
m = re.search(r'(\d+)\.(\d+)\.(\d+)', GS.kicad_version)
GS.kicad_version_major = int(m.group(1))
GS.kicad_version_minor = int(m.group(2))
GS.kicad_version_patch = int(m.group(3))
GS.kicad_version_n = GS.kicad_version_major*1000000+GS.kicad_version_minor*1000+GS.kicad_version_patch
GS.ki6 = GS.kicad_version_major >= 6
GS.ki5 = GS.kicad_version_major < 6
logger.debug('Detected KiCad v{}.{}.{} ({} {})'.format(GS.kicad_version_major, GS.kicad_version_minor,
             GS.kicad_version_patch, GS.kicad_version, GS.kicad_version_n))

if context.ki5():
    ki_path = pcbnew.GetKicadConfigPath()
else:
    ki_path = pcbnew.SETTINGS_MANAGER.GetUserSettingsPath()
GS.kicad_conf_path = None if args.no_conf_path else ki_path


def do_init():
    KiConf.init(os.path.join(context.BOARDS_DIR, 'v5_errors/kibom-test.sch'))
    # Check we can call it again and nothing is done
    KiConf.init('bogus')
    # Try to load the sym-lib-table
    KiConf.get_sym_lib_aliases()


if args.patch_get_path:
    with context.cover_it(cov):
        old = os.environ.get('KICAD_PATH')
        if old:
            del os.environ['KICAD_PATH']
        with patch("sysconfig.get_path", lambda a, b=None: ''):
            do_init()
        if old:
            os.environ['KICAD_PATH'] = old
else:
    with context.cover_it(cov):
        do_init()
