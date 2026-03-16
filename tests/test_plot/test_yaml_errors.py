"""
Tests various errors in the config file

- Wrong kibot
- No kibot.version
- Typo in kibot.version
- Wrong kibot.version
- Missing drill map type
- Wrong drill map type
- Wrong step origin
- Wrong step min_distance
- Wrong layer:
  - Incorrect name
  - Inner.1, but no inner layers
  - Inner_1 (malformed)
  - Not a list
  - Unknown attribute
  - No layer attribute
- No output:
  - name
  - type
  - layers
- Output:
  - with unknown attribute
  - Not a list
- Filters:
  - Not a list
  - Empty number
  - No number
  - Empty regex
  - No regex
  - No filter
- Pre-flight:
  - Not a list
  - Unknown entry
  - Wrong type for entry (run_drc)
- YAML syntax
- Unknown section
- HPGL wrong pen_number
- KiBoM wrong format
  - Invalid column name
  - Failed to get columns
  - Column without field
- PcbDraw
  - Wrong color

For debug information use:
pytest-3 --log-cli-level debug
"""

import pytest
import os
from . import context
from kibot.misc import (EXIT_BAD_CONFIG, PLOT_ERROR, WRONG_ARGUMENTS)
PRJ = 'fail-project'


@pytest.mark.indep
def test_no_version(test_dir):
    ctx = context.TestContext(test_dir, '3Rs', 'error_no_version')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err('YAML config needs `kibot.version`.')
    ctx.clean_up()


@pytest.mark.indep
def test_wrong_version(test_dir):
    ctx = context.TestContext(test_dir, '3Rs', 'error_wrong_version')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err('Unknown KiBot config version: 20')
    ctx.clean_up()


@pytest.mark.indep
def test_wrong_version_2(test_dir):
    ctx = context.TestContext(test_dir, '3Rs', 'error_wrong_version_2')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err('Incorrect .?kibot.? section')
    ctx.clean_up()


@pytest.mark.indep
def test_wrong_version_3(test_dir):
    ctx = context.TestContext(test_dir, '3Rs', 'error_wrong_version_3')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err('YAML config needs .?kibot.version.?')
    ctx.clean_up()


@pytest.mark.indep
def test_drill_map_no_type_1(test_dir):
    ctx = context.TestContext(test_dir, '3Rs', 'error_drill_map_no_type')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Empty option .?map.?")
    ctx.clean_up()


@pytest.mark.indep
def test_drill_map_no_type_2(test_dir):
    ctx = context.TestContext(test_dir, '3Rs', 'error_drill_map_no_type_2')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Unknown option .?types.?")
    ctx.clean_up()


@pytest.mark.indep
def test_drill_map_wrong_type_1(test_dir):
    ctx = context.TestContext(test_dir, '3Rs', 'error_drill_map_wrong_type')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Option .?type.? must be any of")
    ctx.clean_up()


@pytest.mark.indep
def test_drill_map_wrong_type_2(test_dir):
    ctx = context.TestContext(test_dir, '3Rs', 'error_drill_map_wrong_type_2')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Option .?type.? must be a string")
    ctx.clean_up()


@pytest.mark.indep
def test_drill_map_wrong_type_3(test_dir):
    ctx = context.TestContext(test_dir, '3Rs', 'error_drill_map_wrong_type_3')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Option .?map.? must be any of")
    ctx.clean_up()


@pytest.mark.skipif(not context.ki10(), reason="No HPGL in v10+")
def test_drill_map_wrong_type_4(test_dir):
    ctx = context.TestContext(test_dir, 'bom', 'error_drill_map_wrong_type_4')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("support HPGL")
    ctx.clean_up()


@pytest.mark.indep
def test_drill_report_no_type_1(test_dir):
    ctx = context.TestContext(test_dir, '3Rs', 'error_drill_report_no_type')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Empty option .?report.?")
    ctx.clean_up()


@pytest.mark.indep
def test_drill_report_no_type_2(test_dir):
    ctx = context.TestContext(test_dir, '3Rs', 'error_drill_report_no_type_2')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Unknown option .?filenames.?")
    ctx.clean_up()


@pytest.mark.indep
def test_drill_report_wrong_type_2(test_dir):
    ctx = context.TestContext(test_dir, '3Rs', 'error_drill_report_wrong_type_2')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Option .?filename.? must be a string")
    ctx.clean_up()


@pytest.mark.indep
def test_drill_report_wrong_type_3(test_dir):
    ctx = context.TestContext(test_dir, '3Rs', 'error_drill_report_wrong_type_3')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Option .?report.? must be any of")
    ctx.clean_up()


@pytest.mark.indep
def test_wrong_layer_1(test_dir):
    ctx = context.TestContext(test_dir, '3Rs', 'error_wrong_layer_1')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Unknown layer name: .?F.Bogus.?")
    ctx.clean_up()


@pytest.mark.indep
def test_wrong_layer_2(test_dir):
    ctx = context.TestContext(test_dir, '3Rs', 'error_wrong_layer_2')
    ctx.run(PLOT_ERROR)
    assert ctx.search_err("Inner layer (.*) is not valid for this board")
    ctx.clean_up()


@pytest.mark.indep
def test_wrong_layer_3(test_dir):
    ctx = context.TestContext(test_dir, '3Rs', 'error_wrong_layer_3')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Malformed inner layer name: .?Inner_1.?,")
    ctx.clean_up()


@pytest.mark.indep
def test_wrong_layer_4(test_dir):
    ctx = context.TestContext(test_dir, '3Rs', 'error_wrong_layer_4')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err(".?layers.? must be any of")
    ctx.clean_up()


@pytest.mark.indep
def test_wrong_layer_5(test_dir):
    ctx = context.TestContext(test_dir, '3Rs', 'error_wrong_layer_5')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Unknown option .?bogus.?")
    ctx.clean_up()


@pytest.mark.indep
def test_wrong_layer_6(test_dir):
    ctx = context.TestContext(test_dir, '3Rs', 'error_wrong_layer_6')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Missing or empty .?layer.? attribute")
    ctx.clean_up()


@pytest.mark.indep
def test_wrong_layer_7(test_dir):
    """ List of numbers """
    ctx = context.TestContext(test_dir, '3Rs', 'error_wrong_layer_7')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err(".?layers.? must be any of")
    ctx.clean_up()


@pytest.mark.indep
def test_wrong_layer_9(test_dir):
    """ A bogus string """
    ctx = context.TestContext(test_dir, '3Rs', 'error_wrong_layer_9')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Unknown layer spec: .?nada.?")
    ctx.clean_up()


@pytest.mark.indep
def test_wrong_layer_8(test_dir):
    """ List of strings, but number in middle """
    ctx = context.TestContext(test_dir, '3Rs', 'error_wrong_layer_8')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err(".?4.? must be any of")
    ctx.clean_up()


@pytest.mark.indep
def test_no_name(test_dir):
    ctx = context.TestContext(test_dir, '3Rs', 'error_no_name')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Output needs a name")
    ctx.clean_up()


@pytest.mark.indep
def test_empty_name(test_dir):
    ctx = context.TestContext(test_dir, '3Rs', 'error_empty_name')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Output needs a name")
    ctx.clean_up()


@pytest.mark.indep
def test_no_type(test_dir):
    ctx = context.TestContext(test_dir, '3Rs', 'error_no_type')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Output .PDF. needs a type")
    ctx.clean_up()


@pytest.mark.indep
def test_out_unknown_attr(test_dir):
    ctx = context.TestContext(test_dir, '3Rs', 'error_unk_attr')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Unknown option .?directory.?")
    ctx.clean_up()


@pytest.mark.indep
def test_out_needs_type(test_dir):
    ctx = context.TestContext(test_dir, '3Rs', 'error_needs_type')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("needs a type")
    ctx.clean_up()


# Now is valid
# @pytest.mark.indep
# def test_no_options(test_dir):
#     ctx = context.TestContext(test_dir, '3Rs', 'error_no_options')
#     ctx.run(EXIT_BAD_CONFIG)
#     assert ctx.search_err("Output .PDF. needs options")
#     ctx.clean_up()


# Now we interpret it as "all"
# @pytest.mark.indep
# def test_no_layers(test_dir):
#     ctx = context.TestContext(test_dir, '3Rs', 'error_no_layers')
#     ctx.run(EXIT_BAD_CONFIG)
#     assert ctx.search_err("Missing .?layers.? list")
#     ctx.clean_up()


@pytest.mark.indep
def test_error_step_origin(test_dir):
    ctx = context.TestContext(test_dir, 'bom', 'error_step_origin')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Origin must be")
    ctx.clean_up()


@pytest.mark.indep
def test_error_step_min_distance(test_dir):
    ctx = context.TestContext(test_dir, 'bom', 'error_step_min_distance')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err(".?min_distance.? must be a number")
    ctx.clean_up()


@pytest.mark.indep
def test_filter_not_list(test_dir):
    ctx = context.TestContext(test_dir, PRJ, 'error_filter_not_list')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err(r"Option .?filters.? must be a list\(dict\) not `dict`")
    ctx.clean_up(keep_project=True)


@pytest.mark.indep
def test_filter_no_number_1(test_dir):
    ctx = context.TestContext(test_dir, PRJ, 'error_filter_no_number')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Empty option .?number.?")
    ctx.clean_up(keep_project=True)


@pytest.mark.indep
def test_filter_no_number_2(test_dir):
    ctx = context.TestContext(test_dir, PRJ, 'error_filter_no_number_2')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Missing .?error.?")
    ctx.clean_up(keep_project=True)


@pytest.mark.indep
def test_filter_no_regex_1(test_dir):
    ctx = context.TestContext(test_dir, PRJ, 'error_filter_no_regex')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Empty option .?regex.?")
    ctx.clean_up(keep_project=True)


@pytest.mark.indep
def test_filter_wrong_entry(test_dir):
    ctx = context.TestContext(test_dir, PRJ, 'error_filter_wrong_entry')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Unknown option .?numerito.?")
    ctx.clean_up(keep_project=True)


@pytest.mark.indep
def test_error_pre_list(test_dir):
    ctx = context.TestContext(test_dir, PRJ, 'error_pre_list')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Incorrect .?preflight.? section")
    ctx.clean_up(keep_project=True)


@pytest.mark.indep
def test_error_pre_unk(test_dir):
    ctx = context.TestContext(test_dir, PRJ, 'error_pre_unk')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Unknown preflight: .?run_drcs.?")
    ctx.clean_up(keep_project=True)


@pytest.mark.indep
def test_error_wrong_type_1(test_dir):
    """ run_drc = number """
    ctx = context.TestContext(test_dir, PRJ, 'error_pre_wrong_type_1')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("In preflight .?run_drc.?: (.*)not .?number.?")
    ctx.clean_up(keep_project=True)


@pytest.mark.indep
def test_error_wrong_type_2(test_dir):
    """ ignore_unconnected = string """
    ctx = context.TestContext(test_dir, PRJ, 'error_pre_wrong_type_2')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("In preflight .?ignore_unconnected.?: (.*)must be a boolean")
    ctx.clean_up(keep_project=True)


@pytest.mark.indep
def test_error_wrong_type_3(test_dir):
    """ run_erc = number """
    ctx = context.TestContext(test_dir, PRJ, 'error_pre_wrong_type_3')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("In preflight .?run_erc.?: (.*)must be any")
    ctx.clean_up(keep_project=True)


@pytest.mark.indep
def test_error_wrong_type_4(test_dir):
    """ update_xml = number """
    ctx = context.TestContextSCH(test_dir, 'bom', 'error_pre_wrong_type_4')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("In preflight .?update_xml.?: (.*)must be any of")
    ctx.clean_up(keep_project=True)


@pytest.mark.indep
def test_error_wrong_type_5(test_dir):
    """ check_zone_fills = number """
    ctx = context.TestContext(test_dir, PRJ, 'error_pre_wrong_type_5')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("In preflight .?check_zone_fills.?: (.*)must be a boolean")
    ctx.clean_up(keep_project=True)


@pytest.mark.indep
def test_error_yaml(test_dir):
    ctx = context.TestContext(test_dir, PRJ, 'error_yaml')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Error loading YAML")
    ctx.clean_up(keep_project=True)


@pytest.mark.indep
def test_out_not_list(test_dir):
    ctx = context.TestContext(test_dir, PRJ, 'error_out_not_list')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err(".?outputs.? must be a list")
    ctx.clean_up(keep_project=True)


@pytest.mark.indep
def test_unk_section(test_dir):
    ctx = context.TestContext(test_dir, PRJ, 'error_unk_section')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Unknown section .?bogus.? in config")
    ctx.clean_up(keep_project=True)


@pytest.mark.indep
def test_error_hpgl_pen_num(test_dir):
    ctx = context.TestContext(test_dir, PRJ, 'error_hpgl_pen_num')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Option .?pen_number.? outside its range")
    ctx.clean_up(keep_project=True)


@pytest.mark.indep
def test_error_bom_wrong_format(test_dir):
    ctx = context.TestContext(test_dir, PRJ, 'error_bom_wrong_format')
    ctx.run(EXIT_BAD_CONFIG, no_board_file=True, extra=['-e', os.path.join(ctx.get_board_dir(), 'bom'+context.KICAD_SCH_EXT)])
    assert ctx.search_err("Option .?format.? must be any of")
    ctx.clean_up(keep_project=True)


@pytest.mark.indep
def test_error_bom_column(test_dir, monkeypatch):
    ctx = context.TestContext(test_dir, PRJ, 'error_bom_column')
    with monkeypatch.context() as m:
        m.setenv("LANG", "")
        ctx.run(EXIT_BAD_CONFIG, no_board_file=True, extra=['-e', os.path.join(ctx.get_board_dir(),
                'bom'+context.KICAD_SCH_EXT)])
    assert ctx.search_err("Invalid column name .?Impossible.?")
    ctx.clean_up(keep_project=True)


@pytest.mark.indep
def test_error_bom_no_columns(test_dir):
    ctx = context.TestContext(test_dir, PRJ, 'error_bom_column')
    ctx.run(EXIT_BAD_CONFIG, no_board_file=True, extra=['-e', os.path.join(ctx.get_board_dir(),
            'bom_no_xml'+context.KICAD_SCH_EXT)])
    assert ctx.search_err("can't verify the field names")
    ctx.clean_up(keep_project=True)


@pytest.mark.indep
def test_error_bom_no_field(test_dir):
    ctx = context.TestContext(test_dir, PRJ, 'error_bom_no_field')
    ctx.run(EXIT_BAD_CONFIG, no_board_file=True, extra=['-e', os.path.join(ctx.get_board_dir(),
            'fail-erc'+context.KICAD_SCH_EXT)])
    assert ctx.search_err("Missing or empty .?field.?")
    ctx.clean_up(keep_project=True)


@pytest.mark.indep
def test_error_wrong_boolean(test_dir):
    ctx = context.TestContext(test_dir, PRJ, 'error_wrong_boolean')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err(".?exclude_edge_layer.? must be a boolean")
    ctx.clean_up(keep_project=True)


@pytest.mark.indep
def test_error_gerber_precision(test_dir):
    ctx = context.TestContext(test_dir, PRJ, 'error_gerber_precision')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err(".?gerber_precision.? must be any of")
    ctx.clean_up(keep_project=True)


@pytest.mark.indep
def test_error_wrong_drill_marks_1(test_dir):
    ctx = context.TestContext(test_dir, PRJ, 'error_wrong_drill_marks')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err(r"Option `drill_marks` must be any of \['none', 'small', 'full'\] not `bogus`")
    ctx.clean_up(keep_project=True)


@pytest.mark.indep
def test_error_print_pcb_no_layer(test_dir):
    prj = 'bom'
    ctx = context.TestContext(test_dir, prj, 'error_print_pcb_no_layer')
    ctx.run()  # EXIT_BAD_CONFIG Now allowed
    assert ctx.search_err("No layers specified for")
    ctx.clean_up()


@pytest.mark.indep
def test_error_color(test_dir):
    ctx = context.TestContext(test_dir, 'bom', 'error_color')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Invalid color for .?board.?")
    ctx.clean_up()


@pytest.mark.indep
def test_wrong_global(test_dir):
    ctx = context.TestContext(test_dir, 'bom', 'error_wrong_global')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Incorrect .?global.? section")
    ctx.clean_up()


@pytest.mark.indep
def test_goutput_not_string(test_dir):
    ctx = context.TestContext(test_dir, 'bom', 'error_goutput_not_string')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Option .?output.? must be a string")
    ctx.clean_up()


@pytest.mark.indep
def test_unk_global(test_dir):
    ctx = context.TestContext(test_dir, 'bom', 'error_unk_global')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Unknown global option")
    ctx.clean_up()


@pytest.mark.indep
def test_error_int_bom_no_field(test_dir):
    ctx = context.TestContextSCH(test_dir, 'links', 'error_int_bom_no_field')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Missing or empty `field` in columns list")
    ctx.clean_up()


@pytest.mark.indep
def test_error_int_bom_miss_logo(test_dir):
    ctx = context.TestContextSCH(test_dir, 'links', 'error_int_bom_miss_logo')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Missing logo file")
    ctx.clean_up()


@pytest.mark.indep
def test_error_int_bom_miss_style(test_dir):
    ctx = context.TestContextSCH(test_dir, 'links', 'error_int_bom_miss_style')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Missing style file")
    ctx.clean_up()


@pytest.mark.indep
def test_error_int_bom_unknown_style(test_dir):
    ctx = context.TestContextSCH(test_dir, 'links', 'error_int_bom_unknown_style')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Unknown style .?bogus.?")
    ctx.clean_up()


@pytest.mark.indep
def test_error_int_bom_invalid_col(test_dir):
    ctx = context.TestContextSCH(test_dir, 'links', 'error_int_bom_invalid_col')
    ctx.run()
    assert ctx.search_err("Invalid column name")
    ctx.clean_up()


@pytest.mark.indep
def test_error_int_bom_logo_format(test_dir):
    ctx = context.TestContextSCH(test_dir, 'links', 'error_int_bom_logo_format')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Only PNG images are supported for the logo")
    ctx.clean_up()


@pytest.mark.indep
def test_error_var_no_name(test_dir):
    ctx = context.TestContextSCH(test_dir, 'links', 'error_var_no_name')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Variant needs a name in:")
    ctx.clean_up()


@pytest.mark.indep
def test_error_var_empty_name(test_dir):
    ctx = context.TestContextSCH(test_dir, 'links', 'error_var_empty_name')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Variant needs a name in:")
    ctx.clean_up()


@pytest.mark.indep
def test_error_var_wrong_type(test_dir):
    ctx = context.TestContextSCH(test_dir, 'links', 'error_var_wrong_type')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Unknown variant type")
    ctx.clean_up()


@pytest.mark.indep
def test_error_var_no_type(test_dir):
    ctx = context.TestContextSCH(test_dir, 'links', 'error_var_no_type')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Variant (.*) needs a type")
    ctx.clean_up()


@pytest.mark.indep
def test_error_var_empty_type(test_dir):
    ctx = context.TestContextSCH(test_dir, 'links', 'error_var_empty_type')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Variant (.*) needs a type")
    ctx.clean_up()


@pytest.mark.indep
def test_error_var_no_list(test_dir):
    ctx = context.TestContextSCH(test_dir, 'links', 'error_var_no_list')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err(".?variants.? must be a list")
    ctx.clean_up()


@pytest.mark.indep
def test_error_fil_no_list(test_dir):
    ctx = context.TestContextSCH(test_dir, 'links', 'error_fil_no_list')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err(".?filters.? must be a list")
    ctx.clean_up()


@pytest.mark.indep
def test_error_fil_unknown(test_dir):
    ctx = context.TestContextSCH(test_dir, 'links', 'error_fil_unknown')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Unknown filter (.*) used for ")
    ctx.clean_up()


@pytest.mark.indep
def test_error_var_unknown(test_dir):
    ctx = context.TestContextSCH(test_dir, 'links', 'error_unk_variant')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Unknown variant name")
    ctx.clean_up()


@pytest.mark.indep
def test_error_wrong_fil_name(test_dir):
    ctx = context.TestContextSCH(test_dir, 'links', 'error_wrong_fil_name')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Filter names starting with (.*) are reserved")
    ctx.clean_up()


@pytest.mark.indep
def test_error_pcbdraw_comp_key(test_dir):
    ctx = context.TestContext(test_dir, 'bom', 'error_pcbdraw_comp_key')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Option .?show_components.? must be any of")
    ctx.clean_up()


@pytest.mark.indep
def test_error_rot_not_two(test_dir):
    ctx = context.TestContext(test_dir, 'bom', 'error_rot_not_two')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Each regex/angle pair must contain exactly two values")
    ctx.clean_up()


@pytest.mark.indep
def test_error_rot_not_number(test_dir):
    ctx = context.TestContext(test_dir, 'bom', 'error_rot_not_number')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("The second value in the regex/angle pairs must be a number")
    ctx.clean_up()


@pytest.mark.indep
def test_error_rot_no_rotations(test_dir):
    ctx = context.TestContext(test_dir, 'bom', 'error_rot_no_rotations')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("No rotations and/or offsets provided")
    ctx.clean_up()


@pytest.mark.indep
def test_error_makefile_wrong_out(test_dir):
    ctx = context.TestContext(test_dir, 'bom', 'error_makefile_wrong_out')
    ctx.run(WRONG_ARGUMENTS)
    assert ctx.search_err("Unknown output `position` selected in")
    ctx.clean_up()


@pytest.mark.indep
def test_error_no_column_id(test_dir):
    ctx = context.TestContext(test_dir, 'bom', 'error_no_column_id')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Missing or empty `id` in columns list")
    ctx.clean_up()


@pytest.mark.indep
def test_error_aggregate_no_file(test_dir):
    ctx = context.TestContext(test_dir, 'bom', 'error_aggregate_no_file')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Missing or empty `file` in aggregate list")
    ctx.clean_up()


@pytest.mark.indep
def test_error_aggregate_miss_file(test_dir):
    yaml = 'error_aggregate_miss_file'
    if context.ki6():
        yaml += '_k6'
    ctx = context.TestContext(test_dir, 'bom', yaml, '')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Missing `dummy`")
    ctx.clean_up()


@pytest.mark.indep
def test_error_wrong_import_type(test_dir):
    ctx = context.TestContext(test_dir, PRJ, 'error_wrong_import_type')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err(r"Incorrect `import` section \(must be a list\)")
    ctx.clean_up(keep_project=True)


@pytest.mark.indep
def test_error_import_not_str(test_dir):
    ctx = context.TestContext(test_dir, PRJ, 'error_import_not_str')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err(r"`import` items must be strings")
    ctx.clean_up(keep_project=True)


@pytest.mark.indep
def test_error_import_miss_file(test_dir):
    ctx = context.TestContext(test_dir, PRJ, 'error_import_miss_file')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err(r"issing import file")
    ctx.clean_up(keep_project=True)


@pytest.mark.indep
def test_error_import_no_outputs(test_dir):
    ctx = context.TestContext(test_dir, PRJ, 'error_import_no_outputs')
    ctx.run()
    assert ctx.search_err(r"No outputs found in `(.*)drc.kibot.yaml`")
    ctx.clean_up(keep_project=True)


@pytest.mark.indep
def test_same_name_1(test_dir):
    """ 2 outputs with the same name in the same file """
    ctx = context.TestContext(test_dir, PRJ, 'error_same_name_1')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err(r"Output name `position` already defined")
    ctx.clean_up(keep_project=True)


@pytest.mark.indep
def test_same_name_2(test_dir):
    """ Using import, but the 2nd is in the main file """
    ctx = context.TestContext(test_dir, PRJ, 'error_same_name_2')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err(r"Output name `position` already defined")
    ctx.clean_up(keep_project=True)


@pytest.mark.indep
def test_same_name_3(test_dir):
    """ Using import and the 2nd is from the import """
    ctx = context.TestContext(test_dir, PRJ, 'error_same_name_3')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err(r"Output name `position` already defined, while importing from")
    ctx.clean_up(keep_project=True)


@pytest.mark.indep
def test_extends_1(test_dir):
    """ Extend an undefined output """
    ctx = context.TestContext(test_dir, PRJ, 'error_extends_1')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err(r"In section 'position_mine' \(position\): Unknown output `position2` in `extends`")
    ctx.clean_up(keep_project=True)


@pytest.mark.indep
def test_pre_list_instead_of_dict(test_dir):
    """ Extend an undefined output """
    ctx = context.TestContext(test_dir, PRJ, 'error_pre_list_instead_of_dict_issue_360')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err(r"must be a dict(.*)list")
    ctx.clean_up(keep_project=True)


@pytest.mark.indep
def test_import_not_list(test_dir):
    """ Import preflights, but give a number """
    ctx = context.TestContext(test_dir, PRJ, 'error_import_not_list')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err(r"`preflights` must be a string or a list")
    ctx.clean_up(keep_project=True)


@pytest.mark.indep
def test_import_item_not_str(test_dir):
    """ Import preflights, but give a number in the list """
    ctx = context.TestContext(test_dir, PRJ, 'error_import_item_not_str')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err(r"`preflights` items must be strings")
    ctx.clean_up(keep_project=True)


@pytest.mark.indep
def test_import_defs_not_dict(test_dir):
    """ Import definitions, but not a dict """
    ctx = context.TestContext(test_dir, PRJ, 'error_import_defs_not_dict')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err(r"definitions must be a dict")
    ctx.clean_up(keep_project=True)


@pytest.mark.indep
def test_import_unk_entry(test_dir):
    """ Import unknown entry (pre-flight) """
    ctx = context.TestContext(test_dir, PRJ, 'error_import_unk_entry')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err(r"Unknown import entry `pre-flights` .* in .unnamed. import")
    ctx.clean_up(keep_project=True)


@pytest.mark.indep
def test_import_no_file(test_dir):
    """ Import no file name """
    ctx = context.TestContext(test_dir, PRJ, 'error_import_no_file')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err(r"`import` entry without `file`")
    ctx.clean_up(keep_project=True)


@pytest.mark.indep
def test_import_no_str_or_dict(test_dir):
    """ Import no file name """
    ctx = context.TestContext(test_dir, PRJ, 'error_import_no_str_or_dict')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err(r"`import` items must be strings or dicts")
    ctx.clean_up(keep_project=True)


@pytest.mark.indep
def test_download_datasheets_no_field(test_dir):
    """ Download datasheet no field specified """
    ctx = context.TestContext(test_dir, 'bom', 'error_download_datasheets_no_field')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err(r"Empty `field`")
    ctx.clean_up(keep_project=True)


@pytest.mark.indep
def test_download_datasheets_no_output(test_dir):
    """ Download datasheet no output specified """
    ctx = context.TestContext(test_dir, 'bom', 'error_download_datasheets_no_output')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err(r"Empty `output`")
    ctx.clean_up(keep_project=True)


@pytest.mark.indep
def test_line_width_min(test_dir):
    """ line_width < min """
    ctx = context.TestContext(test_dir, 'bom', 'error_wrong_line_width_min')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err(r"`line_width` outside its range ")
    ctx.clean_up(keep_project=True)


@pytest.mark.indep
def test_line_width_max(test_dir):
    """ line_width > max """
    ctx = context.TestContext(test_dir, 'bom', 'error_wrong_line_width_max')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err(r"`line_width` outside its range ")
    ctx.clean_up(keep_project=True)


@pytest.mark.indep
def test_error_empty_pth_id(test_dir):
    ctx = context.TestContext(test_dir, PRJ, 'error_empty_pth_id')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Empty option .pth_id.")
    ctx.clean_up(keep_project=True)


@pytest.mark.indep
def test_error_drill_wrong_column(test_dir):
    ctx = context.TestContext(test_dir, PRJ, 'error_drill_wrong_column')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Invalid column name .Bogus.")
    ctx.clean_up(keep_project=True)


@pytest.mark.indep
def test_drill_missing_field(test_dir):
    ctx = context.TestContext(test_dir, PRJ, 'error_drill_missing_field')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("Missing or empty .field. in columns list")
    ctx.clean_up(keep_project=True)


@pytest.mark.indep
def test_drill_no_columns(test_dir):
    ctx = context.TestContext(test_dir, PRJ, 'error_drill_no_columns')
    ctx.run(EXIT_BAD_CONFIG)
    assert ctx.search_err("No columns for the drill table")
    ctx.clean_up(keep_project=True)
