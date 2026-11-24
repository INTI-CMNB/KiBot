# -*- coding: utf-8 -*-
# Copyright (c) 2023 Salvador E. Tropea
# Copyright (c) 2023 Instituto Nacional de Tecnología Industrial
# License: MIT
# Project: KiBot (formerly KiPlot)

from decimal import Decimal
from lark import Lark, Transformer
import os
from ..gs import GS
from .. import log

logger = log.get_logger()
# Metric to imperial package sizes
TO_IMPERIAL = {'0402': '01005',
               '0603': '0201',
               '1005': '0402',
               '1608': '0603',
               '2012': '0805',
               '2520': '1008',
               '3216': '1206',
               '3225': '1210',
               '4516': '1806',
               '4532': '1812',
               '5025': '2010',
               '6332': '2512'}
parser = None


class ComponentTransformer(Transformer):
    """ Transforms a tree parsed by Lark to the electro-grammar dict """
    def __init__(self):
        self.parsed = {}
        # Extra information, not in the original lib and needed for internal purposes
        self.extra = {}

    def value3(self, d, type):
        """ VALUE [METRIC_PREFIX [MANTISSA]] """
        v = Decimal(d[0])
        c = len(d)
        if c >= 3:
            # We have something like 2n2
            dec = d[2]
            c_dec = len(dec)
            v += Decimal(dec)/(Decimal(10)*c_dec)
        self.extra['val'] = v
        if c >= 2:
            # Metric prefix
            v *= d[1]
            self.extra['mult'] = d[1]
        else:
            self.extra['mult'] = Decimal(1)
        v = float(v)
        self.parsed[type] = v
        return v

    def value2(self, d, type):
        """ VALUE [MANTISSA] """
        v = float(d[0])
        c = len(d)
        if c >= 2:
            # We have something like 3V3
            dec = d[1]
            c_dec = len(dec)
            v += float(dec)/(10.0*c_dec)
        self.parsed[type] = v
        return v

    def value1(self, d, type):
        """ VALUE """
        v = float(d[0])
        iv = round(v)
        if iv == v:
            v = iv
        self.parsed[type] = v
        return v

    def tolerance(self, d):
        return self.value1(d, 'tolerance')

    def voltage_rating(self, d):
        return self.value2(d, 'voltage_rating')

    def temp_coef(self, d):
        c_len = len(d)
        if c_len == 3:
            # Class 2: i.e. X7R
            v = d[0].value+d[1].value+d[2].value
        else:
            # Class 1: i.e. C0G
            v = d[0].type
        self.parsed['characteristic'] = v.upper()
        return v

    def power_rating(self, d):
        if len(d) == 1:
            # 1 W
            v = float(d[0])
        elif d[0].type == 'INT':
            # 1/4 W
            v = float(d[0].value)/float(d[1].value)
        else:
            # 250 mW
            v = float(Decimal(d[0].value)*d[1])
        self.parsed['power_rating'] = v
        return v

    def color(self, d):
        c = d[0].value.lower()
        self.parsed['color'] = c
        return c

    def set_type(self, type, d):
        self.parsed['type'] = type
        return d

    # Package size
    def imperial_size(self, d):
        s = d[0].value
        self.parsed['size'] = s
        return s

    def unambigious_metric_size(self, d):
        s = TO_IMPERIAL[d[0].value]
        self.parsed['size'] = s
        return s

    metric_size_base = unambigious_metric_size

    # RLC
    def resistance(self, d):
        return self.value3(d, 'resistance')

    resistance_no_r = resistance

    def inductance(self, d):
        return self.value3(d, 'inductance')

    inductance_no_henry = inductance

    def capacitance(self, d):
        return self.value3(d, 'capacitance')

    capacitance_no_farad = capacitance

    # Known components
    def inductor(self, d):
        return self.set_type('inductor', d)

    def capacitor(self, d):
        return self.set_type('capacitor', d)

    def resistor(self, d):
        return self.set_type('resistor', d)

    def led(self, d):
        return self.set_type('led', d)

    # Metrix prefixes
    def giga(self, _):
        return Decimal('1e9')

    def mega(self, _):
        return Decimal('1e6')

    def kilo(self, _):
        return Decimal('1e3')

    def unit(self, _):
        return Decimal(1)

    def milli(self, _):
        return Decimal('1e-3')

    def nano(self, _):
        return Decimal('1e-9')

    def micro(self, _):
        return Decimal('1e-6')

    def pico(self, _):
        return Decimal('1e-12')

    def femto(self, _):
        return Decimal('1e-15')

    def crap(self, v):
        if 'discarded' in self.extra:
            self.extra['discarded'].append(v[0].value)
        else:
            self.extra['discarded'] = [v[0].value]
        return None


def initialize():
    global parser
    if parser is not None:
        return
    with open(os.path.join(GS.get_resource_path('parsers'), 'electro.lark'), 'rt') as f:
        g = f.read()
    parser = Lark(g, start='main')  # , debug=DEBUG)


def parse(text: str, with_extra=False, stronger=False):
    initialize()
    if stronger:
        text = text.replace('+/-', ' +/-')
        text = text.replace(' - ', ' ')
    try:
        tree = parser.parse(text)
    except Exception as e:
        logger.debugl(2, str(e))
        return {}
    logger.debugl(3, tree.pretty())
    res_o = ComponentTransformer()
    res = res_o.transform(tree)
    logger.debugl(3, res)
    res = res_o.parsed
    if with_extra:
        res.update(res_o.extra)
    return res
