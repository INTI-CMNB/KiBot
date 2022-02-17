# -*- coding: utf-8 -*-
# Copyright (c) 2020-2021 Salvador E. Tropea
# Copyright (c) 2020-2021 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
from .registrable import RegFilter, Registrable, RegOutput
from .optionable import Optionable
from .gs import GS
from .misc import (IFILT_MECHANICAL, IFILT_VAR_RENAME, IFILT_ROT_FOOTPRINT, IFILT_KICOST_RENAME, DISTRIBUTORS,
                   IFILT_VAR_RENAME_KICOST, IFILT_KICOST_DNP)
from .error import KiPlotConfigurationError
from .bom.columnlist import ColumnList
from .macros import macros, document  # noqa: F401
from . import log

logger = log.get_logger()
DEFAULT_EXCLUDE = [{'column': ColumnList.COL_REFERENCE, 'regex': '^TP[0-9]*'},
                   {'column': ColumnList.COL_REFERENCE, 'regex': '^FID'},
                   {'column': ColumnList.COL_PART, 'regex': 'mount.*hole'},
                   {'column': ColumnList.COL_PART, 'regex': 'solder.*bridge'},
                   {'column': ColumnList.COL_PART, 'regex': 'solder.*jump'},
                   {'column': ColumnList.COL_PART, 'regex': 'test.*point'},
                   {'column': ColumnList.COL_FP, 'regex': 'test.*point'},
                   {'column': ColumnList.COL_FP, 'regex': 'mount.*hole'},
                   {'column': ColumnList.COL_FP, 'regex': 'fiducial'},
                   ]
KICOST_NAME_TRANSLATIONS = {
    # Manufacturer part number
    'mpn': 'manf#',
    'pn': 'manf#',
    'manf_num': 'manf#',
    'manf-num': 'manf#',
    'mfg_num': 'manf#',
    'mfg-num': 'manf#',
    'mfg#': 'manf#',
    'mfg part#': 'manf#',
    'man_num': 'manf#',
    'man-num': 'manf#',
    'man#': 'manf#',
    'mnf_num': 'manf#',
    'mnf-num': 'manf#',
    'mnf#': 'manf#',
    'mfr_num': 'manf#',
    'mfr-num': 'manf#',
    'mfr#': 'manf#',
    'part-num': 'manf#',
    'part_num': 'manf#',
    'p#': 'manf#',
    'part#': 'manf#',
    # Manufacturer
    'manufacturer': 'manf',
    'mnf': 'manf',
    'man': 'manf',
    'mfg': 'manf',
    'mfr': 'manf',
    # Various
    'version': 'variant',
    'nopop': 'dnp',
    'description': 'desc',
    'pdf': 'datasheet',
}


class DummyFilter(Registrable):
    """ A filter that allows all """
    def __init__(self):
        super().__init__()
        self.name = 'Dummy'
        self.type = 'dummy'
        self.comment = 'A filter that does nothing'
        self._is_transform = False

    def filter(self, comp):
        return True


class MultiFilter(Registrable):
    """ A filter containing a list of filters.
        They are applied in sequence. """
    def __init__(self, filters, is_transform):
        super().__init__()
        self.name = ','.join([f.name for f in filters])
        self.type = ','.join([f.type for f in filters])
        self.comment = 'Multi-filter'
        self.filters = filters
        self._is_transform = is_transform

    def filter(self, comp):
        comps = [comp]
        # We support logic and transform filters mixed
        # Apply all the filters
        for f in self.filters:
            if f._is_transform:
                # A transform filter, doesn't affect the logic, but can affect the list of components
                new_comps = []
                for c in comps:
                    ret = f.filter(c)
                    if ret is None:
                        # None means the component remains in the list
                        new_comps.append(c)
                    else:
                        # Replace the original by the list (could be empty)
                        new_comps.extend(ret)
                comps = new_comps
            else:
                if self._is_transform:
                    # Interpret the logic filter as a transformation
                    comps = list(filter(lambda c: f.filter(c), comps))
                else:
                    # Logic filter used for logic
                    for c in comps:
                        if not f.filter(c):
                            return False
        if not self._is_transform:
            # A logic filter that passed all tests
            return True
        # A transform filter
        if len(comps) == 1 and comps[0] == comp:
            # No changes to the list
            return None
        return comps


class NotFilter(Registrable):
    """ A filter that returns the inverted result """
    def __init__(self, filter):
        super().__init__()
        self.name = 'Not '+filter.name
        self.type = '!'+filter.type
        self.comment = filter.comment
        self._filter = filter
        self._is_transform = False

    def filter(self, comp):
        return not self._filter.filter(comp)


def apply_pre_transform(comps, filter):
    if filter:
        logger.debug('Applying transform filter `{}`'.format(filter.name))
        new_comps = []
        for c in comps:
            ret = filter.filter(c)
            if ret is None:
                new_comps.append(c)
            else:
                new_comps.extend(ret)
        return new_comps
    return comps


def apply_exclude_filter(comps, filter):
    if filter:
        logger.debug('Applying filter `{}` to exclude'.format(filter.name))
        for c in comps:
            if c.included:
                c.included = filter.filter(c)


def reset_filters(comps):
    logger.debug('Filters reset')
    for c in comps:
        c.included = True
        c.fitted = True
        c.fixed = False
        c.back_up_fields()


def apply_fitted_filter(comps, filter):
    if filter:
        logger.debug('Applying filter `{}` to fitted'.format(filter.name))
        for c in comps:
            if c.fitted:
                c.fitted = filter.filter(c)
                if not c.fitted and GS.debug_level > 2:
                    logger.debug('- Not fit: '+c.ref)


def apply_fixed_filter(comps, filter):
    if filter:
        logger.debug('Applying filter `{}` to fixed'.format(filter.name))
        for c in comps:
            if not c.fixed:
                c.fixed = filter.filter(c)


class BaseFilter(RegFilter):
    def __init__(self):
        super().__init__()
        self._unknown_is_error = True
        self._internal = False
        # Two type of filters:
        # Transform: can change the component. Returns
        #            - None, the component remains
        #            - A list of components: the component is replaced by this list
        # Logic: can't change the component. Return True/False indicating if the component pass the test.
        self._is_transform = False
        with document:
            self.name = ''
            """ Used to identify this particular filter definition """
            self.type = ''
            """ Type of filter """
            self.comment = ''
            """ A comment for documentation purposes """

    def config(self, parent):
        super().config(parent)
        if self.name[0] == '_' and not self._internal:
            raise KiPlotConfigurationError('Filter names starting with `_` are reserved ({})'.format(self.name))

    @staticmethod
    def _create_mechanical(name):
        o_tree = {'name': name}
        o_tree['type'] = 'generic'
        o_tree['comment'] = 'Internal default mechanical filter'
        o_tree['exclude_all_hash_ref'] = True
        o_tree['exclude_any'] = DEFAULT_EXCLUDE
        o_tree['exclude_virtual'] = True
        logger.debug('Creating internal filter: '+str(o_tree))
        return o_tree

    @staticmethod
    def _create_var_rename(name):
        o_tree = {'name': name}
        o_tree['type'] = 'var_rename'
        o_tree['comment'] = 'Internal default variant field renamer filter'
        logger.debug('Creating internal filter: '+str(o_tree))
        return o_tree

    @staticmethod
    def _create_var_rename_kicost(name):
        o_tree = {'name': name}
        o_tree['type'] = 'var_rename_kicost'
        o_tree['comment'] = 'Internal default variant field renamer filter (KiCost style)'
        logger.debug('Creating internal filter: '+str(o_tree))
        return o_tree

    @staticmethod
    def _create_rot_footprint(name):
        o_tree = {'name': name}
        o_tree['type'] = 'rot_footprint'
        o_tree['comment'] = 'Internal default footprint rotator'
        logger.debug('Creating internal filter: '+str(o_tree))
        return o_tree

    @staticmethod
    def _create_kibom_dnx(name):
        type = name[7:10]
        if len(name) > 11:
            subtype = name[11:]
        else:
            subtype = 'config'
        o_tree = {'name': name}
        o_tree['type'] = 'generic'
        o_tree['comment'] = 'Internal KiBoM '+type.upper()+' filter ('+subtype+')'
        o_tree['config_field'] = subtype
        o_tree['exclude_value'] = True
        o_tree['exclude_config'] = True
        o_tree['keys'] = type+'_list'
        if type[-1] == 'c':
            o_tree['invert'] = True
        logger.debug('Creating internal filter: '+str(o_tree))
        return o_tree

    @staticmethod
    def _create_kicost_rename(name):
        o_tree = {'name': name}
        o_tree['type'] = 'field_rename'
        o_tree['comment'] = 'Internal filter to emulate KiCost field aliases'
        rename = []
        for k, v in KICOST_NAME_TRANSLATIONS.items():
            rename.append({'field': k, 'name': v})
        for stub in ['part#', '#', 'p#', 'pn', 'vendor#', 'vp#', 'vpn', 'num']:
            for dist in DISTRIBUTORS:
                base = dist
                dist += '#'
                if stub != '#':
                    rename.append({'field': base + stub, 'name': dist})
                rename.append({'field': base + '_' + stub, 'name': dist})
                rename.append({'field': base + '-' + stub, 'name': dist})
        o_tree['rename'] = rename
        logger.debug('Creating internal filter: '+str(o_tree))
        return o_tree

    @staticmethod
    def _create_kicost_dnp(name):
        o_tree = {'name': name}
        o_tree['type'] = 'generic'
        o_tree['comment'] = 'Internal filter for KiCost `dnp` field'
        # dnp = 0 and empty are included, other dnp values are excluded
        o_tree['exclude_any'] = [{'column': 'dnp', 'regex': r'^((\s*0(\.0*)?\s*)|(\s*))$', 'invert': True,
                                  'skip_if_no_field': True}]
        return o_tree

    @staticmethod
    def _create_internal_filter(name):
        if name == IFILT_MECHANICAL:
            tree = BaseFilter._create_mechanical(name)
        elif name.startswith('_kibom_dn') and len(name) >= 10:
            tree = BaseFilter._create_kibom_dnx(name)
        elif name == IFILT_VAR_RENAME:
            tree = BaseFilter._create_var_rename(name)
        elif name == IFILT_ROT_FOOTPRINT:
            tree = BaseFilter._create_rot_footprint(name)
        elif name == IFILT_KICOST_RENAME:
            tree = BaseFilter._create_kicost_rename(name)
        elif name == IFILT_VAR_RENAME_KICOST:
            tree = BaseFilter._create_var_rename_kicost(name)
        elif name == IFILT_KICOST_DNP:
            tree = BaseFilter._create_kicost_dnp(name)
        else:
            return None
        filter = RegFilter.get_class_for(tree['type'])()
        filter._internal = True
        filter.set_tree(tree)
        filter.config(None)
        RegOutput.add_filter(filter)
        return filter

    @staticmethod
    def solve_filter(names, target_name, default=None, is_transform=False):
        """ Name can be:
            - A class, meaning we have to use a default.
            - A string, the name of a filter.
            - A list of strings, the name of 1 or more filters. """
        if isinstance(names, type):
            # Nothing specified, use the default
            if default is None:
                return None
            if isinstance(default, list):
                names = default
            else:
                names = [default]
        elif isinstance(names, str):
            # User provided, but only one, make a list
            if names == '_none':
                return None
            names = [names]
        # Here we should have a list of strings
        filters = []
        for name in names:
            if not name:
                continue
            if isinstance(name, Registrable):
                # A filter already converted
                filters.append(name)
                continue
            if name[0] == '!':
                invert = True
                name = name[1:]
                # '!' => always False
                if not name:
                    filters.append(NotFilter(DummyFilter()))
                    continue
            else:
                invert = False
            # Is already defined?
            if RegOutput.is_filter(name):
                fil = RegOutput.get_filter(name)
            else:  # Nope, can be created?
                fil = BaseFilter._create_internal_filter(name)
                if fil is None:
                    raise KiPlotConfigurationError("Unknown filter `{}` used for `{}`".format(name, target_name))
            if invert:
                if fil._is_transform:
                    raise KiPlotConfigurationError("Transform filter `{}` can't be inverted, used for `{}`"
                                                   .format(name, target_name))
                filters.append(NotFilter(fil))
            else:
                filters.append(fil)
        # Finished collecting filters
        if not filters:
            return DummyFilter()
        # If we need a `Logic` filter ensure that at least one in the list is `Logic`
        if not is_transform and not next(filter(lambda x: not x._is_transform, filters), False):
            raise KiPlotConfigurationError("At least one logic filter is needed for `{}`".format(target_name))
        if len(filters) == 1:
            return filters[0]
        return MultiFilter(filters, is_transform)


class FieldRename(Optionable):
    """ Field translation """
    def __init__(self):
        super().__init__()
        self._unknown_is_error = True
        with document:
            self.field = ''
            """ Name of the field to rename """
            self.name = ''
            """ New name """
        self._field_example = 'mpn'
        self._name_example = 'manf#'

    def config(self, parent):
        super().config(parent)
        if not self.field:
            raise KiPlotConfigurationError("Missing or empty `field` in rename list ({})".format(str(self._tree)))
        if not self.name:
            raise KiPlotConfigurationError("Missing or empty `name` in rename list ({})".format(str(self._tree)))
        self.field = self.field.lower()
