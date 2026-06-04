# -*- coding: utf-8 -*-
# Copyright (c) 2026 Salvador E. Tropea
# Copyright (c) 2026 Instituto Nacional de Tecnología Industrial
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)
import json
import os
from .registrable import RegOutput
from .error import config_error
from .gs import GS
from .kiplot import load_sch
from .var_base import BasicVariant
from .macros import macros, document, variant_class  # noqa: F401
from . import log

logger = log.get_logger()


@variant_class
class KiCad(BasicVariant):
    """ KiCad variant style
        Used for KiCad 10 and newer variants.
        Defining them in the configuration file allows to change the comment and to define the `file_id`
    """
    def filter(self, comps, call_back=None):
        # Applies this variant to the components
        logger.debug(f'Applying KiCad variant `{self.name}`')
        if call_back is None:
            if GS.debug_level:
                GS.trace_dump()
            logger.warning("Filter without callback")
            return comps
        for c in comps:
            call_back(c)
        return comps

    @staticmethod
    def add_default():
        if not GS.ki10 or not GS.global_kicad_default_variant:
            return
        v = 'Default'
        if RegOutput.is_variant(v):
            logger.debug(f"{v} variant already defined")
            return
        kv = KiCad()
        kv.name = v
        kv.type = 'kicad'
        kv.comment = 'Default KiCad variant'
        kv.file_id = ''
        RegOutput.add_variant(kv)
        logger.debug("Created the `Default` KiCad variant")

    @staticmethod
    def get_from_sch():
        """ Add variants from the schematic.
            This is not ideal, the descriptions are only in the project """
        if not GS.ki10:
            return
        logger.debug("Importing variants from the schematic")
        load_sch()
        used_variants = GS.sch.used_variants.get(GS.sch.uuid)
        if not used_variants:
            return
        for v in used_variants:
            # Check if already defined
            if RegOutput.is_variant(v):
                cur_v = RegOutput.get_variant(v)
                if cur_v.type != 'kicad':
                    # Collision with another variant
                    config_error(f'The schematic defines a varinat named `{v}` which is already used by `{cur_v}`')
                # Skip if already defined in the config file
                continue
            kv = KiCad()
            kv.name = v
            kv.type = 'kicad'
            kv.comment = v+' imported from schematic'
            kv.file_id = '_'+v
            logger.debug(f"- Variant {kv.name} from schematic")
            RegOutput.add_variant(kv)

    @staticmethod
    def get_from_pro():
        """ Add variants from the project """
        if not GS.ki10 or not GS.pro_file or not os.path.isfile(GS.pro_file):
            return False
        try:
            with open(GS.pro_file, 'rt') as f:
                data = json.load(f)
            variants = data["schematic"]["variants"]
        except Exception as e:
            # This is not fatal
            logger.debug(f"Error while looking for variants in the project: {e}")
            return False
        for v in variants:
            name = v.get('name')
            if not name:
                continue
            # Check if already defined
            if RegOutput.is_variant(name):
                cur_v = RegOutput.get_variant(name)
                if cur_v.type != 'kicad':
                    logger.error(cur_v.__dict__)
                    # Collision with another variant
                    config_error(f'The project defines a variant named `{v}` which is already used by `{cur_v}`')
                # Skip if already defined in the config file
                continue
            # Import it
            kv = KiCad()
            kv.name = name
            kv.type = 'kicad'
            kv.comment = v.get('description')
            if not kv.comment:
                kv.comment = kv.name+' imported from project'
            kv.file_id = '_'+kv.name
            logger.debug(f"- Variant {kv.name} from schematic")
            RegOutput.add_variant(kv)
        return True
