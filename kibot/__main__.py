# -*- coding: utf-8 -*-
# Copyright (c) 2020-2021 Salvador E. Tropea
# Copyright (c) 2020-2021 Instituto Nacional de Tecnología Industrial
# Copyright (c) 2018 John Beard
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
# Adapted from: https://github.com/johnbeard/kiplot
"""KiBot: KiCad automation tool for documents generation

Usage:
  kibot [-b BOARD] [-e SCHEMA] [-c CONFIG] [-d OUT_DIR] [-s PRE]
         [-q | -v...] [-i] [-C] [-m MKFILE] [-g DEF]... [TARGET...]
  kibot [-v...] [-b BOARD] [-e SCHEMA] [-c PLOT_CONFIG] --list
  kibot [-v...] [-b BOARD] [-d OUT_DIR] [-p | -P] --example
  kibot [-v...] --help-filters
  kibot [-v...] --help-list-outputs
  kibot [-v...] --help-output=HELP_OUTPUT
  kibot [-v...] --help-outputs
  kibot [-v...] --help-preflights
  kibot -h | --help
  kibot --version

Arguments:
  TARGET    Outputs to generate, default is all

Options:
  -h, --help                       Show this help message and exit
  -b BOARD, --board-file BOARD     The PCB .kicad-pcb board file
  -c CONFIG, --plot-config CONFIG  The plotting config file to use
  -C, --cli-order                  Generate outputs using the indicated order
  -d OUT_DIR, --out-dir OUT_DIR    The output directory [default: .]
  -e SCHEMA, --schematic SCHEMA    The schematic file (.sch)
  -g DEF, --global-redef DEF       Overwrite a global value (VAR=VAL)
  --help-filters                   List supported filters and details
  --help-list-outputs              List supported outputs
  --help-output HELP_OUTPUT        Help for this particular output
  --help-outputs                   List supported outputs and details
  --help-preflights                List supported preflights and details
  -i, --invert-sel                 Generate the outputs not listed as targets
  -l, --list                       List available outputs (in the config file)
  -m MKFILE, --makefile MKFILE     Generate a Makefile (no targets created)
  -p, --copy-options               Copy plot options from the PCB file
  -P, --copy-and-expand            As -p but expand the list of layers
  -q, --quiet                      Remove information logs
  -s PRE, --skip-pre PRE           Skip preflights, comma separated or `all`
  -v, --verbose                    Show debugging information
  -V, --version                    Show program's version number and exit
  -x, --example                    Create a template configuration file.

"""
from __future__ import annotations
__author__ = 'Salvador E. Tropea, John Beard'
__copyright__ = 'Copyright 2018-2021, Salvador E. Tropea/INTI/John Beard'
__credits__ = ['Salvador E. Tropea', 'John Beard']
__license__ = 'GPL v3+'
__email__ = 'stropea@inti.gob.ar'
__url__ = 'https://github.com/INTI-CMNB/KiBot/'
__status__ = 'stable'
__version__ = '0.11.0'

import os
import sys
from sys import path as sys_path
import re
import gzip
import locale
from glob import glob
from logging import DEBUG

# Import log first to set the domain
from . import log
log.set_domain('kibot')
logger = log.init()
from .docopt import docopt
from .gs import (GS)
from .misc import (NO_PCB_FILE, NO_SCH_FILE, EXIT_BAD_ARGS, W_VARSCH, W_VARCFG, W_VARPCB, NO_PCBNEW_MODULE,
                   W_NOKIVER, hide_stderr)
from .pre_base import (BasePreFlight)
from .config_reader import (CfgYamlReader, print_outputs_help, print_output_help, print_preflights_help, create_example,
                            print_filters_help)
from .kiplot import (generate_outputs, load_actions, config_output, generate_makefile)
GS.kibot_version = __version__


def list_pre_and_outs(logger, outputs):
    logger.info('Available actions:\n')
    pf = BasePreFlight.get_in_use_objs()
    if len(pf):
        logger.info('Pre-flight:')
        for c in pf:
            logger.info('- '+str(c))
    if len(outputs):
        logger.info('Outputs:')
        for o in outputs:
            # Note: we can't do a `dry` config because some layer and field names can be validated only if we
            # load the schematic and the PCB.
            config_output(o, dry=False)
            logger.info('- '+str(o))


def solve_schematic(a_schematic, a_board_file, config):
    schematic = a_schematic
    if not schematic and a_board_file:
        base = os.path.splitext(a_board_file)[0]
        sch = base+'.sch'
        if os.path.isfile(sch):
            schematic = sch
        else:
            sch = base+'.kicad_sch'
            if os.path.isfile(sch):
                schematic = sch
    if not schematic:
        schematics = glob('*.sch')+glob('*.kicad_sch')
        if len(schematics) == 1:
            schematic = schematics[0]
            logger.info('Using SCH file: '+schematic)
        elif len(schematics) > 1:
            # Look for a schematic with the same name as the config
            if config[0] == '.':
                # Unhide hidden config
                config = config[1:]
            while '.' in config:
                config = os.path.splitext(config)[0]
            sch = config+'.sch'
            if os.path.isfile(sch):
                schematic = sch
            else:
                sch = config+'.kicad_sch'
                if os.path.isfile(sch):
                    schematic = sch
                else:
                    # Look for a schematic with a PCB and/or project
                    for sch in schematics:
                        base = os.path.splitext(sch)[0]
                        if os.path.isfile(base+'.pro') or os.path.isfile(base+'.kicad_pro') or \
                           os.path.isfile(base+'.kicad_pcb'):
                            schematic = sch
                            break
                    else:
                        schematic = schematics[0]
            logger.warning(W_VARSCH + 'More than one SCH file found in current directory.\n'
                           '  Using '+schematic+' if you want to use another use -e option.')
    if schematic and not os.path.isfile(schematic):
        logger.error("Schematic file not found: "+schematic)
        sys.exit(NO_SCH_FILE)
    if schematic:
        schematic = os.path.abspath(schematic)
        logger.debug('Using schematic: `{}`'.format(schematic))
    else:
        logger.debug('No schematic file found')
    return schematic


def solve_config(a_plot_config):
    plot_config = a_plot_config
    if not plot_config:
        plot_configs = glob('*.kibot.yaml')+glob('*.kiplot.yaml')+glob('*.kibot.yaml.gz')
        if len(plot_configs) == 1:
            plot_config = plot_configs[0]
            logger.info('Using config file: '+plot_config)
        elif len(plot_configs) > 1:
            plot_config = plot_configs[0]
            logger.warning(W_VARCFG + 'More than one config file found in current directory.\n'
                           '  Using '+plot_config+' if you want to use another use -c option.')
        else:
            logger.error('No config file found (*.kibot.yaml), use -c to specify one.')
            sys.exit(EXIT_BAD_ARGS)
    if not os.path.isfile(plot_config):
        logger.error("Plot config file not found: "+plot_config)
        sys.exit(EXIT_BAD_ARGS)
    logger.debug('Using configuration file: `{}`'.format(plot_config))
    return plot_config


def check_board_file(board_file):
    if board_file and not os.path.isfile(board_file):
        logger.error("Board file not found: "+board_file)
        sys.exit(NO_PCB_FILE)


def solve_board_file(schematic, a_board_file):
    board_file = a_board_file
    if not board_file and schematic:
        pcb = os.path.splitext(schematic)[0]+'.kicad_pcb'
        if os.path.isfile(pcb):
            board_file = pcb
    if not board_file:
        board_files = glob('*.kicad_pcb')
        if len(board_files) == 1:
            board_file = board_files[0]
            logger.info('Using PCB file: '+board_file)
        elif len(board_files) > 1:
            board_file = board_files[0]
            logger.warning(W_VARPCB + 'More than one PCB file found in current directory.\n'
                           '  Using '+board_file+' if you want to use another use -b option.')
    check_board_file(board_file)
    if board_file:
        logger.debug('Using PCB: `{}`'.format(board_file))
    else:
        logger.debug('No PCB file found')
    return board_file


def set_locale():
    """ Try to set the locale for all the cataegories.
        If it fails try with LC_NUMERIC (the one we need for tests). """
    try:
        locale.setlocale(locale.LC_ALL, '')
        return
    except locale.Error:
        pass
    try:
        locale.setlocale(locale.LC_NUMERIC, '')
        return
    except locale.Error:
        pass


def detect_kicad():
    # Check if we have to run the nightly KiCad build
    nightly = False
    if os.environ.get('KIAUS_USE_NIGHTLY'):  # pragma: no cover (nightly)
        # Path to the Python module
        pcbnew_path = '/usr/lib/kicad-nightly/lib/python3/dist-packages'
        sys_path.insert(0, pcbnew_path)
        # This helps other tools like iBoM to pick-up the right pcbnew module
        if 'PYTHONPATH' in os.environ:
            os.environ['PYTHONPATH'] += ':'+pcbnew_path
        else:
            os.environ['PYTHONPATH'] = pcbnew_path
        nightly = True
    try:
        import pcbnew
    except ImportError:
        logger.error("Failed to import pcbnew Python module."
                     " Is KiCad installed?"
                     " Do you need to add it to PYTHONPATH?")
        sys.exit(NO_PCBNEW_MODULE)
    try:
        GS.kicad_version = pcbnew.GetBuildVersion()
    except AttributeError:
        logger.warning(W_NOKIVER+"Unknown KiCad version, please install KiCad 5.1.6 or newer")
        # Assume the best case
        GS.kicad_version = '5.1.5'
    try:
        # Debian sid may 2021 mess:
        really_index = GS.kicad_version.index('really')
        GS.kicad_version = GS.kicad_version[really_index+6:]
    except ValueError:
        pass

    m = re.search(r'(\d+)\.(\d+)\.(\d+)', GS.kicad_version)
    if m is None:
        logger.error("Unable to detect KiCad version, got: `{}`".format(GS.kicad_version))
        sys.exit(NO_PCBNEW_MODULE)
    GS.kicad_version_major = int(m.group(1))
    GS.kicad_version_minor = int(m.group(2))
    GS.kicad_version_patch = int(m.group(3))
    GS.kicad_version_n = GS.kicad_version_major*1000000+GS.kicad_version_minor*1000+GS.kicad_version_patch
    logger.debug('Detected KiCad v{}.{}.{} ({} {})'.format(GS.kicad_version_major, GS.kicad_version_minor,
                 GS.kicad_version_patch, GS.kicad_version, GS.kicad_version_n))
    # Used to look for plug-ins.
    # KICAD_PATH isn't good on my system.
    # The kicad-nightly package overwrites the regular package!!
    GS.kicad_share_path = '/usr/share/kicad'
    if GS.ki6():
        GS.kicad_conf_path = pcbnew.GetSettingsManager().GetUserSettingsPath()
        if nightly:
            # Nightly Debian packages uses `/usr/share/kicad-nightly/kicad-nightly.env` as an environment extension
            # This script defines KICAD_CONFIG_HOME="$HOME/.config/kicadnightly"
            # So we just patch it, as we patch the name of the binaries
            # No longer needed for 202112021512+6.0.0+rc1+287+gbb08ef2f41+deb11
            # GS.kicad_conf_path = GS.kicad_conf_path.replace('/kicad/', '/kicadnightly/')
            GS.kicad_share_path = GS.kicad_share_path.replace('/kicad/', '/kicad-nightly/')
            GS.kicad_dir = 'kicad-nightly'
        GS.pro_ext = '.kicad_pro'
        # KiCad 6 doesn't support the Rescue layer
        GS.work_layer = 'User.9'
    else:
        # Bug in KiCad (#6989), prints to stderr:
        # `../src/common/stdpbase.cpp(62): assert "traits" failed in Get(test_dir): create wxApp before calling this`
        # Found in KiCad 5.1.8, 5.1.9
        # So we temporarily suppress stderr
        with hide_stderr():
            GS.kicad_conf_path = pcbnew.GetKicadConfigPath()
        GS.pro_ext = '.pro'
        GS.work_layer = 'Rescue'
    # Dirs to look for plugins
    GS.kicad_plugins_dirs = []
    # /usr/share/kicad/*
    GS.kicad_plugins_dirs.append(os.path.join(GS.kicad_share_path, 'scripting'))
    GS.kicad_plugins_dirs.append(os.path.join(GS.kicad_share_path, 'scripting', 'plugins'))
    # ~/.config/kicad/*
    GS.kicad_plugins_dirs.append(os.path.join(GS.kicad_conf_path, 'scripting'))
    GS.kicad_plugins_dirs.append(os.path.join(GS.kicad_conf_path, 'scripting', 'plugins'))
    # ~/.kicad_plugins and ~/.kicad
    if 'HOME' in os.environ:
        home = os.environ['HOME']
        GS.kicad_plugins_dirs.append(os.path.join(home, '.kicad_plugins'))
        GS.kicad_plugins_dirs.append(os.path.join(home, '.kicad', 'scripting'))
        GS.kicad_plugins_dirs.append(os.path.join(home, '.kicad', 'scripting', 'plugins'))
    if GS.debug_level > 1:
        logger.debug('KiCad config path {}'.format(GS.kicad_conf_path))


def main():
    set_locale()
    ver = 'KiBot '+__version__+' - '+__copyright__+' - License: '+__license__
    GS.out_dir_in_cmd_line = '-d' in sys.argv or '--out-dir' in sys.argv
    args = docopt(__doc__, version=ver, options_first=True)

    # Set the specified verbosity
    log.set_verbosity(logger, args.verbose, args.quiet)
    GS.debug_enabled = logger.getEffectiveLevel() <= DEBUG
    GS.debug_level = args.verbose
    # Now we have the debug level set we can check (and optionally inform) KiCad info
    detect_kicad()

    # Parse global overwrite options
    for redef in args.global_redef:
        if '=' not in redef:
            logger.error('Malformed global-redef option, must be VARIABLE=VALUE ({})'.format(redef))
            sys.exit(EXIT_BAD_ARGS)
        var = redef.split('=')[0]
        GS.global_from_cli[var] = redef[len(var)+1:]

    # Output dir: relative to CWD (absolute path overrides)
    GS.out_dir = os.path.join(os.getcwd(), args.out_dir)

    # Load output and preflight plugins
    load_actions()

    if args.help_outputs or args.help_list_outputs:
        print_outputs_help(details=args.help_outputs)
        sys.exit(0)
    if args.help_output:
        print_output_help(args.help_output)
        sys.exit(0)
    if args.help_preflights:
        print_preflights_help()
        sys.exit(0)
    if args.help_filters:
        print_filters_help()
        sys.exit(0)
    if args.example:
        check_board_file(args.board_file)
        if args.copy_options and not args.board_file:
            logger.error('Asked to copy options but no PCB specified.')
            sys.exit(EXIT_BAD_ARGS)
        create_example(args.board_file, GS.out_dir, args.copy_options, args.copy_and_expand)
        sys.exit(0)

    # Determine the YAML file
    plot_config = solve_config(args.plot_config)
    # Determine the SCH file
    GS.set_sch(solve_schematic(args.schematic, args.board_file, plot_config))
    # Determine the PCB file
    GS.set_pcb(solve_board_file(GS.sch_file, args.board_file))

    # Read the config file
    cr = CfgYamlReader()
    outputs = None
    try:
        # The Python way ...
        with gzip.open(plot_config) as cf_file:
            outputs = cr.read(cf_file)
    except OSError:
        pass
    if outputs is None:
        with open(plot_config) as cf_file:
            outputs = cr.read(cf_file)

    # Is just list the available targets?
    if args.list:
        list_pre_and_outs(logger, outputs)
        sys.exit(0)

    if args.makefile:
        # Only create a makefile
        generate_makefile(args.makefile, plot_config, outputs)
    else:
        # Do all the job (pre-flight + outputs)
        generate_outputs(outputs, args.target, args.invert_sel, args.skip_pre, args.cli_order)
    # Print total warnings
    logger.log_totals()


if __name__ == "__main__":
    main()  # pragma: no cover
