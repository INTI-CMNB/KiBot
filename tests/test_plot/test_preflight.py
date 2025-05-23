"""
Tests for the preflight options

We test:
- ERC
- DRC
  - ignore_unconnected
  - error
  - filter
- XML update

For debug information use:
pytest-3 --log-cli-level debug

"""
import json
import logging
import pytest
import os
import re
import shutil
from subprocess import run, PIPE
from . import context
from kibot.misc import (DRC_ERROR, ERC_ERROR, BOM_ERROR, CORRUPTED_PCB, CORRUPTED_SCH, EXIT_BAD_CONFIG, NETLIST_DIFF,
                        CHECK_FIELD, IGNORED_ERRORS)


@pytest.mark.slow
@pytest.mark.eeschema
def test_erc_1(test_dir):
    prj = 'bom'
    ctx = context.TestContext(test_dir, prj, 'erc', '')
    ctx.run()
    # Check all outputs are there
    ctx.expect_out_file(prj+'-erc.txt')
    ctx.clean_up()


@pytest.mark.skipif(not context.ki8(), reason="Needs ERC CLI")
def test_erc_k8_1(test_dir):
    prj = 'bom'
    ctx = context.TestContext(test_dir, prj, 'erc_k8', '')
    ctx.run()
    # Check all outputs are there
    ctx.expect_out_file(prj+'-erc.html')
    ctx.expect_out_file(prj+'-erc.rpt')
    ctx.expect_out_file(prj+'-erc.csv')
    ctx.expect_out_file(prj+'-erc.json')
    ctx.clean_up()


@pytest.mark.slow
@pytest.mark.eeschema
def test_erc_fail_1(test_dir):
    """ Using an SCH with ERC errors """
    prj = 'fail-erc'
    ctx = context.TestContext(test_dir, prj, 'erc', '')
    ctx.run(ERC_ERROR)
    # Check all outputs are there
    ctx.expect_out_file(prj+'-erc.txt')
    ctx.clean_up()


@pytest.mark.skipif(not context.ki8(), reason="Needs ERC CLI")
def test_erc_fail_k8_1(test_dir):
    """ Using an SCH with ERC errors """
    prj = 'fail-erc'
    ctx = context.TestContext(test_dir, prj, 'erc_k8', '')
    ctx.run(ERC_ERROR)
    # Check all outputs are there
    ctx.expect_out_file(prj+'-erc.html')
    ctx.expect_out_file(prj+'-erc.rpt')
    ctx.expect_out_file(prj+'-erc.csv')
    ctx.expect_out_file(prj+'-erc.json')
    ctx.clean_up()


@pytest.mark.skipif(not context.ki8(), reason="Needs ERC CLI")
def test_erc_fail_k8_2(test_dir):
    """ Test don't stop """
    prj = 'fail-erc'
    ctx = context.TestContext(test_dir, prj, 'erc_k8_dont_stop', '')
    ctx.run()
    # Check all outputs are there
    ctx.expect_out_file(prj+'-erc.html')
    ctx.expect_out_file(prj+'-erc.rpt')
    ctx.expect_out_file(prj+'-erc.csv')
    ctx.expect_out_file(prj+'-erc.json')
    ctx.clean_up()


def test_erc_fail_2(test_dir):
    """ Using a dummy SCH """
    prj = '3Rs'
    ctx = context.TestContext(test_dir, prj, 'erc', '')
    ctx.run(CORRUPTED_SCH)
    ctx.clean_up()


@pytest.mark.slow
@pytest.mark.eeschema
def test_erc_warning_1(test_dir):
    """ Using an SCH with ERC warnings """
    prj = 'warning-project'
    ctx = context.TestContextSCH(test_dir, 'erc_warning/'+prj, 'erc', '')
    ctx.run()
    # Check all outputs are there
    ctx.expect_out_file(prj+'-erc.txt')
    ctx.search_err(r"WARNING:\(W058\) 1 ERC warnings detected")
    ctx.clean_up(keep_project=context.ki7())


@pytest.mark.skipif(not context.ki8(), reason="Needs ERC CLI")
def test_erc_warning_k8_1(test_dir):
    """ Using an SCH with ERC warnings """
    prj = 'warning-project'
    ctx = context.TestContextSCH(test_dir, 'erc_warning/'+prj, 'erc_k8', '')
    ctx.run()
    # Check all outputs are there
    ctx.expect_out_file(prj+'-erc.html')
    ctx.expect_out_file(prj+'-erc.rpt')
    ctx.expect_out_file(prj+'-erc.csv')
    ctx.expect_out_file(prj+'-erc.json')
    ctx.search_err(r"WARNING:\(W142\) 1 ERC warnings detected")
    ctx.search_err(r"WARNING:\(W144\)")
    ctx.clean_up(keep_project=context.ki7())


@pytest.mark.slow
@pytest.mark.eeschema
def test_erc_warning_2(test_dir):
    """ Using an SCH with ERC warnings as errors """
    prj = 'warning-project'
    ctx = context.TestContextSCH(test_dir, 'erc_warning/'+prj, 'erc_no_w', 'def_dir')
    ctx.run(ERC_ERROR)
    # Check all outputs are there
    ctx.expect_out_file(prj+'-erc.txt', sub=True)
    ctx.search_err(r"ERROR:1 ERC errors detected")
    ctx.clean_up(keep_project=context.ki7())


@pytest.mark.skipif(not context.ki8(), reason="Needs ERC CLI")
def test_erc_warning_k8_2(test_dir):
    """ Using an SCH with ERC warnings as errors """
    prj = 'warning-project'
    ctx = context.TestContextSCH(test_dir, 'erc_warning/'+prj, 'erc_no_w_k8', 'def_dir')
    ctx.run(ERC_ERROR)
    # Check all outputs are there
    ctx.expect_out_file(prj+'-erc.html', sub=True)
    ctx.search_err(r"ERC warnings: 1, promoted as errors")
    ctx.clean_up(keep_project=context.ki7())


@pytest.mark.slow
@pytest.mark.eeschema
def test_erc_warning_3(test_dir):
    """ Using an SCH with ERC warnings as errors """
    prj = 'warning-project'
    ctx = context.TestContextSCH(test_dir, 'erc_warning/'+prj, 'erc_no_w_2', 'def_dir')
    ctx.run(ERC_ERROR)
    # Check all outputs are there
    ctx.expect_out_file(prj+'-erc.txt', sub=True)
    ctx.search_err(r"ERROR:1 ERC errors detected")
    ctx.clean_up(keep_project=context.ki7())


@pytest.mark.skipif(not context.ki8(), reason="Needs ERC CLI")
def test_erc_warning_k8_3(test_dir):
    """ Using an SCH with ERC warnings as errors """
    prj = 'warning-project'
    ctx = context.TestContextSCH(test_dir, 'erc_warning/'+prj, 'erc_no_w_2_k8', 'def_dir')
    ctx.run(ERC_ERROR)
    # Check all outputs are there
    ctx.expect_out_file(prj+'-erc.html', sub=True)
    ctx.search_err(r"ERC warnings: 1, promoted as errors")
    ctx.clean_up(keep_project=context.ki7())


@pytest.mark.skipif(not context.ki8(), reason="Needs ERC CLI")
def test_erc_warning_k8_4(test_dir):
    """ Using an SCH with ERC warnings as errors, using ERC options """
    prj = 'warning-project'
    ctx = context.TestContextSCH(test_dir, 'erc_warning/'+prj, 'erc_no_w2_k8', 'def_dir')
    ctx.run(ERC_ERROR)
    # Check all outputs are there
    ctx.expect_out_file(prj+'-erc.html', sub=True)
    ctx.search_err(r"ERC warnings: 1, promoted as errors")
    ctx.clean_up(keep_project=context.ki7())


@pytest.mark.slow
@pytest.mark.eeschema
@pytest.mark.skipif(not context.ki7(), reason="KiCad 7 off grid check")
def test_erc_off_grid_1(test_dir):
    """ ERC using 25 mils grid """
    prj = 'off-grid'
    ctx = context.TestContextSCH(test_dir, prj, 'erc_grid_25')
    ctx.run()
    # Check all outputs are there
    ctx.expect_out_file(prj+'-erc.txt', sub=True)
    ctx.clean_up(keep_project=context.ki8())


@pytest.mark.slow
@pytest.mark.pcbnew
def test_drc_1(test_dir):
    prj = name = 'bom'
    if context.ki7():
        prj = name = 'bom_ok_drc'
    ctx = context.TestContext(test_dir, prj, 'drc', '')
    ctx.run()
    # Check all outputs are there
    ctx.expect_out_file(name+'-drc.txt')
    ctx.clean_up(keep_project=context.ki7())


@pytest.mark.skipif(not context.ki8(), reason="Needs DRC CLI")
def test_drc_k8_1(test_dir):
    prj = name = 'bom_ok_drc'
    ctx = context.TestContext(test_dir, prj, 'drc_k8', '')
    ctx.run()
    # Check all outputs are there
    ctx.expect_out_file(name+'-drc.rpt')
    ctx.expect_out_file(name+'-drc.html')
    ctx.expect_out_file(name+'-drc.csv')
    ctx.expect_out_file(name+'-drc.json')
    ctx.clean_up(keep_project=True)


@pytest.mark.slow
@pytest.mark.pcbnew
def test_drc_filter_1(test_dir):
    """ Test using internal filters """
    prj = 'fail-project'
    ctx = context.TestContext(test_dir, prj, 'drc_filter', 'def_dir')
    ctx.run(extra_debug=True)
    # Check all outputs are there
    ctx.expect_out_file(prj+'-drc.txt', sub=True)
    ctx.expect_out_file('kibot_errors.filter', sub=True)
    ctx.clean_up(keep_project=True)


@pytest.mark.skipif(not context.ki8(), reason="Needs DRC CLI")
def test_drc_filter_k8_1(test_dir):
    """ Test using internal filters """
    prj = 'fail-project'
    ctx = context.TestContext(test_dir, prj, 'drc_filter_k8', 'def_dir')
    ctx.run(extra_debug=True)
    # Check all outputs are there
    ctx.expect_out_file(prj+'-drc.html', sub=True)
    ctx.expect_out_file(prj+'-drc.csv', sub=True)
    ctx.expect_out_file(prj+'-drc.rpt', sub=True)
    ctx.expect_out_file(prj+'-drc.json', sub=True)
    ctx.clean_up(keep_project=True)


@pytest.mark.slow
@pytest.mark.pcbnew
@pytest.mark.skipif(context.ki5(), reason="KiCad 6 exclusions")
def test_drc_filter_2(test_dir):
    """ Test using KiCad 6 exclusions """
    prj = 'fail-project'
    ctx = context.TestContext(test_dir, prj, 'drc_filter_k6_exc', '')
    ctx.run(extra_debug=True)
    # Check all outputs are there
    ctx.expect_out_file(prj+'-drc.txt')
    ctx.expect_out_file('kibot_errors.filter')
    ctx.clean_up(keep_project=True)


@pytest.mark.skipif(not context.ki8(), reason="Needs DRC CLI")
def test_drc_filter_ki8_2(test_dir):
    """ Test using KiCad 6 exclusions """
    prj = 'fail-project'
    ctx = context.TestContext(test_dir, prj, 'drc_filter_k8_exc', '')
    ctx.run(extra_debug=True)
    # Check all outputs are there
    ctx.expect_out_file(prj+'-drc.html')
    ctx.clean_up(keep_project=True)


@pytest.mark.slow
@pytest.mark.pcbnew
def test_drc_unco_1(test_dir):
    """ Check we can ignore unconnected nets. Old style """
    prj = 'warning-project'
    ctx = context.TestContext(test_dir, prj, 'drc_unco', '')
    ctx.run()
    # Check all outputs are there
    ctx.expect_out_file(prj+'-drc.txt')
    ctx.clean_up()


@pytest.mark.skipif(not context.ki8(), reason="Needs DRC CLI")
def test_drc_unco_k8_1(test_dir):
    """ Check we can ignore unconnected nets. Old style """
    prj = 'warning-project'
    ctx = context.TestContext(test_dir, prj, 'drc_unco_k8', '')
    ctx.run()
    # Check all outputs are there
    ctx.expect_out_file(prj+'-drc.html')
    ctx.clean_up()


@pytest.mark.slow
@pytest.mark.pcbnew
def test_drc_unco_2(test_dir):
    """ Check we can ignore unconnected nets. New style """
    prj = 'warning-project'
    ctx = context.TestContext(test_dir, prj, 'drc_unco_2', 'def_dir')
    ctx.run()
    # Check all outputs are there
    ctx.expect_out_file(prj+'-drc.txt', sub=True)
    ctx.clean_up()


@pytest.mark.skipif(not context.ki8(), reason="Needs DRC CLI")
def test_drc_unco_k8_2(test_dir):
    """ Check we can ignore unconnected nets. New style """
    prj = 'warning-project'
    ctx = context.TestContext(test_dir, prj, 'drc_unco_2_k8', 'def_dir')
    ctx.run()
    # Check all outputs are there
    ctx.expect_out_file(prj+'-drc.html', sub=True)
    ctx.clean_up()


@pytest.mark.slow
@pytest.mark.pcbnew
def test_drc_error(test_dir):
    """ Check we catch DRC errors """
    prj = 'warning-project'
    ctx = context.TestContext(test_dir, prj, 'drc', '')
    ctx.run(DRC_ERROR)
    # Check all outputs are there
    ctx.expect_out_file(prj+'-drc.txt')
    ctx.clean_up()


@pytest.mark.skipif(not context.ki8(), reason="Needs DRC CLI")
def test_drc_error_k8_1(test_dir):
    """ Check we catch DRC errors """
    prj = 'warning-project'
    ctx = context.TestContext(test_dir, prj, 'drc_k8', '')
    ctx.run(DRC_ERROR)
    # Check all outputs are there
    ctx.expect_out_file(prj+'-drc.html')
    ctx.clean_up()


@pytest.mark.skipif(not context.ki8(), reason="Needs DRC CLI")
def test_drc_error_k8_2(test_dir):
    """ Check we can ignore DRC errors """
    prj = 'warning-project'
    ctx = context.TestContext(test_dir, prj, 'drc_k8_ds', '')
    ctx.run()
    # Check all outputs are there
    ctx.expect_out_file(prj+'-drc.html')
    ctx.search_err('Missing connection between items')
    ctx.clean_up()


@pytest.mark.skipif(not context.ki8(), reason="Needs DRC CLI")
def test_drc_error_k8_3(test_dir):
    """ Check we can ignore DRC errors, and then get an error """
    prj = 'warning-project'
    ctx = context.TestContext(test_dir, prj, 'drc_k8_ds', '')
    ctx.run(IGNORED_ERRORS, extra=['-F'])
    # Check all outputs are there
    ctx.expect_out_file(prj+'-drc.html')
    ctx.search_err('Missing connection between items')
    ctx.clean_up()


@pytest.mark.slow
@pytest.mark.pcbnew
def test_drc_fail(test_dir):
    """ Check we dummy PCB """
    prj = 'bom_no_xml'
    ctx = context.TestContext(test_dir, prj, 'drc', '')
    ctx.run(CORRUPTED_PCB)
    ctx.clean_up()


@pytest.mark.slow
@pytest.mark.pcbnew
@pytest.mark.skipif(context.ki6(), reason="KiCad 6+ can't time-out")
def test_drc_time_out(test_dir):
    prj = 'bom'
    ctx = context.TestContext(test_dir, prj, 'drc_time_out', '')
    ctx.run(DRC_ERROR)
    ctx.search_err('Time out detected')
    ctx.search_err('kiauto_wait_start must be integer')
    ctx.clean_up()


@pytest.mark.skipif(not context.ki8(), reason="Needs DRC CLI")
def test_drc_parity_1(test_dir):
    prj = 'pcb_parity'
    ctx = context.TestContext(test_dir, prj, 'drc_parity', '')
    # ctx.run(ret_val=NETLIST_DIFF, extra_debug=True)
    ctx.run(extra_debug=True)
    errors = ["Missing footprint FID1 .Fiducial.",
              "Pad net .VCC. doesn't match net given by schematic .GND.",
              "Pad net .Net-.C1-Pad1.. doesn't match net given by schematic .unconnected-.C1-Pad1..",
              "Pad net .Net-.C1-Pad1.. doesn't match net given by schematic .Net-.R1-Pad2.."]
    if context.ki9():
        # Is that supposed to be an improvement?
        errors.extend(["Capacitor_SMD:C_0805_2012Metric doesn't match footprint given by symbol",
                       "Value .R1. doesn't match symbol value .100."])
    else:
        errors.extend(["C1 footprint .Capacitor_SMD:C_0805_2012Metric. doesn't match that given by symbol",
                       "Footprint R1 value .100. doesn't match symbol value .120."])
    ctx.search_err(errors)
    ctx.clean_up()


@pytest.mark.slow
@pytest.mark.eeschema
def test_update_xml_1(test_dir):
    prj = 'bom'
    ctx = context.TestContext(test_dir, prj, 'update_xml', '')
    # The XML should be created where the schematic is located
    xml = os.path.abspath(os.path.join(ctx.get_board_dir(), prj+'.xml'))
    os.replace(xml, xml+'-bak')
    try:
        ctx.run()
        # Check all outputs are there
        # ctx.expect_out_file(prj+'.csv')
        assert os.path.isfile(xml)
        assert os.path.getsize(xml) > 0
        logging.debug(os.path.basename(xml)+' OK')
    finally:
        os.remove(xml)
        os.replace(xml+'-bak', xml)
    ctx.clean_up()


@pytest.mark.slow
@pytest.mark.eeschema
@pytest.mark.skipif(context.ki5() or context.ki8(), reason="KiCad 6+ implementation")
def test_update_xml_2(test_dir):
    prj = 'pcb_parity'
    ctx = context.TestContext(test_dir, prj, 'update_xml_2', '')
    # The XML should be created where the schematic is located
    xml = os.path.abspath(os.path.join(ctx.get_board_dir(), prj+'.xml'))
    ctx.run(ret_val=NETLIST_DIFF, extra_debug=True)
    # Check all outputs are there
    # ctx.expect_out_file(prj+'.csv')
    assert os.path.isfile(xml)
    assert os.path.getsize(xml) > 0
    logging.debug(os.path.basename(xml)+' OK')
    ctx.search_err(["C1 footprint mismatch",
                    "R1 value mismatch .PCB: .100. vs schematic: .120",
                    "R1 schematic property .Sheetname. not in PCB",
                    "R1 PCB property .Size. not in schematic ",
                    "F1 found in PCB, but not in schematic",
                    "FID1 found in schematic, but not in PCB",
                    "Net count mismatch .PCB 3 vs schematic 4.",
                    "Net .Net-.C1-Pad1.. not in schematic",
                    "Net .Net-.R1-Pad2.. not in PCB",
                    "Net .VCC. extra PCB connection/s: R2 pin 2"])
    ctx.clean_up()


@pytest.mark.slow
@pytest.mark.eeschema
@pytest.mark.skipif(context.ki5() or context.ki8(), reason="KiCad 6+ implementation")
def test_update_xml_not_in_bom(test_dir):
    prj = 'parity_not_in_bom'
    ctx = context.TestContext(test_dir, prj, 'update_xml_2', '')
    # The XML should be created where the schematic is located
    xml = os.path.abspath(os.path.join(ctx.get_board_dir(), prj+'.xml'))
    ctx.run()
    # Check all outputs are there
    assert os.path.isfile(xml)
    assert os.path.getsize(xml) > 0
    logging.debug(os.path.basename(xml)+' OK')
    if context.ki6() and not context.ki7():
        ctx.search_err("R2 excluded from BoM")
    ctx.clean_up()


@pytest.mark.slow
@pytest.mark.eeschema
def test_update_xml_fail(test_dir):
    """ Using a dummy SCH """
    prj = '3Rs'
    ctx = context.TestContext(test_dir, prj, 'update_xml', '')
    ctx.run(BOM_ERROR)
    ctx.clean_up()


def test_sch_replace_1(test_dir):
    """ Tags replacements in an schematic """
    prj = 'test_v5'
    ctx = context.TestContext(test_dir, prj, 'sch_replace_1', '')
    ctx.run(extra=[])
    files = {}
    file = ctx.sch_file
    files[file] = file + '-bak'
    file = ctx.sch_file.replace('test_v5', 'deeper')
    files[file] = file + '-bak'
    file = ctx.sch_file.replace('test_v5', 'sub-sheet')
    files[file] = file + '-bak'
    for v in files.values():
        assert os.path.isfile(v), v
        assert os.path.getsize(v) > 0
    try:
        for k in files.keys():
            logging.debug(k)
            cmd = ['/bin/bash', '-c', "date -d @`git log -1 --format='%at' -- " + k + "` +%Y-%m-%d_%H-%M-%S"]
            text = run(cmd, stdout=PIPE, stderr=PIPE, universal_newlines=True).stdout.strip()
            with open(k, 'rt') as f:
                c = f.read()
            if context.ki5():
                m = re.search(r'^Date "((?:[^"]|\\")*)"$', c, re.MULTILINE)
            else:
                m = re.search(r'\(date "((?:[^"]|\\")*)"\)', c, re.MULTILINE)
            logging.debug('Date: ' + text)
            assert m is not None
            assert m.group(1) == text
            if 'test_v5' in k:
                cmd = ['/bin/bash', '-c', "git log -1 --format='%h' " + k]
                text = run(cmd, stdout=PIPE, stderr=PIPE, universal_newlines=True).stdout.strip()
                m = re.search("Git_hash:'(.*)'", c)
                logging.debug('Hash: ' + text)
                assert m is not None
                assert m.group(1) == text
    finally:
        for k, v in files.items():
            os.replace(v, k)
    ctx.clean_up()


def test_pcb_replace_1(test_dir):
    """ Tags replacements in a PCB """
    prj = 'light_control'
    ctx = context.TestContext(test_dir, prj, 'pcb_replace_1', '')
    ctx.run(extra=[])
    file = ctx.board_file
    file_back = file + '-bak'
    assert os.path.isfile(file_back), file_back
    assert os.path.getsize(file_back) > 0
    try:
        logging.debug(file)
        cmd = ['/bin/bash', '-c', "date -d @`git log -1 --format='%at' -- " + file + "` +%Y-%m-%d_%H-%M-%S"]
        text = run(cmd, stdout=PIPE, stderr=PIPE, universal_newlines=True).stdout.strip()
        with open(file, 'rt') as f:
            c = f.read()
        m = re.search(r'^    \(date (\S+|"(?:[^"]|\\")+")\)$', c, re.MULTILINE)
        logging.debug('Date: ' + text)
        assert m is not None
        assert m.group(1) == '"' + text + '"'
        cmd = ['/bin/bash', '-c', "git log -1 --format='%h' " + file]
        text = run(cmd, stdout=PIPE, stderr=PIPE, universal_newlines=True).stdout.strip()
        m = re.search("Git_hash:'(.*)'", c)
        logging.debug('Hash: ' + text)
        assert m is not None
        assert m.group(1) == text
    finally:
        os.replace(file_back, file)
    ctx.clean_up(keep_project=True)


def test_set_text_variables_1(test_dir):
    """ KiCad 6 variables """
    prj = 'test_vars'
    ctx = context.TestContextSCH(test_dir, prj, 'set_text_variables_1', '')
    if context.ki5():
        ctx.run(EXIT_BAD_CONFIG)
    else:
        ctx.run(extra_debug=True)
        file = os.path.join(ctx.get_board_dir(), ctx.board_name+context.PRO_EXT)
        file_back = file + '-bak'
        assert os.path.isfile(file_back), file_back
        assert os.path.getsize(file_back) > 0
        try:
            logging.debug(file)
            cmd = ['/bin/bash', '-c', "git log -1 --format='%h' " + ctx.sch_file]
            hash = run(cmd, stdout=PIPE, stderr=PIPE, universal_newlines=True).stdout.strip()
            text = "Git_hash:'{}' ({})".format(hash, prj)
            with open(file, 'rt') as f:
                c = f.read()
            data = json.loads(c)
            assert 'text_variables' in data
            assert 'Comment4' in data['text_variables']
            assert data['text_variables']['Comment4'] == text
        finally:
            os.replace(file_back, file)
        ctx.expect_out_file(prj+'-bom_'+hash+'.csv')
    ctx.clean_up(keep_project=True)


@pytest.mark.skipif(context.ki5(), reason="KiCad 6 text vars (fail already tested)")
def test_set_text_variables_2(test_dir):
    """ KiCad 6 variables, test volatile changes (project restored) """
    prj = 'test_vars'
    ctx = context.TestContextSCH(test_dir, prj, 'set_text_variables_2', '')
    ctx.run()
    file = os.path.join(ctx.get_board_dir(), ctx.board_name+context.PRO_EXT)
    file_back = file + '-bak'
    assert os.path.isfile(file_back), file_back
    assert os.path.getsize(file_back) > 0
    try:
        logging.debug(file)
        cmd = ['/bin/bash', '-c', "git log -1 --format='%h' " + ctx.sch_file]
        hash = run(cmd, stdout=PIPE, stderr=PIPE, universal_newlines=True).stdout.strip()
        with open(file, 'rt') as f:
            c = f.read()
        data = json.loads(c)
        assert 'text_variables' in data
        assert 'Comment4' not in data['text_variables']
    finally:
        os.replace(file_back, file)
    ctx.expect_out_file(prj+'-bom_'+hash+'.csv')
    ctx.clean_up(keep_project=True)


def test_update_footprint_1(test_dir):
    """ Try updating 2 footprints from the lib """
    prj = 'update_footprint_1'
    ctx = context.TestContext(test_dir, 'update_footprint_1/update_footprint_1', prj, 'SVG')
    # Copy the ref file
    shutil.copy2(ctx.board_file+'.ok', ctx.board_file)
    ctx.run(extra=[])
    o = prj+'-F_Silk.svg'
    shutil.copy2(ctx.board_file+'.ok', ctx.board_file)
    ctx.expect_out_file_d(o)
    ctx.compare_image(o, sub=True)
    ctx.clean_up(keep_project=True)


@pytest.mark.skipif(not context.ki7(), reason="Needs board characteristics")
def test_update_pcb_characteristics_1(test_dir):
    """ update_pcb_characteristics ENIG -> ENEPIG
        update_stackup 21116 -> FR408-HR, add a Polyimide prepreg """
    prj = 'board_characteristics'
    ctx = context.TestContext(test_dir, prj, 'update_pcb_characteristics', relaxed=True)
    # Copy the ref file
    shutil.copy2(ctx.board_file+'.ok', ctx.board_file)
    ctx.run(extra=[])
    ctx.search_in_file(ctx.board_file, ['gr_text "ENEPIG"', 'gr_text "FR408-HR"', 'gr_text "Polyimide"'])
    ctx.search_not_in_file(ctx.board_file, ['gr_text "ENIG"', 'gr_text "21116"'])
    file_back = ctx.board_file + '-bak'
    assert os.path.isfile(file_back), file_back
    os.remove(file_back)
    ctx.clean_up()


@pytest.mark.skipif(not context.ki7(), reason="Needs board characteristics")
def test_update_pcb_characteristics_2(test_dir):
    """ update_stackup remove layers  """
    prj = 'board_characteristics_2'
    ctx = context.TestContext(test_dir, prj, 'update_pcb_characteristics', relaxed=True)
    # Copy the ref file
    shutil.copy2(ctx.board_file+'.ok', ctx.board_file)
    ctx.run(extra=[])
    ctx.search_not_in_file(ctx.board_file, ['gr_text "In1.Cu"', 'gr_text "In2.Cu"'])
    file_back = ctx.board_file + '-bak'
    assert os.path.isfile(file_back), file_back
    os.remove(file_back)
    ctx.clean_up()


@pytest.mark.skipif(not context.ki7(), reason="Implemented for 7 and up")
def test_draw_stackup_1(test_dir):
    """ Draw a stackup and compare """
    prj = 'draw_stackup'
    ctx = context.TestContext(test_dir, prj, 'draw_stackup_1', relaxed=True)
    # Copy the ref file
    shutil.copy2(ctx.board_file+'.ok', ctx.board_file)
    ctx.run(extra=['PDF'])
    ctx.compare_pdf('stackup.pdf')
    file_back = ctx.board_file + '-bak'
    assert os.path.isfile(file_back), file_back
    os.remove(file_back)
    ctx.clean_up()


# No reference yet
# @pytest.mark.skipif(not context.ki7(), reason="Implemented for 7 and up")
# def test_draw_stackup_2(test_dir):
#     """ Draw a stackup and compare """
#     prj = 'draw_stackup'
#     ctx = context.TestContext(test_dir, prj, 'draw_stackup_2', relaxed=True)
#     # Copy the ref file
#     shutil.copy2(ctx.board_file+'.ok', ctx.board_file)
#     ctx.run(extra=['PDF'])
#     ctx.compare_pdf('stackup.pdf')
#     file_back = ctx.board_file + '-bak'
#     assert os.path.isfile(file_back), file_back
#     os.remove(file_back)
#     ctx.clean_up()


@pytest.mark.skipif(not context.ki8(), reason="Test for 8 and up")
def test_check_fields_1(test_dir):
    """ Simple check for temperature range """
    prj = 'temp_range'
    ctx = context.TestContextSCH(test_dir, prj, 'check_fields_temp_1')
    ctx.run()
    ctx.search_err([r"WARNING:\(W162\) R2 field `Temp` doesn't match", r"WARNING:\(W162\) R4 field `Temp` fails -5.0 <= -10"])
    ctx.search_out(['R3 field `Temp` fails 20.0 >= 85', 'R5 field `Temp` fails 60.0 >= 85'])
    ctx.clean_up()


@pytest.mark.skipif(not context.ki8(), reason="Test for 8 and up")
def test_check_fields_2(test_dir):
    """ Simple check for temperature range """
    prj = 'temp_range'
    ctx = context.TestContextSCH(test_dir, prj, 'check_fields_temp_2')
    ctx.run(CHECK_FIELD)
    ctx.search_err([r"WARNING:\(W162\) R1 missing field `Temp`", "ERROR:R2 field `Temp` doesn't match"])
    ctx.clean_up()


@pytest.mark.skipif(not context.ki8(), reason="Implemented for 8 and up")
def test_include_table_1(test_dir):
    """ Draw tables and compare """
    prj = 'test_points'
    ctx = context.TestContext(test_dir, prj, 'test_points_table_1')
    # Back-up the file
    shutil.copy2(ctx.board_file, ctx.board_file+'.ok')
    # First run without prefligh to generate the CSVs
    ctx.run(extra=['-s', 'all', 'testpoints', 'position'])
    # Second run with prefligh to generate the SVG plot
    ctx.run(extra=['SVG'])
    shutil.copy2(ctx.board_file+'.ok', ctx.board_file)
    shutil.copy2(ctx.board_file, ctx.get_out_path(prj+'.kicad_pcb'))
    file_back = ctx.board_file + '-bak'
    assert os.path.isfile(file_back), file_back
    os.remove(file_back)
    os.remove(ctx.board_file+'.ok')
    ctx.compare_image('include_table_1.svg')
    ctx.clean_up(keep_project=True)
