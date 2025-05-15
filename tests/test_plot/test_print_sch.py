"""
Tests of Printing Schematic files

We test:
- PDF for bom.sch

For debug information use:
pytest-3 --log-cli-level debug

"""

import os
import logging
import coverage
import pytest
from . import context
from kibot.misc import (PDF_SCH_PRINT, SVG_SCH_PRINT)
from kibot.kicad.v5_sch import Schematic, SchFileError, DrawPoligon, Pin
from kibot.kicad.v6_sch import SchematicV6
from kibot.globals import Globals

PDF_DIR = ''
PDF_FILE = 'Schematic.pdf'
SVG_FILE = 'Schematic.svg'
NI_DIR = 'no_inductor'
cov = coverage.Coverage()


@pytest.mark.slow
@pytest.mark.eeschema
def test_print_sch_ok(test_dir):
    prj = 'bom_no_xml'  # bom has meta data, here we test no meta-data
    ctx = context.TestContext(test_dir, prj, 'print_sch')
    ctx.run()
    # Check all outputs are there
    ctx.expect_out_file(PDF_FILE)
    ctx.clean_up()


@pytest.mark.slow
@pytest.mark.eeschema
@pytest.mark.skipif(context.ki8(), reason="Always prints something")
def test_print_sch_fail(test_dir):
    prj = 'print_err'
    ctx = context.TestContextSCH(test_dir, prj, 'print_sch')
    ctx.run(PDF_SCH_PRINT, no_board_file=True, extra=['-e', os.path.join(ctx.get_board_dir(),
            'print_err'+context.KICAD_SCH_EXT)])
    ctx.clean_up()


@pytest.mark.slow
@pytest.mark.eeschema
def test_print_sch_svg_ok(test_dir):
    prj = 'bom_no_xml'  # bom has meta data, here we test no meta-data
    ctx = context.TestContext(test_dir, prj, 'print_sch_svg')
    ctx.run()
    # Check all outputs are there
    ctx.expect_out_file(SVG_FILE)
    ctx.clean_up()


# @pytest.mark.slow
# @pytest.mark.eeschema
# def test_print_sch_ps_ok(test_dir):
#     prj = 'test_v5'
#     ctx = context.TestContext(test_dir, prj, 'print_sch_ps')
#     ctx.run()
#     # Check all outputs are there
#     ctx.expect_out_file(SVG_FILE.replace('svg', 'ps'))
#     ctx.clean_up()


# @pytest.mark.slow
# @pytest.mark.eeschema
# def test_print_sch_dxf_ok(test_dir):
#     prj = 'test_v5'
#     ctx = context.TestContext(test_dir, prj, 'print_sch_dxf')
#     ctx.run()
#     # Check all outputs are there
#     ctx.expect_out_file(SVG_FILE.replace('svg', 'dxf'))
#     ctx.clean_up()


# @pytest.mark.slow
# @pytest.mark.eeschema
# def test_print_sch_hpgl_ok(test_dir):
#     prj = 'test_v5'
#     ctx = context.TestContext(test_dir, prj, 'print_sch_hpgl')
#     ctx.run()
#     # Check all outputs are there
#     ctx.expect_out_file(SVG_FILE.replace('svg', 'hpgl'))
#     ctx.clean_up()


@pytest.mark.slow
@pytest.mark.eeschema
@pytest.mark.skipif(context.ki8(), reason="Always prints something")
def test_print_sch_svg_fail(test_dir):
    prj = 'print_err'
    ctx = context.TestContext(test_dir, prj, 'print_sch_svg')
    ctx.run(SVG_SCH_PRINT, no_board_file=True, extra=['-e', os.path.join(ctx.get_board_dir(),
            'print_err'+context.KICAD_SCH_EXT)])
    ctx.clean_up()


def check_l1(ctx):
    ctx.run()
    o_name = os.path.join(NI_DIR, 'test_v5'+context.KICAD_SCH_EXT)
    ctx.expect_out_file(o_name)
    glb = Globals()
    glb.set_tree({})
    glb.config(None)
    sch = Schematic() if context.ki5() else SchematicV6()
    try:
        sch.load(ctx.get_out_path(o_name), 'no_project')
    except SchFileError as e:
        logging.error('At line {} of `{}`: {}'.format(e.line, e.file, e.msg))
        logging.error('Line content: `{}`'.format(e.code))
        raise AssertionError()
    comps = sch.get_components()
    l1 = next(c for c in comps if c.ref == 'L1')
    assert l1
    logging.debug('Found L1')
    if context.ki7():
        assert l1.kicad_dnp
    else:
        lib_name = 'n' if context.ki5() else 'kibot_crossed'
        assert l1.lib == lib_name
    logging.debug('L1 is crossed')
    ctx.clean_up()


def test_sch_variant_ni_1(test_dir):
    """ Using a variant """
    prj = 'test_v5'  # Is the most complete, contains every KiCad object I know
    ctx = context.TestContextSCH(test_dir, prj, 'sch_no_inductors_1')
    check_l1(ctx)


def test_sch_variant_ni_2(test_dir):
    """ Using a filter """
    prj = 'test_v5'  # Is the most complete, contains every KiCad object I know
    ctx = context.TestContextSCH(test_dir, prj, 'sch_no_inductors_2')
    check_l1(ctx)


@pytest.mark.slow
@pytest.mark.eeschema
def test_print_sch_variant_ni_1(test_dir):
    """ Using a variant """
    prj = 'test_v5_wks'  # Is the most complete, contains every KiCad object I know
    ctx = context.TestContextSCH(test_dir, prj, 'print_pdf_no_inductors_1')
    ctx.run()
    r_name = 'test_v5_wks-schematic_(no_L).pdf'
    o_name = os.path.join(NI_DIR, r_name)
    ctx.expect_out_file(o_name)
    ctx.compare_pdf(o_name, r_name, height='100%')
    ctx.clean_up(keep_project=True)


@pytest.mark.slow
@pytest.mark.eeschema
def test_print_sch_svg_variant_ni_1(test_dir):
    """ SVG using a variant """
    prj = 'test_v5'  # Is the most complete, contains every KiCad object I know
    ctx = context.TestContextSCH(test_dir, prj, 'print_svg_no_inductors_1')
    ctx.run()
    r_name = 'test_v5-schematic_(no_L).svg'
    o_name = os.path.join(NI_DIR, r_name)
    ctx.expect_out_file(o_name)
    ctx.compare_image(o_name, r_name)
    ctx.clean_up()


@pytest.mark.slow
@pytest.mark.eeschema
def test_print_sch_variant_ni_2(test_dir):
    """ Using a filter """
    prj = 'test_v5'  # Is the most complete, contains every KiCad object I know
    ctx = context.TestContextSCH(test_dir, prj, 'print_pdf_no_inductors_2')
    ctx.run()
    r_name = 'test_v5-schematic_(no_L).pdf'
    o_name = os.path.join(NI_DIR, 'test_v5-schematic.pdf')
    ctx.expect_out_file(o_name)
    ctx.compare_pdf(o_name, r_name)
    ctx.clean_up()


def test_sch_missing_1(test_dir):
    """ R1 exists in l1.lib, but the lib isn't specified.
        R2 is bogus, completely missing.
        Test for the -w/--no-warn option (only in CI/CD where we get W008+W009) """
    prj = 'missing'
    ctx = context.TestContextSCH(test_dir, prj, 'sch_no_inductors_1')
    ctx.run(extra=['-w', '8,9'])
    o_name = os.path.join(NI_DIR, prj+context.KICAD_SCH_EXT)
    ctx.expect_out_file(o_name)
    if context.ki5():
        ctx.search_err("Component .?Resistor.? doesn't specify its library")
    else:
        ctx.search_err("Component .?A:B:Resistor.? with more than one .?:.?")
    ctx.search_err("Missing component .?l1:FooBar.?")
    ctx.search_err("Missing component(.*)Resistor", invert=context.ki5())
    ctx.search_err("Missing doc-lib entry for l1:C", invert=(not context.ki5()))
    ctx.search_out(r"Found 4 unique warning/s \(")
    ctx.clean_up()


def test_sch_missing_filtered(test_dir):
    """ R1 exists in l1.lib, but the lib isn't specified.
        R2 is bogus, completely missing """
    prj = 'missing'
    ctx = context.TestContextSCH(test_dir, prj, 'sch_no_inductors_1_filtered')
    ctx.run()
    o_name = os.path.join(NI_DIR, prj+context.KICAD_SCH_EXT)
    ctx.expect_out_file(o_name)
    if context.ki5():
        ctx.search_err("Component .?Resistor.? doesn't specify its library")
    else:
        ctx.search_err("Component .?A:B:Resistor.? with more than one .?:.?")
    ctx.search_err("WARNING:(.*)Missing component .?l1:FooBar.?", invert=True)
    ctx.search_err("Missing component(.*)Resistor", invert=context.ki5())
    ctx.search_err("Missing doc-lib entry for l1:C", invert=(not context.ki5()))
    ctx.search_out(r"Found 3 unique warning/s \(\d+ total, \d+ filtered\)")
    ctx.clean_up()


def test_sch_bizarre_cases(test_dir):
    """ Polygon without points.
        Pin with unknown direction. """
    if not context.ki5():
        # This is very KiCad 5 loader specific
        return
    pol = DrawPoligon()
    pol.points = 0
    pol.coords = []
    pin = Pin()
    pin.dir = 'bogus'
    cov.load()
    cov.start()
    x1, y1, x2, y2, ok_pol = pol.get_rect()
    x1, y1, x2, y2, ok_pin = pin.get_rect()
    cov.stop()
    cov.save()
    assert ok_pol is False
    assert ok_pin is False


@pytest.mark.slow
@pytest.mark.eeschema
def test_sch_variant_diff(test_dir):
    """ Diff between SCH variants, using a separated output and using mutivar """
    prj = 'kibom-variant_3'
    ctx = context.TestContext(test_dir, prj, 'sch_variant_1', '')
    ctx.run()
    ctx.expect_out_file(['kibom-variant_3-diff_sch_variant_sch_default.pdf',
                         'kibom-variant_3-diff_sch_variant_sch_production.pdf',
                         'kibom-variant_3-diff_sch_variant_sch_test.pdf',
                         'kibom-variant_3-diff_sch_Current-default_variant.pdf',
                         'kibom-variant_3-diff_sch_Current-production_variant.pdf',
                         'kibom-variant_3-diff_sch_Current-test_variant.pdf',
                         'kibom-variant_3-diff_sch.pdf'])
    ctx.clean_up()
