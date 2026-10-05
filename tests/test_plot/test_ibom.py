"""
Tests of InteractiveHtmlBom BoM files

The bom.sch has R1, R2 and C1
We test:
- HTML

For debug information use:
pytest-3 --log-cli-level debug

"""
import json
import logging
import os
import pytest
import re
from . import context
from utils.lzstring import LZString
from kibot.misc import (BOM_ERROR)

BOM_DIR = 'BoM'
IBOM_OUT = 'bom-ibom.html'


def check_modules(ctx, fname, expected):
    with open(ctx.get_out_path(os.path.join(BOM_DIR, fname)), 'rt') as f:
        text = f.read()
    m = re.search(r'var pcbdata = JSON.parse\(LZString.decompressFromBase64\("(.*)"\)\)', text, re.MULTILINE)
    assert m, text
    lz = LZString()
    js = lz.decompressFromBase64(m.group(1))
    # with open('/tmp/dump', 'wt') as f:
    #    f.write(js)
    data = json.loads(js)
    skipped = data['bom']['skipped']
    footprints_name = 'modules' if 'modules' in data else 'footprints'
    modules = [m['ref'] for m in data[footprints_name]]
    assert len(modules)-len(skipped) == len(expected)
    logging.debug("{} components OK".format(len(expected)))
    for m in expected:
        assert m in modules
        assert modules.index(m) not in skipped
    logging.debug("List of components OK")


def test_ibom_1(test_dir):
    prj = 'bom'
    ctx = context.TestContext(test_dir, prj, 'ibom', BOM_DIR)
    ctx.run()
    # Check all outputs are there
    # We use this format: %f_iBoM
    ctx.expect_out_file_d(prj+'_iBoM.html')
    ctx.clean_up()


def test_ibom_no_ops(test_dir):
    prj = 'bom'
    ctx = context.TestContext(test_dir, prj, 'ibom_no_ops', BOM_DIR)
    ctx.run()
    ctx.expect_out_file_d(IBOM_OUT)
    check_modules(ctx, IBOM_OUT, ['C1', 'R1', 'R2'])
    ctx.clean_up()


def test_ibom_fail(test_dir):
    ctx = context.TestContext(test_dir, 'ibom_fail', 'ibom')
    ctx.run(BOM_ERROR)
    ctx.clean_up()


def test_ibom_all_ops(test_dir):
    prj = 'bom_adhes'
    ctx = context.TestContext(test_dir, prj, 'ibom_all_ops', BOM_DIR, add_cfg_kmajor=True)
    ctx.run()
    out_file = IBOM_OUT.replace('bom-', prj+'-')
    ctx.expect_out_file_d(out_file)
    # These options are transferred as defaults:
    ctx.search_in_file_d(out_file, [r'"dark_mode": true',
                                    r'"show_pads": false',
                                    r'"show_fabrication": true',
                                    r'"show_silkscreen": false',
                                    r'"highlight_pin1": "selected"',
                                    r'"redraw_on_drag": false',
                                    r'"board_rotation": 18.0',  # 90/5
                                    r'"offset_back_rotation": true',
                                    r'"checkboxes": "Sourced,Placed,Bogus"',
                                    r'"bom_view": "top-bottom"',
                                    r'"layer_view": "B"',
                                    r'"fields": \["Value", "Footprint", "EF"\]'])
    ctx.clean_up()


@pytest.mark.slow
def test_ibom_variant_1(test_dir):
    prj = 'kibom-variante'
    ctx = context.TestContext(test_dir, prj, 'ibom_variant_1', BOM_DIR)
    ctx.run(extra_debug=True)
    # No variant
    logging.debug("* No variant")
    check_modules(ctx, prj+'-ibom.html', ['R1', 'R2', 'R3'])
    # V1
    logging.debug("* t1_v1 variant")
    check_modules(ctx, prj+'-ibom_(V1).html', ['R1', 'R2'])
    # V2
    logging.debug("* t1_v2 variant")
    check_modules(ctx, prj+'-ibom_(V2).html', ['R1', 'R3'])
    # V3
    logging.debug("* t1_v3 variant")
    check_modules(ctx, prj+'-ibom_V3.html', ['R1', 'R4'])
    # V1,V3
    logging.debug("* `bla bla` variant")
    check_modules(ctx, prj+'-ibom_bla_bla.html', ['R4'])
    ctx.clean_up()


@pytest.mark.skipif(not context.ki10(), reason="Starting with KiCad 10")
def test_ibom_filtered_not_pcb(test_dir):
    """ Related to #955
        Problems with filtered iBoM and components only in the PCB """
    prj = 'ibom_filtered_not_pcb/repro'
    ctx = context.TestContextSCH(test_dir, prj, 'test_ibom_filtered_not_pcb')
    ctx.run()
    ctx.clean_up(keep_project=True)
