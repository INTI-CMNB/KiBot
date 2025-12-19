# -*- coding: utf-8 -*-
# Copyright (c) 2024 Salvador E. Tropea
# Copyright (c) 2024 Instituto Nacional de Tecnologïa Industrial
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)
#
# Data type analyzer and rules enforcer
import json
import math
from os import path as op
import re
from .data_types import get_data_type_tree, create_new_optionable
from ..error import KiPlotConfigurationError
from ..gs import GS
from ..kiplot import config_output
from .. import log
from ..misc import INTERNAL_ERROR
from ..pre_base import BasePreFlight
from ..registrable import RegOutput, RegFilter, RegVariant
logger = log.get_logger()


class DTTStat(object):
    def __init__(self, name):
        self.name = name
        self.params = 0
        self.depth = 0
        self.n_types = []
        self.types = []
        self.names = []
        self.paths = []

    def add_param(self, de, level, name):
        self.params += 1
        self.depth = max(self.depth, level+1)
        self.n_types.append(len(de.valids))
        self.types.append(de.valids)
        self.names.append(name)
        for tp in de.valids:
            self.paths.append(name+'.'+tp.kind)


class DTTStats(object):
    def __init__(self):
        self.stats = []
        self.total_depth = self.total_params = 0
        self.max_depth = self.max_params = 0
        self.min_depth = self.min_params = 1e6
        self.n = 0
        self.single_type = self.multi_type = 0
        self.dts = {}
        self.dts_s = {}
        self.dts_m = {}

    def add(self, stat):
        self.stats.append(stat)
        self.n += 1
        self.total_params += stat.params
        self.total_depth += stat.depth
        self.max_params = max(self.max_params, stat.params)
        self.min_params = min(self.min_params, stat.params)
        self.max_depth = max(self.max_depth, stat.depth)
        self.min_depth = min(self.min_depth, stat.depth)
        for p in stat.n_types:
            if p > 1:
                self.multi_type += 1
            else:
                self.single_type += 1
        for ts, n in zip(stat.types, stat.names):
            cls_s = []
            for t in ts:
                cls = re.search(r"DataType([^']+)", str(t.__class__)).group(1)
                cls_s.append(cls)
                self.dts[cls] = self.dts.get(cls, 0)+1
            cls = ','.join(sorted(cls_s))
            if len(ts) > 1:
                # self.dts_m[cls] = self.dts_m.get(cls, 0)+1
                self.dts_m.setdefault(cls, []).append(n)
            else:
                # self.dts_s[cls] = self.dts_s.get(cls, 0)+1
                self.dts_s.setdefault(cls, []).append(n)

    def analyze(self):
        self.avg_params = round(self.total_params/self.n)
        self.hist_params = [0]*math.ceil(self.max_params/10)
        for st in self.stats:
            cell = int(st.params/10)
            self.hist_params[cell] += 1
        self.avg_depth = self.total_depth/self.n
        self.hist_depth = [0]*(self.max_depth+1)
        for st in self.stats:
            self.hist_depth[st.depth] += 1


def analyze_data_type_tree(tree, stats, pref='', level=0, parent=None):
    entries = []
    for de in tree:
        # logger.error(f'  {"  "*level}- {de.name}')
        name = pref+de.name
        stats.add_param(de, level, name)
        entries.append([de.name, [d.__class__.__name__ for d in de.valids], None])
        if de.def_val == '{}':
            logger.error(f'{name}')
        if de.cls is not None:
            # Check the dict can be represented as a string in the list
            if de.is_list_dict and 'slot' in str(de.cls.__str__):
                GS.exit_with_error(f'{de.cls} without defined __str__ ({name})', INTERNAL_ERROR)
            # Check we can create an empty entry (for "add")
            try:
                # PcbDraw needs _parent._parent.units ... all the chain must be configured
                if not de.obj._configured:
                    de.obj.config(parent)
            except KiPlotConfigurationError:
                pass
            try:
                obj = create_new_optionable(de.cls, de.obj)
            except KiPlotConfigurationError as e:
                GS.exit_with_error(f"{de.cls} can't be created empty ({name}) [{e}]", INTERNAL_ERROR)
            if de.def_val is None and de.ori_def_val is None and obj.get_default() is None:
                GS.exit_with_error(f'No default for {name} `{de.def_val}` ({de.valids})', INTERNAL_ERROR)
            # Go deeper
            if de.is_dict or de.is_list_dict:
                entries[-1][2] = analyze_data_type_tree(de.sub, stats, name+'.', level+1, de.obj)
    return entries


def report(all, kind):
    all.analyze()
    kind_c = kind.capitalize()
    logger.info(f'{all.n} {kind} types with a total of {all.total_params} different parameters')
    logger.info(f'Single type parameters: {all.single_type} ({round(all.single_type/all.total_params*100)} %)')
    logger.info(f'Multi type parameters: {all.multi_type} ({round(all.multi_type/all.total_params*100)} %)')

    logger.info(f'Average parameters: {all.avg_params}')
    logger.info(f'Maximum number of parameters: {all.max_params}')
    logger.info(f'Minimum number of parameters: {all.min_params}')
    logger.info('Histogram:')
    for n, p in enumerate(all.hist_params):
        logger.info(f'{n*10:3d}-{(n+1)*10-1:3d}: {"*"*p}')
    logger.info(f'{kind_c} sorted by parameters:')
    for st in sorted(all.stats, key=lambda x: x.params):
        logger.info(f'- {st.name}: {st.params}')

    logger.info(f'Average depth: {all.avg_depth}')
    logger.info(f'Maximum depth: {all.max_depth}')
    logger.info(f'Minimum depth: {all.min_depth}')
    logger.info('Histogram:')
    for n, p in enumerate(all.hist_depth):
        logger.info(f'{n}: {"*"*p}')
    logger.info(f'{kind_c} sorted by depth:')
    for st in sorted(all.stats, key=lambda x: x.depth):
        logger.info(f'- {st.name}: {st.depth}')

    logger.info('-'*80)
    logger.info(f'{len(all.dts)} different data types')
    for k, v in sorted(all.dts.items(), key=lambda x: x[1], reverse=True):
        logger.info(f'- {k:>18}: {v:4d}')

    logger.info('-'*80)
    logger.info('Used as single data type:')
    for k, v in sorted(all.dts_s.items(), key=lambda x: len(x[1]), reverse=True):
        logger.info(f'- {k:>18}: {len(v):4d} {"" if len(v) > 10 else v}')

    logger.info('-'*80)
    logger.info(f'{len(all.dts_m)} different data type combinations')
    for k, v in sorted(all.dts_m.items(), key=lambda x: len(x[1]), reverse=True):
        logger.info(f'- {k:>26}: {len(v):4d} {"" if len(v) > 10 else v}')


def scan_items(category, iterable, accum, totals, config):
    entries = {}
    for name, cls in iterable.items():
        obj = cls()
        obj.type = name
        config(obj)
        dtt = get_data_type_tree(cls(), obj)
        stats = DTTStat(name)
        entries[name] = analyze_data_type_tree(dtt, stats, name+'.')
        accum.add(stats)
        totals.add(stats)
    report(accum, category)
    if GS.out_dir_in_cmd_line:
        with open(op.join(GS.out_dir, category), 'w') as f:
            f.write(json.dumps(entries, sort_keys=True, indent=2))


CATS = (('outputs', RegOutput.get_registered, True),
        ('preflights', BasePreFlight.get_registered, False),
        ('filters', RegFilter.get_registered, False),
        ('variants', RegVariant.get_registered, False))


def analyze():
    # Check that we have some global options
    if GS.globals_tree is None:
        # Nope, we didn't load a config, so go for defaults
        glb = GS.set_global_options_tree({})
        glb.config(None)
    totals = DTTStats()
    for c in CATS:
        stats = DTTStats()
        scan_items(c[0], c[1](), stats, totals, config_output if c[2] else lambda x: x)
        logger.info('='*80)
        logger.info('='*80)
    report(totals, 'totals')
