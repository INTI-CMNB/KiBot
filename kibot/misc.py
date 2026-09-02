# -*- coding: utf-8 -*-
# Copyright (c) 2020-2026 Salvador E. Tropea
# Copyright (c) 2020-2026 Instituto Nacional de Tecnología Industrial
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)
""" Miscellaneous definitions """

import collections
from contextlib import contextmanager
import hashlib
import os
import re
from struct import unpack


# Error levels
DONT_STOP = -1        # Keep going
INTERNAL_ERROR = 1    # Unhandled exceptions
WRONG_ARGUMENTS = 2   # This is what argsparse uses
UNSUPPORTED_OPTION = 3
MISSING_TOOL = 4
DRC_ERROR = 5
EXIT_BAD_ARGS = 6
EXIT_BAD_CONFIG = 7
NO_PCB_FILE = 8
NO_SCH_FILE = 9
ERC_ERROR = 10
BOM_ERROR = 11
PDF_SCH_PRINT = 12
PDF_PCB_PRINT = 13
PLOT_ERROR = 14
NO_YAML_MODULE = 15
NO_PCBNEW_MODULE = 16
CORRUPTED_PCB = 17
KICAD2STEP_ERR = 18
WONT_OVERWRITE = 19
PCBDRAW_ERR = 20
SVG_SCH_PRINT = 21
CORRUPTED_SCH = 22
WRONG_INSTALL = 23
RENDER_3D_ERR = 24
FAILED_EXECUTE = 25
KICOST_ERROR = 26
MISSING_WKS = 27
MISSING_FILES = 28
DIFF_TOO_BIG = 29
NETLIST_DIFF = 30
PS_SCH_PRINT = 31
DXF_SCH_PRINT = 32
HPGL_SCH_PRINT = 33
CORRUPTED_PRO = 34
BLENDER_ERROR = 35
WARN_AS_ERROR = 36
CHECK_FIELD = 37
IGNORED_ERRORS = 38
GOT_WARNINGS = 39   # Not treated as errors, but using `--fail-on-warnings`
KIPY_ERROR = 40
error_level_to_name = ['NONE',
                       'INTERNAL_ERROR',
                       'WRONG_ARGUMENTS',
                       'UNSUPPORTED_OPTION',
                       'MISSING_TOOL',
                       'DRC_ERROR',
                       'EXIT_BAD_ARGS',
                       'EXIT_BAD_CONFIG',
                       'NO_PCB_FILE',
                       'NO_SCH_FILE',
                       'ERC_ERROR',
                       'BOM_ERROR',
                       'PDF_SCH_PRINT',
                       'PDF_PCB_PRINT',
                       'PLOT_ERROR',
                       'NO_YAML_MODULE',
                       'NO_PCBNEW_MODULE',
                       'CORRUPTED_PCB',
                       'KICAD2STEP_ERR',
                       'WONT_OVERWRITE',
                       'PCBDRAW_ERR',
                       'SVG_SCH_PRINT',
                       'CORRUPTED_SCH',
                       'WRONG_INSTALL',
                       'RENDER_3D_ERR',
                       'FAILED_EXECUTE',
                       'KICOST_ERROR',
                       'MISSING_WKS',
                       'MISSING_FILES',
                       'DIFF_TOO_BIG',
                       'NETLIST_DIFF',
                       'PS_SCH_PRINT',
                       'DXF_SCH_PRINT',
                       'HPGL_SCH_PRINT',
                       'CORRUPTED_PRO',
                       'BLENDER_ERROR',
                       'WARN_AS_ERROR',
                       'CHECK_FIELD',
                       'IGNORED_ERRORS',
                       'GOT_WARNINGS',
                       'KIPY_ERROR'
                       ]
KICOST_SUBMODULE = '../submodules/KiCost/src/kicost'
EXAMPLE_CFG = 'example_template.kibot.yaml'
BASE_HELP = 'https://kibot.readthedocs.io/en/latest/'
BASE_HELP_CFG = BASE_HELP+'configuration/'
AUTO_SCALE = 0
KICAD_VERSION_5_99 = 50990000
KICAD_VERSION_6_0_0 = 60000000
KICAD_VERSION_6_0_2 = 60000020
KICAD_VERSION_7_0_1 = 70000010
KICAD_VERSION_7_0_1_1 = 70000011
KICAD_VERSION_9_0_1 = 90000010
KICAD_VERSION_9_0_5 = 90000050
KICAD_VERSION_9_0_9 = 90000090
KICAD_VERSION_10_0_3 = 100000030
KICAD_VERSION_10_0_5 = 100000050
MIN_KICAD_VERSION = '6.0.11'
TRY_INSTALL_CHECK = 'Try running the installation checker: kibot-check'
EMBED_PREFIX = 'kicad-embed://'

# Internal filter names
IFILT_MECHANICAL = '_mechanical'
IFILT_KICOST_RENAME = '_kicost_rename'
IFILT_KICOST_DNP = '_kicost_dnp'
# KiCad 5 GUI values for the attribute
UI_THT = 0       # 1 for KiCad 6
UI_SMD = 1       # 2 for KiCad 6
UI_VIRTUAL = 2   # 12 for KiCad 6
# KiCad 6 module attributes from class_module.h
MOD_THROUGH_HOLE = 1
MOD_SMD = 2
MOD_EXCLUDE_FROM_POS_FILES = 4
MOD_EXCLUDE_FROM_BOM = 8
MOD_BOARD_ONLY = 16  # Footprint has no corresponding symbol
MOD_JUST_ADDED = 32  # The footprint was added by the netlist update
MOD_ALLOW_SOLDERMASK_BRIDGES = 64
MOD_ALLOW_MISSING_COURTYARD = 128
# This is what a virtual component gets when loaded by KiCad 6
MOD_VIRTUAL = MOD_EXCLUDE_FROM_POS_FILES | MOD_EXCLUDE_FROM_BOM

# Supported values for "do not fit"
DNF = {
    "dnf",
    "dnl",
    "dnp",
    "do not fit",
    "do not place",
    "do not load",
    "nofit",
    "nostuff",
    "noplace",
    "noload",
    "not fitted",
    "not loaded",
    "not placed",
    "no stuff",
}
# String matches for marking a component as "do not change" or "fixed"
DNC = {
    "dnc",
    "do not change",
    "no change",
    "fixed",
}
# KiCost distributors
DISTRIBUTORS = ['arrow', 'digikey', 'farnell', 'lcsc', 'mouser', 'newark', 'rs', 'tme']
DISTRIBUTORS_F = [d+'#' for d in DISTRIBUTORS]
DISTRIBUTORS_STUBS = ['part#', '#', 'p#', 'pn', 'vendor#', 'vp#', 'vpn', 'num']
DISTRIBUTORS_STUBS_SEPS = '_- '
# ISO ISO4217 currency codes
# Not all, but the ones we get from the European Central Bank (march 2021)
ISO_CURRENCIES = {'EUR', 'USD', 'JPY', 'BGN', 'CZK', 'DKK', 'GBP', 'HUF', 'PLN', 'RON', 'SEK', 'CHF', 'ISK', 'NOK', 'HRK',
                  'RUB', 'TRY', 'AUD', 'BRL', 'CAD', 'CNY', 'HKD', 'IDR', 'ILS', 'INR', 'KRW', 'MXN', 'MYR', 'NZD', 'PHP',
                  'SGD', 'THB', 'ZAR'}

W_SILLY = '*'
W_VARCFG = '(W001) '
W_VARPCB = '(W002) '
W_PYCACHE = '(W003) '
W_FIELDCONF = '(W004) '
W_NOHOME = '(W005) '
W_NOUSER = '(W006) '
W_BADSYS = '(W007) '
W_NOCONFIG = '(W008) '
W_NOKIENV = '(W009) '
W_NOLIBS = '(W010) '
W_NODEFSYMLIB = '(W011) '
W_UNKGLOBAL = '(W012) '
W_PCBNOSCH = '(W013) '
W_NONEEDSKIP = '(W014) '
W_UNKOPS = '(W015) '
W_AMBLIST = '(W016) '
W_UNRETOOL = '(W017) '
W_USESVG2 = '(W018) '
W_USEIMAGICK = '(W019) '
W_BADVAL1 = '(W020) '
W_BADVAL2 = '(W021) '
W_BADVAL3 = '(W022) '
W_BADPOLI = '(W023) '
W_POLICOORDS = '(W024) '
W_BADSQUARE = '(W025) '
W_BADCIRCLE = '(W026) '
W_BADARC = '(W027) '
W_BADTEXT = '(W028) '
W_BADPIN = '(W029) '
W_BADCOMP = '(W030) '
W_BADDRAW = '(W031) '
W_UNKDCM = '(W032) '
W_UNKAR = '(W033) '
W_ARNOPATH = '(W034) '
W_ARNOREF = '(W035) '
W_MISCFLD = '(W036) '
W_EXTRASPC = '(W037) '
W_NOLIB = '(W038) '
W_INCPOS = '(W039) '
W_NOANNO = '(W040) '
W_MISSLIB = '(W041) '
W_MISSDCM = '(W042) '
W_MISSCMP = '(W043) '
W_VARSCH = '(W044) '
W_WRONGPASTE = '(W045) '
W_MISFLDNAME = '(W046) '
W_MISS3D = '(W047) '
W_FAILDL = '(W048) '
W_NOLAYER = '(W049) '
W_EMPTYZIP = '(W050) '
W_WRONGCHAR = '(W051) '
W_NOKIVER = '(W052) '
W_EXTNAME = '(W053) '
W_TIMEOUT = '(W054) '
W_MUSTBEINT = '(W055) '
W_NOOUTPUTS = '(W056) '
W_NOTASCII = '(W057) '
W_KIAUTO = '(W058) '
W_NUMSUBPARTS = '(W059) '
W_PARTMULT = '(W060) '
W_EMPTYREN = '(W061) '
W_BADFIELD = '(W062) '
W_UNKDIST = '(W063) '
W_UNKCUR = '(W064) '
W_NONETLIST = '(W065) '
W_NOKICOST = '(W066) '
W_UNKOUT = '(W067) '
W_NOFILTERS = '(W068) '
W_NOVARIANTS = '(W069) '
W_NOENDLIB = '(W070) '
W_NEEDSPCB = '(W071) '
W_NOGLOBALS = '(W072) '
W_EMPTREP = '(W073) '
W_BADCHARS = '(W074) '
W_DATEFORMAT = '(W075) '
W_UNKFLD = '(W076) '
W_ALRDOWN = '(W077) '
W_KICOSTFLD = '(W078) '
W_MIXVARIANT = '(W079) '
W_NOTPDF = '(W080) '
W_NOREF = '(W081) '
W_UNKVAR = '(W082) '
W_WRONGEXT = '(W083) '
W_COLORTHEME = '(W084) '
W_WRONGCOLOR = '(W085) '
W_WKSVERSION = '(W086) '
W_WRONGOAR = '(W087) '
W_ECCLASST = '(W088) '
W_PDMASKFAIL = '(W089) '
W_MISSTOOL = '(W090) '
W_NOTYET = '(W091) '
W_NOMATCH = '(W092) '
W_DOWNTOOL = '(W093) '
W_NOPREFLIGHTS = '(W094) '
W_NOPART = '(W095) '
W_MAXDEPTH = '(W096) '
W_3DRESVER = '(W097) '
W_DOWN3D = '(W098) '
W_MISSREF = '(W099) '
W_COPYOVER = '(W100) '
W_PARITY = '(W101) '
W_MISSFPINFO = '(W102) '
W_PCBDRAW = '(W103) '
W_NOCRTYD = '(W104) '
W_PANELEMPTY = '(W105) '
W_ONWIN = '(W106) '
W_AUTONONE = '(W106) '
W_AUTOPROB = '(W107) '
W_MORERES = '(W108) '
W_NOGROUPS = '(W109) '
W_UNKPCB3DTXT = '(W110) '
W_NOPCB3DBR = '(W111) '
W_NOPCB3DTL = '(W112) '
W_BADPCB3DTXT = '(W113) '
W_UNKPCB3DNAME = '(W114) '
W_BADPCB3DSTK = '(W115) '
W_EEDA3D = '(W116) '
W_MICROVIAS = '(W117) '
W_BLINDVIAS = '(W118) '
W_LIBTVERSION = '(W119) '
W_LIBTUNK = '(W120) '
W_DRC7BUG = '(W121) '
W_BADTOL = '(W122) '
W_BADRES = '(W123) '
W_RESVALISSUE = '(W124) '
W_RES3DNAME = '(W125) '
W_ESCINV = '(W126) '
W_BADVAL4 = '(W127) '
W_ENVEXIST = '(W128) '
W_FLDCOLLISION = '(W129) '
W_NEWGROUP = '(W130) '
W_NOTINBOM = '(W131) '
W_MISSDIR = '(W132) '
W_EXTRAINVAL = '(W133) '
W_BADANGLE = '(W134) '
W_VALMISMATCH = '(W135) '
W_BADOFFSET = '(W136) '
W_BUG16418 = '(W137) '
W_NOTHCMP = '(W138) '
W_KEEPTMP = '(W139) '
W_EXTRADOCS = '(W140) '
W_ERCJSON = '(W141) '
W_ERC = '(W142) '
W_DEPR = '(W143) '
W_FILXRC = '(W144) '
W_DRC = '(W145) '
W_DRCJSON = '(W146) '
W_BADREF = '(W147) '
W_MISLIBTAB = '(W148) '
W_UPSTKUPTOO = '(W149) '
W_INV3DLAYER = '(W150) '
W_NEEDSK8 = '(W151) '
W_NEEDSK7 = '(W152) '
W_NEEDSK6 = '(W153) '
W_UNKPADSH = '(W154) '
W_NOFILES = '(W155) '
W_NODESC = '(W156) '
W_NOPAGES = '(W157) '
W_NOLAYERS = '(W158) '
W_NOPOPMD = '(W159) '
W_NOQR = '(W160) '
W_NOFOOTP = '(W161) '
W_CHKFLD = '(W162) '
W_ONMAC = '(W163) '
W_MULTIREF = '(W164) '
W_NOTHREPE = '(W165) '
W_LANGNOTA = '(W166) '
W_NOVIAS = '(W167) '
W_NOMATCHGRP = '(W168) '
W_NOBOMOPS = '(W169) '
W_NODRILL = '(W170) '
W_NOPCBTB = '(W171) '
W_DEFNOSTR = '(W172) '
W_CONVPDF = '(W173) '
W_MISSWRL = '(W174) '
W_STACKUP = '(W175) '
W_NOVISLA = '(W176) '
W_IBOMNOCHK = '(W177) '
W_PREREDEF = '(W178) '
W_BURIEDVIAS = '(W179) '
W_BADGITREPO = '(W180) '
W_NOUUIDMAP = '(W181) '
W_UUIDSCHISSUE = '(W182) '
W_SCHNOTIMP = '(W183) '
W_NOUTF8 = '(W184) '
W_POSGRID = '(W185) '
W_PAGENOINT = '(W186) '
W_PAGEDUP = '(W187) '
W_PAGEMIS = '(W188) '
W_EXTRAGEN = '(W189) '
W_NONUMBER = '(W190) '
W_REPREF = '(W191) '
W_GRBJOB = '(W192) '
# Somehow arbitrary, the colors are real, but can be different
PCB_MAT_COLORS = {'fr1': "937042", 'fr2': "949d70", 'fr3': "adacb4", 'fr4': "332B16", 'fr5': "6cc290"}
PCB_FINISH_COLORS = {'hal': "8b898c", 'hasl': "8b898c", 'imag': "8b898c", 'enig': "cfb96e", 'enepig': "cfb96e",
                     'none': "d39751", 'hal snpb': "8b898c", 'hal lead-free': "8b898c", 'hard gold': "cfb96e",
                     'immersion silver': "8b898c", 'immersion ag': "8b898c", 'imau': "cfb96e", 'immersion gold': "cfb96e",
                     'immersion au': "cfb96e", 'immersion tin': "8b898c", 'immersion nickel': "cfb96e", 'osp': "d39751",
                     'ht_osp': "d39751"}
SOLDER_COLORS = {'green': ("#285e3a", "#208b47"),
                 'black': ("#1d1918", "#2d2522"),
                 'blue': ("#1b1f44", "#00406a"),
                 'red': ("#812e2a", "#be352b"),
                 'white': ("#bdccc7", "#b7b7ad"),
                 'yellow': ("#73823d", "#f2a756"),
                 'purple': ("#30234a", "#451d70")}
SILK_COLORS = {'black': "0b1013", 'white': "d5dce4"}
G_SILKCOLORS = {
    '': '#f5f5f5ff',  # white
    'white': '#f5f5f5ff',
    'green': '#143324ff',
    'red': '#b51315ff',
    'blue': '#023ba2ff',
    'black': '#0b0b0bff',
    'purple': '#200235ff',
    'yellow': '#c2c300ff',
}
G_MASKCOLORS = {
    '': '#143324d4',  # green
    'green': '#143324d4',
    'light green': '#5ba80cd4',
    'saturated green': '#0d680bd4',
    'red': '#851315d4',         # Adjusted from #b5 13 15 d4
    'light red': '#d2280ed4',
    'red/orange': '#ef3529d4',
    'blue': '#02223bd4',        # Adjusted from 2,  59, 162,
    'light blue 1': '#364f74d4',
    'light blue 2': '#3d5582d4',
    'green/blue': '#154650d4',
    'black': '#0b0b0bd4',
    'white': '#f5f5f5d4',
    'purple': '#200235d4',
    'light purple': '#771f5bd4',
    'yellow': '#c2c300d4',
}
G_PASTECOLORS = {
    'grey': '#808080ff',
    'dark grey': '#5a5a5aff',
    'silver': '#d5d5d5ff',
}
FINISH_TO_COLOR = {'hal': "silver", 'hasl': "silver", 'imag': "silver", 'hal snpb': "silver", 'hal lead-free': "silver",
                   'immersion silver': "silver", 'immersion ag': "silver",
                   'enig': "gold", 'enepig': "gold", 'hard gold': "gold", 'imau': "gold", 'immersion gold': "gold",
                   'immersion au': "gold", 'immersion nickel': "gold",
                   'none': "copper", 'osp': "copper", 'ht_osp': "copper",
                   'immersion tin': "tin"}
G_FINISHCOLORS = {
    'copper': '#b87332ff',
    'gold': '#b29c00ff',
    'silver': '#d5d5d5ff',
    'tin': '#a0a0a0ff',
}
G_BOARDCOLORS = {
    'fr4 natural, dark': '#332b16d4',
    'fr4 natural': '#6d744bd4',
    'ptfe natural': '#fcfcfae6',
    'polyimide': '#cd8200ad',
    'phenolic natural': '#5c1106e6',
    'brown 1': '#92632fd4',
    'brown 2': '#a07b36d4',
    'brown 3': '#92632fd4',
    'aluminum': '#d5d5d5ff',
}

# Some browser name to pretend, popular at the moment
# https://techblog.willshouse.com/2012/01/03/most-common-user-agents/ on 2024-10-22
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36'
# Old value, caused problems with Zscaler
# USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:102.0) Gecko/20100101 Firefox/102.0'
# Text used to disable 3D models
DISABLE_3D_MODEL_TEXT = '_Disabled_by_KiBot'
RENDERERS = ['pcbdraw', 'render_3d', 'blender_export']
PCB_GENERATORS = ['pcb_variant', 'panelize']
KIKIT_UNIT_ALIASES = {'millimeters': 'mm', 'inches': 'inch', 'mils': 'mil'}
UNITS_2_KICAD = {'millimeters': 'mm', 'inches': 'in', 'mils': 'mils', 'meters': 'm', 'deciinches': 'tenths'}
FONT_HELP_TEXT = ('\n        Important: If you use custom fonts and/or colors please consult the `resources_dir` '
                  'global variable.')
MULTI_SCH_NAME = ('\nNote that only for KiCad 10 and newer the `output` option controls the names of all sub-sheets.'
                  '\nIn this case %f and %F contains the project and the sub-sheet path inside the hierarchy')
SUBIMAGE_REGEX = r'_([^\[]+)(?:\[(\d+)\])?'
# CSS style for HTML tables used by BoM and E/DRC
# Light colors
BG_GEN = "#DCF5E4"
BG_KICAD = "#F5DCA9"
BG_USER = "#DCEFF5"
BG_EMPTY = "#F57676"
BG_GEN_L = "#E6FFEE"
BG_KICAD_L = "#FFE6B3"
BG_USER_L = "#E6F9FF"
BG_EMPTY_L = "#FF8080"
HEAD_COLOR_R = "#982020"
HEAD_COLOR_R_L = "#c85050"
HEAD_COLOR_G = "#009879"
HEAD_COLOR_G_L = "#30c8a9"
HEAD_COLOR_B = "#0e4e8e"
HEAD_COLOR_B_L = "#3e7ebe"

# Dark adaptations (by Gemini)
# They maintain a WCAG-compliant contrast ratio of at least 4.5:1 against white text.
BG_GEN_D = "#14532d"
BG_KICAD_D = "#78350f"
BG_USER_D = "#164e63"
BG_EMPTY_D = "#7f1d1d"
BG_GEN_L_D = "#166534"
BG_KICAD_L_D = "#92400e"
BG_USER_L_D = "#0891b2"
BG_EMPTY_L_D = "#991b1b"
HEAD_COLOR_R_D = "#5c1414"    # Deep Burgundy Red
HEAD_COLOR_R_L_D = "#7a1c1c"  # Muted Red (Hover)
HEAD_COLOR_G_D = "#004d3d"    # Deep Forest Teal
HEAD_COLOR_G_L_D = "#006652"  # Muted Teal (Hover)
HEAD_COLOR_B_D = "#09335e"    # Deep Navy Blue
HEAD_COLOR_B_L_D = "#114b8a"  # Muted Blue (Hover)

STYLE_COMMON = ("  /* Light colors */\n"
                "  :root {\n"
                "    --bg-color: #ffffff;\n"
                "    --text-color: #222222;\n"
                "    --link-color: #0e4e8e;\n"
                "\n"
                "    /* Tables */\n"
                "    --table-header-bg: @bg@; /* Theme style defined */\n"
                "    --table-header-text: #ffffff;\n"
                "    --table-row-even: #f3f3f3;\n"
                "    --table-row-hover: @bgl@; /* Theme style defined */\n"
                "    --table-border: #dddddd;\n"
                "    --table-shadow: rgba(0, 0, 0, 0.15);\n"
                "    --table-cl-border: black;\n"
                "\n"
                "    /* Status Colors */\n"
                "    --td-empty0: "+BG_EMPTY+";\n"
                "    --td-gen0: "+BG_GEN+";\n"
                "    --td-kicad0: "+BG_KICAD+";\n"
                "    --td-user0: "+BG_USER+";\n"
                "    --td-empty1: "+BG_EMPTY_L+";\n"
                "    --td-gen1: "+BG_GEN_L+";\n"
                "    --td-kicad1: "+BG_KICAD_L+";\n"
                "    --td-user1: "+BG_USER_L+";\n"
                "    --td-error: #db1218;\n"
                "    --td-warning: #f2e30c;\n"
                "    --td-excluded: #C0C0C0;\n"
                "    --checkmark: green;\n"
                "\n"
                "    /* Toggle Button */\n"
                "    --btn-bg: #ffffff;\n"
                "    --btn-border: #e2e8f0;\n"
                "    --btn-hover: #f1f5f9;\n"
                "  }\n"
                "\n"
                "  /* Dark colors */\n"
                '  [data-theme="dark"] {\n'
                "    --bg-color: #121212;\n"
                "    --text-color: #e2e8f0;\n"
                "    --link-color: #38bdf8;\n"
                "\n"
                "    /* Tables */\n"
                "    --table-header-bg: @bg_d@; /* Theme style defined */\n"
                "    --table-header-text: #f8fafc;\n"
                "    --table-row-even: #1e1e1e;\n"
                "    --table-row-hover: @bgl_d@; /* Theme style defined */\n"
                "    --table-border: #333333;\n"
                "    --table-shadow: rgba(0, 0, 0, 0.5);\n"
                "    --table-cl-border: #dddddd;\n"
                "\n"
                "    /* Status Colors (Darker adaptations) */\n"
                "    --td-empty0: "+BG_EMPTY_D+";\n"
                "    --td-gen0: "+BG_GEN_D+";\n"
                "    --td-kicad0: "+BG_KICAD_D+";\n"
                "    --td-user0: "+BG_USER_D+";\n"
                "    --td-empty1: "+BG_EMPTY_L_D+";\n"
                "    --td-gen1: "+BG_GEN_L_D+";\n"
                "    --td-kicad1: "+BG_KICAD_L_D+";\n"
                "    --td-user1: "+BG_USER_L_D+";\n"
                "    --td-error: #ef4444;\n"
                "    --td-warning: #ca8a04;\n"
                "    --td-excluded: #64748b;\n"
                "    --checkmark: #4ade80;\n"
                "\n"
                "    /* Toggle Button */\n"
                "    --btn-bg: #1e293b;\n"
                "    --btn-border: #334155;\n"
                "    --btn-hover: #475569;\n"
                "  }\n"
                "\n"
                "  body {\n"
                "    background-color: var(--bg-color);\n"
                "    color: var(--text-color);\n"
                "    font-family: sans-serif;\n"
                "    transition: background-color 0.3s, color 0.3s;\n"
                "  }\n"
                "\n"
                "  a {\n"
                "    color: var(--link-color);\n"
                "  }\n"
                "\n"
                "  /* Theme Toggle Button */\n"
                "  .theme-toggle {\n"
                "    position: absolute;\n"
                "    top: 15px;\n"
                "    right: 15px;\n"
                "    background: var(--btn-bg);\n"
                "    border: 1px solid var(--btn-border);\n"
                "    color: var(--text-color);\n"
                "    border-radius: 6px;\n"
                "    padding: 8px;\n"
                "    cursor: pointer;\n"
                "    display: flex;\n"
                "    align-items: center;\n"
                "    justify-content: center;\n"
                "    box-shadow: 0 2px 5px var(--table-shadow);\n"
                "    transition: background 0.2s, color 0.2s, border-color 0.2s;\n"
                "  }\n"
                "  .theme-toggle:hover {\n"
                "    background: var(--btn-hover);\n"
                "  }\n"
                "  .theme-toggle svg {\n"
                "    width: 20px;\n"
                "    height: 20px;\n"
                "    display: none; /* Handled by JS */\n"
                "  }\n"
                "\n"
                "  .cell-title { vertical-align: bottom; }\n"
                "  .cell-info { vertical-align: top; padding: 1em;}\n"
                "  .cell-extra-info { vertical-align: top; padding: 1em;}\n"
                "  .cell-stats { vertical-align: top; padding: 1em;}\n"
                "  .title h1 { font-size:2.5em; font-weight: bold; padding: 0px; margin: 0px; }\n"
                "  .h1 { font-size:1.5em; font-weight: bold; }\n"
                "  .subtitle { font-size:1.5em; font-weight: bold; }\n"
                "  .h2 { font-size:1.5em; font-weight: bold; }\n"
                "\n"
                "  .td-empty0 { text-align: center; background-color: var(--td-empty0); }\n"
                "  .td-gen0 { text-align: center; background-color: var(--td-gen0); }\n"
                "  .td-kicad0 { text-align: center; background-color: var(--td-kicad0); }\n"
                "  .td-user0 { text-align: center; background-color: var(--td-user0); }\n"
                "  .td-empty1 { text-align: center; background-color: var(--td-empty1); }\n"
                "  .td-gen1 { text-align: center; background-color: var(--td-gen1); }\n"
                "  .td-kicad1 { text-align: center; background-color: var(--td-kicad1); }\n"
                "  .td-user1 { text-align: center; background-color: var(--td-user1); }\n"
                "  .td-nocolor { text-align: center; }\n"
                "\n"
                "  .color-ref { margin: 25px 0; }\n"
                "  .color-ref th { text-align: left }\n"
                "  .color-ref td { padding: 5px 20px; }\n"
                "  .head-table { margin-bottom: 2em; }\n"
                # Style the centered checkmark
                "  .centered-checkmark { font-size: 30vw; text-align: center; color: var(--checkmark); }\n"
                # Table sorting cursor. 60% transparent when disabled. Solid white when enabled.
                "  /* Sort Header */\n"
                "  .tg-sort-header::-moz-selection{background:0 0}\n"
                "  .tg-sort-header::selection{background:0 0}.tg-sort-header{cursor:pointer}\n"
                "  .tg-sort-header:after{content:'';float:right;border-width:0 5px 5px;border-style:solid;\n"
                "                        border-color:#ffffff transparent;visibility:hidden;opacity:.6}\n"
                "  .tg-sort-header:hover:after{visibility:visible}\n"
                "  .tg-sort-asc:after,.tg-sort-asc:hover:after,.tg-sort-desc:after{visibility:visible;opacity:1}\n"
                "  .tg-sort-desc:after{border-bottom:none;border-width:5px 5px 0}\n")
TABLE_MODERN = """
  .content-table {
    border-collapse: collapse;
    margin-top: 5px;
    margin-bottom: 4em;
    font-size: 0.9em;
    font-family: sans-serif;
    min-width: 400px;
    border-radius: 5px 5px 0 0;
    overflow: hidden;
    box-shadow: 0 0 20px var(--table-shadow);
  }
  .content-table thead tr { background-color: var(--table-header-bg); color: var(--table-header-text); text-align: left; }
  .content-table th, .content-table td { padding: 12px 15px; }
  .content-table tbody tr { border-bottom: 1px solid var(--table-border); }
  .content-table tbody tr:nth-of-type(even) { background-color: var(--table-row-even); }
  .content-table tbody tr:last-of-type { border-bottom: 2px solid var(--table-header-bg); }
  .content-table * tr:hover > td { background-color: var(--table-row-hover) !important; color: #ffffff; }
"""
TABLE_CLASSIC = (" .content-table, .content-table th, .content-table td { border: 1px solid var(--table-cl-border); }\n"
                 " .content-table * tr:hover > td { background-color: #B0B0B0 !important }\n")
TD_ERC_CLASSES = """
 .td-error { background-color: var(--td-error); }
 .td-warning { background-color: var(--td-warning); }
 .td-excluded { color: var(--td-excluded); }
"""
GENERATOR_CSS = " .generator { text-align: right; font-size: 0.6em; }\n"
# A nice button with sun, moon and computer to select light, dark and system colors (Gemini)
THEME_BUTTON = '''
<!-- Theme Cycle Button -->
<button id="theme-toggle" class="theme-toggle" aria-label="Toggle Theme">
  <!-- Sun (Light) -->
  <svg id="icon-light" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"
       stroke-linejoin="round">
    <circle cx="12" cy="12" r="5"></circle>
    <line x1="12" y1="1" x2="12" y2="3"></line>
    <line x1="12" y1="21" x2="12" y2="23"></line>
    <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line>
    <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line>
    <line x1="1" y1="12" x2="3" y2="12"></line>
    <line x1="21" y1="12" x2="23" y2="12"></line>
    <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line>
    <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>
  </svg>
  <!-- Moon (Dark) -->
  <svg id="icon-dark" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"
       stroke-linejoin="round">
    <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>
  </svg>
  <!-- Monitor (Auto) -->
  <svg id="icon-auto" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"
       stroke-linejoin="round">
    <rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect>
    <line x1="8" y1="21" x2="16" y2="21"></line>
    <line x1="12" y1="17" x2="12" y2="21"></line>
  </svg>
</button>

'''
# JS helpers for the theme button (Gemini)
SEL_THEME = """
 <!-- Apply theme immediately to prevent flashing -->
 <script>
  (function() {
    const theme = localStorage.getItem('kibot-theme') || 'auto';
    if (theme === 'dark' || (theme === 'auto' && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
      document.documentElement.setAttribute('data-theme', 'dark');
    }
  })();
 </script>

"""
THEME_LOGIC = """
<!-- Interactive Theme Logic -->
<script>
  document.addEventListener("DOMContentLoaded", () => {
    const toggleBtn = document.getElementById('theme-toggle');
    const iconLight = document.getElementById('icon-light');
    const iconDark = document.getElementById('icon-dark');
    const iconAuto = document.getElementById('icon-auto');

    function updateIcons(theme) {
        iconLight.style.display = theme === 'light' ? 'block' : 'none';
        iconDark.style.display = theme === 'dark' ? 'block' : 'none';
        iconAuto.style.display = theme === 'auto' ? 'block' : 'none';
    }

    function applyTheme(theme) {
        if (theme === 'dark' || (theme === 'auto' && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
            document.documentElement.setAttribute('data-theme', 'dark');
        } else {
            document.documentElement.removeAttribute('data-theme');
        }
        updateIcons(theme);
        toggleBtn.title = `Theme: ${theme.charAt(0).toUpperCase() + theme.slice(1)} (Click to change)`;
    }

    let currentTheme = localStorage.getItem('kibot-theme') || 'auto';
    applyTheme(currentTheme);

    // Cycle through themes on click
    toggleBtn.addEventListener('click', () => {
        if (currentTheme === 'auto') currentTheme = 'light';
        else if (currentTheme === 'light') currentTheme = 'dark';
        else currentTheme = 'auto';

        localStorage.setItem('kibot-theme', currentTheme);
        applyTheme(currentTheme);
    });

    // Listen for OS theme changes if in 'auto' mode
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
        if (currentTheme === 'auto') {
            applyTheme('auto');
        }
    });
  });
</script>

"""

# Known rotations for JLC
# Notes:
# - Rotations are CC (counter clock)
# - Most components has pin 1 at the top-right angle, while KiCad uses the top-left
#   This is why most of the ICs has a rotation of 270 (-90)
# - The same applies to things like SOT-23-3, so here you get 180.
# - Most polarized components has pin 1 on the positive pin, becoming it the right one.
#   On KiCad this is not the case, diodes follows it, but capacitors don't. So they get 180.
# - There are exceptions, like SOP-18 or SOP-4 which doesn't follow the JLC rules.
# - KiCad mirrors components on the bottom layer, but JLC doesn't. So you need to "un-mirror" them.
# - The JLC mechanism to interpret rotations changed with time
DEFAULT_ROTATIONS = [["^R_Array_Convex_", 90.0],
                     ["^R_Array_Concave_", 90.0],
                     # *SOT* seems to need 180
                     ["^SOT-143", 180.0],
                     ["^SOT-223", 180.0],
                     ["^SOT-23", 180.0],
                     ["^SOT-353", 180.0],
                     ["^SOT-363", 180.0],
                     ["^SOT-89", 180.0],
                     ["^D_SOT-23", 180.0],
                     ["^TSOT-23", 180.0],
                     # Polarized capacitors
                     ["^CP_EIA-", 180.0],
                     ["^CP_Elec_", 180.0],
                     ["^C_Elec_", 180.0],
                     # Most four side components needs -90 (270)
                     ["^QFN-", 270.0],
                     ["^(.*?_|V)?QFN-(16|20|24|28|40)(-|_|$)", 270.0],
                     ["^DFN-", 270.0],
                     ["^LQFP-", 270.0],
                     ["^TQFP-", 270.0],
                     # SMD DIL packages mostly needs -90 (270)
                     ["^SOP-(?!(18_|4_))", 270.0],  # SOP 18 and 4 excluded, wrong at JLCPCB
                     ["^MSOP-", 270.0],
                     ["^TSSOP-", 270.0],
                     ["^HTSSOP-", 270.0],
                     ["^SSOP-", 270.0],
                     ["^SOIC-", 270.0],
                     ["^SO-", 270.0],
                     ["^SOIC127P798X216-8N", 270.0],
                     ["^VSSOP-8_3.0x3.0mm_P0.65mm", 270.0],
                     ["^VSSOP-8_", 180.0],
                     ["^VSSOP-10_", 270.0],
                     ["^VSON-8_", 270.0],
                     ["^TSOP-6", 270.0],
                     ["^UDFN-10", 270.0],
                     ["^USON-10", 270.0],
                     ["^TDSON-8-1", 270.0],
                     # Misc.
                     ["^LED_WS2812B_PLCC4", 180.0],
                     ["^LED_WS2812B-2020_PLCC4_2.0x2.0mm", 90.0],
                     ["^Bosch_LGA-", 90.0],
                     ["^PowerPAK_SO-8_Single", 270.0],
                     ["^PUIAudio_SMT_0825_S_4_R*", 270.0],
                     ["^USB_C_Receptacle_HRO_TYPE-C-31-M-12*", 180.0],
                     ["^ESP32-W", 270.0],
                     ["^SW_DIP_SPSTx01_Slide_Copal_CHS-01B_W7.62mm_P1.27mm", -180.0],
                     ["^BatteryHolder_Keystone_1060_1x2032", -180.0],
                     ["^Relay_DPDT_Omron_G6K-2F-Y", 270.0],
                     ["^RP2040-QFN-56", 270.0],
                     ["^TO-277", 90.0],
                     ["^SW_SPST_B3", 90.0],
                     ["^Transformer_Ethernet_Pulse_HX0068ANL", 270.0],
                     ["^JST_GH_SM", 180.0],
                     ["^JST_PH_S", 180.0],
                     ["^Diodes_PowerDI3333-8", 270.0],
                     ["^Quectel_L80-R", 270.0],
                     ["^SC-74-6", 180.0],
                     [r"^PinHeader_2x05_P1\.27mm_Vertical", -90.0],
                     [r"^PinHeader_2x03_P1\.27mm_Vertical", -90.0],
                     ]
DEFAULT_ROT_FIELDS = ['JLCPCB Rotation Offset', 'JLCRotOffset']
DEFAULT_OFFSETS = [["^USB_C_Receptacle_XKB_U262-16XN-4BVC11", (0.0, -1.44)],
                   [r"^PinHeader_2x05_P1\.27mm_Vertical", (-2.54, -0.635)],
                   [r"^PinHeader_2x03_P1\.27mm_Vertical", (-1.27, -0.635)],
                   ]
DEFAULT_OFFSET_FIELDS = ['JLCPCB Position Offset', 'JLCPosOffset']
RE_LEN = re.compile(r'\{L:(\d+)\}')


class Rect(object):
    """ What KiCad returns isn't a real wxWidget's wxRect.
        Here I add what I really need """
    def __init__(self):
        self.x1 = None
        self.y1 = None
        self.x2 = None
        self.y2 = None

    def Union(self, wxRect):
        if self.x1 is None:
            self.x1 = wxRect.x
            self.y1 = wxRect.y
            self.x2 = wxRect.x+wxRect.width
            self.y2 = wxRect.y+wxRect.height
        else:
            self.x1 = min(self.x1, wxRect.x)
            self.y1 = min(self.y1, wxRect.y)
            self.x2 = max(self.x2, wxRect.x+wxRect.width)
            self.y2 = max(self.y2, wxRect.y+wxRect.height)


def name2make(name):
    return re.sub(r'[ \$\.\\\/]', '_', name)


@contextmanager
def hide_stderr():
    """ Low level stderr suppression, used to hide KiCad bugs. """
    newstderr = os.dup(2)
    devnull = os.open(os.devnull, os.O_WRONLY)
    os.dup2(devnull, 2)
    os.close(devnull)
    try:
        yield
    finally:
        os.dup2(newstderr, 2)


def version_str2tuple(ver):
    return tuple(map(int, ver.split('.')))


def read_png(file, logger, only_size=True):
    if isinstance(file, str):
        with open(file, 'rb') as f:
            s = f.read()
    else:
        # The data itself as bytes
        s = file
    offset = 8
    ppi = 300
    w = h = -1
    if s[0:8] != b'\x89PNG\r\n\x1a\n':
        raise TypeError('Image is not a PNG')
    logger.debugl(2, 'Parsing PNG chunks')
    while offset < len(s):
        size, type = unpack('>L4s', s[offset:offset+8])
        logger.debugl(2, f'- Chunk {type} ({size})')
        if type == b'IHDR':
            w, h = unpack('>LL', s[offset+8:offset+16])
            logger.debugl(2, f'  - Size {w}x{h}')
            if only_size:
                return s, w, h, ppi
        elif type == b'pHYs':
            dpi_w, dpi_h, units = unpack('>LLB', s[offset+8:offset+17])
            if dpi_w != dpi_h:
                raise TypeError(f'PNG with different resolution for X and Y ({dpi_w} {dpi_h})')
            if units != 1:
                raise TypeError(f'PNG with unknown units ({units})')
            ppi = dpi_w/(100/2.54)
            logger.debugl(2, f'  - PPI {ppi} ({dpi_w} {dpi_h} {units})')
            break
        elif type == b'IEND':
            break
        offset += size+12
    if w == -1:
        raise TypeError('Broken PNG, no IHDR chunk')
    return s, w, h, ppi


def force_list(v):
    return v if v is None or isinstance(v, list) else [v]


def typeof(v, cls, valid=None):
    if isinstance(v, bool):
        return 'boolean'
    if isinstance(v, (int, float)):
        return 'number'
    if isinstance(v, str):
        return 'string'
    if isinstance(v, (dict, cls)):
        return 'dict'
    if isinstance(v, list):
        if len(v) == 0:
            if valid is not None:
                return next(filter(lambda x: x.startswith('list('), valid), 'list(string)')
            return 'list(string)'
        return 'list({})'.format(typeof(v[0], cls))
    return 'None'


def pretty_list(items, short=False):
    if not items:
        return ''
    if short:
        if len(items) == 1:
            return items[0].short_str()
        return ', '.join((x.short_str() for x in items[:-1]))+' and '+items[-1].short_str()
    return str(items[0]) if len(items) == 1 else ', '.join(map(str, items[:-1]))+' and '+str(items[-1])


def try_int(value):
    f_val = float(value)
    i_val = int(f_val)
    return i_val if i_val == f_val else f_val


def try_decode_utf8(data, where, logger, cp):
    try:
        data = data.decode()
    except UnicodeDecodeError:
        msg = f'Invalid UTF-8 sequence at {where}'
        if cp:
            logger.warning(W_NOUTF8 + msg + f' using `{cp}` encoding')
            data = data.decode(cp)
            logger.debug('Using: '+data.rstrip())
        else:
            logger.non_critical_error(msg)
            nres = ''
            for c in data:
                if c > 127:
                    c = 32
                nres += chr(c)
            data = nres
            logger.non_critical_error('Using: '+data.rstrip())
    return data


# Adapted from "Gemini 2.5 Pro Preview O5-O6" example
def get_file_hash(filepath, algorithm="sha256", buffer_size=65536):
    """
    Calculates the hash of a file using the specified algorithm.

    Args:
        filepath (str): The path to the file.
        algorithm (str): The hashing algorithm to use (e.g., 'md5', 'sha1', 'sha256', 'sha512').
                         Defaults to 'sha256'.
                         You can see available algorithms with `hashlib.algorithms_available`.
        buffer_size (int): The size of the chunks to read from the file (in bytes).
                           Defaults to 65536 (64KB).

    Returns:
        str: The hexadecimal representation of the file's hash.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the specified algorithm is not supported by hashlib.
    """
    try:
        # Create a hash object using the specified algorithm
        hash_obj = hashlib.new(algorithm)
    except ValueError:
        raise ValueError(f"Unsupported hash algorithm: {algorithm}. "
                         f"Supported: {sorted(hashlib.algorithms_available)}")

    with open(filepath, 'rb') as f:  # Open the file in binary read mode
        # Read the file in chunks
        while True:
            chunk = f.read(buffer_size)
            if not chunk:
                break
            hash_obj.update(chunk)

    return hash_obj.hexdigest()  # Get the hexadecimal digest of the hash


def update_dict(d, u):
    for k, v in u.items():
        if isinstance(v, collections.abc.Mapping):
            d[k] = update_dict(d.get(k, {}), v)
        elif isinstance(v, list) and k in d:
            d[k] = v+d[k]
        elif isinstance(v, set) and k in d:
            d[k] |= v
        else:
            d[k] = v
    return d
