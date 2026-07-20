# -*- coding: utf-8 -*-
# Copyright (c) 2020-2026 Salvador E. Tropea
# Copyright (c) 2020-2026 Instituto Nacional de Tecnología Industrial
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)
import os
from .error import KiPlotConfigurationError
from .gs import GS
from .kicad.v6_sch import Variant
from .optionable import Optionable
from .out_base import VariantOptions
from .registrable import RegOutput
from .macros import macros, document, output_class  # noqa: F401
from . import log

logger = log.get_logger()


class Sch_Variant_Options(VariantOptions):
    def __init__(self):
        with document:
            self.copy_project = False
            """ Copy the KiCad project to the destination directory.
                Disabled by default for compatibility with older versions """
            self.title = ''
            """ Text used to replace the sheet title. %VALUE expansions are allowed.
                If it starts with `+` the text is concatenated """
            self.include = Optionable
            """ [string|list(string)='_all_'] {comma_sep} When exporting a KiCad 10 file also include the listed variants.
                The `_all_` keyword means all other variants.
                The variant indicated by the `variant` option will be the `Default` KiCad variant """
        super().__init__()

    def get_targets(self, out_dir):
        targets = list(GS.sch.file_names_variant(out_dir))
        if self.copy_project:
            targets.extend(GS.copy_project_names(GS.sch_file, ref_dir=out_dir))
        return targets

    def config(self, parent):
        super().config(parent)
        variants = RegOutput.get_variants()
        for v in self.include:
            if v not in variants and v != '_all_':
                raise KiPlotConfigurationError(f"Unknown {v} variant")

    def export_ki10_variants(self):
        """ Convert the variants to native KiCad variants.
            The variant indicated in self.variant becomes the `Default`.
            All variants listed in self.include are converted """
        # Determine which variants will be included
        if '_all_' in self.include:
            # Make a list of all variants, excluding the one currently selected
            cur_variant_name = self.variant.name if self.variant else ''
            include = [k for k in RegOutput.get_variants().keys() if k != cur_variant_name]
        else:
            include = self.include

        # Check we have something to export
        if not include and self.variant is None:
            # No variants to include and no reference variant
            logger.error("No base variant and no variants, no variants exported")
            return False

        # Collect information about the reference variant
        logger.debugl(3, f"Included variants: {include}")
        if self.variant:
            logger.debugl(2, f"Computing default variant using `{self.variant.name}`")
        else:
            logger.debugl(2, "No reference variant")
            self.load_list_components(forced=True)
        default_variants = []
        for c in self._comps:
            default_variant = Variant()
            default_variant.name = "Default"
            default_variant.dnp = not c.fitted
            default_variant.exclude_from_sim = c.exclude_from_sim
            default_variant.in_bom = c.included and c.in_bom
            default_variant.on_board = c.on_board
            default_variant.in_pos_files = c.in_pos_files
            for f in c.fields:
                default_variant.fields[f.name] = f.value
            default_variants.append(default_variant)
            if hasattr(c, 'alt_variants'):
                # Not found in the ones from PCB
                c.alt_variants.clear()

        # Memorice the current variant
        default_variant_obj = self.variant

        # Compare each of the included variants
        for v in include:
            logger.debugl(2, f"- Computing variant `{v}`")
            self.variant = RegOutput.get_variant(v)
            self.load_list_components()
            for c, cur in zip(self._comps, default_variants):
                if not hasattr(c, 'alt_variants'):
                    # Not found in the ones from PCB
                    continue
                new_v = Variant()
                new_v.name = v
                used = False
                if cur.dnp != (not c.fitted):
                    new_v.dnp = not c.fitted
                    used = True
                if cur.exclude_from_sim != c.exclude_from_sim:
                    new_v.exclude_from_sim = c.exclude_from_sim
                    used = True
                included = c.included and c.in_bom
                if cur.in_bom != included:
                    new_v.in_bom = included
                    used = True
                if cur.on_board != c.on_board:
                    new_v.on_board = c.on_board
                    used = True
                if cur.in_pos_files != c.in_pos_files:
                    new_v.in_pos_files = c.in_pos_files
                    used = True
                for f in c.fields:
                    if cur.fields.get(f.name) != f.value:
                        new_v.fields[f.name] = f.value
                        used = True
                if used:
                    c.alt_variants[v] = new_v

        # Restore the current variant
        self.variant = default_variant_obj

        # Apply the default again
        self.load_list_components(forced=True)

        # Transfer the variant to the component
        for c in self._comps:
            c.kicad_dnp = not c.fitted
            c.in_bom = c.included and c.in_bom

        return True

    def run(self, output_dir):
        super().run(output_dir)
        # Create the schematic
        self.set_title(self.title, sch=True)
        replaced_images = self.sch_replace_images(GS.sch)

        alt_variants = self.export_ki10_variants() if GS.ki10 and self.include else False
        GS.sch.save_variant(output_dir, alt_variants=alt_variants)

        self.restore_title(sch=True)
        if replaced_images:
            self.sch_restore_images(GS.sch)
        if self.copy_project:
            GS.copy_project(os.path.join(output_dir, GS.sch_basename+'.kicad_pcb'))


@output_class
class Sch_Variant(BaseOutput):  # noqa: F821
    """ Schematic with variant generator
        Creates a copy of the schematic with all the filters and variants applied.
        This copy isn't intended for development without a careful review.
        Can be used to export legacy variants to KiCad 10 variants.
        Supports the image replacement using the prefix indicated by the `sch_image_prefix` global variable """
    def __init__(self):
        super().__init__()
        with document:
            self.options = Sch_Variant_Options
            """ *[dict={}] Options for the `sch_variant` output """
        self._sch_related = True

    def get_output_sch_name(self, out_dir):
        return os.path.join(out_dir, os.path.basename(GS.sch_file))

    def run(self, output_dir):
        # No output member, just a dir
        self.options.run(output_dir)
