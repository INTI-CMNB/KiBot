"""
Tests of drill files

The 3Rs.kicad_pcb has R1 on top, R2 on bottom and a thru-hole component R3 on top.
We test:
- Separated N/PTH files with DRL, Gerber and PDF map

For debug information use:
pytest-3 --log-cli-level debug

"""

import os
import sys
from . import context

DRILL_DIR = 'Drill'
positions = {'R1': (105, 35, 'top'), 'R2': (110, 35, 'bottom'), 'R3': (110, 45, 'top')}

DRILL_TABLE_HEADER = ['Count', 'Hole Size', 'Plated', 'Hole Shape', 'Drill Layer Pair', 'Hole Type']
ROWS_PTH = [['1', '0.40mm (15.75mils)', 'PTH', 'Round', 'F.Cu - B.Cu', 'Via'],
            ['2', '1.00mm (39.37mils)', 'PTH', 'Round', 'F.Cu - B.Cu', 'Pad'],
            ['Total 3', '', '', '', '', '']]
ROWS_NPTH = [['1', '2.10mm (82.68mils)', 'NPTH', 'Round', 'F.Cu - B.Cu', 'Mechanical'],
             ['Total 1', '', '', '', '', '']]
ROWS_PTH_NPTH = [['1', '0.40mm (15.75mils)', 'PTH', 'Round', 'F.Cu - B.Cu', 'Via'],
                 ['2', '1.00mm (39.37mils)', 'PTH', 'Round', 'F.Cu - B.Cu', 'Pad'],
                 ['1', '2.10mm (82.68mils)', 'NPTH', 'Round', 'F.Cu - B.Cu', 'Mechanical'],
                 ['Total 4', '', '', '', '', '']]
ROWS_F1 = [['1', '0.40mm (15.75mils)', 'PTH', 'Round', 'F.Cu - El1', 'Via'],
           ['Total 1', '', '', '', '', '']]
ROWS_12 = [['1', '0.40mm (15.75mils)', 'PTH', 'Round', 'El1 - In2.Cu', 'Via'],
           ['Total 1', '', '', '', '', '']]


def do_3Rs(test_dir, conf, modern, single=False):
    ctx = context.TestContext(test_dir, '3Rs_bv', conf, DRILL_DIR, test_name=sys._getframe(1).f_code.co_name)
    ctx.run()
    # Check all outputs are there
    pth_drl = ctx.get_pth_drl_filename()
    npth_drl = ctx.get_npth_drl_filename()
    f1_drl = ctx.get_f1_drl_filename()
    i12_drl = ctx.get_12_drl_filename()
    pth_pdf_drl = ctx.get_pth_pdf_drl_filename()
    npth_pdf_drl = ctx.get_npth_pdf_drl_filename()
    f1_pdf_drl = ctx.get_f1_pdf_drl_filename()
    i12_pdf_drl = ctx.get_12_pdf_drl_filename()
    pth_gbr_drl = ctx.get_pth_gbr_drl_filename()
    npth_gbr_drl = ctx.get_npth_gbr_drl_filename()
    f1_gbr_drl = ctx.get_f1_gbr_drl_filename()
    i12_gbr_drl = ctx.get_12_gbr_drl_filename()
    pth_csv_drl = ctx.get_pth_csv_drl_filename()
    npth_csv_drl = ctx.get_npth_csv_drl_filename()
    f1_csv_drl = ctx.get_f1_csv_drl_filename()
    i12_csv_drl = ctx.get_12_csv_drl_filename()
    report = 'report.rpt'

    if modern:
        pth_drl = pth_drl.replace('PTH', 'PTH_drill')
        npth_drl = npth_drl.replace('PTH', 'PTH_drill')
        f1_drl = f1_drl.replace('front-in1', 'front-in1_drill')
        i12_drl = i12_drl.replace('in1-in2', 'in1-in2_drill')
        pth_gbr_drl = pth_gbr_drl.replace('-drl', '_drill')
        npth_gbr_drl = npth_gbr_drl.replace('-drl', '_drill')
        f1_gbr_drl = f1_gbr_drl.replace('-drl', '_drill')
        i12_gbr_drl = i12_gbr_drl.replace('-drl', '_drill')
        pth_pdf_drl = pth_pdf_drl.replace('-drl', '_drill')
        npth_pdf_drl = npth_pdf_drl.replace('-drl', '_drill')
        f1_pdf_drl = f1_pdf_drl.replace('-drl', '_drill')
        i12_pdf_drl = i12_pdf_drl.replace('-drl', '_drill')
        report = '3Rs_bv-drill_report.txt'
        if single:
            pth_drl = pth_drl.replace('PTH_', '')
            npth_drl = npth_drl.replace('NPTH_', '')
            pth_pdf_drl = pth_pdf_drl.replace('PTH_', '')
            npth_pdf_drl = npth_pdf_drl.replace('NPTH_', '')
            npth_csv_drl = npth_csv_drl.replace('_NPTH', '')
    elif single:
        pth_drl = pth_drl.replace('-PTH', '')
        npth_drl = npth_drl.replace('-NPTH', '')
        pth_pdf_drl = pth_pdf_drl.replace('-PTH', '')
        npth_pdf_drl = npth_pdf_drl.replace('-NPTH', '')
        npth_csv_drl = npth_csv_drl.replace('_NPTH', '')

    ctx.expect_out_file(os.path.join(DRILL_DIR, report))
    ctx.expect_out_file(pth_drl)
    ctx.expect_out_file(npth_drl)
    ctx.expect_out_file(f1_drl)
    ctx.expect_out_file(i12_drl)
    ctx.expect_out_file(pth_gbr_drl)
    ctx.expect_out_file(npth_gbr_drl)
    ctx.expect_out_file(f1_gbr_drl)
    ctx.expect_out_file(i12_gbr_drl)
    ctx.expect_out_file(pth_pdf_drl)
    ctx.expect_out_file(npth_pdf_drl)
    ctx.expect_out_file(f1_pdf_drl)
    ctx.expect_out_file(i12_pdf_drl)
    ctx.expect_out_file(pth_csv_drl)
    ctx.expect_out_file(npth_csv_drl)
    ctx.expect_out_file(f1_csv_drl)
    ctx.expect_out_file(i12_csv_drl)
    # We have R3 at (110, 45) length is 9 mm on X, drill 1 mm
    ctx.search_in_file(pth_drl, ['X110.0Y-45.0', 'X119.0Y-45.0'])
    ctx.expect_gerber_flash_at(pth_gbr_drl, 6, (110, -45))
    ctx.expect_gerber_has_apertures(pth_gbr_drl, ['C,1.000000'])
    # We have a mounting hole at (120, 29) is 2.1 mm in diameter
    ctx.search_in_file(npth_drl, ['X120.0Y-29.0', 'T.C2.100'])
    ctx.expect_gerber_flash_at(npth_gbr_drl, 6, (120, -29))
    ctx.expect_gerber_has_apertures(npth_gbr_drl, ['C,2.100000'])
    # Verify the generated drill tables
    rows_pth, header_pth, _ = ctx.load_csv(pth_csv_drl.replace(DRILL_DIR+'/', ''))
    rows_npth, header_npth, _ = ctx.load_csv(npth_csv_drl.replace(DRILL_DIR+'/', ''))
    rows_f1, header_f1, _ = ctx.load_csv(f1_csv_drl.replace(DRILL_DIR+'/', ''))
    rows_12, header_12, _ = ctx.load_csv(i12_csv_drl.replace(DRILL_DIR+'/', ''))
    if single:
        table_verif(rows_pth, ROWS_PTH_NPTH, header_pth, context.ki5())
    else:
        table_verif(rows_pth, ROWS_PTH, header_pth, context.ki5())
        table_verif(rows_npth, ROWS_NPTH, header_npth, context.ki5())
    table_verif(rows_f1, ROWS_F1, header_f1, context.ki5())
    table_verif(rows_12, ROWS_12, header_12, context.ki5())
    ctx.clean_up()


def table_verif(rows, ref_rows, header, ki5):
    if ki5:
        assert header == DRILL_TABLE_HEADER[:-1]  # KiCad 5 doesn't have Hole type
        assert rows == [row[:-1] for row in ref_rows]
    else:
        assert header == DRILL_TABLE_HEADER
        assert rows == ref_rows


def test_drill_3Rs(test_dir):
    do_3Rs(test_dir, 'drill', True)


def test_drill_single_3Rs(test_dir):
    do_3Rs(test_dir, 'drill_single', True, True)


def test_drill_legacy_3Rs(test_dir):
    do_3Rs(test_dir, 'drill_legacy', False)


def test_drill_legacy_s_3Rs(test_dir):
    do_3Rs(test_dir, 'drill_legacy_s', False, True)


def test_drill_sub_pcb_bp(test_dir):
    """ Test a multiboard example """
    prj = 'batteryPack'
    ctx = context.TestContext(test_dir, prj, 'drill_sub_pcb', 'Drill')
    ctx.run()
    # Check all outputs are there
    fname = prj+'-drill_connector.drl'
    # ctx.search_in_file_d(fname, ['X29.75Y-28.09', 'T3C3.200']) KiKit
    ctx.search_in_file_d(fname, ['X137.5Y-102.0', 'T3C3.200'])  # Currently us
    ctx.search_not_in_file_d(fname, ['X189.0Y-59.0', 'T1C0.400'])
    ctx.clean_up(keep_project=True)
