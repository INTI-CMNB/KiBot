# -*- coding: utf-8 -*-
# Copyright (c) 2022-2025 Salvador E. Tropea
# Copyright (c) 2022-2025 Nguyen Vincent
# Copyright (c) 2022-2025 Instituto Nacional de Tecnología Industrial
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)
"""
Dependencies:
  - from: RSVG
    role: Create outputs preview
    id: rsvg1
  - from: RSVG
    role: Create PNG icons
    id: rsvg2
  - from: Ghostscript
    role: Create outputs preview
  - from: ImageMagick
    role: Create outputs preview
  - from: Git
    role: Find origin url
"""
import os
from math import ceil
from .registrable import RegOutput
from .out_any_navigate_results import Any_Navigate_ResultsOptions, CAT_IMAGE, EXT_IMAGE, CAT_REP
from .macros import macros, document, output_class  # noqa: F401
from .kiplot import get_output_dir
from .misc import read_png
from . import log

logger = log.get_logger()

OUT_COLS = 12

STYLE = """
.cat-table { margin-left: auto; margin-right: auto; }
.cat-table td { padding: 20px 24px; }
.nav-table { margin-left: auto; margin-right: auto; }
.nav-table td { padding: 20px 24px; }
.output-table {
  width: 1280px;
  margin-left: auto;
  margin-right: auto;
  border-collapse:
  collapse;
  margin-top: 5px;
  margin-bottom: 4em;
  font-size: 0.9em;
  font-family: sans-serif;
  min-width: 400px;
  border-radius: 5px 5px 0 0;
  overflow: hidden;
  box-shadow: 0 0 20px rgba(0, 0, 0, 0.15);
}
.output-table thead tr { background-color: #0e4e8e; color: #ffffff; text-align: left; }
.output-table th { padding: 10px 12px; }
.output-table td { padding: 5px 7px; }
.out-cell { width: 128px; text-align: center }
.out-cell-md { width: 128px;}
.out-img { text-align: center; margin-left: auto; margin-right: auto; }
.cat-img { text-align: center; margin-left: auto; margin-right: auto; }
.td-small { text-align: center; font-size: 0.6em; }
.td-normal { text-align: center; }
.generator { text-align: right; font-size: 0.6em; }
a:link, a:visited { text-decoration: none;}
a:hover, a:active { text-decoration: underline;}
/* The side navigation menu */
.sidenav {
  height: 100%; /* 100% Full-height */
  width: 0; /* 0 width - change this with JavaScript */
  position: fixed; /* Stay in place */
  z-index: 1; /* Stay on top */
  top: 0; /* Stay at the top */
  left: 0;
  background-color: #0e4e8e; /* Black*/
  overflow-x: hidden; /* Disable horizontal scroll */
  padding-top: 60px; /* Place content 60px from the top */
  transition: 0.5s; /* 0.5 second transition effect to slide in the sidenav */
}
/* The navigation menu links */
.sidenav a {
  padding: 8px 8px 8px 8px;
  text-decoration: none;
  font-size: 16px;
  color: #f1f1f1;
  display: block;
  transition: 0.3s;
}
/* When you mouse over the navigation links, change their color */
.sidenav a:hover {
  color: #ff0000;
}
/* Position and style the close button (top right corner) */
.sidenav .closebtn {
  position: absolute;
  top: 0;
  right: 8px;
  font-size: 36px;
  margin-left: 50px;
}
/* Style page content - use this if you want to push the page content to the right when you open the side navigation */
#main {
  transition: margin-left .5s;
  padding: 20px;
  margin-top: @TOP_MAR@px;
}
/* On smaller screens, where height is less than 450px, change the style of the sidenav (less padding and a smaller font
   size) */
@media screen and (max-height: 450px) {
  .sidenav {padding-top: 15px;}
  .sidenav a {font-size: 18px;}
}
ul {
  display: block;
  list-style-type: none;
  margin-block: -1em 0px;
  margin-inline: 0px 0px;
  padding-inline-start: 10px;
}
ul li {
  margin-block: 0px -1em;
}
.topmenu {
  overflow: hidden;
  position: fixed; /* Set the navbar to fixed position */
  top: 0; /* Position the navbar at the top of the page */
  width: 100%; /* Full width */
  background-color: white; /* Otherwise is transparent and overlaps */
}
.markdown-content {
    font-family: Roboto, sans-serif;
    line-height: 1.6;
    padding: 15px;
    border-radius: 5px;
    max-width: 100%;
    text-align: left;
    white-space: pre-wrap; /* Handle preformatted text */
    transition: background-color 0.4s ease, color 0.4s ease, border-color 0.4s ease;
}
.markdown-content table {
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 20px;
    transition: background-color 0.4s ease, color 0.4s ease, border-color 0.4s ease;
}
.markdown-content pre {
    padding: 10px;
    border-radius: 5px;
    overflow-x: auto;
}
.markdown-content code {
    padding: 2px 5px;
    border-radius: 3px;
    font-family: 'Courier New', Courier, monospace;
}
.markdown-content img {
    max-width: 100%;
    height: auto;
    display: block;
    margin: 10px auto;
}
"""
SCRIPT = """
<script>
function openNav() {
  document.getElementById("theSideNav").style.width = "360px";
  document.getElementById("main").style.marginLeft = "360px";
  document.getElementById("theTopMenu").style.marginLeft = "360px";
  document.getElementById("bmenu").style.display = "none";
}

function closeNav() {
  document.getElementById("theSideNav").style.width = "0";
  document.getElementById("main").style.marginLeft= "0";
  document.getElementById("theTopMenu").style.marginLeft = "0";
  document.getElementById("bmenu").style.display = "block";
}

function ScrollUp() {
  /* When we come here from the navbar we must scroll to avoid the top menu */
  var p = document.getElementById("main");
  var style = p.currentStyle || window.getComputedStyle(p);
  var m_top = parseInt(style.marginTop)

  window.scrollBy(0, -(m_top + 5));
}

window.onload = ScrollUp;
</script>
"""

SCRIPT_MARKDOWN = """
<script>
document.addEventListener('DOMContentLoaded', function () {
    const md = window.markdownit({
        html: true,
        linkify: true,
        typographer: true
    });

    // Find all markdown containers and render them
    document.querySelectorAll('.markdown-content').forEach(container => {
        const rawMarkdown = container.innerHTML;
        container.style.display = 'block';
        container.innerHTML = md.render(rawMarkdown);
    });
});
</script>
"""


class Navigate_ResultsOptions(Any_Navigate_ResultsOptions):
    def __init__(self):
        super().__init__()
        self._style = STYLE
        self._big_2_mid_rel = int(ceil(self._big_icon/self._mid_icon))

    def get_image_for_cat(self, cat):
        if self.display_category_images:
            img = None
            # Check if we have an output that can represent this category
            if cat in CAT_REP and self.convert_command is not None:
                outs_rep = CAT_REP[cat]
                rep_file = None
                # Look in all outputs
                for o in RegOutput.get_outputs():
                    if not o.run_by_default and self.skip_not_run:
                        # Skip outputs that aren't generated in a regular run
                        continue
                    # Is this one that can be used to represent it?
                    if o.type in outs_rep:
                        out_dir = get_output_dir(o.dir, o, dry=True)
                        targets = o.get_targets(out_dir)
                        # Look the output targets
                        for tg in targets:
                            ext = os.path.splitext(tg)[1][1:].lower()
                            # Can be converted to an image?
                            if os.path.isfile(tg) and self.can_be_converted(ext):
                                rep_file = tg
                                break
                        if rep_file:
                            break
                if rep_file:
                    cat, _ = self.get_image_for_file(rep_file, cat, no_icon=True)
                    return cat
            if cat in CAT_IMAGE:
                img = self.copy(CAT_IMAGE[cat], self._big_icon)
                cat_img = '<img src="{}" alt="{}" width="{}" height="{}">'.format(img, cat, self._big_icon, self._big_icon)
                cat = ('<table class="cat-img"><tr><td>{}<br>{}</td></tr></table>'.format(cat_img, cat))
        return cat

    def get_image_for_file(self, file, out_name, no_icon=False, image=None):
        ext = os.path.splitext(file)[1][1:].lower()
        wide = False
        # Copy the icon for this file extension
        icon_name = 'folder' if os.path.isdir(file) else EXT_IMAGE.get(ext, 'unknown')
        img = self.copy(image or icon_name, self._mid_icon)
        # Full name for the file
        file_full = file
        # Just the file, to display it
        file = os.path.basename(file)
        # The icon size
        height = width = self._mid_icon
        # Check if this file can be represented by an image
        if self.can_be_converted(ext):
            # Try to compose the image of the file with the icon
            ok, fimg, new_img = self.compose_image(file_full, ext, img, 'cat_'+out_name, no_icon)
            if ok:
                # It was converted, replace the icon by the composited image
                img = new_img
                # Compute its size
                try:
                    _, width, height, _ = read_png(fimg, logger)
                except TypeError:
                    width = height = 0
                # We are using the big size
                wide = True
        # Now add the image with its file name as caption
        ext_img = '<img src="{}" alt="{}" width="{}" height="{}">'.format(img, file, width, height)
        file = ('<table class="out-img"><tr><td>{}</td></tr><tr><td class="{}">{}</td></tr></table>'.
                format(ext_img, 'td-normal' if no_icon else 'td-small', out_name if no_icon else file))
        return file, wide

    def add_back_home(self, f, prev):
        if prev is not None:
            prev += '.html'
            f.write('<table class="nav-table">')
            f.write(' <tr>')
            f.write('  <td><a href="{}"><img src="{}" width="{}" height="{}" alt="go back"></a></td>'.
                    format(prev, self.back_img, self._mid_icon, self._mid_icon))
            f.write('  <td><a href="{}"><img src="{}" width="{}" height="{}" alt="go home"></a></td>'.
                    format(self.home, self.home_img, self._mid_icon, self._mid_icon))
            f.write(' </tr>')
            f.write('</table>')
        self.write_kibot_version(f)
        f.write('</div>\n')
        if self.nav_bar:
            f.write(SCRIPT)

    def generate_cat_page_for(self, name, node, prev, category):
        logger.debug('- Categories: '+str(node.keys()))
        with open(os.path.join(self.out_dir, name), 'wt') as f:
            self.write_head(f, category)
            name, ext = os.path.splitext(name)
            # Limit to 5 categories by row
            c_cats = len(node)
            rows = ceil(c_cats/5.0)
            by_row = c_cats/rows
            acc = 0
            f.write('<table class="cat-table">\n<tr>\n')
            for cat, content in node.items():
                if not isinstance(content, dict):
                    continue
                if acc >= by_row:
                    # Flush the table and create another
                    acc = 0
                    f.write('</tr>\n</table>\n<table class="cat-table">\n<tr>\n')
                pname = name+'_'+cat+ext
                self.generate_page_for(content, pname, name, category+'/'+cat)
                f.write(' <td><a href="{}">{}</a></td>\n'.format(pname, self.get_image_for_cat(cat)))
                acc += 1
            f.write('</tr>\n</table>\n')
            self.generate_outputs(f, node)
            if self.render_markdown:
                f.write(SCRIPT_MARKDOWN)
            self.add_back_home(f, prev)
            f.write('</body>\n</html>\n')

    def generate_outputs(self, f, node):
        for oname, out in node.items():
            if isinstance(out, dict):
                continue
            f.write(f'<table id="{oname}" class="output-table">\n')
            out_name = oname.replace(' ', '_')
            oname = oname.replace('_', ' ')
            oname = oname[0].upper() + oname[1:]
            if out.comment:
                oname += ': ' + out.comment
            f.write('<thead><tr><th colspan="{}">{}</th></tr></thead>\n'.format(OUT_COLS, oname))
            out_dir = get_output_dir(out.dir, out, dry=True)
            f.write('<tbody><tr>\n')
            targets, icons = out.get_navigate_targets(out_dir)
            c_targets = len(targets)
            if icons is None:
                icons = [None] * c_targets
            else:
                c_icons = len(icons)
                if c_icons < c_targets:
                    icons.extend([None] * (c_targets - c_icons))

            if len(targets) == 1:
                tg_rel = os.path.relpath(os.path.abspath(targets[0]), start=self.out_dir)
                ext = os.path.splitext(targets[0])[1].lower()

                # Handle markdown rendering
                if ext == '.md' and self.render_markdown:
                    with open(targets[0], 'r', encoding='utf-8') as md_file:
                        md_content = md_file.read()
                    md_content = self.adjust_image_paths(md_content, os.path.dirname(targets[0]), self.out_dir)
                    f.write(f'''
                        <td class="out-cell-md" colspan="{OUT_COLS}">
                            <div class="markdown-content">{md_content}</div>
                        </td>
                    ''')
                else:
                    img, _ = self.get_image_for_file(targets[0], out_name, image=icons[0] if icons else None)
                    f.write('<td class="out-cell" colspan="{}"><a href="{}">{}</a></td>\n'.
                            format(OUT_COLS, tg_rel, img))
            else:
                c = 0
                for tg, icon in zip(targets, icons):
                    ext = os.path.splitext(tg)[1].lower()

                    if ext == '.md' and self.render_markdown:
                        # Render Markdown
                        with open(tg, 'r', encoding='utf-8') as md_file:
                            md_content = md_file.read()
                        md_content = self.adjust_image_paths(md_content, os.path.dirname(tg), self.out_dir)
                        if c == OUT_COLS:
                            f.write('</tr>\n<tr>\n')
                            c = 0
                        f.write(f'''
                            <td class="out-cell" colspan="{OUT_COLS}">
                                <div class="markdown-content">{md_content}</div>
                            </td>
                        ''')
                        c += OUT_COLS  # Markdown uses full row width
                    else:
                        if c == OUT_COLS:
                            f.write('</tr>\n<tr>\n')
                            c = 0
                        tg_rel = os.path.relpath(os.path.abspath(tg), start=self.out_dir)
                        img, wide = self.get_image_for_file(tg, out_name, image=icon)
                        span = 1
                        if wide:
                            span = self._big_2_mid_rel
                            remain = OUT_COLS - c
                            if span > remain:
                                f.write('<td class="out-cell" colspan="{}"></td></tr>\n<tr>\n'.format(remain))
                        f.write('<td class="out-cell" colspan="{}"><a href="{}">{}</a></td>\n'.format(span, tg_rel, img))
                        c += span

                if c < OUT_COLS:
                    f.write('<td class="out-cell" colspan="{}"></td>\n'.format(OUT_COLS - c))
            f.write('</tr>\n<tr>\n')
            for _ in range(OUT_COLS):
                f.write('<td></td>\n')
            f.write('</tr>\n</tbody>\n</table>\n')

    def generate_end_page_for(self, name, node, prev, category):
        logger.debug('- Outputs: '+str(node.keys()))
        with open(os.path.join(self.out_dir, name), 'wt') as f:
            self.write_head(f, category)
            name, ext = os.path.splitext(name)
            self.generate_outputs(f, node)
            self.add_back_home(f, prev)
            if self.render_markdown:
                f.write(SCRIPT_MARKDOWN)
            f.write('</body>\n</html>\n')

    def generate_page_for(self, node, name, prev=None, category=''):
        logger.debug('Generating page for '+name)
        if isinstance(list(node.values())[0], dict):
            self.generate_cat_page_for(name, node, prev, category)
        else:
            self.generate_end_page_for(name, node, prev, category)

    def generate_navbar_one(self, node, lvl, name, ext):
        """ Recursively create a menu containing all outputs.
            Using ul and li items """
        indent = ' '+' '*lvl
        code = indent+'<ul>\n'
        indent += ' '
        for k, v in node.items():
            if isinstance(v, dict):
                new_name = name+'_'+k
                code += indent+f'<li><a href="{new_name}{ext}">{k}</a></li>\n'
                code += self.generate_navbar_one(v, lvl+1, new_name, ext)
            else:
                code += indent+f'<li><a href="{name}{ext}#{v.name}">{v.name}</a></li>\n'
        code += indent[:-1]+'</ul>\n'
        return code

    def generate_navbar(self, node, name):
        name, ext = os.path.splitext(name)
        code = '<div id="theSideNav" class="sidenav">\n'
        code += '<a href="javascript:void(0)" class="closebtn" onclick="closeNav()">&times;</a>\n'
        code += self.generate_navbar_one(node, 0, name, ext)
        code += '</div>\n'
        return code

    def generate_top_menu(self):
        # Div for the top info
        fsize = f'{self._title_height}px'
        code = '<div id="theTopMenu" class="topmenu">\n'
        code += ' <table style="width:100%">\n'
        code += '  <tr>\n'
        code += '   <td valign="top" align="left">\n'
        if self.nav_bar:
            code += f'    <span id="bmenu" style="font-size:{fsize};cursor:pointer" onclick="openNav()">&#9776;</span>\n'
        code += '   </td>\n'
        code += '   <td>\n'
        if self.logo is not None and self.header:
            img_name = os.path.join('images', 'logo.png')
            if self.logo_url:
                code += f'     <a href="{self.logo_url}">\n'
            code += '     <img src="'+img_name+'" alt="Logo" width="'+str(self._logo_w)+'" height="'+str(self._logo_h)+'">\n'
            if self.logo_url:
                code += '     </a>\n'
        code += '   </td>\n'
        code += '   <td>\n'
        if self.header:
            if self.title_url:
                code += f'     <a href="{self.title_url}">\n'
            code += f'     <span style="font-size:{fsize};">{self._solved_title}</span>\n'
            if self.title_url:
                code += '     </a>\n'
        code += '   </td>\n'
        code += '  </tr>\n'
        code += ' </table>\n'
        code += '</div>\n'
        return code


@output_class
class Navigate_Results(BaseOutput):  # noqa: F821
    """ Navigate Results
        Generates a web page to navigate the generated outputs """
    def __init__(self):
        super().__init__()
        # Make it low priority so it gets created after all the other outputs
        self.priority = 10
        with document:
            self.options = Navigate_ResultsOptions
            """ *[dict={}] Options for the `navigate_results` output """
        # The help is inherited and already mentions the default priority
        self.fix_priority_help()
        self._any_related = True
