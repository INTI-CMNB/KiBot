# -*- coding: utf-8 -*-
# Copyright (c) 2020-2023 Salvador E. Tropea
# Copyright (c) 2020-2023 Instituto Nacional de Tecnología Industrial
# Copyright (c) 2016-2020 Oliver Henry Walters (@SchrodingersGat)
# License: MIT
# Project: KiBot (formerly KiPlot)
# Adapted from: https://github.com/SchrodingersGat/KiBoM
"""
Units:
This file contains a set of functions for matching values which may be written in different formats
e.g.
0.1uF = 100n (different suffix specified, one has missing unit)
0R1 = 0.1Ohm (Unit replaces decimal, different units)
Oriented to normalize and sort R, L and C values.
"""
from decimal import Decimal
import re
import locale
from math import log10
from .. import log
from ..misc import W_BADVAL1, W_BADVAL2, W_BADVAL3, W_BADVAL4, W_EXTRAINVAL
from .electro_grammar import parse

logger = log.get_logger()

PREFIX_MICRO = [u"μ", u"µ", "u", "micro"]
PREFIX_MILLI = ["milli", "m"]
PREFIX_NANO = ["nano", "n"]
PREFIX_PICO = ["pico", "p"]
PREFIX_KILO = ["kilo", "k"]
PREFIX_MEGA = ["mega", "meg", "M"]
PREFIX_GIGA = ["giga", "g"]

# All prefixes
PREFIX_ALL = PREFIX_PICO + PREFIX_NANO + PREFIX_MICRO + PREFIX_MILLI + PREFIX_KILO + PREFIX_MEGA + PREFIX_GIGA
MAX_POW_PREFIX = 9
MIN_POW_PREFIX = -12
PREFIXES = {-15: 'f', -12: 'p', -9: 'n', -6: u"µ", -3: 'm', 0: '', 3: 'k', 6: 'M', 9: 'G'}

# Common methods of expressing component units
# Note: we match lowercase string, so both: Ω and Ω become the lowercase omega
UNIT_R = ["r", "ohms", "ohm", u'\u03c9']
UNIT_C = ["farad", "f"]
UNIT_L = ["henry", "h"]
OHMS = u"Ω"

UNIT_ALL = UNIT_R + UNIT_C + UNIT_L

GRAM_TYPES = {'inductor': 'L', 'capacitor': 'C', 'resistor': 'R', 'led': ''}
# Compiled regex to match the values
match = None
# Current locale decimal point value
decimal_point = None
# Parser cache
parser_cache = {}
# Flag to indicate we already warned about extra data
warn_extra_issued = False


def get_decima_point():
    return decimal_point


class ParsedValue(object):
    def __init__(self, v, pow, unit, extra=None):
        # From a value that matched the regex
        ival = int(v)
        self.norm_val = int(v) if v == ival else v
        self.exp = pow
        self.unit = unit
        self.prefix = PREFIXES[pow]
        self.extra = extra

    def __str__(self):
        return '{} {}{}'.format(self.norm_val, self.prefix, self.unit)

    def get_sortable(self):
        mult = pow(10, self.exp)
        if self.unit in "FH":
            # femto Farads
            return "{0:15d}".format(int(self.norm_val * 1e15 * mult + 0.1))
        # milli Ohms
        return "{0:15d}".format(int(self.norm_val * 1000 * mult + 0.1))

    def get_decimal(self):
        return Decimal(str(self.norm_val))*pow(10, Decimal(self.exp))

    def get_extra(self, property):
        return self.extra.get(property) if self.extra else None


def get_unit(unit, ref_prefix):
    """ Return a simplified version of a units string, for comparison purposes  """
    if not unit:
        if ref_prefix == 'L':
            return "H"
        if ref_prefix == 'C':
            return "F"
        return OHMS
    unit = unit.lower()
    if unit in UNIT_R:
        return OHMS
    if unit in UNIT_C:
        return "F"
    if unit in UNIT_L:
        return "H"


def get_prefix_simple(prefix):
    """ Return the (numerical) value of a given prefix """
    if not prefix:
        return 0
    # 'M' is mega, 'm' is milli
    if prefix != 'M':
        prefix = prefix.lower()
    if prefix in PREFIX_PICO:
        return -12
    if prefix in PREFIX_NANO:
        return -9
    if prefix in PREFIX_MICRO:
        return -6
    if prefix in PREFIX_MILLI:
        return -3
    if prefix in PREFIX_KILO:
        return 3
    if prefix in PREFIX_MEGA:
        return 6
    if prefix in PREFIX_GIGA:
        return 9
    # Unknown, we shouldn't get here because the regex matched
    # BUT: I found that sometimes unexpected things happen, like mu matching micro and then we reaching this code
    #      Now is fixed, but I can't be sure some bizarre case is overlooked
    logger.non_critical_error('Unknown prefix, please report')
    return 0


def get_prefix(val, prefix):
    if val == 0:
        return 0, 0
    pow = get_prefix_simple(prefix)
    # Try to normalize it
    while val >= 1000.0 and pow < MAX_POW_PREFIX:
        val /= 1000.0
        pow += 3
    while val < 1.0 and pow > MIN_POW_PREFIX:
        val *= 1000.0
        pow -= 3
    return val, pow


def group_string(group):  # Return a reg-ex string for a list of values
    return "|".join(group)


def match_string():
    return r"(\d*\.?\d*)\s*(" + group_string(PREFIX_ALL) + ")*(" + group_string(UNIT_ALL) + r")*(\d*)$"


def value_from_grammar(r):
    """ Convert a result parsed by the Lark grammar to a ParsedResult object """
    val = r.get('val')
    if not val:
        return None
    # Create an object with the result
    val, pow = get_prefix(float(val), PREFIXES[int(log10(r['mult']))])
    parsed = ParsedValue(val, pow, get_unit(None, GRAM_TYPES[r['type']]), r)
    return parsed


def check_extra_data(r, v):
    global warn_extra_issued
    if warn_extra_issued:
        return
    if 'tolerance' in r or 'characteristic' in r or 'voltage_rating' in r or 'power_rating' in r or 'size' in r:
        logger.warning(W_EXTRAINVAL+f'Avoid adding extra information in the component value, use separated fields ({v})')
        warn_extra_issued = True


def comp_match(component, ref_prefix, ref=None, relax_severity=False, stronger=False, warn_extra=False):
    """
    Return a normalized value and units for a given component value string
    Also tries to separate extra data, i.e. tolerance, using a complex parser
    """
    original = component
    global parser_cache
    parsed = parser_cache.get(original+ref_prefix)
    if parsed:
        return parsed
    # Remove useless spaces
    component = component.strip()
    # ~ is the same as empty for KiCad
    if component == '~':
        component = ''
    # Convert the decimal point from the current locale to a '.'
    global decimal_point
    if decimal_point is None:
        decimal_point = locale.localeconv()['decimal_point']
        logger.debug('Decimal point `{}`'.format(decimal_point))
        # Avoid conversions for '.'
        if decimal_point == '.':
            decimal_point = ''
    if decimal_point:
        component = re.sub(r'(\d)'+decimal_point+r'(\d)', r'\1.\2', component)

    with_commas = component
    # Remove any commas
    component = component.strip().replace(",", "")

    # Get the compiled regex
    global match
    if not match:
        # Ignore case
        match = re.compile(match_string(), flags=re.IGNORECASE)

    log_func_warn = logger.debug if relax_severity else logger.warning
    where = ' in {}'.format(ref) if ref is not None else ''
    result = match.match(component)
    if not result:
        # This is used to parse things like "1/8 W", but we get "1/8" here
        result = re.match(r'(\d+)\/(\d+)', component)
        if result:
            # Avoid division by zero
            if int(result.group(2)) != 0:
                val = int(result.group(1))/int(result.group(2))
                val, pow = get_prefix(val, '')
                parsed = ParsedValue(val, pow, get_unit('', ref_prefix))
                # Cache the result
                parser_cache[original+ref_prefix] = parsed
                return parsed
            else
                result = None
                
    if not result:
        # Failed with the regex, try with the parser
        result = parse(ref_prefix[0]+' '+with_commas, with_extra=True, stronger=stronger)
        if result:
            if warn_extra:
                check_extra_data(result, original)
            result = value_from_grammar(result)
            if result and result.get_extra('discarded'):
                discarded = " ".join(('`'+x+'`' for x in result.get_extra('discarded')))
                log_func_warn(W_BADVAL4+"Malformed value: `{}` (discarded: {}{})".format(original, discarded, where))
        if not result:
            log_func_warn(W_BADVAL1+"Malformed value: `{}` (no match{})".format(original, where))
            return None
        # Cache the result
        parser_cache[original+ref_prefix] = result
        return result

    value, prefix, units, post = result.groups()
    if value == '.':
        log_func_warn(W_BADVAL2+"Malformed value: `{}` (reduced to decimal point{})".format(original, where))
        return None
    if value == '':
        value = '0'

    # Special case where units is in the middle of the string
    # e.g. "0R05" for 0.05Ohm
    # In this case, we will NOT have a decimal
    # We will also have a trailing number
    if post:
        if "." in value:
            log_func_warn(W_BADVAL3+"Malformed value: `{}` (unit split, but contains decimal point{})".format(original, where))
            return None
        value = float(value)
        postValue = float(post)/(10**len(post))
        val = value*1.0+postValue
    else:
        val = float(value)

    # Create an object with the result
    val, pow = get_prefix(val, prefix)
    parsed = ParsedValue(val, pow, get_unit(units, ref_prefix))
    # Cache the result
    parser_cache[original+ref_prefix] = parsed
    return parsed


def compare_values(c1, c2):
    """ Compare two values """
    # These are the results from comp_match()
    r1 = c1.value_sort
    r2 = c2.value_sort
    # If they can't be parsed use the value
    if not r1 or not r2:
        return c1.value.strip() == c2.value.strip()
    # Compare the normalized representation, i.e. 3300 == 3k3 == 3.3 k
    return str(r1) == str(r2)
