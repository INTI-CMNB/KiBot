# -*- coding: utf-8 -*-
# Copyright (c) 2022-2025 Salvador E. Tropea
# Copyright (c) 2022-2025 Instituto Nacional de Tecnología Industrial
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)
"""
KiCad v5/6 PCB format.
Currently used only for the paper size
"""
import os
from .config import KiConf
from ..error import KiPlotConfigurationError
from ..misc import W_NOLIB, W_MISSFPINFO, EMBED_PREFIX
from ..gs import GS
from .sexpdata import load, dumps, SExpData, sexp_iter, Symbol
from .sexp_helpers import _check_relaxed, _get_symbol_name, make_separated, load_sexp_file, _symbol
from .v6_sch import _check_str, _check_symbol, _check_is_symbol_list, _check_float, _check_integer
from typing import Sequence

PAGE_SIZE = {'A0': (841, 1189),
             'A1': (594, 841),
             'A2': (420, 594),
             'A3': (297, 420),
             'A4': (210, 297),
             'A5': (148, 210),
             'A': (215.9, 279.4),
             'B': (279.4, 431.8),
             'C': (431.8, 558.8),
             'D': (558.8, 863.6),
             'E': (863.6, 1117.6),
             'USLetter': (215.9, 279.4),
             'USLegal': (215.9, 355.6),
             'USLedger': (279.4, 431.8)}
# Footprint replace:
# Attributes that we don't change for KiCad 6/7 (tedit is for KiCad 6)
KICAD6_ATTRS = {'layer', 'tedit', 'tstamp', 'at', 'path', 'fp_text'}
# Same for KiCad 8
KICAD8_ATTRS = {'layer', 'uuid', 'at', 'property'}


class PCBError(Exception):
    pass


class PCB(object):
    def __init__(self):
        super().__init__()
        self.paper = 'A4'
        self.paper_portrait = False
        self.paper_w = self.paper_h = 0
        self.version = 0

    @staticmethod
    def load(file):
        with open(file, 'rt') as fh:
            error = None
            try:
                pcb = load(fh)[0]
            except SExpData as e:
                error = str(e)
            if error:
                raise PCBError(error)
        if not isinstance(pcb, list) or pcb[0].value() != 'kicad_pcb':
            raise PCBError('No kicad_pcb signature')
        o = PCB()
        for e in pcb[1:]:
            e_type = _check_is_symbol_list(e)
            if e_type == 'version':
                o.version = _check_integer(e, 1, e_type)
            elif e_type == 'paper' or e_type == 'page':
                o.paper = _check_str(e, 1, e_type) if e_type == 'paper' else _check_symbol(e, 1, e_type)
                if o.paper == 'User':
                    o.paper_w = _check_float(e, 2, e_type)
                    o.paper_h = _check_float(e, 3, e_type)
                else:
                    if o.paper not in PAGE_SIZE:
                        raise PCBError('Unknown paper size selected {}'.format(o.paper))
                    size = PAGE_SIZE[o.paper]
                    if len(e) > 2 and _check_symbol(e, 2, e_type) == 'portrait':
                        o.paper_portrait = True
                        o.paper_w = size[0]
                        o.paper_h = size[1]
                    else:
                        o.paper_w = size[1]
                        o.paper_h = size[0]
                break
        return o

    def write(self, fname):
        pcb = [Symbol('kicad_pcb')]
        if self.version:
            pcb.append(_symbol('version', [self.version]))
        paper_data = [self.paper]
        if self.paper == 'User':
            paper_data.extend([self.paper_w, self.paper_h])
        elif self.paper_portrait:
            paper_data.append(Symbol('portrait'))
        pcb.append(_symbol('paper', paper_data))
        with open(fname, 'wt') as f:
            f.write(dumps(pcb))
            f.write('\n')


def save_pcb_from_sexp(pcb, logger, replace_pcb=True):
    """ Save a PCB expressed as S-Expressions to disk """
    # Make it readable
    separated = make_separated(pcb[0])
    # Save it to a temporal
    tmp_pcb = GS.tmp_file(content=dumps(separated)+'\n', suffix='.kicad_pcb', indent=True, what='updated PCB', a_logger=logger)
    # Also copy the project
    GS.copy_project(tmp_pcb)
    # Reload it
    logger.debug('- Loading the temporal PCB')
    GS.load_board(tmp_pcb, forced=True)
    os.remove(tmp_pcb)
    # Create a back-up and save it in the original place
    if replace_pcb:
        logger.debug('- Replacing the old PCB')
        GS.save_pcb()
        # After saving the file the name isn't changed, we must force it!!!
    # Keep the original name, not the temporal one
    GS.board.SetFileName(GS.pcb_file)


def keep_attr(names: Sequence[str], sexp):
    return not isinstance(sexp, list) or len(sexp) < 2 or not isinstance(sexp[0], Symbol) or sexp[0].value() in names


def flip_sexp(sexp):
    if not isinstance(sexp, list) or len(sexp) < 2 or not isinstance(sexp[0], Symbol):
        return
    if sexp[0].value().startswith('layer'):  # layer/layers
        for n in range(1, len(sexp)):
            side = sexp[n][0]
            if side in 'BF':
                sexp[n] = ('B' if side == 'F' else 'F') + sexp[n][1:]
    else:
        for s in sexp[1:]:
            flip_sexp(s)


def update_footprint(ref, name: str, s, aliases, logger) -> bool:
    """ Change footprint 'ref' using 'name' lib footprint """
    logger.debug(f'Replacing {ref} using {name}')
    # Get the footprint from the lib
    res = name.split(':')
    if len(res) != 2:
        logger.warning(W_NOLIB+"Component `{ref}` without correct lib name {name}")
        return False
    lib_alias = aliases.get(res[0])
    if lib_alias is None:
        raise KiPlotConfigurationError(f'Unknown library `{res[0]}`')
    fname = os.path.join(lib_alias.uri, res[1]+'.kicad_mod')
    if not os.path.isfile(fname):
        raise KiPlotConfigurationError(f'Missing footprint `{res[1]}` in `{res[0]}` lib')
    logger.debug(f'- Lib file {fname}')
    c = load_sexp_file(fname)
    # Which attributes we want to keep from the original PCB
    attrs = KICAD8_ATTRS if GS.ki8 else KICAD6_ATTRS
    # Keep the attributes like UUID/tstamp, position, properties, etc.
    keep = list(filter(lambda s: keep_attr(attrs, s), s))
    # Get the other attributes from the lib version
    from_lib = list(filter(lambda s: not keep_attr(attrs, s), c[0]))
    # Check if the component is flipped
    try:
        lib_side = next(filter(lambda s: isinstance(s, list) and s[0].value() == "layer", c[0]))[1]
        cur_side = next(filter(lambda s: isinstance(s, list) and s[0].value() == "layer", keep))[1]
        if cur_side != lib_side:
            # Flipped, flip every layer reference
            logger.debug(f'- Flipping {ref}')
            for sexp in from_lib:
                flip_sexp(sexp)
    except StopIteration:
        logger.warning(W_MISSFPINFO+f'Missing footprint layer {ref}')
    # Replace the footprint using the combination
    s[:] = keep+from_lib
    return True


def replace_footprints(fname, replacements, logger, replace_pcb=True):
    pcb = load_sexp_file(fname)
    aliases = KiConf.get_fp_lib_aliases()
    updated = False
    # Look for all modules (KiCad 5/6) and/or footprints (KiCad 7+)
    for iter in [sexp_iter(pcb, 'kicad_pcb/module'), sexp_iter(pcb, 'kicad_pcb/footprint')]:
        for fp in iter:
            # The first value is the name LIB:FP
            fp_name = _check_relaxed(fp, 1, 'footprint name')
            # Look for the reference of this footprint
            for s in fp[2:]:
                # fp_text/property (KiCad 8) named "reference"
                if _get_symbol_name(s) in ('fp_text', 'property') and \
                   _check_relaxed(s, 1, 'property name').lower() == 'reference':
                    # Check if this reference needs update
                    ref = _check_relaxed(s, 2, 'property value')
                    if ref in replacements:
                        new_fp = replacements.get(ref)  # None means just update from lib
                        updated |= update_footprint(ref, new_fp if new_fp else fp_name, fp, aliases, logger)
    # If we replaced one or more footprints
    if updated:
        save_pcb_from_sexp(pcb, logger, replace_pcb)


def get_embedded_file(fname, efile):
    pcb = load_sexp_file(fname)
    name = efile[len(EMBED_PREFIX):]
    for ef in sexp_iter(pcb, 'kicad_pcb/embedded_files/file'):
        for s in ef[1:]:
            i_type = _check_is_symbol_list(s)
            if i_type == 'name':
                iname = _check_str(s, 1, i_type)
            elif i_type == 'type':
                _check_symbol(s, 1, i_type)
            elif i_type == 'checksum':
                checksum = _check_str(s, 1, i_type)
            elif i_type == 'data':
                _check_symbol(s, 1, i_type)
        if name == iname:
            cache_name = GS.get_embed_dir('kicad_embedded_'+checksum+os.path.splitext(name)[1])
            if os.path.isfile(cache_name):
                return cache_name
    raise KiPlotConfigurationError(f'Missing embedded file `{efile}`')
