# -*- coding: utf-8 -*-
# Copyright (c) 2020-2026 Salvador E. Tropea
# Copyright (c) 2020-2026 Instituto Nacional de Tecnología Industrial
# Copyright (c) 2016-2020 Oliver Henry Walters (@SchrodingersGat)
# License: MIT
# Project: KiBot (formerly KiPlot)
# Adapted from: https://github.com/SchrodingersGat/KiBoM
"""
HTML Writer: Generates a HTML BoM file.
"""
from base64 import b64encode
import os
import urllib.parse
from .columnlist import ColumnList, BoMError
from .kibot_logo import KIBOT_LOGO, KIBOT_LOGO_W, KIBOT_LOGO_H
from ..misc import (read_png, STYLE_COMMON, TABLE_MODERN, TABLE_CLASSIC, HEAD_COLOR_R, HEAD_COLOR_R_L, HEAD_COLOR_G,
                    HEAD_COLOR_G_L, HEAD_COLOR_B, HEAD_COLOR_B_L)
from .. import log
logger = log.get_logger()


# JavaScript table sorter. Is floating around internet, i.e.:
# - Stack Overflow: https://stackoverflow.com/questions/61122696/addeventlistener-after-change-event
# - pimpmykicadbom: https://gitlab.com/antto/pimpmykicadbom
# - Table Generator: https://www.tablesgenerator.com/
SORT_CODE = ('<script charset="utf-8">\n'
             '  var TGSort = window.TGSort || function(n) {\n'
             '    "use strict";\n'
             '    function r(n) { return n ? n.length : 0 }\n'
             '    function t(n, t, e, o = 0) { for (e = r(n); o < e; ++o) t(n[o], o) }\n'
             '    function e(n) { return n.split("").reverse().join("") }\n'
             '    function o(n) {\n'
             '      var e = n[0];\n'
             '      return t(n, function(n) {\n'
             '        for (; !n.startsWith(e);) e = e.substring(0, r(e) - 1)\n'
             '      }), r(e)\n'
             '    }\n'
             '    function u(n, r, e = []) {\n'
             '      return t(n, function(n) {\n'
             '        r(n) && e.push(n)\n'
             '      }), e\n'
             '    }\n'
             '    var a = parseFloat;\n'
             '    function i(n, r) {\n'
             '      return function(t) {\n'
             '        var e = "";\n'
             '        return t.replace(n, function(n, t, o) {\n'
             '          return e = t.replace(r, "") + "." + (o || "").substring(1)\n'
             '        }), a(e)\n'
             '      }\n'
             '    }\n'
             r'    var s = i(/^(?:\s*)([+-]?(?:\d+)(?:,\d{3})*)(\.\d*)?$/g, /,/g),''\n'
             r'      c = i(/^(?:\s*)([+-]?(?:\d+)(?:\.\d{3})*)(,\d*)?$/g, /\./g);''\n'
             '    function f(n) {\n'
             '      var t = a(n);\n'
             '      return !isNaN(t) && r("" + t) + 1 >= r(n) ? t : NaN\n'
             '    }\n'
             '    function d(n) {\n'
             '      var e = [],\n'
             '        o = n;\n'
             '      return t([f, s, c], function(u) {\n'
             '        var a = [],\n'
             '          i = [];\n'
             '        t(n, function(n, r) {\n'
             '          r = u(n), a.push(r), r || i.push(n)\n'
             '        }), r(i) < r(o) && (o = i, e = a)\n'
             '      }), r(u(o, function(n) {\n'
             '        return n == o[0]\n'
             '      })) == r(o) ? e : []\n'
             '    }\n'
             '    function v(n) {\n'
             '      if ("TABLE" == n.nodeName) {\n'
             '        for (var a = function(r) {\n'
             '            var e, o, u = [],\n'
             '              a = [];\n'
             '            return function n(r, e) {\n'
             '              e(r), t(r.childNodes, function(r) {\n'
             '                n(r, e)\n'
             '              })\n'
             '            }(n, function(n) {\n'
             '              "TR" == (o = n.nodeName) ? (e = [], u.push(e), a.push(n)) : "TD" != o && "TH" != o || e.push(n)\n'  # noqa: E501
             '            }), [u, a]\n'
             '          }(), i = a[0], s = a[1], c = r(i), f = c > 1 && r(i[0]) < r(i[1]) ? 1 : 0, v = f + 1, p = i[f], h = r(p), l = [], g = [], N = [], m = v; m < c; ++m) {\n'  # noqa: E501
             '          for (var T = 0; T < h; ++T) {\n'
             '            r(g) < h && g.push([]);\n'
             '            var C = i[m][T],\n'
             '              L = C.textContent || C.innerText || "";\n'
             '            g[T].push(L.trim())\n'
             '          }\n'
             '          N.push(m - v)\n'
             '        }\n'
             '        t(p, function(n, t) {\n'
             '          l[t] = 0;\n'
             '          var a = n.classList;\n'
             '          a.add("tg-sort-header"), n.addEventListener("click", function() {\n'
             '            var n = l[t];\n'
             '            ! function() {\n'
             '              for (var n = 0; n < h; ++n) {\n'
             '                var r = p[n].classList;\n'
             '                r.remove("tg-sort-asc"), r.remove("tg-sort-desc"), l[n] = 0\n'
             '              }\n'
             '            }(), (n = 1 == n ? -1 : +!n) && a.add(n > 0 ? "tg-sort-asc" : "tg-sort-desc"), l[t] = n;\n'
             '            var i, f = g[t],\n'
             '              m = function(r, t) {\n'
             '                return n * f[r].localeCompare(f[t]) || n * (r - t)\n'
             '              },\n'
             '              T = function(n) {\n'
             '                var t = d(n);\n'
             '                if (!r(t)) {\n'
             '                  var u = o(n),\n'
             '                    a = o(n.map(e));\n'
             '                  t = d(n.map(function(n) {\n'
             '                    return n.substring(u, r(n) - a)\n'
             '                  }))\n'
             '                }\n'
             '                return t\n'
             '              }(f);\n'
             '            (r(T) || r(T = r(u(i = f.map(Date.parse), isNaN)) ? [] : i)) && (m = function(r, t) {\n'
             '              var e = T[r],\n'
             '                o = T[t],\n'
             '                u = isNaN(e),\n'
             '                a = isNaN(o);\n'
             '              return u && a ? 0 : u ? -n : a ? n : e > o ? n : e < o ? -n : n * (r - t)\n'
             '            });\n'
             '            var C, L = N.slice();\n'
             '            L.sort(m);\n'
             '            for (var E = v; E < c; ++E)(C = s[E].parentNode).removeChild(s[E]);\n'
             '            for (E = v; E < c; ++E) C.appendChild(s[v + L[E - v]])\n'
             '          })\n'
             '        })\n'
             '      }\n'
             '    }\n'
             '    n.addEventListener("DOMContentLoaded", function() {\n'
             '      for (var t = n.getElementsByClassName("content-table"), e = 0; e < r(t); ++e) try {\n'
             '        v(t[e])\n'
             '      } catch (n) {}\n'
             '    })\n'
             '  }(document)\n'
             '</script>\n')


def cell_class(col):
    """ Return a background color for a given column title """
    col = col.lower()
    # Auto-generated columns
    if col in ColumnList.COLUMNS_GEN_L:
        return 'gen'  # BG_GEN
    # KiCad protected columns
    elif col in ColumnList.COLUMNS_PROTECTED_L:
        return 'kicad'  # BG_KICAD
    # Additional user columns
    return 'user'  # BG_USER


def link(text):
    for t in ["http", "https", "ftp", "www"]:
        if text.startswith(t):
            return '<a href="{t}">{t}</a>'.format(t=text)
    return text


def content_table(html, groups, headings, head_names, cfg, link_datasheet, link_digikey, link_mouser, link_lcsc, col_colors,
                  row_colors, dnf=False):
    cl = ''
    # Table start
    html.write('<table class="content-table">\n')
    # Row titles:
    html.write(" <thead>\n")
    html.write("  <tr>\n")
    for i, h in enumerate(head_names):
        if col_colors:
            # Cell background color
            cl = ' class="th-'+cell_class(headings[i])+'"'
        html.write('   <th{}>{}</th>\n'.format(cl, h))
    html.write("  </tr>\n")
    html.write(" </thead>\n")

    html.write(" <tbody>\n")
    rc = 0
    hl_empty = cfg.html.highlight_empty
    for i, group in enumerate(groups):
        if (cfg.ignore_dnf and not group.is_fitted()) != dnf:
            continue
        # Check if the user wants a color for this row
        row_color = None
        for r_color in row_colors:
            c = group.components[0]
            if r_color.filter.filter(c):
                row_color = r_color.color
                break
        row = group.get_row(headings)
        if link_datasheet != -1:
            datasheet = group.get_field(ColumnList.COL_DATASHEET_L)
        html.write('  <tr id="{}">\n'.format(i))
        for n, r in enumerate(row):
            # A link to Digi-Key?
            if link_digikey and headings[n] in link_digikey:
                r = '<a href="https://www.digikey.com/en/products/result?keywords=' + urllib.parse.quote(r) + '">' + r + '</a>'
            if link_mouser and headings[n] in link_mouser:
                r = '<a href="https://www.mouser.com/ProductDetail/' + r + '">' + r + '</a>'
            if link_lcsc and headings[n] in link_lcsc:
                r = '<a href="https://www.lcsc.com/product-detail/' + r + '.html">' + r + '</a>'
            # Link this column to the datasheet?
            if link_datasheet == n and datasheet.startswith('http'):
                r = '<a href="' + datasheet + '">' + r + '</a>'
            if col_colors:
                # Empty cell?
                if hl_empty and (len(r) == 0 or r.strip() == "~"):
                    cl = 'empty'
                else:
                    cl = cell_class(headings[n])
                cl = ' class="td-{}{}"'.format(cl, rc % 2)
            else:
                cl = ' class="td-nocolor"'
            if row_color is not None:
                cl += f' style="background-color: {row_color}"'
            if headings[n] == ColumnList.COL_REFERENCE_L:
                for ref in r.split(cfg.ref_separator):
                    r = '<div id="{}"></div>'.format(ref)+r
            html.write('   <td{}>{}</td>\n'.format(cl, link(r)))
        html.write("  </tr>\n")
        rc += 1
    html.write(" </tbody>\n")
    html.write("</table>\n")
    return


def embed_image(file):
    try:
        s, w, h, _ = read_png(file, logger)
    except TypeError as e:
        raise BoMError(f'Only PNG images are supported for the logo ({e})')
    return int(w), int(h), 'data:image/png;base64,'+b64encode(s).decode('ascii')


def write_stats(html, cfg):
    if len(cfg.aggregate) == 1:
        # Only one project
        html.write('<tr>\n')
        html.write(' <td class="cell-info">\n')
        if not cfg.html.hide_pcb_info:
            prj = cfg.aggregate[0]
            html.write("   <b>Schematic</b>: {}<br>\n".format(prj.name))
            html.write("   <b>Variant</b>: {}<br>\n".format(cfg.variant.name if cfg.variant else 'default'))
            html.write("   <b>Revision</b>: {}<br>\n".format(prj.sch.revision))
            html.write("   <b>Date</b>: {}<br>\n".format(prj.sch.date))
            html.write("   <b>KiCad Version</b>: {}<br>\n".format(cfg.kicad_version))
        html.write(' </td>\n')
        html.write(' <td class="cell-stats">\n')
        if not cfg.html.hide_stats_info:
            html.write("   <b>Component Groups</b>: {}<br>\n".format(cfg.n_groups))
            html.write("   <b>Component Count</b>: {} (per PCB)<br>\n\n".format(cfg.total_str))
            html.write("   <b>Fitted Components</b>: {} (per PCB)<br>\n".format(cfg.fitted_str))
            html.write("   <b>Number of PCBs</b>: {}<br>\n".format(cfg.number))
            html.write("   <b>Total Components</b>: {t} (for {n} PCBs)<br>\n".format(n=cfg.number, t=cfg.n_build))
        html.write(' </td>\n')
        html.write('</tr>\n')
    else:
        # Multiple projects
        # Global stats
        html.write('<tr>\n')
        html.write(' <td class="cell-info">\n')
        if not cfg.html.hide_pcb_info:
            html.write("   <b>Variant</b>: {}<br>\n".format(cfg.variant.name if cfg.variant else 'default'))
            html.write("   <b>KiCad Version</b>: {}<br>\n".format(cfg.kicad_version))
        html.write(' </td>\n')
        html.write(' <td class="cell-stats">\n')
        if not cfg.html.hide_stats_info:
            html.write("   <b>Component Groups</b>: {}<br>\n".format(cfg.n_groups))
            html.write("   <b>Component Count</b>: {} (per PCB)<br>\n\n".format(cfg.total_str))
            html.write("   <b>Fitted Components</b>: {} (per PCB)<br>\n".format(cfg.fitted_str))
            html.write("   <b>Number of PCBs</b>: {}<br>\n".format(cfg.number))
            html.write("   <b>Total Components</b>: {t} (for {n} PCBs)<br>\n".format(n=cfg.number, t=cfg.n_build))
        html.write(' </td>\n')
        html.write('</tr>\n')
        # Individual stats
        for prj in cfg.aggregate:
            html.write('<tr>\n')
            html.write(' <td colspan="2" class="cell-title">\n')
            html.write('  <div class="subtitle">'+prj.sch.title+'</div>\n')
            html.write(' </td>\n')
            html.write('</tr>\n')
            html.write('<tr>\n')
            html.write(' <td class="cell-info">\n')
            if not cfg.html.hide_pcb_info:
                html.write("   <b>Schematic</b>: {}<br>\n".format(prj.name))
                html.write("   <b>Revision</b>: {}<br>\n".format(prj.sch.revision))
                html.write("   <b>Date</b>: {}<br>\n".format(prj.sch.date))
                if prj.sch.company:
                    html.write("   <b>Company</b>: {}<br>\n".format(prj.sch.company))
                if prj.ref_id:
                    html.write("   <b>ID</b>: {}<br>\n".format(prj.ref_id))
            html.write(' </td>\n')
            html.write(' <td class="cell-stats">\n')
            if not cfg.html.hide_stats_info:
                html.write("   <b>Component Groups</b>: {}<br>\n".format(prj.comp_groups))
                html.write("   <b>Component Count</b>: {} (per PCB)<br>\n\n".format(prj.total_str))
                html.write("   <b>Fitted Components</b>: {} (per PCB)<br>\n".format(prj.fitted_str))
                html.write("   <b>Number of PCBs</b>: {}<br>\n".format(prj.number))
                html.write("   <b>Total Components</b>: {t} (for {n} PCBs)<br>\n".format(n=prj.number, t=prj.comp_build))
            html.write(' </td>\n')
            html.write('</tr>\n')


def write_extra_info(html, cfg):
    if not cfg.html.extra_info:
        return
    html.write('<tr>\n')
    html.write(' <td colspan="2" class="cell-extra-info">\n')
    for e in cfg.html.extra_info:
        html.write("   <b>{}</b><br>\n".format(e))
    html.write(' </td>\n')
    html.write('</tr>\n')


def write_html(filename, groups, headings, head_names, cfg):
    """
    Write BoM out to a HTML file
    filename = path to output file (must be a .csv, .txt or .tsv file)
    groups = [list of ComponentGroup groups]
    headings = [list of headings to search for data in the BoM file]
    head_names = [list of headings to display in the BoM file]
    cfg = BoMOptions object with all the configuration
    """
    link_datasheet = -1
    if cfg.html.datasheet_as_link and cfg.html.datasheet_as_link in headings:
        link_datasheet = headings.index(cfg.html.datasheet_as_link)
    link_digikey = cfg.html.digikey_link
    link_mouser = cfg.html.mouser_link
    link_lcsc = cfg.html.lcsc_link
    col_colors = cfg.html.col_colors
    row_colors = cfg.html.row_colors
    # Compute the CSS
    style_name = cfg.html.style
    if os.path.isfile(style_name):
        with open(style_name, 'rt') as f:
            style = f.read()
    else:
        # Common stuff
        style = STYLE_COMMON
        if style_name.startswith('modern-'):
            # content-table details
            if style_name.endswith('green'):
                head_color = HEAD_COLOR_G
                head_color_l = HEAD_COLOR_G_L
            elif style_name.endswith('blue'):
                head_color = HEAD_COLOR_B
                head_color_l = HEAD_COLOR_B_L
            else:
                head_color = HEAD_COLOR_R
                head_color_l = HEAD_COLOR_R_L
            style += TABLE_MODERN.replace('@bg@', head_color)
            style += TABLE_MODERN.replace('@bgl@', head_color_l)
        else:
            # Background is white, so we change the sorting cursor to black
            style = style.replace('border-color:#ffffff', 'border-color:#000000')
            style += TABLE_CLASSIC

    with open(filename, "w") as html:
        # HTML Head
        html.write("<html>\n")
        html.write("<head>\n")
        html.write(' <meta charset="UTF-8">\n')  # UTF-8 encoding for unicode support
        if cfg.html.title:
            html.write(' <title>'+cfg.html.title+'</title>\n')
        # CSS
        html.write("<style>\n")
        html.write(style)
        html.write("</style>\n")
        html.write("</head>\n")

        html.write("<body>\n")
        # Page Header
        img = None
        if cfg.html.logo is not None:
            if cfg.html.logo:
                img_w, img_h, img = embed_image(cfg.html.logo)
            else:
                img = 'data:image/png;base64,'+KIBOT_LOGO
                img_w = KIBOT_LOGO_W
                img_h = KIBOT_LOGO_H
        if img or not cfg.html.hide_pcb_info or not cfg.html.hide_stats_info or cfg.html.title:
            html.write('<table class="head-table">\n')
            html.write('<tr>\n')
            n = 2
            if len(cfg.aggregate) > 1:
                n += 2*len(cfg.aggregate)
            if len(cfg.html.extra_info):
                n += 1
            html.write(' <td rowspan="{}">\n'.format(n))
            if img:
                html.write('  <img src="'+img+'" alt="Logo" width="'+str(img_w)+'" height="'+str(img_h)+'">\n')
            html.write(' </td>\n')
            html.write(' <td colspan="2" class="cell-title">\n')
            if cfg.html.title:
                html.write('  <div class="title">'+cfg.html.title+'</div>\n')
            html.write(' </td>\n')
            html.write('</tr>\n')
            write_extra_info(html, cfg)
            write_stats(html, cfg)
            html.write('</table>\n')

        # Fitted groups
        html.write("<h2>Component Groups</h2>\n")
        content_table(html, groups, headings, head_names, cfg, link_datasheet, link_digikey, link_mouser, link_lcsc,
                      col_colors, row_colors)

        # DNF component groups
        if cfg.html.generate_dnf and cfg.n_total != cfg.n_fitted:
            html.write("<h2>Optional components (DNF=Do Not Fit)</h2>\n")
            content_table(html, groups, headings, head_names, cfg, link_datasheet, link_digikey, link_mouser, link_lcsc,
                          col_colors, row_colors, True)

        # Color reference
        if col_colors:
            html.write('<table class="color-ref">\n')
            html.write('<tr><th>Color reference for columns:</th></tr>\n')
            html.write('<tr><td class="td-kicad0">KiCad Fields (default)</td></tr>\n')
            html.write('<tr><td class="td-gen0">Generated Fields</td></tr>\n')
            html.write('<tr><td class="td-user0">User Fields</td></tr>\n')
            if cfg.html.highlight_empty:
                html.write('<tr><td class="td-empty0">Empty Fields</td></tr>\n')
            html.write('</table>\n')

        if row_colors:
            html.write('<table class="color-ref">\n')
            html.write('<tr><th>Color reference for rows:</th></tr>\n')
            for r_color in row_colors:
                html.write('<tr><td style="background-color: '
                           f'{r_color.color}">{r_color.description}</td></tr>\n')
            html.write('</table>\n')

        html.write(SORT_CODE)
        html.write("</body></html>")

    return True
