# -*- coding: utf-8 -*-
# Copyright (c) 2022-2024 Salvador E. Tropea
# Copyright (c) 2022-2024 Instituto Nacional de Tecnología Industrial
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)
# The Assembly image is a composition from Pixlok and oNline Web Fonts
# The rest are KiCad icons
import base64
import os
import subprocess
import pprint
import re
from shutil import copy2
from .bom.kibot_logo import KIBOT_LOGO, KIBOT_LOGO_W, KIBOT_LOGO_H
from .error import KiPlotConfigurationError
from .gs import GS
from .optionable import Optionable, BaseOptions
from .kiplot import config_output, run_command
from .misc import W_NOTYET, W_MISSTOOL, W_NOOUTPUTS, read_png, force_list, W_CONVPDF
from .pre_base import BasePreFlight
from .registrable import RegOutput
from .macros import macros, document  # noqa: F401
from . import log, __version__

logger = log.get_logger()
CAT_IMAGE = {'PCB': 'pcbnew',
             'Schematic': 'eeschema',
             'Compress': 'zip',
             'fabrication': 'fabrication',
             'export': 'export',
             'assembly': 'assembly_simple',
             'repair': 'repair',
             'docs': 'project',
             'BoM': 'bom',
             '3D': '3d',
             'gerber': 'gerber',
             'drill': 'load_drill',
             'Auxiliar': 'repair'}
EXT_IMAGE = {'gbr': 'file_gbr',
             'gtl': 'file_gbr',
             'gtp': 'file_gbr',
             'gbo': 'file_gbr',
             'gto': 'file_gbr',
             'gbs': 'file_gbr',
             'gbl': 'file_gbr',
             'gts': 'file_gbr',
             'gml': 'file_gbr',
             'gm1': 'file_gbr',
             'gbrjob': 'file_gerber_job',
             'brd': 'file_brd',
             'brep': 'file_brep',
             'bz2': 'file_bz2',
             'dxf': 'file_dxf',
             'cad': 'file_cad',
             'drl': 'file_drl',
             'pdf': 'file_pdf',
             'txt': 'file_txt',
             'pos': 'file_pos',
             'csv': 'file_csv',
             'svg': 'file_svg',
             'eps': 'file_eps',
             'png': 'file_png',
             'jpg': 'file_jpg',
             'glb': 'file_glb',
             'plt': 'file_plt',
             'ps': 'file_ps',
             'rar': 'file_rar',
             'scad': 'file_scad',
             'stl': 'file_stl',
             'step': 'file_stp',
             'stp': 'file_stp',
             'wrl': 'file_wrl',
             'html': 'file_html',
             'css': 'file_css',
             'xml': 'file_xml',
             'tsv': 'file_tsv',
             'xao': 'file_xao',
             'xlsx': 'file_xlsx',
             'xyrs': 'file_xyrs',
             'xz': 'file_xz',
             'gz': 'file_gz',
             'tar': 'file_tar',
             'zip': 'file_zip',
             'kicad_pcb': 'pcbnew',
             'sch': 'eeschema',
             'kicad_sch': 'eeschema',
             'blend': 'file_blend',
             'pcb3d': 'file_pcb3d',
             'json': 'file_json'}
for i in range(31):
    n = str(i)
    EXT_IMAGE['gl'+n] = 'file_gbr'
    EXT_IMAGE['g'+n] = 'file_gbr'
    EXT_IMAGE['gp'+n] = 'file_gbr'
CAT_REP = {'PCB': ['pdf_pcb_print', 'svg_pcb_print', 'pcb_print'],
           'Schematic': ['pdf_sch_print', 'svg_sch_print']}
IMAGEABLES_SIMPLE = {'png', 'jpg'}
IMAGEABLES_GS = {'pdf', 'eps', 'ps'}
IMAGEABLES_SVG = {'svg'}


def _run_command(cmd, fname=None):
    logger.debug('- Executing: '+GS.pasteable_cmd(cmd))
    try:
        cmd_output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        odecoded = e.output.decode() if e.output else None
        if '--unlimited' in odecoded:
            cmd.remove('--unlimited')
            return _run_command(cmd, fname)
        if odecoded:
            logger.debug('Output from command: '+odecoded)
        msg = f'Failed to run {cmd[0]}, error {e.returncode}'
        if fname is not None:
            msg += ' on file: '+fname
        logger.non_critical_error(msg)
        if odecoded and 'operation not allowed by the security policy' in odecoded:
            logger.warning(W_CONVPDF+"Your system doesn't allow PDF/PS manipulation, read the installation docs")
        return False
    if cmd_output.strip():
        logger.debug('- Output from command:\n'+cmd_output.decode())
    return True


class Any_Navigate_ResultsOptions(BaseOptions):
    def __init__(self):
        with document:
            self.output = GS.def_global_output
            """ *Filename for the output (%i=html, %x=navigate) """
            self.link_from_root = ''
            """ *The name of a file to create at the main output directory linking to the home page """
            self.skip_not_run = False
            """ Skip outputs with `run_by_default: false` """
            self.logo = Optionable
            """ [string|boolean=''] PNG file to use as logo, use false to remove.
                The KiBot logo is used by default """
            self.logo_url = 'https://github.com/INTI-CMNB/KiBot/'
            """ Target link when clicking the logo """
            self.logo_force_height = -1
            """ Force logo height in px. Useful to get consistent heights across different logos. """
            self.title = ''
            """ Title for the page, when empty KiBot will try using the schematic or PCB title.
                If they are empty the name of the project, schematic or PCB file is used.
                You can use %X values and KiCad variables here """
            self.title_url = Optionable
            """ [string|boolean=''] Target link when clicking the title, use false to remove.
                KiBot will try with the origin of the current git repo when empty """
            self.expand_text_vars = True
            """ Expand KiBot %X and KiCad ${VARIABLE} values in the title """
            self.nav_bar = True
            """ Add a side navigation bar to quickly access to the outputs """
            self.render_markdown = True
            """ If True, markdown files are rendered; otherwise, they are treated like other files """
            self.header = True
            """ Add a header containing information for the project """
            self.display_kibot_version = True
            """ If True, display the KiBot version at the bottom of each page """
            self.display_category_images = True
            """ If True, we try to display images for categories according to the category type"""
            self.image_white_background = True
            """ When creating a miniature preview of a document use a white background instead of a transparent background.
                This helps when using a dark mode """
        super().__init__()
        self._variant_name = self._find_variant_name()
        self._expand_id = 'navigate'
        self._expand_ext = 'html'
        self._style = ''
        self._title_height = 30
        self._big_icon = 256
        self._mid_icon = 64

    def config(self, parent):
        super().config(parent)
        # Logo
        if isinstance(self.logo, bool):
            self.logo = '' if self.logo else None
        elif self.logo:
            self.logo = os.path.abspath(self.logo)
            if not os.path.isfile(self.logo):
                raise KiPlotConfigurationError('Missing logo file `{}`'.format(self.logo))
            try:
                self._logo_data, self._logo_w, self._logo_h, _ = read_png(self.logo, logger)
            except TypeError as e:
                raise KiPlotConfigurationError(f'Only PNG images are supported for the logo ({e})')
        if self.logo == '':
            # Internal logo
            self._logo_w = KIBOT_LOGO_W
            self._logo_h = KIBOT_LOGO_H
            self._logo_data = base64.b64decode(KIBOT_LOGO)
        elif self.logo is None:
            self._logo_w = self._logo_h = 0
            self._logo_data = ''
        if self.logo_force_height > 0:
            self._logo_w = self.logo_force_height/self._logo_h*self._logo_w
            self._logo_h = self.logo_force_height
        # Title URL
        if isinstance(self.title_url, bool):
            self.title_url = '' if self.title_url else None

    def add_to_tree(self, cat, out, o_tree):
        if cat == '.' or cat == './':
            # Place output directly at the root level
            o_tree[out.name] = out
        else:
            cat = cat.split('/')
            node = o_tree
            for c in cat:
                if c not in node:
                    # New category
                    node[c] = {}
                node = node[c]
            node[out.name] = out

    def svg_to_png(self, svg_file, png_file, width):
        cmd = [self.rsvg_command, '-w', str(width), '-f', 'png', '--unlimited', '-o', png_file, svg_file]
        return _run_command(cmd, svg_file)

    def copy(self, img, width):
        """ Copy an SVG icon to the images/ dir.
            Tries to convert it to PNG. """
        img_w = "{}_{}".format(os.path.basename(img), width)
        if img_w in self.copied_images:
            # Already copied, just return its name
            return self.copied_images[img_w]
        src = os.path.join(self.img_src_dir, img+'.svg') if not img.endswith('.svg') else img
        dst = os.path.join(self.out_dir, 'images', img_w)
        id = img_w
        if self.rsvg_command is not None and self.svg_to_png(src, dst+'.png', width):
            img_w += '.png'
        else:
            copy2(src, dst+'.svg')
            img_w += '.svg'
        name = os.path.join('images', img_w)
        self.copied_images[id] = name
        return name

    def can_be_converted(self, ext):
        if ext in IMAGEABLES_SVG and self.rsvg_command is None:
            logger.warning(W_MISSTOOL+"Missing SVG to PNG converter")
            return False
        if ext in IMAGEABLES_GS and not self.ps2img_avail:
            logger.warning(W_MISSTOOL+"Missing PS/PDF to PNG converter")
            return False
        if ext in IMAGEABLES_SIMPLE and self.convert_command is None:
            logger.warning(W_MISSTOOL+"Missing ImageMagick converter")
            return False
        return ext in IMAGEABLES_SVG or ext in IMAGEABLES_GS or ext in IMAGEABLES_SIMPLE

    def compose_image(self, file, ext, img, out_name, no_icon=False):
        if not os.path.isfile(file):
            logger.warning(W_NOTYET+"{} not yet generated, using an icon".format(os.path.relpath(file)))
            return False, None, None
        if self.convert_command is None:
            return False, None, None
        file_ori = file
        # Create a unique name using the output name and the generated file name
        bfname = os.path.splitext(os.path.basename(file))[0]
        fname = os.path.join(self.out_dir, 'images', out_name+'_'+bfname+'.png')
        # Full path for the icon image
        icon = os.path.join(self.out_dir, img)
        if ext == 'pdf':
            # Only page 1
            file += '[0]'
        if ext == 'svg':
            tmp_name = GS.tmp_file(suffix='.png')
            logger.debug('Temporal convert: {} -> {}'.format(file, tmp_name))
            if not self.svg_to_png(file, tmp_name, self._big_icon):
                return False, None, None
            file = tmp_name
        cmd = [self.convert_command, file,
               # Size for the big icons (width)
               '-resize', str(self._big_icon)+'x']
        if self.image_white_background:
            cmd.extend(['-background', 'white', '-alpha', 'remove', '-alpha', 'off'])
        if ext == 'ps':
            # ImageMagick 6.9.11 (and also the one in Debian 11) rotates the PS
            cmd.extend(['-rotate', '90'])
        if not no_icon:
            cmd.extend([  # Add the file type icon
                        icon,
                        # At the bottom right
                        '-gravity', 'south-east',
                        # This is a composition, not 2 images
                        '-composite'])
        cmd.append(fname)
        res = _run_command(cmd, file_ori)
        if ext == 'svg':
            logger.debug('Removing temporal {}'.format(tmp_name))
            os.remove(tmp_name)
        return res, fname, os.path.relpath(fname, start=self.out_dir)

    def write_kibot_version(self, f):
        if self.display_kibot_version:
            f.write('<p class="generator">Generated by <a href="https://github.com/INTI-CMNB/KiBot/">KiBot</a> v{}</p>\n'.
                    format(__version__))

    def write_head(self, f, title):
        f.write('<!DOCTYPE html>\n')
        f.write('<html lang="en">\n')
        f.write('<head>\n')
        f.write(' <title>{}</title>\n'.format(title if title else 'Main page'))
        f.write(' <meta charset="UTF-8">\n')  # UTF-8 encoding for unicode support
        f.write(' <link rel="stylesheet" href="styles.css">\n')
        f.write(' <link rel="icon" href="favicon.ico">\n')
        # Include Markdown-it
        if self.render_markdown:
            f.write(' <script src="markdown-it.min.js"></script>\n')
        f.write('</head>\n')
        f.write('<body>\n')
        f.write(self.navbar)
        f.write(self.top_menu)
        f.write('<div id="main">\n')

    def generate_cat_page_for(self, name, node, prev, category):
        raise NotImplementedError

    def adjust_image_paths(self, md_content, current_dir, html_output_dir):

        image_pattern = r'!\[.*?\]\((.*?)\)'  # Markdown image paths: ![Alt text](path/to/image.png)
        html_img_pattern = r'<img\s+[^>]*src="([^"]+)"'  # HTML img src="path/to/image.png"

        def replace_path(match):
            original_path = match.group(1)

            # Skip absolute URLs or paths
            if original_path.startswith(('http://', 'https://', '/')):
                return match.group(0)

            # Convert relative path to absolute and back to relative for the HTML output directory
            abs_path = os.path.abspath(os.path.join(current_dir, original_path))
            rel_path = os.path.relpath(abs_path, html_output_dir)

            # Replace the path with the new relative path
            return match.group(0).replace(original_path, rel_path)

        # Replace Markdown image paths
        md_content = re.sub(image_pattern, replace_path, md_content)

        # Replace HTML <img> tag paths
        md_content = re.sub(html_img_pattern, replace_path, md_content)

        return md_content

    def generate_outputs(self, f, node):
        raise NotImplementedError

    def generate_end_page_for(self, name, node, prev, category):
        raise NotImplementedError

    def generate_page_for(self, node, name, prev=None, category=''):
        raise NotImplementedError

    def get_targets(self, out_dir):
        # Listing all targets is too complex, we list the most relevant
        # This is good enough to compress the result
        name = self._parent.expand_filename(out_dir, self.output)
        files = [os.path.join(out_dir, 'images'),
                 os.path.join(out_dir, 'styles.css'),
                 os.path.join(out_dir, 'favicon.ico')]
        if self.render_markdown:
            files.append(os.path.join(out_dir, 'markdown-it.min.js'))
        if self.link_from_root:
            files.append(os.path.join(GS.out_dir, self.link_from_root))
        self.out_dir = out_dir
        self.get_html_names(self.create_tree(), name, files)
        return files

    def get_html_names_cat(self, name, node, prev, category, files):
        files.append(os.path.join(self.out_dir, name))
        name, ext = os.path.splitext(name)
        for cat, content in node.items():
            if not isinstance(content, dict):
                continue
            pname = name+'_'+cat+ext
            self.get_html_names(content, pname, files, name, category+'/'+cat)

    def get_html_names(self, node, name, files, prev=None, category=''):
        if isinstance(list(node.values())[0], dict):
            self.get_html_names_cat(name, node, prev, category, files)
        else:
            files.append(os.path.join(self.out_dir, name))

    def get_html_names_for_path(self, category_path, name, ext):
        files = []
        node = self.create_tree()
        self.get_html_names_cat(name, node, None, category_path, files)
        for file_path in files:
            if category_path.replace('/', '_') in file_path:
                return os.path.basename(file_path) + ext
        return None

    def create_tree(self):
        o_tree = {}
        BasePreFlight.configure_all()
        for n in BasePreFlight.get_in_use_names():
            pre = BasePreFlight.get_preflight(n)
            cat = force_list(pre.get_category())
            if not cat:
                continue
            for c in cat:
                self.add_to_tree(c, pre, o_tree)
        for o in RegOutput.get_outputs():
            if not o.run_by_default and self.skip_not_run:
                # Skip outputs that aren't generated in a regular run
                continue
            config_output(o)
            cat = o.category
            if cat is None:
                continue
            for c in cat:
                self.add_to_tree(c, o, o_tree)
        return o_tree

    def generate_navbar_one(self, node, lvl, name, ext):
        raise NotImplementedError

    def generate_navbar(self, node, name):
        raise NotImplementedError

    def generate_top_menu(self, category=''):
        raise NotImplementedError

    def solve_title(self):
        base_title = None
        if GS.sch:
            base_title = GS.sch.get_title()
        if GS.board and not base_title:
            tb = GS.board.GetTitleBlock()
            base_title = tb.GetTitle()
        if not base_title:
            base_title = GS.pro_basename or GS.sch_basename or GS.pcb_basename or 'Unknown'
        text = self.expand_filename_sch(self.title if self.title else '+')
        if text[0] == '+':
            if self.expand_text_vars:
                base_title = self.expand_filename_sch(base_title)
            text = base_title+text[1:]
        self._solved_title = text
        # Now the URL
        if self.title_url is not None and not self.title_url:
            # Empty but not None
            self._git_command = self.check_tool('Git')
            if self._git_command:
                res = ''
                try:
                    res = run_command([self._git_command, 'remote', 'get-url', 'origin'], just_raise=True)
                except subprocess.CalledProcessError:
                    pass
                if res:
                    self.title_url = res

    def solve_revision(self):
        base_rev = None
        if GS.sch:
            GS.load_sch()
            GS.load_sch_title_block()
            base_rev = GS.sch_rev
        if GS.board and not base_rev:
            tb = GS.board.GetTitleBlock()
            base_rev = tb.GetRevision()
        if not base_rev:
            base_rev = 'Unknown'
        self._solved_revision = base_rev

    def solve_company(self):
        base_comp = None
        if GS.sch:
            GS.load_sch()
            GS.load_sch_title_block()
            base_comp = GS.sch_comp
        if GS.board and not base_comp:
            tb = GS.board.GetTitleBlock()
            base_comp = tb.GetCompany()
        if not base_comp:
            base_comp = 'Unknown'
        self._solved_company = base_comp

    def run(self, name):
        self.out_dir = os.path.dirname(name)
        self.img_src_dir = GS.get_resource_path('images')
        self.js_src_dir = GS.get_resource_path('navigate_results')
        self.img_dst_dir = os.path.join(self.out_dir, 'images')
        os.makedirs(self.img_dst_dir, exist_ok=True)
        self.copied_images = {}
        name = os.path.basename(name)
        # Create a tree with all the outputs
        o_tree = self.create_tree()
        logger.debug('Collected outputs:\n'+pprint.pformat(o_tree))
        if not o_tree:
            logger.warning(W_NOOUTPUTS+'No outputs for navigate results')
            return
        with open(os.path.join(self.out_dir, 'styles.css'), 'wt') as f:
            if not self.header:
                top_margin = 0 if not self.nav_bar else self._title_height
            else:
                top_margin = str(max(self._logo_h, self._title_height))
            f.write(self._style.replace('@TOP_MAR@', str(top_margin)))
        self.rsvg_command = self.check_tool('rsvg1')
        self.convert_command = self.check_tool('ImageMagick')
        self.ps2img_avail = self.check_tool('Ghostscript')
        # Create the pages
        self.home = name
        self.back_img = self.copy('back', self._mid_icon)
        self.home_img = self.copy('home', self._mid_icon)
        copy2(os.path.join(self.img_src_dir, 'favicon.ico'), os.path.join(self.out_dir, 'favicon.ico'))
        if self.render_markdown:
            copy2(os.path.join(self.js_src_dir, 'markdown-it.min.js'), os.path.join(self.out_dir, 'markdown-it.min.js'))
        # Copy the logo image
        if self.logo is not None and self.header:
            with open(os.path.join(self.out_dir, 'images', 'logo.png'), 'wb') as f:
                f.write(self._logo_data)
        self.solve_title()
        self.solve_company()
        self.solve_revision()
        self.navbar = self.generate_navbar(o_tree, name) if self.nav_bar else ''
        self.top_menu = self.generate_top_menu() if self.nav_bar or self.header else ''
        self.generate_page_for(o_tree, name)
        # Link it?
        if self.link_from_root:
            redir_file = os.path.join(GS.out_dir, self.link_from_root)
            rel_start = os.path.relpath(os.path.join(self.out_dir, name), start=GS.out_dir)
            logger.debug('Creating redirector: {} -> {}'.format(redir_file, rel_start))
            with open(redir_file, 'wt') as f:
                f.write('<html>\n<head>\n<meta http-equiv="refresh" content="0; {}"/>'.format(rel_start))
                f.write('</head>\n</html>')
