"""
Tests miscellaneous stuff.

- -s all -i
- -s run_erc,update_xml,run_drc -i
- -s all,run_drc
- -s bogus
- An unknown output type
- -s all and_one_of_two_outs
- Missing schematic
- Wrong PCB name
- Missing PCB
- Missing SCH
- Missing config
- Wrong config name
- Guess the PCB and YAML
- Guess the PCB and YAML when more than one is present
- Guess the SCH and YAML
- Guess the SCH and YAML when more than one is present
- --list
- Create example
  - with PCB
  - already exists
  - Copying
- Load plugin

For debug information use:
pytest-3 --log-cli-level debug
"""
from glob import glob
import os
import re
import shutil
import logging
import pytest
import subprocess
import json
from . import context
from kibot.misc import (EXIT_BAD_ARGS, EXIT_BAD_CONFIG, NO_PCB_FILE, NO_SCH_FILE, EXAMPLE_CFG, WONT_OVERWRITE, CORRUPTED_PCB,
                        PCBDRAW_ERR, NO_PCBNEW_MODULE, NO_YAML_MODULE, INTERNAL_ERROR, MISSING_FILES)


POS_DIR = 'positiondir'
MK_TARGETS = ['position', 'archive', 'interactive_bom', 'run_erc', '3D', 'kibom_internal', 'drill', 'pcb_render',
              'print_front', 'svg_sch_def', 'svg_sch_int', 'pdf_sch_def', 'pdf_sch_int', 'fake_sch', 'update_xml',
              'run_drc']
# Even the Ubuntu builds are slightly different
is_debian = os.path.isfile('/etc/debian_version') and not os.path.isfile('/etc/lsb-release')
# If we are not running on Debian skip the text part at the top of diff PDFs
OFFSET_Y = '0' if is_debian else '80'
DIFF_TOL = 0 if is_debian else 1200
# The 3D models in copy_files
MODELS = ['3d_models/3d/1/test.wrl', '3d_models/3d/2/test.wrl',
          '3d_models/Resistor_SMD.3dshapes/R_0805_2012Metrico.step',
          '3d_models/Resistor_SMD.3dshapes/R_0805_2012Metrico.wrl',
          '3d_models/Capacitor_SMD.3dshapes/C_0805_2012Metric.step',
          '3d_models/Capacitor_SMD.3dshapes/C_0805_2012Metric.wrl',
          '3d_models/Resistor_SMD.3dshapes/R_0805_2012Metric.step',
          '3d_models/Resistor_SMD.3dshapes/R_0805_2012Metric.wrl']


def test_skip_pre_and_outputs(test_dir):
    prj = 'simple_2layer'
    ctx = context.TestContext(test_dir, prj, 'pre_and_position', POS_DIR)
    ctx.run(extra=['-s', 'all', '-i'])
    ctx.dont_expect_out_file(ctx.get_pos_both_csv_filename())
    assert ctx.search_err('Skipping all preflight actions')
    assert ctx.search_err('Skipping all outputs')
    ctx.clean_up()


def test_skip_pre_and_outputs_2(test_dir):
    prj = 'simple_2layer'
    ctx = context.TestContext(test_dir, prj, 'pre_and_position', POS_DIR)
    ctx.run(extra=['-s', 'run_erc,update_xml,run_drc', '-i'])
    ctx.dont_expect_out_file(ctx.get_pos_both_csv_filename())
    assert ctx.search_err('Skipping .?run_erc')
    assert ctx.search_err('Skipping .?run_drc')
    assert ctx.search_err('Skipping .?update_xml')
    assert ctx.search_err('Skipping all outputs')
    ctx.clean_up()


def test_skip_pre_and_outputs_3(test_dir):
    prj = 'simple_2layer'
    ctx = context.TestContext(test_dir, prj, 'pre_and_position', POS_DIR)
    ctx.run(EXIT_BAD_ARGS, extra=['-s', 'all,run_drc'])
    ctx.dont_expect_out_file(ctx.get_pos_both_csv_filename())
    assert ctx.search_err('Use `--skip all`')
    ctx.clean_up()


def test_skip_pre_and_outputs_4(test_dir):
    prj = 'simple_2layer'
    ctx = context.TestContext(test_dir, prj, 'pre_and_position', POS_DIR)
    ctx.run(EXIT_BAD_ARGS, extra=['-s', 'bogus'])
    ctx.dont_expect_out_file(ctx.get_pos_both_csv_filename())
    assert ctx.search_err('Unknown preflight .?bogus')
    ctx.clean_up()


def test_skip_pre_and_outputs_5(test_dir):
    prj = 'simple_2layer'
    ctx = context.TestContext(test_dir, prj, 'pre_skip')
    ctx.run(extra=['-s', 'run_erc,run_drc'])
    assert ctx.search_err('no need to skip')
    ctx.clean_up()


def test_unknown_out_type(test_dir):
    prj = 'simple_2layer'
    ctx = context.TestContext(test_dir, prj, 'unknown_out')
    ctx.run(EXIT_BAD_CONFIG)
    ctx.dont_expect_out_file(ctx.get_pos_both_csv_filename())
    assert ctx.search_err("Unknown output type:? .?bogus")
    ctx.clean_up()


def test_unknown_out_name_1(test_dir):
    prj = 'simple_2layer'
    ctx = context.TestContext(test_dir, prj, 'pre_and_position')
    ctx.run(EXIT_BAD_ARGS, extra=['-s', 'all', '-C', 'pp'])
    assert ctx.search_err("Unknown output/group .?pp")
    ctx.clean_up()


def test_unknown_out_name_2(test_dir):
    prj = 'simple_2layer'
    ctx = context.TestContext(test_dir, prj, 'pre_and_position')
    ctx.run(EXIT_BAD_ARGS, extra=['-s', 'all', 'pp'])
    assert ctx.search_err("Unknown output/group .?pp")
    ctx.clean_up()


def test_select_output(test_dir):
    prj = '3Rs'
    ctx = context.TestContext(test_dir, prj, 'pre_and_position', POS_DIR)
    ctx.run(extra=['-s', 'all', 'pos_ascii'])
    ctx.dont_expect_out_file(ctx.get_pos_both_csv_filename())
    ctx.expect_out_file(ctx.get_pos_both_filename())
    assert ctx.search_err('Skipping (.*)position(.*) output')
    ctx.clean_up()


def test_miss_sch(test_dir):
    prj = 'fail-project'
    ctx = context.TestContext(test_dir, prj, 'pre_and_position')
    ctx.run(EXIT_BAD_ARGS, extra=['pos_ascii'])
    assert ctx.search_err('No SCH file found')
    ctx.clean_up(keep_project=True)


def test_miss_sch_2(test_dir):
    prj = 'fail-project'
    ctx = context.TestContext(test_dir, prj, 'pre_and_position')
    ctx.run(NO_SCH_FILE, no_board_file=True, extra=['-e', 'bogus', 'pos_ascii'])
    assert ctx.search_err('Schematic file not found')
    ctx.clean_up(keep_project=True)


def test_miss_pcb(test_dir):
    prj = '3Rs'
    ctx = context.TestContext(test_dir, prj, 'pre_and_position')
    ctx.board_file = 'bogus'
    ctx.run(NO_PCB_FILE, extra=['-s', 'run_erc,update_xml', 'pos_ascii'])
    assert ctx.search_err('Board file not found')
    ctx.clean_up()


def test_miss_pcb_2(test_dir):
    ctx = context.TestContext(test_dir, '3Rs', 'pre_and_position')
    ctx.run(EXIT_BAD_ARGS, no_board_file=True, extra=['-s', 'run_erc,update_xml', 'pos_ascii'])
    assert ctx.search_err('No PCB file found')
    ctx.clean_up()


def test_miss_yaml(test_dir):
    prj = 'bom'
    ctx = context.TestContext(test_dir, prj, 'pre_and_position')
    ctx.run(EXIT_BAD_ARGS, no_yaml_file=True)
    assert ctx.search_err('No config file')
    ctx.clean_up()


def test_miss_yaml_2(test_dir):
    prj = '3Rs'
    ctx = context.TestContext(test_dir, prj, 'pre_and_position')
    ctx.yaml_file = 'bogus'
    ctx.run(EXIT_BAD_ARGS)
    assert ctx.search_err('Plot config file not found: bogus')
    ctx.clean_up()


def test_auto_pcb_and_cfg_1(test_dir):
    """ Test guessing the PCB and config file.
        Only one them is there. """
    prj = '3Rs'
    ctx = context.TestContext(test_dir, prj, 'pre_and_position', POS_DIR)
    board_file = os.path.basename(ctx.board_file)
    shutil.copy2(ctx.board_file, ctx.get_out_path(board_file))
    yaml_file = os.path.basename(ctx.yaml_file)
    shutil.copy2(ctx.yaml_file, ctx.get_out_path(yaml_file))
    ctx.run(extra=['-s', 'all', '-i', 'pos_ascii'], no_out_dir=True, no_board_file=True, no_yaml_file=True, chdir_out=True)
    ctx.dont_expect_out_file(ctx.get_pos_both_filename())
    ctx.expect_out_file(ctx.get_pos_both_csv_filename())
    assert ctx.search_out('Using PCB file: '+board_file)
    assert ctx.search_out('Using config file: '+yaml_file)
    ctx.clean_up()


def test_auto_pcb_and_cfg_2(test_dir):
    """ Test guessing the PCB and config file.
        Two of them are there. """
    prj = '3Rs'
    ctx = context.TestContext(test_dir, prj, 'pre_and_position', POS_DIR)
    board_file = os.path.basename(ctx.board_file)
    shutil.copy2(ctx.board_file, ctx.get_out_path(board_file))
    shutil.copy2(ctx.board_file, ctx.get_out_path('b_'+board_file))
    yaml_file = os.path.basename(ctx.yaml_file)
    shutil.copy2(ctx.yaml_file, ctx.get_out_path(yaml_file))
    shutil.copy2(ctx.yaml_file, ctx.get_out_path('b_'+yaml_file))
    ctx.run(extra=['-s', 'all', '-i', 'pos_ascii'], no_out_dir=True, no_board_file=True, no_yaml_file=True, chdir_out=True)
    assert ctx.search_err('More than one PCB')
    assert ctx.search_err('More than one config')
    m = ctx.search_err('Using (.*).kicad_pcb')
    assert m
    ctx.board_name = m.group(1)
    ctx.dont_expect_out_file(ctx.get_pos_both_filename())
    ctx.expect_out_file(ctx.get_pos_both_csv_filename())
    ctx.clean_up()


def test_auto_pcb_and_cfg_3(test_dir):
    """ Test guessing the SCH and config file.
        Only one them is there. """
    prj = '3Rs'
    ctx = context.TestContext(test_dir, prj, 'pre_and_position', POS_DIR)
    sch = os.path.basename(ctx.sch_file)
    shutil.copy2(ctx.sch_file, ctx.get_out_path(sch))
    yaml_file = os.path.basename(ctx.yaml_file)
    shutil.copy2(ctx.yaml_file, ctx.get_out_path(yaml_file))
    ctx.run(extra=['-s', 'all', '-i'], no_out_dir=True, no_board_file=True, no_yaml_file=True, chdir_out=True)
    ctx.search_out('Using SCH file: '+sch)
    ctx.search_out('Using config file: '+yaml_file)
    ctx.clean_up()


def test_auto_pcb_and_cfg_4(test_dir):
    """ Test guessing the SCH and config file.
        Two SCHs and one PCB.
        The SCH with same name as the PCB should be selected. """
    prj = '3Rs'
    ctx = context.TestContext(test_dir, prj, 'pre_and_position', POS_DIR)
    sch = os.path.basename(ctx.sch_file)
    shutil.copy2(ctx.sch_file, ctx.get_out_path(sch))
    shutil.copy2(ctx.sch_file, ctx.get_out_path('b_'+sch))
    brd = os.path.basename(ctx.board_file)
    shutil.copy2(ctx.board_file, ctx.get_out_path(brd))
    yaml_file = os.path.basename(ctx.yaml_file)
    shutil.copy2(ctx.yaml_file, ctx.get_out_path(yaml_file))
    ctx.run(extra=['-s', 'all', '-i'], no_out_dir=True, no_board_file=True, no_yaml_file=True, chdir_out=True)
    ctx.search_err('Using ./'+sch)
    ctx.search_out('Using config file: '+yaml_file)
    ctx.clean_up()


def test_auto_pcb_and_cfg_5(test_dir):
    """ Test guessing the SCH and config file.
        Two SCHs. """
    prj = '3Rs'
    ctx = context.TestContext(test_dir, prj, 'pre_and_position')

    sch = os.path.basename(ctx.sch_file)
    shutil.copy2(ctx.sch_file, ctx.get_out_path(sch))
    shutil.copy2(ctx.sch_file, ctx.get_out_path('b_'+sch))
    yaml_file = os.path.basename(ctx.yaml_file)
    shutil.copy2(ctx.yaml_file, ctx.get_out_path(yaml_file))
    ctx.run(extra=['-s', 'all', '-i'], no_out_dir=True, no_board_file=True, no_yaml_file=True, chdir_out=True)
    assert ctx.search_err('Using ./(b_)?'+sch)
    assert ctx.search_out('Using config file: '+yaml_file)
    ctx.clean_up()


def test_list_full(test_dir):
    ctx = context.TestContext(test_dir, '3Rs', 'pre_and_position')
    ctx.run(extra=['--list'], no_verbose=True, no_out_dir=True)
    ctx.search_out(['run_erc: True', 'run_drc: True', 'update_xml: True', r'Pick and place file.? \(position\) \[position\]',
                    r'Pick and place file.? \(pos_ascii\) \[position\]'])
    ctx.clean_up()


def test_list_only_names(test_dir):
    ctx = context.TestContext(test_dir, '3Rs', 'pre_and_position')
    ctx.run(extra=['--list', '--only-names'], no_verbose=True, no_out_dir=True)
    ctx.search_out(['position', 'pos_ascii'])
    ctx.search_out('Pick and place file', invert=True)
    ctx.clean_up()


def test_list_variants(test_dir):
    ctx = context.TestContext(test_dir, '3Rs', 'test_list_variants')
    ctx.run(extra=['--list-variants'], no_verbose=True, no_out_dir=True, no_board_file=True)
    ctx.search_out(['Default variant', 'Production variant', 'Test variant'])
    ctx.clean_up()


def test_help(test_dir):
    ctx = context.TestContext(test_dir, '3Rs', 'pre_and_position')
    ctx.run(extra=['--help'], no_verbose=True, no_out_dir=True, no_yaml_file=True)
    assert ctx.search_out('Usage:')
    assert ctx.search_out('Arguments:')
    assert ctx.search_out('Options:')
    ctx.clean_up()


def test_help_errors(test_dir):
    ctx = context.TestContext(test_dir, '3Rs', 'pre_and_position')
    ctx.run(extra=['--help-errors'], no_verbose=True, no_out_dir=True, no_yaml_file=True, no_board_file=True)
    assert ctx.search_out('1: INTERNAL_ERROR')
    ctx.clean_up()


def test_help_list_rotations(test_dir):
    ctx = context.TestContext(test_dir, '3Rs', 'pre_and_position')
    ctx.run(extra=['--help-list-rotations'], no_verbose=True, no_out_dir=True, no_yaml_file=True, no_board_file=True)
    assert ctx.search_out('SOT-223(.*)180')
    ctx.clean_up()


def test_help_list_offsets(test_dir):
    ctx = context.TestContext(test_dir, '3Rs', 'pre_and_position')
    ctx.run(extra=['--help-list-offsets'], no_verbose=True, no_out_dir=True, no_yaml_file=True, no_board_file=True)
    assert ctx.search_out(r'Footprint\s+Offset X')
    ctx.clean_up()


def test_help_list_outputs(test_dir):
    ctx = context.TestContext(test_dir, '3Rs', 'pre_and_position')
    ctx.run(extra=['--help-list-outputs'], no_verbose=True, no_out_dir=True, no_yaml_file=True, no_board_file=True)
    assert ctx.search_out('Supported outputs')
    assert ctx.search_out('Gerber format')
    ctx.clean_up()


def test_help_output(test_dir):
    ctx = context.TestContext(test_dir, '3Rs', 'pre_and_position')
    ctx.run(extra=['--help-output', 'gerber'], no_verbose=True, no_out_dir=True, no_yaml_file=True, no_board_file=True)
    assert ctx.search_out('Gerber format')
    assert ctx.search_out('Type: .?gerber.?')
    ctx.clean_up()


def test_help_output_unk(test_dir):
    ctx = context.TestContext(test_dir, '3Rs', 'pre_and_position')
    ctx.run(EXIT_BAD_ARGS, extra=['--help-output', 'bogus'], no_verbose=True, no_out_dir=True, no_yaml_file=True,
            no_board_file=True)
    assert ctx.search_err('Unknown output type')
    ctx.clean_up()


def test_help_filters(test_dir):
    ctx = context.TestContext(test_dir, '3Rs', 'pre_and_position')
    ctx.run(extra=['--help-filters'], no_verbose=True, no_out_dir=True, no_yaml_file=True, no_board_file=True)
    assert ctx.search_out('Generic filter')
    ctx.clean_up()


def test_help_variants(test_dir):
    ctx = context.TestContext(test_dir, '3Rs', 'pre_and_position')
    ctx.run(extra=['--help-variants'], no_verbose=True, no_out_dir=True, no_yaml_file=True, no_board_file=True)
    assert ctx.search_out('KiCost variant style')
    ctx.clean_up()


def test_help_global(test_dir):
    ctx = context.TestContext(test_dir, '3Rs', 'pre_and_position')
    ctx.run(extra=['--help-global-options', '--rst'], no_verbose=True, no_out_dir=True, no_yaml_file=True, no_board_file=True)
    assert ctx.search_out('allow_blind_buried_vias')
    ctx.clean_up()


def test_help_output_plugin_1(test_dir, monkeypatch):
    ctx = context.TestContext(test_dir, '3Rs', 'pre_and_position')
    ctx.home_local_link()
    with monkeypatch.context() as m:
        m.setenv("HOME", os.path.join(ctx.get_board_dir(), '../..'))
        logging.debug('HOME='+os.environ['HOME'])
        ctx.run(ret_val=1, extra=['--help-output', 'test'], no_verbose=True, no_out_dir=True, no_yaml_file=True,
                no_board_file=True)
        assert ctx.search_err(r'Undocumented option: .not_documented')
#     assert ctx.search_out(r'- Undocumented')
#     assert ctx.search_out('Description: No description')
#     assert ctx.search_out('Type: .?test.?')
#     assert ctx.search_out('nothing')
#     assert ctx.search_out('chocolate')
#     assert ctx.search_out('`not_documented`: Undocumented')
    ctx.clean_up()


def test_help_output_plugin_2(test_dir, monkeypatch):
    ctx = context.TestContext(test_dir, '3Rs', 'pre_and_position')
    ctx.home_local_link()
    with monkeypatch.context() as m:
        m.setenv("HOME", os.path.join(ctx.get_board_dir(), '../..'))
        logging.debug('HOME='+os.environ['HOME'])
        ctx.run(extra=['--help-output', 'test2'], no_verbose=True, no_out_dir=True, no_yaml_file=True, no_board_file=True)
    assert ctx.search_out('Test for plugin')
    assert ctx.search_out('Type: .?test2.?')
    assert ctx.search_out('todo')
    assert ctx.search_out('frutilla')
    ctx.clean_up()


def test_help_output_plugin_3(test_dir, monkeypatch):
    ctx = context.TestContext(test_dir, '3Rs', 'pre_and_position')
    ctx.home_local_link()
    with monkeypatch.context() as m:
        m.setenv("HOME", os.path.join(ctx.get_board_dir(), '../..'))
        logging.debug('HOME='+os.environ['HOME'])
        ctx.run(extra=['--help-preflights'], no_verbose=True, no_out_dir=True, no_yaml_file=True, no_board_file=True)
    assert ctx.search_out(['- Pre Test', 'A preflight just for testing purposes', r'- \*\*`pre_test`\*\*'])
    ctx.clean_up()


def test_help_output_plugin_4(test_dir, monkeypatch):
    ctx = context.TestContext(test_dir, '3Rs', 'pre_and_position')
    ctx.home_local_link()
    with monkeypatch.context() as m:
        m.setenv("HOME", os.path.join(ctx.get_board_dir(), '../..'))
        logging.debug('HOME='+os.environ['HOME'])
        ctx.run(ret_val=1, extra=['--help-filters'], no_verbose=True, no_out_dir=True, no_yaml_file=True, no_board_file=True)
    assert ctx.search_err(r'Undocumented option: .foo')
    # assert ctx.search_out(r'- \*\*filter_test\*\*: Undocumented')
    ctx.clean_up()


def test_help_outputs_md(test_dir):
    ctx = context.TestContext(test_dir, '3Rs', 'pre_and_position')
    ctx.run(extra=['--help-outputs'], no_verbose=True, no_out_dir=True, no_yaml_file=True, no_board_file=True)
    assert ctx.search_out('Gerber format')
    assert ctx.search_out('Type: .?gerber.?')
    ctx.clean_up()


def test_help_outputs_rst_1(test_dir):
    ctx = context.TestContext(test_dir, '3Rs', 'pre_and_position')
    ctx.run(extra=['--help-outputs', '--rst'], no_verbose=True, no_out_dir=True, no_yaml_file=True, no_board_file=True)
    assert ctx.search_out('Gerber format')
    assert ctx.search_out('Type: .?.?gerber.?.?')
    ctx.clean_up()


def test_help_outputs_rst_2(test_dir):
    """ Separated files """
    ctx = context.TestContext(test_dir, '3Rs', 'pre_and_position')
    ctx.run(extra=['--help-outputs', '--rst'], no_verbose=True, no_yaml_file=True, no_board_file=True)
    ctx.search_out('outputs/gerber')
    ctx.expect_out_file('gerber.rst', sub=True)
    ctx.clean_up()


def test_help_preflights(test_dir):
    ctx = context.TestContext(test_dir, '3Rs', 'pre_and_position')
    ctx.run(extra=['--help-preflights'], no_verbose=True, no_out_dir=True, no_yaml_file=True, no_board_file=True)
    assert ctx.search_out('Supported preflights')
    ctx.clean_up()


def test_example_1(test_dir):
    """ Example without board + Banner """
    ctx = context.TestContext(test_dir, '3Rs', 'pre_and_position')
    ctx.run(extra=['--example', '--banner', '1'], no_verbose=True, no_yaml_file=True, no_board_file=True)
    assert ctx.expect_out_file(EXAMPLE_CFG)
    ctx.clean_up()


def test_example_2(test_dir):
    """ Example with board + Random Banner """
    ctx = context.TestContext(test_dir, 'good-project', 'pre_and_position')
    ctx.run(extra=['--example', '--banner', '-1'], no_verbose=True, no_yaml_file=True)
    assert ctx.expect_out_file(EXAMPLE_CFG)
    ctx.search_in_file(EXAMPLE_CFG, ['layers: all'])
    ctx.clean_up()


def test_example_3(test_dir):
    """ Overwrite error """
    ctx = context.TestContext(test_dir, 'good-project', 'pre_and_position')
    ctx.run(extra=['--example'], no_verbose=True, no_yaml_file=True)
    assert ctx.expect_out_file(EXAMPLE_CFG)
    ctx.run(WONT_OVERWRITE, extra=['--example'], no_verbose=True, no_yaml_file=True)
    ctx.clean_up()


def test_example_4(test_dir):
    """ Expand copied layers """
    ctx = context.TestContext(test_dir, 'good-project', 'pre_and_position')
    ctx.run(extra=['--example', '-P'], no_verbose=True, no_yaml_file=True)
    assert ctx.expect_out_file(EXAMPLE_CFG)
    ctx.search_in_file(EXAMPLE_CFG, ['GND.Cu', 'pen_width: 35.0'])
    ctx.search_not_in_file(EXAMPLE_CFG, ["layer: 'F.Adhes"])
    ctx.clean_up()


def test_example_5(test_dir):
    """ Copy setting from PCB """
    ctx = context.TestContext(test_dir, 'good-project', 'pre_and_position')
    output_dir = os.path.join(ctx.output_dir, 'pp')
    ctx.run(extra=['--example', '-p', '-d', output_dir], no_verbose=True, no_yaml_file=True, no_out_dir=True)
    file = os.path.join('pp', EXAMPLE_CFG)
    assert ctx.expect_out_file(file)
    ctx.search_in_file(file, ['layers: selected', 'pen_width: 35.0'])
    ctx.clean_up()


def test_example_6(test_dir):
    """ Copy setting but no PCB """
    ctx = context.TestContext(test_dir, 'good-project', 'pre_and_position')
    ctx.run(EXIT_BAD_ARGS, extra=['--example', '-p'], no_verbose=True, no_yaml_file=True, no_board_file=True)
    assert ctx.search_err('no PCB specified')
    ctx.clean_up()


def test_example_7(test_dir, monkeypatch):
    """ With dummy plug-ins """
    ctx = context.TestContext(test_dir, '3Rs', 'pre_and_position')
    ctx.home_local_link()
    with monkeypatch.context() as m:
        m.setenv("HOME", os.path.join(ctx.get_board_dir(), '../..'))
        ctx.run(extra=['--example'], no_verbose=True, no_yaml_file=True, no_board_file=True)
    assert ctx.expect_out_file(EXAMPLE_CFG)
    ctx.search_in_file(EXAMPLE_CFG, ['# Undocumented:', "comment: 'No description'"])
    ctx.clean_up()


def test_corrupted_pcb(test_dir):
    prj = 'bom_no_xml'
    ctx = context.TestContext(test_dir, prj, 'print_pcb')
    ctx.run(CORRUPTED_PCB)
    assert ctx.search_err('Error loading PCB file')
    ctx.clean_up()


def test_pcbdraw_fail(test_dir):
    prj = 'bom'
    ctx = context.TestContext(test_dir, prj, 'pcbdraw_fail')
    ctx.run(PCBDRAW_ERR)
    assert ctx.search_err('Cannot locate resource bogus')
    ctx.clean_up()


# This test was designed for `mcpy`.
# `mcpyrate` can pass it using Python 3.8.6, but seems to have problems on the docker image.
# def test_import_fail(test_dir):
#     ctx = context.TestContext(test_dir, '3Rs', 'pre_and_position', POS_DIR)
#     # Create a read only cache entry that we should delete
#     call(['py3compile', 'kibot/out_any_layer.py'])
#     cache_dir = os.path.join('kibot', '__pycache__')
#     cache_file = glob(os.path.join(cache_dir, 'out_any_layer.*'))[0]
#     os.chmod(cache_file, stat.S_IREAD)
#     os.chmod(cache_dir, stat.S_IREAD | stat.S_IEXEC)
#     try:
#         # mcpyrate: not a problem, for Python 3.8.6
#         ret_code = 0
#         # mcpy:
#         # ret_code = WRONG_INSTALL
#         # Run the command
#         ctx.run(ret_code, extra=['--help-list-outputs'], no_out_dir=True, no_yaml_file=True, no_board_file=True)
#     finally:
#         os.chmod(cache_dir, stat.S_IREAD | stat.S_IWRITE | stat.S_IEXEC)
#         os.remove(cache_file)
#     if False:
#         # mcpy
#         assert ctx.search_err('Wrong installation')
#         assert ctx.search_err('Unable to import plug-ins')
#     ctx.clean_up()
#
#
# def test_import_no_fail(test_dir):
#     ctx = context.TestContext(test_dir, '3Rs', 'pre_and_position', POS_DIR)
#     # Create a cache entry that we should delete
#     call(['py3compile', 'kibot/out_any_layer.py'])
#     cache_dir = os.path.join('kibot', '__pycache__')
#     cache_file = glob(os.path.join(cache_dir, 'out_any_layer.*'))[0]
#     try:
#         # Run the command
#         ctx.run(extra=['--help-list-outputs'], no_out_dir=True, no_yaml_file=True, no_board_file=True)
#         if False:
#             # mcpy
#             assert not os.path.isfile(cache_file)
#     finally:
#         if os.path.isfile(cache_file):
#             os.remove(cache_file)
#     ctx.clean_up()


def test_wrong_global_redef(test_dir):
    ctx = context.TestContext(test_dir, '3Rs', 'pre_and_position', POS_DIR)
    ctx.run(EXIT_BAD_ARGS, extra=['--global-redef', 'bogus'])
    assert ctx.search_err('Malformed global-redef option')
    ctx.clean_up()


def test_no_pcbnew(test_dir):
    ctx = context.TestContext(test_dir, 'bom', 'bom')
    cmd = [os.path.abspath(os.path.dirname(os.path.abspath(__file__))+'/force_pcbnew_error.py')]
    ctx.do_run(cmd, NO_PCBNEW_MODULE)
    ctx.search_err('Failed to import pcbnew Python module.')
    ctx.search_err('PYTHONPATH')


def test_old_pcbnew(test_dir):
    ctx = context.TestContext(test_dir, 'bom', 'bom')
    cmd = [os.path.abspath(os.path.dirname(os.path.abspath(__file__))+'/force_pcbnew_error.py'), 'fake']
    ctx.do_run(cmd)
    ctx.search_err('Unknown KiCad version, please install KiCad 5.1.6 or newer')


def test_no_yaml(test_dir):
    ctx = context.TestContext(test_dir, 'bom', 'bom')
    cmd = [os.path.abspath(os.path.dirname(os.path.abspath(__file__))+'/force_yaml_error.py')]
    ctx.do_run(cmd, NO_YAML_MODULE)
    ctx.search_err('No yaml module for Python, install python3-yaml')


def test_no_colorama(test_dir):
    ctx = context.TestContext(test_dir, 'bom', 'bom')
    cmd = [os.path.abspath(os.path.dirname(os.path.abspath(__file__))+'/force_colorama_error.py')]
    ctx.do_run(cmd, use_a_tty=True)
    ctx.search_err(r'\[31m.\[1mERROR:Testing 1 2 3')


def check_test_v5_sch_deps(ctx, deps, extra=(), in_output=False):
    ndeps = 4
    if in_output:
        ndeps -= 1
    assert len(deps) == ndeps+len(extra), deps
    dir = os.path.dirname(ctx.board_file)
    deps_abs = [os.path.abspath(f) for f in deps]
    for sch in ['test_v5'+context.KICAD_SCH_EXT, 'sub-sheet'+context.KICAD_SCH_EXT, 'deeper'+context.KICAD_SCH_EXT]:
        if in_output:
            assert os.path.abspath(ctx.get_out_path(sch)) in deps_abs
        else:
            assert os.path.abspath(os.path.join(dir, sch)) in deps_abs
    for f in extra:
        assert f in deps
    if not in_output:
        assert os.path.relpath(ctx.yaml_file) in deps


def check_makefile(ctx, mkfile, prj, dbg, txt):
    ctx.expect_out_file('Makefile')
    res = ctx.search_in_file('Makefile', [r'DEBUG\?=(.*)', txt])
    assert res[0][0] == dbg, res
    targets = ctx.read_mk_targets(mkfile)
    all = targets['all']
    phony = targets['.PHONY']
    for target in MK_TARGETS:
        assert target in all
        assert target in phony
        assert target in targets
        logging.debug('- Target `'+target+'` in all, .PHONY and itself OK')
    assert 'kibom_external' not in targets
    yaml = os.path.relpath(ctx.yaml_file)
    board_file = os.path.relpath(ctx.board_file)
    # position target
    deps = targets['position'].split(' ')
    assert len(deps) == 2, deps
    assert ctx.get_out_path(os.path.join(POS_DIR, prj+'-top_pos.csv')) in deps
    assert ctx.get_out_path(os.path.join(POS_DIR, prj+'-bottom_pos.csv')) in deps
    deps = targets[targets['position']].split(' ')
    assert len(deps) == 2
    assert board_file in deps
    assert yaml in deps
    logging.debug('- Target `position` OK')
    # interactive_bom target
    deps = targets['interactive_bom'].split(' ')
    assert len(deps) == 1, deps
    assert ctx.get_out_path(os.path.join('ibom', prj+'-ibom.html')) in deps
    deps = targets[targets['interactive_bom']].split(' ')
    assert len(deps) == 3
    assert board_file in deps
    assert yaml in deps
    assert 'tests/board_samples/kicad_5/bom.xml' in deps
    logging.debug('- Target `interactive_bom` OK')
    # pcb_render target
    deps = targets['pcb_render'].split(' ')
    assert len(deps) == 1, deps
    assert ctx.get_out_path(prj+'-top$.svg') in deps
    deps = targets[targets['pcb_render']].split(' ')
    assert len(deps) == 3
    assert board_file in deps
    assert yaml in deps
    assert 'tests/data/html_style.css' in deps
    logging.debug('- Target `pcb_render` OK')
    # print_front target
    deps = targets['print_front'].split(' ')
    assert len(deps) == 1, deps
    assert ctx.get_out_path(prj+'-F_Cu+F_SilkS.pdf') in deps
    deps = targets[targets['print_front']].split(' ')
    assert len(deps) == 2
    assert board_file in deps
    assert yaml in deps
    logging.debug('- Target `print_front` OK')
    # drill target
    deps = targets['drill'].split(' ')
    assert len(deps) == 3, deps
    assert ctx.get_out_path(os.path.join('gerbers', prj+'-drill.drl')) in deps
    assert ctx.get_out_path(os.path.join('gerbers', prj+'-drill_report.txt')) in deps
    assert ctx.get_out_path(os.path.join('gerbers', prj+'-drill_map.pdf')) in deps
    deps = targets[targets['drill']].split(' ')
    assert len(deps) == 2
    assert board_file in deps
    assert yaml in deps
    logging.debug('- Target `drill` OK')
    # svg_sch_def
    deps = targets['svg_sch_def'].split(' ')
    assert len(deps) == 1, deps
    assert ctx.get_out_path(prj+'.svg') in deps
    check_test_v5_sch_deps(ctx, targets[targets['svg_sch_def']].split(' '))
    logging.debug('- Target `svg_sch_def` OK')
    # svg_sch_int
    deps = targets['svg_sch_int'].split(' ')
    assert len(deps) == 1, deps
    assert ctx.get_out_path(prj+'-schematic.svg') in deps
    check_test_v5_sch_deps(ctx, targets[targets['svg_sch_int']].split(' '))
    logging.debug('- Target `svg_sch_int` OK')
    # pdf_sch_def
    deps = targets['pdf_sch_def'].split(' ')
    assert len(deps) == 1, deps
    assert ctx.get_out_path(prj+'.pdf') in deps
    check_test_v5_sch_deps(ctx, targets[targets['pdf_sch_def']].split(' '))
    logging.debug('- Target `pdf_sch_def` OK')
    # boardview
    deps = targets['Board_View_Test'].split(' ')
    assert len(deps) == 1, deps
    assert ctx.get_out_path(prj+'-boardview.brd') in deps
    deps = targets[targets['Board_View_Test']].split(' ')
    assert len(deps) == 2
    assert board_file in deps
    assert yaml in deps
    logging.debug('- Target `Board View Test` OK')
    # pdf_sch_int
    deps = targets['pdf_sch_int'].split(' ')
    assert len(deps) == 1, deps
    assert ctx.get_out_path(prj+'-schematic.pdf') in deps
    check_test_v5_sch_deps(ctx, targets[targets['pdf_sch_int']].split(' '))
    logging.debug('- Target `pdf_sch_int` OK')
    # run_erc target
    deps = targets['run_erc'].split(' ')
    assert len(deps) == 1, deps
    assert ctx.get_out_path(prj+'-erc.txt') in deps
    check_test_v5_sch_deps(ctx, targets[targets['run_erc']].split(' '))
    logging.debug('- Target `run_erc` OK')
    # run_drc target
    deps = targets['run_drc'].split(' ')
    assert len(deps) == 1, deps
    assert ctx.get_out_path(prj+'-drc.txt') in deps
    deps = targets[targets['run_drc']].split(' ')
    assert len(deps) == 2
    assert board_file in deps
    assert yaml in deps
    logging.debug('- Target `run_drc` OK')
    # fake_sch target
    deps = targets['fake_sch'].split(' ')
    if context.ki5():
        # SCHs + 2 libs + symbols table
        assert len(deps) == 6, deps
        extra = [ctx.get_out_path('n.lib'), ctx.get_out_path('y.lib'), ctx.get_out_path('sym-lib-table')]
    else:
        assert len(deps) == 3, deps
        extra = []
    check_test_v5_sch_deps(ctx, deps, extra=extra, in_output=True)
    check_test_v5_sch_deps(ctx, targets[targets['fake_sch']].split(' '))
    logging.debug('- Target `fake_sch` OK')
    # 3D target
    deps = targets['3D'].split(' ')
    assert len(deps) == 1, deps
    assert ctx.get_out_path(os.path.join('3D', prj+'-3D.step')) in deps
    deps = targets[targets['3D']].split(' ')
    assert os.path.relpath(ctx.board_file) in deps
    assert 'tests/data/R_0805_2012Metric.wrl' in deps
    assert yaml in deps
    # We can't check the WRL because it isn't included in the docker image
    logging.debug('- Target `3D` OK')
    # update_xml target
    deps = targets['update_xml'].split(' ')
    assert len(deps) == 1, deps
    assert os.path.abspath(deps[0]) == ctx.board_file.replace('kicad_pcb', 'xml')
    check_test_v5_sch_deps(ctx, targets[targets['update_xml']].split(' '))
    logging.debug('- Target `update_xml` OK')
    # kibom_internal target
    deps = targets['kibom_internal'].split(' ')
    assert len(deps) == 1, deps
    assert ctx.get_out_path(os.path.join('BoM', prj+'-bom.html')) in deps
    check_test_v5_sch_deps(ctx, targets[targets['kibom_internal']].split(' '), [ctx.get_out_path('config.kibom.ini')])
    logging.debug('- Target `kibom_internal` OK')
    # archive target
    deps = targets['archive'].split(' ')
    assert len(deps) == 1, deps
    assert ctx.get_out_path(prj+'-archive.zip') in deps
    deps = targets[targets['archive']].split(' ')
    assert len(deps) == 18, deps
    # - position
    assert ctx.get_out_path(os.path.join(POS_DIR, prj+'-top_pos.csv')) in deps
    assert ctx.get_out_path(os.path.join(POS_DIR, prj+'-bottom_pos.csv')) in deps
    # - interactive_bom
    assert ctx.get_out_path(os.path.join('ibom', prj+'-ibom.html')) in deps
    # - 3D
    assert ctx.get_out_path(os.path.join('3D', prj+'-3D.step')) in deps
    # - drill
    assert ctx.get_out_path(os.path.join('gerbers', prj+'-drill.drl')) in deps
    assert ctx.get_out_path(os.path.join('gerbers', prj+'-drill_report.txt')) in deps
    assert ctx.get_out_path(os.path.join('gerbers', prj+'-drill_map.pdf')) in deps
    # - Other files
    assert ctx.get_out_path('error.txt') in deps
    assert ctx.get_out_path('output.txt') in deps
    assert ctx.get_out_path('Makefile') in deps
    assert ctx.get_out_path('config.kibom.ini') in deps
    assert ctx.get_out_path('positiondir') in deps
    assert ctx.get_out_path('ibom') in deps
    assert ctx.get_out_path('3D') in deps
    assert ctx.get_out_path('gerbers') in deps
    # - Config
    assert yaml in deps
    logging.debug('- Target `archive` OK')
    ctx.search_err(r'\(kibom_external\) \[kibom\] uses a name generated by the external tool')
    ctx.search_err(r'\(ibom_external\) \[ibom\] uses a name generated by the external tool')
    ctx.search_err(r'Wrong character in file name `(.*)/test_v5-top\$.svg')


@pytest.mark.slow
@pytest.mark.kicad2step
def test_makefile_1(test_dir):
    prj = 'test_v5'
    ctx = context.TestContext(test_dir, prj, 'makefile_1')
    mkfile = ctx.get_out_path('Makefile')
    ctx.run(extra=['-s', 'all', 'archive'])
    ctx.run(extra=['-m', mkfile])
    check_makefile(ctx, mkfile, prj, '-v', r"^\t\$\(KIBOT_CMD\) -s (.*) -i$")
    ctx.clean_up()


@pytest.mark.slow
@pytest.mark.kicad2step
def test_makefile_2(test_dir):
    prj = 'test_v5'
    ctx = context.TestContext(test_dir, prj, 'makefile_1')
    mkfile = ctx.get_out_path('Makefile')
    ctx.run(extra=['-s', 'all', 'archive'])
    ctx.run(extra=['-m', mkfile], no_verbose=True)
    check_makefile(ctx, mkfile, prj, '', r"^\t@\$\(KIBOT_CMD\) -s (.*) -i 2>> \$\(LOGFILE\)$")
    ctx.clean_up()


def test_empty_zip(test_dir):
    prj = 'test_v5'
    ctx = context.TestContext(test_dir, prj, 'empty_zip')
    ctx.run()
    ctx.expect_out_file(prj+'-result.zip')
    ctx.search_err('No files provided, creating an empty archive')
    ctx.clean_up()


def test_compress_fail_deps(test_dir, monkeypatch):
    ctx = context.TestContext(test_dir, '3Rs', 'compress_fail_deps', 'Test')
    ctx.home_local_link()
    with monkeypatch.context() as m:
        m.setenv("HOME", os.path.join(ctx.get_board_dir(), '../..'))
        ctx.run(INTERNAL_ERROR)
    ctx.search_err(r"Unable to generate `dummy` from 'Test plug-in, dummy' \(do_test\) \[test\]")
    ctx.clean_up()


def test_import_1(test_dir):
    """ Import some outputs """
    prj = 'test_v5'
    ctx = context.TestContext(test_dir, prj, 'import_test_1')
    ctx.run(extra=['-i'])
    ctx.search_err(r'Outputs loaded from `tests/yaml_samples/gerber_inner.kibot.yaml`: \[\'gerbers\', \'result\'\]')
    ctx.search_err(r'Outputs loaded from `tests/yaml_samples/ibom.kibot.yaml`: \[\'interactive_bom\'\]')
    ctx.clean_up()


def test_import_g_1(test_dir):
    """ Import a global option """
    prj = 'test_v5'
    ctx = context.TestContext(test_dir, prj, 'import_test_g_1')
    ctx.run()
    ctx.expect_out_file(POS_DIR+'/test_v5_(bottom_pos)_2024_01_19.pos')
    ctx.expect_out_file(POS_DIR+'/test_v5_(top_pos)_2024_01_19.pos')
    ctx.clean_up()


def test_import_g_2(test_dir):
    """ Import a particular global option """
    prj = 'test_v5'
    ctx = context.TestContext(test_dir, prj, 'import_test_g_2')
    ctx.run()
    ctx.expect_out_file(POS_DIR+'/test_v5_(bottom_pos)_2024-01-19.pos')
    ctx.expect_out_file(POS_DIR+'/test_v5_(top_pos)_2024-01-19.pos')
    ctx.search_err(r"can't import `foobar`")
    ctx.clean_up()


def test_import_g_3(test_dir):
    """ Import a global option: not a dict """
    prj = 'test_v5'
    ctx = context.TestContext(test_dir, prj, 'import_test_g_3')
    ctx.run(EXIT_BAD_CONFIG)
    ctx.search_err(r"Incorrect `global` section")
    ctx.clean_up()


def test_import_g_4(test_dir):
    """ Import a global option: no globals """
    prj = 'test_v5'
    ctx = context.TestContext(test_dir, prj, 'import_test_g_4')
    ctx.run()
    ctx.expect_out_file(POS_DIR+'/test_v5-bottom_pos.pos')
    ctx.expect_out_file(POS_DIR+'/test_v5-top_pos.pos')
    ctx.search_err(r"No globals found")
    ctx.clean_up()


def test_import_3(test_dir):
    """ Import an output and change it """
    prj = 'test_v5'
    ctx = context.TestContext(test_dir, prj, 'import_test_3')
    ctx.run(extra=['position_mine'])
    ctx.expect_out_file(POS_DIR+'/test_v5_(both_pos)_2024_01_19.csv')
    ctx.clean_up()


def test_import_4(test_dir):
    """ Import an output and change it, also disable the original """
    prj = 'test_v5'
    ctx = context.TestContext(test_dir, prj, 'import_test_4')
    ctx.run(extra=[])
    ctx.expect_out_file(POS_DIR+'/test_v5_(both_pos)_2024_01_19.csv')
    ctx.dont_expect_out_file(POS_DIR+'/test_v5_(bottom_pos)_2024_01_19.csv')
    ctx.clean_up()


def test_import_5(test_dir):
    """ Infinite loop import """
    prj = 'test_v5'
    ctx = context.TestContext(test_dir, prj, 'import_test_5')
    ctx.run(EXIT_BAD_CONFIG)
    ctx.search_err(r'.*infinite loop')
    ctx.clean_up()


def test_import_6(test_dir):
    """ Import an output and change it, but using an import inside another """
    prj = 'test_v5'
    ctx = context.TestContext(test_dir, prj, 'import_test_6')
    ctx.run(extra=['position_mine'])
    ctx.expect_out_file(POS_DIR+'/test_v5_(both_pos)_2024_01_19.csv')
    ctx.clean_up()


def create_rules_project(ctx):
    if context.ki7():
        with open(ctx.board_file.replace('kicad_pcb', 'kicad_pro'), 'wt') as f:
            f.write(json.dumps({"board": {"design_settings": {"rule_severities": {"lib_footprint_issues": "ignore",
                               "lib_footprint_mismatch": "ignore"}}}}))


# Isn't really slow, just avoid to run it in parallel
@pytest.mark.slow
@pytest.mark.skipif(context.ki5(), reason="too slow on KiCad 5")
def test_import_p_1(test_dir):
    """ Import a preflight """
    prj = '3Rs'
    ctx = context.TestContext(test_dir, prj, 'import_test_p_1')
    create_rules_project(ctx)
    ctx.run()
    ctx.expect_out_file('3Rs-drc.txt')
    ctx.clean_up()


# Isn't really slow, just avoid to run it in parallel
@pytest.mark.slow
@pytest.mark.skipif(context.ki5(), reason="too slow on KiCad 5")
def test_import_p_2(test_dir):
    """ Import a particular preflight """
    prj = '3Rs'
    ctx = context.TestContext(test_dir, prj, 'import_test_p_2')
    create_rules_project(ctx)
    ctx.run()
    ctx.expect_out_file('3Rs-drc.txt')
    ctx.dont_expect_out_file('3Rs-erc.txt')
    ctx.search_err(r"can't import `foobar`")
    ctx.clean_up()


def test_import_p_3(test_dir):
    """ Import preflight: no preflights """
    prj = '3Rs'
    ctx = context.TestContext(test_dir, prj, 'import_test_p_3')
    create_rules_project(ctx)
    ctx.run()
    ctx.search_err(r"No preflights found")
    ctx.clean_up()


def test_import_8(test_dir):
    """ Import at the end """
    prj = 'light_control'
    ctx = context.TestContext(test_dir, prj, 'import_test_8')
    ctx.run(extra=[])
    ctx.expect_out_file('JLCPCB/light_control_cpl_jlc.csv')
    ctx.clean_up(keep_project=True)


def test_import_internal_1(test_dir):
    """ Import an internal file """
    prj = 'light_control'
    ctx = context.TestContext(test_dir, prj, 'import_test_internal_1')
    ctx.run(extra=['_Elecrow_drill'])
    ctx.expect_out_file('Elecrow/light_control.TXT')
    ctx.clean_up(keep_project=True)


def test_disable_default_1(test_dir):
    """ Disable in the same file and out-of-order """
    prj = 'test_v5'
    ctx = context.TestContext(test_dir, prj, 'disable_default_1')
    ctx.run(extra=[])
    ctx.expect_out_file(POS_DIR+'/test_v5_(both_pos_test).csv')
    ctx.dont_expect_out_file(POS_DIR+'/test_v5_(bottom_pos).csv')
    ctx.clean_up()


def test_expand_comment_1(test_dir):
    """ Disable in the same file and out-of-order """
    prj = 'test_v5'
    ctx = context.TestContext(test_dir, prj, 'expand_comment_1')
    ctx.run(extra=[])
    ctx.expect_out_file(POS_DIR+'/test_v5_(Comment 1)_(The_C2).csv')
    ctx.clean_up()


def test_compress_sources_1(test_dir):
    """ Disable in the same file and out-of-order """
    prj = 'test_v5'
    ctx = context.TestContext(test_dir, prj, 'compress_sources_1')
    ctx.run()
    files = ['source/'+prj+'.kicad_pcb', 'source/'+prj+'.sch', 'source/deeper.sch', 'source/sub-sheet.sch']
    ctx.test_compress(prj + '-result.tar.bz2', files)
    ctx.clean_up()


def test_date_format_1(test_dir):
    """ Date from SCH reformatted """
    prj = 'test_v5'
    ctx = context.TestContext(test_dir, prj, 'date_format_1')
    ctx.run(extra=[])
    ctx.expect_out_file(POS_DIR+'/test_v5_20200812.csv')
    ctx.clean_up()


def test_date_format_2(test_dir):
    """ Date from SCH reformatted """
    prj = 'bom'
    ctx = context.TestContext(test_dir, prj, 'date_format_1')
    ctx.run(extra=[])
    ctx.expect_out_file(POS_DIR+'/bom_13_07_2020.csv')
    assert ctx.search_err('Trying to reformat SCH time, but not in ISO format')
    ctx.clean_up()


@pytest.mark.slow
def test_download_datasheets_1(test_dir):
    prj = 'kibom-variant_2ds'
    ctx = context.TestContextSCH(test_dir, prj, 'download_datasheets_1')
    # We use a fake server to avoid needing good URLs and reliable internet connection
    ctx.run(kicost=True)
    ctx.expect_out_file('DS/C0805C102J4GAC7800.pdf')
    ctx.expect_out_file('DS/CR0805-JW-102ELF.pdf')
    ctx.expect_out_file('DS_production/CR0805-JW-102ELF.pdf')
    ctx.expect_out_file('DS_test/C0805C102J4GAC7800-1000 pF__test.pdf')
    ctx.expect_out_file('DS_test/C0805C102J4GAC7800-1nF__test.pdf')
    ctx.expect_out_file('DS_test/CR0805-JW-102ELF-3k3__test.pdf')
    ctx.clean_up()


def test_cli_order(test_dir):
    prj = 'simple_2layer'
    ctx = context.TestContext(test_dir, prj, 'pre_and_position', POS_DIR)
    ctx.run(extra=['-s', 'all', '-C', 'pos_ascii', 'position'])

    csv = ctx.get_pos_both_csv_filename()
    pos = ctx.get_pos_both_filename()
    ctx.expect_out_file(csv)
    ctx.expect_out_file(pos)
    pos_txt = ctx.search_out('pos_ascii')
    csv_txt = ctx.search_out('position')
    assert pos_txt.start() < csv_txt.start()

    ctx.clean_up()


@pytest.mark.slow
@pytest.mark.eeschema
def test_qr_lib_1(test_dir):
    prj = 'qr_test/qr_test'
    ctx = context.TestContext(test_dir, prj, 'qr_lib_1', POS_DIR)
    ctx.run()  # extra_debug=True
    # Check the schematic
    fname = 'Schematic.pdf'
    ctx.expect_out_file(fname)
    cmd = ['convert', '-density', '300', ctx.get_out_path(fname), '-background', 'white', '-alpha', 'remove', '-alpha',
           'off', ctx.get_out_path('%d.png')]
    subprocess.check_call(cmd)
    cmd = ['zbarimg', ctx.get_out_path('0.png')]
    res = subprocess.check_output(cmd, stderr=subprocess.STDOUT).decode()
    logging.debug(res.split('\n')[0])
    assert 'QR-Code:QR Test A' in res
    cmd = ['zbarimg', ctx.get_out_path('1.png')]
    res = subprocess.check_output(cmd, stderr=subprocess.STDOUT).decode()
    logging.debug(res.split('\n')[0])
    assert 'QR-Code:https://github.com/INTI-CMNB/KiBot/' in res
    # Check the PCB
    fname = 'PCB.pdf'
    ctx.expect_out_file(fname)
    cmd = ['convert', '-density', '300', ctx.get_out_path(fname), '-background', 'white', '-alpha', 'remove', '-alpha',
           'off', ctx.get_out_path('p%d.png')]
    subprocess.check_call(cmd)
    cmd = ['zbarimg', ctx.get_out_path('p0.png')]
    res = subprocess.check_output(cmd, stderr=subprocess.STDOUT).decode()
    logging.debug(res.split('\n')[0])
    assert 'QR-Code:QR PCB B' in res
    cmd = ['zbarimg', ctx.get_out_path('p1.png')]
    res = subprocess.check_output(cmd, stderr=subprocess.STDOUT).decode()
    logging.debug(res.split('\n')[0])
    assert 'QR-Code:https://github.com/INTI-CMNB/KiBot/' in res
    assert ctx.search_err('Updating text `https')
    # Restore the original files
    bd = ctx.get_board_dir()
    files = ['qr.lib', 'qr.kicad_sym', 'qr.pretty/QR.kicad_mod', 'qr.pretty/QR2.kicad_mod', 'qr_test.kicad_pcb',
             'qr_test.kicad_sch', 'sub_1.kicad_sch']
    for f in files:
        bogus = os.path.join(bd, 'qr_test/'+f+'.bogus')
        if os.path.isfile(bogus):
            shutil.copy2(bogus, os.path.join(bd, 'qr_test/'+f))
    if context.ki5():
        os.remove(os.path.join(bd, 'qr_test/qr_test.pro-bak'))
    else:
        os.remove(os.path.join(bd, 'qr_test/qr_test.kicad_sch-bak'))
        os.remove(os.path.join(bd, 'qr_test/sub_1.kicad_sch-bak'))
    bkp = os.path.join(bd, 'qr_test/qr_test.kicad_pcb-bak')
    if os.path.isfile(bkp):
        # Not always there, pcbnew_do can remove it
        os.remove(bkp)


def test_report_simple_1(test_dir):
    prj = 'light_control'
    ctx = context.TestContext(test_dir, prj, 'report_simple_1', POS_DIR)
    ctx.run(extra=['report_full', 'report_simple'])
    ctx.expect_out_file(prj+'-report.txt')
    ctx.expect_out_file(prj+'-report_simple.txt')
    ctx.compare_txt(prj+'-report.txt')
    ctx.compare_txt(prj+'-report_simple.txt')
    ctx.clean_up(keep_project=True)


@pytest.mark.slow
@pytest.mark.eeschema
def test_report_simple_2(test_dir):
    prj = 'light_control'
    ctx = context.TestContext(test_dir, prj, 'report_simple_2', POS_DIR)
    ctx.run()
    f_report = os.path.join('report', prj+'-report.txt')
    ctx.expect_out_file(f_report)
    ctx.expect_out_file(prj+'-report_simple.txt')
    ctx.compare_txt(f_report, prj+'-report.txt_2')
    ctx.compare_txt(prj+'-report_simple.txt')
    ctx.expect_out_file(f_report.replace('.txt', '.pdf'))
    ctx.clean_up(keep_project=True)


def test_report_edge_1(test_dir):
    """ Measures the PCB size when using a component that contains the real PCB edges #164 """
    prj = 'comp_edge'
    ctx = context.TestContext(test_dir, prj, 'report_edge_1', POS_DIR)
    ctx.run()
    ctx.expect_out_file(prj+'-report.txt')
    ctx.compare_txt(prj+'-report.txt')
    ctx.clean_up()


@pytest.mark.skipif(context.ki5(), reason="Example in KiCad 6 format")
def test_report_edge_2(test_dir):
    """ Measures the PCB size when using circles in the PCB edge #375 """
    prj = 'circle_edge'
    ctx = context.TestContext(test_dir, prj, 'report_edge_1', POS_DIR)
    ctx.run()
    ctx.expect_out_file(prj+'-report.txt')
    ctx.compare_txt(prj+'-report.txt')
    ctx.clean_up()


def test_report_output_path(test_dir):
    prj = 'light_control'
    ctx = context.TestContext(test_dir, prj, 'report_output_path', POS_DIR)
    ctx.run(extra=['pcb_print_png', 'report_output_path_1', 'report_output_path_2'])
    ctx.expect_out_file('report/'+prj+'-report_output_path_1.txt')
    ctx.expect_out_file(prj+'-report_output_path_2.txt')
    ctx.compare_txt('report/'+prj+'-report_output_path_1.txt', reference=prj+'-report_output_path_1.txt')
    ctx.compare_txt(prj+'-report_output_path_2.txt')
    ctx.clean_up(keep_project=True)


def test_board_view_1(test_dir):
    prj = 'glasgow'
    ctx = context.TestContext(test_dir, prj, 'boardview', POS_DIR)
    ctx.run()
    o = prj+'-boardview.brd'
    ctx.expect_out_file(o)
    ctx.compare_txt(o)
    ctx.clean_up()


def test_annotate_power_1(test_dir):
    prj = 'test_v5'
    ctx = context.TestContextSCH(test_dir, prj, 'annotate_power', POS_DIR)
    # Copy test_v5 schematic, but replacing all #PWRxx references by #PWR?
    sch_file = os.path.basename(ctx.sch_file)
    sch_base = ctx.get_out_path(sch_file)
    with open(ctx.sch_file, 'rt') as f:
        text = f.read()
    text = re.sub(r'#(PWR|FLG)\d+', r'#\1?', text)
    with open(sch_base, 'wt') as f:
        f.write(text)
    # deeper
    sch_file = 'deeper'+context.KICAD_SCH_EXT
    shutil.copy2(os.path.abspath(os.path.join(ctx.get_board_dir(), sch_file)), ctx.get_out_path(sch_file))
    # sub-sheet
    sch_file = 'sub-sheet'+context.KICAD_SCH_EXT
    with open(os.path.abspath(os.path.join(ctx.get_board_dir(), sch_file)), 'rt') as f:
        text = f.read()
    text = re.sub(r'#(PWR|FLG)\d+', r'#\1?', text)
    with open(ctx.get_out_path(sch_file), 'wt') as f:
        f.write(text)
    ctx.run(extra=['-e', sch_base], no_board_file=True)
    ctx.compare_txt('test_v5'+context.KICAD_SCH_EXT)
    ctx.compare_txt('deeper'+context.KICAD_SCH_EXT)
    ctx.compare_txt('sub-sheet'+context.KICAD_SCH_EXT)
    ctx.clean_up()


def test_pdfunite_1(test_dir):
    prj = 'bom'
    ctx = context.TestContext(test_dir, prj, 'pdfunite_1', POS_DIR)
    ctx.run()
    o = prj+'-PDF_Joined.pdf'
    ctx.expect_out_file(o)
    ctx.clean_up()


def test_pdfunite_2(test_dir):
    prj = 'bom'
    ctx = context.TestContext(test_dir, prj, 'pdfunite_2', POS_DIR)
    ctx.run()
    o = prj+'-PDF_Joined.pdf'
    ctx.expect_out_file(o)
    ctx.clean_up()


def test_pdfunite_no_input(test_dir):
    prj = 'bom'
    ctx = context.TestContext(test_dir, prj, 'pdfunite_2', POS_DIR)
    ctx.run(MISSING_FILES, extra=['PDF_Joined'])
    ctx.clean_up()


def test_pdfunite_wrong_input(test_dir):
    prj = 'bom'
    ctx = context.TestContext(test_dir, prj, 'error_pdfunite_wrong_files', POS_DIR)
    ctx.run(MISSING_FILES, extra=['PDF_Joined'])
    ctx.search_err('No match found for')
    ctx.clean_up()


def check_refs(ctx, refs):
    rows, _, _ = ctx.load_csv('ano_pcb-bom.csv')
    for r in rows:
        assert r[1] == refs[r[0]], "{}={} should be {}".format(r[0], r[1], refs[r[0]])
    assert len(rows) == len(refs)
    logging.debug("{} references OK".format(len(rows)))


def check_anno_pcb(test_dir, type, refs):
    prj = 'ano_pcb'
    ctx = context.TestContext(test_dir, prj, 'annotate_pcb_'+type, '', test_name='annotate_pcb_'+type)
    pcb_file = ctx.get_out_path(os.path.basename(ctx.board_file))
    sch_file = ctx.get_out_path(os.path.basename(ctx.sch_file))
    shutil.copy2(ctx.board_file, pcb_file)
    shutil.copy2(ctx.sch_file, sch_file)
    ctx.run(extra=['-b', pcb_file], no_board_file=True)
    check_refs(ctx, refs)
    ctx.clean_up()


def test_annotate_pcb_tblr(test_dir):
    check_anno_pcb(test_dir, 'tblr',
                   {'C1': '2u', 'C2': '1u', 'R1': '2', 'R2': '1', 'C101': '3u', 'C102': '4u', 'R101': '3', 'R102': '4'})


def test_annotate_pcb_btlr(test_dir):
    check_anno_pcb(test_dir, 'btlr',
                   {'C1': '1u', 'C2': '2u', 'R1': '1', 'R2': '2', 'C101': '4u', 'C102': '3u', 'R101': '4', 'R102': '3'})


def test_annotate_pcb_btrl(test_dir):
    check_anno_pcb(test_dir, 'btrl',
                   {'C1': '1u', 'C2': '2u', 'R1': '2', 'R2': '1', 'C101': '4u', 'C102': '3u', 'R101': '4', 'R102': '3'})


def test_annotate_pcb_lrbt(test_dir):
    check_anno_pcb(test_dir, 'lrbt',
                   {'C1': '1u', 'C2': '2u', 'R1': '1', 'R2': '2', 'C101': '4u', 'C102': '3u', 'R101': '4', 'R102': '3'})


def test_annotate_pcb_lrtb(test_dir):
    check_anno_pcb(test_dir, 'lrtb',
                   {'C1': '1u', 'C2': '2u', 'R1': '1', 'R2': '2', 'C101': '3u', 'C102': '4u', 'R101': '3', 'R102': '4'})


def test_annotate_pcb_rlbt(test_dir):
    check_anno_pcb(test_dir, 'rlbt',
                   {'C1': '2u', 'C2': '1u', 'R1': '2', 'R2': '1', 'C101': '4u', 'C102': '3u', 'R101': '4', 'R102': '3'})


def test_annotate_pcb_rltb(test_dir):
    check_anno_pcb(test_dir, 'rltb',
                   {'C1': '2u', 'C2': '1u', 'R1': '2', 'R2': '1', 'C101': '3u', 'C102': '4u', 'R101': '3', 'R102': '4'})


def test_annotate_pcb_tbrl_big_grid(test_dir):
    check_anno_pcb(test_dir, 'tbrl_big_grid',
                   {'C1': '2u', 'C2': '1u', 'R1': '2', 'R2': '1', 'C3': '3u', 'C4': '4u', 'R3': '3', 'R4': '4'})


def test_annotate_pcb_tbrl_small_grid(test_dir):
    check_anno_pcb(test_dir, 'tbrl_small_grid',
                   {'C1': '1u', 'C2': '2u', 'R1': '2', 'R2': '1', 'C3': '3u', 'C4': '4u', 'R3': '3', 'R4': '4'})


@pytest.mark.slow
@pytest.mark.pcbnew
def test_gencad_1(test_dir):
    prj = 'gencad'
    ctx = context.TestContext(test_dir, prj, 'gencad_1')
    ctx.run()
    o = prj+'-gencad.cad'
    ctx.expect_out_file(o)
    file = ctx.get_out_path(o)
    with open(file, 'rt') as f:
        text = f.read()
    text = re.sub(r'(USER|DRAWING) "(.*)"', r'\1 ""', text)
    with open(file, 'wt') as f:
        f.write(text)
    ctx.compare_txt(o)
    ctx.clean_up()


@pytest.mark.slow
@pytest.mark.pcbnew
def test_quick_start_1(test_dir):
    """ Very naive test to see if it doesn't crash """
    prj = 'light_control'
    dir_o = 'navigate'
    generated = 'kibot_generated.kibot.yaml'
    # 1) Run the quick-start
    logging.debug('Running with quick-start')
    ctx = context.TestContext(test_dir, prj, 'pre_and_position', dir_o)
    board_file = os.path.basename(ctx.board_file)
    dest_dir = ctx.get_out_path(dir_o)
    dest_file = os.path.join(dest_dir, board_file)
    os.makedirs(dest_dir, exist_ok=True)
    shutil.copy2(ctx.board_file, dest_file)
    shutil.copy2(ctx.board_file.replace('.kicad_pcb', context.PRO_EXT), dest_file.replace('.kicad_pcb', context.PRO_EXT))
    sch_file = os.path.basename(ctx.sch_file)
    dest_file_sch = os.path.join(dest_dir, sch_file)
    shutil.copy2(ctx.sch_file, dest_file_sch)
    # Create a git repo
    git_init(ctx)
    # Add the files to the repo
    ctx.run_command(['git', 'add', board_file, sch_file], chdir_out=dest_dir)
    ctx.run_command(['git', 'commit', '-m', 'Reference'], chdir_out=dest_dir)
    # Modify the PCB
    shutil.copy2(ctx.board_file.replace(prj, prj+'_diff'), dest_file)
    ctx.run_command(['git', 'add', board_file], chdir_out=dest_dir)
    ctx.run_command(['git', 'commit', '-m', 'Change'], chdir_out=dest_dir)
    # 1) Run the Quick Start
    ctx.run(extra=['--quick-start', '--dry', '--start', dest_dir], no_board_file=True, no_yaml_file=True)
    dest_conf = os.path.join(dir_o, generated)
    dest_conf_f = os.path.join(dest_dir, 'kibot_generated.kibot.yaml')
    ctx.expect_out_file(dest_conf)
    # 2) List the generated outputs
    ctx.run(extra=['-c', dest_conf_f, '-b', dest_file, '-l'], no_out_dir=True, no_yaml_file=True, no_board_file=True)
    OUTS = ['boardview', 'dxf', 'excellon', 'gencad', 'gerb_drill', 'gerber', 'compress', 'hpgl', 'ibom',
            'navigate_results_rb', 'netlist', 'pcb_print', 'pcbdraw', 'pdf', 'position', 'ps', 'render_3d',
            'report', 'svg', 'kiri', 'kicanvas',
            'bom', 'download_datasheets', 'pdf_sch_print', 'svg_sch_print']
    if context.ki9():
        OUTS.extend(['odb', 'export_3d', 'ipc2581'])
    else:
        OUTS.append('step')
    for o in OUTS:
        ctx.search_out(r'\['+o+r'\]')
    # 3) Generate one output that we can use as image for a category
    logging.debug('Creating `basic_pcb_print_pdf`')
    ctx.run(extra=['-c', dest_conf_f, '-b', dest_file, 'basic_pcb_print_pdf'], no_yaml_file=True, no_board_file=True)
    ctx.expect_out_file(os.path.join('PCB', 'PDF', prj+'-assembly.pdf'))
    # 4) Generate the navigate_results stuff
    logging.debug('Creating the web pages')
    ctx.run(extra=['-c', dest_conf_f, '-b', dest_file, 'basic_navigate_results_rb'], no_yaml_file=True, no_board_file=True)
    ctx.expect_out_file('index.html')
    ctx.expect_out_file(os.path.join('Browse', 'light_control-navigate.html'))


@pytest.mark.slow
@pytest.mark.eeschema
def test_netlist_classic_1(test_dir):
    prj = 'light_control'
    dir_o = 'Export'
    ctx = context.TestContext(test_dir, prj, 'netlist_classic_1', dir_o)
    ctx.run()
    ctx.expect_out_file(os.path.join(dir_o, prj+'-netlist.net'))


@pytest.mark.slow
@pytest.mark.pcbnew
def test_netlist_ipc_1(test_dir):
    prj = 'light_control'
    dir_o = 'Export'
    ctx = context.TestContext(test_dir, prj, 'netlist_ipc_1', dir_o)
    ctx.run()
    ctx.expect_out_file(os.path.join(dir_o, prj+'-IPC-D-356.d356'))


def test_dependencies_1(test_dir):
    dep = 'KiCad Automation tools'
    ctx = context.TestContext(test_dir, 'bom', 'netlist_ipc_1')
    ctx.run(extra=['--help-dependencies'], no_board_file=True, no_out_dir=True, no_yaml_file=True)
    ctx.search_out(dep)
    ctx.run(extra=['--help-dependencies', '--markdown'], no_board_file=True, no_out_dir=True, no_yaml_file=True)
    ctx.search_out(r'\*\*'+dep+r'\*\*')
    ctx.run(extra=['--help-dependencies', '--json'], no_board_file=True, no_out_dir=True, no_yaml_file=True)
    with open(ctx.get_out_path('output.txt'), 'rt') as f:
        data = json.load(f)
    assert dep in data
    ctx.run(extra=['--help-dependencies', '--rst'], no_board_file=True, no_out_dir=True, no_yaml_file=True)
    ctx.search_out('`'+dep+' <')


def test_dont_stop_1(test_dir):
    """ The first target fails, check we get the second """
    ctx = context.TestContext(test_dir, 'light_control', 'dont_stop_1', 'positiondir')
    ctx.run(extra=['--dont-stop'])
    pos_top = ctx.get_pos_top_csv_filename()
    pos_bot = ctx.get_pos_bot_csv_filename()
    ctx.expect_out_file(pos_top)
    ctx.expect_out_file(pos_bot)
    ctx.search_err('ERROR:Failed to create BoM')
    ctx.clean_up(keep_project=True)


def test_diff_file_1(test_dir):
    """ Difference between the current PCB and a reference file """
    prj = 'light_control_diff'
    yaml = f'diff_file_k{context.kicad_major}'
    ctx = context.TestContext(test_dir, prj, yaml)
    ctx.run()
    ctx.compare_pdf(prj+'-diff_pcb.pdf', reference='light_control-diff_pcb.pdf', off_y=OFFSET_Y, tol=DIFF_TOL)
    ctx.clean_up(keep_project=True)


def git_init(ctx, cwd=True):
    ctx.run_command(['git', 'init', '.'], chdir_out=cwd)
    ctx.run_command(['git', 'config', 'user.email', 'pytest@nowherem.com'], chdir_out=cwd)
    ctx.run_command(['git', 'config', 'user.name', 'KiBot test'], chdir_out=cwd)


def test_diff_git_1(test_dir):
    """ Difference between the current PCB and the git HEAD """
    prj = 'light_control'
    yaml = 'diff_git_1'
    ctx = context.TestContext(test_dir, prj, yaml)
    # Create a git repo
    git_init(ctx)
    # Copy the "old" file
    pcb = prj+'.kicad_pcb'
    file = ctx.get_out_path(pcb)
    shutil.copy2(ctx.board_file, file)
    shutil.copy2(ctx.board_file.replace('.kicad_pcb', context.KICAD_SCH_EXT),
                 file.replace('.kicad_pcb', context.KICAD_SCH_EXT))
    # Add it to the repo
    ctx.run_command(['git', 'add', pcb], chdir_out=True)
    ctx.run_command(['git', 'commit', '-m', 'Reference'], chdir_out=True)
    # Copy the "new" file
    shutil.copy2(ctx.board_file.replace(prj, prj+'_diff'), file)
    # Run the test
    ctx.run(extra=['-b', file], no_board_file=True)
    ctx.compare_pdf(prj+'-diff_pcb.pdf', off_y=OFFSET_Y, tol=DIFF_TOL)
    ctx.clean_up(keep_project=True)


@pytest.mark.slow
@pytest.mark.eeschema
def test_diff_kiri_1(test_dir):
    """ Difference between the current PCB and the git HEAD """
    prj = 'light_control'
    yaml = 'kiri_1'
    ctx = context.TestContext(test_dir, prj, yaml)
    # Create a git repo
    git_init(ctx)
    # Copy the "old" file
    pcb = prj+'.kicad_pcb'
    sch = prj+context.KICAD_SCH_EXT
    file = ctx.get_out_path(pcb)
    shutil.copy2(ctx.board_file, file)
    shutil.copy2(ctx.board_file.replace('.kicad_pcb', context.KICAD_SCH_EXT),
                 file.replace('.kicad_pcb', context.KICAD_SCH_EXT))
    # Add it to the repo
    ctx.run_command(['git', 'add', pcb, sch], chdir_out=True)
    ctx.run_command(['git', 'commit', '-m', 'Reference'], chdir_out=True)
    hash = ctx.run_command(['git', 'log', '--pretty=format:%h', '-n', '1'], chdir_out=True)
    # Copy the "new" file
    shutil.copy2(ctx.board_file.replace(prj, prj+'_diff'), file)
    # Run the test
    ctx.run(extra=['-b', file], no_board_file=True, extra_debug=True)
    ctx.expect_out_file(['_local_/_KIRI_/pcb_layers', hash+'/_KIRI_/pcb_layers',
                         '_local_/_KIRI_/sch_sheets', hash+'/_KIRI_/sch_sheets',
                         'index.html', 'commits', 'project'])
    ctx.clean_up(keep_project=True)


def test_diff_git_2(test_dir):
    """ Difference between the two repo points, wipe the current file """
    prj = 'light_control'
    yaml = 'diff_git_2'
    ctx = context.TestContext(test_dir, prj, yaml)
    # Create something to use as submodule
    sub_dir = os.path.join(ctx.output_dir, 'sub')
    os.makedirs(sub_dir)
    git_init(ctx, sub_dir)
    some_file = os.path.join(sub_dir, 'some_file.txt')
    with open(some_file, 'wt') as f:
        f.write('Hello!\n')
    ctx.run_command(['git', 'add', 'some_file.txt'], chdir_out=sub_dir)
    ctx.run_command(['git', 'commit', '-m', 'Some change'], chdir_out=sub_dir)
    # Create a git repo
    repo_dir = os.path.join(ctx.output_dir, 'repo')
    os.makedirs(repo_dir)
    git_init(ctx, repo_dir)
    # Copy the "old" file
    pcb = prj+'.kicad_pcb'
    file = os.path.join(repo_dir, pcb)
    shutil.copy2(ctx.board_file, file)
    shutil.copy2(ctx.board_file.replace('.kicad_pcb', context.KICAD_SCH_EXT),
                 file.replace('.kicad_pcb', context.KICAD_SCH_EXT))
    # Add it to the repo
    ctx.run_command(['git', 'add', pcb], chdir_out=repo_dir)
    ctx.run_command(['git', 'commit', '-m', 'Reference'], chdir_out=repo_dir)
    # Tag it, just to test the link name
    ctx.run_command(['git', 'tag', '-a', 'v1', '-m', 'Tag description'], chdir_out=repo_dir)
    # Add a submodule
    ctx.run_command(['git', 'submodule', 'add', '../sub'], chdir_out=repo_dir)
    # Add an extra commit
    dummy = os.path.join(repo_dir, 'dummy')
    with open(dummy, 'wt') as f:
        f.write('dummy\n')
    ctx.run_command(['git', 'add', 'dummy'], chdir_out=repo_dir)
    ctx.run_command(['git', 'commit', '-m', 'Dummy noise'], chdir_out=repo_dir)
    # Copy the "new" file
    shutil.copy2(ctx.board_file.replace(prj, prj+'_diff'), file)
    # Add it to the repo
    ctx.run_command(['git', 'add', pcb], chdir_out=repo_dir)
    ctx.run_command(['git', 'commit', '-m', 'New version'], chdir_out=repo_dir)
    # Now just wipe the current file
    shutil.copy2(ctx.board_file.replace(prj, '3Rs'), file)
    # Change the file in the submodule
    some_file = os.path.join(repo_dir, 'sub', 'some_file.txt')
    with open(some_file, 'wt') as f:
        f.write('Bye!\n')
    # Run the test
    ctx.run(extra=['-b', file], no_board_file=True, extra_debug=True)
    ctx.compare_pdf(prj+'-diff_pcb.pdf', off_y=OFFSET_Y, tol=DIFF_TOL)
    # Check the submodule was restored
    with open(some_file, 'rt') as f:
        msg = f.read()
    assert msg == 'Bye!\n'
    # Check the link
    assert (glob(os.path.join(ctx.output_dir, prj+'-diff_pcb_*(v1)-*(master[[]v1[]]).pdf')) +
            glob(os.path.join(ctx.output_dir, prj+'-diff_pcb_*(v1)-*(v1-2-*).pdf'))), "Can't find link"
    ctx.clean_up(keep_project=True)


def test_diff_git_3(test_dir):
    """ Difference between the two repo points, no changes to stash """
    prj = 'light_control'
    yaml = 'diff_git_3'
    ctx = context.TestContext(test_dir, prj, yaml)
    # Create a git repo
    git_init(ctx)
    # Copy the "old" file
    pcb = prj+'.kicad_pcb'
    file = ctx.get_out_path(pcb)
    shutil.copy2(ctx.board_file, file)
    shutil.copy2(ctx.board_file.replace('.kicad_pcb', context.KICAD_SCH_EXT),
                 file.replace('.kicad_pcb', context.KICAD_SCH_EXT))
    # Add it to the repo
    ctx.run_command(['git', 'add', pcb], chdir_out=True)
    ctx.run_command(['git', 'commit', '-m', 'Reference'], chdir_out=True)
    # Add an extra commit
    dummy = ctx.get_out_path('dummy')
    with open(dummy, 'wt') as f:
        f.write('dummy\n')
    ctx.run_command(['git', 'add', 'dummy'], chdir_out=True)
    ctx.run_command(['git', 'commit', '-m', 'Dummy noise'], chdir_out=True)
    # Copy the "new" file
    shutil.copy2(ctx.board_file.replace(prj, prj+'_diff'), file)
    # Add it to the repo
    ctx.run_command(['git', 'add', pcb], chdir_out=True)
    ctx.run_command(['git', 'commit', '-m', 'New version'], chdir_out=True)
    # Run the test
    ctx.run(extra=['-b', file], no_board_file=True, extra_debug=True)
    ctx.compare_pdf(prj+'-diff_pcb.pdf', off_y=OFFSET_Y, tol=DIFF_TOL)
    ctx.clean_up(keep_project=True)


@pytest.mark.slow
@pytest.mark.eeschema
def test_diff_git_4(test_dir):
    """ Difference between the two repo points, wipe the current file, the first is missing """
    prj = 'light_control'
    yaml = 'diff_git_4'
    ctx = context.TestContext(test_dir, prj, yaml)
    # Create a git repo
    repo_dir = os.path.join(ctx.output_dir, 'repo')
    os.makedirs(repo_dir)
    git_init(ctx, repo_dir)
    # Copy the "old" file
    pcb = prj+'.kicad_pcb'
    sch = prj+context.KICAD_SCH_EXT
    file = os.path.join(repo_dir, pcb)
    # Create a dummy
    dummy = os.path.join(repo_dir, 'dummy')
    with open(dummy, 'wt') as f:
        f.write('dummy\n')
    # Add it to the repo
    ctx.run_command(['git', 'add', 'dummy'], chdir_out=repo_dir)
    ctx.run_command(['git', 'commit', '-m', 'Empty repo'], chdir_out=repo_dir)
    # Tag it
    ctx.run_command(['git', 'tag', '-a', 'v1', '-m', 'Tag description'], chdir_out=repo_dir)
    # Add an extra commit, now with the files
    shutil.copy2(ctx.board_file, file)
    shutil.copy2(ctx.board_file.replace('.kicad_pcb', context.KICAD_SCH_EXT),
                 file.replace('.kicad_pcb', context.KICAD_SCH_EXT))
    ctx.run_command(['git', 'add', sch, pcb], chdir_out=repo_dir)
    ctx.run_command(['git', 'commit', '-m', 'Filled repo'], chdir_out=repo_dir)
    # Copy the "new" file
    shutil.copy2(ctx.board_file.replace(prj, prj+'_diff'), file)
    # Add it to the repo
    ctx.run_command(['git', 'add', pcb], chdir_out=repo_dir)
    ctx.run_command(['git', 'commit', '-m', 'New version'], chdir_out=repo_dir)
    # Now just wipe the current file
    shutil.copy2(ctx.board_file.replace(prj, '3Rs'), file)
    # Run the test
    ctx.run(extra=['-b', file], no_board_file=True, extra_debug=True)
    ctx.compare_pdf(prj+'-diff_pcb.pdf', prj+'-only_new.pdf', off_y=OFFSET_Y, tol=DIFF_TOL)
    if is_debian:
        # Impossible to compare the Ubuntu version
        ctx.compare_pdf(prj+'-diff_sch.pdf', off_y=OFFSET_Y, tol=DIFF_TOL)
    ctx.clean_up(keep_project=True)


def test_diff_git_5(test_dir):
    """ Difference between the two repo points, using tags """
    prj = 'light_control'
    yaml = 'diff_git_5'
    ctx = context.TestContext(test_dir, prj, yaml)
    # Create a git repo
    git_init(ctx)
    # Copy the "old" file
    pcb = prj+'.kicad_pcb'
    file = ctx.get_out_path(pcb)
    shutil.copy2(ctx.board_file, file)
    shutil.copy2(ctx.board_file.replace('.kicad_pcb', context.KICAD_SCH_EXT),
                 file.replace('.kicad_pcb', context.KICAD_SCH_EXT))
    # Add it to the repo
    ctx.run_command(['git', 'add', pcb], chdir_out=True)
    ctx.run_command(['git', 'commit', '-m', 'Reference'], chdir_out=True)
    # Tag it (this will be our target)
    ctx.run_command(['git', 'tag', '-a', 't1', '-m', 't1'], chdir_out=True)
    # Add an extra commit
    dummy = ctx.get_out_path('dummy')
    with open(dummy, 'wt') as f:
        f.write('dummy\n')
    ctx.run_command(['git', 'add', 'dummy'], chdir_out=True)
    ctx.run_command(['git', 'commit', '-m', 'Dummy noise'], chdir_out=True)
    # Add a noisy branch
    ctx.run_command(['git', 'switch', '-c', 'a_branch'], chdir_out=True)
    # Copy the "new" file
    with open(file, 'wt') as f:
        f.write('broken\n')
    # Add it to the repo
    ctx.run_command(['git', 'commit', '-a', '-m', 'New version'], chdir_out=True)
    # Tag it (this shouldn't be a problem)
    ctx.run_command(['git', 'tag', '-a', 't2', '-m', 't2'], chdir_out=True)
    # Back to the master
    ctx.run_command(['git', 'checkout', 'master'], chdir_out=True)
    # Copy the "new" file
    shutil.copy2(ctx.board_file.replace(prj, prj+'_diff'), file)
    # Add it to the repo
    ctx.run_command(['git', 'add', pcb], chdir_out=True)
    ctx.run_command(['git', 'commit', '-m', 'New version'], chdir_out=True)
    # Tag it (this shouldn't be a problem)
    ctx.run_command(['git', 'tag', '-a', 't3', '-m', 't3'], chdir_out=True)
    # Run the test
    ctx.run(extra=['-b', file], no_board_file=True, extra_debug=True)
    ctx.compare_pdf(prj+'-diff_pcb.pdf', off_y=OFFSET_Y, tol=DIFF_TOL)
    ctx.clean_up(keep_project=True)


@pytest.mark.slow
@pytest.mark.eeschema
def test_diff_file_sch_1(test_dir):
    """ Difference between the current Schematic and a reference file
        Also test definitions (from CLI and env)
        Also log file """
    prj = 'light_control_diff'
    yaml = 'diff_file_sch'
    ctx = context.TestContext(test_dir, prj, yaml)
    os.environ['SCHExt'] = context.KICAD_SCH_EXT
    ctx.run(extra=['-E', 'KiVer='+str(context.kicad_major), '--defs-from-env', '-L', ctx.get_out_path('log')])
    ctx.expect_out_file(prj+'-diff_sch_FILE-Current.pdf')
    if is_debian:
        ctx.compare_pdf(prj+'-diff_sch.pdf')
    ctx.expect_out_file('log')
    ctx.clean_up(keep_project=True)


@pytest.mark.slow
@pytest.mark.skipif(context.ki5(), reason="KiCad 6 aliases used")
def test_copy_files_1(test_dir):
    """ Copy files and 3D models """
    prj = 'copy_files'
    ctx = context.TestContext(test_dir, prj, 'copy_files_1', 'test.files')
    os.environ['KIBOT_3D_MODELS'] = '/tmp'
    ctx.run(kicost=True)  # We use the fake web server
    del os.environ['KIBOT_3D_MODELS']
    # The modified PCB
    ctx.expect_out_file(prj+'.kicad_pcb', sub=True)
    # The 3D models
    ctx.expect_out_file('3d_models/C_0805_2012Metric.wrl', sub=True)
    ctx.expect_out_file('3d_models/R_0805_2012Metric.wrl', sub=True)
    ctx.expect_out_file('3d_models/R_0805_2012Metrico.wrl', sub=True)
    ctx.expect_out_file('3d_models/test.wrl', sub=True)
    # From output with dest
    ctx.expect_out_file('my_position/'+prj+'-both_pos.pos', sub=True)
    # From output without dest
    ctx.expect_out_file('positiondir/'+prj+'-both_pos.pos', sub=True)
    # From output dir
    ctx.expect_out_file('my_position2/'+prj+'-both_pos.pos', sub=True)
    # From outside the output dir
    ctx.expect_out_file('source/test_v5.sch', sub=True)
    ctx.expect_out_file('source/deeper.sch', sub=True)
    ctx.expect_out_file('source/sub-sheet.sch', sub=True)
    ctx.expect_out_file('source/test_v5.kicad_pcb', sub=True)
    # Some warnings
    ctx.search_err([r'WARNING:\(W098\)  2 3D models downloaded',   # 2 models are missing and they are downloaded
                    r'WARNING:\(W100\)'])  # 2 models has the same name
    ctx.clean_up()


@pytest.mark.slow
@pytest.mark.skipif(context.ki5(), reason="KiCad 6 aliases used")
def test_copy_files_2(test_dir):
    """ Copy files and 3D models """
    prj = 'copy_files'
    ctx = context.TestContext(test_dir, prj, 'copy_files_2', 'test.files')
    os.environ['KIBOT_3D_MODELS'] = '/tmp'
    ctx.run(kicost=True)  # We use the fake web server
    del os.environ['KIBOT_3D_MODELS']
    # The modified PCB
    ctx.expect_out_file(prj+'.kicad_pcb', sub=True)
    # The 3D models
    for m in MODELS:
        ctx.expect_out_file(m, sub=True)
    # Make sure the PCB points to them
    ctx.search_in_file(prj+'.kicad_pcb', ['model "{}"'.format(r'\$\{KIPRJMOD\}/'+m) for m in MODELS if m.endswith('wrl')],
                       sub=True)
    # Some warnings
    ctx.search_err(r'WARNING:\(W098\)  2 3D models downloaded')   # 2 models are missing and they are downloaded
    ctx.search_err(r'WARNING:\(W100\)', invert=True)   # 2 models has the same name, but goes to different target
    ctx.clean_up()


@pytest.mark.slow
@pytest.mark.skipif(not context.ki7(), reason="Just testing with 7")
def test_copy_files_3(test_dir):
    """ Copy files and 3D models """
    prj = 'copy_files'
    ctx = context.TestContext(test_dir, prj, 'copy_files_3', 'test.files')
    os.environ['KIBOT_3D_MODELS'] = '/tmp'
    ctx.run(kicost=True)  # We use the fake web server
    del os.environ['KIBOT_3D_MODELS']
    # The modified PCB
    prj_s = os.path.join('prj', prj)
    ctx.expect_out_file([prj_s+'.kicad_pcb', prj_s+'.kicad_sch', prj_s+'.kicad_pro', prj_s+'.kicad_prl',
                         'prj/fp-lib-table', 'prj/sym-lib-table', 'prj/symbols/Device.kicad_sym',
                         'prj/footprints/Capacitor_SMD.pretty/C_0805_2012Metric.kicad_mod',
                         'prj/footprints/Resistor_SMD.pretty/R_0805_2012Metric.kicad_mod'], sub=True)
    ctx.expect_out_file(['prj/'+m for m in MODELS], sub=True)
    # Make sure the PCB points to them
    ctx.search_in_file(prj_s+'.kicad_pcb', ['model "{}"'.format(r'\$\{KIPRJMOD\}/'+m) for m in MODELS if m.endswith('wrl')],
                       sub=True)
    ctx.clean_up()


def test_sub_pcb_bp(test_dir):
    """ Test a multiboard example """
    prj = 'batteryPack'
    ctx = context.TestContext(test_dir, prj, 'pcb_variant_sub_pcb_bp', '')
    ctx.run()
    # Check all outputs are there
    fname_b = prj+'-variant_'
    ctx.expect_out_file(fname_b+'battery.kicad_pcb')
    ctx.expect_out_file(fname_b+'charger.kicad_pcb')
    ctx.expect_out_file(fname_b+'connector.kicad_pcb')
    ctx.clean_up(keep_project=True)


@pytest.mark.skipif(context.ki5(), reason="Needs porting")
def test_lcsc_field_known(test_dir):
    """ Test we can detect a known LCSC field name """
    prj = 'lcsc_field_known'
    ctx = context.TestContextSCH(test_dir, prj, 'lcsc_field_detect', 'JLCPCB')
    ctx.run(extra=['_JLCPCB_bom'])
    r, _, _ = ctx.load_csv(prj+'_bom_jlc.csv')
    assert r[0][3] == 'C1234'


@pytest.mark.skipif(context.ki5(), reason="Needs porting")
def test_lcsc_field_unknown(test_dir):
    """ Test we can detect an unknown LCSC field name """
    prj = 'lcsc_field_unknown'
    ctx = context.TestContextSCH(test_dir, prj, 'lcsc_field_detect', 'JLCPCB')
    ctx.run(extra=['_JLCPCB_bom'])
    r, _, _ = ctx.load_csv(prj+'_bom_jlc.csv')
    assert r[0][3] == 'C1234'


@pytest.mark.skipif(context.ki5(), reason="Needs porting")
def test_lcsc_field_specified(test_dir):
    """ Test we select the field
        Also log to existing file """
    prj = 'lcsc_field_unknown'
    ctx = context.TestContextSCH(test_dir, prj, 'lcsc_field_specified', 'JLCPCB')
    log_file = ctx.get_out_path('log')
    with open(log_file, 'w') as f:
        f.write('already there')
    ctx.run(extra=['-L', log_file, '_JLCPCB_bom'])
    assert ctx.search_err('User selected.*Cryptic')
    r, _, _ = ctx.load_csv(prj+'_bom_jlc.csv')
    assert r[0][3] == 'C1234'
    ctx.expect_out_file('log')
    with open(log_file) as f:
        v = f.read()
    assert not v.startswith('already')


@pytest.mark.skipif(context.ki5(), reason="KiKit is v6+")
def test_stencil_3D_1(test_dir):
    prj = 'light_control'
    ctx = context.TestContext(test_dir, prj, 'stencil_3D_1', 'stencil/3D')
    ctx.run(extra=[])
    ctx.expect_out_file_d(prj+'-stencil_3d_top.stl')
    ctx.compare_image(prj+'-stencil_3d_top.png', sub=True, tol=100)
    ctx.clean_up(keep_project=True)


@pytest.mark.slow
@pytest.mark.skipif(context.ki5(), reason="KiKit is v6+")
def test_stencil_steel_1(test_dir):
    prj = 'light_control'
    ctx = context.TestContext(test_dir, prj, 'stencil_for_jig_1', 'stencil/Jig')
    ctx.run(extra=[])
    ctx.expect_out_file_d(prj+'-stencil_for_jig_top.stl')
    ctx.compare_image(prj+'-stencil_for_jig_top.png', sub=True, tol=100)
    ctx.clean_up(keep_project=True)


@pytest.mark.slow
@pytest.mark.skipif(context.ki5(), reason="KiKit is v6+")
def test_panelize_1(test_dir):
    prj = 'light_control'
    ctx = context.TestContext(test_dir, prj, 'panelize_2')
    ctx.run(extra=[])
    if is_debian:
        ctx.compare_image(prj+'-panel.png', tol=100)
    ctx.clean_up(keep_project=True)


@pytest.mark.skipif(not context.ki7(), reason="Uses fonts")
def test_font_and_colors_1(test_dir):
    prj = 'font_and_colors'
    ctx = context.TestContext(test_dir, prj, 'resources_1')
    ctx.run()
    ctx.compare_image(prj+'-top.png')
    ctx.compare_image(prj+'-assembly_page_01.png', tol=DIFF_TOL*1.2)
    ctx.clean_up()


@pytest.mark.skipif(not context.ki7(), reason="Netclass flags")
def test_netclass_flag_1(test_dir):
    prj = 'netclass_flag'
    ctx = context.TestContextSCH(test_dir, prj, 'int_bom_csv_no_info', 'BoM')
    ctx.run()
    ctx.expect_out_file_d(prj+'-bom.csv')
    ctx.clean_up()


def test_value_split_1(test_dir):
    prj = 'value_split'
    ctx = context.TestContextSCH(test_dir, prj, 'value_split_2', 'Modified')
    ctx.run()
    ctx.expect_out_file_d(prj+context.KICAD_SCH_EXT)
    ctx.clean_up()


def test_definitions_1(test_dir):
    prj = 'simple_2layer'
    ctx = context.TestContext(test_dir, prj, 'definitions_top', 'gerberdir')
    ctx.run()
    for la in ['B_Cu', 'F_Cu']:
        for copy in range(2):
            ctx.expect_out_file(f'{prj}-{la}_copper_{copy+1}.gbr')
    for la in ['B_SilkS', 'F_SilkS'] if context.ki5() else ['B_Silkscreen', 'F_Silkscreen']:
        for copy in range(2):
            ctx.expect_out_file(f'{prj}-{la}_silk_{copy+1}.gbr')
    ctx.clean_up()


@pytest.mark.slow
@pytest.mark.skipif(not context.ki7(), reason="Just testing with 7")
def test_populate_1(test_dir):
    """ Using PcbDraw as renderer """
    prj = 'simple_2layer'  # Fake
    ctx = context.TestContext(test_dir, prj, 'populate', 'Populate')
    ctx.run(no_board_file=True, extra=['-b', 'tests/data/ArduinoLearningKitStarter.kicad_pcb', 'Populate'])
    ctx.compare_image('Populate/img/populating_4.png', 'populating_4.png', tol=100)
    ctx.clean_up()


@pytest.mark.slow
@pytest.mark.skipif(not context.ki7(), reason="Just testing with 7")
def test_populate_2(test_dir):
    """ Using Blender as renderer """
    prj = 'simple_2layer'  # Fake
    ctx = context.TestContext(test_dir, prj, 'populate_blender', 'PopulateSimple')
    ctx.run(no_board_file=True, extra=['-b', 'tests/data/ArduinoLearningKitStarter.kicad_pcb'])
    ctx.expect_out_file_d(['img/populating_1.png', 'img/populating_2.png',
                           'ArduinoLearningKitStarter-blender_export.pcb3d', 'index.html'])
    ctx.clean_up()


@pytest.mark.slow
@pytest.mark.skipif(not context.ki7(), reason="Just testing with 7")
def test_present_1(test_dir):
    prj = 'light_control'
    ctx = context.TestContext(test_dir, prj, 'kikit_present_external_1', 'Present/Files')
    ctx.run()
    ctx.expect_out_file_d(['boards/light_control-back.svg', 'boards/light_control-front.svg',
                           'boards/light_control-gerbers.zip', 'boards/light_control.kicad_pcb',
                           'css/styles.css', 'index.html'])
    ctx.clean_up(keep_project=True)


@pytest.mark.slow
@pytest.mark.skipif(not context.ki7(), reason="Just testing with 7")
def test_present_2(test_dir):
    prj = 'light_control'
    ctx = context.TestContext(test_dir, prj, 'kikit_present_local_1', 'Present/Local_1')
    ctx.run()
    ctx.expect_out_file_d(['boards/light_control-back.svg', 'boards/light_control-front.svg',
                           'boards/light_control-gerbers.zip', 'boards/light_control.kicad_pcb',
                           'css/styles.css', 'index.html'])
    ctx.clean_up(keep_project=True)


@pytest.mark.slow
@pytest.mark.skipif(not context.ki7(), reason="Just testing with 7")
def test_present_3(test_dir):
    prj = 'light_control'
    ctx = context.TestContext(test_dir, prj, 'kikit_present_file_1', 'Present/Files')
    ctx.run()
    ctx.expect_out_file_d(['boards/light_control-back.png', 'boards/light_control-front.png',
                           'boards/light_control-gerbers.png', 'boards/light_control.kicad_pcb',
                           'css/styles.css', 'index.html'])
    ctx.search_err('No project description')
    ctx.clean_up(keep_project=True)


@pytest.mark.slow
@pytest.mark.skipif(not context.ki7(), reason="Just testing with 7")
def test_present_4(test_dir):
    """ Gerbers from output, PCB from panel """
    prj = 'simple_2layer'
    ctx = context.TestContext(test_dir, prj, 'kikit_present_out_1', 'Present/Out')
    ctx.run()
    ctx.expect_out_file_d(['boards/simple_2layer-panel-back.svg', 'boards/simple_2layer-panel-front.svg',
                           'boards/simple_2layer-panel-gerbers.zip', 'boards/simple_2layer-panel.kicad_pcb',
                           'css/styles.css', 'index.html'])
    ctx.clean_up(keep_project=True)


def test_groups_1(test_dir):
    """ Groups definitions """
    prj = 'simple_2layer'  # fake
    ctx = context.TestContext(test_dir, prj, 'groups_1')
    ctx.run(no_board_file=True, no_out_dir=True, extra=['--list'])
    ctx.search_out(['fab: gerbers, excellon_drill, position', 'plot: PcbDraw, PcbDraw2, SVG', 'fab_svg: fab, SVG'])
    ctx.clean_up()


def test_groups_2(test_dir):
    """ Imported groups and outputs """
    prj = 'simple_2layer'  # fake
    ctx = context.TestContext(test_dir, prj, 'import_test_internal_group')
    ctx.run(no_board_file=True, no_out_dir=True, extra=['--only-groups', '--only-names', '--list'])
    ctx.search_out('_Elecrow')
    ctx.run(no_board_file=True, no_out_dir=True, extra=['--only-names', '--list'])
    ctx.search_out(['_Elecrow_compress', '_Elecrow_drill', '_Elecrow_gerbers'])
    ctx.clean_up()


@pytest.mark.indep
def test_info_1(test_dir):
    """ System information """
    prj = 'simple_2layer'  # fake
    ctx = context.TestContext(test_dir, prj, 'info_1')
    ctx.run()
    ctx.expect_out_file(prj+'-info.txt')
    ctx.clean_up()


@pytest.mark.skipif(not context.ki7(), reason="Just v7 test")
def test_kicanvas_1(test_dir):
    prj = 'resistor_tht'
    ctx = context.TestContext(test_dir, prj, 'kicanvas_1', 'KiCanvas')
    ctx.run(extra=['KiCanvas'])
    ctx.expect_out_file_d(['kicanvas.js', prj+'-kicanvas.html', prj+'.kicad_pcb', prj+'.kicad_sch', prj+'.kicad_pro'])
    ctx.clean_up(keep_project=True)


@pytest.mark.skipif(not context.ki7(), reason="Just v7 test")
def test_only_pcb_bad_ref(test_dir):
    prj = 'only_pcb_bad_ref'
    ctx = context.TestContext(test_dir, prj, 'simple_position_dummy_filter', '')
    ctx.run()
    ctx.search_err('Not including component')
    ctx.clean_up()


def test_report_variant_t1(test_dir):
    prj = 'kibom-variante'
    ctx = context.TestContextSCH(test_dir, prj, 'int_bom_var_t1_csv', '')
    ctx.run()
    ctx.search_in_file(prj+'-report.txt', [r'|\s+Total\s+|\s+40\s+|\s+52'])
    ctx.search_in_file(prj+'-report_(V1).txt', [r'|\s+Total\s+|\s+4\s+|\s+5\.'])
    ctx.clean_up()


# ODB++ export using kicad-cli on KiCad 9+
@pytest.mark.skipif(not context.ki9(), reason="Needs KiCad 9")
def test_odb_zip(test_dir):
    prj = 'light_control'
    ctx = context.TestContext(test_dir, prj, 'odb_zip_mm', 'Export')
    ctx.run()
    ctx.expect_out_file(prj+'-odb.zip', sub=True)
    ctx.clean_up(keep_project=True)


# IPC-2581 export using kicad-cli on KiCad 9+
@pytest.mark.skipif(not context.ki9(), reason="Needs KiCad 9")
def test_ipc2581_xml(test_dir):
    prj = 'light_control'
    ctx = context.TestContext(test_dir, prj, 'ipc2581_xml_mils', 'Export')
    ctx.run()
    ctx.expect_out_file(prj+'-IPC-2581.xml', sub=True)
    ctx.clean_up(keep_project=True)


def test_vrml_1(test_dir):
    prj = 'light_control'
    ctx = context.TestContext(test_dir, prj, 'vrml_1')
    ctx.run()
    ctx.expect_out_file(prj+'-vrml.wrl')
    ctx.search_err('Missing component in generated VRML', invert=True)
    ctx.clean_up(keep_project=True)
