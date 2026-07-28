"""
Tests of PDF format (PCB Plot).

For debug information use:
pytest-3 --log-cli-level debug
"""
import os
from . import context
PS_DIR = 'PDF'
DIFF_TOL = 10 if os.path.isfile('/etc/debian_version') else 250


def test_pdf(test_dir):
    prj = 'simple_2layer'
    ctx = context.TestContext(test_dir, prj, 'pdf', PS_DIR)
    ctx.run()
    ctx.expect_out_file(ctx.get_gerber_filename('F_Cu', '.pdf'))
    ctx.expect_out_file(ctx.get_gerber_filename('B_Silks', '.pdf'))
    ctx.dont_expect_out_file(ctx.get_gerber_job_filename())
    ctx.clean_up()


def test_pdf_refill_1(test_dir):
    prj = 'zone-refill'
    ctx = context.TestContext(test_dir, prj, 'pdf_zone-refill')
    ctx.run()
    b_cu = ctx.get_gerber_filename('B_Cu', '.pdf')
    ctx.expect_out_file(b_cu)
    ctx.compare_image(b_cu, tol=DIFF_TOL)
    ctx.clean_up()


def test_pdf_refill_2(test_dir):
    prj = 'zone-refill'
    ctx = context.TestContext(test_dir, prj, 'pdf_zone-refill_2')
    ori = ctx.board_file
    bkp = ori+'-bak'
    try:
        ctx.run()
        b_cu = ctx.get_gerber_filename('B_Cu', '.pdf')
        ctx.expect_out_file(b_cu)
        ctx.compare_image(b_cu, tol=DIFF_TOL)
        assert os.path.isfile(bkp)
    finally:
        if os.path.isfile(bkp):
            os.replace(bkp, ori)
    ctx.clean_up()


def test_pdf_variant_1(test_dir):
    # Here we cross C2
    # In the past KiCad crossed C1, but "disable_kicad_cross_on_fab" currently avoids it
    # On KiCad 9.0.5 KiCad seems to always ignore po.SetCrossoutDNPFPsOnFabLayers(False) and never crosses it
    prj = 'kibom-variant_4'
    ctx = context.TestContext(test_dir, prj, 'pdf_variant_1')
    ctx.run()
    fname = prj+'-F_Fab.pdf'
    ctx.expect_out_file(fname)
    ctx.compare_image(fname, tol=DIFF_TOL)
    fname = prj+'-B_Fab.pdf'
    ctx.expect_out_file(fname)
    ctx.compare_image(fname, tol=DIFF_TOL)
    ctx.clean_up()
