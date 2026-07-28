# -*- coding: utf-8 -*-
"""
Tests of Internal BoM files

- Simple cases for:
  - CSV
  - HTML
  - XML
  - XLSX
- Components units
  - Sort and groups of RLC_sort
- Datasheet as link (HTML and XLSX)
- Digi-Key link (HTML and XLSX)
- Join columns
- ignore_dnf = 0
- html_generate_dnf = 0
- use_alt = 1 (also non contiguous)
- COLUMN_RENAME
  - CSV
  - HTML
  - XML
  - XLSX
- group_connectors = 1/0
- Columns are case insensitive
- component_aliases
- merge_blank_fields
- Don't group components
- Multipart component (not repeated)
- Field collision
- test_regex/exclude_any/include_only
- No XLSX support

Missing:
- number_boards
- XLSX/HTML colors (for real)

KiBoM Variants:
- kibom-variant_2.sch
- kibom-variant_5.sch

IBoM Variants:
- test_int_bom_variant_t2if + kibom-variant_3.sch + int_bom_var_t2i_csv
- test_int_bom_variant_t2is + kibom-variant_3.sch + int_bom_var_t2is_csv
- kibom-variant_4.sch

For debug information use:
pytest-3 --log-cli-level debug

"""

from base64 import b64decode
import logging
import os
import pytest
from . import context
from kibot.misc import EXIT_BAD_CONFIG

BOM_DIR = 'BoM'
REF_COLUMN_NAME = 'References'
REF_COLUMN_NAME_R = 'Referencias'
QTY_COLUMN_NAME = 'Quantity Per PCB'
STATUS_COLUMN_NAME = 'Status'
COMP_COLUMN_NAME = 'Row'
COMP_COLUMN_NAME_R = 'Renglón'
VALUE_COLUMN_NAME = 'Value'
DATASHEET_COLUMN_NAME = 'Datasheet'
SOURCE_BOM_COLUMN_NAME = 'Source BoM'
KIBOM_TEST_HEAD = [COMP_COLUMN_NAME, 'Description', 'Part', REF_COLUMN_NAME, 'Value', 'Footprint', QTY_COLUMN_NAME, 'Status',
                   DATASHEET_COLUMN_NAME, 'Config']
KIBOM_TEST_HEAD_TOL = list(KIBOM_TEST_HEAD)
KIBOM_TEST_HEAD_TOL.insert(-1, 'Tolerance')
KIBOM_RENAME_HEAD = [COMP_COLUMN_NAME_R, REF_COLUMN_NAME_R, 'Componente', 'Valor', 'Código Digi-Key', 'Cantidad por PCB']
CONN_HEAD = [COMP_COLUMN_NAME, 'Description', 'Part', REF_COLUMN_NAME, 'Value', 'Footprint', QTY_COLUMN_NAME, 'Status',
             DATASHEET_COLUMN_NAME]
KIBOM_TEST_COMPONENTS = ['C1', 'C2', 'C3', 'C4', 'R1', 'R2', 'R3', 'R4', 'R5', 'R7', 'R8', 'R9', 'R10']
KIBOM_TEST_COMPONENTS_FIL = ['C1', 'C2', 'C4', 'R1', 'R2', 'R3', 'R4', 'R5', 'R7', 'R8', 'R10']
KIBOM_TEST_COMPONENTS_FIL2 = ['C1', 'C2', 'R1', 'R2', 'R3', 'R4', 'R5', 'R7', 'R8', 'R10']
KIBOM_TEST_COMPONENTS_ALT = ['C1-C4', 'R9', 'R10', 'R7', 'R8', 'R1-R5']
KIBOM_TEST_COMPONENTS_ALT2 = ['C1-C4', 'R9', 'R10', 'R7', 'R8', 'R1', 'R2', 'R4', 'R5', 'R3']
KIBOM_TEST_EXCLUDE = ['R6']
KIBOM_TEST_GROUPS = 5
KIBOM_PRJ_INFO = ['kibom-test', 'default', 'A', '2020-03-12', None]
LINKS_PRJ_INFO = ['links', 'default', 'A', '2020-03-12', None]
KIBOM_STATS = [KIBOM_TEST_GROUPS+len(KIBOM_TEST_EXCLUDE),
               len(KIBOM_TEST_COMPONENTS)+len(KIBOM_TEST_EXCLUDE),
               len(KIBOM_TEST_COMPONENTS),
               1,
               len(KIBOM_TEST_COMPONENTS)]
LINKS_STATS = [3, '4 (2 SMD/ 2 THT)', '3 (1 SMD/ 2 THT)', 1, 3]
VARIANTE_PRJ_INFO = ['kibom-variante', 'default', 'A', '2020-03-12', None]
VARIANTE_PRJ_INFO_10 = ['kicad-variante', 'default', 'A', '2020-03-12', None]
LINK_HEAD = ['References', 'Part', 'Value', 'Quantity Per PCB', 'digikey#', 'digikey_alt#', 'mouser#', 'mouser_alt#', 'LCSC#',
             'manf#']
LINKS_COMPONENTS = ['J1', 'J2', 'R1']
LINKS_EXCLUDE = ['C1']
LINKS_GROUPS = 2
INFO_ROWS = ['Schematic:', 'Variant:', 'Revision:', 'Date:', 'KiCad Version:']
STATS_ROWS = ['Component Groups:', 'Component Count:', 'Fitted Components:', 'Number of PCBs:', 'Total Components:']
DEF_TITLE = 'KiBot Bill of Materials'
MERGED_COMPS = ['A:R1-A:R3', 'A:C1', 'A:C2', 'B:R1', 'B:R2-B:R4', 'B:C1', 'B:C2', 'C:R1-C:R4', 'C:R5']
MERGED_R1_SRC = 'A:(3) B:(3) C:(1)'


def check_kibom_test_netlist(rows, ref_column, groups, exclude, comps, ref_sep=' ', vals=None, val_column=None):
    """ Checks the kibom-test.sch expected results """
    # Groups
    assert len(rows) == groups, "Number of groups"
    logging.debug(str(groups) + " groups OK")
    # Components
    if comps:
        components = []
        comp_vals = {}
        for r in rows:
            components.extend(r[ref_column].split(ref_sep))
            if val_column:
                comp_vals[r[ref_column]] = r[val_column]
        assert len(components) == len(comps)
        logging.debug(str(len(comps)) + " components OK")
    # Excluded
    if exclude:
        for ex in exclude:
            assert ex not in components
        logging.debug(str(len(exclude)) + " not fitted OK")
    # All the other components
    if comps:
        for c in comps:
            assert c in components
        logging.debug("list of components OK")
    # Check values
    if vals:
        for r, v in vals.items():
            assert r in comp_vals
            assert v == comp_vals[r]
        logging.debug("component values OK")


def check_dnc(rows, comp, ref, status, datasheet=None):
    for row in rows:
        if row[ref].find(comp) != -1:
            assert '(DNC)' in row[status]
            logging.debug(comp + " is DNC OK")
            if datasheet is not None:
                assert row[datasheet].startswith('<a href="')
                logging.debug(comp + " datasheet link OK")
            return


def check_source(rows, comp, ref, src, val):
    for row in rows:
        if row[ref].find(comp) != -1:
            assert row[src] == val
            logging.debug(comp+" is from '"+val+"' OK")
            return


def check_path(rows, comp, ref, sp, val):
    for row in rows:
        if row[ref].find(comp) != -1:
            assert row[sp] == val
            logging.debug(comp + " sheetpath OK")
            return


def check_head_xlsx(r, info, stats, title=DEF_TITLE, extra_info=None):
    rn = 0
    if title:
        # First row is just the title
        assert r[rn][0] == title
        rn += 1
        logging.debug('Title Ok')
    if extra_info:
        for e in extra_info:
            assert r[rn][0] == e
            rn += 1
            logging.debug('Extra `{}` Ok'.format(e))
    if info:
        info_col = 0
        for i, txt in enumerate(info):
            assert r[rn+i][info_col] == INFO_ROWS[i]
            if txt:
                assert r[rn+i][info_col+1] == txt
        logging.debug('Info block Ok')
    if stats:
        stats_col = 0
        if info:
            stats_col += 2
        for i, txt in enumerate(stats):
            assert r[rn+i][stats_col] == STATS_ROWS[i]
            assert r[rn+i][stats_col+1] == txt, 'index: {} title: {}'.format(i, STATS_ROWS[i])
        logging.debug('Stats block Ok')


def check_head_html(r, info, stats, title, logo, extra_info):
    if title:
        assert 'title' in r
        assert r['title'] == title
        logging.debug('Title Ok')
    else:
        assert 'title' not in r
        logging.debug('No title Ok')
    if logo:
        assert 'logo' in r
        logging.debug('Logo Ok')
    else:
        assert 'logo' not in r
        logging.debug('No logo Ok')
    if extra_info:
        assert 'extra_info' in r
        extra = r['extra_info']
        for i, val in enumerate(extra_info):
            assert extra[i] == val
        logging.debug('Extra info Ok')
    else:
        assert 'extra_info' not in r
        logging.debug('No extra info Ok')
    if info:
        assert 'info' in r
        for i, tit in enumerate(INFO_ROWS):
            if info[i] is None:
                continue
            key = 'info_'+tit[:-1]
            assert key in r
            assert info[i] == r[key]
        logging.debug('Info block Ok')
    else:
        assert 'info' not in r
        logging.debug('No info block Ok')
    if stats:
        assert 'stats' in r
        for i, tit in enumerate(STATS_ROWS):
            if stats[i] is None:
                continue
            key = 'stats_'+tit[:-1]
            assert key in r
            assert stats[i] == r[key]
        logging.debug('Stats block Ok')
    else:
        assert 'stats' not in r
        logging.debug('No stats block Ok')


def check_csv_info(r, info, stats):
    row = 0
    if info:
        assert r[row][0] == 'Project info:'
        for i, tit in enumerate(INFO_ROWS):
            row += 1
            assert r[row][0] == tit
            if info[i] is not None:
                assert r[row][1] == info[i]
        logging.debug('Info block Ok')
        row += 1
    if stats:
        assert r[row][0] == 'Statistics:'
        for i, tit in enumerate(STATS_ROWS):
            row += 1
            assert r[row][0] == tit
            if stats[i] is not None:
                assert r[row][1] == str(stats[i])
        logging.debug('Stats block Ok')
        row += 1
    assert row == len(r)


def kibom_verif(rows, header, skip_head=False, qty_name=STATUS_COLUMN_NAME, ref_sep=' '):
    if not skip_head:
        assert header == KIBOM_TEST_HEAD
    ref_column = header.index(REF_COLUMN_NAME)
    status_column = header.index(qty_name)
    check_kibom_test_netlist(rows, ref_column, KIBOM_TEST_GROUPS, KIBOM_TEST_EXCLUDE, KIBOM_TEST_COMPONENTS, ref_sep)
    check_dnc(rows, 'R7', ref_column, status_column)


def kibom_setup(test_dir, test, ext='csv'):
    prj = 'kibom-test'
    ctx = context.TestContextSCH(test_dir, prj, test, BOM_DIR, test_name=test)
    ctx.run()
    out = prj+'-bom.'+ext
    return ctx, out


def test_int_bom_simple_csv(test_dir):
    ctx, out = kibom_setup(test_dir, 'int_bom_simple_csv')
    rows, header, info = ctx.load_csv(out)
    check_csv_info(info, KIBOM_PRJ_INFO, KIBOM_STATS)
    kibom_verif(rows, header)
    # Check not quoted and comma as delimiter
    ctx.search_in_file_d(out, [KIBOM_TEST_HEAD[0]+','+KIBOM_TEST_HEAD[1]])
    ctx.clean_up()


def test_int_bom_simple_hrtxt(test_dir):
    ctx, out = kibom_setup(test_dir, 'int_bom_simple_hrtxt', ext='txt')
    ctx.expect_out_file(out, sub=True)
    rows, header, info = ctx.load_hrtxt(out)
    check_csv_info(info, KIBOM_PRJ_INFO, KIBOM_STATS)
    kibom_verif(rows, header)
    ctx.clean_up()


def test_int_bom_csv_no_info(test_dir):
    """ No PCB info """
    ctx, out = kibom_setup(test_dir, 'int_bom_csv_no_info')
    rows, header, info = ctx.load_csv(out)
    check_csv_info(info, None, KIBOM_STATS)
    kibom_verif(rows, header)
    # Check not quoted and comma as delimiter
    ctx.search_in_file_d(out, [KIBOM_TEST_HEAD[0]+','+KIBOM_TEST_HEAD[1]])
    ctx.clean_up()


def test_int_bom_csv_no_stats(test_dir):
    """ No Stats """
    ctx, out = kibom_setup(test_dir, 'int_bom_csv_no_stats')
    rows, header, info = ctx.load_csv(out)
    check_csv_info(info, KIBOM_PRJ_INFO, None)
    kibom_verif(rows, header)
    # Check not quoted and comma as delimiter
    ctx.search_in_file_d(out, [KIBOM_TEST_HEAD[0]+','+KIBOM_TEST_HEAD[1]])
    ctx.clean_up()


def test_int_bom_csv_no_extra(test_dir):
    """ No Stats, no info """
    ctx, out = kibom_setup(test_dir, 'int_bom_csv_no_extra')
    rows, header, info = ctx.load_csv(out)
    assert len(info) == 0
    kibom_verif(rows, header)
    # Check not quoted and comma as delimiter
    ctx.search_in_file_d(out, [KIBOM_TEST_HEAD[0]+','+KIBOM_TEST_HEAD[1]])
    ctx.clean_up()


def test_int_bom_simple_txt(test_dir):
    ctx, out = kibom_setup(test_dir, 'int_bom_simple_txt', 'txt')
    rows, header, info = ctx.load_csv(out, delimiter='\t')
    kibom_verif(rows, header)
    check_csv_info(info, KIBOM_PRJ_INFO, KIBOM_STATS)
    # Check all quoted and tab as delimiter
    ctx.search_in_file_d(out, ['"'+KIBOM_TEST_HEAD[0]+'"\t"'+KIBOM_TEST_HEAD[1]+'"'])
    ctx.clean_up()


def simple_html_test(ctx, rows, headers, sh_head, prj, do_title=True, do_logo=True, do_info=True, do_stats=True,
                     a_title=DEF_TITLE, extra_info=None):
    title = a_title if do_title else None
    info = KIBOM_PRJ_INFO if do_info else None
    stats = None
    if do_stats:
        stats = KIBOM_STATS
    check_head_html(sh_head, info, stats, title=title, logo=do_logo, extra_info=extra_info)
    # Test we got the normal and DNF tables
    assert len(rows) == 2
    assert len(headers) == 2
    # Test both tables has the same headings and they are the expected
    assert headers[0] == headers[1]
    assert headers[0] == KIBOM_TEST_HEAD
    # Look for reference and quantity columns
    ref_column = headers[0].index(REF_COLUMN_NAME)
    status_column = headers[0].index(STATUS_COLUMN_NAME)
    ds_column = headers[0].index(DATASHEET_COLUMN_NAME)
    # Check the normal table
    check_kibom_test_netlist(rows[0], ref_column, KIBOM_TEST_GROUPS, KIBOM_TEST_EXCLUDE, KIBOM_TEST_COMPONENTS)
    check_dnc(rows[0], 'R7', ref_column, status_column, ds_column)
    # Check the DNF table
    check_kibom_test_netlist(rows[1], ref_column, 1, KIBOM_TEST_COMPONENTS, KIBOM_TEST_EXCLUDE)
    ctx.clean_up()


def simple_html_setup(test_dir, name, ret_val=0, get_out=False):
    prj = 'kibom-test'
    ext = 'html'
    ctx = context.TestContextSCH(test_dir, prj, name, BOM_DIR, test_name=name)
    ctx.run(ret_val)
    out = prj + '-bom.' + ext
    if ret_val == 0 and not get_out:
        return ctx.load_html(out), prj, ctx
    else:
        return (out, None, None), prj, ctx


def test_int_bom_simple_html_1(test_dir):
    (rows, headers, sh_head), prj, ctx = simple_html_setup(test_dir, 'int_bom_simple_html_1')
    simple_html_test(ctx, rows, headers, sh_head, prj, extra_info=['Extra 1: '+prj, 'Extra 2: 2020-03-12'])


def test_int_bom_simple_html_2(test_dir):
    """ No title """
    (rows, headers, sh_head), prj, ctx = simple_html_setup(test_dir, 'int_bom_simple_html_2')
    simple_html_test(ctx, rows, headers, sh_head, prj, do_title=False)


def test_int_bom_simple_html_3(test_dir):
    """ No logo """
    (rows, headers, sh_head), prj, ctx = simple_html_setup(test_dir, 'int_bom_simple_html_3')
    simple_html_test(ctx, rows, headers, sh_head, prj, do_logo=False, a_title=prj+' BOM')


def test_int_bom_simple_html_4(test_dir):
    """ No title, no logo """
    (rows, headers, sh_head), prj, ctx = simple_html_setup(test_dir, 'int_bom_simple_html_4')
    simple_html_test(ctx, rows, headers, sh_head, prj, do_title=False, do_logo=False)


def test_int_bom_simple_html_5(test_dir):
    """ No title, no logo, no info """
    (rows, headers, sh_head), prj, ctx = simple_html_setup(test_dir, 'int_bom_simple_html_5')
    simple_html_test(ctx, rows, headers, sh_head, prj, do_title=False, do_logo=False, do_info=False)


def test_int_bom_simple_html_6(test_dir):
    """ No title, no logo, no info, no stats """
    (rows, headers, sh_head), prj, ctx = simple_html_setup(test_dir, 'int_bom_simple_html_6')
    simple_html_test(ctx, rows, headers, sh_head, prj, do_title=False, do_logo=False, do_info=False, do_stats=False)


def test_int_bom_simple_html_7(test_dir):
    """ No title, bogus logo, no info, no stats """
    (rows, headers, sh_head), prj, ctx = simple_html_setup(test_dir, 'int_bom_simple_html_7', EXIT_BAD_CONFIG)
    ctx.search_err(r'Missing logo file')


def test_int_bom_simple_html_8(test_dir):
    """ No title, custom logo, no info, no stats """
    (rows, headers, sh_head), prj, ctx = simple_html_setup(test_dir, 'int_bom_simple_html_8')
    simple_html_test(ctx, rows, headers, sh_head, prj, do_title=False, do_logo=True, do_info=False, do_stats=False)
    logo = sh_head['logo']
    assert logo.startswith('data:image/png;base64,')
    image = b64decode(logo[22:])
    with open('docs/images/Ki.png', 'rb') as f:
        ref = f.read()
    assert image == ref
    logging.debug('Image content OK')


def test_int_bom_simple_html_9(test_dir):
    """ No title, no logo, no info, no stats, custom style """
    (rows, headers, sh_head), prj, ctx = simple_html_setup(test_dir, 'int_bom_simple_html_9')
    style = ctx.load_html_style('kibom-test-bom.html')
    with open('tests/data/html_style.css', 'rt') as f:
        ref = f.read()
    assert style[1:] == ref
    simple_html_test(ctx, rows, headers, sh_head, prj, do_title=False, do_logo=False, do_info=False, do_stats=False)


def test_int_bom_simple_html_colored_rows(test_dir):
    (outf, r1, r2), prj, ctx = simple_html_setup(test_dir, 'int_bom_simple_html_colored_rows', get_out=True)
    ctx.search_in_file(outf, ['Color reference for rows'], sub=True)


def adapt_xml(h):
    h = h.replace(' ', '_')
    h = h.replace('"', '')
    h = h.replace("'", '')
    h = h.replace('#', '_num')
    return h


def test_int_bom_simple_xml(test_dir):
    ctx, out = kibom_setup(test_dir, 'int_bom_simple_xml', 'xml')
    rows, header = ctx.load_xml(out)
    # Columns get sorted by name, so we need to take care of it
    for c in KIBOM_TEST_HEAD:
        assert adapt_xml(c) in header, "Missing column "+c
    kibom_verif(rows, header, skip_head=True, qty_name=adapt_xml(STATUS_COLUMN_NAME))
    ctx.clean_up()


def test_int_bom_simple_json(test_dir):
    ctx, out = kibom_setup(test_dir, 'int_bom_simple_json', 'json')
    ctx.clean_up()


def simple_xlsx_verify(ctx, prj, dnf=True, title=DEF_TITLE, extra_info=None):
    ext = 'xlsx'
    ctx.run()
    out = prj + '-bom.' + ext
    rows, header, sh_head = ctx.load_xlsx(out)
    check_head_xlsx(sh_head, KIBOM_PRJ_INFO, KIBOM_STATS, title=title, extra_info=extra_info)
    assert header == KIBOM_TEST_HEAD
    ref_column = header.index(REF_COLUMN_NAME)
    status_column = header.index(STATUS_COLUMN_NAME)
    check_kibom_test_netlist(rows, ref_column, KIBOM_TEST_GROUPS, KIBOM_TEST_EXCLUDE, KIBOM_TEST_COMPONENTS)
    check_dnc(rows, 'R7', ref_column, status_column)
    rows, header, sh_head = ctx.load_xlsx(out, 2)
    if dnf:
        check_kibom_test_netlist(rows, ref_column, 1, [], KIBOM_TEST_EXCLUDE)
    else:
        assert rows is None
    ctx.clean_up()


def test_int_bom_simple_xlsx_1(test_dir):
    prj = 'kibom-test'
    ctx = context.TestContextSCH(test_dir, prj, 'int_bom_simple_xlsx', BOM_DIR)
    simple_xlsx_verify(ctx, prj, extra_info=['Extra 1: '+prj, 'Extra 2: 2020-03-12'])


def get_column(rows, col, split=True):
    components = []
    for r in rows:
        if split:
            components.extend(r[col].split())
        else:
            components.append(r[col])
    return components


def int_bom_sort(test_dir, locale, dp):
    prj = 'RLC_sort'
    ext = 'csv'
    ctx = context.TestContextSCH(test_dir, prj, 'int_bom_sort_1', BOM_DIR, test_name='int_bom_sort_'+locale)
    ctx.run(do_locale=locale)
    out = prj + '-bom.' + ext
    rows, header, info = ctx.load_csv(out)
    ref_column = header.index(REF_COLUMN_NAME)
    exp = ['C5', 'C6', 'C7', 'C8', 'C9', 'C10', 'C1', 'C2', 'C3', 'C4', 'C11', 'C12',
           'L2', 'L1', 'L3',
           'R5', 'R16', 'R12', 'R4', 'R13', 'R9', 'R10', 'R3']
    if dp == ',':
        exp += ['R2', 'R1', 'R8']
    else:
        # 8,2 k is interpreted as 82 k
        exp += ['R1', 'R2', 'R8']
    exp += ['R7', 'R11', 'R14', 'R15']
    check_kibom_test_netlist(rows, ref_column, 23, None, exp)
    # Check the sorting
    assert get_column(rows, ref_column) == exp
    # Check normalization
    vals_column = header.index('Value')
    for r in rows:
        if 'C7' in r[ref_column]:
            assert r[vals_column] == '3'+dp+'3 pF'
            logging.debug('C7 == 3'+dp+'3 pF OK')
            break
    ctx.search_err(r'Malformed value: .?10Q.?')
    ctx.search_err(r'Malformed value: .?\.G.?')
    ctx.search_err(r'Malformed value: .?2\.2k2.?')
    ctx.clean_up()


def test_int_bom_sort_1(test_dir):
    int_bom_sort(test_dir, 'es_AR.UTF-8', ',')


def test_int_bom_sort_2(test_dir):
    int_bom_sort(test_dir, 'en_US.UTF-8', '.')


def test_int_bom_sort_3(test_dir):
    int_bom_sort(test_dir, 'xx_XX.UTF-8', '.')


def test_int_bom_datasheet_link(test_dir):
    prj = 'links'
    ext = 'html'
    ctx = context.TestContextSCH(test_dir, prj, 'int_bom_datasheet_link', BOM_DIR)
    ctx.run()
    out = prj + '.' + ext
    rows, headers, sh_head = ctx.load_html(out)
    # Test we got the normal and DNF tables
    assert len(rows) == 2
    assert len(headers) == 2
    # Test both tables has the same headings and they are the expected
    assert headers[0] == headers[1]
    assert headers[0] == LINK_HEAD
    # Look for reference and quantity columns
    ref_column = headers[0].index(REF_COLUMN_NAME)
    part_column = headers[0].index('Part')
    # Check the normal table
    check_kibom_test_netlist(rows[0], ref_column, LINKS_GROUPS, LINKS_EXCLUDE, LINKS_COMPONENTS)
    # Check the DNF table
    check_kibom_test_netlist(rows[1], ref_column, 1, LINKS_COMPONENTS, LINKS_EXCLUDE)
    # Check the datasheet link
    parts = get_column(rows[0]+rows[1], part_column, False)
    for c in parts:
        assert c.strip().startswith('<a href')
        assert 'pdf' in c
        logging.debug(c + ' OK')
    ctx.clean_up()


def test_int_bom_digikey_link_1(test_dir):
    prj = 'links'
    ext = 'html'
    ctx = context.TestContextSCH(test_dir, prj, 'int_bom_digikey_link', BOM_DIR)
    ctx.run()
    out = prj + '.' + ext
    rows, headers, sh_head = ctx.load_html(out)
    # Test we got the normal and DNF tables
    assert len(rows) == 2
    assert len(headers) == 2
    # Test both tables has the same headings and they are the expected
    assert headers[0] == headers[1]
    assert headers[0] == LINK_HEAD
    # Look for reference and quantity columns
    ref_column = headers[0].index(REF_COLUMN_NAME)
    dk_column = headers[0].index('digikey#')
    mo_column = headers[0].index('mouser#')
    lcsc_column = headers[0].index('LCSC#')
    # Check the normal table
    check_kibom_test_netlist(rows[0], ref_column, LINKS_GROUPS, LINKS_EXCLUDE, LINKS_COMPONENTS)
    # Check the DNF table
    check_kibom_test_netlist(rows[1], ref_column, 1, LINKS_COMPONENTS, LINKS_EXCLUDE)
    # Check the digikey link
    parts = get_column(rows[0]+rows[1], dk_column, False)
    for c in parts:
        assert c.strip().startswith('<a href')
        assert 'digikey' in c
        logging.debug(c + ' OK')
    parts = get_column(rows[0]+rows[1], mo_column, False)
    for c in parts:
        assert c.strip().startswith('<a href')
        assert 'mouser' in c
        logging.debug(c + ' OK')
    parts = get_column(rows[0]+rows[1], lcsc_column, False)
    for c in parts:
        assert c.strip().startswith('<a href'), c
        assert 'lcsc.com' in c
        logging.debug(c + ' OK')
    ctx.clean_up()


def test_int_bom_digikey_links(test_dir):
    prj = 'links'
    ext = 'html'
    ctx = context.TestContextSCH(test_dir, prj, 'int_bom_digikey_links', BOM_DIR)
    ctx.run()
    out = prj + '.' + ext
    rows, headers, sh_head = ctx.load_html(out)
    # Test we got the normal and DNF tables
    assert len(rows) == 2
    assert len(headers) == 2
    # Test both tables has the same headings and they are the expected
    assert headers[0] == headers[1]
    assert headers[0] == LINK_HEAD
    # Look for reference and quantity columns
    ref_column = headers[0].index(REF_COLUMN_NAME)
    dk_column = headers[0].index('digikey#')
    dk2_column = headers[0].index('digikey_alt#')
    mo_column = headers[0].index('mouser#')
    mo2_column = headers[0].index('mouser_alt#')
    # Check the normal table
    check_kibom_test_netlist(rows[0], ref_column, LINKS_GROUPS, LINKS_EXCLUDE, LINKS_COMPONENTS)
    # Check the DNF table
    check_kibom_test_netlist(rows[1], ref_column, 1, LINKS_COMPONENTS, LINKS_EXCLUDE)
    # Check the digikey link
    parts = get_column(rows[0]+rows[1], dk_column, False)
    for c in parts:
        assert c.strip().startswith('<a href')
        assert 'digikey' in c
        logging.debug(c + ' OK')
    parts = get_column(rows[0]+rows[1], dk2_column, False)
    for c in parts:
        assert c.strip().startswith('<a href')
        assert 'digikey' in c
        logging.debug(c + ' OK')
    parts = get_column(rows[0]+rows[1], mo_column, False)
    for c in parts:
        assert c.strip().startswith('<a href')
        assert 'mouser' in c
        logging.debug(c + ' OK')
    parts = get_column(rows[0]+rows[1], mo2_column, False)
    for c in parts:
        assert c.strip().startswith('<a href')
        assert 'mouser' in c
        logging.debug(c + ' OK')
    ctx.clean_up()


def test_int_bom_join_1(test_dir):
    prj = 'join'
    ext = 'csv'
    ctx = context.TestContextSCH(test_dir, prj, 'int_bom_join_1', BOM_DIR)
    ctx.run()
    out = prj + '-bom.' + ext
    rows, header, info = ctx.load_csv(out)
    assert header == [COMP_COLUMN_NAME, REF_COLUMN_NAME, 'Part', 'Value', 'manf', 'digikey#', QTY_COLUMN_NAME]
    ref_column = header.index(REF_COLUMN_NAME)
    manf_column = header.index('manf')
    value_column = header.index('Value')
    check_kibom_test_netlist(rows, ref_column, LINKS_GROUPS+1, [], LINKS_EXCLUDE+LINKS_COMPONENTS)
    assert rows[0][ref_column] == 'C1'
    assert rows[0][value_column] == '1nF 10% 50V'
    assert rows[0][manf_column] == 'KEMET C0805C102K5RACTU'
    assert rows[1][ref_column] == 'J1 J2'
    assert rows[1][value_column] == 'Molex KK'
    assert rows[1][manf_column] == 'Molex 0022232021'
    assert rows[2][ref_column] == 'R1'
    assert rows[2][value_column] == '1k 5%'
    assert rows[2][manf_column] == 'Bourns CR0805-JW-102ELF'
    ctx.clean_up()


def test_int_bom_join_2(test_dir):
    prj = 'join'
    ext = 'csv'
    ctx = context.TestContextSCH(test_dir, prj, 'int_bom_join_2', BOM_DIR)
    ctx.run()
    out = prj + '-bom.' + ext
    rows, header, info = ctx.load_csv(out)
    assert header == [COMP_COLUMN_NAME, REF_COLUMN_NAME, 'Part', 'Value', 'manf', 'digikey#', QTY_COLUMN_NAME]
    ref_column = header.index(REF_COLUMN_NAME)
    manf_column = header.index('manf')
    value_column = header.index('Value')
    check_kibom_test_netlist(rows, ref_column, LINKS_GROUPS+1, [], LINKS_EXCLUDE+LINKS_COMPONENTS)
    assert rows[0][ref_column] == 'C1'
    assert rows[0][value_column] == '1nF 10% - (50V)\nAlternative'
    assert rows[0][manf_column] == 'KEMET C0805C102K5RACTU'
    assert rows[1][ref_column] == 'J1 J2'
    assert rows[1][value_column] == 'Molex KK -'
    assert rows[1][manf_column] == 'Molex 0022232021'
    assert rows[2][ref_column] == 'R1'
    assert rows[2][value_column] == '1k 5% -'
    assert rows[2][manf_column] == 'Bourns CR0805-JW-102ELF'
    ctx.clean_up()


def test_int_include_dnf(test_dir):
    """ ignore_dnf: false """
    prj = 'kibom-test'
    ext = 'csv'
    ctx = context.TestContextSCH(test_dir, prj, 'int_bom_include_dnf', BOM_DIR)
    ctx.run()
    out = prj + '-bom.' + ext
    rows, header, info = ctx.load_csv(out)
    assert header == KIBOM_TEST_HEAD
    ref_column = header.index(REF_COLUMN_NAME)
    status_column = header.index(STATUS_COLUMN_NAME)
    check_kibom_test_netlist(rows, ref_column, KIBOM_TEST_GROUPS+1, [], KIBOM_TEST_COMPONENTS+KIBOM_TEST_EXCLUDE)
    check_dnc(rows, 'R7', ref_column, status_column)
    ctx.clean_up()


def test_int_bom_html_generate_dnf(test_dir):
    """ html_generate_dnf: false """
    prj = 'kibom-test'
    ext = 'html'
    ctx = context.TestContextSCH(test_dir, prj, 'int_bom_html_generate_dnf', BOM_DIR)
    ctx.run()
    out = prj + '-bom.' + ext
    rows, headers, sh_head = ctx.load_html(out)
    logging.debug(rows)
    # Test we got the normal and DNF tables
    assert len(rows) == 1
    assert len(headers) == 1
    assert headers[0] == KIBOM_TEST_HEAD
    # Look for reference and quantity columns
    ref_column = headers[0].index(REF_COLUMN_NAME)
    status_column = headers[0].index(STATUS_COLUMN_NAME)
    check_kibom_test_netlist(rows[0], ref_column, KIBOM_TEST_GROUPS, KIBOM_TEST_EXCLUDE, KIBOM_TEST_COMPONENTS)
    check_dnc(rows[0], 'R7', ref_column, status_column)
    ctx.clean_up()


def test_int_bom_use_alt_1(test_dir):
    """ use_alt: true """
    prj = 'kibom-test'
    ext = 'csv'
    ctx = context.TestContextSCH(test_dir, prj, 'int_bom_use_alt', BOM_DIR)
    ctx.run()
    out = prj + '-bom.' + ext
    rows, header, info = ctx.load_csv(out)
    assert header == KIBOM_TEST_HEAD
    ref_column = header.index(REF_COLUMN_NAME)
    status_column = header.index(STATUS_COLUMN_NAME)
    check_kibom_test_netlist(rows, ref_column, KIBOM_TEST_GROUPS, KIBOM_TEST_EXCLUDE, KIBOM_TEST_COMPONENTS_ALT)
    check_dnc(rows, 'R7', ref_column, status_column)
    ctx.clean_up()


@pytest.mark.skipif(context.ki5(), reason="needs KiCad 6 sch attributes")
def test_int_bom_marked_1(test_dir):
    """ Components marked as `Exclude from bill of materials` """
    prj = 'kibom-test-marked'
    ext = 'csv'
    ctx = context.TestContextSCH(test_dir, prj, 'int_bom_simple_csv', BOM_DIR)
    ctx.run()
    out = prj + '-bom.' + ext
    rows, header, info = ctx.load_csv(out)
    assert header == KIBOM_TEST_HEAD
    ref_column = header.index(REF_COLUMN_NAME)
    status_column = header.index(STATUS_COLUMN_NAME)
    check_kibom_test_netlist(rows, ref_column, KIBOM_TEST_GROUPS, KIBOM_TEST_EXCLUDE, KIBOM_TEST_COMPONENTS_FIL)
    check_dnc(rows, 'R7', ref_column, status_column)
    ctx.clean_up()


@pytest.mark.skipif(context.ki5(), reason="needs KiCad 6 PCB attributes")
def test_int_bom_marked_2(test_dir):
    """ Components marked as `Exclude from bill of materials`, also PCB """
    prj = 'kibom-test-marked'
    ext = 'csv'
    ctx = context.TestContextSCH(test_dir, prj, 'int_bom_simple_csv_npcb', BOM_DIR)
    ctx.run()
    out = prj + '-bom.' + ext
    rows, header, info = ctx.load_csv(out)
    assert header == KIBOM_TEST_HEAD
    ref_column = header.index(REF_COLUMN_NAME)
    status_column = header.index(STATUS_COLUMN_NAME)
    check_kibom_test_netlist(rows, ref_column, KIBOM_TEST_GROUPS, KIBOM_TEST_EXCLUDE, KIBOM_TEST_COMPONENTS_FIL2)
    check_dnc(rows, 'R7', ref_column, status_column)
    ctx.clean_up()


def test_int_bom_use_alt_2(test_dir):
    """ use_alt: true and not merge blank fields, non contiguous """
    prj = 'kibom-test-2'
    ext = 'csv'
    ctx = context.TestContextSCH(test_dir, prj, 'int_bom_use_alt_2', BOM_DIR)
    ctx.run()
    out = prj + '-bom.' + ext
    rows, header, info = ctx.load_csv(out)
    assert header == KIBOM_TEST_HEAD
    ref_column = header.index(REF_COLUMN_NAME)
    status_column = header.index(STATUS_COLUMN_NAME)
    # R3 without footprint won't be merged with other 10K resistors
    check_kibom_test_netlist(rows, ref_column, KIBOM_TEST_GROUPS+1, KIBOM_TEST_EXCLUDE, KIBOM_TEST_COMPONENTS_ALT2,
                             ref_sep=';')
    check_dnc(rows, 'R7', ref_column, status_column)
    ctx.clean_up()


def test_int_bom_no_number_rows(test_dir):
    """ Was number_rows: false, now is different """
    prj = 'kibom-test'
    ext = 'csv'
    ctx = context.TestContextSCH(test_dir, prj, 'int_bom_no_number_rows', BOM_DIR)
    ctx.run()
    out = prj + '-bom.' + ext
    rows, header, info = ctx.load_csv(out)
    assert header == KIBOM_TEST_HEAD[1:]
    ref_column = header.index(REF_COLUMN_NAME)
    status_column = header.index(STATUS_COLUMN_NAME)
    check_kibom_test_netlist(rows, ref_column, KIBOM_TEST_GROUPS, KIBOM_TEST_EXCLUDE, KIBOM_TEST_COMPONENTS)
    check_dnc(rows, 'R7', ref_column, status_column)
    ctx.clean_up()


def test_int_bom_column_rename_csv(test_dir):
    prj = 'links'
    ext = 'csv'
    ctx = context.TestContextSCH(test_dir, prj, 'int_bom_column_rename_csv', BOM_DIR)
    ctx.run()
    out = prj + '-bom.' + ext
    rows, header, info = ctx.load_csv(out)
    assert header == KIBOM_RENAME_HEAD
    ref_column = header.index(REF_COLUMN_NAME_R)
    check_kibom_test_netlist(rows, ref_column, LINKS_GROUPS, LINKS_EXCLUDE, LINKS_COMPONENTS)
    ctx.clean_up()


def test_int_bom_column_rename_html(test_dir):
    prj = 'links'
    ext = 'html'
    ctx = context.TestContextSCH(test_dir, prj, 'int_bom_column_rename_html', BOM_DIR)
    ctx.run()
    out = prj + '-bom.' + ext
    rows, headers, sh_head = ctx.load_html(out)
    assert headers[0] == KIBOM_RENAME_HEAD
    ref_column = headers[0].index(REF_COLUMN_NAME_R)
    check_kibom_test_netlist(rows[0], ref_column, LINKS_GROUPS, LINKS_EXCLUDE, LINKS_COMPONENTS)
    ctx.clean_up()


def test_int_bom_column_rename_xml(test_dir):
    prj = 'links'
    ext = 'xml'
    ctx = context.TestContextSCH(test_dir, prj, 'int_bom_column_rename_xml', BOM_DIR)
    ctx.run()
    out = prj + '-bom.' + ext
    rows, header = ctx.load_xml(out)
    # Columns get sorted by name, so we need to take care of it
    for c in KIBOM_RENAME_HEAD:
        assert adapt_xml(c) in header, "Missing column "+c
    ref_column = header.index(REF_COLUMN_NAME_R)
    check_kibom_test_netlist(rows, ref_column, LINKS_GROUPS, LINKS_EXCLUDE, LINKS_COMPONENTS)
    ctx.clean_up()


def test_int_bom_column_rename_xlsx(test_dir):
    prj = 'links'
    ext = 'xlsx'
    ctx = context.TestContextSCH(test_dir, prj, 'int_bom_column_rename_xlsx', BOM_DIR)
    ctx.run()
    out = prj + '-bom.' + ext
    rows, header, sh_head = ctx.load_xlsx(out)
    assert header == KIBOM_RENAME_HEAD
    ref_column = header.index(REF_COLUMN_NAME_R)
    check_kibom_test_netlist(rows, ref_column, LINKS_GROUPS, LINKS_EXCLUDE, LINKS_COMPONENTS)
    check_head_xlsx(sh_head, LINKS_PRJ_INFO, LINKS_STATS)
    ctx.clean_up()


def test_int_bom_group_connectors(test_dir):
    """ Default behavior, ignore the 'Value' for connectors """
    prj = 'connectors'
    ext = 'csv'
    ctx = context.TestContextSCH(test_dir, prj, 'int_bom_simple_csv', BOM_DIR)
    ctx.run()
    out = prj + '-bom.' + ext
    rows, header, info = ctx.load_csv(out)
    assert header == CONN_HEAD
    ref_column = header.index(REF_COLUMN_NAME)
    check_kibom_test_netlist(rows, ref_column, 2, [], ['J4', 'J1', 'J3', 'J2'])
    ctx.clean_up()


def test_int_bom_no_group_connectors(test_dir):
    """ group_connectors: false """
    prj = 'connectors'
    ext = 'csv'
    ctx = context.TestContextSCH(test_dir, prj, 'int_bom_no_group_connectors', BOM_DIR)
    ctx.run()
    out = prj + '-bom.' + ext
    rows, header, info = ctx.load_csv(out)
    assert header == CONN_HEAD
    ref_column = header.index(REF_COLUMN_NAME)
    check_kibom_test_netlist(rows, ref_column, 4, [], ['J4', 'J1', 'J3', 'J2'])
    ctx.clean_up()


def test_int_bom_column_sensitive(test_dir):
    """ Test if the columns list can contain columns in lowercase """
    prj = 'links'
    ext = 'csv'
    ctx = context.TestContextSCH(test_dir, prj, 'int_bom_column_sensitive', BOM_DIR)
    ctx.run()
    out = prj + '-bom.' + ext
    rows, header, info = ctx.load_csv(out)
    assert header == [REF_COLUMN_NAME.lower(), 'value', 'part', 'description']
    ref_column = header.index(REF_COLUMN_NAME.lower())
    check_kibom_test_netlist(rows, ref_column, LINKS_GROUPS, LINKS_EXCLUDE, LINKS_COMPONENTS)
    ctx.clean_up()


def test_int_bom_alias_csv(test_dir):
    """ Component aliases and merge blank fields """
    prj = 'kibom-test-2'
    ext = 'csv'
    ctx = context.TestContextSCH(test_dir, prj, 'int_bom_alias_csv', BOM_DIR)
    ctx.run()
    out = prj + '-bom.' + ext
    rows, header, info = ctx.load_csv(out)
    assert header == KIBOM_TEST_HEAD
    ref_column = header.index(REF_COLUMN_NAME)
    status_column = header.index(STATUS_COLUMN_NAME)
    check_kibom_test_netlist(rows, ref_column, KIBOM_TEST_GROUPS, KIBOM_TEST_EXCLUDE, KIBOM_TEST_COMPONENTS)
    check_dnc(rows, 'R7', ref_column, status_column)
    ctx.clean_up()


def test_int_bom_alias_nm_csv(test_dir):
    """ Component aliases and not merge blank fields """
    prj = 'kibom-test-2'
    ext = 'csv'
    ctx = context.TestContextSCH(test_dir, prj, 'int_bom_alias_nm_csv', BOM_DIR)
    ctx.run()
    out = prj + '-bom.' + ext
    rows, header, info = ctx.load_csv(out)
    assert header == KIBOM_TEST_HEAD
    ref_column = header.index(REF_COLUMN_NAME)
    status_column = header.index(STATUS_COLUMN_NAME)
    # R3 without footprint won't be merged with other 10K resistors
    check_kibom_test_netlist(rows, ref_column, KIBOM_TEST_GROUPS+1, KIBOM_TEST_EXCLUDE, KIBOM_TEST_COMPONENTS)
    check_dnc(rows, 'R7', ref_column, status_column)
    ctx.clean_up()


def test_int_bom_no_group_csv(test_dir):
    """ Don't group components """
    prj = 'kibom-test'
    ext = 'csv'
    ctx = context.TestContextSCH(test_dir, prj, 'int_bom_no_group_csv', BOM_DIR)
    ctx.run()
    out = prj + '-bom.' + ext
    rows, header, info = ctx.load_csv(out)
    assert header == KIBOM_TEST_HEAD
    ref_column = header.index(REF_COLUMN_NAME)
    status_column = header.index(STATUS_COLUMN_NAME)
    # R3 without footprint won't be merged with other 10K resistors
    check_kibom_test_netlist(rows, ref_column, len(KIBOM_TEST_COMPONENTS), KIBOM_TEST_EXCLUDE, KIBOM_TEST_COMPONENTS)
    check_dnc(rows, 'R7', ref_column, status_column)
    ctx.clean_up()


def test_int_bom_repeat_csv(test_dir):
    """ Multipart component (not repeated)
        Also DNC in value + Config. """
    prj = 'kibom-test-rep'
    ext = 'csv'
    ctx = context.TestContextSCH(test_dir, prj, 'int_bom_simple_csv', BOM_DIR)
    ctx.run()
    out = prj + '-bom.' + ext
    rows, header, info = ctx.load_csv(out)
    assert header == KIBOM_TEST_HEAD
    ref_column = header.index(REF_COLUMN_NAME)
    status_column = header.index(STATUS_COLUMN_NAME)
    check_kibom_test_netlist(rows, ref_column, 2, ['R2'], ['U1', 'R1'])
    check_dnc(rows, 'R1', ref_column, status_column)
    ctx.clean_up()


def test_int_bom_collision(test_dir):
    """ Field collision and exclude_any """
    prj = 'kibom-test-3'
    ext = 'csv'
    ctx = context.TestContextSCH(test_dir, prj, 'int_bom_simple_csv', BOM_DIR)
    ctx.run(extra_debug=True)
    out = prj + '-bom.' + ext
    rows, header, info = ctx.load_csv(out)
    assert header == KIBOM_TEST_HEAD_TOL
    ref_column = header.index(REF_COLUMN_NAME)
    status_column = header.index(STATUS_COLUMN_NAME)
    check_kibom_test_netlist(rows, ref_column, KIBOM_TEST_GROUPS, KIBOM_TEST_EXCLUDE, KIBOM_TEST_COMPONENTS)
    check_dnc(rows, 'R7', ref_column, status_column)
    ctx.search_err('Field conflict')
    ctx.clean_up()


def test_int_bom_exclude_any(test_dir):
    """ Field collision and exclude_any """
    prj = 'kibom-test-3'
    ext = 'csv'
    ctx = context.TestContextSCH(test_dir, prj, 'int_bom_exclude_any', BOM_DIR)
    ctx.run()
    out = prj + '-bom.' + ext
    rows, header, info = ctx.load_csv(out)
    assert header == KIBOM_TEST_HEAD_TOL
    ref_column = header.index(REF_COLUMN_NAME)
    status_column = header.index(STATUS_COLUMN_NAME)
    check_kibom_test_netlist(rows, ref_column, KIBOM_TEST_GROUPS+1, KIBOM_TEST_EXCLUDE, KIBOM_TEST_COMPONENTS+['X1'])
    check_dnc(rows, 'R7', ref_column, status_column)
    ctx.search_err('Field conflict')
    ctx.clean_up()


def test_int_bom_include_only(test_dir):
    """ Include only (0805 components) """
    prj = 'kibom-test'
    ext = 'csv'
    ctx = context.TestContextSCH(test_dir, prj, 'int_bom_include_only', BOM_DIR)
    ctx.run(extra_debug=True)
    out = prj + '-bom.' + ext
    rows, header, info = ctx.load_csv(out)
    assert header == KIBOM_TEST_HEAD
    ref_column = header.index(REF_COLUMN_NAME)
    status_column = header.index(STATUS_COLUMN_NAME)
    check_kibom_test_netlist(rows, ref_column, 3, KIBOM_TEST_EXCLUDE, ['R1', 'R2', 'R3', 'R4', 'R5', 'R7', 'R8'])
    check_dnc(rows, 'R7', ref_column, status_column)
    ctx.clean_up()


# def test_int_bom_no_test_regex(test_dir):
#     prj = 'kibom-test'
#     ext = 'csv'
#     ctx = context.TestContextSCH(test_dir, prj, 'int_bom_no_include_only', BOM_DIR)
#     ctx.run()
#     out = prj + '-bom.' + ext
#     rows, header, info = ctx.load_csv(out)
#     assert header == KIBOM_TEST_HEAD
#     ref_column = header.index(REF_COLUMN_NAME)
#     status_column = header.index(STATUS_COLUMN_NAME)
#     check_kibom_test_netlist(rows, ref_column, KIBOM_TEST_GROUPS, KIBOM_TEST_EXCLUDE, KIBOM_TEST_COMPONENTS)
#     check_dnc(rows, 'R7', ref_column, status_column)
#     ctx.clean_up()


def test_int_bom_sub_sheet_alt(test_dir):
    """ Test for 2 sub sheets used twice.
        Also stress the v5 loader.
        Also tests sheet path and no grouping with multi-part components """
    prj = 'test_v5'
    ext = 'csv'
    ctx = context.TestContextSCH(test_dir, prj, 'int_bom_sheet_path', BOM_DIR)
    ctx.run(extra_debug=True)
    out = prj + '-bom.' + ext
    rows, header, info = ctx.load_csv(out)
    assert header == KIBOM_TEST_HEAD[:-1] + ['Sheetpath']
    ref_column = header.index(REF_COLUMN_NAME)
    sp_column = header.index('Sheetpath')
    check_kibom_test_netlist(rows, ref_column, 8, [], ['R3', 'R4', 'C1', 'L1', 'R1', 'R2', 'U1', 'U2'])
    check_path(rows, 'U1', ref_column, sp_column, '/Sub Sheet')
    check_path(rows, 'U2', ref_column, sp_column, '/Sub Sheet 2')
    check_path(rows, 'R3', ref_column, sp_column, '/Sub Sheet/Deeper test')
    check_path(rows, 'R4', ref_column, sp_column, '/Sub Sheet 2/Deeper test')
    ctx.clean_up()


def test_int_bom_simple_xlsx_2(test_dir):
    """ No title """
    prj = 'kibom-test'
    ext = 'xlsx'
    ctx = context.TestContextSCH(test_dir, prj, 'int_bom_simple_xlsx_2', BOM_DIR)
    ctx.run()
    out = prj + '-bom.' + ext
    rows, header, sh_head = ctx.load_xlsx(out)
    check_head_xlsx(sh_head, KIBOM_PRJ_INFO, KIBOM_STATS, title=None)
    assert header == KIBOM_TEST_HEAD
    ref_column = header.index(REF_COLUMN_NAME)
    status_column = header.index(STATUS_COLUMN_NAME)
    check_kibom_test_netlist(rows, ref_column, KIBOM_TEST_GROUPS, KIBOM_TEST_EXCLUDE, KIBOM_TEST_COMPONENTS)
    check_dnc(rows, 'R7', ref_column, status_column)
    ctx.clean_up()


def test_int_bom_simple_xlsx_3(test_dir):
    """ No logo """
    prj = 'kibom-test'
    ctx = context.TestContextSCH(test_dir, prj, 'int_bom_simple_xlsx_3', BOM_DIR)
    simple_xlsx_verify(ctx, prj, title=prj+' BOM')


def test_int_bom_simple_xlsx_4(test_dir):
    """ No title, no logo """
    prj = 'kibom-test'
    ext = 'xlsx'
    ctx = context.TestContextSCH(test_dir, prj, 'int_bom_simple_xlsx_4', BOM_DIR)
    ctx.run()
    out = prj + '-bom.' + ext
    rows, header, sh_head = ctx.load_xlsx(out)
    check_head_xlsx(sh_head, KIBOM_PRJ_INFO, KIBOM_STATS, title=None)
    assert header == KIBOM_TEST_HEAD
    ref_column = header.index(REF_COLUMN_NAME)
    status_column = header.index(STATUS_COLUMN_NAME)
    check_kibom_test_netlist(rows, ref_column, KIBOM_TEST_GROUPS, KIBOM_TEST_EXCLUDE, KIBOM_TEST_COMPONENTS)
    check_dnc(rows, 'R7', ref_column, status_column)
    ctx.clean_up()


def test_int_bom_simple_xlsx_5(test_dir):
    """ No title, no logo, no info """
    prj = 'kibom-test'
    ext = 'xlsx'
    ctx = context.TestContextSCH(test_dir, prj, 'int_bom_simple_xlsx_5', BOM_DIR)
    ctx.run()
    out = prj + '-bom.' + ext
    rows, header, sh_head = ctx.load_xlsx(out)
    check_head_xlsx(sh_head, None, KIBOM_STATS, title=None)
    assert header == KIBOM_TEST_HEAD
    ref_column = header.index(REF_COLUMN_NAME)
    status_column = header.index(STATUS_COLUMN_NAME)
    check_kibom_test_netlist(rows, ref_column, KIBOM_TEST_GROUPS, KIBOM_TEST_EXCLUDE, KIBOM_TEST_COMPONENTS)
    check_dnc(rows, 'R7', ref_column, status_column)
    ctx.clean_up()


def test_int_bom_simple_xlsx_6(test_dir):
    """ No title, no logo, no info, no stats """
    prj = 'kibom-test'
    ext = 'xlsx'
    ctx = context.TestContextSCH(test_dir, prj, 'int_bom_simple_xlsx_6', BOM_DIR)
    ctx.run()
    out = prj + '-bom.' + ext
    rows, header, sh_head = ctx.load_xlsx(out)
    assert len(sh_head) == 0
    assert header == KIBOM_TEST_HEAD
    ref_column = header.index(REF_COLUMN_NAME)
    status_column = header.index(STATUS_COLUMN_NAME)
    check_kibom_test_netlist(rows, ref_column, KIBOM_TEST_GROUPS, KIBOM_TEST_EXCLUDE, KIBOM_TEST_COMPONENTS)
    check_dnc(rows, 'R7', ref_column, status_column)
    ctx.clean_up()


def test_int_bom_simple_xlsx_7(test_dir):
    """ Logo from file, no colors (no real test for the style) """
    prj = 'kibom-test'
    ctx = context.TestContextSCH(test_dir, prj, 'int_bom_simple_xlsx_7', BOM_DIR)
    simple_xlsx_verify(ctx, prj)


def test_int_bom_simple_xlsx_8(test_dir):
    """ Style green (no real test for the style) """
    prj = 'kibom-test'
    ctx = context.TestContextSCH(test_dir, prj, 'int_bom_simple_xlsx_8', BOM_DIR)
    simple_xlsx_verify(ctx, prj)


def test_int_bom_simple_xlsx_9(test_dir):
    """ Style red (no real test for the style) """
    prj = 'kibom-test'
    ctx = context.TestContextSCH(test_dir, prj, 'int_bom_simple_xlsx_9', BOM_DIR)
    simple_xlsx_verify(ctx, prj)


def test_int_bom_simple_xlsx_a(test_dir):
    """ No DNF """
    prj = 'kibom-test'
    ctx = context.TestContextSCH(test_dir, prj, 'int_bom_simple_xlsx_a', BOM_DIR)
    simple_xlsx_verify(ctx, prj, False)


def test_int_bom_simple_xlsx_colored_rows(test_dir):
    """ Colored rows """
    prj = 'kibom-test'
    ctx = context.TestContextSCH(test_dir, prj, 'int_bom_simple_xlsx_colored_rows', BOM_DIR)
    simple_xlsx_verify(ctx, prj)


def test_int_bom_datasheet_link_xlsx(test_dir):
    prj = 'links'
    ext = 'xlsx'
    ctx = context.TestContextSCH(test_dir, prj, 'int_bom_datasheet_link_xlsx', BOM_DIR)
    ctx.run()
    out = prj + '.' + ext
    rows, headers, sh_head = ctx.load_xlsx(out)
    assert headers == LINK_HEAD
    # Look for reference and quantity columns
    ref_column = headers.index(REF_COLUMN_NAME)
    part_column = headers.index('Part')
    # Check the normal table
    check_kibom_test_netlist(rows, ref_column, LINKS_GROUPS, LINKS_EXCLUDE, LINKS_COMPONENTS)
    rows2, headers, sh_head = ctx.load_xlsx(out, 2)
    assert headers == LINK_HEAD
    # Check the DNF table
    check_kibom_test_netlist(rows2, ref_column, 1, LINKS_COMPONENTS, LINKS_EXCLUDE)
    # Check the datasheet link
    parts = get_column(rows+rows2, part_column, False)
    for c in parts:
        assert c.strip().startswith('<a href')
        assert 'pdf' in c
        logging.debug(c + ' OK')
    ctx.clean_up()


def test_int_bom_digikey_link_xlsx(test_dir):
    prj = 'links'
    ext = 'xlsx'
    ctx = context.TestContextSCH(test_dir, prj, 'int_bom_digikey_link_xlsx', BOM_DIR)
    ctx.run()
    out = prj + '.' + ext
    rows, headers, sh_head = ctx.load_xlsx(out)
    assert headers == LINK_HEAD
    # Look for reference and quantity columns
    ref_column = headers.index(REF_COLUMN_NAME)
    dk_column = headers.index('digikey#')
    # Check the normal table
    check_kibom_test_netlist(rows, ref_column, LINKS_GROUPS, LINKS_EXCLUDE, LINKS_COMPONENTS)
    rows2, headers, sh_head = ctx.load_xlsx(out, 2)
    assert headers == LINK_HEAD
    # Check the DNF table
    check_kibom_test_netlist(rows2, ref_column, 1, LINKS_COMPONENTS, LINKS_EXCLUDE)
    # Check the datasheet link
    parts = get_column(rows+rows2, dk_column, False)
    for c in parts:
        assert c.strip().startswith('<a href')
        assert 'digikey' in c
        logging.debug(c + ' OK')
    parts = get_column(rows+rows2, headers.index('LCSC#'), False)
    for c in parts:
        assert c.strip().startswith('<a href')
        assert 'lcsc.com' in c
        logging.debug(c + ' OK')
    parts = get_column(rows+rows2, headers.index('mouser#'), False)
    for c in parts:
        assert c.strip().startswith('<a href')
        assert 'mouser' in c
        logging.debug(c + ' OK')
    ctx.clean_up()


def test_int_bom_digikey_links_xlsx(test_dir):
    prj = 'links'
    ext = 'xlsx'
    ctx = context.TestContextSCH(test_dir, prj, 'int_bom_digikey_links_xlsx', BOM_DIR)
    ctx.run()
    out = prj + '.' + ext
    rows, headers, sh_head = ctx.load_xlsx(out)
    assert headers == LINK_HEAD
    # Look for reference and quantity columns
    ref_column = headers.index(REF_COLUMN_NAME)
    dk_column = headers.index('digikey#')
    dk2_column = headers.index('digikey_alt#')
    # Check the normal table
    check_kibom_test_netlist(rows, ref_column, LINKS_GROUPS, LINKS_EXCLUDE, LINKS_COMPONENTS)
    rows2, headers, sh_head = ctx.load_xlsx(out, 2)
    assert headers == LINK_HEAD
    # Check the DNF table
    check_kibom_test_netlist(rows2, ref_column, 1, LINKS_COMPONENTS, LINKS_EXCLUDE)
    # Check the datasheet link
    parts = get_column(rows+rows2, dk_column, False)
    for c in parts:
        assert c.strip().startswith('<a href')
        assert 'digikey' in c
        logging.debug(c + ' OK')
    parts = get_column(rows+rows2, dk2_column, False)
    for c in parts:
        assert c.strip().startswith('<a href')
        assert 'digikey' in c
        logging.debug(c + ' OK')
    ctx.clean_up()


def test_int_bom_no_xlsx_support(test_dir):
    ctx = context.TestContextSCH(test_dir, 'links', 'int_bom_digikey_links_xlsx', BOM_DIR)
    cmd = [os.path.abspath(os.path.dirname(os.path.abspath(__file__))+'/force_xlsx_error.py')]
    ctx.do_run(cmd)
    ctx.search_err('Python xlsxwriter module not installed')
    ctx.search_err('writing XLSX output')


def test_int_bom_missing_lib(test_dir):
    if context.kicad_version >= context.KICAD_VERSION_5_99:
        # V6 schematics are self-contained, no point in checking for libs
        return
    prj = 'v5_errors/kibom-test'
    ctx = context.TestContextSCH(test_dir, prj, 'int_bom_simple_csv', BOM_DIR)
    ctx.run()
    out = 'kibom-test-bom.csv'
    rows, header, info = ctx.load_csv(out)
    check_csv_info(info, KIBOM_PRJ_INFO, KIBOM_STATS)
    kibom_verif(rows, header)
    ctx.search_err(r'Missing library (.*) \(t1')
    ctx.search_err(r'Missing doc-lib entry for t2:R')
    ctx.clean_up()


def test_int_bom_variant_t1(test_dir):
    prj = 'kibom-variante'
    ctx = context.TestContextSCH(test_dir, prj, 'int_bom_var_t1_csv', BOM_DIR)
    ctx.run()
    # No variant
    logging.debug("* No variant")
    rows, header, info = ctx.load_csv(prj+'-bom.csv')
    ref_column = header.index(REF_COLUMN_NAME)
    check_kibom_test_netlist(rows, ref_column, 2, ['R4'], ['R1', 'R2', 'R3'])
    VARIANTE_PRJ_INFO[1] = 'default'
    check_csv_info(info, VARIANTE_PRJ_INFO, [4, 20, 3, 1, 3])
    # V1
    logging.debug("* t1_v1 variant")
    rows, header, info = ctx.load_csv(prj+'-bom_(V1).csv')
    check_kibom_test_netlist(rows, ref_column, 2, ['R3', 'R4'], ['R1', 'R2'])
    ctx.search_err(r'Field Config of component (.*) contains extra spaces')
    VARIANTE_PRJ_INFO[1] = 't1_v1'
    check_csv_info(info, VARIANTE_PRJ_INFO, [4, 20, 2, 1, 2])
    # V2
    logging.debug("* t1_v2 variant")
    rows, header, info = ctx.load_csv(prj+'-bom_(V2).csv')
    check_kibom_test_netlist(rows, ref_column, 1, ['R2', 'R4'], ['R1', 'R3'])
    VARIANTE_PRJ_INFO[1] = 't1_v2'
    check_csv_info(info, VARIANTE_PRJ_INFO, [3, 20, 2, 1, 2])
    # V3
    logging.debug("* t1_v3 variant")
    rows, header, info = ctx.load_csv(prj+'-bom_V3.csv')
    check_kibom_test_netlist(rows, ref_column, 1, ['R2', 'R3'], ['R1', 'R4'])
    VARIANTE_PRJ_INFO[1] = 't1_v3'
    check_csv_info(info, VARIANTE_PRJ_INFO, [3, 20, 2, 1, 2])
    # V1,V3
    logging.debug("* `bla bla` variant")
    rows, header, info = ctx.load_csv(prj+'-bom_bla_bla.csv')
    check_kibom_test_netlist(rows, ref_column, 1, ['R2', 'R3'], ['R1', 'R4'])
    VARIANTE_PRJ_INFO[1] = 'bla bla'
    check_csv_info(info, VARIANTE_PRJ_INFO, [3, 20, 2, 1, 2])
    ctx.clean_up()


@pytest.mark.skipif(not context.ki10(), reason="Target is v10+")
def test_int_bom_variant_t1_10(test_dir):
    # KiCad 10 native variants
    prj = 'kicad-variante'
    ctx = context.TestContextSCH(test_dir, prj, 'int_bom_var_t1_10_csv', BOM_DIR)
    ctx.run()
    extra = ['R9', 'R10', 'R11', 'R12', 'R13', 'R14', 'R15', 'R16']
    # No variant
    logging.debug("* No variant")
    rows, header, info = ctx.load_csv(prj+'-bom.csv')
    ref_column = header.index(REF_COLUMN_NAME)
    check_kibom_test_netlist(rows, ref_column, 2, ['R4'], ['R1', 'R2', 'R3']+extra)
    VARIANTE_PRJ_INFO_10[1] = 'Default'
    check_csv_info(info, VARIANTE_PRJ_INFO_10, [4, 16, 11, 1, 11])
    # V1
    logging.debug("* V1 variant")
    rows, header, info = ctx.load_csv(prj+'-bom_(V1).csv')
    check_kibom_test_netlist(rows, ref_column, 2, ['R3', 'R4'], ['R1', 'R2']+extra)
    ctx.search_err(r'Field Config of component (.*) contains extra spaces')
    VARIANTE_PRJ_INFO_10[1] = 'V1'
    check_csv_info(info, VARIANTE_PRJ_INFO_10, [4, 16, 10, 1, 10])
    # V2
    logging.debug("* V2 variant")
    rows, header, info = ctx.load_csv(prj+'-bom_(V2).csv')
    check_kibom_test_netlist(rows, ref_column, 1, ['R2', 'R4'], ['R1', 'R3']+extra)
    VARIANTE_PRJ_INFO_10[1] = 'V2'
    check_csv_info(info, VARIANTE_PRJ_INFO_10, [3, 16, 10, 1, 10])
    # V3
    logging.debug("* V3 variant")
    rows, header, info = ctx.load_csv(prj+'-bom_V3.csv')
    check_kibom_test_netlist(rows, ref_column, 1, ['R2', 'R3'], ['R1', 'R4']+extra)
    VARIANTE_PRJ_INFO_10[1] = 'V3'
    check_csv_info(info, VARIANTE_PRJ_INFO_10, [3, 16, 10, 1, 10])
    ctx.clean_up(keep_project=True)


@pytest.mark.skipif(not context.ki8(), reason="Target is v8+")
def test_int_bom_variant_t4(test_dir):
    """ Just like test_int_bom_variant_t1 but using the command line to specify all variants instead of repeating the
        outputs """
    prj = 'kibom-variante'
    ctx = context.TestContextSCH(test_dir, prj, 'int_bom_var_t4_csv', BOM_DIR)
    ctx.run(extra=['--variant', 'NONE', '--variant', 'ALL'])
    # No variant
    logging.debug("* No variant")
    rows, header, info = ctx.load_csv(prj+'-bom.csv')
    ref_column = header.index(REF_COLUMN_NAME)
    check_kibom_test_netlist(rows, ref_column, 2, ['R4'], ['R1', 'R2', 'R3'])
    VARIANTE_PRJ_INFO[1] = 'default'
    check_csv_info(info, VARIANTE_PRJ_INFO, [4, 20, 3, 1, 3])
    # V1
    logging.debug("* t1_v1 variant")
    rows, header, info = ctx.load_csv(prj+'-bom_(V1).csv')
    check_kibom_test_netlist(rows, ref_column, 2, ['R3', 'R4'], ['R1', 'R2'])
    ctx.search_err(r'Field Config of component (.*) contains extra spaces')
    VARIANTE_PRJ_INFO[1] = 't1_v1'
    check_csv_info(info, VARIANTE_PRJ_INFO, [4, 20, 2, 1, 2])
    # V2
    logging.debug("* t1_v2 variant")
    rows, header, info = ctx.load_csv(prj+'-bom_(V2).csv')
    check_kibom_test_netlist(rows, ref_column, 1, ['R2', 'R4'], ['R1', 'R3'])
    VARIANTE_PRJ_INFO[1] = 't1_v2'
    check_csv_info(info, VARIANTE_PRJ_INFO, [3, 20, 2, 1, 2])
    # V3
    logging.debug("* t1_v3 variant")
    rows, header, info = ctx.load_csv(prj+'-bom_V3.csv')
    check_kibom_test_netlist(rows, ref_column, 1, ['R2', 'R3'], ['R1', 'R4'])
    VARIANTE_PRJ_INFO[1] = 't1_v3'
    check_csv_info(info, VARIANTE_PRJ_INFO, [3, 20, 2, 1, 2])
    # V1,V3
    logging.debug("* `bla bla` variant")
    rows, header, info = ctx.load_csv(prj+'-bom_bla_bla.csv')
    check_kibom_test_netlist(rows, ref_column, 1, ['R2', 'R3'], ['R1', 'R4'])
    VARIANTE_PRJ_INFO[1] = 'bla bla'
    check_csv_info(info, VARIANTE_PRJ_INFO, [3, 20, 2, 1, 2])
    ctx.clean_up()


def check_value(rows, r_col, ref, v_col, val):
    for r in rows:
        refs = r[r_col].split(' ')
        if ref in refs:
            assert r[v_col] == val
            logging.debug(ref+'='+val+' OK')
            return
    raise AssertionError("Failed to find "+ref)


def test_int_bom_variant_t2b(test_dir):
    prj = 'kibom-variant_2'
    ctx = context.TestContextSCH(test_dir, prj, 'int_bom_var_t2_csv', BOM_DIR)
    ctx.run()
    rows, header, info = ctx.load_csv(prj+'-bom.csv')
    ref_column = header.index(REF_COLUMN_NAME)
    val_column = header.index(VALUE_COLUMN_NAME)
    check_kibom_test_netlist(rows, ref_column, 1, ['C1', 'C2'], ['R1', 'R2'])
    check_value(rows, ref_column, 'R1', val_column, '1k')
    rows, header, info = ctx.load_csv(prj+'-bom_(production).csv')
    check_kibom_test_netlist(rows, ref_column, 2, ['C1'], ['R1', 'R2', 'C2'])
    check_value(rows, ref_column, 'R1', val_column, '1k')
    rows, header, info = ctx.load_csv(prj+'-bom_(test).csv')
    check_kibom_test_netlist(rows, ref_column, 2, ['R2'], ['R1', 'C1', 'C2'])
    check_value(rows, ref_column, 'R1', val_column, '3k3')
    ctx.clean_up()


def test_int_bom_variant_t2c(test_dir):
    """ Test KiBoM variant and field rename filter, R1 must be changed to 3k3 """
    prj = 'kibom-variant_2'
    ctx = context.TestContextSCH(test_dir, prj, 'int_bom_var_t2c_csv', BOM_DIR)
    ctx.run()
    rows, header, info = ctx.load_csv(prj+'-bom_(test).csv')
    ref_column = header.index(REF_COLUMN_NAME)
    val_column = header.index(VALUE_COLUMN_NAME)
    check_kibom_test_netlist(rows, ref_column, 2, ['R2'], ['R1', 'C1', 'C2'])
    check_value(rows, ref_column, 'R1', val_column, '3k3')
    ctx.clean_up()


def test_int_bom_variant_rename_1(test_dir):
    prj = 'f_rename_1'
    ctx = context.TestContextSCH(test_dir, prj, 'int_bom_var_rename_1_csv', BOM_DIR)
    ctx.run(extra_debug=True)
    rows, header, info = ctx.load_csv(prj+'-bom_(PROD).csv')
    ref_column = header.index(REF_COLUMN_NAME)
    check_kibom_test_netlist(rows, ref_column, 2, ['R2', 'D2'], ['R1', 'D1'])
    rows, header, info = ctx.load_csv(prj+'-bom_(DEV).csv')
    check_kibom_test_netlist(rows, ref_column, 3, None, ['R1', 'R2', 'D1', 'D2'])
    ctx.clean_up()


def test_int_bom_variant_rename_2(test_dir):
    prj = 'f_rename_2'
    ctx = context.TestContextSCH(test_dir, prj, 'int_bom_var_rename_2_csv', BOM_DIR)
    ctx.run(extra_debug=True)
    rows, header, info = ctx.load_csv(prj+'-bom_(PROD).csv')
    ref_column = header.index(REF_COLUMN_NAME)
    check_kibom_test_netlist(rows, ref_column, 2, ['R2', 'D2'], ['R1', 'D1'])
    rows, header, info = ctx.load_csv(prj+'-bom_(DEV).csv')
    check_kibom_test_netlist(rows, ref_column, 3, None, ['R1', 'R2', 'D1', 'D2'])
    ctx.clean_up()


def test_int_bom_variant_t2s(test_dir):
    prj = 'kibom-variant_2'
    ctx = context.TestContextSCH(test_dir, prj, 'int_bom_var_t2s_csv', BOM_DIR)
    ctx.run(extra_debug=True)
    rows, header, info = ctx.load_csv(prj+'-bom_(dummy).csv')
    ref_column = header.index(REF_COLUMN_NAME)
    check_kibom_test_netlist(rows, ref_column, 1, ['C1', 'C2'], ['R1', 'R2'])
    rows, header, info = ctx.load_csv(prj+'-bom_(dummy2).csv')
    check_kibom_test_netlist(rows, ref_column, 1, ['C1', 'C2'], ['R1', 'R2'])
    ctx.clean_up()


def test_int_bom_variant_t2if(test_dir):
    """ IBoM variants test full """
    prj = 'kibom-variant_3'
    ctx = context.TestContextSCH(test_dir, prj, 'int_bom_var_t2i_csv', BOM_DIR)
    ctx.run()
    rows, header, info = ctx.load_csv(prj+'-bom.csv')
    ref_column = header.index(REF_COLUMN_NAME)
    check_kibom_test_netlist(rows, ref_column, 2, ['C1', 'C2'], ['R1', 'R2', 'R3'])
    rows, header, info = ctx.load_csv(prj+'-bom_[2].csv')
    check_kibom_test_netlist(rows, ref_column, 1, ['C1', 'C2'], ['R1', 'R2'])
    rows, header, info = ctx.load_csv(prj+'-bom_(production).csv')
    check_kibom_test_netlist(rows, ref_column, 3, ['C1'], ['R1', 'R2', 'C2', 'R3'])
    rows, header, info = ctx.load_csv(prj+'-bom_(test).csv')
    check_kibom_test_netlist(rows, ref_column, 3, ['R2'], ['R1', 'C1', 'C2', 'R3'])
    ctx.clean_up(keep_project=True)


@pytest.mark.skipif(context.ki5(), reason="needs KiCad 6 text variables")
def test_int_bom_variant_t2it(test_dir):
    """ IBoM variants test full, here we expand KiCad 6 variables """
    prj = 'kibom-variant_3_txt'
    ctx = context.TestContextSCH(test_dir, prj, 'int_bom_var_t2i_csv', BOM_DIR)
    ctx.run()
    rows, header, info = ctx.load_csv(prj+'-bom.csv')
    ref_column = header.index(REF_COLUMN_NAME)
    check_kibom_test_netlist(rows, ref_column, 2, ['C1', 'C2'], ['R1', 'R2', 'R3'])
    rows, header, info = ctx.load_csv(prj+'-bom_[2].csv')
    check_kibom_test_netlist(rows, ref_column, 1, ['C1', 'C2'], ['R1', 'R2'])
    rows, header, info = ctx.load_csv(prj+'-bom_(production).csv')
    check_kibom_test_netlist(rows, ref_column, 3, ['C1'], ['R1', 'R2', 'C2', 'R3'])
    rows, header, info = ctx.load_csv(prj+'-bom_(test).csv')
    check_kibom_test_netlist(rows, ref_column, 3, ['R2'], ['R1', 'C1', 'C2', 'R3'])
    ctx.clean_up(keep_project=True)


def test_int_bom_variant_t2is(test_dir):
    """ IBoM variants test simple """
    prj = 'kibom-variant_3'
    ctx = context.TestContextSCH(test_dir, prj, 'int_bom_var_t2is_csv', BOM_DIR)
    ctx.run(extra_debug=True)
    rows, header, info = ctx.load_csv('filter_R1.csv')
    ref_column = header.index(REF_COLUMN_NAME)
    check_kibom_test_netlist(rows, ref_column, 2, ['R2', 'R1'], ['C1', 'C2', 'R3'])
    ctx.clean_up(keep_project=True)


def test_int_bom_variant_t2kf(test_dir):
    """ KiCost variants test full.
        R1 must be changed to 3k3.
        We also test the DNP mechanism. """
    prj = 'kibom-variant_kicost'
    ctx = context.TestContextSCH(test_dir, prj, 'int_bom_var_t2k_csv', BOM_DIR)
    ctx.run()
    rows, header, info = ctx.load_csv(prj+'-bom.csv')
    ref_column = header.index(REF_COLUMN_NAME)
    check_kibom_test_netlist(rows, ref_column, 1, ['C1', 'C2'], ['R1', 'R2'])
    rows, header, info = ctx.load_csv(prj+'-bom_(production).csv')
    check_kibom_test_netlist(rows, ref_column, 2, ['C1'], ['R1', 'R2', 'C2'])
    val_column = header.index(VALUE_COLUMN_NAME)
    check_value(rows, ref_column, 'R1', val_column, '1k')
    rows, header, info = ctx.load_csv(prj+'-bom_(test).csv')
    check_kibom_test_netlist(rows, ref_column, 2, ['R2'], ['R1', 'C1', 'C2'])
    check_value(rows, ref_column, 'R1', val_column, '3k3')
    ctx.clean_up()


def test_int_bom_wrong_variant(test_dir):
    ctx = context.TestContextSCH(test_dir, 'links', 'int_bom_wrong_variant', '')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Unknown variant name")
    ctx.clean_up()


def test_int_bom_fil_dummy(test_dir):
    prj = 'kibom-test-4'
    ctx = context.TestContextSCH(test_dir, prj, 'int_bom_fil_dummy', BOM_DIR)
    ctx.run()
    rows, header, info = ctx.load_csv(prj+'-bom.csv')
    ref_column = header.index(REF_COLUMN_NAME)
    check_kibom_test_netlist(rows, ref_column, 4, None, ['R1', 'R2', 'R3', 'R4', 'R5', 'R6', 'C1', 'C2'])
    ctx.search_err('Field conflict', invert=True)
    ctx.clean_up()


def test_int_bom_fil_1(test_dir):
    prj = 'kibom-test-4'
    ctx = context.TestContextSCH(test_dir, prj, 'int_bom_fil_1', BOM_DIR)
    ctx.run()
    rows, header, info = ctx.load_csv('empty_val.csv')
    ref_column = header.index(REF_COLUMN_NAME)
    check_kibom_test_netlist(rows, ref_column, 3, None, ['R3', 'R4', 'R5', 'R6', 'C1', 'C2'])
    rows, header, info = ctx.load_csv('by_prefix.csv')
    check_kibom_test_netlist(rows, ref_column, 3, None, ['R2', 'R3', 'R4', 'R5', 'R6'])
    rows, header, info = ctx.load_csv('no_kk.csv')
    check_kibom_test_netlist(rows, ref_column, 3, None, ['R1', 'R2', 'R5', 'R6', 'C1', 'C2'])
    rows, header, info = ctx.load_csv('no_conf_kk.csv')
    check_kibom_test_netlist(rows, ref_column, 3, None, ['R1', 'R2', 'R3', 'R4', 'C1', 'C2'])
    rows, header, info = ctx.load_csv('no_by_prefix.csv')
    check_kibom_test_netlist(rows, ref_column, 2, None, ['R1', 'C1', 'C2'])
    rows, header, info = ctx.load_csv('multi.csv')
    check_kibom_test_netlist(rows, ref_column, 1, None, ['C1', 'C2'])
    ctx.search_err('Field conflict')
    ctx.clean_up()


def test_int_bom_fil_2(test_dir):
    prj = 'kibom-variant_3'
    ctx = context.TestContextSCH(test_dir, prj, 'int_bom_fil_2', BOM_DIR)
    ctx.run(extra_debug=True)
    rows, header, info = ctx.load_csv('smd.csv')
    ref_column = header.index(REF_COLUMN_NAME)
    check_kibom_test_netlist(rows, ref_column, 3, None, ['R2', 'C2', 'FID1'])
    rows, header, info = ctx.load_csv('tht.csv')
    check_kibom_test_netlist(rows, ref_column, 3, None, ['R1', 'C1', 'FID1'])
    rows, header, info = ctx.load_csv('virtual.csv')
    check_kibom_test_netlist(rows, ref_column, 2, None, ['R1', 'R2', 'C1', 'C2'])
    ctx.search_err(r"Repeated PCB R3")
    ctx.test_compress(prj+'-result.zip', ['BoM/smd.csv', 'BoM/tht.csv', 'BoM/virtual.csv'])
    ctx.clean_up(keep_project=True)


def test_int_bom_variant_t3(test_dir):
    """ Test if we can move the filters to the variant.
        Also test the '!' filter (always false) """
    prj = 'kibom-variante'
    ctx = context.TestContextSCH(test_dir, prj, 'int_bom_var_t3_csv', BOM_DIR)
    ctx.run()
    rows, header, info = ctx.load_csv(prj+'-bom_(V1).csv')
    ref_column = header.index(REF_COLUMN_NAME)
    check_kibom_test_netlist(rows, ref_column, 2, ['R3', 'R4'], ['R1', 'R2'])
    VARIANTE_PRJ_INFO[1] = 't1_v1'
    check_csv_info(info, VARIANTE_PRJ_INFO, [4, 20, 2, 1, 2])
    ctx.search_err(r"Creating internal filter(.*)_mechanical")
    ctx.search_err(r"Creating internal filter(.*)_kibom_dnf_Config")
    ctx.search_err(r"Creating internal filter(.*)_kibom_dnc")
    rows, header, info = ctx.load_csv(prj+'-bom_(V1b).csv')
    # Here we remove the DNC, so R1 and R2 becomes identical
    check_kibom_test_netlist(rows, ref_column, 1, ['R3', 'R4'], ['R1', 'R2'])
    ctx.clean_up()


def test_int_bom_variant_cli(test_dir):
    """ Assign t1_v1 to default from cli. Make sure t1_v3 isn't affected """
    prj = 'kibom-variante'
    ctx = context.TestContextSCH(test_dir, prj, 'int_bom_var_t1_cli', BOM_DIR)
    ctx.run(extra=['--global-redef', 'variant=t1_v1'])
    # No variant -> t1_v1
    logging.debug("* No variant -> t1_v1")
    rows, header, info = ctx.load_csv(prj+'-bom_(V1).csv')
    ref_column = header.index(REF_COLUMN_NAME)
    check_kibom_test_netlist(rows, ref_column, 2, ['R3', 'R4'], ['R1', 'R2'])
    VARIANTE_PRJ_INFO[1] = 't1_v1'
    check_csv_info(info, VARIANTE_PRJ_INFO, [4, 20, 2, 1, 2])
    # V3
    logging.debug("* t1_v3 variant")
    rows, header, info = ctx.load_csv(prj+'-bom_V3.csv')
    check_kibom_test_netlist(rows, ref_column, 1, ['R2', 'R3'], ['R1', 'R4'])
    VARIANTE_PRJ_INFO[1] = 't1_v3'
    check_csv_info(info, VARIANTE_PRJ_INFO, [3, 20, 2, 1, 2])
    ctx.clean_up()


def test_int_bom_variant_glb(test_dir):
    """ Assign t1_v1 to default from global. Make sure t1_v3 isn't affected """
    prj = 'kibom-variante'
    ctx = context.TestContextSCH(test_dir, prj, 'int_bom_var_t1_glb', BOM_DIR)
    ctx.run()
    # No variant -> t1_v1
    logging.debug("* No variant -> t1_v1")
    rows, header, info = ctx.load_csv(prj+'-bom_(V1).csv')
    ref_column = header.index(REF_COLUMN_NAME)
    check_kibom_test_netlist(rows, ref_column, 2, ['R3', 'R4'], ['R1', 'R2'])
    VARIANTE_PRJ_INFO[1] = 't1_v1'
    check_csv_info(info, VARIANTE_PRJ_INFO, [4, 20, 2, 1, 2])
    # V3
    logging.debug("* t1_v3 variant")
    rows, header, info = ctx.load_csv(prj+'-bom_V3.csv')
    check_kibom_test_netlist(rows, ref_column, 1, ['R2', 'R3'], ['R1', 'R4'])
    VARIANTE_PRJ_INFO[1] = 't1_v3'
    check_csv_info(info, VARIANTE_PRJ_INFO, [3, 20, 2, 1, 2])


def test_int_bom_variant_cl_gl(test_dir):
    """ Assign t1_v1 to default from global.
        Overwrite it from cli to t1_v2.
        Make sure t1_v3 isn't affected """
    prj = 'kibom-variante'
    ctx = context.TestContextSCH(test_dir, prj, 'int_bom_var_t1_glb', BOM_DIR)
    ctx.run(extra=['--global-redef', 'variant=t1_v2'])
    ctx.search_out(r'Using command line value .?t1_v2.? for global option .?variant.?')
    # No variant -> t1_v2
    logging.debug("* No variant -> t1_v2")
    rows, header, info = ctx.load_csv(prj+'-bom_(V2).csv')
    ref_column = header.index(REF_COLUMN_NAME)
    check_kibom_test_netlist(rows, ref_column, 1, ['R2', 'R4'], ['R1', 'R3'])
    VARIANTE_PRJ_INFO[1] = 't1_v2'
    check_csv_info(info, VARIANTE_PRJ_INFO, [3, 20, 2, 1, 2])
    # V3
    logging.debug("* t1_v3 variant")
    rows, header, info = ctx.load_csv(prj+'-bom_V3.csv')
    check_kibom_test_netlist(rows, ref_column, 1, ['R2', 'R3'], ['R1', 'R4'])
    VARIANTE_PRJ_INFO[1] = 't1_v3'
    check_csv_info(info, VARIANTE_PRJ_INFO, [3, 20, 2, 1, 2])
    ctx.clean_up()


def test_int_bom_ref_separator(test_dir):
    ctx, out = kibom_setup(test_dir, 'int_bom_ref_separator')
    rows, header, info = ctx.load_csv(out)
    check_csv_info(info, KIBOM_PRJ_INFO, KIBOM_STATS)
    kibom_verif(rows, header, ref_sep=',')
    ctx.clean_up()


def test_int_bom_variant_5(test_dir):
    prj = 'kibom-variant_5'
    ctx = context.TestContextSCH(test_dir, prj, 'int_bom_var_5_csv', BOM_DIR)
    ctx.run()
    rows, header, info = ctx.load_csv(prj+'-bom.csv')
    ref_column = header.index(REF_COLUMN_NAME)
    check_kibom_test_netlist(rows, ref_column, 1, ['C1', 'C2', 'R1'], ['R2'])
    ctx.clean_up()


def test_int_bom_merge_csv_1(test_dir):
    prj = 'merge_1'
    yaml = 'int_bom_merge_csv_1'
    if context.ki6():
        yaml += '_k6'
    ctx = context.TestContextSCH(test_dir, prj, yaml, BOM_DIR)
    ctx.run(extra_debug=True)
    rows, header, info = ctx.load_csv(prj+'-bom.csv')
    ref_column = header.index(REF_COLUMN_NAME)
    check_kibom_test_netlist(rows, ref_column, 4, None, MERGED_COMPS)
    src_column = header.index(SOURCE_BOM_COLUMN_NAME)
    check_source(rows, 'A:R1', ref_column, src_column, MERGED_R1_SRC)
    ctx.search_err(r'Stats for')
    ctx.clean_up()


def test_int_bom_merge_csv_2(test_dir):
    prj = 'merge_1'
    yaml = 'int_bom_merge_csv_2'
    ctx = context.TestContextSCH(test_dir, prj, yaml, BOM_DIR)
    ctx.run(extra_debug=True)
    rows, header, info = ctx.load_csv(prj+'-bom.csv')
    ref_column = header.index(REF_COLUMN_NAME)
    check_kibom_test_netlist(rows, ref_column, 4, None, MERGED_COMPS)
    src_column = header.index(SOURCE_BOM_COLUMN_NAME)
    check_source(rows, 'A:R1', ref_column, src_column, MERGED_R1_SRC)
    ctx.search_err(r'Stats for')
    ctx.clean_up()


def test_int_bom_merge_html_1(test_dir):
    prj = 'merge_1'
    yaml = 'int_bom_merge_html_1'
    if context.ki6():
        yaml += '_k6'
    ctx = context.TestContextSCH(test_dir, prj, yaml, BOM_DIR)
    ctx.run()
    rows, header, info = ctx.load_html(prj+'-bom.html')
    logging.debug(rows[0])
    ref_column = header[0].index(REF_COLUMN_NAME)
    check_kibom_test_netlist(rows[0], ref_column, 4, None, MERGED_COMPS)
    src_column = header[0].index(SOURCE_BOM_COLUMN_NAME)
    check_source(rows[0], 'A:R1', ref_column, src_column, MERGED_R1_SRC)
    ctx.clean_up()


def test_int_bom_merge_html_2(test_dir):
    prj = 'merge_1'
    yaml = 'int_bom_merge_html_2'
    ctx = context.TestContextSCH(test_dir, prj, yaml, BOM_DIR)
    ctx.run()
    rows, header, info = ctx.load_html(prj+'-bom.html')
    logging.debug(rows[0])
    ref_column = header[0].index(REF_COLUMN_NAME)
    check_kibom_test_netlist(rows[0], ref_column, 4, None, MERGED_COMPS)
    src_column = header[0].index(SOURCE_BOM_COLUMN_NAME)
    check_source(rows[0], 'A:R1', ref_column, src_column, MERGED_R1_SRC)
    ctx.clean_up()


def test_int_bom_merge_xlsx_1(test_dir):
    prj = 'merge_1'
    yaml = 'int_bom_merge_xlsx_1'
    if context.ki6():
        yaml += '_k6'
    ctx = context.TestContextSCH(test_dir, prj, yaml, BOM_DIR)
    ctx.run()
    rows, header, info = ctx.load_xlsx(prj+'-bom.xlsx')
    ref_column = header.index(REF_COLUMN_NAME)
    check_kibom_test_netlist(rows, ref_column, 4, None, MERGED_COMPS)
    src_column = header.index(SOURCE_BOM_COLUMN_NAME)
    check_source(rows, 'A:R1', ref_column, src_column, MERGED_R1_SRC)
    ctx.clean_up()


def test_int_bom_merge_xlsx_2(test_dir):
    prj = 'merge_1'
    yaml = 'int_bom_merge_xlsx_2'
    ctx = context.TestContextSCH(test_dir, prj, yaml, BOM_DIR)
    ctx.run()
    rows, header, info = ctx.load_xlsx(prj+'-bom.xlsx')
    ref_column = header.index(REF_COLUMN_NAME)
    check_kibom_test_netlist(rows, ref_column, 4, None, MERGED_COMPS)
    src_column = header.index(SOURCE_BOM_COLUMN_NAME)
    check_source(rows, 'A:R1', ref_column, src_column, MERGED_R1_SRC)
    ctx.clean_up()


def test_int_bom_merge_xml_1(test_dir):
    prj = 'merge_1'
    yaml = 'int_bom_merge_xml_1'
    if context.ki6():
        yaml += '_k6'
    ctx = context.TestContextSCH(test_dir, prj, yaml, BOM_DIR)
    ctx.run()
    rows, header = ctx.load_xml(prj+'-bom.xml')
    ref_column = header.index(REF_COLUMN_NAME)
    check_kibom_test_netlist(rows, ref_column, 4, None, MERGED_COMPS)
    src_column = header.index(SOURCE_BOM_COLUMN_NAME.replace(' ', '_'))
    check_source(rows, 'A:R1', ref_column, src_column, MERGED_R1_SRC)
    ctx.clean_up()


def test_int_bom_merge_xml_2(test_dir):
    prj = 'merge_1'
    yaml = 'int_bom_merge_xml_2'
    ctx = context.TestContextSCH(test_dir, prj, yaml, BOM_DIR)
    ctx.run()
    rows, header = ctx.load_xml(prj+'-bom.xml')
    ref_column = header.index(REF_COLUMN_NAME)
    check_kibom_test_netlist(rows, ref_column, 4, None, MERGED_COMPS)
    src_column = header.index(SOURCE_BOM_COLUMN_NAME.replace(' ', '_'))
    check_source(rows, 'A:R1', ref_column, src_column, MERGED_R1_SRC)
    ctx.clean_up()


def test_int_bom_subparts_1(test_dir):
    prj = 'subparts'
    ctx = context.TestContextSCH(test_dir, prj, 'int_bom_subparts_1')
    ctx.run(extra_debug=True)
    output = prj+'-bom.csv'
    ctx.expect_out_file(output)
    ctx.compare_txt(output)
    ctx.clean_up()


def test_int_bom_subparts_2(test_dir):
    prj = 'subparts_rename'
    ctx = context.TestContextSCH(test_dir, prj, 'int_bom_subparts_2')
    ctx.run(extra_debug=True)
    output = prj+'-bom.csv'
    ctx.expect_out_file(output)
    ctx.compare_txt(output, 'subparts-bom.csv')
    ctx.clean_up()


def test_int_bom_subparts_3(test_dir):
    prj = 'subparts_rename'
    ctx = context.TestContextSCH(test_dir, prj, 'int_bom_subparts_3')
    ctx.run(extra_debug=True)
    output = prj+'-bom.csv'
    ctx.expect_out_file(output)
    ctx.compare_txt(output, 'subparts-bom.csv')
    ctx.clean_up()


@pytest.mark.skipif(not context.ki6(), reason="Target is v6+")
def test_value_change_1(test_dir):
    prj = 'value_change'
    ctx = context.TestContextSCH(test_dir, 'shared_page_value_change/'+prj, 'value_change_1', 'Modified')
    ctx.run()
    sch = ctx.expect_out_file_d(prj+'.kicad_sch')
    ctx = context.TestContextSCH(test_dir, 'shared_page_value_change_complex/'+prj, 'int_bom_csv_no_info', 'BoM')
    ctx.run(no_board_file=True, extra=['-e', sch])
    rows, header, info = ctx.load_csv(prj+'-bom.csv')
    ref_column = header.index(REF_COLUMN_NAME)
    check_kibom_test_netlist(rows, ref_column, 4, None, ['C1', 'C2', 'J1', 'J2', 'R1', 'R2'],
                             vals={'C1': '150p', 'C2': '220p'}, val_column=header.index('Value'))
    ctx.clean_up()


@pytest.mark.skipif(not context.ki6(), reason="Target is v6+")
def test_value_change_2(test_dir):
    prj = 'value_change'
    ctx = context.TestContextSCH(test_dir, 'shared_page_value_change_complex/'+prj, 'value_change_2', 'Modified')
    ctx.run()
    sch = ctx.expect_out_file_d(prj+'.kicad_sch')
    # assert False
    ctx = context.TestContextSCH(test_dir, 'shared_page_value_change_complex/'+prj, 'int_bom_csv_no_info', 'BoM')
    ctx.run(no_board_file=True, extra=['-e', sch])
    rows, header, info = ctx.load_csv(prj+'-bom.csv')
    ref_column = header.index(REF_COLUMN_NAME)
    check_kibom_test_netlist(rows, ref_column, 5, None,
                             ['C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'J1', 'J2', 'R1', 'R2', 'R3', 'R4', 'R5', 'R6'],
                             vals={'C1 C3 C6': '150p', 'C2 C4': '220p', 'C5': '330p'},
                             val_column=header.index('Value'))
    ctx.clean_up()


@pytest.mark.skipif(not context.ki8(), reason="Target is v8+")
def test_int_bom_simple_sub_pcb(test_dir):
    prj = 'simple_sub_pcb'
    ctx = context.TestContextSCH(test_dir, prj, 'int_bom_simple_sub_pcb')
    ctx.run()
    rows, header, info = ctx.load_csv(prj+'-bom_board1.csv')
    ref_column = header.index("Designator")
    check_kibom_test_netlist(rows, ref_column, 1, ['R6', 'R7', 'R8', 'R9', 'R10'], ['R1', 'R2', 'R3', 'R4', 'R5'], ref_sep=',')
    rows, header, info = ctx.load_csv(prj+'-bom_board2.csv')
    ref_column = header.index("Designator")
    check_kibom_test_netlist(rows, ref_column, 1, ['R1', 'R2', 'R3', 'R4', 'R5'], ['R6', 'R7', 'R8', 'R9', 'R10'], ref_sep=',')
    ctx.clean_up()


@pytest.mark.skipif(not context.ki8(), reason="Just checking with modern KiCad")
def test_bom_panel_C1x4_base(test_dir):
    """ This tests a 4 boards panel with just one component C1 """
    prj = 'panel_C1x4'
    ctx = context.TestContext(test_dir, prj, 'int_bom_csv_no_extra', 'BoM')
    ctx.run()
    rows, header, info = ctx.load_csv(prj+'-bom.csv')
    # All in 1 group
    assert len(rows) == 1
    # Qty 1
    assert rows[0][6] == '1'
    ctx.clean_up()


@pytest.mark.skipif(not context.ki8(), reason="Just checking with modern KiCad")
def test_bom_panel_C1x4_rep(test_dir):
    """ This tests a 4 boards panel with just one component C1, SCH repeats """
    prj = 'panel_C1x4_rep'
    ctx = context.TestContext(test_dir, prj, 'int_bom_csv_no_extra', 'BoM')
    ctx.run()
    rows, header, info = ctx.load_csv(prj+'-bom.csv')
    # All in 1 group
    assert len(rows) == 1
    # Qty 4
    assert rows[0][6] == '4'
    ctx.clean_up()


@pytest.mark.skipif(not context.ki8(), reason="Just checking with modern KiCad")
def test_bom_panel_U1x4_base(test_dir):
    """ This tests a 4 boards panel with just one component U1 """
    prj = 'panel_U1x4'
    ctx = context.TestContext(test_dir, prj, 'int_bom_csv_no_extra', 'BoM')
    ctx.run()
    rows, header, info = ctx.load_csv(prj+'-bom.csv')
    # All in 1 group
    assert len(rows) == 1
    # Qty 1
    assert rows[0][6] == '1'
    ctx.clean_up()


@pytest.mark.skipif(not context.ki8(), reason="Just checking with modern KiCad")
def test_bom_panel_U1x4_rep(test_dir):
    """ This tests a 4 boards panel with just one component U1, SCH repeats """
    prj = 'panel_U1x4_rep'
    ctx = context.TestContext(test_dir, prj, 'int_bom_csv_no_extra', 'BoM')
    ctx.run()
    rows, header, info = ctx.load_csv(prj+'-bom.csv')
    # All in 1 group
    assert len(rows) == 1
    # Qty 4
    assert rows[0][6] == '4'
    ctx.clean_up()
