"""
Tests of Printing Schematic files

We test:
- STEP for bom.kicad_pcb

For debug information use:
pytest-3 --log-cli-level debug

"""
import os
import pytest
from glob import glob
from . import context


STEP_DIR = '3D'
# STEP_FILE = 'bom.step'


@pytest.mark.slow
@pytest.mark.kicad2step
def test_step_1(test_dir):
    prj = 'bom'
    ctx = context.TestContext(test_dir, prj, 'step_simple', STEP_DIR)
    ctx.run()
    # Check all outputs are there
    name = prj+'-3D.step'
    ctx.expect_out_file_d(name)
    # Check the R and C 3D models are there
    ctx.search_in_file_d(name, ['R_0805_2012Metric', 'C_0805_2012Metric'])
    ctx.search_err(['Missing 3D model for R1: `(.*)R_0805_2012Metrico',
                    'Failed to download `(.*)R_0805_2012Metrico'])
    ctx.clean_up()


# Generate STEP files using kicad-cli directly
@pytest.mark.skipif(not context.ki9(), reason="Needs KiCad 9")
def test_step_k9(test_dir):
    prj = 'bom'
    ctx = context.TestContext(test_dir, prj, 'export_3d_step_simple', STEP_DIR)
    ctx.run()
    # Check all outputs are there
    name = prj+'-3D.step'
    ctx.expect_out_file_d(name)
    # Check the R and C 3D models are there
    ctx.search_in_file_d(name, ['R_0805_2012Metric', 'C_0805_2012Metric'])
    ctx.search_err(['Missing 3D model for R1: `(.*)R_0805_2012Metrico',
                    'Failed to download `(.*)R_0805_2012Metrico'])
    ctx.clean_up()


# Generate 3D PDF files using kicad-cli
@pytest.mark.skipif(not context.ki10(), reason="Needs KiCad 10")
def test_3d_pdf(test_dir):
    prj = 'bom'
    ctx = context.TestContext(test_dir, prj, 'export_3d_pdf_simple', STEP_DIR)
    ctx.run()
    # Check all outputs are there
    name = prj+'-3D.pdf'
    ctx.expect_out_file_d(name)
    ctx.clean_up()


@pytest.mark.slow
@pytest.mark.kicad2step
def test_step_2(test_dir):
    prj = 'bom_fake_models'
    yaml = 'step_simple_2'
    if context.ki6():
        yaml += '_k6'
    ctx = context.TestContext(test_dir, prj, 'step_simple_2', STEP_DIR)
    ctx.run()
    # Check all outputs are there
    ctx.expect_out_file_d(prj+'-3D.step')
    ctx.search_err(['Missing 3D model for C1', 'Could not add 3D model to C1'], invert=True)
    ctx.clean_up(keep_project=True)


@pytest.mark.slow
@pytest.mark.kicad2step
def test_step_3(test_dir):
    prj = 'bom'
    ctx = context.TestContext(test_dir, prj, 'step_simple_3', STEP_DIR)
    ctx.run()
    # Check all outputs are there
    ctx.expect_out_file_d(prj+'.step')
    ctx.clean_up()


@pytest.mark.slow
@pytest.mark.kicad2step
def test_step_gl_env(test_dir):
    prj = 'bom'
    ctx = context.TestContext(test_dir, prj, 'step_gl_env', STEP_DIR)
    ctx.run()
    # Check all outputs are there
    name = prj+'-3D.step'
    ctx.expect_out_file_d(name)
    # Check the R and C 3D models are there
    ctx.search_in_file_d(name, ['R_0805_2012Metric', 'R_0805_2012Metrico', 'C_0805_2012Metric'])
    ctx.search_err(['Missing 3D model for R1: `(.*)R_0805_2012Metrico',
                    'Failed to download `(.*)R_0805_2012Metrico'], invert=True)
    ctx.clean_up()


@pytest.mark.slow
@pytest.mark.kicad2step
@pytest.mark.skipif(context.ki5(), reason="uses text variables")
def test_step_alias_1(test_dir):
    prj = 'bom_w_prj'
    ctx = context.TestContext(test_dir, prj, 'step_alias', STEP_DIR)
    ctx.run(extra_debug=True)
    # Check all outputs are there
    name = prj+'-3D.step'
    ctx.expect_out_file_d(name)
    # Check the R and C 3D models are there
    ctx.search_in_file_d(name, ['R_0805_2012Metric', 'R_0805_2012Metrico', 'C_0805_2012Metric'])
    ctx.search_err(['Missing 3D model for R1: `(.*)R_0805_2012Metrico',
                    'Failed to download `(.*)R_0805_2012Metrico'], invert=True)
    ctx.clean_up(keep_project=True)


@pytest.mark.slow
@pytest.mark.kicad2step
@pytest.mark.skipif(context.ki5(), reason="uses 3D aliases")
def test_step_alias_2(test_dir):
    prj = 'bom_w_prj'
    ctx = context.TestContext(test_dir, prj, 'step_alias_2', STEP_DIR)
    ctx.run(extra_debug=True)
    # Check all outputs are there
    name = prj+'-3D.step'
    ctx.expect_out_file_d(name)
    # Check the R and C 3D models are there
    ctx.search_in_file_d(name, ['R_0805_2012Metric', 'R_0805_2012Metrico', 'C_0805_2012Metric'])
    ctx.search_err(['Missing 3D model for R1: `(.*)R_0805_2012Metrico',
                    'Failed to download `(.*)R_0805_2012Metrico'], invert=True)
    ctx.clean_up(keep_project=True)


@pytest.mark.slow
@pytest.mark.kicad2step
def test_step_variant_1(test_dir):
    prj = 'kibom-variant_3'
    ctx = context.TestContext(test_dir, prj, 'step_variant_1')
    tmps_before = glob(os.path.join(ctx.get_board_dir(), 'tmp*pro'))
    ctx.run(extra_debug=True)
    # Check all outputs are there
    ctx.expect_out_file(prj+'-3D.step')
    tmps = glob(os.path.join(ctx.get_board_dir(), 'tmp*pro'))
    assert len(tmps) == len(tmps_before), tmps
    ctx.clean_up(keep_project=True)


@pytest.mark.skipif(not context.ki7(), reason="KiCad 7 3D relative dirs")
def test_step_rel_dir_1(test_dir):
    prj = 'test'
    ctx = context.TestContext(test_dir, '3d_rel_path/'+prj, 'step_simple', STEP_DIR)
    ctx.run()
    # Check all outputs are there
    name = prj+'-3D.step'
    ctx.expect_out_file_d(name)
    # Check the R and C 3D models are there
    ctx.search_in_file_d(name, [r"PRODUCT\('R',"])
    # KiCad 7/8 says "Add", 9 says "Adding", 10 says nothing
    if not context.ki10():
        ctx.search_err(['Add(.*) component R1'])
    ctx.clean_up(keep_project=True)


# @pytest.mark.indep But we use KiCad 5 ...
@pytest.mark.skipif(not context.ki7() or context.ki8(), reason="Is indep, but needs KiCad 7")
def test_step_ea_dl_1(test_dir):
    prj = 'easyeda_3d_dl'
    ctx = context.TestContext(test_dir, prj, 'step_simple', STEP_DIR)
    os.environ['KIBOT_3D_MODELS'] = os.path.join(ctx.output_dir, STEP_DIR)
    ctx.run(kicost=True)
    del os.environ['KIBOT_3D_MODELS']
    # Check all outputs are there
    name = prj+'-3D.step'
    step = 'SOT-23-3P_L2.9-W1.3-H1.0-LS2.4-P0.95.step'
    wrl = 'SOT-23-3P_L2.9-W1.3-H1.0-LS2.4-P0.95.wrl'
    ctx.expect_out_file_d([name, step, wrl])
    ctx.search_in_file_d(step, 'This is a STEP file')
    ctx.compare_txt(os.path.join(STEP_DIR, wrl))
    ctx.clean_up(keep_project=True)


@pytest.mark.slow
@pytest.mark.pcbnew
def test_render_3d_variant_1(test_dir):
    # Text variables to ensure they are rendered.
    # Traces
    prj = 'kibom-variant_3_txt'
    yaml = 'render_3d_variant_1'
    if context.ki5():
        yaml += '_k5'
    ctx = context.TestContext(test_dir, prj, yaml)
    ctx.run(extra_debug=True)
    # Check all outputs are there
    name = prj+'-3D_top.png'
    ctx.expect_out_file(name)
    ctx.compare_image(name, fuzz='48%', tol=1000, trim=True)
    ctx.clean_up(keep_project=True)


@pytest.mark.slow
@pytest.mark.pcbnew
@pytest.mark.skipif(not context.ki7(), reason="slow")
def test_render_3d_res_tht_1(test_dir):
    """ Very naive test, just check if working """
    prj = 'resistor_tht'
    yaml = 'render_3d_tht_res_1'
    ctx = context.TestContext(test_dir, prj, yaml)
    ctx.run()  # extra_debug=True
    # Check all outputs are there
    name = prj+'-3D_top.png'
    ctx.expect_out_file(name)
    ctx.clean_up(keep_project=True)


@pytest.mark.slow
@pytest.mark.pcbnew
@pytest.mark.skipif(context.ki5(), reason="uses pcb2blender")
def test_blender_export_1(test_dir):
    prj = 'light_control'
    yaml = 'blender_export_1'
    ctx = context.TestContext(test_dir, prj, yaml)
    ctx.run(extra_debug=True)
    # Check all outputs are there
    name = prj+'-3D_blender_top.blend'
    ctx.expect_out_file(name, sub=True)
    name = prj+'.pcb3d'
    ctx.expect_out_file(name, sub=True)
    # ctx.compare_image(name, fuzz='7%', tol=1000)
    ctx.clean_up(keep_project=True)


@pytest.mark.slow
@pytest.mark.pcbnew
@pytest.mark.skipif(context.ki5(), reason="uses pcb2blender")
def test_blender_export_2(test_dir):
    """ Stacked PCBs using the JSON stack-up """
    prj = 'batteryPack'
    yaml = 'pcb2blender_tools_3'
    ctx = context.TestContext(test_dir, prj, yaml)
    ctx.run(extra_debug=True)
    name = prj+'.pcb3d'
    ctx.expect_out_file(name, sub=True)
    ctx.clean_up()
