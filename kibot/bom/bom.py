# -*- coding: utf-8 -*-
# Copyright (c) 2020-2023 Salvador E. Tropea
# Copyright (c) 2020-2023 Instituto Nacional de Tecnología Industrial
# Copyright (c) 2016-2020 Oliver Henry Walters (@SchrodingersGat)
# License: MIT
# Project: KiBot (formerly KiPlot)
# Adapted from: https://github.com/SchrodingersGat/KiBoM
# Contributors: Kenny Huynh (@hkennyv)
"""
All the logic to convert a list of components into the rows and columns used to create the BoM.
"""
import locale
from copy import deepcopy
from math import ceil
from .units import compare_values, comp_match
from .bom_writer import write_bom
from .columnlist import ColumnList
from ..misc import DNF, W_FIELDCONF, W_MISSFPINFO, W_NOBOMOPS
from ..gs import GS
from .. import log

logger = log.get_logger()
# RV == Resistor Variable or Varistor
# RN == Resistor 'N'(Pack)
# RT == Thermistor
RLC_PREFIX = {'R', 'L', 'C', 'RV', 'RN', 'RT'}


def compare_value(c1, c2, cfg):
    """ Compare the value of two components """
    c1_value = c1.value.strip().lower()
    c2_value = c2.value.strip().lower()
    # '~' is the same as empty for KiCad
    if c1_value == '~':
        c1_value = ''
    if c2_value == '~':
        c2_value = ''
    # Simple string comparison
    if c1_value == c2_value:
        return True
    # Otherwise, perform a more complicated value comparison
    if compare_values(c1, c2):
        return True
    # Ignore value if both components are connectors
    # Note: Is common practice to use the "Value" field of connectors to denote its use.
    #       In this case the values won't match even when the connectors are equivalent.
    if cfg.group_connectors:
        if 'connector' in c1.lib.lower() and 'connector' in c2.lib.lower():
            return True
    # No match, return False
    return False


def compare_part_name(c1, c2, cfg):
    """ Determine if two parts have the same name, compute aliases """
    pn1 = c1.name.lower()
    pn2 = c2.name.lower()
    # Simple direct match
    if pn1 == pn2:
        return True
    # Compare part aliases e.g. "c" to "c_small"
    for alias in cfg.component_aliases:
        if pn1 in alias and pn2 in alias:
            return True
    return False


def compare_field(c1, c2, field, cfg):
    c1_value = c1.get_field_value(field).lower()
    c2_value = c2.get_field_value(field).lower()
    # If blank comparisons are allowed
    if (c1_value == "" or c2_value == "") and cfg.merge_blank_fields:
        return True
    if not cfg.merge_both_blank and c1_value == "" and c2_value == "":
        # Avoid merging two components with empty field
        return False
    return c1_value == c2_value


def compare_components(c1, c2, cfg):
    """ Determine if two parts are 'equal' """
    # 'fitted' value must be the same for both parts
    if not cfg.group_not_fitted and c1.fitted != c2.fitted:
        return False
    # 'fixed' value must be the same for both parts
    if c1.fixed != c2.fixed:
        return False
    # Do not group components
    if len(cfg.group_fields) == 0:
        return c1.ref == c2.ref
    # Check if the grouping fields match
    for i, field in enumerate(cfg.group_fields):
        # Check if we have a fallback
        field_alt = cfg.group_fields_fallbacks[i]
        if field_alt:
            # Check if we have an empty field
            c1_value = c1.get_field_value(field)
            c2_value = c2.get_field_value(field)
            if c1_value == "" or c2_value == "":
                # Try with the fallback field
                c1_value = c1.get_field_value(field_alt)
                c2_value = c2.get_field_value(field_alt)
                if c1_value != "" and c2_value != "":
                    # Compare using the fallback
                    field = field_alt
        # Perform special matches
        if field == ColumnList.COL_VALUE_L:
            if not compare_value(c1, c2, cfg):
                return False
        # Match part name
        elif field == ColumnList.COL_PART_L:
            if not compare_part_name(c1, c2, cfg):
                return False
        # Generic match
        elif not compare_field(c1, c2, field, cfg):
            return False
    return True


class Joiner:
    def __init__(self):
        self.stack = {}

    def add(self, P, N):
        if P not in self.stack:
            self.stack[P] = [((P, N), (P, N))]
            return
        stack = self.stack[P]
        S, E = stack[-1]
        if N == E[1] + 1:
            stack[-1] = (S, (P, N))
        else:
            stack.append(((P, N), (P, N)))

    def flush(self, sep, dash='-'):
        refstr = u''
        c = 0
        for pref in sorted(self.stack.keys()):
            stack = self.stack[pref]
            for Q in stack:
                if c != 0:
                    refstr += sep
                S, E = Q
                refstr += S[0]+str(S[1])
                if S == E:
                    # Only one element
                    c += 1
                elif S[1]+1 == E[1]:
                    # Two elements, I think this is better than pretending this is a real range
                    refstr += sep+E[0]+str(E[1])
                    c += 2
                else:
                    # A range
                    refstr += dash+E[0]+str(E[1])
                    c += 2
        return refstr


def _suffix_to_num(suffix):
    return 0 if suffix == '?' else int(suffix)


class ComponentGroup(object):
    """ A row in the BoM """
    def __init__(self, cfg):
        """ Initialize the group with no components, and default fields """
        self.components = []
        self.refs = {}
        self.cfg = cfg
        # Columns loaded from KiCad
        self.fields = {c.lower(): None for c in ColumnList.COLUMNS_DEFAULT}
        self.field_names = deepcopy(ColumnList.COLUMNS_DEFAULT)

    def match_component(self, c):
        """ Test if a given component fits in this group """
        return compare_components(c, self.components[0], self.cfg)

    def contains_component(self, c):
        """ Test if a given component is already contained in this group """
        return c.ref+c.project in self.refs

    def add_component(self, c):
        """ Add a component to the group.
            Avoid repetition, checks if suitable.
            Note: repeated components happens when the PCB is a panel """
        if not self.components:
            self.components.append(c)
            self.refs[c.ref+c.project] = c
        elif self.contains_component(c):
            return
        elif self.match_component(c):
            self.components.append(c)
            self.refs[c.ref+c.project] = c

    def round_qty(self, qty):
        if self.cfg.int_qtys:
            return int(ceil(qty))
        int_qty = int(qty)
        return int_qty if int_qty == qty else qty

    def get_count(self, project=None):
        if project is None:
            # Total components
            qty = sum((c.qty for c in self.components))
        else:
            # Only for the specified project
            qty = sum((c.qty for c in self.components if c.project == project))
        return self.round_qty(qty)

    def get_build_count(self):
        if not self.is_fitted():
            # Not fitted -> 0
            return 0
        if len(self.cfg.aggregate) == 1:
            # Just one project
            qty = sum((c.qty for c in self.components))*self.cfg.number
        else:
            # Multiple projects, count them using the number of board for each project
            qty = sum((self.cfg.qtys[c.project]*c.qty for c in self.components))
        return self.round_qty(qty)

    def get_sources(self):
        sources = {}
        for c in self.components:
            prj = c.project
            if self.cfg.source_by_id:
                prj = self.cfg.source_to_id[prj]
            if prj in sources:
                sources[prj] += c.qty
            else:
                sources[prj] = c.qty
        field = ''
        for prj in sorted(sources.keys()):
            n = sources[prj]
            if len(field):
                field += ' '
            field += prj+'('+str(n)+')'
        return field

    def is_fitted(self):
        # compare_components ensures all has the same status
        return self.components[0].fitted

    def is_fixed(self):
        # compare_components ensures all has the same status
        return self.components[0].fixed

    def is_smd(self):
        return self.components[0].smd

    def is_tht(self):
        return self.components[0].tht

    def get_field(self, field):
        field = field.lower()
        if field not in self.fields or not self.fields[field]:
            return ""
        return self.fields[field]

    def sort_components(self):
        """ Sort the components in correct order (by reference).
            First priority is the prefix, second the number (as integer) """
        self.components = sorted(self.components, key=lambda c: [c.ref_prefix, _suffix_to_num(c.ref_suffix)])

    def get_refs(self):
        """ Return a list of the components """
        return self.cfg._ref_separator.join([c.ref for c in self.components])

    def get_alt_refs(self):
        """ Alternative list of references using ranges """
        refs = ''
        for sch in self.cfg.aggregate:
            S = Joiner()
            for n in self.components:
                if n.project == sch.name:
                    S.add(n.ref_id+n.ref_prefix, _suffix_to_num(n.ref_suffix))
            result = S.flush(self.cfg._ref_separator, self.cfg._ref_range_separator)
            if result:
                if refs:
                    refs += self.cfg._ref_separator
                refs += result
        return refs

    def update_field(self, field, value, ref=None):
        """ Update a given field, concatenates existing values and informs a collision """
        if not value:
            return
        if self.cfg.tilde_is_empty and value == '~':
            return
        field_ori = field
        field = field.lower()
        if (field not in self.fields) or (not self.fields[field]):
            self.fields[field] = value
            self.field_names.append(field_ori)
        elif value.lower() in self.fields[field].lower():
            return
        else:
            # Config contains variant information, which is different for each component
            # Part can be one of the defined aliases
            if field not in self.cfg._no_conflict:
                logger.warning(W_FIELDCONF + "Field conflict: ({refs}) [{name}] : '{flds}' <- '{fld}' (in {ref})".format(
                    refs=self.get_refs(),
                    name=field,
                    flds=self.fields[field],
                    fld=value, ref=ref))
                if len(self.components) == 1:
                    logger.warning(W_FIELDCONF + "Most probably created by a renamed field")
            self.fields[field] += self.cfg.sep_for_merged + value

    def update_fields(self, conv, bottom_negative_x, x_origin, y_origin, angle_positive, footprint_populate_values,
                      footprint_type_values, uses_fp_info, usealt=False, right_digits=4):
        for c in self.components:
            for f, v in c.get_user_fields():
                self.update_field(f, v, c.ref)
            if self.cfg.merge_values:
                self.update_field(ColumnList.COL_VALUE_L, c.value, c.ref)
        # Update 'global' fields
        if usealt:
            self.fields[ColumnList.COL_REFERENCE_L] = self.get_alt_refs()
        else:
            self.fields[ColumnList.COL_REFERENCE_L] = self.get_refs()
        # Quantity
        self.fields[ColumnList.COL_QUANTITY_L] = self.fields[ColumnList.COL_GRP_QUANTITY_L] = str(self.get_count())
        self.total = self.get_build_count()
        self.fields[ColumnList.COL_GRP_BUILD_QUANTITY_L] = str(self.total)
        self.fields[ColumnList.COL_SOURCE_BOM_L] = self.get_sources()
        # Group status
        status = ' '
        if not self.is_fitted():
            status += '(DNF)'
        if self.is_fixed():
            status += '(DNC)'
        self.fields[ColumnList.COL_STATUS_L] = status
        # Component data
        comp = self.components[0]
        if not self.cfg.merge_values:
            self.fields[ColumnList.COL_VALUE_L] = comp.value
        self.fields[ColumnList.COL_PART_L] = comp.name
        self.fields[ColumnList.COL_PART_LIB_L] = comp.lib
        self.fields[ColumnList.COL_DATASHEET_L] = comp.datasheet
        self.fields[ColumnList.COL_FP_L] = comp.footprint
        if uses_fp_info and not comp.has_pcb_info and comp.on_board:
            logger.warning(W_MISSFPINFO+'Missing footprint information for {}'.format(comp.ref))
            if not GS.pcb_file:
                logger.warning(W_MISSFPINFO+'Please provide a PCB file')
        pos_x = (comp.footprint_x - x_origin) * conv
        if bottom_negative_x and comp.bottom:
            pos_x = -pos_x
        float_format = "{{:.{}f}}".format(right_digits) if right_digits else "{}"
        self.fields[ColumnList.COL_FP_X_L] = float_format.format(pos_x)
        self.fields[ColumnList.COL_FP_Y_L] = float_format.format(-(comp.footprint_y - y_origin) * conv)
        rot = comp.footprint_rot
        if angle_positive:
            rot = rot % 360
        self.fields[ColumnList.COL_FP_ROT_L] = float_format.format(rot)
        self.fields[ColumnList.COL_FP_SIDE_L] = "bottom" if comp.bottom else "top"
        type = 0
        if comp.tht:
            type = 1
        if comp.virtual:
            type = 2
        self.fields[ColumnList.COL_FP_TYPE_L] = footprint_type_values[type]
        if comp.smd:
            type = footprint_type_values[0]
        elif comp.tht:
            type = footprint_type_values[1]
        else:
            type = ''
        self.fields[ColumnList.COL_FP_TYPE_NV_L] = type
        self.fields[ColumnList.COL_FP_FIT_L] = footprint_populate_values[comp.fitted]
        self.fields[ColumnList.COL_FP_XS_L] = float_format.format(comp.footprint_w * conv)
        self.fields[ColumnList.COL_FP_YS_L] = float_format.format(comp.footprint_h * conv)
        self.fields[ColumnList.COL_FP_LIB_L] = comp.footprint_lib
        self.fields[ColumnList.COL_FP_FULL_L] = (comp.footprint_lib+':'+comp.footprint if comp.footprint_lib else
                                                 comp.footprint)
        self.fields[ColumnList.COL_SHEETPATH_L] = comp.sheet_path_h
        if not self.fields[ColumnList.COL_DESCRIPTION_L]:
            self.fields[ColumnList.COL_DESCRIPTION_L] = comp.desc
        self.fields[ColumnList.COL_NET_NAME_L] = comp.net_name
        self.fields[ColumnList.COL_NET_LABEL_L] = comp.net_name.split('/')[-1]
        self.fields[ColumnList.COL_NET_CLASS_L] = comp.net_class
        # KiCad attributes
        self.fields[ColumnList.COL_DNP_L] = self.solve_multiple_attributes('kicad_dnp', 'DNP')
        self.fields[ColumnList.COL_EXCLUDE_FROM_BOARD_L] = self.solve_multiple_attributes('on_board', 'Excluded from board',
                                                                                          invert=True)
        self.fields[ColumnList.COL_EXCLUDE_FROM_SIM_L] = self.solve_multiple_attributes('exclude_from_sim',
                                                                                        'Excluded from simulation',)

    def solve_multiple_attributes(self, attr, label, invert=False):
        positive = 0
        found = 0
        for c in self.components:
            if hasattr(c, attr):
                found += 1
                if getattr(c, attr):
                    positive += 1
        if not found:
            return 'Unknown'
        if positive != 0 and positive != len(self.components):
            return '-- mixed values --'
        return label if invert ^ positive != 0 else ''

    def get_row(self, columns):
        """ Return a dict of the KiCad data based on the supplied columns """
        row = []
        for key in columns:
            val = self.get_field(key)
            # Join fields (appending to current value)
            for join_l in self.cfg._join:
                # Each list is "target, source..." so we need at least 2 elements
                elements = len(join_l)
                target = join_l[0]
                if elements > 1 and target == key:
                    # Append data from the other fields
                    for source in join_l[1:]:
                        v = source.get_text(self.get_field)
                        if v:
                            val += v
            row.append(val)
        return row


def get_value_sort(comp, fallback_ref=False):
    """ Try to better sort R, L and C components """
    res = comp.value_sort
    if res:
        return res.get_sortable()
    if fallback_ref:
        return comp.ref_prefix + "{0:15d}".format(_suffix_to_num(comp.ref_suffix))
    return comp.value


def normalize_value(c, decimal_point, value):
    if c.value_sort is None:
        return value.strip()
    value = str(c.value_sort)
    if decimal_point:
        value = value.replace('.', decimal_point)
    return value


def compute_multiple_stats(cfg, groups):
    for sch in cfg.aggregate:
        sch.comp_total = sch.comp_total_smd = sch.comp_total_tht = 0
        sch.comp_fitted = sch.comp_fitted_smd = sch.comp_fitted_tht = 0
        sch.comp_build = 0
        sch.comp_groups = 0
        for g in groups:
            g_l = g.get_count(sch.name)
            if g_l:
                sch.comp_groups = sch.comp_groups+1
            sch.comp_total += g_l
            if g.is_smd():
                sch.comp_total_smd += g_l
            if g.is_tht():
                sch.comp_total_tht += g_l
            if g.is_fitted():
                sch.comp_fitted += g_l
                if g.is_smd():
                    sch.comp_fitted_smd += g_l
                if g.is_tht():
                    sch.comp_fitted_tht += g_l
        sch.comp_build = sch.comp_fitted*sch.number
        if cfg.debug_level > 1:
            logger.debug('Stats for {}: total {} fitted {} build {}'.
                         format(sch.name, sch.comp_total, sch.comp_fitted, sch.comp_build))


def group_components(cfg, components):
    groups = []
    # Iterate through each component, and test whether a group for these already exists
    for c in components:
        if not c.included:  # Skip components marked as excluded from BoM
            continue
        # Cache the value used to sort
        if cfg.parse_value and c.ref_prefix in RLC_PREFIX and c.value.lower() not in DNF:
            c.value_sort = comp_match(c.value, c.ref_prefix, c.ref, warn_extra=True)
        else:
            c.value_sort = None
        # Try to add the component to an existing group
        found = False
        for g in groups:
            if g.match_component(c):
                g.add_component(c)
                found = True
                break
        if not found:
            # Create a new group
            g = ComponentGroup(cfg)
            g.add_component(c)
            groups.append(g)
    # Now unify the data from the components of each group
    decimal_point = None
    if cfg.normalize_locale:
        decimal_point = locale.localeconv()['decimal_point']
        if decimal_point == '.':
            decimal_point = None
    # Determine if we need information from the PCB
    uses_fp_info = len(set(ColumnList.COLUMNS_FP_L).intersection({c.lower() for c in cfg._columns})) != 0
    # Coordinates origin for XYRS
    x_origin = 0.0
    y_origin = 0.0
    if cfg.use_aux_axis_as_origin:
        (x_origin, y_origin) = GS.get_aux_origin()
        logger.debug('Using auxiliary origin: x={} y={}'.format(x_origin, y_origin))
    # Process the groups
    for g in groups:
        # Sort the references within each group
        g.sort_components()
        # Fill the columns
        g.update_fields(cfg.conv_units, cfg.bottom_negative_x, x_origin, y_origin, cfg.angle_positive,
                        cfg.footprint_populate_values, cfg.footprint_type_values, uses_fp_info, cfg._use_alt, cfg.right_digits)
        if cfg.normalize_values:
            g.fields[ColumnList.COL_VALUE_L] = normalize_value(g.components[0], decimal_point,
                                                               g.fields[ColumnList.COL_VALUE_L])
    # Sort the groups
    sort_style = cfg.sort_style
    if sort_style == 'kicad_bom':
        bom_settings = GS.load_pro_bom_settings()
        sort_asc = bom_settings.get("sort_asc", True)
        sort_field = bom_settings.get("sort_field", '')
        if not sort_field:
            logger.warning(W_NOBOMOPS+'No KiCad BoM options available, sorting using `type_value`')
            sort_style = 'type_value'
    elif sort_style == 'field':
        sort_asc = cfg.sort_ascending
        sort_field = cfg.sort_field
    if sort_style == 'type_value':
        # First priority is the Type of component (e.g. R?, U?, L?)
        # Second is the value
        groups = sorted(groups, key=lambda g: [g.components[0].ref_prefix, get_value_sort(g.components[0])],
                        reverse=not cfg.sort_ascending)
    elif sort_style == 'type_value_ref':
        # First priority is the Type of component (e.g. R?, U?, L?)
        # Second is the value, but if we don't have a value we use the reference
        groups = sorted(groups, key=lambda g: [g.components[0].ref_prefix, get_value_sort(g.components[0], True)],
                        reverse=not cfg.sort_ascending)
    elif sort_style == 'ref':
        groups = sorted(groups, key=lambda g: [g.components[0].ref_prefix, _suffix_to_num(g.components[0].ref_suffix)],
                        reverse=not cfg.sort_ascending)
    else:  # kicad_bom and field
        logger.debug(f'Sorting using KiCad definition, field: `{sort_field}`, ascending: {sort_asc}')
        groups = sorted(groups, key=lambda g: g.components[0].get_field_value(sort_field, lower=True), reverse=not sort_asc)
    # Enumerate the groups and compute stats
    n_total = n_total_smd = n_total_tht = 0
    n_fitted = n_fitted_smd = n_fitted_tht = 0
    n_build = 0
    c = 1
    dnf = 1
    cfg.n_groups = len(groups)
    for g in groups:
        is_fitted = g.is_fitted()
        if cfg.ignore_dnf and not is_fitted:
            g.update_field(ColumnList.COL_ROW_NUMBER, str(dnf))
            g.update_field(ColumnList.COL_ITEM_NUMBER, str(dnf))
            dnf += 1
        else:
            g.update_field(ColumnList.COL_ROW_NUMBER, str(c))
            g.update_field(ColumnList.COL_ITEM_NUMBER, str(c))
            c += 1
        # Stats
        g_l = g.get_count()
        n_total += g_l
        n_total_smd += g_l*g.is_smd()
        n_total_tht += g_l*g.is_tht()
        if is_fitted:
            n_fitted += g_l
            n_fitted_smd += g_l*g.is_smd()
            n_fitted_tht += g_l*g.is_tht()
            n_build += g.total
    cfg.n_total = n_total
    cfg.n_total_smd = n_total_smd
    cfg.n_total_tht = n_total_tht
    cfg.n_fitted = n_fitted
    cfg.n_fitted_smd = n_fitted_smd
    cfg.n_fitted_tht = n_fitted_tht
    cfg.n_build = n_build
    if cfg.debug_level > 1:
        logger.debug('Global stats: total {} fitted {} build {}'.format(n_total, n_fitted, n_build))
    # Compute stats for multiple schematics
    if len(cfg.aggregate) > 1:
        compute_multiple_stats(cfg, groups)
    return groups


def smd_tht(cfg, tot, smd, tht):
    if cfg.count_smd_tht:
        return "{} ({} SMD/ {} THT)".format(tot, smd, tht)
    return tot


def do_bom(file_name, ext, comps, cfg):
    # Group components according to group_fields
    groups = group_components(cfg, comps)
    # Create the BoM
    logger.debug("Saving BOM File: "+file_name)
    number = cfg.number
    cfg.number = sum((prj.number for prj in cfg.aggregate))
    # Pre-format the total and fitted strings
    cfg.total_str = smd_tht(cfg, cfg.n_total, cfg.n_total_smd, cfg.n_total_tht)
    cfg.fitted_str = smd_tht(cfg, cfg.n_fitted, cfg.n_fitted_smd, cfg.n_fitted_tht)
    if len(cfg.aggregate) > 1:
        for prj in cfg.aggregate:
            prj.total_str = smd_tht(cfg, prj.comp_total, prj.comp_total_smd, prj.comp_total_tht)
            prj.fitted_str = smd_tht(cfg, prj.comp_fitted, prj.comp_fitted_smd, prj.comp_fitted_tht)
    # Create the BoM
    write_bom(file_name, ext, groups, cfg._columns, cfg)
    cfg.number = number
