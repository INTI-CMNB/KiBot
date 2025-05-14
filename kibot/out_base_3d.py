# -*- coding: utf-8 -*-
# Copyright (c) 2020-2025 Salvador E. Tropea
# Copyright (c) 2020-2025 Instituto Nacional de Tecnología Industrial
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)
from decimal import Decimal
from fnmatch import fnmatch
import os
import re
import requests
import urllib
from shutil import copy2
from .bom.units import comp_match
from .EasyEDA.easyeda_3d import download_easyeda_3d_model
from .fil_base import reset_filters
from .misc import (W_MISS3D, W_FAILDL, W_DOWN3D, DISABLE_3D_MODEL_TEXT, W_BADTOL, W_BADRES, W_RESVALISSUE, W_RES3DNAME,
                   EMBED_PREFIX, get_file_hash)
from .gs import GS
from .optionable import Optionable
from .out_base import VariantOptions, BaseOutput
from .kicad.config import KiConf
from .macros import macros, document  # noqa: F401
from . import log

logger = log.get_logger()
# 3D models for resistors data

# Tolerance bar:
# 20%     -     3
# 10%   Silver  4
#  5%    Gold   4
#  2%    Red    5
#  1%   Brown   5
# 0.5%  Green   5
# 0.25%  Blue   5
# 0.1%  Violet  5
# 0.05% Orange  5
# 0.02% Yellow  5
# 0.01%  Grey   5

# Special multipliers
# Multiplier < 1
# 0.1   Gold
# 0.01  Silver

X = 0
Y = 1
Z = 2
COLORS = [(0.149, 0.10, 0.10, 0.10, 0.10, 0.10, 0.10, 0.4),  # 0 Black
          (0.149, 0.40, 0.26, 0.13, 0.40, 0.26, 0.13, 0.4),  # 1 Brown
          (0.149, 0.85, 0.13, 0.13, 0.85, 0.13, 0.13, 0.4),  # 2 Red
          (0.149, 0.94, 0.37, 0.14, 0.94, 0.37, 0.14, 0.4),  # 3 Naraja
          (0.149, 0.98, 0.99, 0.06, 0.98, 0.99, 0.06, 0.4),  # 4 Yellow
          (0.149, 0.20, 0.80, 0.20, 0.20, 0.80, 0.20, 0.4),  # 5 Green
          (0.149, 0.03, 0.00, 0.77, 0.03, 0.00, 0.77, 0.4),  # 6 Blue
          (0.149, 0.56, 0.00, 1.00, 0.56, 0.00, 1.00, 0.4),  # 7 Violet
          (0.149, 0.62, 0.62, 0.62, 0.62, 0.62, 0.62, 0.4),  # 8 Grey
          (0.149, 0.99, 0.99, 0.99, 0.99, 0.99, 0.99, 0.4),  # 9 White
          (0.379, 0.86, 0.74, 0.50, 0.86, 0.74, 0.50, 1.0),  # 5% Gold (10)
          (0.271, 0.82, 0.82, 0.78, 0.33, 0.26, 0.17, 0.7),  # 10% Silver (11)
          (0.149, 0.883, 0.711, 0.492, 0.043, 0.121, 0.281, 0.4),  # Body color
          ]
TOL_COLORS = {5: 10, 10: 11, 20: 12, 2: 2, 1: 1, 0.5: 5, 0.25: 6, 0.1: 7, 0.05: 3, 0.02: 4, 0.01: 8}
WIDTHS_4 = [5, 12, 10.5, 12, 10.5, 12, 21, 12, 5]
WIDTHS_5 = [5, 10, 8.5, 10, 8.5, 10, 8.5, 10, 14.5, 10, 5]


def abs_path_model(data, replace):
    """ Make sure the 3D model uses an absolute path.
        Used for temporal files create at /tmp """
    return os.path.abspath(replace)


def do_expand_env(fname, used_extra, extra_debug, lib_nickname):
    if fname.startswith(EMBED_PREFIX):
        return fname, True
    # Is it using ALIAS:xxxxx?
    force_used_extra = False
    if ':' in fname:
        ind = fname.index(':')
        alias_name = fname[:ind]
        rest = fname[ind+1:]
        if alias_name in KiConf.aliases_3D:
            # Yes, replace the alias
            fname = os.path.join(KiConf.aliases_3D[alias_name], rest)
            # Make sure the name we created is what kicad2step gets
            force_used_extra = True
            if extra_debug:
                logger.debug("- Replaced alias {} -> {}".format(alias_name+':'+rest, fname))
    full_name = KiConf.expand_env(fname, used_extra, ref_dir=GS.pcb_dir)
    if extra_debug:
        logger.debug("- Expanded {} -> {}".format(fname, full_name))
    if os.path.isfile(full_name):
        if force_used_extra:
            used_extra[0] = True
        return full_name, False
    if ':' not in fname or GS.global_disable_3d_alias_as_env:
        # Try using the current working dir
        full_name_cwd = KiConf.expand_env(fname, used_extra, ref_dir=os.getcwd())
        if os.path.isfile(full_name_cwd):
            # Was relative to cwd, not all KiCad versions supports it, patch the model
            full_name = full_name_cwd
            force_used_extra = True
        else:
            # We still missing the 3D model
            # Try relative to the footprint lib
            # This was introduced in 7.0.0, but it doesn't work for all things in 7.0.1.
            # I.e. You can't export a VRML when using this feature
            aliases = KiConf.get_fp_lib_aliases()
            lib_alias = aliases.get(lib_nickname)
            if lib_alias is not None:
                full_name_lib = os.path.join(lib_alias.uri, fname)
                if os.path.isfile(full_name_lib):
                    logger.debug("- Using path relative to `{}` for `{}` ({})".format(lib_nickname, fname, full_name_lib))
                    full_name = full_name_lib
                    # KiCad 5 and 6 will need help
                    # force_used_extra = not GS.ki7
                    # Even KICad 7.0.1 needs help
                    force_used_extra = True
        if force_used_extra:
            used_extra[0] = True
        return full_name, False
    # Look for ALIAS:file
    ind = fname.index(':')
    alias_name = fname[:ind]
    if len(alias_name) == 1:
        # Is a drive letter, not an alias
        return full_name, False
    rest = fname[ind+1:]
    new_fname = '${'+alias_name+'}'+os.path.sep+rest
    new_full_name = KiConf.expand_env(new_fname, used_extra)
    if extra_debug:
        logger.debug("- Expanded {} -> {}".format(new_fname, new_full_name))
    if os.path.isfile(new_full_name):
        used_extra[0] = True
        return new_full_name, False
    return full_name, False


class Base3DOptions(VariantOptions):
    def __init__(self):
        with document:
            self.no_virtual = False
            """ *Used to exclude 3D models for components with 'virtual' attribute """
            self.download = True
            """ *Downloads missing 3D models from KiCad git.
                Only applies to models in KISYS3DMOD and KICAD6_3DMODEL_DIR.
                They are downloaded to a temporal directory and discarded.
                If you want to cache the downloaded files specify a directory using the
                KIBOT_3D_MODELS environment variable """
            self.download_lcsc = True
            """ In addition to try to download the 3D models from KiCad git also try to get
                them from LCSC database. In order to work you'll need to provide the LCSC
                part number. The field containing the LCSC part number is defined by the
                `field_lcsc_part` global variable """
            self.kicad_3d_url = 'https://gitlab.com/kicad/libraries/kicad-packages3D/-/raw/master/'
            """ Base URL for the KiCad 3D models """
            self.kicad_3d_url_suffix = ''
            """ Text added to the end of the download URL.
                Can be used to pass variables to the GET request, i.e. ?VAR1=VAL1&VAR2=VAL2 """
        # Temporal dir used to store the downloaded files
        self._tmp_dir = None
        super().__init__()
        self._expand_id = '3D'

    def copy_options(self, ref):
        super().copy_options(ref)
        self.no_virtual = ref.no_virtual
        self.download = ref.download
        self.download_lcsc = ref.download_lcsc
        self.kicad_3d_url = ref.kicad_3d_url
        self.kicad_3d_url_suffix = ref.kicad_3d_url_suffix

    def download_model(self, url, fname, rel_dirs):
        """ Download the 3D model from the provided URL """
        dest = os.path.join(self._tmp_dir, fname)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        # Is already there?
        if os.path.isfile(dest):
            logger.debug(f'Using cached model `{dest}` ({os.path.getsize(dest)})')
            return dest
        logger.debug('Downloading `{}`'.format(url))
        failed = False
        try:
            r = requests.get(url, allow_redirects=True)
        except Exception:
            failed = True
        if failed or r.status_code != 200:
            logger.warning(W_FAILDL+'Failed to download `{}`'.format(url))
            return None
        with open(dest, 'wb') as f:
            f.write(r.content)
        logger.debug(f'- Downloaded {dest} ({os.path.getsize(dest)})')
        return dest

    def wrl_name(self, name, force_wrl):
        """ Try to use the WRL version """
        if not force_wrl:
            return name
        nm, ext = os.path.splitext(name)
        if ext.lower() == '.wrl':
            return name
        nm += '.wrl'
        if os.path.isfile(nm):
            logger.debug('- Forcing WRL '+nm)
            return nm
        return name

    def try_download_kicad(self, model, full_name, downloaded, rel_dirs, force_wrl):
        if not (model.startswith('${KISYS3DMOD}/') or re.search(r"^\$\{KICAD\d+_3DMODEL_DIR\}\/", model)):
            return None
        # This is a model from KiCad, try to download it
        fname = model[model.find('/')+1:]
        replace = None
        if full_name in downloaded:
            # Already downloaded
            return os.path.join(self._tmp_dir, fname)
        # Download the model
        url = self.kicad_3d_url+urllib.parse.quote_plus(fname)+self.kicad_3d_url_suffix
        replace = self.download_model(url, fname, rel_dirs)
        if not replace:
            return None
        # Successfully downloaded
        downloaded.add(full_name)
        # If this is a .wrl also download the .step
        extra_fname = None
        if fname.endswith('.wrl'):
            extra_fname = fname[:-4]+'.step'
        elif force_wrl:  # This should be a .step, so we download the wrl
            extra_fname = os.path.splitext(fname)[0]+'.wrl'
        if extra_fname is not None:
            url = self.kicad_3d_url+urllib.parse.quote_plus(extra_fname)+self.kicad_3d_url_suffix
            self.download_model(url, extra_fname, rel_dirs)
        return replace

    def try_download_easyeda(self, model, full_name, downloaded, sch_comp, lcsc_field):
        if not lcsc_field or not sch_comp:
            return None
        lcsc_id = sch_comp.get_field_value(lcsc_field)
        if not lcsc_id:
            return None
        fname = os.path.basename(model)
        cache_name = os.path.join(self._tmp_dir, fname)
        if full_name in downloaded:
            # Already downloaded
            return cache_name
        if os.path.isfile(cache_name):
            downloaded.add(full_name)
            logger.debug('Using cached model `{}`'.format(cache_name))
            return cache_name
        logger.debug('- Trying to download {} component as {}/{}'.format(lcsc_id, self._tmp_dir, fname))
        try:
            replace = download_easyeda_3d_model(lcsc_id, self._tmp_dir, fname)
        except Exception as e:
            logger.non_critical_error(f'Error downloading 3D model for LCSC part {lcsc_id} (model: {model} problem: {e})')
            replace = None
        if not replace:
            return None
        # Successfully downloaded
        downloaded.add(full_name)
        return replace

    def is_tht_resistor(self, name):
        # Works for R_Axial_DIN* KiCad 6.0.10 3D models
        name = os.path.splitext(os.path.basename(name))[0]
        return name.startswith('R_Axial_DIN')

    def colored_tht_resistor_name(self, name, bars):
        name = os.path.splitext(os.path.basename(name))[0]
        return os.path.join(self._tmp_dir, name+'_'+'_'.join(map(str, bars))+'.wrl')

    def add_tht_resistor_colors(self, file, colors):
        for bar, c in enumerate(colors):
            col = COLORS[c]
            file.write("Shape {\n")
            file.write("\t\tappearance Appearance {material DEF RES-BAR-%02d Material {\n" % (bar+1))
            file.write("\t\tambientIntensity {}\n".format(col[0]))
            file.write("\t\tdiffuseColor {} {} {}\n".format(col[1], col[2], col[3]))
            file.write("\t\tspecularColor {} {} {}\n".format(col[4], col[5], col[6]))
            file.write("\t\temissiveColor 0.0 0.0 0.0\n")
            file.write("\t\ttransparency 0.0\n")
            file.write("\t\tshininess {}\n".format(col[7]))
            file.write("\t\t}\n")
            file.write("\t}\n")
            file.write("}\n")

    def write_tht_resistor_strip(self, points, file, axis, n, mat, index, only_coord=False):
        if not only_coord:
            file.write("Shape { geometry IndexedFaceSet\n")
            file.write(index)
        end = points[0][axis]
        start = points[2][axis]
        length = start-end
        length/15
        n_start = start-self.starts[n]*length
        n_end = n_start-self.widths[n]*length
        new_points = []
        for p in points:
            ax = []
            for a, v in enumerate(p):
                if a == axis:
                    ax.append("%.3f" % (n_start if v == start else n_end))
                else:
                    ax.append("%.3f" % v)
            new_points.append(' '.join(ax))
        file.write("coord Coordinate { point ["+','.join(new_points)+"]\n")
        if only_coord:
            return
        file.write("}}\n")
        file.write("appearance Appearance{material USE "+mat+" }\n")
        file.write("}\n")

    def create_colored_tht_resistor(self, ori, name, bars, r_len):
        # ** Process the 3D model
        # Fill the starts
        ac = 0
        self.starts = []
        for c, w in enumerate(self.widths):
            self.starts.append(ac/100)
            self.widths[c] = w/100
            ac += w
        # Create the model
        coo_re = re.compile(r"coord Coordinate \{ point \[((\S+ \S+ \S+,?)+)\](.*)")
        with open(ori, "rt") as f:
            prev_ln = None
            points = None
            axis = None
            os.makedirs(os.path.dirname(name), exist_ok=True)
            with open(name, "wt") as d:
                colors_defined = False
                for ln in f:
                    if not colors_defined and ln.startswith('Shape { geometry IndexedFaceSet'):
                        self.add_tht_resistor_colors(d, bars)
                        colors_defined = True
                    m = coo_re.match(ln)
                    if m:
                        index = prev_ln
                        points = [tuple(float(v) for v in x.split(' ')) for x in m.group(1).split(',')]
                        x_len = (points[0][X]-points[2][X])*2.54*2
                        if abs(x_len-r_len) < 0.01:
                            logger.debug('  - Found horizontal: {}'.format(round(x_len, 2)))
                            self.write_tht_resistor_strip(points, d, X, 0, 'PIN-01', index, only_coord=True)
                            # d.write(ln)
                            axis = X
                        else:
                            y_len = (points[0][Z]-points[2][Z])*2.54*2
                            if abs(y_len-r_len) < 0.01:
                                logger.debug('  - Found vertical: {}'.format(round(y_len, 2)))
                                self.write_tht_resistor_strip(points, d, Z, 0, 'PIN-01', index, only_coord=True)
                                axis = Z
                            else:
                                d.write(ln)
                                points = None
                    else:
                        d.write(ln)
                    if ln == "}\n" and points is not None:
                        for st in range(1, len(self.widths)):
                            bar = (st >> 1)+1
                            self.write_tht_resistor_strip(points, d, axis, st,
                                                          'RES-BAR-%02d' % bar if st % 2 else 'RES-THT-01', index)
                        points = None
                    prev_ln = ln
        # Copy the STEP model (no colors)
        step_ori = os.path.splitext(ori)[0]+'.step'
        if os.path.isfile(step_ori):
            step_name = os.path.splitext(name)[0]+'.step'
            copy2(step_ori, step_name)
        else:
            logger.warning(W_MISS3D+'Missing 3D model {}'.format(step_ori))

    def do_colored_tht_resistor(self, name, c, changed):
        if not GS.global_colored_tht_resistors or not self.is_tht_resistor(name) or c is None:
            return name
        # Find the length of the resistor (is in the name of the 3D model)
        m = re.search(r"L([\d\.]+)mm", name)
        if not m:
            logger.warning(W_RES3DNAME+'3D model for resistor without length: {}'.format(name))
            return name
        r_len = float(m.group(1))
        # THT Resistor that we want to add colors
        # Check the value
        res = comp_match(c.value, c.ref_prefix, c.ref)
        if res is None:
            return name
        val = res.get_decimal()
        if val < Decimal('0.01'):
            logger.warning(W_BADRES+'Resistor {} out of range, minimum value is 10 mOhms'.format(c.ref))
            return name
        val_str = "{0:.0f}".format(val*100)
        # Check the tolerance (from the schematic fields)
        tol = next(filter(lambda x: x, map(c.get_field_value, GS.global_field_tolerance)), None)
        if not tol:
            # Try using the parsed value (i.e. Value="12k 1%")
            tol = res.get_extra('tolerance')
            if not tol:
                tol = GS.global_default_resistor_tolerance
                logger.warning(W_BADTOL+'Missing tolerance for {}, using {}%'.format(c.ref, tol))
        else:
            tol = tol.strip()
            if tol[-1] == '%':
                tol = tol[:-1].strip()
            try:
                tol = float(tol)
            except ValueError:
                logger.warning(W_BADTOL+'Malformed tolerance for {}: `{}`'.format(c.ref, tol))
                return name
        if tol not in TOL_COLORS:
            logger.warning(W_BADTOL+'Unknown tolerance for {}: `{}`'.format(c.ref, tol))
            return name
        tol_color = TOL_COLORS[tol]
        # Find how many bars we'll use
        if tol < 5:
            # Use 5 bars for 2 % tol or better
            self.widths = WIDTHS_5.copy()
            nbars = 5
        else:
            self.widths = WIDTHS_4.copy()
            nbars = 4
        bars = [0]*nbars
        # Bars with digits
        dig_bars = nbars-2
        # Fill the multiplier
        mult = len(val_str)-nbars
        if mult < 0:
            val_str = val_str.rjust(dig_bars, '0')
            mult = min(9-mult, 11)
        bars[dig_bars] = mult
        # Max is all 99 with 9 as multiplier
        max_val = pow(10, dig_bars)-1
        if val > max_val*1e9:
            logger.warning(W_BADRES+'Resistor {} out of range, maximum value is {} GOhms'.format(c.ref, max_val))
            return name
        # Fill the digits
        for bar in range(dig_bars):
            bars[bar] = ord(val_str[bar])-ord('0')
        # Make sure we don't have digits that can't be represented
        rest = val_str[dig_bars:]
        if rest and not all((x == '0' for x in rest)):
            logger.warning(W_RESVALISSUE+'Digits not represented in {} {} ({} %)'.format(c.ref, c.value, tol))
        bars[nbars-1] = tol_color
        # For 20% remove the last bar
        if tol_color == 12:
            bars = bars[:-1]
            self.widths[-3] = self.widths[-1]+self.widths[-2]+self.widths[-3]
            self.widths = self.widths[:-2]
        # Create the name in the cache
        cache_name = self.colored_tht_resistor_name(name, bars)
        if os.path.isfile(cache_name) and GS.global_cache_3d_resistors:
            status = 'cached'
        else:
            status = 'created'
            self.create_colored_tht_resistor(name, cache_name, bars, r_len)
        changed[0] = True
        # Show the result
        logger.debug(' - {} {} {}% {} ({})'.format(c.ref, c.value, tol, bars, status))
        return cache_name

    def replace_model(self, replace, m3d, force_wrl, is_copy_mode, rename_function, rename_data):
        """ Helper function to replace the 3D model in m3d using the `replace` file """
        self.source_models.add(replace)
        old_name = m3d.m_Filename
        new_name = self.wrl_name(replace, force_wrl) if not is_copy_mode else rename_function(rename_data, replace)
        self._undo_3d_models[new_name] = old_name
        if GS.debug_level > 2:
            try:
                fsize = os.path.getsize(new_name)
                fhash = get_file_hash(new_name)
            except FileNotFoundError:
                fsize = 'not found'
                fhash = 'unknown'
            logger.debug(f' - Replacing 3D model `{m3d.m_Filename}` by `{new_name}` ({fsize} - {fhash})')
        m3d.m_Filename = new_name
        self.models_replaced = True

    def download_models(self, rename_filter=None, rename_function=None, rename_data=None, force_wrl=False, all_comps=None):
        """ Check we have the 3D models.
            Inform missing models.
            Try to download the missing models
            Stores changes in self._undo_3d_models_rep """
        self.models_replaced = False
        # Load KiCad configuration so we can expand the 3D models path
        KiConf.init(GS.pcb_file)
        # List of models we already downloaded
        downloaded = set()
        # For the mode where we copy the 3D models
        self.source_models = set()
        is_copy_mode = rename_filter is not None
        rel_dirs = getattr(rename_data, 'rel_dirs', [])
        extra_debug = GS.debug_level > 3
        if all_comps is None:
            all_comps = []
        all_comps_hash = {c.ref: c for c in all_comps}
        # Find the LCSC field
        lcsc_field = self.solve_field_name('_field_lcsc_part', empty_when_none=True)
        # Find a place to store the downloaded models
        if self._tmp_dir is None:
            self._tmp_dir = os.environ.get('KIBOT_3D_MODELS')
            if self._tmp_dir is None:
                self._tmp_dir = os.path.join(os.path.expanduser('~'), '.cache', 'kibot', '3d')
            else:
                self._tmp_dir = os.path.abspath(self._tmp_dir)
            logger.debug('Using `{}` as dir for downloaded 3D models'.format(self._tmp_dir))
        rel_dirs.append(self._tmp_dir)
        self.used_3d_models = {}
        # Look for all the footprints
        for m in GS.get_modules():
            ref = m.GetReference()
            lib_id = m.GetFPID()
            lib_nickname = str(lib_id.GetLibNickname())
            sch_comp = all_comps_hash.get(ref, None)
            # Extract the models (the iterator returns copies)
            models = m.Models()
            models_l = []
            while not models.empty():
                models_l.append(models.pop())
            # Look for all the 3D models for this footprint
            for m3d in models_l:
                if m3d.m_Filename.endswith(DISABLE_3D_MODEL_TEXT):
                    # Skip models we intentionally disabled using a bogus name
                    if extra_debug:
                        logger.debug("- Skipping {} (disabled)".format(m3d.m_Filename))
                    continue
                if is_copy_mode and not fnmatch(m3d.m_Filename, rename_filter):
                    # Skip filtered footprints
                    continue
                used_extra = [False]
                full_name, is_embedded = do_expand_env(m3d.m_Filename, used_extra, extra_debug, lib_nickname)
                if is_embedded:
                    # Inside the PCB file, must be there
                    continue
                if not os.path.isfile(full_name):
                    # Missing 3D model
                    logger.debugl(2, 'Missing 3D model file {} ({})'.format(full_name, m3d.m_Filename))
                    if self.download:
                        replace = self.try_download_kicad(m3d.m_Filename, full_name, downloaded, rel_dirs, force_wrl)
                        if replace is None and self.download_lcsc:
                            replace = self.try_download_easyeda(m3d.m_Filename, full_name, downloaded, sch_comp, lcsc_field)
                        if replace:
                            replace = self.do_colored_tht_resistor(replace, sch_comp, used_extra)
                            self.replace_model(replace, m3d, force_wrl, is_copy_mode, rename_function, rename_data)
                    if full_name not in downloaded:
                        logger.warning(W_MISS3D+'Missing 3D model for {}: `{}`'.format(ref, full_name))
                    else:
                        self.used_3d_models[os.path.basename(replace)] = replace
                else:  # File was found
                    replace = self.do_colored_tht_resistor(full_name, sch_comp, used_extra)
                    self.used_3d_models[os.path.basename(replace)] = replace
                    if used_extra[0] or is_copy_mode:
                        # The file is there, but we got it expanding a user defined text
                        # This is completely valid for KiCad, but kicad2step doesn't support it
                        if not self.models_replaced and extra_debug:
                            logger.debug('- Modifying models with text vars')
                        self.replace_model(replace, m3d, force_wrl, is_copy_mode, rename_function, rename_data)
            # Push the models back
            for model in reversed(models_l):
                models.append(model)
        if downloaded:
            logger.warning(W_DOWN3D+' {} 3D models downloaded or cached'.format(len(downloaded)))
        return self.models_replaced if not is_copy_mode else list(self.source_models)

    def list_models(self, even_missing=False):
        """ Get the list of 3D models """
        # Load KiCad configuration so we can expand the 3D models path
        KiConf.init(GS.pcb_file)
        models = set()
        # Look for all the footprints
        for m in GS.get_modules():
            # Look for all the 3D models for this footprint
            for m3d in m.Models():
                full_name = KiConf.expand_env(m3d.m_Filename)
                if even_missing or os.path.isfile(full_name):
                    models.add(full_name)
        return list(models)

    def filter_components(self, highlight=None, force_wrl=False, also_sch=False):
        if not self._comps:
            # No filters, but we need to apply some stuff
            all_comps = None
            dnp_removed = False
            # Get a list of components in the schematic. Enables downloading LCSC parts.
            if GS.sch_file:
                GS.load_sch()
                all_comps = GS.sch.get_components()
                if (GS.global_kicad_dnp_applies_to_3D and any((c.kicad_dnp is not None and c.kicad_dnp for c in all_comps))):
                    # One or more components are DNP, remove them
                    reset_filters(all_comps)
                    all_comps_hash = {c.ref: c for c in all_comps}
                    self.remove_3D_models(GS.board, all_comps_hash)
                    dnp_removed = True
            # No variant/filter to apply
            if self.download_models(force_wrl=force_wrl, all_comps=all_comps) or dnp_removed:
                # Some missing components found and we downloaded them
                # Save the fixed board
                ret = self.save_tmp_board()
                if also_sch and GS.sch_file:
                    link_name = ret.replace('.kicad_pcb', '.kicad_sch')
                    os.symlink(GS.sch_file, link_name)
                    self._files_to_remove.append(link_name)
                # Undo the changes done during download
                self.undo_3d_models_rename(GS.board)
                if dnp_removed:
                    self.restore_3D_models(GS.board, all_comps_hash)
                return ret
            return GS.pcb_file
        self.filter_pcb_components(do_3D=True, do_2D=True, highlight=highlight)
        if also_sch:
            self.download_models(force_wrl=force_wrl, all_comps=self._comps, rename_function=abs_path_model,
                                 rename_filter='*')
            fname, pcb_dir = self.save_tmp_dir_board('3D')
            replaced_images = self.sch_replace_images(GS.sch)
            GS.sch.save_variant(pcb_dir)
            if replaced_images:
                self.sch_restore_images(GS.sch)
            self._files_to_remove.append(pcb_dir)
        else:
            self.download_models(force_wrl=force_wrl, all_comps=self._comps)
            fname = self.save_tmp_board()
        self.unfilter_pcb_components(do_3D=True, do_2D=True)
        return fname

    def get_targets(self, out_dir):
        return [self._parent.expand_filename(out_dir, self.output)]

    def remove_temporals(self):
        super().remove_temporals()
        self._tmp_dir = None


class Base3DOptionsWithHL(Base3DOptions):
    """ 3D options including which components will be displayed and highlighted """
    def __init__(self):
        with document:
            self.show_components = Optionable
            """ *[list(string)|string='all'] [none,all,*] List of components to draw, can be also a string for `none` or `all`.
                Ranges like *R5-R10* are supported.
                Unlike the `pcbdraw` output, the default is `all` """
            self.highlight = Optionable
            """ [list(string)=[]] List of components to highlight. Ranges like *R5-R10* are supported """
            self.highlight_padding = 1.5
            """ [0,1000] How much the highlight extends around the component [mm] """
            self.highlight_on_top = False
            """ Highlight over the component (not under) """
        super().__init__()

    def config(self, parent):
        super().config(parent)
        self._filters_to_expand = False
        # List of components
        self._show_all_components = False
        self._show_components_raw = self.show_components
        if len(self.show_components) == 1 and self.show_components[0] in {'all', 'none'}:
            if self.show_components[0] == 'all':
                self._show_all_components = True
            else:  # if self.show_components[0] == 'none':
                self.show_components = []
        else:  # a list
            self.show_components = self.solve_kf_filters(self.show_components)
        # Highlight
        self._highlight = self.solve_kf_filters(self.highlight)

    def copy_options(self, ref):
        """ Copy its options from another similar object """
        super().copy_options(ref)
        self.show_components = ref.show_components
        self._highlight = ref._highlight
        self.highlight_padding = ref.highlight_padding
        self.highlight_on_top = ref.highlight_on_top
        self._filters_to_expand = ref._filters_to_expand
        self._show_all_components = ref._show_all_components


class Base3D(BaseOutput):
    def __init__(self):
        super().__init__()

    def get_dependencies(self):
        files = super().get_dependencies()
        files.extend(self.options.list_models())
        return files
