# -*- coding: utf-8 -*-
# Copyright (c) 2022-2026 Salvador E. Tropea
# Copyright (c) 2022-2026 Instituto Nacional de Tecnología Industrial
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)
from .error import KiPlotConfigurationError
from .gs import GS
from .kicad.v6_sch import Variant
from .optionable import Optionable
from .out_base import VariantOptions
from .registrable import RegOutput
from .macros import macros, document, output_class  # noqa: F401
from . import log

if GS.ki10:
    from pcbnew import KIID
logger = log.get_logger()


class PCB_Variant_Options(VariantOptions):
    def __init__(self):
        with document:
            self.hide_excluded = False
            """ Hide components in the Fab layer that are marked as excluded by a variant.
                Affected by global options """
            self.output = GS.def_global_output
            """ *Filename for the output (%i=variant, %x=kicad_pcb) """
            self.copy_project = True
            """ Copy the KiCad project to the destination directory """
            self.title = ''
            """ Text used to replace the sheet title. %VALUE expansions are allowed.
                If it starts with `+` the text is concatenated """
            self.include = Optionable
            """ [string|list(string)='_all_'] {comma_sep} When exporting a KiCad 10 file also include the listed variants.
                The `_all_` keyword means all other variants.
                The variant indicated by the `variant` option will be the `Default` KiCad variant """
        super().__init__()
        self._expand_id = 'variant'
        self._expand_ext = 'kicad_pcb'

    def get_targets(self, out_dir):
        targets = [self._parent.expand_filename(out_dir, self.output)]
        if self.copy_project:
            targets.extend(GS.copy_project_names(targets[0], ref_dir=out_dir))
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
            default_variant.in_bom = c.included and c.in_bom_pcb
            default_variant.on_board = c.on_board
            default_variant.in_pos_files = c.in_pos_files
            for f in c.fields:
                default_variant.fields[f.name] = f.value
            default_variants.append(default_variant)

        # Memorice the current variant
        default_variant_obj = self.variant

        # Compare each of the included variants
        for v in include:
            logger.debugl(2, f"- Computing variant `{v}`")
            if not GS.board.HasVariant(v):
                GS.board.AddVariant(v)
                GS.board.SetVariantDescription(v, RegOutput.get_variant(v).comment)
            self.variant = RegOutput.get_variant(v)
            self.load_list_components()
            for c, cur in zip(self._comps, default_variants):
                if not hasattr(c, 'pcb_id'):
                    logger.debugl(3, f"Skipping {c} because it doesn't have PCB info")
                    continue
                # Find if this component changes
                for f in c.fields:
                    if cur.fields.get(f.name) != f.value:
                        diff_fields = True
                        break
                else:
                    diff_fields = False
                included = c.included and c.in_bom_pcb
                if cur.dnp != (not c.fitted) or cur.in_bom != included or cur.in_pos_files != c.in_pos_files or diff_fields:
                    m = GS.board.ResolveItem(KIID(c.pcb_id)).Cast()
                    # Create or recycle a variant
                    new_v = m.GetVariant(v) if m.HasVariant(v) else m.AddVariant(v)
                    # Set it as the legacy variant
                    new_v.SetDNP(not c.fitted)
                    new_v.SetExcludedFromBOM(not included)
                    new_v.SetExcludedFromPosFiles(not c.in_pos_files)
                    for f in c.fields:
                        new_v.SetFieldValue(f.name, f.value)
                    # Update it in the footprint
                    m.SetVariant(new_v)

        # Restore the current variant
        self.variant = default_variant_obj

        # Apply the default again
        self.load_list_components(forced=True)

        # Transfer the variant to the component
        GS.board.SetCurrentVariant('')
        for c in self._comps:
            if not hasattr(c, 'pcb_id'):
                continue
            m = GS.board.ResolveItem(KIID(c.pcb_id))
            if m.GetClass() == "DELETED_BOARD_ITEM":
                continue
            m = m.Cast()
            m.SetDNP(not c.fitted)
            included = c.included and c.in_bom_pcb
            m.SetExcludedFromBOM(not included)
            for f in c.fields:
                m.SetField(f.name, f.value)

        return True

    def run(self, output):
        super().run(output)
        self.filter_pcb_components(do_3D=True)
        self.set_title(self.title)

        if GS.ki10 and self.include:
            self.export_ki10_variants()

        logger.debug('Saving PCB to '+output)
        GS.board.Save(output)
        if self.copy_project:
            GS.copy_project(output)
        self.restore_title()
        self.unfilter_pcb_components(do_3D=True)


@output_class
class PCB_Variant(BaseOutput):  # noqa: F821
    """ PCB with variant generator
        Creates a copy of the PCB with all the filters and variants applied.
        This copy isn't intended for development without a careful review.
        Can be used to export legacy variants to KiCad 10 variants. In this case you should disable the global
        `cross_footprints_for_dnp`, `remove_solder_paste_for_dnp`, `remove_adhesive_for_dnp` and
        `remove_3D_models_for_dnp` options.
        Here is an [example](https://github.com/INTI-CMNB/KiBot/blob/dev/tests/yaml_samples/export_variants.kibot.yaml)
        configuration showing how to migrate to KiCad 10 native variants
    """
    def __init__(self):
        super().__init__()
        with document:
            self.options = PCB_Variant_Options
            """ *[dict={}] Options for the `pcb_variant` output """
