# -*- coding: utf-8 -*-
# Copyright (c) 2020-2024 Salvador E. Tropea
# Copyright (c) 2020-2024 Instituto Nacional de Tecnología Industrial
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)
from base64 import b64encode
from copy import deepcopy
import math
import os
import re
from shutil import rmtree
from .bom.columnlist import ColumnList
from .gs import GS
from .kicad.pcb import replace_footprints
from .kicad.v6_sch import SchematicBitmapV6, Stroke, Color
from .kiplot import get_all_components, look_for_output, get_output_targets, run_output
from .misc import (Rect, W_WRONGPASTE, DISABLE_3D_MODEL_TEXT, W_NOCRTYD, MOD_ALLOW_MISSING_COURTYARD, W_MISSDIR, W_KEEPTMP,
                   RENDERERS, read_png)
if not GS.kicad_version_n:
    # When running the regression tests we need it
    from kibot.__main__ import detect_kicad
    detect_kicad()
if GS.ki6:
    # New name, no alias ...
    from pcbnew import FP_3DMODEL, LSET, ToMM, wxPoint
else:
    from pcbnew import wxPoint, LSET, MODULE_3D_SETTINGS, ToMM
    FP_3DMODEL = MODULE_3D_SETTINGS
from .registrable import RegOutput
from .optionable import Optionable, BaseOptions
from .fil_base import BaseFilter, apply_fitted_filter, reset_filters, apply_pre_transform, apply_exclude_filter
from .kicad.config import KiConf
from .macros import macros, document  # noqa: F401
from .error import KiPlotConfigurationError
from . import log

logger = log.get_logger()
HIGHLIGHT_3D_WRL = """#VRML V2.0 utf8
#KiBot generated highlight
Shape {
  appearance Appearance {
    material DEF RED-01 Material {
      ambientIntensity 0.494
      diffuseColor 1.0 0.0 0.0
      specularColor 0.5 0.0 0.0
      emissiveColor 0.0 0.0 0.0
      transparency 0.5
      shininess 0.25
    }
  }
}
Shape {
  geometry Box { size 1 1 1 }
  appearance Appearance {material USE RED-01 }
}

"""
comp_range_regex = re.compile(r'([a-zA-Z]+)(\d+)-([a-zA-Z]+)(\d+)')


class BaseOutput(RegOutput):
    def __init__(self):
        super().__init__()
        with document:
            self.name = ''
            """ *Used to identify this particular output definition.
                Avoid using `_` as first character. These names are reserved for KiBot """
            self.type = ''
            """ *Type of output """
            self.dir = './'
            """ *Output directory for the generated files.
                If it starts with `+` the rest is concatenated to the default dir """
            self.comment = ''
            """ *A comment for documentation purposes. It helps to identify the output """
            self.extends = ''
            """ Copy the `options` section from the indicated output.
                Used to inherit options from another output of the same type """
            self.run_by_default = True
            """ When enabled this output will be created when no specific outputs are requested """
            self.disable_run_by_default = ''
            """ [string|boolean=''] Use it to disable the `run_by_default` status of other output.
                Useful when this output extends another and you don't want to generate the original.
                Use the boolean true value to disable the output you are extending """
            self.output_id = ''
            """ Text to use for the %I expansion content. To differentiate variations of this output """
            self.category = Optionable
            """ [string|list(string)=''] {comma_sep} The category for this output. If not specified an internally defined
                category is used.
                Categories looks like file system paths, i.e. **PCB/fabrication/gerber**.
                Using '.' or './' as a category puts the file at the root.
                The categories are currently used for `navigate_results` and `navigate_results_rb` """
            self.priority = 50
            """ [0,100] Priority for this output. High priority outputs are created first.
                Internally we use 10 for low priority, 90 for high priority and 50 for most outputs """
            self.groups = Optionable
            """ [string|list(string)=''] One or more groups to add this output. In order to catch typos
                we recommend to add outputs only to existing groups. You can create an empty group if
                needed """
        if GS.global_dir:
            self.dir = GS.global_dir
        self._sch_related = False    # True if we need an schematic
        self._both_related = False   # True if we need an schematic AND a PCB
        self._none_related = False   # True if not related to the schematic AND the PCB
        self._any_related = False    # True if we need an schematic OR a PCB
        self._unknown_is_error = True
        self._done = False
        self._category = None

    @staticmethod
    def attr2longopt(attr):
        return '--'+attr.replace('_', '-')

    def is_sch(self):
        """ True for outputs that needs the schematic """
        return self._sch_related or self._both_related

    def is_pcb(self):
        """ True for outputs that needs the PCB """
        return (not self._sch_related and not self._none_related and not self._any_related) or self._both_related

    def is_any(self):
        """ True for outputs that needs the schematic and/or the PCB """
        return self._any_related

    def get_targets(self, out_dir):
        """ Returns a list of targets generated by this output """
        if not (hasattr(self, "options") and hasattr(self.options, "get_targets")):
            logger.non_critical_error(f"Output {self} doesn't implement get_targets(), please report it")
            return []
        return self.options.get_targets(out_dir)

    def get_navigate_targets(self, out_dir):
        """ Returns a list of targets suitable for the navigate results """
        return self.get_targets(out_dir), None

    def get_dependencies(self):
        """ Returns a list of files needed to create this output """
        if self._sch_related:
            if GS.sch:
                return GS.sch.get_files()
            return [GS.sch_file]
        return [GS.pcb_file]

    def get_extension(self):
        return self.options._expand_ext

    def config(self, parent):
        if self._tree and not self._configured and isinstance(self.extends, str) and self.extends:
            logger.debug("Extending `{}` from `{}`".format(self.name, self.extends))
            # Copy the data from the base output
            out = RegOutput.get_output(self.extends)
            if out is None:
                raise KiPlotConfigurationError('Unknown output `{}` in `extends`'.format(self.extends))
            if out.type != self.type:
                raise KiPlotConfigurationError('Trying to extend `{}` using another type `{}`'.format(out, self))
            if not out._configured:
                # Make sure the extended output is configured, so it can be an extension of another output
                out.config(None)
            if out._tree:
                options = out._tree.get('options', None)
                if options:
                    old_options = self._tree.get('options', {})
                    # logger.error(self.name+" Old options: "+str(old_options))
                    options = deepcopy(options)
                    options.update(old_options)
                    self._tree['options'] = options
                    # logger.error(self.name+" New options: "+str(options))
        super().config(parent)
        to_dis = self.disable_run_by_default
        if isinstance(to_dis, str) and to_dis:  # Skip the boolean case
            out = RegOutput.get_output(to_dis)
            if out is None:
                raise KiPlotConfigurationError('Unknown output `{}` in `disable_run_by_default`'.format(to_dis))
        if self.dir[0] == '+':
            self.dir = (GS.global_dir if GS.global_dir is not None else './') + self.dir[1:]
        if not self.category:
            self.category = self.force_list(self._category)

    def expand_dirname(self, out_dir):
        return self.options.expand_filename_both(out_dir, is_sch=self._sch_related)

    def expand_filename(self, out_dir, name):
        name = self.options.expand_filename_both(name, is_sch=self._sch_related)
        return os.path.abspath(os.path.join(out_dir, name))

    @staticmethod
    def get_conf_examples(name, layers):
        return None

    @staticmethod
    def simple_conf_examples(name, comment, dir):
        gb = {}
        outs = [gb]
        gb['name'] = 'basic_'+name
        gb['comment'] = comment
        gb['type'] = name
        gb['dir'] = dir
        return outs

    def fix_priority_help(self):
        self._help_priority = self._help_priority.replace('[number=50]', '[number={}]'.format(self.priority))

    def get_csv_separator(self):
        """ Default separator for CSV files """
        return ','

    def run(self, output_dir):
        self.output_dir = output_dir
        output = self.options.output if hasattr(self.options, 'output') else ''
        target = os.path.realpath(self.expand_filename(output_dir, output))
        # Ensure the destination dir already exists
        target_dir = os.path.dirname(os.path.abspath(target))
        if not os.path.isdir(target_dir):
            logger.warning(W_MISSDIR+f'Missing target directory `{target_dir}`, creating it')
            logger.warning(W_MISSDIR+'Note: use the `dir` option properly or just create the dir before running KiBot')
            os.makedirs(target_dir)
        self.options.run(target)


class BoMRegex(Optionable):
    """ Implements the pair column/regex """
    def __init__(self):
        super().__init__()
        self._unknown_is_error = True
        with document:
            self.column = ''
            """ Name of the column to apply the regular expression.
                Use `_field_lcsc_part` to get the value defined in the global options """
            self.regex = ''
            """ Regular expression to match """
            self.field = None
            """ {column} """
            self.regexp = None
            """ {regex} """
            self.skip_if_no_field = False
            """ Skip this test if the field doesn't exist """
            self.match_if_field = False
            """ Match if the field exists, no regex applied. Not affected by `invert` """
            self.match_if_no_field = False
            """ Match if the field doesn't exists, no regex applied. Not affected by `invert` """
            self.invert = False
            """ Invert the regex match result """
        self._column_example = ColumnList.COL_REFERENCE

    def config(self, parent):
        super().config(parent)
        if not self.column:
            raise KiPlotConfigurationError("Missing or empty `column` in field regex ({})".format(str(self._tree)))

    def __str__(self):
        invert = '!' if self.invert else ''
        return f'{self.column} {invert}`{self.regex}`'


class VariantOptions(BaseOptions):
    """ BaseOptions plus generic support for variants. """
    def __init__(self):
        with document:
            self.variant = ''
            """ Board variant to apply """
            self.pre_transform = Optionable
            """ [string|list(string)='_null'] Name of the filter to transform fields before applying other filters.
                Is a short-cut to use for simple cases where a variant is an overkill.
                Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
                variant """
            self.exclude_filter = Optionable
            """ [string|list(string)='_null'] Name of the filter to exclude components from processing.
                Is a short-cut to use for simple cases where a variant is an overkill.
                Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
                variant """
            self.dnf_filter = Optionable
            """ [string|list(string)='_null'] Name of the filter to mark components as not fitted.
                Is a short-cut to use for simple cases where a variant is an overkill.
                Can be used to fine-tune a variant for a particular output that needs extra filtering done before the
                variant """
        super().__init__()
        self._comps = None
        self._sub_pcb = None
        self._undo_3d_models = {}
        self._undo_3d_models_rep = {}
        self._highlight_3D_file = None
        self._highlighted_3D_components = None
        # Use a condensed list of components. Repeated references are listed once. Sub-units are represented by one
        self._collapse_components = True

    def config(self, parent):
        super().config(parent)
        self.variant = RegOutput.check_variant(self.variant)
        self.dnf_filter = BaseFilter.solve_filter(self.dnf_filter, 'dnf_filter')
        self.pre_transform = BaseFilter.solve_filter(self.pre_transform, 'pre_transform', is_transform=True)
        self.exclude_filter = BaseFilter.solve_filter(self.exclude_filter, 'exclude_filter')

    def copy_options(self, ref):
        self.variant = ref.variant
        self.dnf_filter = ref.dnf_filter
        self.pre_transform = ref.pre_transform
        self.exclude_filter = ref.exclude_filter

    def get_refs_hash(self):
        if not self._comps:
            return None
        return {c.ref: c for c in self._comps}

    def get_refs_hash_multi(self):
        """ This version allows having multiple components with the same reference.
            Is useful for things like a panel """
        if not self._comps:
            return None
        comps_hash = {}
        for c in self._comps:
            cur_list = comps_hash.get(c.ref, [])
            cur_list.append(c)
            comps_hash[c.ref] = cur_list
        return comps_hash

    def get_fitted_refs(self):
        """ List of fitted and included components """
        if not self._comps:
            return []
        return [c.ref for c in self._comps if c.fitted and c.included]

    def get_not_fitted_refs(self, parent=False):
        """ List of 'not fitted' components, also includes 'not included' """
        if not self._comps:
            return []
        if not parent:
            return [c.ref for c in self._comps if not c.fitted or not c.included]
        # Here we want only parent components
        return list({c.get_parent_ref() for c in self._comps if not c.fitted or not c.included})

    def help_only_sub_pcbs(self):
        self.add_to_doc('variant', 'Used for sub-PCBs')

    # Here just to avoid pulling pcbnew for this
    @staticmethod
    def to_mm(val):
        return ToMM(val)

    @staticmethod
    def cross_module(m, rect, layer, angle):
        """ Draw a cross over a module.
            The rect is a Rect object with the size.
            The layer is which layer id will be used.
            The angle is the cross angle, which matches the footprint. """
        center = GS.p2v_k7(m.GetCenter())
        seg1 = GS.create_module_element(m)
        seg1.SetWidth(120000)
        seg1.SetStart(GS.p2v_k7(wxPoint(rect.x1, rect.y1)))
        seg1.SetEnd(GS.p2v_k7(wxPoint(rect.x2, rect.y2)))
        seg1.SetLayer(layer)
        seg1.Rotate(center, GS.angle(angle))
        GS.footprint_update_local_coords(seg1)
        m.Add(seg1)
        seg2 = GS.create_module_element(m)
        seg2.SetWidth(120000)
        seg2.SetStart(GS.p2v_k7(wxPoint(rect.x1, rect.y2)))
        seg2.SetEnd(GS.p2v_k7(wxPoint(rect.x2, rect.y1)))
        seg2.SetLayer(layer)
        seg2.Rotate(center, GS.angle(angle))
        GS.footprint_update_local_coords(seg2)
        m.Add(seg2)
        return [seg1, seg2]

    def cross_modules(self, board, comps_hash):
        """ Draw a cross in all 'not fitted' modules using *.Fab layer for
            component positions and plots them on the provided tlayer (top)
            and blayer (bottom) """
        if comps_hash is None or not GS.global_cross_footprints_for_dnp:
            return
        # Cross the affected components
        ffab = board.GetLayerID('F.Fab')
        bfab = board.GetLayerID('B.Fab')
        tlay = board.GetLayerID(GS.global_dnp_cross_top_layer)
        blay = board.GetLayerID(GS.global_dnp_cross_bottom_layer)
        extra_tlay_lines = []
        extra_blay_lines = []
        for m in GS.get_modules_board(board):
            ref = m.GetReference()
            # Rectangle containing the drawings, no text
            frect = Rect()
            brect = Rect()
            c = comps_hash.get(ref, None)
            if c and c.included and not c.fitted:
                # Measure the component BBox (only graphics)
                fp_angle = m.GetOrientationDegrees()
                center = GS.p2v_k7(m.GetCenter())
                m.Rotate(center, GS.angle(-fp_angle))
                for gi in m.GraphicalItems():
                    if gi.GetClass() == GS.footprint_gr_type:
                        l_gi = gi.GetLayer()
                        if l_gi == ffab:
                            frect.Union(GS.get_rect_for(gi.GetBoundingBox()))
                        if l_gi == bfab:
                            brect.Union(GS.get_rect_for(gi.GetBoundingBox()))
                # Rotate the footprint back (using the same center)
                m.Rotate(center, GS.angle(fp_angle))
                # Cross the graphics in *.Fab
                if frect.x1 is not None:
                    extra_tlay_lines.append(self.cross_module(m, frect, tlay, fp_angle))
                else:
                    extra_tlay_lines.append(None)
                if brect.x1 is not None:
                    extra_blay_lines.append(self.cross_module(m, brect, blay, fp_angle))
                else:
                    extra_blay_lines.append(None)
        # Remmember the data used to undo it
        self.extra_tlay_lines = extra_tlay_lines
        self.extra_blay_lines = extra_blay_lines

    def uncross_modules(self, board, comps_hash):
        """ Undo the crosses in provided top or bottom layers (default *.Fab) """
        if comps_hash is None or not GS.global_cross_footprints_for_dnp:
            return
        # Undo the drawings
        for m in GS.get_modules_board(board):
            ref = m.GetReference()
            c = comps_hash.get(ref, None)
            if c and c.included and not c.fitted:
                restore = self.extra_tlay_lines.pop(0)
                if restore:
                    for line in restore:
                        m.Remove(line)
                restore = self.extra_blay_lines.pop(0)
                if restore:
                    for line in restore:
                        m.Remove(line)

    def detect_solder_paste(self, board):
        """ Detects if the top and/or bottom layer has solder paste """
        fpaste = board.GetLayerID('F.Paste')
        bpaste = board.GetLayerID('B.Paste')
        top = bottom = False
        for m in GS.get_modules_board(board):
            for p in m.Pads():
                pad_layers = p.GetLayerSet()
                if not top and fpaste in pad_layers.Seq():
                    top = True
                if not bottom and bpaste in pad_layers.Seq():
                    bottom = True
                if top and bottom:
                    return top, bottom
        return top, bottom

    def remove_paste_and_glue(self, board, comps_hash):
        """ Remove from solder paste layers the filtered components. """
        if comps_hash is None or not (GS.global_remove_solder_paste_for_dnp or GS.global_remove_adhesive_for_dnp or
                                      GS.global_remove_solder_mask_for_dnp):
            return
        logger.debug('Removing paste, mask and/or glue')
        exclude = LSET()
        fpaste = board.GetLayerID('F.Paste')
        bpaste = board.GetLayerID('B.Paste')
        exclude.addLayer(fpaste)
        exclude.addLayer(bpaste)
        old_layers = []
        fadhes = board.GetLayerID('F.Adhes')
        badhes = board.GetLayerID('B.Adhes')
        old_fadhes = []
        old_badhes = []
        old_fmask = []
        old_bmask = []
        rescue = board.GetLayerID(GS.global_work_layer)
        fmask = board.GetLayerID('F.Mask')
        bmask = board.GetLayerID('B.Mask')
        if GS.global_remove_solder_mask_for_dnp:
            exclude.addLayer(fmask)
            exclude.addLayer(bmask)
        for m in GS.get_modules_board(board):
            ref = m.GetReference()
            c = comps_hash.get(ref, None)
            if c and not c.fitted:
                # Remove all pads from *.Paste
                if GS.global_remove_solder_paste_for_dnp or GS.global_remove_solder_mask_for_dnp:
                    old_c_layers = []
                    for p in m.Pads():
                        pad_layers = p.GetLayerSet()
                        is_front = (fpaste in pad_layers.Seq()) or (fmask in pad_layers.Seq())
                        old_c_layers.append(pad_layers.FmtHex())
                        pad_layers.removeLayerSet(exclude)
                        if len(pad_layers.Seq()) == 0:
                            # No layers at all. Ridiculous, but happens.
                            # At least add an F.Mask
                            pad_layers.addLayer(fmask if is_front else bmask)
                            pad_name = p.GetName()
                            # Some footprints has solder paste "pads" they don't have a name
                            if pad_name or GS.global_always_warn_about_paste_pads:
                                logger.warning(f"{W_WRONGPASTE}Pad with solder paste, but no copper or solder mask aperture "
                                               f" in {ref} ({pad_name})")
                        p.SetLayerSet(pad_layers)
                    old_layers.append(old_c_layers)
                    logger.debugl(3, '- Removed paste/mask from '+ref)
                # Remove any graphical item in the *.Adhes layers
                if GS.global_remove_adhesive_for_dnp:
                    found = False
                    for gi in m.GraphicalItems():
                        l_gi = gi.GetLayer()
                        if l_gi == fadhes:
                            gi.SetLayer(rescue)
                            old_fadhes.append(gi)
                            found = True
                        if l_gi == badhes:
                            gi.SetLayer(rescue)
                            old_badhes.append(gi)
                            found = True
                    if found:
                        logger.debugl(3, '- Removed adhesive from '+ref)
                if GS.global_remove_solder_mask_for_dnp:
                    found = False
                    for gi in m.GraphicalItems():
                        l_gi = gi.GetLayer()
                        if l_gi == fmask:
                            gi.SetLayer(rescue)
                            old_fmask.append(gi)
                            found = True
                        if l_gi == bmask:
                            gi.SetLayer(rescue)
                            old_bmask.append(gi)
                            found = True
                    if found:
                        logger.debugl(3, '- Removed mask from '+ref)
        # Store the data to undo the above actions
        self._old_layers = old_layers
        self._old_fadhes = old_fadhes
        self._old_badhes = old_badhes
        self._old_fmask = old_fmask
        self._old_bmask = old_bmask
        self._fadhes = fadhes
        self._badhes = badhes
        self._fmask = fmask
        self._bmask = bmask
        return exclude

    def restore_paste_and_glue(self, board, comps_hash):
        if comps_hash is None:
            return
        logger.debug('Restoring paste, mask and/or glue')
        if GS.global_remove_solder_paste_for_dnp or GS.global_remove_solder_mask_for_dnp:
            for m in GS.get_modules_board(board):
                ref = m.GetReference()
                c = comps_hash.get(ref, None)
                if c and not c.fitted:
                    logger.debugl(3, '- Restoring paste/mask for '+ref)
                    restore = self._old_layers.pop(0)
                    for p in m.Pads():
                        pad_layers = p.GetLayerSet()
                        res = restore.pop(0)
                        if GS.ki9:
                            pad_layers.ParseHex(res)
                        else:
                            pad_layers.ParseHex(res, len(res))
                        p.SetLayerSet(pad_layers)
        if GS.global_remove_adhesive_for_dnp:
            for gi in self._old_fadhes:
                gi.SetLayer(self._fadhes)
            for gi in self._old_badhes:
                gi.SetLayer(self._badhes)
        if GS.global_remove_solder_mask_for_dnp:
            for gi in self._old_fmask:
                gi.SetLayer(self._fmask)
            for gi in self._old_bmask:
                gi.SetLayer(self._bmask)

    def remove_graphics_from_layer(self, board, comps_hash, layer_name):
        """ Remove from layer_name the excluded components. """
        if comps_hash is None:
            return None, None
        logger.debug(f'Removing from {layer_name}')
        layer_id = board.GetLayerID(layer_name)
        old_graphs = []
        rescue = board.GetLayerID(GS.global_work_layer)
        for m in GS.get_modules_board(board):
            ref = m.GetReference()
            c = comps_hash.get(ref, None)
            if c is not None and not c.included:
                logger.debugl(3, f'- Removed {ref} drawings from {layer_name}')
                # Remove any graphical item in the *.Fab layers
                for gi in m.GraphicalItems():
                    l_gi = gi.GetLayer()
                    if l_gi == layer_id:
                        gi.SetLayer(rescue)
                        old_graphs.append(gi)
        return layer_id, old_graphs

    def remove_fab(self, board, comps_hash):
        """ Remove from Fab the excluded components. """
        self._ffab, self.old_ffab = self.remove_graphics_from_layer(board, comps_hash, 'F.Fab')
        self._bfab, self.old_bfab = self.remove_graphics_from_layer(board, comps_hash, 'B.Fab')

    def restore_graphics_from_layer(self, board, comps_hash, layer_id, graphs):
        if comps_hash is None:
            return
        for gi in graphs:
            gi.SetLayer(layer_id)

    def restore_fab(self, board, comps_hash):
        self.restore_graphics_from_layer(board, comps_hash, self._ffab, self.old_ffab)
        self.restore_graphics_from_layer(board, comps_hash, self._bfab, self.old_bfab)

    def replace_3D_models(self, models, new_model, c):
        """ Changes the 3D model using a provided model.
            Stores changes in self._undo_3d_models_rep """
        logger.debug('Changing 3D models for '+c.ref)
        # Get the model references
        models_l = []
        while not models.empty():
            models_l.append(models.pop())
        # Check if we have more than one model
        c_models = len(models_l)
        if c_models > 1:
            new_model = new_model.split(',')
            c_replace = len(new_model)
            if c_models != c_replace:
                raise KiPlotConfigurationError('Found {} models in component {}, but {} replacements provided'.
                                               format(c_models, c, c_replace))
        else:
            new_model = [new_model]
        # Change the models
        replaced = []
        for i, m3d in enumerate(models_l):
            replaced.append(m3d.m_Filename)
            m3d.m_Filename = new_model[i]
        self._undo_3d_models_rep[c.ref] = replaced
        # Push the models back
        for model in reversed(models_l):
            models.append(model)

    def undo_3d_models_rename(self, board):
        """ Restores the file name for any renamed 3D module """
        for m in GS.get_modules_board(board):
            # Get the model references
            models = m.Models()
            models_l = []
            while not models.empty():
                models_l.append(models.pop())
            # Fix any changed path
            replaced = self._undo_3d_models_rep.get(m.GetReference())
            for i, m3d in enumerate(models_l):
                if m3d.m_Filename in self._undo_3d_models:
                    m3d.m_Filename = self._undo_3d_models[m3d.m_Filename]
                if replaced:
                    m3d.m_Filename = replaced[i]
            # Push the models back
            for model in reversed(models_l):
                models.append(model)
        # Reset the list of changes
        self._undo_3d_models = {}
        self._undo_3d_models_rep = {}

    def remove_3D_models(self, board, comps_hash):
        """ Removes 3D models for excluded or not fitted components.
            Applies the global_field_3D_model model rename """
        if not comps_hash:
            return
        # Remove the 3D models for not fitted components
        rem_models = []
        for m in GS.get_modules_board(board):
            ref = m.GetReference()
            c = comps_hash.get(ref, None)
            if c:
                # The filter/variant knows about this component
                models = m.Models()
                if not c.fitted:  # c.included was here, but the docs says this is for "BoM processing", not 3D
                    # Not fitted, remove the 3D model
                    rem_m_models = []
                    while not models.empty():
                        rem_m_models.append(models.pop())
                    rem_models.append(rem_m_models)
                else:
                    # Fitted
                    new_model = c.get_field_value(GS.global_field_3D_model)
                    if new_model:
                        # We will change the 3D model
                        self.replace_3D_models(models, new_model, c)
        self.rem_models = rem_models

    def restore_3D_models(self, board, comps_hash):
        """ Restore the removed 3D models.
            Restores the renamed models. """
        self.undo_3d_models_rename(board)
        if not comps_hash:
            return
        # Undo the removing
        for m in GS.get_modules_board(board):
            ref = m.GetReference()
            c = comps_hash.get(ref, None)
            if c and not c.fitted:
                models = m.Models()
                restore = self.rem_models.pop(0)
                for model in reversed(restore):
                    models.append(model)

    def apply_list_of_3D_models(self, enable, slots, m, var):
        if self.extra_debug:
            logger.debug(f"  - Applying {enable} to {slots} for {var}")
        # Disable the unused models adding bogus text to the end
        slots = [int(v) for v in slots if v]
        models = m.Models()
        m_objs = []
        # Extract the models, we get a copy
        while not models.empty():
            m_objs.insert(0, models.pop())
        for i, m3d in enumerate(m_objs):
            if self.extra_debug:
                logger.debug(f"   - {i+1} applies: {i+1 not in slots} {m3d.m_Filename}")
            if i+1 not in slots:
                if enable:
                    # Revert the added text
                    m3d.m_Filename = m3d.m_Filename[:-self.len_disable]
                else:
                    # Not used, add text to make their name invalid
                    m3d.m_Filename += DISABLE_3D_MODEL_TEXT
            # Push it back to the module
            models.push_back(m3d)

    def apply_3D_variant_aspect(self, board, enable=False):
        """ Disable/Enable the 3D models that aren't for this variant.
            This mechanism uses the MTEXT or PCB_TEXT attributes. """
        # The magic text is %variant:slot1,slot2...%
        field_regex = re.compile(r'\%([^:]+):([\d,]*)\%')     # Generic (by name)
        field_regex_sp = re.compile(r'\$([^:]*):([\d,]*)\$')  # Variant specific
        self.extra_debug = extra_debug = GS.debug_level > 3
        if extra_debug:
            logger.debug("{} 3D models that aren't for this variant".format('Enable' if enable else 'Disable'))
        self.len_disable = len(DISABLE_3D_MODEL_TEXT)
        variant_name = self.variant.name if self.variant else 'None'
        for m in GS.get_modules_board(board):
            if extra_debug:
                logger.debug("- Processing module " + m.GetReference())
            default = None
            matched = False
            # Look for text objects
            for gi in m.GraphicalItems():
                if gi.GetClass() in ['MTEXT', 'PCB_TEXT']:
                    # Check if the text matches the magic style
                    text = gi.GetText().strip()
                    match = field_regex.match(text)
                    if match:
                        if extra_debug:
                            logger.debug(f" - By variant name: {text}")
                        # Check if this is for the current variant
                        var = match.group(1)
                        slots = match.group(2).split(',') if match.group(2) else []
                        # Do the match
                        if var == '_default_':
                            default = slots
                            if self.extra_debug:
                                logger.debug('- Found defaults: {}'.format(slots))
                        else:
                            matched = var == variant_name
                        if matched:
                            self.apply_list_of_3D_models(enable, slots, m, var)
                            break
                    else:
                        # Try with the variant specific pattern
                        match = field_regex_sp.match(text)
                        if match:
                            if extra_debug:
                                logger.debug(f" - Variant specific: {text}")
                            var = match.group(1)
                            slots = match.group(2).split(',') if match.group(2) else []
                            # Do the match
                            matched = self.variant.matches_variant(var)
                            if matched:
                                self.apply_list_of_3D_models(enable, slots, m, var)
                                break
            if not matched and default is not None:
                self.apply_list_of_3D_models(enable, slots, m, '_default_')

    def create_3D_highlight_file(self):
        if self._highlight_3D_file:
            return
        tname = GS.tmp_file(content=HIGHLIGHT_3D_WRL, suffix='.wrl', what='temporal highlight', a_logger=logger)
        self._highlight_3D_file = tname
        self._files_to_remove.append(tname)

    def get_crtyd_bbox(self, board, m):
        fcrtyd = board.GetLayerID('F.CrtYd')
        bcrtyd = board.GetLayerID('B.CrtYd')
        bbox = Rect()
        for gi in m.GraphicalItems():
            if gi.GetClass() == GS.footprint_gr_type:
                l_gi = gi.GetLayer()
                if l_gi == fcrtyd or l_gi == bcrtyd:
                    bbox.Union(GS.get_rect_for(gi.GetBoundingBox()))
        return bbox

    def highlight_3D_models(self, board, highlight):
        if not highlight:
            return
        self.create_3D_highlight_file()
        extra_debug = GS.debug_level > 3
        # TODO: Adjust? Configure?
        z = (100.0 if self.highlight_on_top else 0.1)/2.54
        for m in GS.get_modules_board(board):
            ref = m.GetReference()
            if ref not in highlight:
                continue
            models = m.Models()
            m_pos = m.GetPosition()
            rot = m.GetOrientationDegrees()
            if m.IsFlipped():
                rot = 180-rot
            # Measure the courtyard
            bbox = self.get_crtyd_bbox(board, m)
            if bbox.x1 is not None:
                # Use the courtyard as bbox
                w = bbox.x2-bbox.x1
                h = bbox.y2-bbox.y1
                m_cen = wxPoint((bbox.x2+bbox.x1)/2, (bbox.y2+bbox.y1)/2)
            else:
                # No courtyard, ask KiCad
                # Avoid including the text. KiCad 8 can return ridiculous things
                bbox = m.GetBoundingBox() if GS.ki5 else m.GetBoundingBox(False, False)
                w = bbox.GetWidth()
                h = bbox.GetHeight()
                m_cen = m.GetCenter()
                if not (m.GetAttributes() & MOD_ALLOW_MISSING_COURTYARD):
                    logger.warning(W_NOCRTYD+"Missing courtyard for `{}`".format(ref))
            if extra_debug:
                logger.debug(f'Highlight for {ref}')
                logger.debug(f' - Position {ToMM(m_pos.x)}, {ToMM(m_pos.y)}')
                logger.debug(f' - Orientation {rot} (Flipped: {m.IsFlipped()})')
                logger.debug(f' - Center {ToMM(m_cen.x)} {ToMM(m_cen.y)}')
                logger.debug(f' - w,h {ToMM(w)}, {ToMM(h)}')
            # Compute the offset
            off_x = m_cen.x - m_pos.x
            off_y = m_cen.y - m_pos.y
            rrot = math.radians(rot)
            # KiCad coordinates are inverted in the Y axis
            off_y = -off_y
            if m.IsFlipped():
                off_x = -off_x
            # Apply the component rotation
            off_xp = off_x*math.cos(rrot)+off_y*math.sin(rrot)
            off_yp = -off_x*math.sin(rrot)+off_y*math.cos(rrot)
            # Create a new 3D model for the highlight
            hl = FP_3DMODEL()
            hl.m_Scale.x = (ToMM(w)+self.highlight_padding)/2.54
            hl.m_Scale.y = (ToMM(h)+self.highlight_padding)/2.54
            hl.m_Scale.z = z
            hl.m_Rotation.z = rot
            hl.m_Offset.x = ToMM(off_xp)
            hl.m_Offset.y = ToMM(off_yp)
            hl.m_Filename = self._highlight_3D_file
            # Add the model
            models.push_back(hl)
        self._highlighted_3D_components = highlight

    def unhighlight_3D_models(self, board):
        if not self._highlighted_3D_components:
            return
        for m in GS.get_modules_board(board):
            if m.GetReference() not in self._highlighted_3D_components:
                continue
            m.Models().pop()
        self._highlighted_3D_components = None

    def will_filter_pcb_components(self):
        """ True if we will apply filters/variants """
        return self._comps or self._sub_pcb

    def apply_footprint_variants(self, board, comps_hash):
        """ Allows changing the footprints using variants """
        if comps_hash is None:
            return
        # Check if we have footprints that needs change
        to_change = {}
        for m in GS.get_modules_board(board):
            ref = m.GetReference()
            c = comps_hash.get(ref, None)
            if hasattr(c, '_footprint_variant') and c._footprint_variant:
                to_change[c.ref] = c.get_field_value('footprint')
        if not to_change:
            return
        # One or more needs a change
        logger.debug(f'Replacing footprints from variant change {to_change}')
        replace_footprints(GS.pcb_file, to_change, logger, replace_pcb=False)

    def add_parent_comps(self, c, comps):
        if c.parent_component and c.parent_component.ref not in comps:
            comps[c.parent_component.ref] = c.parent_component
            self.add_parent_comps(c.parent_component, comps)

    def include_parents(self, comps):
        new_comps = {}
        for ref, c in comps.items():
            new_comps[ref] = c
            self.add_parent_comps(c, new_comps)
        return new_comps

    def filter_pcb_components(self, do_3D=False, do_2D=True, highlight=None):
        if not self.will_filter_pcb_components():
            return False
        self._comps_hash = self.get_refs_hash()
        # As we will be comparing the reference split components won't match, so include their parents
        self._comps_hash = self.include_parents(self._comps_hash)
        if self._sub_pcb:
            self._sub_pcb.apply(self._comps_hash)
        if self._comps:
            if do_2D:
                self.apply_footprint_variants(GS.board, self._comps_hash)
                self.cross_modules(GS.board, self._comps_hash)
                self.remove_paste_and_glue(GS.board, self._comps_hash)
                if hasattr(self, 'hide_excluded') and self.hide_excluded:
                    self.remove_fab(GS.board, self._comps_hash)
                # Copy any change in the schematic fields to the PCB properties
                # I.e. the value of a component so it gets updated in the *.Fab layer
                # Also useful for iBoM that can read the sch fields from the PCB
                self.sch_fields_to_pcb(GS.board, self._comps_hash)
            if do_3D:
                # Disable the models that aren't for this variant
                self.apply_3D_variant_aspect(GS.board)
                # Remove the 3D models for not fitted components (also rename)
                self.remove_3D_models(GS.board, self._comps_hash)
                # Highlight selected components
                self.highlight_3D_models(GS.board, highlight)
        return True

    def unfilter_pcb_components(self, do_3D=False, do_2D=True):
        if not self.will_filter_pcb_components():
            return
        if do_2D and self._comps_hash:
            self.uncross_modules(GS.board, self._comps_hash)
            self.restore_paste_and_glue(GS.board, self._comps_hash)
            if hasattr(self, 'hide_excluded') and self.hide_excluded:
                self.restore_fab(GS.board, self._comps_hash)
            # Restore the PCB properties and values
            self.restore_sch_fields_to_pcb(GS.board)
        if do_3D and self._comps_hash:
            # Undo the removing (also rename)
            self.restore_3D_models(GS.board, self._comps_hash)
            # Re-enable the modules that aren't for this variant
            self.apply_3D_variant_aspect(GS.board, enable=True)
            # Remove the highlight 3D object
            self.unhighlight_3D_models(GS.board)
        if self._sub_pcb:
            self._sub_pcb.revert(self._comps_hash)

    def set_title(self, title, sch=False):
        self.old_title = None
        if title:
            if sch:
                self.old_title = GS.sch.get_title() or ''
            else:
                tb = GS.board.GetTitleBlock()
                self.old_title = tb.GetTitle()
            text = self.expand_filename_pcb(title)
            if text[0] == '+':
                text = self.old_title+text[1:]
            if sch:
                self.old_title = GS.sch.set_title(text)
            else:
                tb.SetTitle(text)

    def restore_title(self, sch=False):
        if self.old_title is not None:
            if sch:
                GS.sch.set_title(self.old_title)
            else:
                GS.board.GetTitleBlock().SetTitle(self.old_title)
            self.old_title = None

    def sch_fields_to_pcb(self, board, comps_hash):
        """ Change the module/footprint data according to the filtered fields.
            iBoM can parse it. """
        self._sch_fields_to_pcb_bkp = {}
        has_GetFPIDAsString = False
        first = True
        for m in GS.get_modules_board(board):
            if first:
                has_GetFPIDAsString = hasattr(m, 'GetFPIDAsString')
                first = False
            ref = m.GetReference()
            comp = comps_hash.get(ref, None)
            if comp is not None:
                old_value = m.GetValue()
                old_fields = GS.get_fields(m)
                # Introduced in 6.0.6
                old_fp = m.GetFPIDAsString() if has_GetFPIDAsString else None
                fields = {f.name: f.value for f in comp.fields}
                GS.set_fields(m, fields)
                m.SetValue(fields['Value'])
                if has_GetFPIDAsString:
                    m.SetFPIDAsString(fields['Footprint'])
                self._sch_fields_to_pcb_bkp[ref] = (old_value, old_fields, old_fp)
        self._has_GetFPIDAsString = has_GetFPIDAsString

    def restore_sch_fields_to_pcb(self, board):
        """ Undo sch_fields_to_pcb() """
        has_GetFPIDAsString = self._has_GetFPIDAsString
        for m in GS.get_modules_board(board):
            ref = m.GetReference()
            data = self._sch_fields_to_pcb_bkp.get(ref, None)
            if data is not None:
                m.SetValue(data[0])
                if has_GetFPIDAsString:
                    m.SetFPIDAsString(data[2])
                GS.set_fields(m, data[1])

    def patch_prjname(self, fname):
        """ Fixes ${PROJECTNAME} when we save to a temporal PCB """
        with open(fname, 'rt') as fh:
            data = fh.read()
        if '${PROJECTNAME}' in data:
            with open(fname, 'wt') as fh:
                fh.write(data.replace('${PROJECTNAME}', GS.pcb_basename))

    def save_tmp_board(self, dir=None):
        """ Save the PCB to a temporal file.
            Advantage: all relative paths inside the file remains valid
            Disadvantage: the name of the file gets altered """
        fname = GS.tmp_file(suffix='.kicad_pcb', dir=GS.pcb_dir if dir is None else dir, what='modified PCB', a_logger=logger)
        GS.board.Save(fname)
        self.patch_prjname(fname)
        GS.copy_project(fname)
        self._files_to_remove.extend(GS.get_pcb_and_pro_names(fname))
        return fname

    def save_tmp_board_if_variant(self, new_title='', dir=None, do_3D=False):
        """ If we have a variant apply it and save the PCB to a file """
        if not self.will_filter_pcb_components() and not new_title:
            return GS.pcb_file
        logger.debug('Creating modified PCB')
        self.filter_pcb_components(do_3D=do_3D)
        self.set_title(new_title)
        fname = self.save_tmp_board()
        self.restore_title()
        self.unfilter_pcb_components(do_3D=do_3D)
        logger.debug('- Modified PCB: '+fname)
        return fname

    def save_tmp_sch_if_variant(self, force=False):
        if self._comps or force:
            # Save it to a temporal dir
            sch_dir = GS.mkdtemp(self._expand_ext+'_sch_print')
            GS.copy_project_sch(sch_dir)
            fname = GS.sch.save_variant(sch_dir)
            sch_file = os.path.join(sch_dir, fname)
            self._files_to_remove.append(sch_dir)
        else:
            sch_file = GS.sch_file
        return sch_file

    @staticmethod
    def save_tmp_dir_board(id, force_dir=None, forced_name=None):
        """ Save the PCB to a temporal dir.
            Disadvantage: all relative paths inside the file becomes useless
            Advantage: the name of the file remains the same """
        pcb_dir = GS.mkdtemp(id) if force_dir is None else force_dir
        basename = forced_name if forced_name else GS.pcb_basename
        fname = os.path.join(pcb_dir, basename+'.kicad_pcb')
        logger.debug('Storing modified PCB to `{}`'.format(fname))
        GS.board.Save(fname)
        pro_name, _, _ = GS.copy_project(fname)
        KiConf.fix_page_layout(pro_name)
        return fname, pcb_dir

    def solve_kf_filters(self, components):
        """ Solves references to KiBot filters in the list of components to show.
            They are not yet expanded, just solved to filter objects """
        new_list = []
        for c in components:
            c_s = c.strip()
            if c_s.startswith('_kf('):
                # A reference to a KiBot filter
                if c_s[-1] != ')':
                    raise KiPlotConfigurationError('Missing `)` in KiBot filter reference: `{}`'.format(c))
                filter_name = c_s[4:-1].strip().split(';')
                logger.debug('Expanding KiBot filter in list of components: `{}`'.format(filter_name))
                filter = BaseFilter.solve_filter(filter_name, 'show_components')
                if not filter:
                    raise KiPlotConfigurationError('Unknown filter in: `{}`'.format(c))
                new_list.append(filter)
                self._filters_to_expand = True
            else:
                if GS.global_allow_component_ranges and c_s.count('-') == 1:
                    m = comp_range_regex.match(c_s)
                    if m:
                        prefix = m.group(1)
                        start = int(m.group(2))
                        prefix2 = m.group(3)
                        end = int(m.group(4))
                        if prefix == prefix2 and end > start:
                            # We have a match, both prefixes are the same and the numbers looks right
                            logger.debugl(2, f'Expanding range {c_s} to {prefix}{start}...{prefix}{end}')
                            new_list.extend([prefix+str(n) for n in range(start, end+1)])
                            return new_list
                new_list.append(c)
        return new_list

    def expand_kf_components(self, components):
        """ Expands references to filters in show_components """
        if not components:
            return []
        if not self._filters_to_expand:
            return components
        new_list = []
        all_comps = self._comps if self._comps else get_all_components()
        # Scan the list to show
        for c in components:
            if isinstance(c, str):
                # A reference, just add it
                new_list.append(c)
                continue
            # A filter, add its results
            ext_list = []
            for ac in all_comps:
                if c.filter(ac):
                    ext_list.append(ac.ref)
            new_list += ext_list
        return new_list

    def remove_temporals(self):
        logger.debug('Removing temporal files')
        for f in self._files_to_remove:
            if os.path.isfile(f):
                logger.debug('- File `{}`'.format(f))
                os.remove(f)
            elif os.path.isdir(f):
                logger.debug('- Dir `{}`'.format(f))
                rmtree(f)
        self._files_to_remove = []
        self._highlight_3D_file = None

    def add_extra_options(self, cmd, dir=None):
        cmd, video_remove = GS.add_extra_options(cmd)
        if video_remove:
            self._files_to_remove.append(os.path.join(dir or cmd[-1], GS.get_kiauto_video_name(cmd)))
        return cmd

    def exec_with_retry(self, cmd, exit_with):
        try:
            GS.exec_with_retry(cmd, exit_with)
        except SystemExit:
            if GS.debug_enabled:
                if self._files_to_remove:
                    logger.warning(W_KEEPTMP+'Keeping temporal files: '+str(self._files_to_remove))
            else:
                self.remove_temporals()
            raise
        if self._files_to_remove:
            self.remove_temporals()

    def load_list_components(self):
        """ Makes the list of components available """
        self._files_to_remove = []
        if not self.dnf_filter and not self.variant and not self.pre_transform and not self.exclude_filter:
            return
        # Get the components list from the schematic
        comps = get_all_components(collapse=self._collapse_components)
        # Apply the filter
        reset_filters(comps)
        comps = apply_pre_transform(comps, self.pre_transform)
        apply_exclude_filter(comps, self.exclude_filter)
        apply_fitted_filter(comps, self.dnf_filter)
        # Apply the variant
        if self.variant:
            # Apply the variant
            comps = self.variant.filter(comps)
            self._sub_pcb = self.variant._sub_pcb
        self._comps = comps

    def run(self, output_dir):
        self.load_list_components()

    # The following 5 members are used by 2D and 3D renderers
    def setup_renderer(self, components, active_components):
        """ Setup the options to use it as a renderer """
        self._show_all_components = False
        self._filters_to_expand = False
        self._highlight = self.solve_kf_filters([c for c in active_components if c])
        self.show_components = [c for c in components if c]
        if self.show_components:
            self._show_components_raw = self.show_components
            self.show_components = self.solve_kf_filters(self.show_components)

    def save_renderer_options(self):
        """ Save the current renderer settings """
        self.old_filters_to_expand = self._filters_to_expand
        self.old_show_components = self.show_components
        self.old_highlight = self._highlight
        self.old_dir = self._parent.dir
        self.old_done = self._parent._done

    def restore_renderer_options(self):
        """ Restore the renderer settings """
        self._filters_to_expand = self.old_filters_to_expand
        self.show_components = self.old_show_components
        self._highlight = self.old_highlight
        self._parent.dir = self.old_dir
        self._parent._done = self.old_done

    def apply_show_components(self):
        if self._show_all_components:
            # Don't change anything
            return
        logger.debug('Applying components list ...')
        # The user specified a list of components, we must remove the rest
        if not self._comps:
            # No variant or filter applied
            # Load the components
            self._comps = get_all_components()
        # If the component isn't listed by the user make it DNF
        show_components = set(self.expand_kf_components(self.show_components))
        self.undo_show = set()
        for c in self._comps:
            if c.ref not in show_components and c.fitted:
                c.set_fitted(False)
                self.undo_show.add(c.ref)
                logger.debugl(2, '- Removing '+c.ref)

    def undo_show_components(self):
        if self._show_all_components:
            # Don't change anything
            return
        for c in self._comps:
            if c.ref in self.undo_show:
                c.set_fitted(True)

    def sch_replace_one_image(self, sheet, box, output_name, box_index):
        """ Replace one image in the schematic, see sch_replace_images """
        # Get the image file name
        logger.debugl(2, f"- Looking for output {output_name} images")
        output_obj = look_for_output(output_name, '`sch print image`', self._parent, RENDERERS)
        targets, _, _ = get_output_targets(output_name, self._parent)
        targets = [fn for fn in targets if fn.endswith('.png')]
        if not targets:
            raise KiPlotConfigurationError("{self.desc_box(box)} uses `{output_name}` which doesn't"
                                           " generate any PNG")
        fname = targets[0]
        logger.debugl(2, f"- Related image: {fname}")
        if not os.path.exists(fname):
            # The target doesn't exist
            if not output_obj._done:
                # The output wasn't created in this run, try running it
                logger.debug('- Not yet generated, tying to generate it')
                run_output(output_obj)
        if not os.path.exists(fname):
            raise KiPlotConfigurationError("Failed to generate `{fname}` for {self.desc_box(box)}`")
        logger.debugl(2, "- Reading image")
        # Add the image to the SCH
        try:
            s, w, h, dpi = read_png(fname, logger, only_size=False)
        except TypeError as e:
            raise KiPlotConfigurationError(f'Error reading {fname} size: {e} for {self.desc_box(box)}')
        # Check if we already have an image there
        old_img_index = -1
        old_img = None
        new_images = []
        for index, img in enumerate(sheet.bitmaps):
            if abs(img.pos_x-box.size.x/2-box.pos_x) < 0.1 and abs(img.pos_y-box.size.y/2-box.pos_y) < 0.1:
                old_img_index = index
                old_img = img
            else:
                new_images.append(img)
        sheet.bitmaps = new_images
        if old_img_index > 0:
            logger.debugl(2, "- Replacing existing image")
        # Put the image
        img_w = w/dpi*25.4
        img_h = h/dpi*25.4
        logger.debugl(2, f'- PNG: {w}x{h} px {dpi} PPIs {img_w}x{img_h} mm')
        logger.debugl(2, f'- Box: {box.pos_x},{box.pos_y} +{box.size.x},{box.size.y} mm')
        scale = box.size.x/img_w
        logger.debugl(2, f'- Scale {scale}')
        bmp = SchematicBitmapV6()
        bmp.pos_x = box.pos_x + box.size.x/2
        bmp.pos_y = box.pos_y + (img_h*scale)/2
        bmp.scale = scale
        bmp.uuid = ''
        data = b64encode(s).decode('ascii')
        bmp.data = [data[i:i+76] for i in range(0, len(data), 76)]
        # Append the new image
        sheet.bitmaps.append(bmp)
        old_box = deepcopy(box)
        sheet._replaced_images.append((old_img_index, old_box, old_img, box_index))
        # Ensure the box is invisible
        transparent = Color()
        transparent.r = 255
        transparent.a = 0
        new_stroke = Stroke()
        new_stroke.color = transparent
        box.stroke = new_stroke
        box.effects.color = transparent
        box.effects.w = box.effects.h = 0
        # Adjust the box height
        box.size.y = img_h*scale
        return True

    def sch_replace_images(self, sch):
        """ Used by outputs that support replacing 'kibot_image_OUTPUT' in schematics """
        if not GS.global_sch_image_prefix or GS.ki5:
            return False
        logger.debug("Replacing images in schematic")
        res = False
        key = GS.global_sch_image_prefix+'_'
        key_l = len(key)
        for s in GS.sch.all_sheets:
            s._replaced_images = []
            for index, b in enumerate(s.text_boxes):
                text = b.text.strip()
                if text.startswith(key):
                    res |= self.sch_replace_one_image(s, b, text[key_l:], index)
        return res

    def sch_restore_images(self, sch):
        """ Used to undo sch_replace_images """
        if not GS.global_sch_image_prefix or GS.ki5:
            return False
        logger.debug("Restoring images in schematic")
        key = GS.global_sch_image_prefix+'_'
        len(key)
        for s in GS.sch.all_sheets:
            for (index, box, img, box_index) in reversed(s._replaced_images):
                s.text_boxes[box_index] = box
                if index < 0:
                    # Was appended
                    s.bitmaps.pop()
                else:
                    # Put the original image back
                    s.bitmaps[index] = img
            s._replaced_images = None


class PcbMargin(Optionable):
    """ To adjust each margin """
    def __init__(self):
        super().__init__()
        with document:
            self.left = 0
            """ Left margin [mm] """
            self.right = 0
            """ Right margin [mm] """
            self.top = 0
            """ Top margin [mm] """
            self.bottom = 0
            """ Bottom margin [mm] """

    @staticmethod
    def solve(margin):
        if isinstance(margin, PcbMargin):
            return ((GS.from_mm(margin.left), GS.from_mm(margin.right), GS.from_mm(margin.top), GS.from_mm(margin.bottom)),
                    margin)
        margin = GS.from_mm(margin)
        return (margin, margin, margin, margin), margin
