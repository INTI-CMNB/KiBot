# -*- coding: utf-8 -*-
# Copyright (c) 2023-2024 Salvador E. Tropea
# Copyright (c) 2023-2024 Instituto Nacional de Tecnología Industrial
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)
# Description: Extracts information from the distributor spec and fills fields
import re
from .bom.units import comp_match, get_prefix, ParsedValue
from .bom.xlsx_writer import get_spec
from .error import KiPlotConfigurationError
from .kiplot import look_for_output, run_output
from .misc import W_FLDCOLLISION, pretty_list
# from .gs import GS
from .optionable import Optionable
from .macros import macros, document, filter_class  # noqa: F401
from . import log

logger = log.get_logger()
UNITS = {'voltage': 'V', 'power': 'W', 'current': 'A'}
EI_TYPES = {'value': 'value', 'tolerance': 'percent', 'footprint': 'string', 'power': 'power', 'current': 'current',
            'voltage': 'voltage', 'frequency': 'string', 'temp_coeff': 'string', 'manf': 'string', 'size': 'string'}
DEF_CHECK = ['_value', '_tolerance', '_power', '_current', '_voltage', '_temp_coeff']


class SpecOptions(Optionable):
    """ A spec to copy """
    _default = [{'spec': '_voltage', 'field': '_field_voltage'}, {'spec': '_tolerance', 'field': '_field_tolerance'},
                {'spec': '_power', 'field': '_field_power'}, {'spec': '_current', 'field': '_field_current'}]

    def __init__(self):
        super().__init__()
        self._unknown_is_error = True
        with document:
            self.spec = Optionable
            """ *[string|list(string)=''] {comma_sep} Name/s of the source spec/s.
                The following names are uniform across distributors: '_desc', '_value', '_tolerance', '_footprint',
                '_power', '_current', '_voltage', '_frequency', '_temp_coeff', '_manf' and '_size' """
            self.field = ''
            """ *Name of the destination field """
            self.policy = 'overwrite'
            """ [overwrite,update,new] Controls the behavior of the copy mechanism.
                `overwrite` always copy the spec value,
                `update` copy only if the field already exist,
                `new` copy only if the field doesn't exist. """
            self.collision = 'warning'
            """ [warning,error,ignore] How to report a collision between the current value and the new value """
            self.type = 'string'
            """ [percent,voltage,power,current,value,string] How we compare the current value to determine a collision.
                `value` is the component value i.e. resistance for R* """
        self._field_example = 'RoHS'
        self._spec_example = 'rohs_status'

    def config(self, parent):
        super().config(parent)
        if not self.field:
            raise KiPlotConfigurationError("Missing or empty `field` in spec_to_field filter ({})".format(str(self._tree)))
        if not self.spec:
            raise KiPlotConfigurationError("Missing or empty `spec` in spec_to_field filter ({})".format(str(self._tree)))

    def __str__(self):
        return pretty_list(self.spec)+' -> '+self.field


class CheckDistFields(Optionable):
    _default = DEF_CHECK


@filter_class
class Spec_to_Field(BaseFilter):  # noqa: F821
    """ Spec to Field
        This filter extracts information from the specs obtained from component distributors
        and fills fields.
        I.e. create a field with the RoHS status of a component.
        In order to make it work you must be able to get prices using the KiCost options of
        the `bom` output. Make sure you can do this before trying to use this filter.
        Usage [example](https://inti-cmnb.github.io/kibot-examples-1/spec_to_field/) """
    def __init__(self):
        super().__init__()
        self._is_transform = True
        with document:
            self.from_output = ''
            """ *Name of the output used to collect the specs.
                Currently this must be a `bom` output with KiCost enabled and a distributor that returns specs """
            self.specs = SpecOptions
            """ *[list(dict)|dict] One or more specs to be copied """
            self.check_dist_coherence = True
            """ Check that the data we got from different distributors is equivalent """
            self.check_dist_fields = CheckDistFields
            """ [string|list(string)] {comma_sep} List of fields to include in the check.
                For a full list of fields consult the `specs` option """
        self._from = None
        self._check_dist_fields_example = DEF_CHECK
        self._from_output_example = 'bom_output_name'

    def config(self, parent):
        super().config(parent)
        if not self.from_output:
            raise KiPlotConfigurationError("You must specify an output that collected the specs")
        if not self.specs:
            raise KiPlotConfigurationError("At least one spec must be provided ({})".format(str(self._tree)))

    def _normalize(self, val, kind, comp):
        val = val.strip()
        if kind == 'string':
            return val
        if kind == 'percent':
            # TODO: What about +20%, -10%?
            res = re.match(r"(?:\+/-|±|\+-)?\s*(\d+)\s*%?", val)
            if not res:
                return val
            return res.group(1)+'%'
        if kind == 'value':
            if not comp.ref_prefix or comp.ref_prefix[0] not in "RLC":
                return val
            res = comp_match(val, comp.ref_prefix, comp.ref, relax_severity=True, stronger=True)
            if not res:
                return val
            return str(res)
        # voltage,power,current
        new_val = re.sub(r"\s*(Volts?|V|Watts?|W|Amperes?|Ampers|Amp|A)", '', val)
        # Change things like 0.125 to 125 m
        res = comp_match(new_val, ' ', comp.ref, relax_severity=True, stronger=True)
        if res is None:
            if ',' not in new_val:
                return val
            # Some distributor APIs can return multiple values separated by comma
            res_many = []
            for v in new_val.split(','):
                res = comp_match(v.strip(), ' ', comp.ref, relax_severity=True, stronger=True)
                if res is not None:
                    res.unit = UNITS[kind]
                    res_many.append(res)
            if not res_many:
                return val
            res = res_many[0]
            reference = str(res)
            if len(res_many) > 1:
                for r in res_many[1:]:
                    if str(r) != reference:
                        logger.warning(W_FLDCOLLISION+'Inconsistencies in multiple values {}: `{}` ({} vs {})'.
                                       format(comp.ref, val, r, reference))
        res.unit = UNITS[kind]
        return str(res)

    def normalize(self, old_val, kind, comp):
        val = self._normalize(old_val, kind, comp)
        logger.debugl(3, "- Normalize {} -> {}".format(old_val, val))
        return val

    def compare(self, cur_val, spec_val):
        cur_val = cur_val.lower().strip()
        spec_val = spec_val.lower().strip()
        return cur_val == spec_val

    def solve_from(self):
        if self._from is not None:
            return
        # Check the renderer output is valid
        out = look_for_output(self.from_output, 'from_output', self._parent, {'bom'})
        if not out._done:
            run_output(out)
        self._from = out

    def update_extra_info(self, res, attr, ei, dattr, pattern: str = "{}", units=""):
        if dattr in ei:
            # Don't overwrite collected data
            return
        value = res.get_extra(attr)
        if not value:
            # No result for this
            return
        if isinstance(value, float):
            if int(value) == value:
                value = int(value)
            if units:
                # Change things like 0.125 to 125 m
                v, pow = get_prefix(value, '')
                parsed = ParsedValue(v, pow, units)
                value = str(parsed)
        ei[dattr] = pattern.format(value)

    def check_coherent(self, c):
        if not self.check_dist_coherence or not hasattr(c, 'kicost_part'):
            return
        extra_info = {}
        for d, dd in c.kicost_part.dd.items():
            ei = dd.extra_info
            if not ei:
                # We got nothing for this distributor
                continue
            if 'desc' in ei and 'value' not in ei:
                # Very incomplete extra info, try to fill it
                desc = ei['desc']
                logger.debugl(3, '- Parsing {}'.format(desc))
                res = comp_match(desc, c.ref_prefix, c.ref, relax_severity=True, stronger=True)
                if res:
                    ei['value'] = str(res)
                    self.update_extra_info(res, 'tolerance', ei, 'tolerance', "{}%")
                    self.update_extra_info(res, 'voltage_rating', ei, 'voltage', units="V")
                    self.update_extra_info(res, 'size', ei, 'footprint')
                    self.update_extra_info(res, 'characteristic', ei, 'temp_coeff')
                    self.update_extra_info(res, 'power_rating', ei, 'power', units="W")
                    logger.debugl(3, '- New extra_info: {}'.format(ei))
            for n, v in ei.items():
                if '_'+n not in self.check_dist_fields:
                    continue
                if n not in extra_info:
                    # First time we see it
                    extra_info[n] = (self.normalize(v, EI_TYPES[n], c), d)
                else:
                    cur_val, cur_dist = extra_info[n]
                    v = self.normalize(v, EI_TYPES[n], c)
                    if not self.compare(cur_val, v):
                        desc = "`{}` vs `{}` collision, `{}` != `{}`".format(d, cur_dist, v, cur_val)
                        logger.non_critical_error(desc)

    def filter(self, comp):
        self.solve_from()
        self.check_coherent(comp)
        for s in self.specs:
            field_solved = Optionable.solve_field_name(s.field)
            field = field_solved.lower()
            spec_name = []
            spec_val = set()
            for sp in s.spec:
                name, val = get_spec(comp.kicost_part, sp)
                if name:
                    spec_name.append(name)
                if val:
                    val = self.normalize(val, s.type, comp)
                    spec_val.add(val)
            spec_name = ','.join(spec_name)
            spec_val = ' '.join(spec_val)
            if not spec_name or not spec_val:
                # No info
                continue
            has_field = comp.is_field(field)
            cur_val = comp.get_field_value(field) if has_field else None
            if cur_val:
                cur_val = self.normalize(cur_val, s.type, comp)
                if cur_val == spec_val:
                    # Already there
                    continue
                if not self.compare(cur_val, spec_val):
                    # Collision
                    desc = "{} field `{}` collision, has `{}`, found `{}`".format(comp.ref, field_solved, cur_val, spec_val)
                    if s.collision == 'warning':
                        logger.warning(W_FLDCOLLISION+desc)
                    elif s.collision == 'error':
                        raise KiPlotConfigurationError(desc)
            if s.policy == 'overwrite' or (self.p == 'update' and has_field) or (s.policy == 'new' and not has_field):
                comp.set_field(field_solved, spec_val)
                logger.debugl(2, "- {} {}: {} ({})".format(comp.ref, field_solved, spec_val, spec_name))
