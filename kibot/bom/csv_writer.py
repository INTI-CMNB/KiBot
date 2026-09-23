# -*- coding: utf-8 -*-
# Copyright (c) 2020-2022 Salvador E. Tropea
# Copyright (c) 2020-2022 Instituto Nacional de Tecnología Industrial
# Copyright (c) 2016-2020 Oliver Henry Walters (@SchrodingersGat)
# License: MIT
# Project: KiBot (formerly KiPlot)
# Adapted from: https://github.com/SchrodingersGat/KiBoM
"""
CSV Writer: Generates a CSV, TSV, TXT or HRTXT BoM file.
            Can also mimic KiCad BoM output
"""
from ..gs import GS
import csv
from .. import log

logger = log.get_logger()
ALIGN_CODE = {'right': '>', 'left': '<', 'center': '^'}


class HRTXT(object):
    def __init__(self, fh, delimiter=',', hsep='-', align='left'):
        self.f = fh
        self.delimiter = delimiter
        self.hsep = hsep
        self.cols_w = []
        self.data = []
        self.align = ALIGN_CODE[align]

    def writerow(self, row):
        self.data.append(row)
        for c, d in enumerate(row):
            d = str(d)
            l_cell = len(d)
            try:
                self.cols_w[c] = max(self.cols_w[c], l_cell)
            except IndexError:
                self.cols_w.append(l_cell)

    def add_sep(self):
        self.data.append(None)

    def flush(self):
        self.col_fmt = []
        for ln in self.cols_w:
            self.col_fmt.append("{:"+self.align+str(ln)+"s}")
        prev = None
        for r in self.data:
            # Is a separator?
            if r is None:
                # Skip if we don't want separators
                if not self.hsep:
                    continue
                # Create a fake row using the separator
                r = []
                for _, ln in zip(prev, self.cols_w):
                    r.append(self.hsep*ln)
            if len(r):
                self.f.write(self.delimiter)
            for cell, fmt in zip(r, self.col_fmt):
                cell = str(cell)
                self.f.write(fmt.format(cell.replace("\n", self.delimiter)))
                self.f.write(self.delimiter)
            self.f.write("\n")
            prev = r


def write_stats(writer, cfg, ops, write_sep):
    if len(cfg.aggregate) == 1:
        # Only one project
        if not ops.hide_pcb_info:
            prj = cfg.aggregate[0]
            writer.writerow(["Project info:"])
            write_sep()
            writer.writerow(["Schematic:", prj.name])
            writer.writerow(["Variant:", cfg.variant.name if cfg.variant else 'default'])
            writer.writerow(["Revision:", prj.sch.revision])
            writer.writerow(["Date:", prj.sch.date])
            writer.writerow(["KiCad Version:", cfg.kicad_version])
            write_sep()
        if not ops.hide_stats_info:
            writer.writerow(["Statistics:"])
            write_sep()
            writer.writerow(["Component Groups:", cfg.n_groups])
            writer.writerow(["Component Count:", cfg.total_str])
            writer.writerow(["Fitted Components:", cfg.fitted_str])
            writer.writerow(["Number of PCBs:", cfg.number])
            writer.writerow(["Total Components:", cfg.n_build])
            write_sep()
    else:
        # Multiple projects
        if not ops.hide_pcb_info:
            prj = cfg.aggregate[0]
            writer.writerow(["Project info:"])
            write_sep()
            writer.writerow(["Variant:", cfg.variant.name if cfg.variant else 'default'])
            writer.writerow(["KiCad Version:", cfg.kicad_version])
            write_sep()
        if not ops.hide_stats_info:
            writer.writerow(["Global statistics:"])
            write_sep()
            writer.writerow(["Component Groups:", cfg.n_groups])
            writer.writerow(["Component Count:", cfg.total_str])
            writer.writerow(["Fitted Components:", cfg.fitted_str])
            writer.writerow(["Number of PCBs:", cfg.number])
            writer.writerow(["Total Components:", cfg.n_build])
            write_sep()
        # Individual stats
        for prj in cfg.aggregate:
            if not ops.hide_pcb_info:
                writer.writerow(["Project info:", prj.sch.title])
                write_sep()
                writer.writerow(["Schematic:", prj.name])
                writer.writerow(["Revision:", prj.sch.revision])
                writer.writerow(["Date:", prj.sch.date])
                if prj.sch.company:
                    writer.writerow(["Company:", prj.sch.company])
                if prj.ref_id:
                    writer.writerow(["ID", prj.ref_id])
                write_sep()
            if not ops.hide_stats_info:
                writer.writerow(["Statistics:", prj.sch.title])
                write_sep()
                writer.writerow(["Component Groups:", prj.comp_groups])
                writer.writerow(["Component Count:", prj.total_str])
                writer.writerow(["Fitted Components:", prj.fitted_str])
                writer.writerow(["Number of PCBs:", prj.number])
                writer.writerow(["Total Components:", prj.comp_build])
                write_sep()


def dummy():
    pass


def process_special_chars(row, keep_line_breaks, keep_tabs):
    if keep_line_breaks and keep_tabs:
        return
    for index in range(len(row)):
        if not keep_line_breaks:
            row[index] = row[index].replace('\n', '')
        if not keep_tabs:
            row[index] = row[index].replace('\t', '')


def write_csv(filename, ext, groups, headings, head_names, cfg):
    """
    Write BoM out to a CSV file
    filename = path to output file (must be a .csv, .txt or .tsv file)
    groups = [list of ComponentGroup groups]
    headings = [list of headings to search for data in the BoM file]
    head_names = [list of headings to display in the BoM file]
    cfg = BoMOptions object with all the configuration
    """
    is_hrtxt = ext == "hrtxt"
    is_kicad = ext == "kicad"

    ops = cfg.hrtxt if is_hrtxt else cfg.csv
    # KiCad BoM options
    kops = GS.load_pro_bom_fmt_settings() if is_kicad else None
    # Delimiter is assumed from file extension
    # Override delimiter if separator specified
    if is_hrtxt or (ext == "csv" and ops.separator):
        delimiter = ops.separator
    elif is_kicad:
        delimiter = kops.get("field_delimiter", ",")
    else:
        if ext == "csv":
            delimiter = ","
        elif ext == "tsv" or ext == "txt":
            delimiter = "\t"

    quoting = csv.QUOTE_MINIMAL
    if is_kicad or (hasattr(ops, 'quote_all') and ops.quote_all):
        quoting = csv.QUOTE_ALL
    if is_kicad:
        quotechar = kops.get("string_delimiter", '"')
        # KiCad has a couple of options to remove \t and \n
        keep_line_breaks = kops.get("keep_line_breaks", False)
        keep_tabs = kops.get("keep_tabs", False)
    elif hasattr(ops, 'string_delimiter'):
        quotechar = ops.string_delimiter
        keep_line_breaks = ops.keep_line_breaks
        keep_tabs = ops.keep_tabs
    else:
        quotechar = '"'
        keep_line_breaks = True
        keep_tabs = True

    # KiCad has a couple of options to remove \t and \n
    keep_line_breaks = kops.get("keep_line_breaks", False) if is_kicad else True
    keep_tabs = kops.get("keep_tabs", False) if is_kicad else True

    with open(filename, "wt", newline='') as f:
        if is_hrtxt:
            writer = HRTXT(f, delimiter=delimiter, hsep=ops.header_sep, align=ops.justify)
        else:
            writer = csv.writer(f, delimiter=delimiter, lineterminator="\n", quoting=quoting, quotechar=quotechar)
        write_sep = writer.add_sep if is_hrtxt else dummy
        # Headers
        if not ops.hide_header or is_kicad:
            writer.writerow(head_names)
            write_sep()
        # Body
        for group in groups:
            if cfg.ignore_dnf and not group.is_fitted():
                continue
            row = group.get_row(headings)
            process_special_chars(row, keep_line_breaks, keep_tabs)
            writer.writerow(row)
        write_sep()
        # PCB info
        if not (ops.hide_pcb_info and ops.hide_stats_info) and not is_kicad:
            # Add some blank rows
            for _ in range(5):
                writer.writerow([])
            # The info
            write_stats(writer, cfg, ops, write_sep)
        if is_hrtxt:
            writer.flush()

    return True
