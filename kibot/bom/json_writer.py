# -*- coding: utf-8 -*-
# Copyright (c) 2026 Salvador E. Tropea
# Copyright (c) 2026 Instituto Nacional de Tecnología Industrial
# License: AGPL
# Project: KiBot (formerly KiPlot)
"""
JSON Writer: Generates a JSON BoM file.
"""
import base64
import json
import os
from shutil import copy2
import urllib.parse

from .columnlist import ColumnList
from .html_writer import cell_class
from .kibot_logo import KIBOT_LOGO
from .. import log
logger = log.get_logger()


def write_stats(data, cfg):
    multi = len(cfg.aggregate) > 1
    stats = {}
    stats['variant'] = cfg.variant.name if cfg.variant else 'Default'
    stats['kicad_version'] = cfg.kicad_version
    stats['component_groups'] = cfg.n_groups
    stats['component_count'] = cfg.total_str
    stats['fitted_components'] = cfg.fitted_str
    stats['number_of_pcbs'] = cfg.number
    stats['total_components'] = cfg.n_build
    prjs = []
    for prj in cfg.aggregate:
        d = {}
        d['schematic'] = prj.name
        d['revision'] = prj.sch.revision
        d['date'] = prj.sch.date
        if prj.sch.company:
            d['company'] = prj.sch.company
        if prj.ref_id:
            d['id'] = prj.ref_id
        if multi:
            d['component_groups'] = prj.comp_groups
            d['component_count'] = prj.total_str
            d['fitted_components'] = prj.fitted_str
            d['number_of_pcbs'] = prj.number
            d['total_components'] = prj.comp_build
        prjs.append(d)
    stats['projects'] = prjs
    data['stats'] = stats


def write_json(filename, groups, headings, head_names, cfg):
    """
    Write BoM out to a JSON file
    filename = path to output file (should be a .json)
    groups = [list of ComponentGroup groups]
    headings = [list of headings to search for data in the BoM file]
    head_names = [list of headings to display in the BoM file]
    cfg = BoMOptions object with all the configuration
    """
    link_datasheet = -1
    if cfg.json.datasheet_as_link and cfg.json.datasheet_as_link in headings:
        link_datasheet = headings.index(cfg.json.datasheet_as_link)
    link_digikey = cfg.json.digikey_link
    link_mouser = cfg.json.mouser_link
    link_lcsc = cfg.json.lcsc_link
    hl_empty = cfg.json.highlight_empty

    data = {'title': cfg.json.title}
    write_stats(data, cfg)

    # Solve the logo
    if cfg.json.logo is not None:
        if cfg.json.logo:
            logo = os.path.basename(cfg.json.logo)
            dest = os.path.join(os.path.dirname(filename), logo)
            logger.debug(f"Copying logo `{cfg.json.logo}` -> `{dest}`")
            copy2(cfg.json.logo, dest)
        else:
            logo = 'kibot_logo.png'
            dest = os.path.join(os.path.dirname(filename), logo)
            logger.debug(f"Creating logo `{dest}`")
            with open(dest, "wb") as img:
                img.write(base64.b64decode(KIBOT_LOGO))
        data['logo'] = logo
        data['logo_width'] = cfg.json.logo_width

    # Headings and where the data came from
    data['headings'] = [{'name': h, 'class': cell_class(f)} for h, f in zip(head_names, headings)]

    # User defined strings
    if cfg.json.extra_info:
        data['extra_info'] = cfg.json.extra_info

    # We use this code twice (regular + DNF) so I encapsulated it in a function ... the Pythonic way
    def do_groups(dnf=False):
        rows = []
        for group in groups:
            if (cfg.ignore_dnf and not group.is_fitted()) != dnf:
                continue
            row = group.get_row(headings)
            if link_datasheet != -1:
                datasheet = group.get_field(ColumnList.COL_DATASHEET_L)
            cells = []
            for n, r in enumerate(row):
                cell = {'value': r}
                field = headings[n]
                #
                # Solve any link
                #
                # A link to Digi-Key?
                if link_digikey and field in link_digikey and r:
                    cell['link'] = 'https://www.digikey.com/en/products/result?keywords=' + urllib.parse.quote(r)
                if link_mouser and field in link_mouser and r:
                    cell['link'] = 'https://www.mouser.com/ProductDetail/' + r
                if link_lcsc and field in link_lcsc and r:
                    cell['link'] = 'https://www.lcsc.com/product-detail/' + r + '.html'
                # Link this column to the datasheet?
                if link_datasheet == n and datasheet.startswith('http') and r:
                    cell['link'] = datasheet
                #
                # Color hint
                #
                # Empty cell?
                if hl_empty and ((len(r) == 0 and field not in group.fields_with_tilde) or r.strip() == "~"):
                    cell['empty'] = True
                # Add the cell
                cells.append(cell)
            rows.append(cells)
        return rows
    # End of helper function "do_groups"

    data['rows'] = do_groups()
    # DNF component groups
    if cfg.json.generate_dnf and cfg.n_total != cfg.n_fitted:
        data['rows_dnf'] = do_groups(True)

    with open(filename, "wt") as output:
        text = json.dumps(data, sort_keys=True, indent=2)
        output.write(text)

    return True
