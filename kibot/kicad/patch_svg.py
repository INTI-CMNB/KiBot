# -*- coding: utf-8 -*-
# Copyright (c) 2022-2023 Salvador E. Tropea
# Copyright (c) 2022-2023 Instituto Nacional de Tecnología Industrial
# License: GPL-3.0
# Project: KiBot (formerly KiPlot)
# Note about the size:
# A4 landscape 841.889764 x 595.275591 pt = 297 x 210 mm
# 1 pt = 4/3*px  1 px = 1"/96 => 1 pt = 4/3 * 1"/96 = 4"/288 = 1"/72 (72 dpi)
# 1" = 25.4 mm => 1 pt = 25.4/72 mm = 0.3527777778 mm
import re
from .. import log

logger = log.get_logger()
SVG_VIEW_BOX_REGEX = r'<svg (.*) width="(.*)" height="(.*)" viewBox="(\S+) (\S+) (\S+) (\S+)"'
SVG_VIEW_BOX_SUB_FIX = r'<svg \1 width="\3" height="\2" viewBox="\4 \5 \7 \6"'
SVG_VIEW_BOX_REGEX2 = r'width="(.*)" height="(.*)" viewBox="(\S+) (\S+) (\S+) (\S+)"'
SVG_VIEW_BOX_SUB_PAT = r'width="{}cm" height="{}cm" viewBox="{} {} {} {}"'


def patch_svg_file(file, remove_bkg=False, is_portrait: bool = False):
    """ KiCad always prints in portrait """
    if is_portrait and not remove_bkg:
        # Nothing to do
        return
    logger.debug('Patching SVG file `{}`'.format(file))
    with open(file, 'rt') as f:
        text = f.read()
    if not is_portrait:
        text = re.sub(SVG_VIEW_BOX_REGEX, SVG_VIEW_BOX_SUB_FIX, text)
    if remove_bkg:
        text = re.sub(r'<rect.*>', '', text)
    elif not is_portrait:
        text = re.sub(r'<rect x="(\S+)" y="(\S+)" width="(\S+)" height="(\S+)"',
                      r'<rect x="\1" y="\2" width="\4" height="\3"', text)
    with open(file, 'wt') as f:
        f.write(text)


def change_svg_viewbox(file, view_box, w, h):
    with open(file, 'rt') as f:
        text = f.read()
    text = re.sub(SVG_VIEW_BOX_REGEX2, SVG_VIEW_BOX_SUB_PAT.format(w, h, view_box[0], view_box[1], view_box[2], view_box[3]),
                  text)
    with open(file, 'wt') as f:
        f.write(text)
