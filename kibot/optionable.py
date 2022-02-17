# -*- coding: utf-8 -*-
# Copyright (c) 2020-2021 Salvador E. Tropea
# Copyright (c) 2020-2021 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
""" Base class for output options """
import os
import re
import inspect
from re import compile
from .error import KiPlotConfigurationError
from .gs import GS
from .misc import W_UNKOPS
from . import log

logger = log.get_logger()


def filter(v):
    return inspect.isclass(v) or not (callable(v) or isinstance(v, (dict, list)))


def _cl(text):
    """ Eliminates dangerous characters from the text """
    return re.sub(r'[\\\/\?%\*:|"<>]', '_', text)


class Optionable(object):
    """ A class to validate and hold configuration outputs/options.
        Is configured from a dict and the collected values are stored in its attributes. """
    _str_values_re = compile(r"string=.*\] \[([^\]]+)\]")
    _num_range_re = compile(r"number=.*\] \[(-?\d+),(-?\d+)\]")
    _default = None
    _color_re = re.compile(r"#[A-Fa-f0-9]{6}$")

    def __init__(self):
        self._unknown_is_error = False
        self._error_context = ''
        self._tree = {}
        self._configured = False
        # File/directory pattern expansion
        self._expand_id = ''
        self._expand_ext = ''
        super().__init__()
        for var in ['output', 'variant', 'units']:
            glb = getattr(GS, 'global_'+var)
            if glb is not None and hasattr(self, var):
                setattr(self, var, glb)
                if GS.debug_level > 2:
                    logger.debug('Using global `{}`=`{}`'.format(var, glb))

    @staticmethod
    def _check_str(key, val, doc):
        if not isinstance(val, str):
            raise KiPlotConfigurationError("Option `{}` must be a string".format(key))
        # If the docstring specifies the allowed values in the form [v1,v2...] enforce it
        m = Optionable._str_values_re.search(doc)
        if m:
            vals = m.group(1).split(',')
            if val not in vals:
                raise KiPlotConfigurationError("Option `{}` must be any of {} not `{}`".format(key, vals, val))

    @staticmethod
    def _check_num(key, val, doc):
        if not isinstance(val, (int, float)):
            raise KiPlotConfigurationError("Option `{}` must be a number".format(key))
        # If the docstring specifies a range in the form [from-to] enforce it
        m = Optionable._num_range_re.search(doc)
        if m:
            min = float(m.group(1))
            max = float(m.group(2))
            if val < min or val > max:
                raise KiPlotConfigurationError("Option `{}` outside its range [{},{}]".format(key, min, max))

    @staticmethod
    def _check_bool(key, val):
        if not isinstance(val, bool):
            raise KiPlotConfigurationError("Option `{}` must be true/false".format(key))

    def get_doc(self, name):
        try:
            doc = getattr(self, '_help_'+name).strip()
        except AttributeError:
            return None, name, False
        if doc[0] == '{':
            alias = doc[1:-1]
            return getattr(self, '_help_'+alias).strip(), alias, True
        return doc, name, False

    def add_to_doc(self, name, text):
        doc = getattr(self, '_help_'+name).strip()
        setattr(self, '_help_'+name, doc+'.\n'+text)

    def set_doc(self, name, text):
        setattr(self, '_help_'+name, text)

    @staticmethod
    def _typeof(v):
        if isinstance(v, bool):
            return 'boolean'
        if isinstance(v, (int, float)):
            return 'number'
        if isinstance(v, str):
            return 'string'
        if isinstance(v, dict):
            return 'dict'
        if isinstance(v, list):
            if len(v) == 0:
                return 'list(string)'
            return 'list({})'.format(Optionable._typeof(v[0]))
        return 'None'

    def _perform_config_mapping(self):
        """ Map the options to class attributes """
        attrs = self.get_attrs_for()
        for k, v in self._tree.items():
            # Map known attributes and avoid mapping private ones
            if (k[0] == '_') or (k not in attrs):
                if self._unknown_is_error:
                    raise KiPlotConfigurationError("Unknown {}option `{}`".format(self._error_context, k))
                logger.warning(W_UNKOPS + "Unknown {}option `{}`".format(self._error_context, k))
                continue
            # Check the data type
            cur_doc, alias, is_alias = self.get_doc(k)
            cur_val = getattr(self, alias)
            if cur_doc[0] == '[':
                # Separate the valid types for this key
                valid = cur_doc[1:].split(']')[0].split('|')
                # Remove the XXXX=Value
                if '=' in valid[-1]:
                    valid[-1] = valid[-1].split('=')[0]
                # Get the type used by the user as a string
                v_type = Optionable._typeof(v)
                if v_type not in valid:
                    # Not a valid type for this key
                    if v_type == 'None':
                        raise KiPlotConfigurationError("Empty option `{}`".format(k))
                    if len(valid) == 1:
                        raise KiPlotConfigurationError("Option `{}` must be a {} not `{}`".format(k, valid[0], v_type))
                    else:
                        raise KiPlotConfigurationError("Option `{}` must be any of {} not `{}`".format(k, valid, v_type))
            else:
                valid = None
                v_type = Optionable._typeof(cur_val)
            if v_type == 'boolean':
                Optionable._check_bool(k, v)
            elif v_type == 'number':
                Optionable._check_num(k, v, cur_doc)
            elif v_type == 'string':
                Optionable._check_str(k, v, cur_doc)
            elif isinstance(cur_val, type):
                # A class, so we need more information i.e. "[dict|string]"
                if valid is not None:
                    # We know the type matches, now apply validations
                    if isinstance(v, (int, float)) and not isinstance(v, bool):
                        # Note: booleans are also instance of int
                        # Not used yet
                        Optionable._check_num(k, v, cur_doc)  # pragma: no cover (Internal)
                    elif isinstance(v, str):
                        Optionable._check_str(k, v, cur_doc)
                    elif isinstance(v, dict):
                        # Dicts are solved using Optionable classes
                        new_val = v
                        # Create an object for the valid class
                        v = cur_val()
                        # Delegate the validation to the object
                        v.set_tree(new_val)
                        v.config(self)
                    elif isinstance(v, list):
                        new_val = []
                        for element in v:
                            e_type = 'list('+Optionable._typeof(element)+')'
                            if e_type not in valid:
                                raise KiPlotConfigurationError("Option `{}` must be any of {} not `{}`".
                                                               format(element, valid, e_type))
                            if isinstance(element, dict):
                                nv = cur_val()
                                nv.set_tree(element)
                                nv.config(self)
                                new_val.append(nv)
                            else:
                                new_val.append(element)
                        v = new_val
            # Seems to be ok, map it
            setattr(self, alias if is_alias else k, v)

    def set_tree(self, tree):
        self._tree = tree

    def config(self, parent):
        self._parent = parent
        if self._tree and not self._configured:
            self._perform_config_mapping()
            self._configured = True

    def get_attrs_for(self):
        """ Returns all attributes """
        return dict(inspect.getmembers(self, filter))

    def get_attrs_gen(self):
        """ Returns a (key, val) iterator on public attributes """
        attrs = self.get_attrs_for()
        return ((k, v) for k, v in attrs.items() if k[0] != '_')

    def _find_variant(self):
        """ Returns the text to add for the current variant.
            Also try with the globally defined variant.
            If no variant is defined an empty string is returned. """
        if hasattr(self, 'variant') and self.variant and hasattr(self.variant, 'file_id'):
            return self.variant.file_id
        if GS.solved_global_variant:
            return GS.solved_global_variant.file_id
        return ''

    def _find_variant_name(self):
        """ Returns the name for the current variant.
            Also try with the globally defined variant.
            If no variant is defined an empty string is returned. """
        if hasattr(self, 'variant') and self.variant and hasattr(self.variant, 'name'):
            return self.variant.name
        if GS.solved_global_variant:
            return GS.solved_global_variant.name
        return ''

    def expand_filename_common(self, name, parent):
        """ Expansions common to the PCB and Schematic """
        # PCB expansions, explicit
        if GS.board and '%b' in name:
            name = name.replace('%bc', _cl(GS.pcb_comp))
            name = name.replace('%bd', _cl(GS.pcb_date))
            name = name.replace('%bF', GS.pcb_no_ext)
            name = name.replace('%bf', GS.pcb_basename)
            name = name.replace('%bp', _cl(GS.pcb_title))
            name = name.replace('%br', _cl(GS.pcb_rev))
            for num, val in enumerate(GS.pcb_com):
                name = name.replace('%bC'+str(num+1), _cl(val))
        if GS.solved_global_variant:
            name = name.replace('%g', GS.solved_global_variant.file_id)
            name = name.replace('%G', GS.solved_global_variant.name)
        # Schematic expansions, explicit
        if GS.sch and '%s' in name:
            name = name.replace('%sc', _cl(GS.sch_comp))
            name = name.replace('%sd', _cl(GS.sch_date))
            name = name.replace('%sF', GS.sch_no_ext)
            name = name.replace('%sf', GS.sch_basename)
            name = name.replace('%sp', _cl(GS.sch_title))
            name = name.replace('%sr', _cl(GS.sch_rev))
            for num, val in enumerate(GS.sch_com):
                name = name.replace('%sC'+str(num+1), _cl(val))
        name = name.replace('%D', GS.n.strftime(GS.global_date_format))
        name = name.replace('%T', GS.n.strftime(GS.global_time_format))
        if self:
            name = name.replace('%i', self._expand_id)
            name = name.replace('%v', _cl(self._find_variant()))
            name = name.replace('%V', _cl(self._find_variant_name()))
            name = name.replace('%x', self._expand_ext)
            replace_id = ''
            if parent and hasattr(parent, 'output_id'):
                replace_id = _cl(parent.output_id)
            name = name.replace('%I', replace_id)
        return name

    def expand_filename_both(self, name, is_sch=True, make_safe=True):
        """ Expands %* values in filenames.
            Uses data from the PCB. """
        parent = None
        if self and hasattr(self, '_parent'):
            parent = self._parent
        if GS.debug_level > 3:
            logger.debug('Expanding `{}` in {} context for {} parent: {}'.
                         format(name, 'SCH' if is_sch else 'PCB', self, parent))
        # Determine if we need to expand SCH and/or PCB related data
        has_dep_exp = any(map(lambda x: x in name, ['%c', '%d', '%F', '%f', '%p', '%r', '%C1', '%C2', '%C3', '%C4']))
        do_sch = is_sch and has_dep_exp
        # logger.error(name + '  is_sch ' +str(is_sch)+"   "+ str(do_sch))
        # raise
        do_pcb = not is_sch and has_dep_exp
        # Load the needed data
        if GS.pcb_file and (do_pcb or '%b' in name):
            if GS.board is None:
                GS.load_board()
            GS.load_pcb_title_block()
        if GS.sch_file and (do_sch or '%s' in name):
            if GS.sch is None:
                GS.load_sch()
            GS.load_sch_title_block()
        # This member can be called with a preflight object
        name = Optionable.expand_filename_common(self, name, parent)
        if GS.board and do_pcb:
            name = name.replace('%c', _cl(GS.pcb_comp))
            name = name.replace('%d', _cl(GS.pcb_date))
            name = name.replace('%F', GS.pcb_no_ext)
            name = name.replace('%f', GS.pcb_basename)
            name = name.replace('%p', _cl(GS.pcb_title))
            name = name.replace('%r', _cl(GS.pcb_rev))
            for num, val in enumerate(GS.pcb_com):
                name = name.replace('%C'+str(num+1), _cl(val))
        if GS.sch and do_sch:
            name = name.replace('%c', _cl(GS.sch_comp))
            name = name.replace('%d', _cl(GS.sch_date))
            name = name.replace('%F', GS.sch_no_ext)
            name = name.replace('%f', GS.sch_basename)
            name = name.replace('%p', _cl(GS.sch_title))
            name = name.replace('%r', _cl(GS.sch_rev))
            for num, val in enumerate(GS.sch_com):
                name = name.replace('%C'+str(num+1), _cl(val))
        if make_safe:
            # sanitize the name to avoid characters illegal in file systems
            name = name.replace('\\', '/')
            name = re.sub(r'[?%*:|"<>]', '_', name)
        if GS.debug_level > 3:
            logger.debug('Expanded `{}`'.format(name))
        return name

    def expand_filename_pcb(self, name):
        """ Expands %* values in filenames.
            Uses data from the PCB. """
        # This member can be called with a preflight object
        return Optionable.expand_filename_both(self, name, is_sch=False)

    def expand_filename_sch(self, name):
        """ Expands %* values in filenames.
            Uses data from the SCH. """
        # This member can be called with a preflight object
        return Optionable.expand_filename_both(self, name)

    @staticmethod
    def force_listl(val: str|list[str]|None) -> list[str]:
        """ Used for values that accept a string or a list of strings.
            The string can be a comma separated list """
        if isinstance(val, type):
            # Not used
            val = []
        elif isinstance(val, str):
            # A string
            if val:
                val = [v.strip() for v in val.split(',')]
            else:
                # Empty string
                val = []
        elif val is None:
            val = []
        return val

    @classmethod
    def get_default(cls):
        return cls._default

    def validate_color(self, name: str):
        color = getattr(self, name)
        if not self._color_re.match(color):
            raise KiPlotConfigurationError('Invalid color for `{}` use `#rrggbb` with hex digits'.format(name))

    def validate_colors(self, names):
        for color in names:
            self.validate_color(color)


class BaseOptions(Optionable):
    """ A class to validate and hold output options.
        Is configured from a dict and the collected values are stored in its attributes. """
    def __init__(self):
        super().__init__()

    def read_vals_from_po(self, po):
        """ Set attributes from a PCB_PLOT_PARAMS (plot options) """
        return

    def expand_filename(self, dir, name, id, ext):
        cur_id = self._expand_id
        cur_ext = self._expand_ext
        self._expand_id = id
        self._expand_ext = ext
        name = self.expand_filename_both(name, is_sch=self._parent._sch_related)
        res = os.path.abspath(os.path.join(dir, name))
        self._expand_id = cur_id
        self._expand_ext = cur_ext
        return res
