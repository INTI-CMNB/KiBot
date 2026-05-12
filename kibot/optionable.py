# -*- coding: utf-8 -*-
# Copyright (c) 2020-2025 Salvador E. Tropea
# Copyright (c) 2020-2025 Instituto Nacional de Tecnología Industrial
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)
""" Base class for output options """
import difflib
import os
import re
from re import compile
from .error import KiPlotConfigurationError
from .gs import GS
from .misc import W_UNKOPS, DISTRIBUTORS_STUBS, DISTRIBUTORS_STUBS_SEPS, typeof, RE_LEN
from . import log

logger = log.get_logger()
HEX_DIGIT = '[A-Fa-f0-9]{2}'
PATTERNS_DEP = ['%c', '%d', '%F', '%f', '%M', '%p', '%r']
for n in range(1, 10):
    PATTERNS_DEP.append('%C'+str(n))


def _cl(text):
    """ Eliminates dangerous characters from the text """
    return re.sub(r'[\\\/\?%\*:|"<>]', '_', text)


class Optionable(object):
    """ A class to validate and hold configuration outputs/options.
        Is configured from a dict and the collected values are stored in its attributes. """
    _str_values_re = compile(r"string.*\](?:\[.*\])* \[([^\]]+)\]")
    _num_range_re = compile(r"number.*\](?:\[.*\])* \[(-?[\d\.]+),(-?[\d\.]+)\]")
    _num_values_re = compile(r"number.*\](?:\[.*\])* \[([^\]]+)\]")
    _default = None

    _color_re = re.compile(r"#("+HEX_DIGIT+"){3}$")
    _color_re_a = re.compile(r"#("+HEX_DIGIT+"){4}$")
    _color_re_component = re.compile(HEX_DIGIT)

    def __init__(self):
        self._unknown_is_error = False
        self._error_context = ''
        self._tree = {}
        self._configured = False
        # File/directory pattern expansion
        self._expand_id = ''
        self._expand_ext = ''
        # Used to indicate we have an output pattern and it must be suitable to generate multiple files
        self._output_multiple_files = False
        # The KiBoM output uses "variant" for the KiBoM variant, not for KiBot variants
        self._variant_is_real = True
        super().__init__()
        for var in ['output', 'variant', 'units', 'hide_excluded']:
            glb = getattr(GS, 'global_'+var)
            if glb and hasattr(self, var):
                setattr(self, var, glb)
                if GS.debug_level > 2:
                    logger.debug('Using global `{}`=`{}`'.format(var, glb))

    @staticmethod
    def _promote_str_to_list(val, doc, valid):
        if 'list(string)' not in valid or val == '_null':
            return val, False
        # Promote strings to list of strings
        if not val:
            return [], True
        if ',' in val and '{comma_sep}' in doc:
            return [v.strip() for v in val.split(',')], True
        return [val], True

    @staticmethod
    def _check_str(key, val, doc, valid):
        if not isinstance(val, str):
            raise KiPlotConfigurationError("Option `{}` must be a string".format(key))
        new_val, is_list = Optionable._promote_str_to_list(val, doc, valid)
        if '{no_case}' in doc:
            new_val = new_val.lower() if not is_list else [v.lower() for v in new_val]
        # If the docstring specifies the allowed values in the form [v1,v2...] enforce it
        m = Optionable._str_values_re.search(doc)
        if m:
            vals = [v.strip() for v in m.group(1).split(',')]
            if '*' not in vals:
                if not is_list:
                    wrong = val not in vals
                else:
                    for v in new_val:
                        if v not in vals:
                            wrong = True
                            val = v
                            break
                    else:
                        wrong = False
                if wrong:
                    raise KiPlotConfigurationError("Option `{}` must be any of {} not `{}`".format(key, vals, val))
        if is_list:
            Optionable._check_list_len(key, new_val, doc)
        return new_val

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
            return
        m = Optionable._num_values_re.search(doc)
        if m:
            vals = [float(v) for v in m.group(1).split(';')]
            if val not in vals and '*' not in vals:
                raise KiPlotConfigurationError("Option `{}` must be any of {} not `{}`".format(key, vals, val))

    @staticmethod
    def _check_bool(key, val):
        if not isinstance(val, bool):
            raise KiPlotConfigurationError("Option `{}` must be true/false".format(key))

    @staticmethod
    def _check_list_len(k, v, doc):
        m = re.search(RE_LEN, doc)
        if m:
            items = int(m.group(1))
            if len(v) != items:
                raise KiPlotConfigurationError(f"The `{k}` must contain {items} values ({v})")

    def get_doc_simple(self, name):
        return getattr(self, '_help_'+name)

    def get_doc(self, name, no_basic=False):
        try:
            doc = getattr(self, '_help_'+name).strip()
        except AttributeError:
            return None, name, False
        if doc[0] == '{':
            is_alias = True
            name = doc[1:-1]
            doc = getattr(self, '_help_'+name).strip()
        else:
            is_alias = False
        if no_basic and doc[0] == '*':
            # Remove the 'basic' indicator
            doc = doc[1:]
        return doc, name, is_alias

    def is_basic_option(self, name):
        help, _, _ = self.get_doc(name)
        return help and help[0] == '*'

    def add_to_doc(self, name, text, with_nl=True):
        doc = getattr(self, '_help_'+name).strip()
        setattr(self, '_help_'+name, doc+('.\n' if with_nl else '')+text)

    def set_doc(self, name, text):
        setattr(self, '_help_'+name, text)

    def get_valid_types(self, doc, skip_extra=False):
        assert doc[0] == '[', doc[0]+'\n'+str(self.__dict__)
        # Separate the valid types for this key
        sections = doc[1:].split('] ')
        valid = sections[0].split('|')
        real_help = ' '+'] '.join([x for x in sections[1:] if x[0] != '['])
        # Remove the XXXX=Value
        def_val = None
        if '=' in valid[-1]:
            res = valid[-1].split('=')
            valid[-1] = res[0]
            def_val = '='.join(res[1:])
        validation = []
        if not skip_extra:
            for v in valid:
                if v == 'number' or v == 'list(number)':
                    m = Optionable._num_range_re.search(doc)
                    if m:
                        min = float(m.group(1))
                        if int(min) == min:
                            min = int(min)
                        max = float(m.group(2))
                        if int(max) == max:
                            max = int(max)
                        validation.append((min, max))
                        continue
                    m = Optionable._num_values_re.search(doc)
                    if m:
                        validation.append(('C', m.group(1).split(';')))
                        continue
                if v == 'string' or v == 'list(string)':
                    m = Optionable._str_values_re.search(doc)
                    if m:
                        validation.append([v.strip() for v in m.group(1).split(',')])
                        continue
                validation.append(None)
        return valid, validation, def_val, real_help

    def check_string_dict(self, v_type, valid, k, v):
        if v_type != 'dict' or 'string_dict' not in valid:
            return False
        # A particular case for dict
        for key, value in v.items():
            if not isinstance(value, str):
                raise KiPlotConfigurationError(f"Key `{key}` of option `{k}` must be a string, not"
                                               f" `{typeof(value, Optionable)}`")
        return True

    def check_list_string_dict(self, v_type, valid, k, v):
        if v_type != 'list(dict)' or 'list(string_dict)' not in valid:
            return False
        # A particular case for list(dict)
        for item in v:
            for key, value in item.items():
                if not isinstance(value, str):
                    raise KiPlotConfigurationError(f"Key `{key}` of option `{k}` must be a string, not"
                                                   f" `{typeof(value, Optionable)}`")
        return True

    def _perform_config_mapping(self):
        """ Map the options to class attributes """
        attrs = self.get_attrs_for()
        if not isinstance(self._tree, dict):
            raise KiPlotConfigurationError('Found {} instead of dict'.format(type(self._tree)))
        for k, v in self._tree.items():
            # Map known attributes and avoid mapping private ones
            if (k[0] == '_') or (k not in attrs):
                if self._unknown_is_error:
                    valid = list(filter(lambda x: x[0] != '_', attrs.keys()))
                    msg = "Unknown {}option `{}`.".format(self._error_context, k)
                    possible = difflib.get_close_matches(k, valid, n=1)
                    if possible:
                        msg += " Did you meen {}?".format(possible[0])
                    msg += " Valid options: {}".format(valid)
                    raise KiPlotConfigurationError(msg)
                logger.warning(W_UNKOPS + "Unknown {}option `{}`".format(self._error_context, k))
                continue
            # Check the data type
            cur_doc, alias, is_alias = self.get_doc(k, no_basic=True)
            assert cur_doc[0] == '[', cur_doc[0]
            # Separate the valid types for this key
            valid, _, def_val, real_help = self.get_valid_types(cur_doc, skip_extra=True)
            if isinstance(v, type):
                # An optionable
                v.set_default(def_val)
            cur_val = getattr(self, alias)
            # Get the type used by the user as a string
            v_type = typeof(v, Optionable, valid)
            if (v_type not in valid and not self.check_string_dict(v_type, valid, k, v) and
               not self.check_list_string_dict(v_type, valid, k, v)):
                # Not a valid type for this key
                if v_type == 'None':
                    raise KiPlotConfigurationError("Empty option `{}`".format(k))
                if len(valid) == 1:
                    raise KiPlotConfigurationError("Option `{}` must be a {} not `{}`".format(k, valid[0], v_type))
                else:
                    raise KiPlotConfigurationError("Option `{}` must be any of {} not `{}`".format(k, valid, v_type))
            if v_type == 'boolean':
                Optionable._check_bool(k, v)
            elif v_type == 'number':
                Optionable._check_num(k, v, cur_doc)
            elif v_type == 'string':
                v = Optionable._check_str(k, v, cur_doc, valid)
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
                        if 'string_dict' not in valid:
                            # Create an object for the valid class
                            v = cur_val()
                            # Delegate the validation to the object
                            v.set_tree(new_val)
                            v.config(self)
                            # Promote to a list if possible
                            if 'list(dict)' in valid:
                                v = [v]
                    elif isinstance(v, list):
                        new_val = []
                        filtered_valid = [t[5:-1] for t in valid if t.startswith('list(')]
                        no_case = '{no_case}' in cur_doc
                        is_string_dict = 'string_dict' in filtered_valid
                        if is_string_dict:
                            filtered_valid.append('dict')
                        for element in v:
                            e_type = typeof(element, Optionable)
                            if e_type not in filtered_valid:
                                raise KiPlotConfigurationError("Option `{}` must be any of {} not `{}`".
                                                               format(element, filtered_valid, e_type))
                            if isinstance(element, dict) and not is_string_dict:
                                nv = cur_val()
                                nv.set_tree(element)
                                nv.config(self)
                                new_val.append(nv)
                            else:
                                if no_case and isinstance(element, str):
                                    element = element.lower()
                                new_val.append(element)
                        v = new_val
                        self._check_list_len(k, v, cur_doc)
            # Seems to be ok, map it
            dest_name = alias if is_alias else k
            setattr(self, dest_name, v)
            self.set_user_defined(dest_name)

    def set_user_defined(self, name):
        setattr(self, '_{}_user_defined'.format(name), True)

    def get_user_defined(self, name):
        name = '_{}_user_defined'.format(name)
        if hasattr(self, name):
            return getattr(self, name)
        return False

    def set_tree(self, tree):
        self._tree = tree

    def do_defaults(self):
        """ Assign the defaults to complex data types """
        for k, v in self.get_attrs_gen():
            if not isinstance(v, type):
                # We only process things that points to its class (Optionable)
                continue
            if self.get_user_defined(k):
                # If the user assigned a value skip it
                continue
            cur_doc, alias, is_alias = self.get_doc(k, no_basic=True)
            if is_alias:
                # Aliases ignored
                continue
            valid, _, def_val, real_help = self.get_valid_types(cur_doc, skip_extra=True)
            if def_val is None:
                # Use the class default, used for complex cases
                self.configure_from_default(k)
                continue
            new_val = None
            # TODO: Merge with adapt_default
            if def_val == '?':
                # The local config will creat something useful
                continue
            elif def_val == '{}':
                if 'string_dict' in valid:
                    new_val = {}
                else:
                    # The default initialization for the class
                    new_val = v()
                    new_val.config(self)
            elif def_val == '[{}]':
                # The default initialization for the class
                new_val = v()
                new_val.config(self)
                new_val = [new_val]
            elif def_val == '[]':
                # An empty list
                new_val = []
            elif def_val == 'true':
                new_val = True
            elif def_val == 'false':
                new_val = False
            elif def_val == 'null':
                # Explicit None
                new_val = None
            elif def_val[0] == "'":
                # String
                new_val, _ = self._promote_str_to_list(def_val[1:-1], real_help, valid)
            elif def_val[0] in {'-', '1', '2', '3', '4', '5', '6', '7', '8', '9', '0'}:
                new_val = float(def_val)
            else:
                assert new_val is not None, f'{self} {k} {def_val}'
            logger.debugl(3, f'Configuring from default: {k} -> {new_val}')
            setattr(self, k, new_val)

    def config(self, parent):
        self._parent = parent
        old_configured = self._configured
        if self._tree and not self._configured:
            self._perform_config_mapping()
        self._configured = True
        if not old_configured:
            self.do_defaults()
        if self._output_multiple_files and ('%i' not in self.output or '%x' not in self.output):
            raise KiPlotConfigurationError('The output pattern must contain %i and %x, otherwise file names will collide')

    def reconfigure(self, tree, parent=None):
        """ Configures an already configured object """
        # We need to reset the members that indicates which class is used for them
        self.__init__()
        # self._configured = False  done by __init__()
        self.set_tree(tree)
        self.config(parent if parent is not None else (self._parent if hasattr(self, '_parent') else None))

    def get_attrs_for(self):
        """ Returns all attributes """
        return dict(vars(self).items())

    def get_attrs_gen(self):
        """ Returns a (key, val) iterator on public attributes """
        return filter(lambda k: k[0][0] != '_', vars(self).items())

    @staticmethod
    def _find_global_variant():
        if GS.solved_global_variant:
            return GS.solved_global_variant.file_id
        return ''

    def _find_variant(self):
        """ Returns the text to add for the current variant.
            Also try with the globally defined variant.
            If no variant is defined an empty string is returned. """
        if not self._variant_is_real:
            return self.variant
        if hasattr(self, 'variant') and self.variant:
            self.variant = GS.solve_variant(self.variant)
            return self.variant.file_id
        return Optionable._find_global_variant()

    @staticmethod
    def _find_global_variant_name():
        if GS.solved_global_variant:
            return GS.solved_global_variant.name
        return ''

    def _find_variant_name(self):
        """ Returns the name for the current variant.
            Also try with the globally defined variant.
            If no variant is defined an empty string is returned. """
        if not self._variant_is_real:
            return self.variant
        if hasattr(self, 'variant') and self.variant:
            self.variant = GS.solve_variant(self.variant)
            return self.variant.name
        return Optionable._find_global_variant_name()

    @staticmethod
    def _find_global_subpcb():
        if GS.solved_global_variant and GS.solved_global_variant._sub_pcb:
            return GS.solved_global_variant._sub_pcb.name
        return ''

    def _find_subpcb(self):
        """ Returns the name of the sub-PCB.
            Also try with the globally defined variant.
            If no variant is defined an empty string is returned. """
        if not self._variant_is_real:
            return ''
        if hasattr(self, 'variant') and self.variant:
            self.variant = GS.solve_variant(self.variant)
            if self.variant._sub_pcb:
                return self.variant._sub_pcb.name
        return Optionable._find_global_subpcb()

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
            name = name.replace('%S', _cl(self._find_subpcb()))
            name = name.replace('%x', self._expand_ext)
            replace_id = ''
            if parent and hasattr(parent, 'output_id'):
                replace_id = _cl(parent.output_id)
            name = name.replace('%I', replace_id)
        else:
            name = name.replace('%v', _cl(Optionable._find_global_variant()))
            name = name.replace('%V', _cl(Optionable._find_global_variant_name()))
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
        # Replace KiCad 6 variables first
        name = GS.expand_text_variables(name)
        # Determine if we need to expand SCH and/or PCB related data
        has_dep_exp = any((x in name for x in PATTERNS_DEP))
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
            name = name.replace('%M', GS.pcb_last_dir)
            name = name.replace('%p', _cl(GS.pcb_title))
            name = name.replace('%r', _cl(GS.pcb_rev))
            for num, val in enumerate(GS.pcb_com):
                name = name.replace('%C'+str(num+1), _cl(val))
        if GS.sch and do_sch:
            name = name.replace('%c', _cl(GS.sch_comp))
            name = name.replace('%d', _cl(GS.sch_date))
            name = name.replace('%F', GS.sch_no_ext)
            name = name.replace('%f', GS.sch_basename)
            name = name.replace('%M', GS.sch_last_dir)
            name = name.replace('%p', _cl(GS.sch_title))
            name = name.replace('%r', _cl(GS.sch_rev))
            for num, val in enumerate(GS.sch_com):
                name = name.replace('%C'+str(num+1), _cl(val))
        # Also replace KiCad 6 variables after it
        name = GS.expand_text_variables(name)
        if make_safe:
            name = GS.sanitize_file_name(name)
        if GS.debug_level > 3:
            logger.debug('Expanded `{}`'.format(name))
        return name

    def expand_filename_pcb(self, name, make_safe=True):
        """ Expands %* values in filenames.
            Uses data from the PCB. """
        # This member can be called with a preflight object
        return Optionable.expand_filename_both(self, name, is_sch=False, make_safe=make_safe)

    def expand_filename_sch(self, name):
        """ Expands %* values in filenames.
            Uses data from the SCH. """
        # This member can be called with a preflight object
        return Optionable.expand_filename_both(self, name)

    @staticmethod
    def force_list(val, comma_sep=True, lower_case=False, default=None):
        """ Used for values that accept a string or a list of strings.
            The string can be a comma separated list """
        if isinstance(val, type):
            # Not used
            val = [] if default is None else default
        elif isinstance(val, str):
            # A string
            if val:
                if comma_sep:
                    val = [v.strip() for v in val.split(',')]
                else:
                    val = [val]
            else:
                # Empty string
                val = []
        if lower_case:
            return [c.lower() for c in val]
        return val

    @classmethod
    def get_default(cls):
        return cls._default

    def configure_from_default(self, member):
        """ Initializes the `member` using its default value.
            The `member` should be assigned with the class used for it """
        v = getattr(self, member)
        default = v.get_default()
        assert default is not None, f'Missing default for {member} in {self}'
        if isinstance(default, dict):
            o = v()
            o.set_tree(default)
            o.config(self)
            default = o
        elif isinstance(default, list) and isinstance(default[0], dict):
            res = []
            for item in default:
                o = v()
                o.set_tree(item)
                o.config(self)
                res.append(o)
            default = res
        logger.debugl(3, f'Configuring from default: {member} -> {default}')
        setattr(self, member, default)

    def validate_color_str(self, color):
        return self._color_re.match(color) or self._color_re_a.match(color)

    def validate_color(self, name):
        if not self.validate_color_str(getattr(self, name)):
            raise KiPlotConfigurationError('Invalid color for `{}` use `#rrggbb` or `#rrggbbaa` with hex digits'.format(name))

    def validate_colors(self, names):
        for color in names:
            self.validate_color(color)

    def parse_one_color(self, color, scale=1/255.0):
        res = self._color_re_component.findall(color)
        alpha = 1.0
        if len(res) > 3:
            alpha = int(res[3], 16)*scale
        return (int(res[0], 16)*scale, int(res[1], 16)*scale, int(res[2], 16)*scale, alpha)

    def color_to_rgb(self, color):
        index = 4 if len(color) > 4 else 0
        alpha = color[index+3]
        if alpha == 1.0:
            return "rgb({}, {}, {})".format(round(color[index]*255.0), round(color[index+1]*255.0),
                                            round(color[index+2]*255.0))
        return "rgba({}, {}, {}, {})".format(round(color[index]*255.0), round(color[index+1]*255.0),
                                             round(color[index+2]*255.0), alpha)

    def color_str_to_rgb(self, color):
        return self.color_to_rgb(self.parse_one_color(color))

    @staticmethod
    def _solve_field_name(field, empty_when_none):
        """ Applies special replacements for field """
        # The global name for the LCSC part field
        if GS.global_field_lcsc_part:
            logger.debug('- User selected: '+GS.global_field_lcsc_part)
            return GS.global_field_lcsc_part
        # No name defined, try to figure out
        if not GS.sch and GS.sch_file:
            GS.load_sch()
        if not GS.sch:
            logger.debug("- No schematic loaded, can't search the name")
            return '' if empty_when_none else 'LCSC#'
        if hasattr(GS.sch, '_field_lcsc_part'):
            return GS.sch._field_lcsc_part
        # Look for a common name
        fields = {f.lower() for f in GS.sch.get_field_names([])}
        for stub in DISTRIBUTORS_STUBS:
            fld = 'lcsc'+stub
            if fld in fields:
                GS.sch._field_lcsc_part = fld
                return fld
            if stub != '#':
                for sep in DISTRIBUTORS_STUBS_SEPS:
                    fld = 'lcsc'+sep+stub
                    if fld in fields:
                        GS.sch._field_lcsc_part = fld
                        return fld
        if 'lcsc' in fields:
            GS.sch._field_lcsc_part = 'LCSC'
            return 'LCSC'
        # Look for a field that only contains LCSC codes
        comps = GS.sch.get_components()
        lcsc_re = re.compile(r'C\d+')
        for f in fields:
            found = False
            for c in comps:
                val = c.get_field_value(f).strip()
                if not val:
                    continue
                if lcsc_re.match(val):
                    found = True
                else:
                    found = False
                    break
            if found:
                GS.sch._field_lcsc_part = f
                return f
        logger.debug('- No LCSC field found')
        res = '' if empty_when_none else 'LCSC#'
        GS.sch._field_lcsc_part = res
        return res

    @staticmethod
    def solve_field_name(field, empty_when_none=False):
        if field[:7] != '_field_':
            return field
        rest = field[7:]
        if rest == 'current':
            return GS.global_field_current[0] if GS.global_field_current else field
        if rest == 'lcsc_part':
            logger.debug('Looking for LCSC field name')
            field = Optionable._solve_field_name(field, empty_when_none)
            logger.debug('Using {} as LCSC field name'.format(field))
            return field
        field_or_empty = '' if empty_when_none else field
        if rest == 'package':
            return GS.global_field_package[0] if GS.global_field_package else field_or_empty
        if rest == 'power':
            return GS.global_field_power[0] if GS.global_field_power else field_or_empty
        if rest == 'temp_coef':
            return GS.global_field_temp_coef[0] if GS.global_field_temp_coef else field_or_empty
        if rest == 'tolerance':
            return GS.global_field_tolerance[0] if GS.global_field_tolerance else field_or_empty
        if rest == 'voltage':
            return GS.global_field_voltage[0] if GS.global_field_voltage else field_or_empty
        if rest == 'part_number':
            return GS.global_field_part_number[0] if GS.global_field_part_number else field_or_empty
        if rest == 'manufacturer':
            return GS.global_field_manufacturer[0] if GS.global_field_manufacturer else field_or_empty
        if rest == 'dist_part_number':
            return GS.global_field_dist_part_number[0] if GS.global_field_dist_part_number else field_or_empty
        if rest == 'distributor':
            return GS.global_field_distributor[0] if GS.global_field_distributor else field_or_empty
        return field


class BaseOptions(Optionable):
    """ A class to validate and hold output options.
        Is configured from a dict and the collected values are stored in its attributes. """
    def __init__(self):
        super().__init__()

    def read_vals_from_po(self, po):
        """ Set attributes from a PCB_PLOT_PARAMS (plot options) """
        return

    def ensure_tool(self, name):
        """ Looks for a mandatory dependency """
        return GS.check_tool_dep(self._parent.type, name, fatal=True)

    def ensure_tool_get_ver(self, name):
        """ Looks for a mandatory dependency, also returns its version """
        return GS.check_tool_dep_get_ver(self._parent.type, name, fatal=True)

    def check_tool(self, name):
        """ Looks for a dependency """
        return GS.check_tool_dep(self._parent.type, name, fatal=False)

    def expand_filename(self, dir, name, id, ext, make_safe=True):
        cur_id = self._expand_id
        cur_ext = self._expand_ext
        self._expand_id = id
        self._expand_ext = ext
        name = self.expand_filename_both(name, is_sch=self._parent._sch_related, make_safe=make_safe)
        res = os.path.abspath(os.path.join(dir, name))
        self._expand_id = cur_id
        self._expand_ext = cur_ext
        return res


class PanelOptions(BaseOptions):
    """ A class for options that uses KiKit's units """
    _num_regex = re.compile(r'([\d\.]+)(mm|cm|dm|m|mil|inch|in)')
    _per_regex = re.compile(r'([\d\.]+)%')
    _ang_regex = re.compile(r'([\d\.]+)(deg|°|rad)')

    def add_units(self, ops, def_units=None, convert=False, percent=False):
        if def_units is None:
            def_units = self._parent._parent.units
        for op in ops:
            val = getattr(self, op)
            _op = '_'+op
            if val is None:
                if convert:
                    setattr(self, _op, 0)
                continue
            if isinstance(val, (int, float)):
                setattr(self, op, str(val)+def_units)
                if convert:
                    setattr(self, _op, int(val*GS.kikit_units_to_kicad[def_units]))
            else:
                if percent and PanelOptions._per_regex.match(val):
                    continue
                m = PanelOptions._num_regex.match(val)
                if m is None:
                    raise KiPlotConfigurationError('Malformed value `{}: {}` must be a number and units'.format(op, val))
                num = m.group(1)
                try:
                    num_d = float(num)
                except ValueError:
                    num_d = None
                if num_d is None:
                    raise KiPlotConfigurationError('Malformed number in `{}` ({})'.format(op, num))
                if convert:
                    setattr(self, _op, int(num_d*GS.kikit_units_to_kicad[m.group(2)]))

    def add_angle(self, ops, def_units=None):
        if def_units is None:
            def_units = self._parent._parent.default_angles
        for op in ops:
            val = getattr(self, op)
            if isinstance(val, (int, float)):
                setattr(self, op, str(val)+def_units)
            else:
                m = PanelOptions._ang_regex.match(val)
                if m is None:
                    raise KiPlotConfigurationError('Malformed angle `{}: {}` must be a number and its type'.format(op, val))
                num = m.group(1)
                try:
                    num_d = float(num)
                except ValueError:
                    num_d = None
                if num_d is None:
                    raise KiPlotConfigurationError('Malformed number in `{}` ({})'.format(op, num))
