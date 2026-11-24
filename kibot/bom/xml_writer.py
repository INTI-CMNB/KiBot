# -*- coding: utf-8 -*-
# Copyright (c) 2020-2022 Salvador E. Tropea
# Copyright (c) 2020-2022 Instituto Nacional de Tecnología Industrial
# Copyright (c) 2016-2020 Oliver Henry Walters (@SchrodingersGat)
# License: MIT
# Project: KiBot (formerly KiPlot)
# Adapted from: https://github.com/SchrodingersGat/KiBoM
# Contributors: Geoffrey Hunter (@gbmhunter)
"""
XML Writer: Generates an XML BoM file.
"""
from xml.etree import ElementTree
from xml.dom import minidom
from typing import Sequence


def write_xml(filename, groups, headings, head_names: Sequence[str], cfg) -> bool:
    """
    Write BoM out to an XML file
    filename = path to output file (must be a .csv, .txt or .tsv file)
    groups = [list of ComponentGroup groups]
    headings = [list of headings to search for data in the BoM file]
    head_names = [list of headings to display in the BoM file]
    cfg = BoMOptions object with all the configuration
    """
    attrib = {}
    attrib['PCB_Variant'] = cfg.variant.name if cfg.variant else 'default'
    attrib['KiCad_Version'] = cfg.kicad_version
    attrib['Component_Groups'] = str(cfg.n_groups)
    attrib['Component_Count'] = str(cfg.total_str)
    attrib['Fitted_Components'] = str(cfg.fitted_str)
    attrib['Number_of_PCBs'] = str(cfg.number)
    attrib['Total_Components'] = str(cfg.n_build)
    if len(cfg.aggregate) == 1:
        prj = cfg.aggregate[0]
        attrib['Schematic_Source'] = prj.name
        attrib['Schematic_Revision'] = prj.sch.revision
        attrib['Schematic_Date'] = prj.sch.date
    else:
        for n, prj in enumerate(cfg.aggregate):
            attrib['Schematic{}_Source'.format(n)] = prj.name
            attrib['Schematic{}_Revision'.format(n)] = prj.sch.revision
            attrib['Schematic{}_Date'.format(n)] = prj.sch.date
            attrib['Schematic{}_ID'.format(n)] = prj.ref_id
            attrib['Component_Groups{}'.format(n)] = str(prj.comp_groups)
            attrib['Component_Count{}'.format(n)] = str(prj.total_str)
            attrib['Fitted_Components{}'.format(n)] = str(prj.fitted_str)
            attrib['Number_of_PCBs{}'.format(n)] = str(prj.number)
            attrib['Total_Components{}'.format(n)] = str(prj.comp_build)
    xml = ElementTree.Element('KiCad_BOM', attrib=attrib, encoding='utf-8')
    for group in groups:
        if cfg.ignore_dnf and not group.is_fitted():
            continue
        row = group.get_row(headings)
        attrib = {}
        for i, h in enumerate(head_names):
            # Adapt the column name to a valid XML attribute name
            h = h.replace(' ', '_')
            h = h.replace('/', '_')
            h = h.replace('"', '')
            h = h.replace("'", '')
            h = h.replace('#', '_num')
            attrib[h] = str(row[i])
        ElementTree.SubElement(xml, "group", attrib=attrib)

    with open(filename, "wb") as output:
        out = ElementTree.tostring(xml, encoding="utf-8")
        reparsed = minidom.parseString(out.decode('utf-8'))
        output.write(reparsed.toprettyxml(indent="\t", encoding="utf-8"))

    return True
