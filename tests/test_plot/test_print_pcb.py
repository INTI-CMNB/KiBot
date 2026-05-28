"""
Tests of Printing PCB files

We test:
- PDF for bom.kicad_pcb

For debug information use:
pytest-3 --log-cli-level debug

"""
import logging
import os
import pytest
from . import context
PDF_DIR = 'Layers'
PDF_FILE = 'bom-F_Cu+F_SilkS.pdf'
PDF_FILE_B = 'PCB_Bot.pdf'
PDF_FILE_C = 'PCB_Bot_def.pdf'
# Even the Ubuntu builds are slightly different
is_debian = os.path.isfile('/etc/debian_version') and not os.path.isfile('/etc/lsb-release')
DIFF_TOL = 10 if is_debian else 5000
DIFF_TOL2 = 100 if is_debian else 5000


@pytest.mark.slow
@pytest.mark.pcbnew
def test_print_pcb_simple(test_dir):
    prj = 'bom'
    ctx = context.TestContext(test_dir, prj, 'print_pcb', PDF_DIR)
    ctx.run()
    # Check all outputs are there
    ctx.expect_out_file_d(PDF_FILE)
    ctx.clean_up()


@pytest.mark.slow
@pytest.mark.pcbnew
def test_print_pcb_svg_simple_1(test_dir):
    prj = 'bom'
    ctx = context.TestContext(test_dir, prj, 'print_pcb_svg')
    ctx.run()
    # Check all outputs are there
    file = PDF_FILE.replace('.pdf', '.svg')
    ctx.expect_out_file(file)
    ctx.compare_image(file)
    ctx.clean_up()


@pytest.mark.slow
@pytest.mark.pcbnew
def test_print_pcb_svg_simple_2(test_dir):
    """ Check the portrait version is OK """
    prj = 'bom_portrait'
    ctx = context.TestContext(test_dir, prj, 'print_pcb_svg')
    ctx.run()
    # Check all outputs are there
    file = prj+'-F_Cu+F_SilkS.svg'
    ctx.expect_out_file(file)
    ctx.compare_image(file)
    ctx.clean_up()


@pytest.mark.slow
@pytest.mark.pcbnew
def test_print_pcb_refill_1(test_dir):
    prj = 'zone-refill'
    ctx = context.TestContext(test_dir, prj, 'print_pcb_zone-refill')
    ctx.run()
    ctx.expect_out_file(PDF_FILE_B)
    ctx.compare_image(PDF_FILE_B, tol=10)
    ctx.clean_up()


@pytest.mark.slow
@pytest.mark.pcbnew
def test_print_pcb_refill_2(test_dir):
    """ Using KiCad 6 colors """
    if context.ki5():
        return
    prj = 'zone-refill'
    ctx = context.TestContext(test_dir, prj, 'print_pcb_zone-refill_def')
    ctx.run()
    ctx.expect_out_file(PDF_FILE_B)
    ctx.compare_image(PDF_FILE_B, PDF_FILE_C, tol=10)
    ctx.clean_up()


@pytest.mark.slow
@pytest.mark.pcbnew
def test_print_variant_1(test_dir):
    prj = 'kibom-variant_3_txt'
    ctx = context.TestContext(test_dir, prj, 'print_pcb_variant_1')
    ctx.run()
    # Check all outputs are there
    fname = prj+'-F_Fab.pdf'
    ctx.search_err(r'KiCad project file not found', True)
    ctx.expect_out_file(fname)
    ctx.compare_pdf(fname, height='100%')
    ctx.clean_up(keep_project=True)


@pytest.mark.slow
@pytest.mark.pcbnew
def test_print_pcb_options(test_dir):
    prj = 'bom'
    ctx = context.TestContext(test_dir, prj, 'print_pcb_options', PDF_DIR)
    ctx.run()
    # Check all outputs are there
    ctx.expect_out_file(PDF_FILE)
    ctx.compare_pdf(PDF_FILE)
    ctx.clean_up()


@pytest.mark.slow
@pytest.mark.pcbnew
def test_print_wrong_paste(test_dir):
    prj = 'wrong_paste'
    ctx = context.TestContext(test_dir, prj, 'wrong_paste', PDF_DIR)
    ctx.run()
    # Check all outputs are there
    ctx.expect_out_file(prj+'-F_Fab.pdf')
    ctx.search_err(r'Pad with solder paste, but no copper')
    ctx.clean_up()


@pytest.mark.slow
@pytest.mark.pcbnew
def test_pcb_print_simple_1(test_dir):
    prj = 'light_control'
    ctx = context.TestContext(test_dir, prj, 'pcb_print_2')
    ctx.run(extra_debug=True)
    ctx.expect_out_file(prj+'-F_Cu_mono.png')
    ctx.expect_out_file(prj+'-F_Cu_color.png')
    if is_debian:
        ctx.compare_image(prj+'-F_Cu_color.png', height='100%', fuzz='10%', tol=50)
    ctx.expect_out_file(prj+'-assembly_page_01.eps')
    ctx.expect_out_file(prj+'-assembly_page_01.svg')
    ctx.expect_out_file(prj+'-assembly.ps')
    ctx.clean_up(keep_project=True)


@pytest.mark.slow
@pytest.mark.pcbnew
def test_pcb_print_simple_2(test_dir):
    if context.ki6():
        prj = 'pcb_print_rare'
        yaml = 'pcb_print_3'
    else:
        prj = 'bom_portrait'
        yaml = 'pcb_print_4'
    ctx = context.TestContext(test_dir, prj, yaml)
    ctx.run()
    file = ctx.expect_out_file(prj+'-assembly.pdf')
    w, h = ctx.get_pdf_size(file)
    logging.debug('PDF size {} x {} mm'.format(w, h))
    if context.ki6():
        assert abs(w-431.8) < 0.1 and abs(h-279.4) < 0.1
    else:
        assert abs(w-210.0) < 0.1 and abs(h-297.0) < 0.1
    ctx.clean_up()


@pytest.mark.skipif(context.ki5(), reason="uses KiCad 6 nested zones")
def test_pcb_print_multizone_1(test_dir):
    prj = 'print_multizone'
    ctx = context.TestContext(test_dir, prj, 'print_multizone')
    ctx.run()
    ctx.compare_image(prj+'-assembly_page_01.png', tol=DIFF_TOL)
    # 7.0.1+f1f69c6 generates 48 diff compared to 7.0.1 release
    ctx.compare_image(prj+'-assembly_page_02.png', tol=DIFF_TOL2)
    ctx.clean_up()


@pytest.mark.skipif(not context.ki7(), reason="Implemented for KiCad 7+")
def test_pcb_print_drill_map(test_dir):
    prj = 'drill_types'
    ctx = context.TestContext(test_dir, prj, 'print_drill_map')
    ctx.run()
    ctx.compare_image(prj+'-assembly_page_01.png', diff='diff_01.png', tol=DIFF_TOL, height='90%')
    ctx.compare_image(prj+'-assembly_page_02.png', diff='diff_02.png', tol=DIFF_TOL, height='90%')
    ctx.compare_image(prj+'-assembly_page_03.png', diff='diff_03.png', tol=DIFF_TOL, height='90%')
    ctx.compare_image(prj+'-assembly_page_04.png', diff='diff_04.png', tol=DIFF_TOL, height='90%')
    ctx.compare_image(prj+'-assembly_page_05.png', diff='diff_05.png', tol=DIFF_TOL, height='90%')
    ctx.compare_image(prj+'-assembly_page_06.png', diff='diff_06.png', tol=DIFF_TOL, height='90%')
    ctx.clean_up()


@pytest.mark.skipif(not context.ki7(), reason="Implemented for KiCad 7+")
def test_pcb_print_drill_table(test_dir):
    prj = 'drill_types'
    ctx = context.TestContext(test_dir, prj, 'print_drill_table')
    ctx.run()
    ctx.compare_image(prj+'-assembly_page_01_table.png', diff='diff_01.png', tol=DIFF_TOL)
    ctx.compare_image(prj+'-assembly_page_02_table.png', diff='diff_02.png', tol=DIFF_TOL)
    ctx.compare_image(prj+'-assembly_page_03_table.png', diff='diff_03.png', tol=DIFF_TOL)
    ctx.compare_image(prj+'-assembly_page_04_table.png', diff='diff_04.png', tol=DIFF_TOL)
    ctx.compare_image(prj+'-assembly_page_05_table.png', diff='diff_05.png', tol=DIFF_TOL)
    ctx.compare_image(prj+'-assembly_page_06_table.png', diff='diff_06.png', tol=DIFF_TOL)
    ctx.clean_up()


@pytest.mark.skipif(not context.ki7(), reason="Just checking with modern KiCad")
def test_var_rename_footprint_1(test_dir):
    prj = 'var_rename_footprint'
    ctx = context.TestContext(test_dir, prj, prj, 'PNG')
    ctx.run(extra=['-g', 'variant=production'])
    ctx.compare_image(prj+'-assembly_page_01_(PROD).png', tol=DIFF_TOL, sub=True)
    if context.ki8():
        ctx.compare_image(prj+'-assembly_page_02_(PROD).png', tol=DIFF_TOL, sub=True)
    ctx.run(extra=['-g', 'variant=development'])
    ctx.compare_image(prj+'-assembly_page_01_(DEV).png', tol=DIFF_TOL, sub=True)
    if context.ki8():
        ctx.compare_image(prj+'-assembly_page_02_(DEV).png', tol=DIFF_TOL, sub=True)
    ctx.clean_up()


@pytest.mark.skipif(not context.ki7(), reason="Just checking with modern KiCad")
def test_var_rename_kicost_footprint_1(test_dir):
    prj = 'var_rename_kicost_footprint'
    ctx = context.TestContext(test_dir, prj, prj, 'PNG')
    ctx.run(extra=['-g', 'variant=production'])
    ctx.compare_image(prj+'-assembly_page_01_(PROD).png', tol=DIFF_TOL, sub=True)
    ctx.run(extra=['-g', 'variant=development'])
    ctx.compare_image(prj+'-assembly_page_01_(DEV).png', tol=DIFF_TOL, sub=True)
    ctx.clean_up()


@pytest.mark.skipif((not context.ki9()) or context.ki10(), reason="KiCad 9 using KiCad 10 vars")
def test_print_pcb_variant_var_ki9(test_dir):
    """ Test printing a PCB that uses VARIANT and VARIANT_DESC in:
        - Front copper layer
        - Front silkscreen
        - The worksheet itself
        - Fields used in the worksheet
        We try 2 variants and no variant.
        This test uses KiCad 9 and KiBoM variants.
        The result isn't really good because we can't currently tell to KiCad 9 about variables on-the-fly """
    prj = 'variant_var'
    ctx = context.TestContext(test_dir, prj, prj, 'PNG')
    ctx.run(extra=['--variant', 'production', '--variant', 'development', '--variant', 'NONE'])
    ctx.run()
    ctx.compare_image(prj+'-assembly_page_01_(PROD).png', tol=DIFF_TOL, sub=True)
    ctx.compare_image(prj+'-assembly_page_01_(DEV).png', tol=DIFF_TOL, sub=True)
    ctx.compare_image(prj+'-assembly_page_01.png', tol=DIFF_TOL, sub=True)
    ctx.clean_up(keep_project=True)


@pytest.mark.skipif(not context.ki10(), reason="KiCad native variants")
def test_print_pcb_variant_var_ki10(test_dir):
    """ Test printing a PCB that uses VARIANT and VARIANT_DESC in:
        - Front copper layer
        - Front silkscreen
        - The worksheet itself
        - Fields used in the worksheet
        We try 2 variants and no variant.
        This test uses KiCad 10 native variants and the internal print mechanism """
    prj = 'variant_var'
    ctx = context.TestContext(test_dir, prj, 'variant_var_ki10', 'PNG')
    ctx.run(extra=['--variant', 'production', '--variant', 'development', '--variant', 'NONE'])
    ctx.compare_image(prj+'-assembly_page_01_production.png', tol=DIFF_TOL, sub=True)
    ctx.compare_image(prj+'-assembly_page_01_development.png', tol=DIFF_TOL, sub=True)
    ctx.compare_image(prj+'-assembly_page_01.png', tol=DIFF_TOL, sub=True)
    ctx.clean_up(keep_project=True)
