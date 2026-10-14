from decimal import Decimal as D
import os
import re
import pytest
import coverage
import logging
import requests
import subprocess
import sys
from . import context
from kibot.layer import Layer
from kibot.pre_base import BasePreFlight
from kibot.out_base import BaseOutput
from kibot.gs import GS
from kibot.kiplot import load_actions, _import, load_board, generate_makefile, get_columns
from kibot.dep_downloader import search_as_plugin
from kibot.registrable import RegOutput, RegFilter
from kibot.misc import (WRONG_INSTALL, BOM_ERROR, DRC_ERROR, ERC_ERROR, PDF_PCB_PRINT, KICAD2STEP_ERR)
from kibot.bom.columnlist import ColumnList
from kibot.bom.units import get_prefix, comp_match
import kibot.bom.units as units
from kibot.bom.electro_grammar import parse
from kibot.__main__ import detect_kicad
from kibot.kicad.config import KiConf
from kibot.globals import Globals
from kibot.PcbDraw.unit import read_resistance
from kibot.out_download_datasheets import Download_Datasheets_Options

cov = coverage.Coverage()
mocked_check_output_FNF = True
mocked_check_output_retOK = ''
mocked_call_enabled = False
subprocess_run = None


# Important note:
# - We can't load the plug-ins twice, the import fails.
# - Once we patched them using monkey patch the patch isn't reverted unless we load them again.
# I don't know the real reason, may be related to the way we load plug-ins.
# For this reason this patch is used for more than one case.
def mocked_check_output(cmd, stderr=None, text=False):
    logging.debug('mocked_check_output called')
    if mocked_check_output_FNF:
        raise FileNotFoundError()
    else:
        if mocked_check_output_retOK:
            return mocked_check_output_retOK
        e = subprocess.CalledProcessError(10, 'rar')
        e.output = b'THE_ERROR'
        raise e


def mocked_run(command, change_to):
    logging.error('mocked_run')
    e = subprocess.CalledProcessError(10, 'rar')
    e.output = b'THE_ERROR'
    raise e


def mocked_call(cmd, exit_with=None):
    if mocked_call_enabled:
        logging.debug('Forcing fail on '+str(cmd))
        if exit_with is not None:
            logging.error(cmd[0]+' returned %d', 5)
            sys.exit(exit_with)
        return 5
    return subprocess.call(cmd)


def patch_functions(m):
    m.setattr("subprocess.check_output", mocked_check_output)
    m.setattr('kibot.kiplot.exec_with_retry', mocked_call)
    GS.exec_with_retry = mocked_call


def init_globals():
    glb = Globals()
    glb.set_tree({})
    glb.config(None)


def run_compress(ctx, test_import_fail=False):
    with context.cover_it(cov):
        # Load the plug-ins
        load_actions()
        init_globals()
        # Create a compress object with the dummy file as source
        out = RegOutput.get_class_for('compress')()
        out.set_tree({'type': 'compress', 'options': {'format': 'RAR', 'files': [{'source': ctx.get_out_path('*')}]}})
        out.config(None)
        # Setup the GS output dir, needed for the output path
        GS.out_dir = '.'
        # Run the compression and catch the error
        with pytest.raises(SystemExit) as pytest_wrapped_e:
            if test_import_fail:
                _import('out_bogus', os.path.abspath(os.path.join(os.path.dirname(__file__), 'fake_plugin/out_bogus.py')))
            else:
                out.run('')
    return pytest_wrapped_e


# No longer possible, we trust in check_tool_dep, it won't return an unexistent file name, so we don't catch FileNoFound
# def test_no_rar(test_dir, caplog, monkeypatch):
#     global mocked_check_output_FNF
#     mocked_check_output_FNF = True
#     # Create a silly context to get the output path
#     ctx = context.TestContext(test_dir, 'test_v5', 'empty_zip', '')
#     # The file we pretend to compress
#     ctx.create_dummy_out_file('Test.txt')
#     # We will patch subprocess.check_output to make rar fail
#     with monkeypatch.context() as m:
#         patch_functions(m)
#         pytest_wrapped_e = run_compress(ctx)
#     # Check we exited because rar isn't installed
#     assert pytest_wrapped_e.type == SystemExit
#     assert pytest_wrapped_e.value.code == MISSING_TOOL
#     assert "Missing `rar` command" in caplog.text


@pytest.mark.indep
def test_rar_fail(test_dir, caplog, monkeypatch):
    global mocked_check_output_FNF
    mocked_check_output_FNF = False
    # Create a silly context to get the output path
    ctx = context.TestContext(test_dir, 'test_v5', 'empty_zip', '')
    # The file we pretend to compress
    ctx.create_dummy_out_file('Test.txt')
    # We will patch subprocess.check_output to make rar fail
    with monkeypatch.context() as m:
        patch_functions(m)
        m.setattr('kibot.kiplot._run_command', mocked_run)
        pytest_wrapped_e = run_compress(ctx)
        pytest_wrapped_e2 = run_compress(ctx, test_import_fail=True)
    # Check we exited because rar isn't installed
    assert pytest_wrapped_e.type is SystemExit
    assert pytest_wrapped_e.value.code == WRONG_INSTALL
    assert "Failed to invoke rar command, error 10" in caplog.text
    # Not in the docker image ... pytest issue? (TODO)
    # assert "THE_ERROR" in caplog.text
    # Check we exited because the import failed
    assert pytest_wrapped_e2.type is SystemExit
    assert pytest_wrapped_e2.value.code == WRONG_INSTALL
    assert "Unable to import plug-ins:" in caplog.text


class NoGetTargets(BaseOutput):
    def __init__(self):
        self.options = True
        self.comment = 'Fake'
        self.name = 'dummy'
        self.type = 'none'
        self._sch_related = True


class DummyPre(BasePreFlight):
    def __init__(self):
        super().__init__()
        self._sch_related = True


@pytest.mark.indep
def test_no_get_targets(caplog):
    test = NoGetTargets()
    test_pre = DummyPre()
    # Also check the dependencies fallback
    GS.sch = None
    GS.sch_file = 'fake'
    with context.cover_it(cov):
        test.get_targets('')
        files = test.get_dependencies()
        files_pre = test_pre.get_dependencies()
    assert "Output 'Fake' (dummy) [none] doesn't implement get_targets(), please report it" in caplog.text
    assert files == [GS.sch_file]
    assert files_pre == [GS.sch_file]


@pytest.mark.indep
def test_ibom_parse_fail(test_dir, caplog, monkeypatch):
    global mocked_check_output_FNF
    mocked_check_output_FNF = False
    global mocked_check_output_retOK
    mocked_check_output_retOK = b'ERROR Parsing failed'
    # We will patch subprocess.check_output to make ibom fail
    with monkeypatch.context() as m:
        patch_functions(m)
        os.environ['INTERACTIVE_HTML_BOM_NO_DISPLAY'] = 'True'
        with context.cover_it(cov):
            detect_kicad()
            # Load the plug-ins
            load_actions()
            init_globals()
            # Create an ibom object
            out = RegOutput.get_class_for('ibom')()
            out.set_tree({})
            out.type = 'ibom'
            out.config(None)
            with pytest.raises(SystemExit) as pytest_wrapped_e:
                out.run('')
    assert pytest_wrapped_e.type is SystemExit
    assert pytest_wrapped_e.value.code == BOM_ERROR
    # logging.debug(caplog.text)
    assert "Failed to create BoM" in caplog.text
    mocked_check_output_retOK = ''


@pytest.mark.indep
def test_var_rename_no_variant():
    with context.cover_it(cov):
        # Load the plug-ins
        load_actions()
        # Create an ibom object
        filter = RegFilter.get_class_for('var_rename')()
        GS.variant = None
        # Should just return
        filter.filter(None)


@pytest.mark.indep
def test_bom_no_sch():
    with context.cover_it(cov):
        # Load the plug-ins
        load_actions()
        # Create an ibom object
        GS.sch = None
        out = RegOutput.get_class_for('bom')()
        (columns, extra) = get_columns()
        assert columns == ColumnList.COLUMNS_DEFAULT
        out = RegOutput.get_class_for('kibom')()
        options = out.options()
        columns = options.conf._get_columns()
        assert columns == ColumnList.COLUMNS_DEFAULT


@pytest.mark.indep
def test_pre_xrc_fail(test_dir, caplog, monkeypatch):
    ctx = context.TestContext(test_dir, 'test_v5', 'empty_zip', '')
    global mocked_call_enabled
    mocked_call_enabled = True
    with monkeypatch.context() as m:
        patch_functions(m)
        with context.cover_it(cov):
            load_actions()
            GS.set_pcb(ctx.board_file)
            sch = ctx.board_file
            GS.set_sch(sch.replace('.kicad_pcb', context.KICAD_SCH_EXT))
            GS.out_dir = test_dir
            init_globals()
            pre_drc = BasePreFlight.get_object_for('run_drc', True)
            with pytest.raises(SystemExit) as e1:
                pre_drc.config(None)
                pre_drc.run()
            pre_erc = BasePreFlight.get_object_for('run_erc', True)
            with pytest.raises(SystemExit) as e2:
                pre_erc.config(None)
                pre_erc.run()
            out = RegOutput.get_class_for('pdf_pcb_print')()
            out.set_tree({'layers': 'all'})
            out.config(None)
            out.type = 'pdf_pcb_print'
            with pytest.raises(SystemExit) as e3:
                out.run('')
    assert e1.type is SystemExit
    assert e1.value.code == DRC_ERROR
    assert e2.type is SystemExit
    assert e2.value.code == ERC_ERROR
    assert e3.type is SystemExit
    assert e3.value.code == PDF_PCB_PRINT
    assert 'pcbnew_do returned 5' in caplog.text
    ctx.clean_up()
    mocked_call_enabled = False


@pytest.mark.indep
def test_unimplemented_layer(caplog):
    with context.cover_it(cov):
        with pytest.raises(AssertionError) as e:
            Layer.solve(1)
    assert e.type is AssertionError
    assert e.value.args[0] == "Unimplemented layer type <class 'int'>"


@pytest.mark.indep
def test_step_fail(test_dir, caplog, monkeypatch):
    global mocked_check_output_FNF
    mocked_check_output_FNF = False
    global mocked_call_enabled
    mocked_call_enabled = True
    # Create a silly context to get the output path
    ctx = context.TestContext(test_dir, 'test_v5', 'empty_zip', '')
    # We will patch subprocess.check_output to make rar fail
    with monkeypatch.context() as m:
        patch_functions(m)
        with context.cover_it(cov):
            detect_kicad()
            load_actions()
            init_globals()
            GS.set_pcb(ctx.board_file)
            GS.board = None
            KiConf.loaded = False
            load_board()
            # Create a compress object with the dummy file as source
            out = RegOutput.get_class_for('step')()
            out.set_tree({})
            out.config(None)
            out.type = 'step'
            with pytest.raises(SystemExit) as e:
                out.run('')
    # Check we exited because rar isn't installed
    assert e.type is SystemExit
    assert e.value.code == KICAD2STEP_ERR
    assert "kicad2step_do returned 5" in caplog.text
    mocked_call_enabled = False


@pytest.mark.indep
def test_unknown_prefix(caplog):
    with context.cover_it(cov):
        get_prefix(1, 'y')
    assert 'Unknown prefix, please report' in caplog.text


def test_search_as_plugin_ok(test_dir, caplog):
    ctx = context.TestContext(test_dir, 'test_v5', 'empty_zip', '')
    with context.cover_it(cov):
        detect_kicad()
        load_actions()
        dir_fake = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
        GS.kicad_plugins_dirs.append(dir_fake)
        logging.debug('GS.kicad_plugins_dirs: '+str(GS.kicad_plugins_dirs))
        fname = search_as_plugin('fake', ['fake_plugin'])
        logging.debug('fname: '+fname)
        with open(ctx.get_out_path('error.txt'), 'wt') as f:
            f.write(caplog.text)
        # Fails to collect caplog on docker image (TODO)
        # This is a bizarre case, the test alone works, all tests in test_misc* together work.
        # But when running all the tests this one fails to get caplog.
        # The test_rar_fail has a similar problem.
        # assert re.search(r"Using `(.*)data/fake_plugin/fake` for `fake` \(fake_plugin\)", caplog.text) is not None
        assert re.search(r"(.*)data/fake_plugin/fake", fname) is not None
    ctx.clean_up()


def test_search_as_plugin_fail(test_dir, caplog):
    with context.cover_it(cov):
        detect_kicad()
        load_actions()
        dir_fake = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
        GS.kicad_plugins_dirs.append(dir_fake)
        fname = search_as_plugin('fake', [''])
        assert fname is None


@pytest.mark.indep
def test_layer_no_id():
    with context.cover_it(cov):
        la = Layer()
        la.layer = 'F.Cu'
        la.description = 'Top'
        la.suffix = 'F_Cu'
        assert str(la) == "F.Cu ('Top' F_Cu)"


@pytest.mark.indep
def test_makefile_kibot_sys(test_dir):
    ctx = context.TestContext(test_dir, 'test_v5', 'empty_zip', '')
    GS.sch_file = 'foo.sch'
    GS.pcb_file = 'bar.kicad_pcb'
    GS.out_dir = ctx.get_out_path('')
    with context.cover_it(cov):
        generate_makefile(ctx.get_out_path('Makefile'), 'pp', [], kibot_sys=True)
    ctx.search_in_file('Makefile', [r'KIBOT\?=kibot'])
    ctx.clean_up()


@pytest.mark.indep
def test_units_1():
    with context.cover_it(cov):
        # Test for ',' as decimal point
        units.decimal_point = ','
        assert str(comp_match("3,3 pF", 'C')) == "3.3 pF"
        a = comp_match("0,1uf 10% 0402 50v x7r", 'C')
        assert str(a) == "100 nF"
        assert a.extra['tolerance'] == 10
        assert a.extra['size'] == '0402'
        assert a.extra['voltage_rating'] == 50
        assert a.extra['characteristic'] == 'X7R'
        a = comp_match("0.01uf, 50v, cog, 5%, 0603", 'C')
        assert str(a) == "10 nF"
        assert a.extra['tolerance'] == 5
        assert a.extra['size'] == '0603'
        assert a.extra['voltage_rating'] == 50
        assert a.extra['characteristic'] == 'C0G'
        a = comp_match("0,01uf; 50v; cog; 5%; 0603", 'C')
        assert str(a) == "10 nF"
        assert a.extra['tolerance'] == 5
        assert a.extra['size'] == '0603'
        assert a.extra['voltage_rating'] == 50
        assert a.extra['characteristic'] == 'C0G'
        units.decimal_point = ''

        assert str(comp_match("1", 'R')) == "1 Ω"
        assert str(comp_match("1000", 'R')) == "1 kΩ"
        assert str(comp_match("1000000", 'R')) == "1 MΩ"
        assert str(comp_match("1000000000", 'R')) == "1 GΩ"
        assert str(comp_match("3.3 pF", 'C')) == "3.3 pF"
        assert str(comp_match("0.0033 nF", 'C')) == "3.3 pF"
        assert str(comp_match("3p3", 'C')) == "3.3 pF"
        a = comp_match("3k3 1% 0805", 'R')
        assert str(a) == "3.3 kΩ"
        assert a.extra['tolerance'] == 1
        assert a.extra['size'] == '0805'
        a = comp_match("0.01 1%", 'R')
        assert str(a) == "10 mΩ"
        assert a.extra['tolerance'] == 1


@pytest.mark.indep
def test_read_resistance():
    with context.cover_it(cov):
        assert read_resistance("4k7")[0] == D("4700")
        assert read_resistance("4k7")[0] == D("4700")
        assert read_resistance("4.7R")[0] == D("4.7")
        assert read_resistance("4R7")[0] == D("4.7")
        assert read_resistance("0R47")[0] == D("0.47")
        assert read_resistance("4700k")[0] == D("4700000")
        assert read_resistance("470m")[0] == D("0.47")
        assert read_resistance("470M")[0] == D("470000000")
        assert read_resistance("4M7")[0] == D("4700000")
        assert read_resistance("470")[0] == D("470")
        assert read_resistance("470Ω")[0] == D("470")
        assert read_resistance("470 Ω")[0] == D("470")
        assert read_resistance("470Ohm")[0] == D("470")
        assert read_resistance("470 Ohms")[0] == D("470")
        assert read_resistance("R47")[0] == D("0.47")
        assert read_resistance("1G")[0] == D("1000000000")
        assert read_resistance("4k7000")[0] == D("4700")


@pytest.mark.indep
def test_electro_grammar_1():
    with context.cover_it(cov):
        C2UF_0603_30P = {'type': 'capacitor', 'capacitance': 2e-6, 'size': '0603', 'tolerance': 30}
        C2UF_0603 = {'type': 'capacitor', 'capacitance': 2e-6, 'size': '0603'}
        C10UF_0402 = {'type': 'capacitor', 'capacitance': 10e-6, 'size': '0402'}
        C100NF_0603 = {'type': 'capacitor', 'capacitance': 100e-9, 'size': '0603'}
        C100NF_0603_X7R = {'type': 'capacitor', 'capacitance': 100e-9, 'size': '0603', 'characteristic': 'X7R'}
        C100NF_0603_Z5U = {'type': 'capacitor', 'capacitance': 100e-9, 'size': '0603', 'characteristic': 'Z5U'}
        C100NF_0603_Y5V = {'type': 'capacitor', 'capacitance': 100e-9, 'size': '0603', 'characteristic': 'Y5V'}
        C100NF_0603_C0G = {'type': 'capacitor', 'capacitance': 100e-9, 'size': '0603', 'characteristic': 'C0G'}
        C100NF_0603_25V = {'type': 'capacitor', 'capacitance': 100e-9, 'size': '0603', 'voltage_rating': 25}
        C100NF_0603_6V3 = {'type': 'capacitor', 'capacitance': 100e-9, 'size': '0603', 'voltage_rating': 6.3}
        C100UF_0603 = {'type': 'capacitor', 'capacitance': 100e-6, 'size': '0603'}
        C100UF_0603_X7R = {'type': 'capacitor', 'capacitance': 100e-6, 'size': '0603', 'characteristic': 'X7R'}
        C1N5_0603_X7R = {'type': 'capacitor', 'capacitance': 1.5e-9, 'size': '0603', 'characteristic': 'X7R'}
        C1F_0603_25V = {'type': 'capacitor', 'capacitance': 1, 'size': '0603', 'voltage_rating': 25}
        C_01005 = {'type': 'capacitor', 'size': '01005'}
        C_0201 = {'type': 'capacitor', 'size': '0201'}
        C_0402 = {'type': 'capacitor', 'size': '0402'}
        C_0603 = {'type': 'capacitor', 'size': '0603'}
        C_0805 = {'type': 'capacitor', 'size': '0805'}
        C_1206 = {'type': 'capacitor', 'size': '1206'}
        C_TESTS = ((('this is total rubbish', ''), {}),
                   (('2uF 0603',), C2UF_0603),
                   (('2uF 0603 30%', '2uF 0603 +/-30%', '2uF 0603 ±30%', '2uF 0603 +-30%'), C2UF_0603_30P),
                   (('10uF 0402',
                     '10 micro Farad 0402',
                     '10 \u03BC''F 0402',
                     '10 \u00B5''F 0402',
                     '10𝛍F 0402',
                     '10𝜇F 0402',
                     '10𝝁 F 0402',
                     '10    𝝻F 0402',
                     '10𝞵F 0402'), C10UF_0402),
                   (('100nF 0603 kajdlkja alkdjlkajd',
                     'adjalkjd 100nF akjdlkjda 0603 kajdlkja alkdjlkajd',
                     'capacitor 100nF 0603, warehouse 5',
                     'adjalkjd 0603 akjdlkjda 100nF kajdlkja alkdjlkajd',
                     'C 100n 0603',
                     'Capacitor 100n 0603',
                     'cap 100n 0603'), C100NF_0603),
                   (('1n5F 0603 X7R',), C1N5_0603_X7R),
                   (('100NF 0603 X7R', '100nF 0603 X7R', '100nF 0603 x7r'), C100NF_0603_X7R),
                   (('100UF 0603 X7R',), C100UF_0603_X7R),
                   (('100nF 0603 Z5U',), C100NF_0603_Z5U),
                   (('100nF 0603 Y5V',), C100NF_0603_Y5V),
                   (('100nF 0603 C0G',
                     '100nF 0603 NP0',
                     '100nF 0603 np0',
                     '100nF 0603 c0g',
                     '100nF 0603 cog',
                     '100nF 0603 npO',
                     '100nF 0603 COG',
                     '100nF 0603 C0G/NP0'), C100NF_0603_C0G),
                   (('1F 0603 25V', '1f 0603 25V', '1 Farad 0603 25V'), C1F_0603_25V),
                   (('100nF 0603 25V', '100nF 0603 25 v'), C100NF_0603_25V),
                   (('100nF 0603 6v3', '100nF 0603 6V3', '100nF 0603 6.3V', '100nF 0603 6.3v'), C100NF_0603_6V3),
                   (('0603 0.0001F', '0603 0.0001 F', '0603 0.1mF'), C100UF_0603),
                   (('capacitor 01005',), C_01005),
                   (('capacitor 0201',), C_0201),
                   (('capacitor 0402',), C_0402),
                   (('capacitor 0603',), C_0603),
                   (('capacitor 0805',), C_0805),
                   (('capacitor 1206',), C_1206))
        R1K_0603 = {'type': 'resistor', 'size': '0603', 'resistance': 1000}
        R1K_0805_5P = {'type': 'resistor', 'size': '0805', 'resistance': 1000, 'tolerance': 5}
        R1K_0805_01P = {'type': 'resistor', 'size': '0805', 'resistance': 1000, 'tolerance': 0.1}
        R1K_0805_5P_100MW = {'type': 'resistor', 'size': '0805', 'resistance': 1000, 'tolerance': 5, 'power_rating': 0.1}
        R1K_0201_500MW = {'type': 'resistor', 'size': '0201', 'resistance': 1000, 'power_rating': 0.5}
        R0_0201_125MW = {'type': 'resistor', 'size': '0201', 'resistance': 0, 'power_rating': 0.125}
        R1M_0603 = {'type': 'resistor', 'size': '0603', 'resistance': 1e6}
        R1M = {'type': 'resistor', 'resistance': 1e6}
        R1M1_0603 = {'type': 'resistor', 'size': '0603', 'resistance': 1.1e6}
        R100 = {'type': 'resistor', 'resistance': 100}
        R10K_0805 = {'type': 'resistor', 'size': '0805', 'resistance': 10000}
        R1 = {'type': 'resistor', 'resistance': 1}
        R1_0402 = {'type': 'resistor', 'resistance': 1, 'size': '0402'}
        R1_0805 = {'type': 'resistor', 'resistance': 1, 'size': '0805'}
        R1K5_0402 = {'type': 'resistor', 'resistance': 1500, 'size': '0402'}
        R2_7_0402 = {'type': 'resistor', 'resistance': 2.7, 'size': '0402'}
        R1MILI = {'type': 'resistor', 'resistance': 0.001}
        R100U = {'type': 'resistor', 'resistance': 0.0001}
        R_01005 = {'type': 'resistor', 'size': '01005'}
        R_0201 = {'type': 'resistor', 'size': '0201'}
        R_0402 = {'type': 'resistor', 'size': '0402'}
        R_0603 = {'type': 'resistor', 'size': '0603'}
        R_0805 = {'type': 'resistor', 'size': '0805'}
        R_1206 = {'type': 'resistor', 'size': '1206'}
        R_TESTS = ((('R 0.01 1%',), {'type': 'resistor', 'resistance': 0.01, 'tolerance': 1}),
                   (('1k 0603', '1k ohm 0603', '1K ohms 0603'), R1K_0603),
                   (('resistor 100', '100R', '100 R'), R100),
                   (('r 10000 0805',), R10K_0805),
                   (('res or whatever 1',), R1),
                   (('1 ohm 0402',), R1_0402),
                   (('1Ω 0805', '1Ω 0805'), R1_0805),
                   (('1MEG 0603', '1M 0603'), R1M_0603),
                   (('1M1 ohms 0603',), R1M1_0603),
                   (('1k5 0402', '1.5k 0402'), R1K5_0402),
                   (('2r7 0402', '2R7 0402'), R2_7_0402),
                   (('1 mOhm',), R1MILI),
                   (('1 MOhm',), R1M),
                   (('100 uΩ',), R100U),
                   (('1k 0805 5%',), R1K_0805_5P),
                   (('1k 0805 0.1%',), R1K_0805_01P),
                   (('1k 0805 5% 100mW',), R1K_0805_5P_100MW),
                   (('0 ohm 0201 0.125W', '0 ohm 0201 1/8W'), R0_0201_125MW),
                   (('resistor 1k 0201 1/2 watts',), R1K_0201_500MW),
                   (('resistor 01005',), R_01005),
                   (('resistor 0201',), R_0201),
                   (('resistor 0402',), R_0402),
                   (('resistor 0603',), R_0603),
                   (('resistor 0805',), R_0805),
                   (('resistor 1206',), R_1206))
        LED_TEST = ((('led red 0603',), {'type': 'led', 'size': '0603', 'color': 'red'}),
                    (('SMD LED GREEN 0805', 'GREEN 0805 LED'), {'type': 'led', 'size': '0805', 'color': 'green'}))
        L_TEST = ((('L 100 0805', 'IND 100 0805', 'Inductor 100 0805'), {'type': 'inductor', 'inductance': 100,
                                                                         'size': '0805'}),
                  (('3n3 H', '3n3H', '3.3 nH', '3300pH', '3.3 nano Henry',
                    'This is a 3.3 nH inductor'), {'type': 'inductor', 'inductance': 3.3e-9}))
        TESTS = C_TESTS+R_TESTS+L_TEST+LED_TEST
        for test in TESTS:
            ref = test[1]
            for c in test[0]:
                res = parse(c)
                assert res == ref, "For `{}` got:\n{}\nExpected:\n{}".format(c, res, ref)
                logging.debug(c+" Ok")


class Comp:
    def __init__(self):
        self.ref = 'R1'


def mocked_requests_get(url, allow_redirects=True, headers=None, timeout=20):
    res = requests.Response()
    if url == '1':
        res.status_code = 666
        return res
    elif url == '2':
        raise requests.exceptions.ReadTimeout()
    elif url == '3':
        raise requests.exceptions.SSLError()
    elif url == '4':
        raise requests.exceptions.TooManyRedirects()
    elif url == '5':
        raise requests.exceptions.ConnectionError()
    elif url == '6':
        raise requests.exceptions.RequestException("Hello!")
    elif url == 'ok':
        res.status_code = 200
        return res
    logging.error(url)
    return res


@pytest.mark.indep
def test_ds_net_error(test_dir, caplog, monkeypatch):
    ctx = context.TestContext(test_dir, 'test_v5', 'empty_zip', '')
    dummy = ctx.get_out_path('dummy')
    with open(dummy, 'wt') as f:
        f.write('Hello!')
    with context.cover_it(cov):
        o = Download_Datasheets_Options()
        o._downloaded = {'dnl'}
        o._created = []
        c = Comp()
        o.download(c, '1N1234.pdf', 'pp', '1N1234', None)
        assert 'Invalid URL' in caplog.text
        with monkeypatch.context() as m:
            caplog.clear()
            o.download(c, 'x', 'pp', 'dnl', None)
            assert 'already downloaded' in caplog.text
            caplog.clear()
            o._dry = True
            o.download(c, 'ok', '', dummy, None)
            o._dry = False
            assert dummy in o._created
            m.setattr('requests.get', mocked_requests_get)
            caplog.clear()
            o.download(c, '1', 'pp', '1N1234', None)
            assert 'Failed with status 666' in caplog.text
            caplog.clear()
            o.download(c, '2', 'pp', '1N1234', None)
            assert 'Timeout' in caplog.text
            caplog.clear()
            o.download(c, '3', 'pp', '1N1234', None)
            assert 'SSL Error' in caplog.text
            caplog.clear()
            o.download(c, '4', 'pp', '1N1234', None)
            assert 'More than 30 redirections' in caplog.text
            caplog.clear()
            o.download(c, '5', 'pp', '1N1234', None)
            assert 'Connection' in caplog.text
            caplog.clear()
            o.download(c, '6', 'pp', '1N1234', None)
            assert 'Hello!' in caplog.text
