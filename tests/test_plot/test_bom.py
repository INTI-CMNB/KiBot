"""
Tests of KiBoM BoM files

The bom.sch has R1, R2 and C1
We test:
- HTML and CSV

For debug information use:
pytest-3 --log-cli-level debug

"""

import pytest
import os
from . import context
from kibot.misc import BOM_ERROR

BOM_DIR = 'BoM'


def test_bom_ok(test_dir):
    prj = 'bom'
    ctx = context.TestContextSCH(test_dir, prj, prj, BOM_DIR)
    ctx.run()
    # Check all outputs are there
    # Default format is PRJ_bom_REVISION
    csv = prj+'-bom.csv'
    html = prj+'_bom_r1_(pp).html'
    ctx.expect_out_file_d(csv)
    ctx.expect_out_file_d(html)
    ctx.search_in_file_d(csv, ['R,R1,100', 'R,R2,200', 'C,C1,1uF'])
    os.remove(ctx.get_board_dir('bom.ini'))
    ctx.clean_up()


def test_bom_fail(test_dir):
    ctx = context.TestContext(test_dir, 'bom_no_xml', 'bom')
    ctx.run(BOM_ERROR)
    ctx.clean_up()


def test_bom_cfg_1(test_dir):
    prj = 'bom'
    ctx = context.TestContextSCH(test_dir, prj, 'bom_cfg', BOM_DIR)
    ctx.run()
    csv = prj+'-bom.csv'
    ctx.expect_out_file_d(csv)
    if context.ki10():
        ctx.search_in_file_d(csv, ['R,R1,100 R_0805_2012Metric', 'R,R2,200 R_0805_2012Metric', 'C,C1,1uF C_0805_2012Metric'])
    else:
        ctx.search_in_file_d(csv, ['R,R1,100 R_0805_2012Metric ~', 'R,R2,200 R_0805_2012Metric ~',
                                   'C,C1,1uF C_0805_2012Metric ~'])
    ctx.clean_up()


def test_bom_cfg_2(test_dir):
    prj = 'bom'
    ctx = context.TestContextSCH(test_dir, prj, 'bom_cfg2', BOM_DIR)
    ctx.run()
    csv = prj+'-bom.csv'
    ctx.expect_out_file_d(csv)
    ctx.search_in_file_d(csv, ['R,100 R_0805_2012Metric,R1', 'R,200 R_0805_2012Metric,R2'])
    ctx.search_not_in_file_d(csv, ['C,1uF C_0805_2012Metric,C1'])
    ctx.clean_up()


def test_bom_cfg_3(test_dir):
    """ Without any column """
    prj = 'bom'
    ctx = context.TestContextSCH(test_dir, prj, 'bom_cfg3', BOM_DIR)
    ctx.run()
    csv = prj+'-bom.csv'
    ctx.expect_out_file_d(csv)
    ctx.search_in_file_d(csv, ['R,R1,100', 'R,R2,200', 'C,C1,1uF'])
    ctx.clean_up()


def test_bom_cfg_4(test_dir):
    """ Without join """
    prj = 'bom'
    ctx = context.TestContext(test_dir, prj, 'bom_cfg4', BOM_DIR)
    ctx.run()
    csv = prj+'-bom.csv'
    ctx.expect_out_file_d(csv)
    ctx.search_in_file_d(csv, ['R,100,R1', 'R,200,R2', 'C,1uF,C1'])
    ctx.clean_up()


@pytest.mark.skipif(not context.ki9(), reason="Testing on KiCad 9+")
def test_bom_alternatives_1(test_dir):
    """ Simple alternatives """
    prj = 'alternatives'
    ctx = context.TestContextSCH(test_dir, prj, 'alternatives_1', '')
    ctx.run()
    csv = prj+'-bom.csv'
    ctx.expect_out_file_d(csv)
    ctx.compare_txt(csv)
    ctx.clean_up()
