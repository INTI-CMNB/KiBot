"""
Tests of Gerber format.
- Simple 2 layers
- Inner layer

For debug information use:
pytest-3 --log-cli-level debug
"""

import os
import pytest
from . import context
from kibot.misc import PLOT_ERROR
from kibot.gs import GS
from kibot.__main__ import detect_kicad


def ki5_2_ki6(la):
    l_dot = la.replace('_', '.')
    if l_dot in GS.KICAD6_RENAME:
        la = GS.KICAD6_RENAME[l_dot].replace('.', '_')
    return la


GERBER_DIR = 'gerberdir'
ALL_LAYERS = ['B_Adhes',
              'B_CrtYd',
              'B_Cu',
              'B_Fab',
              'B_Mask',
              'B_Paste',
              'B_SilkS',
              'Cmts_User',
              'Dwgs_User',
              'Eco1_User',
              'Eco2_User',
              'Edge_Cuts',
              'F_Adhes',
              'F_CrtYd',
              'F_Cu',
              'F_Fab',
              'F_Mask',
              'F_Paste',
              'F_SilkS',
              'Margin',
              ]
detect_kicad()
# New layer names in KiCad 6
if GS.ki6:
    ALL_LAYERS = [ki5_2_ki6(la) for la in ALL_LAYERS]
ALL_EXTS = ['gba',
            'gbr',
            'gbl',
            'gbr',
            'gbs',
            'gbp',
            'gbo',
            'gbr',
            'gbr',
            'gbr',
            'gbr',
            'gm1',
            'gta',
            'gbr',
            'gtl',
            'gbr',
            'gts',
            'gtp',
            'gto',
            'gbr',
            ]
INNER_LAYERS = ['GND_Cu',
                'Power_Cu',
                'Signal1_Cu',
                'Signal2_Cu',
                ]
OLD_INNER_EXTS = ['g2', 'g5', 'g3', 'g4']
INNER_EXTS = ['g1', 'g4', 'g2', 'g3'] if GS.ki9 else OLD_INNER_EXTS


def test_gerber_2layer(test_dir):
    prj = 'simple_2layer'
    ctx = context.TestContext(test_dir, prj, prj, GERBER_DIR)
    ctx.run()

    f_cu = ctx.get_gerber_filename('F_Cu')
    ctx.expect_out_file(f_cu)
    ctx.expect_out_file(ctx.get_gerber_job_filename())

    ctx.expect_gerber_has_apertures(f_cu, [
        r"C,0.200000",
        r"R,2.000000X2.000000",
        r"C,1.000000"])

    # Expect a flash for the square pad
    ctx.expect_gerber_flash_at(f_cu, 5, (140, -100))
    ctx.clean_up()


def test_gerber_inner_ok(test_dir):
    prj = 'good-project'
    ctx = context.TestContext(test_dir, prj, 'gerber_inner', GERBER_DIR)
    rarfile = prj+'-result.rar'
    ctx.create_dummy_out_file(rarfile)
    ctx.run()
    files = [prj+'_GND_Cu.gbr', prj+'_Signal1.gbr', 'test-'+prj+'.gbrjob']
    for f in files:
        ctx.expect_out_file_d(f)
    ctx.test_compress_d(rarfile, files)
    ctx.clean_up()


def test_gerber_inner_wrong(test_dir):
    prj = 'good-project'
    ctx = context.TestContext(test_dir, prj, 'gerber_inner_wrong')
    ctx.run(PLOT_ERROR)
    assert ctx.search_err('is not valid for this board')
    ctx.clean_up()


def test_gerber_inner_wrong_2(test_dir):
    prj = 'good-project'
    ctx = context.TestContext(test_dir, prj, 'gerber_inner_wrong_2')
    ctx.run(PLOT_ERROR)
    assert ctx.search_err('is not valid for this board')
    ctx.clean_up()


def compose_fname(dir, prefix, layer, suffix, ext='gbr'):
    return os.path.join(dir, prefix+'-'+layer+suffix+'.'+ext)


def check_layers_exist(ctx, dir, prefix, layers, suffix):
    for layer in layers:
        ctx.expect_out_file(compose_fname(dir, prefix, layer, suffix))
    ctx.expect_out_file(compose_fname(dir, prefix, 'job', suffix, 'gbrjob'))


def check_components(ctx, dir, prefix, layers, suffix, exclude, include):
    if GS.ki6:
        layers = [ki5_2_ki6(la) for la in layers]
    for layer in layers:
        fname = compose_fname(dir, prefix, layer, suffix)
        inc = [r'%TO\.C,{}\*%'.format(v) for v in include]
        ctx.search_in_file(fname, inc)
        exc = [r'%TO\.C,{}\*%'.format(v) for v in exclude]
        ctx.search_not_in_file(fname, exc)


def test_gerber_variant_1(test_dir):
    prj = 'kibom-variant_3'
    ctx = context.TestContext(test_dir, prj, 'gerber_variant_1')
    ctx.run()
    # R3 is a component added to the PCB, included in all cases
    # variant: default     directory: gerber      components: R1, R2 and R3
    check_layers_exist(ctx, 'gerber', prj, ALL_LAYERS, '')
    check_components(ctx, 'gerber', prj, ['F_Paste', 'F_Adhes', 'F_Mask'], '', ['C1', 'C2'], ['R1', 'R2', 'R3'])
    # variant: production  directory: production  components: R1, R2, R3 and C2
    check_layers_exist(ctx, 'production', prj, ALL_LAYERS, '_(production)')
    check_components(ctx, 'production', prj, ['F_Paste', 'F_Adhes', 'F_Mask'], '_(production)', ['C1'],
                     ['R1', 'R2', 'R3', 'C2'])
    # variant: test        directory: test        components: R1, R3 and C2
    check_layers_exist(ctx, 'test', prj, ALL_LAYERS, '_(test)')
    check_components(ctx, 'test', prj, ['F_Paste', 'F_Adhes', 'F_Mask'], '_(test)', ['R2'], ['C1', 'R1', 'R3', 'C2'])
    ctx.clean_up(keep_project=True)


def test_gerber_protel_1(test_dir):
    prj = 'good-project'
    ctx = context.TestContext(test_dir, prj, 'gerber_inner_protel_1', GERBER_DIR)
    ctx.run()
    exts = ALL_EXTS+INNER_EXTS
    for n, suf in enumerate(ALL_LAYERS+INNER_LAYERS):
        ctx.expect_out_file_d(prj+'_'+suf+'.'+exts[n])
    ctx.clean_up()


def test_gerber_protel_2(test_dir):
    prj = 'good-project'
    ctx = context.TestContext(test_dir, prj, 'gerber_inner_protel_2', GERBER_DIR)
    ctx.run(extra_debug=True)
    inner = ['gin'+str(int(layer[-1])-1) for layer in OLD_INNER_EXTS]
    exts = ALL_EXTS+inner
    files = []
    for n, suf in enumerate(ALL_LAYERS+INNER_LAYERS):
        ext = exts[n]
        if ext == 'gm1':
            ext = 'e_cut'
        file = prj+'_'+suf+'.'+ext.upper()
        ctx.expect_out_file_d(file)
        files.append(file)
    assert ctx.search_err('Layer "Inner layer 6" (.*)isn\'t used')
    ctx.search_in_file_d('Report.txt', ['Top layer: good-project_F_Cu.GTL', 'Basename: good-project'])
    ctx.test_compress_d(prj+'-result.tar.gz', files)
    ctx.clean_up()


@pytest.mark.skipif(context.ki5(), reason="KiKit currently supports KiCad 6 only")
def test_gerber_sub_pcb_bp(test_dir):
    """ Test a multiboard example """
    prj = 'batteryPack'
    ctx = context.TestContext(test_dir, prj, 'gerber_sub_pcb', GERBER_DIR)
    ctx.run()
    # Check all outputs are there
    fname = f'{prj}-F_Cu_connector.gbr'
    ctx.search_in_file_d(fname, [r'%ADD10C,4.000000\*%'])
    ctx.search_not_in_file_d(fname, [r'%ADD10R,1.300000X0.450000\*%'])
    ctx.clean_up(keep_project=True)
