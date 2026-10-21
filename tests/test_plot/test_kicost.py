"""
Tests for the KiCost output.

For debug information use:
pytest-3 --log-cli-level debug
"""
import os.path as op
import re
from . import context
import logging
import pytest
import subprocess

OUT_DIR = 'KiCost'
xlsx2csv_version = None


def do_int(v):
    return int(v) if v is not None else 0


def get_xlsx2csv_version():
    global xlsx2csv_version
    if xlsx2csv_version:
        return xlsx2csv_version
    res = subprocess.check_output(['xlsx2csv', '--version']).decode()
    ver = tuple(map(do_int, res.split('.')))
    return ver


def convert2csv(ctx, xlsx, skip_empty=False, sheet=None):
    xlsx = ctx.get_out_path(op.join(OUT_DIR, xlsx))
    csv = xlsx[:-4]+'csv'
    logging.debug('Converting to CSV')
    cmd = ['xlsx2csv']
    if skip_empty:
        cmd.append('--skipemptycolumns')
    if sheet:
        cmd.extend(['-n', sheet])
    if get_xlsx2csv_version() >= (0, 8, 0):
        cmd.append('--include-hidden-rows')
    cmd.append(xlsx)
    cmd.append(csv)
    subprocess.check_output(cmd)
    with open(csv, 'rt') as f:
        content = f.read()
    content = re.sub(r'(\$|Prj) date:,[^,]+', r'\1 date:,', content, count=3)
    content = re.sub(r'KiCost[^,]+', 'KiCost', content, count=1)
    content = re.sub(r'KiCad Version:,[^,]+', 'KiCad Version:,', content)
    content = re.sub(r'Created:,[^,]+', 'Created:,', content, count=1)
    with open(csv, 'wt') as f:
        f.write(content)


def check_simple(ctx, variant, prj='simple'):
    if variant:
        variant = '_'+variant
    name = prj+variant+'.xlsx'
    ctx.expect_out_file_d(name)
    convert2csv(ctx, name, skip_empty=True)
    ctx.compare_txt_d2(name[:-4]+'csv')


def test_kicost_simple(test_dir):
    """ External KiCost using variants, very simple case """
    prj = 'kibom-variant_kicost'
    ctx = context.TestContextSCH(test_dir, prj, 'kicost_simple', OUT_DIR)
    ctx.run()
    check_simple(ctx, '')
    check_simple(ctx, 'default')
    check_simple(ctx, 'production')
    check_simple(ctx, 'test')
    ctx.clean_up()


def test_kicost_int_variant(test_dir):
    """ External KiCost using internal variants """
    prj = 'kibom-variant_kicost'
    ctx = context.TestContextSCH(test_dir, prj, 'kicost_int_variant', OUT_DIR)
    ctx.run(extra_debug=True)
    check_simple(ctx, '')
    check_simple(ctx, 'default')
    check_simple(ctx, 'production')
    check_simple(ctx, 'test')
    ctx.clean_up()


def test_kicost_merge(test_dir):
    """ External KiCost multiple projects and field translation """
    prj = 'multipart'
    ctx = context.TestContextSCH(test_dir, prj, 'kicost_merge', OUT_DIR)
    ctx.run(extra_debug=True)
    check_simple(ctx, '', prj)
    ctx.clean_up()


def test_kicost_bom_simple(test_dir):
    """ Internal BoM + KiCost, very simple case. With DNF sheet. """
    prj = 'kibom-variant_2c'
    ctx = context.TestContextSCH(test_dir, prj, 'int_bom_kicost_simple_xlsx', OUT_DIR)
    ctx.run(kicost=True)  # , extra_debug=True
    output = prj+'-bom.xlsx'
    ctx.expect_out_file_d(output)
    convert2csv(ctx, output, sheet='Costs')
    csv = output[:-4]+'csv'
    ctx.compare_txt_d2(csv, 'ks_'+csv)
    convert2csv(ctx, output, sheet='Costs (DNF)')
    ctx.compare_txt_d2(csv, 'ks_'+output[:-5]+'_dnf.csv')
    convert2csv(ctx, output, sheet='Specs')
    ctx.compare_txt_d2(csv, 'ks_'+output[:-5]+'_spec.csv')
    convert2csv(ctx, output, sheet='Specs (DNF)')
    ctx.compare_txt_d2(csv, 'ks_'+output[:-5]+'_spec_dnf.csv')
    ctx.clean_up()


def test_kicost_bom_sel_dist_1(test_dir):
    """ Internal BoM + KiCost, select distributors (Mouser+Digi-Key). With DNF sheet. """
    prj = 'kibom-variant_2c'
    ctx = context.TestContextSCH(test_dir, prj, 'int_bom_kicost_sel_dist_1_xlsx', OUT_DIR)
    ctx.run(kicost=True, extra_debug=True)  # , extra_debug=True
    output = prj+'-bom.xlsx'
    ctx.expect_out_file_d(output)
    convert2csv(ctx, output, sheet='Costs')
    csv = output[:-4]+'csv'
    ctx.compare_txt_d2(csv, output[:-5]+'_dk_mou.csv')
    convert2csv(ctx, output, sheet='Costs (DNF)')
    ctx.compare_txt_d2(csv, output[:-5]+'_dk_mou_dnf.csv')
    ctx.clean_up()


def test_kicost_bom_merge_1(test_dir):
    """ Internal BoM + KiCost, merging 3 projects. """
    prj = 'merge_1'
    yaml = 'int_bom_kicost_merge_xlsx'
    if context.ki6():
        yaml += '_k6'
    ctx = context.TestContextSCH(test_dir, prj, yaml, OUT_DIR)
    ctx.run(kicost=True)  # , extra_debug=True
    output = prj+'-bom.xlsx'
    ctx.expect_out_file_d(output)
    convert2csv(ctx, output, sheet='Costs')
    csv = output[:-4]+'csv'
    ctx.compare_txt_d2(csv)


def test_kicost_spec_to_field_1(test_dir):
    """ Internal BoM + KiCost, select distributors (Mouser+Digi-Key). With DNF sheet.
        Then copy the RoHS spec to a variant schematic """
    prj = 'kibom-variant_2c'
    ctx = context.TestContextSCH(test_dir, prj, 'spec_to_field_1', OUT_DIR)
    ctx.run(kicost=True, extra_debug=True)
    output = prj+'-bom.xlsx'
    ctx.expect_out_file_d(output)
    ctx.search_err([r'WARNING:\(.*\) C1 field `Tolerance` collision, has `20%`, found `10%`',
                    r'WARNING:\(.*\) R1 field `Tolerance` collision, has `1%`, found `5%`',
                    'C1 RoHS: ROHS3 Compliant'])
    ctx.clean_up()


def check_modules(ctx, fname, modules):
    convert2csv(ctx, fname)
    rows, _, _ = ctx.load_csv(fname.replace('.xlsx', '.csv'))
    found = rows[5][0].split(',')
    assert len(found) == len(modules)
    logging.debug(str(len(modules)) + " components OK")
    for c in modules:
        assert c in found
    logging.debug("list of components OK")


@pytest.mark.skipif(not context.ki10(), reason="KiCad 10+ variants")
def test_kicost_variant_10(test_dir):
    prj = 'kicad-variante'
    ctx = context.TestContext(test_dir, prj, 'kicost_int_variant_10', OUT_DIR)
    ctx.run(extra_debug=True)
    extra = ['R9', 'R10', 'R11', 'R12', 'R13', 'R14', 'R15', 'R16']
    # No variant
    logging.debug("* No variant")
    check_modules(ctx, prj+'-kicost.xlsx', ['R1', 'R2', 'R3']+extra)
    # V1
    logging.debug("* V1 variant")
    check_modules(ctx, prj+'-kicost_(V1).xlsx', ['R1', 'R2']+extra)
    # V2
    logging.debug("* V2 variant")
    check_modules(ctx, prj+'-kicost_(V2).xlsx', ['R1', 'R3']+extra)
    # V3
    logging.debug("* V3 variant")
    # Here R4 is removed by the PCB saying this isn't in the BoM
    check_modules(ctx, prj+'-kicost_V3.xlsx', ['R1']+extra)
    ctx.clean_up(keep_project=True)
