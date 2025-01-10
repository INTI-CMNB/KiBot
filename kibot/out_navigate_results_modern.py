# -*- coding: utf-8 -*-
# Copyright (c) 2022-2025 Salvador E. Tropea
# Copyright (c) 2022-2025 Nguyen Vincent
# Copyright (c) 2022-2025 Instituto Nacional de Tecnología Industrial
# Contributed by Nguyen Vincent (@nguyen-v)
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)
# The Assembly image is a composition from Pixlok and oNline Web Fonts
# The rest are KiCad icons
"""
Dependencies:
  - from: RSVG
    role: Create outputs preview
    id: rsvg1
  - from: RSVG
    role: Create PNG icons
    id: rsvg2
  - from: Ghostscript
    role: Create outputs preview
  - from: ImageMagick
    role: Create outputs preview
  - from: Git
    role: Find origin url
"""
import base64
import os
import re
import subprocess
import pprint
from shutil import copy2
from math import ceil
from .bom.kibot_logo import KIBOT_LOGO
from .error import KiPlotConfigurationError
from .gs import GS
from .optionable import Optionable, BaseOptions
from .kiplot import config_output, get_output_dir, run_command
from .misc import W_NOTYET, W_MISSTOOL, W_NOOUTPUTS, read_png, force_list
from .pre_base import BasePreFlight
from .registrable import RegOutput
from .macros import macros, document, output_class  # noqa: F401
from . import log, __version__

logger = log.get_logger()
EXT_IMAGE = {'gbr': 'file_gbr',
             'gtl': 'file_gbr',
             'gtp': 'file_gbr',
             'gbo': 'file_gbr',
             'gto': 'file_gbr',
             'gbs': 'file_gbr',
             'gbl': 'file_gbr',
             'gts': 'file_gbr',
             'gml': 'file_gbr',
             'gm1': 'file_gbr',
             'gbrjob': 'file_gerber_job',
             'brd': 'file_brd',
             'bz2': 'file_bz2',
             'dxf': 'file_dxf',
             'cad': 'file_cad',
             'drl': 'file_drl',
             'pdf': 'file_pdf',
             'txt': 'file_txt',
             'pos': 'file_pos',
             'csv': 'file_csv',
             'svg': 'file_svg',
             'eps': 'file_eps',
             'png': 'file_png',
             'jpg': 'file_jpg',
             'plt': 'file_plt',
             'ps': 'file_ps',
             'rar': 'file_rar',
             'scad': 'file_scad',
             'stl': 'file_stl',
             'step': 'file_stp',
             'stp': 'file_stp',
             'wrl': 'file_wrl',
             'html': 'file_html',
             'css': 'file_css',
             'xml': 'file_xml',
             'tsv': 'file_tsv',
             'xlsx': 'file_xlsx',
             'xyrs': 'file_xyrs',
             'xz': 'file_xz',
             'gz': 'file_gz',
             'tar': 'file_tar',
             'zip': 'file_zip',
             'kicad_pcb': 'pcbnew',
             'sch': 'eeschema',
             'kicad_sch': 'eeschema',
             'blend': 'file_blend',
             'pcb3d': 'file_pcb3d',
             'json': 'file_json'}
for i in range(31):
    n = str(i)
    EXT_IMAGE['gl'+n] = 'file_gbr'
    EXT_IMAGE['g'+n] = 'file_gbr'
    EXT_IMAGE['gp'+n] = 'file_gbr'

BIG_ICON = 512
MID_ICON = 64

IMAGEABLES_SIMPLE = {'png', 'jpg'}
IMAGEABLES_GS = {'pdf', 'eps', 'ps'}
IMAGEABLES_SVG = {'svg'}
TITLE_HEIGHT = 30
STYLE = """

/* Colors =================================================================== */

:root {
	--light-bg-color: #ffffff;
	--dark-bg-color: #1e1e2f;
	--light-bg-color-banner: #dfdfdf;
	--dark-bg-color-banner: #27293d;
	--light-text-color: #444444;
	--dark-text-color: #e5e5e5;
	--light-hover-color: #902ec9;
	--light-hover-color-act: #652f85;
	--dark-hover-color: #ffa500;
	--dark-hover-color-act: #cc8400;
	--dark-text-color-accent: #a3a3c2;
	--light-text-color-accent: #444444;
	--light-banner-hover: #b0b0b0;
	--dark-banner-hover: #383b4b;
	--text-color-accent: #a3a3c2;
}

/* Main body ================================================================ */

body {
	margin: 0;
	font-family: 'Roboto', sans-serif;
	background-color: var(--dark-bg-color);
	color: var(--dark-text-color);
	transition: 
        background-color 0.4s ease,
        color 0.4s ease,
        transition: scrollbar-color 0.2s ease-in-out;
}

body.dark-mode {
	--text-color-accent: var(--dark-text-color-accent);
	background-color: var(--dark-bg-color);
	color: var(--dark-text-color);
}

body.light-mode {
	--text-color-accent: var(--light-text-color-accent);
	background-color: var(--light-bg-color);
	color: var(--light-text-color);
}

/* Top Menu ================================================================= */

/* Layout is as follows */
/* [X/☰] [↩] [↪] <Category Path> <Title> (Logo) [☾/☀] [🏠︎] */

#topmenu {
	position: fixed;
	top: 0;
	left: 0;
	width: 100%;
	z-index: 1000;
	background-color: var(--dark-bg-color-banner);
	padding: 10px 0;
	box-shadow: 0 2px 5px rgba(0, 0, 0, 0.3);
	display: flex;
	align-items: center;
	justify-content: space-between;
    transition: background-color 0.2s ease, color 0.2s ease;
}

body.light-mode #topmenu {
  	background-color: var(--light-bg-color-banner);
}

body.dark-mode #topmenu {
  	background-color: var(--dark-bg-color-banner);
}

/* Buttons ================================================================== */

/* button corresponds to the navigation buttons (forward, backward, home) */

button, #open-sidenav, #close-sidenav {
	background: none;
	border: none;
	color: var(--dark-text-color);
	cursor: pointer;
	transition: color 0.3s ease;
}

body.light-mode #topmenu button,
body.light-mode #topmenu #open-sidenav,
body.light-mode #topmenu #close-sidenav {
  	color: var(--light-text-color);
}

body.dark-mode #topmenu button,
body.dark-mode #topmenu #open-sidenav,
body.dark-mode #topmenu #close-sidenav {
  	color: var(--dark-text-color);
}

button {
	font-size: 20px;
	margin: 0 10px;
}

#open-sidenav, #close-sidenav {
	width: 36px;
	height: 36px;
	line-height: 36px;
	text-align: center;
	font-size: 28px;
	margin-left: 10px;
	user-select: none; /* Prevent text selection */
}

/* Hover effects */

button:hover, #open-sidenav:hover, #close-sidenav:hover {
  	color: var(--dark-hover-color);
}

body.dark-mode #topmenu button:hover,
body.dark-mode #topmenu #open-sidenav:hover,
body.dark-mode #topmenu #close-sidenav:hover {
  	color: var(--dark-hover-color);
}

body.light-mode #topmenu button:hover,
body.light-mode #topmenu #open-sidenav:hover,
body.light-mode #topmenu #close-sidenav:hover {
  	color: var(--light-hover-color);
}

/* Active effects */

button:active, #open-sidenav:active, #close-sidenav:active {
	color: var(--dark-hover-color-act);
	transition: none;
}

body.dark-mode #topmenu button:active,
body.dark-mode #topmenu #open-sidenav:active,
body.dark-mode #topmenu #close-sidenav:active {
  	color: var(--dark-hover-color-act);
}

body.light-mode #topmenu button:active,
body.light-mode #topmenu #open-sidenav:active,
body.light-mode #topmenu #close-sidenav:active {
  	color: var(--light-hover-color-act);
}

/* Sidebar Navigation ======================================================= */

.sidenav {
    position: fixed;
    width: 0; /* Initially collapsed */
    height: calc(100% - var(--top-menu-height, 60px));
    top: var(--top-menu-height, 60px);
    left: 0;
    background-color: #27293d;
    overflow-x: hidden;
    overflow-y: auto;
    transition: 
        width 0.5s ease, 
        padding-left 0.5s ease,
        scrollbar-color 0.2s ease-in-out,
        background-color 0.2s ease-in-out;
    box-sizing: border-box;
    padding-top: 0;
}


body.dark-mode .sidenav {
  	background-color: var(--dark-bg-color-banner);
}

body.light-mode .sidenav {
  	background-color: var(--light-bg-color-banner);
}

.sidenav > ul:first-child {
  	margin-top: 20px; /* Padding between top menu and first element of sidenav */
}

/* Side Navigation Outputs -------------------------------------------------- */ 

.sidenav-output {
	padding: 8px 30px;
	text-decoration: none;
	font-size: 16px;
	color: var(--dark-text-color);
	display: block;
	transition: color 0.3s ease;
	border-radius: 4px;
}

body.light-mode .sidenav-output {
  	color: var(--light-text-color);
}

body.dark-mode .sidenav-output {
  	color: var(--dark-text-color);
}

/* Hover effects */

.sidenav-output:hover {
	color: var(--dark-hover-color);
	background-color: var(--dark-banner-hover);
}

body.dark-mode .sidenav-output:hover {
	color: var(--dark-hover-color);
	background-color: var(--dark-banner-hover);
}

body.light-mode .sidenav-output:hover {
	color: var(--light-hover-color);
	background-color: var(--light-banner-hover);
}

/* Active effects */

.sidenav-output:active {
  	color: var(--dark-hover-color-act);
}

body.dark-mode .sidenav-output:active {
  	color: var(--dark-hover-color-act);
}

body.light-mode .sidenav-output:active {
  	color: var(--light-hover-color-act);
}

/* Side Navigation Categories ----------------------------------------------- */

.sidenav-category {
	list-style: none;
	padding: 0;
	margin: 0;
	user-select: none; /* Prevent text selection */
}

.sidenav-category .folder > span {
	display: flex;
	align-items: center;
	cursor: pointer;
	color: var(--dark-text-color-accent);
	padding: 10px 20px;
	margin-bottom: 0px;
	width: 100%;
	transition: background-color 0.3s, color 0.3s;
	border-radius: 4px;
}

.sidenav-category .folder-contents {
	list-style: none;
	margin-left: 20px;
	padding: 0;
}

body.dark-mode .sidenav-category .folder > span {
  	color: var(--dark-text-color-accent);
}

body.light-mode .sidenav-category .folder > span {
  	color: var(--light-text-color);
}

/* Hover effects */

.sidenav-category .folder > span:hover {
	background-color: var(--dark-banner-hover);
	color: var(--dark-hover-color);
}

body.dark-mode .sidenav-category .folder > span:hover {
	color: var(--dark-hover-color);
	background-color: var(--dark-banner-hover);
}

body.light-mode .sidenav-category .folder > span:hover {
	color: var(--light-hover-color);
	background-color: var(--light-banner-hover);
}

/* Active effects */

.sidenav-category .folder > span:active {
	color: var(--dark-hover-color);
	transition: none;
}

body.dark-mode .sidenav-category .folder > span:active {
  	color: var(--dark-hover-color-act);
}

body.light-mode .sidenav-category .folder > span:active {
  	color: var(--light-hover-color-act);
}

/* Chevron (arrow) styling -------------------------------------------------- */

.chevron {
	display: block;
	width: 0;
	height: 0;
	border: 8px solid transparent;
	border-left-color: #606077;
	margin-right: 8px;
	transform-origin: 25% 50%;
	transition: transform 0.3s ease, border-left-color 0.3s ease;
	pointer-events: none;
}

body.dark-mode .chevron {
  	border-left-color: #606077;
}

body.light-mode .chevron {
  	border-left-color: #909090;
}

/* We change styles for when the chevron is pointing down */

.folder.open > span .chevron {
	border-left-color: var(--dark-text-color-accent);
	transform: rotate(90deg);
}

body.dark-mode .folder.open > span .chevron {
  	border-left-color: var(--dark-text-color-accent);
}

body.light-mode .folder.open > span .chevron {
  	border-left-color: var(--light-text-color-accent);
}

/* Hover effects */

body.dark-mode .folder > span:hover .chevron {
  	border-left-color: var(--dark-hover-color)
}

body.light-mode .folder > span:hover .chevron {
  	border-left-color: var(--light-hover-color)
}

/* Active effects */

body.dark-mode .folder > span:active .chevron {
  	border-left-color: var(--dark-hover-color-act)
}


body.light-mode .folder > span:active .chevron {
  	border-left-color: var(--light-hover-color-act)
}

/* Main content ============================================================= */

#main {
	transition: margin-left 0.5s;
	padding: 16px;
	margin-top: 80px;
}

/* Comment field of output is used as a title for each output */

.output-comment {
	font-size: 1.4em;
	font-weight: 500;
	color: var(--dark-text-color);
	margin: 20px 0 10px 0;
	text-align: center;
}

body.light-mode .output-comment {
  	color: var(--light-text-color);
}

body.dark-mode .output-comment {
  	color: var(--dark-text-color);
}

/* Category boxes (folder) -------------------------------------------------- */

.category-box {
    display: flex;
    align-items: center;
    justify-content: center;
    background-color: var(--dark-bg-color-banner);
    border: 1px solid var(--dark-bg-color-banner);
    border-radius: 8px;
    padding: 10px 20px;
    text-decoration: none;
    color: var(--light-text-color);
    max-width: 400px;
    transition: background-color 0.3s ease, transform 0.2s ease;
    margin: 10px auto;
}

body.light-mode .category-box {
	color: var(--light-text-color);
	background-color: var(--light-bg-color-banner);
	border: var(--light-bg-color-banner);
}


body.dark-mode .category-box {
	color: var(--dark-text-color);
	background-color: var(--dark-bg-color-banner);
	border: var(--dark-bg-color-banner);
}

.category-title {
    font-size: 1.4em;
    font-weight: 500;
    text-align: center;
    color: #e5e5e5;
    text-decoration: none;
    display: inline-block;
}

body.light-mode .category-title {
  	color: var(--light-text-color);
}

body.dark-mode .category-title {
  	color: var(--dark-text-color);
}

/* Hover effects */

.category-box:hover {
		background-color: var(--dark-banner-hover);
		transform: scale(1.05); /* Slight zoom effect */
		cursor: pointer;
}

body.light-mode .category-box:hover {
  	background-color: var(--light-banner-hover);
}

body.dark-mode .category-box:hover {
  	background-color: var(--dark-banner-hover);
}

/* Output boxes (files) ----------------------------------------------------- */

.output-box {
	background-color: var(--dark-bg-color-banner);
	border: 1px solid var(--dark-bg-color-banner);
	border-radius: 8px;
	padding: 16px;
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	width: 300px;
	height: 140px;
	text-decoration: none;
	transition: background-color 0.3s ease, transform 0.2s ease;
}

/* Offset the scroll position */
.output-virtual-box {
    position: relative;
    padding-top: var(--top-menu-height, 80px);
    margin-top: calc(-1 * var(--top-menu-height, 80px));
}

/* Some files (e.g. PDF, PNG) have wider output boxes */

.output-box.wide {
	width: 400px;
	height: auto;
}

.output-box img {
	max-width: 100%;
	max-height: 100%;
	height: auto;
	margin-bottom: 10px;
}

/* The output boxes are centered and wrap around */

.items-container {
	display: flex;
	flex-wrap: wrap;
	justify-content: center;
	gap: 20px;
	padding: 20px;
}

body.light-mode .output-box {
	color: var(--light-text-color);
	background-color: var(--light-bg-color-banner);
	border: var(--light-bg-color-banner);
}

body.dark-mode .output-box {
	color: var(--dark-text-color);
	background-color: var(--dark-bg-color-banner);
	border: var(--dark-bg-color-banner);
}

/* Hover effects */

.output-box:hover {
	background-color: var(--dark-banner-hover);
	transform: scale(1.05);
	cursor: pointer;
}

body.light-mode .output-box:hover {
  	background-color: var(--light-banner-hover);
}

body.dark-mode .output-box:hover {
  	background-color: var(--dark-banner-hover);
}

/* Name of the output below the icon */

.output-box .output-name {
	color: #8997c6;
	font-size: 14px;
	margin-top: 8px;
	text-align: center;
}

body.light-mode .output-box .output-name {
  	color: var(--light-text-color-accent);
}

body.dark-mode .output-box .output-name {
  	color: #8997c6;
}

/* Filename below the icon */

.output-box .filename {
	text-decoration: none;
	color: var(--dark-text-color);
	text-align: center;
	font-size: 14px;
}

body.light-mode .output-box .filename {
  	color: var(--light-text-color);
}

body.dark-mode .output-box .filename {
  	color: var(--dark-text-color);
}

/* Theme Toggle Switch ====================================================== */

.theme-switch {
	position: relative;
	display: inline-block;
	width: 50px;
	height: 25px;
	margin-left: 10px;
}

/* Hide the default checkbox button */

.theme-switch input {
	opacity: 0;
	width: 0;
	height: 0;
}

.theme-switch span {
	position: absolute;
	cursor: pointer;
	background-color: var(--light-banner-hover);
	border-radius: 25px;
	top: 0;
	left: 0;
	right: 0;
	bottom: 0;
	transform: translateY(-30%); /* Center vertically */
	transition: 0.4s;
}

.theme-switch span::before {
	position: absolute;
	content: "";
	height: 20px;
	width: 20px;
	left: 4px;
	bottom: 3px;
	background-color: var(--light-bg-color);
	border-radius: 50%;
	transition: none; /* Disable animation by default */
}

.theme-switch span.animate::before {
  	transition: transform 0.4s ease, background-color 0.4s ease;
}

.theme-switch input:checked + span {
  	background-color: var(--dark-bg-color);
}

.theme-switch input:checked + span::before {
	transform: translateX(25px);
	background-color: var(--dark-text-color);
}

/* Scrollbar ================================================================ */

body, html {
    scroll-behavior: smooth;
    scrollbar-width: auto;
}

body.dark-mode .sidenav {
    scrollbar-color: var(--dark-banner-hover) var(--dark-bg-color);
}

body.light-mode .sidenav {
    scrollbar-color: var(--light-banner-hover) var(--light-bg-color);
}

/* WebKit Scrollbar Styles */
body::-webkit-scrollbar, .sidenav::-webkit-scrollbar {
    width: 12px;
    height: 12px;
}

body::-webkit-scrollbar-thumb, .sidenav::-webkit-scrollbar-thumb {
    border-radius: 6px;
    background: var(--dark-banner-hover);
    border: 2px solid var(--dark-bg-color);
}

body::-webkit-scrollbar-track, .sidenav::-webkit-scrollbar-track {
    border-radius: 6px;
    background: var(--dark-bg-color);
}

body.dark-mode::-webkit-scrollbar-thumb:hover, .sidenav.dark-mode::-webkit-scrollbar-thumb:hover {
    background: #44475a !important;
}

body.light-mode::-webkit-scrollbar-thumb, .sidenav.light-mode::-webkit-scrollbar-thumb {
    background: var(--light-banner-hover);
    border: 2px solid var(--light-bg-color);
}

body.light-mode::-webkit-scrollbar-track, .sidenav.light-mode::-webkit-scrollbar-track {
    background: var(--light-bg-color);
}

body.light-mode::-webkit-scrollbar-thumb:hover, .sidenav.light-mode::-webkit-scrollbar-thumb:hover {
    background: #909090 !important;
}

body::-webkit-scrollbar-corner, .sidenav::-webkit-scrollbar-corner {
    background: var(--dark-bg-color);
}

/* Markdown ================================================================= */

.markdown-content {
    font-family: Roboto, sans-serif;
    line-height: 1.6;
    margin-left: 150px;
    margin-right: 150px;
    padding: 15px;
    border-radius: 5px;
    white-space: pre-wrap; /* Handle preformatted text */
    transition: background-color 0.4s ease, color 0.4s ease, border-color 0.4s ease;
}

body.light-mode .markdown-content {
    background-color: #f9f9f9;
    border: 1px solid #ddd;
    color: #444444;
    transition: background-color 0.4s ease, color 0.4s ease, border-color 0.4s ease;
}

body.dark-mode .markdown-content {
    background-color: #1e1e2f;
    border: 1px solid #44475a;
    color: #e5e5e5;
    transition: background-color 0.4s ease, color 0.4s ease, border-color 0.4s ease;
}

/* Tables */
.markdown-content table {
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 20px;
    transition: background-color 0.4s ease, color 0.4s ease, border-color 0.4s ease;
}

body.light-mode .markdown-content table th,
body.light-mode .markdown-content table td {
    border: 1px solid #ddd;
    padding: 8px;
    text-align: left;
    background-color: #ffffff;
    color: #444444;
    transition: background-color 0.4s ease, color 0.4s ease, border-color 0.4s ease;
}

body.dark-mode .markdown-content table th,
body.dark-mode .markdown-content table td {
    border: 1px solid #44475a;
    padding: 8px;
    text-align: left;
    background-color: #27293d;
    color: #e5e5e5;
    transition: background-color 0.4s ease, color 0.4s ease, border-color 0.4s ease;
}

/* Code Blocks */
.markdown-content pre {
    background-color: var(--dark-bg-color-banner);
    color: var(--dark-text-color); /* Matches dark theme text */
    padding: 10px;
    border-radius: 5px;
    overflow-x: auto;
    transition: background-color 0.4s ease, color 0.4s ease;
}

body.light-mode .markdown-content pre {
    background-color: var(--light-bg-color-banner);
    color: var(--light-text-color);
    transition: background-color 0.4s ease, color 0.4s ease;
}

body.dark-mode .markdown-content pre {
    background-color: var(--dark-bg-color-banner);
    color: var(--dark-text-color);
    transition: background-color 0.4s ease, color 0.4s ease;
}

/* Inline Code */
.markdown-content code {
    background-color: var(--light-bg-color-banner);
    padding: 2px 5px;
    border-radius: 3px;
    font-family: 'Courier New', Courier, monospace;
    transition: background-color 0.4s ease, color 0.4s ease;
}

body.light-mode .markdown-content code {
    background-color: var(--light-bg-color-banner);
    color: var(--light-text-color);
    transition: background-color 0.4s ease, color 0.4s ease;
}

body.dark-mode .markdown-content code {
    background-color: var(--dark-bg-color-banner);
    color: var(--dark-text-color);
    transition: background-color 0.4s ease, color 0.4s ease;
}

/* Links */
body.light-mode .markdown-content a {
    color: var(--light-hover-color);
    text-decoration: none;
    transition: color 0.4s ease;
}

body.dark-mode .markdown-content a {
    color: var(--dark-hover-color);
    text-decoration: none;
    transition: color 0.4s ease;
}

.markdown-content a:hover {
    text-decoration: underline;
}

/* Images */
.markdown-content img {
    max-width: 100%;
    height: auto;
    display: block;
    margin: 10px auto;
    transition: opacity 0.4s ease;
}

/* Search bar =============================================================== */

#search-container,
#search-bar,
#autocomplete-list,
#autocomplete-list li {
    transition: background-color 0.3s, color 0.3s, border-color 0.3s;
}

#search-container {
    padding: 10px;
    background-color: transparent;
    margin-top: 10px;
    top: 0;
    z-index: 1001;
    width: calc(100% - 10px);
    box-sizing: border-box;
}

#search-bar {
    width: 100%; /* Match the width of the container */
    padding: 8px;
    border: 1px solid var(--light-text-color-accent);
    border-radius: 4px;
    outline: none;
    background-color: transparent;
    color: var(--light-text-color);
    box-sizing: border-box; /* Ensure padding is included in width */
}

#search-bar::placeholder {
    color: var(--light-text-color-accent);
}

#autocomplete-list {
    list-style-type: none;
    padding: 0;
    margin: 5px 0 0;
    max-height: 200px;
    overflow-y: auto;
    background-color: var(--light-bg-color-banner);
    border: 1px solid var(--light-text-color-accent);
    border-radius: 4px;
    position: absolute;
    z-index: 1001;
    width: auto; /* Width will be dynamically calculated */
    box-sizing: border-box;
    display: none; /* Hidden by default */
}

#autocomplete-list li {
    padding: 8px;
    cursor: pointer;
    transition: background-color 0.2s;
    color: var(--light-text-color);
}

#autocomplete-list li:hover {
    background-color: var(--light-banner-hover);
    color: var(--light-hover-color);
}

.dark-mode #search-bar {
    color: var(--dark-text-color);
    border-color: var(--dark-text-color-accent);
}

.dark-mode #search-bar::placeholder {
    color: var(--dark-text-color-accent);
}

.dark-mode #autocomplete-list {
    background-color: var(--dark-bg-color-banner);
    border-color: var(--dark-text-color-accent);
}

.dark-mode #autocomplete-list li {
    color: var(--dark-text-color);
}

.dark-mode #autocomplete-list li:hover {
    background-color: var(--dark-banner-hover);
    color: var(--dark-hover-color);
}


/* New classes to remove transitions on page load =========================== */

body.no-transition,
.no-transition .output-box,
body.no-transition .theme-switch span,
body.no-transition button,
body.no-transition #close-sidenav,
body.no-transition #home-button, 
body.no-transition #back-button, 
body.no-transition #forward-button,
body.no-transition #topmenu,
body.no-transition .sidenav-category .folder > span,
body.no-transition .category-box {
    transition: none !important; /* Disable transition during page load */
}

"""
SCRIPT_NAV_BAR = """
<script>

// Side Navigation functions ===================================================

function openNav() {
	const sidenav = document.getElementById("theSideNav");
	const main = document.getElementById("main");

	sidenav.style.width = "360px";
	sidenav.style.paddingLeft = "20px";
	main.style.marginLeft = "360px";
	document.getElementById("open-sidenav").style.display = "none";
	document.getElementById("close-sidenav").style.display = "inline-block";
}

function closeNav() {
	const sidenav = document.getElementById("theSideNav");
	const main = document.getElementById("main");

	sidenav.style.width = "0"; // Close the sidenav
	sidenav.style.paddingLeft = "0"; // Reset padding
	main.style.marginLeft = "0"; // Reset page content position
	document.getElementById("open-sidenav").style.display = "inline-block";
	document.getElementById("close-sidenav").style.display = "none";
}

function toggleFolder(folderHeader) {
	const folder = folderHeader.parentElement;
	const folderContents = folderHeader.nextElementSibling;

	if (folder.classList.contains("open")) {
		folder.classList.remove("open");
		folderContents.style.display = "none";
	} else {
		folder.classList.add("open");
		folderContents.style.display = "block";
	}

	// Save the updated state
	saveSideNavState();
}

function saveSideNavState() {
	const sidenav = document.getElementById("theSideNav");
	const isOpen = sidenav.style.width !== "0px"; // Check if sidenav is open

	// Save the state of each folder
	const folderStates = Array.from(document.querySelectorAll(".folder")).map(folder => ({
		id: folder.querySelector("span").textContent.trim(), // Use folder name as identifier
		isOpen: folder.classList.contains("open") // Check if folder is open
	}));

	// Save the sidenav and folder states to localStorage
	localStorage.setItem("sidenavState", JSON.stringify({ isOpen, folderStates }));
}

function restoresidenavState() {
	const savedState = localStorage.getItem("sidenavState");
	if (savedState) {
		const { isOpen, folderStates } = JSON.parse(savedState);
		const sidenav = document.getElementById("theSideNav");
		const main = document.getElementById("main");

		// Temporarily disable animations on page load so elements don't move
		sidenav.style.transition = "none";
		main.style.transition = "none";
		const chevrons = document.querySelectorAll(".chevron");
		chevrons.forEach(chevron => {
			chevron.style.transition = "none";
		});

		// Restore side navigation state
		if (isOpen) {
			openNav()
		} else {
			closeNav()
		}

		// Restore folder open/closed states
		folderStates.forEach(({ id, isOpen }) => {
			const folder = Array.from(document.querySelectorAll(".folder"))
				.find(folder => folder.querySelector("span").textContent.trim() === id);

			if (folder) {
				const folderContents = folder.querySelector(".folder-contents");
				if (isOpen) {
					folder.classList.add("open");
					folderContents.style.display = "block";
				} else {
					folder.classList.remove("open");
					folderContents.style.display = "none";
				}
			}
		});

		// Re-enable animation
		setTimeout(() => {
			sidenav.style.transition = "";
			main.style.transition = "";
			chevrons.forEach(chevron => {
				chevron.style.transition = "";
			});
		}, 100);
	}
}

function saveSidenavScrollPosition() {
	const sidenav = document.getElementById("theSideNav");
	const scrollPosition = sidenav.scrollTop;
	localStorage.setItem("sidenavScrollPosition", scrollPosition);
}

function restoreSidenavScrollPosition() {
	const sidenav = document.getElementById("theSideNav");
	const savedPosition = localStorage.getItem("sidenavScrollPosition");
	if (savedPosition !== null) {
		sidenav.scrollTop = parseInt(savedPosition, 10);
	}
}

function adjustSidenavOffset() {
	const topMenu = document.getElementById("topmenu");
	const sidenav = document.getElementById("theSideNav");

	if (topMenu) {
		const topMenuHeight = topMenu.offsetHeight;
		document.documentElement.style.setProperty('--top-menu-height', `${topMenuHeight}px`);
	}
}

adjustSidenavOffset();
window.addEventListener("resize", adjustSidenavOffset);

/* This is the scrolling offset when we click on an output in the side navigation bar
   It should take into account the top menu height */
function adjustOutputOffset() {
    const topMenu = document.getElementById("topmenu"); // Replace with your top menu's ID
    if (topMenu) {
        const topMenuHeight = topMenu.offsetHeight; // Dynamically get the top menu height
        document.documentElement.style.setProperty('--top-menu-height', `${topMenuHeight}px`);
    }
}

window.addEventListener("DOMContentLoaded", adjustOutputOffset);
window.addEventListener("resize", adjustOutputOffset);

// Prevent flickering on page navigation
window.addEventListener("beforeunload", () => {
	saveSideNavState();
	saveSidenavScrollPosition();
});

window.addEventListener("load", restoreSidenavScrollPosition);
document.addEventListener("DOMContentLoaded", restoresidenavState);
</script>
"""

SCRIPT = """
<script>
// Theme toggle ================================================================

function toggleTheme() {
    const body = document.body;

    // Check if the current theme is dark
    const isDark = body.classList.contains('dark-mode');

    // Toggle between dark and light themes
    if (isDark) {
        body.classList.remove('dark-mode');
        body.classList.add('light-mode');
    } else {
        body.classList.remove('light-mode');
        body.classList.add('dark-mode');
    }

    // Save the selected theme to localStorage
    localStorage.setItem('theme', isDark ? 'light' : 'dark');
}

// Do not animate theme toggle on page load
document.addEventListener("DOMContentLoaded", () => {
    const themeToggle = document.getElementById('themeToggle');
    const toggleSpan = themeToggle.nextElementSibling; // The <span> element

    // Prevent animation on page load
    const savedTheme = localStorage.getItem('theme') || 'dark';
    document.body.classList.add(savedTheme === 'dark' ? 'dark-mode' : 'light-mode');
    themeToggle.checked = savedTheme === 'dark';

    // Add the "animate" class on user interaction
    themeToggle.addEventListener('change', () => {
        toggleSpan.classList.add('animate');
        setTimeout(() => {
            toggleSpan.classList.remove('animate'); // Remove the animation class after completion
        }, 400); // Match the CSS transition duration (0.4s)
    });
});

// Avoid flickering of theme toggle on page load
document.addEventListener("DOMContentLoaded", () => {
    const body = document.body;

    // Temporarily disable transitions during page load
    body.classList.add('no-transition');

    // Remove the no-transition class after the page is fully loaded
    setTimeout(() => {
        body.classList.remove('no-transition');
    }, 50); // Allow rendering to complete before enabling transitions
});

document.addEventListener('DOMContentLoaded', function () {
    const md = window.markdownit({
        html: true,
        linkify: true,
        typographer: true
    });

    // Find all markdown containers and render them
    document.querySelectorAll('.markdown-content').forEach(container => {
        const rawMarkdown = container.innerHTML;
        container.style.display = 'block';
        container.innerHTML = md.render(rawMarkdown);
    });
});

function adjustMainBodyOffset() {
    const topMenu = document.getElementById("topmenu");
    const mainBody = document.getElementById("main");

    if (topMenu && mainBody) {
        const topMenuHeight = topMenu.offsetHeight;
        mainBody.style.marginTop = `${topMenuHeight}px`;
    }
}

// Apply the adjustment on page load and window resize
window.addEventListener("DOMContentLoaded", adjustMainBodyOffset);
window.addEventListener("resize", adjustMainBodyOffset);

document.addEventListener("DOMContentLoaded", function () {
    const searchBar = document.getElementById("search-bar");
    const autocompleteList = document.getElementById("autocomplete-list");
    const outputLinks = document.querySelectorAll(".sidenav-output");

    // Collect output names and their hrefs
    const outputs = Array.from(outputLinks).map(link => ({
        name: link.textContent.trim(),
        href: link.getAttribute("href")
    }));

    function updateAutocompleteWidth() {
        const searchBarWidth = searchBar.offsetWidth; // Get the width of the search bar
        autocompleteList.style.width = `${searchBarWidth}px`; // Match autocomplete width to search bar
    }

    // Initial width adjustment
    updateAutocompleteWidth();

    // Update width on window resize to handle responsiveness
    window.addEventListener("resize", updateAutocompleteWidth);


    // Update autocomplete suggestions
    function updateAutocomplete(query) {
        // Clear previous suggestions
        autocompleteList.innerHTML = "";

        // Filter and display matching outputs
        const matches = outputs.filter(output =>
            output.name.toLowerCase().includes(query.toLowerCase())
        );

        if (matches.length > 0) {
            matches.forEach(match => {
                const listItem = document.createElement("li");
                listItem.textContent = match.name;
                listItem.addEventListener("click", () => {
                    window.location.href = match.href; // Redirect to the selected output
                });
                autocompleteList.appendChild(listItem);
            });
            autocompleteList.style.display = "block"; // Show the list
        } else {
            autocompleteList.style.display = "none"; // Hide the list if no matches
        }
    }

    // Add event listeners to the search bar
    searchBar.addEventListener("input", () => {
        const query = searchBar.value.trim();
        if (query) {
            updateAutocomplete(query);
        } else {
            autocompleteList.innerHTML = ""; // Clear suggestions
            autocompleteList.style.display = "none"; // Hide the list
        }
    });

    // Hide autocomplete list when clicking outside
    document.addEventListener("click", (event) => {
        if (!searchBar.contains(event.target) && !autocompleteList.contains(event.target)) {
            autocompleteList.style.display = "none";
        }
    });
});
</script>
"""

def _run_command(cmd):
    logger.debug('- Executing: '+GS.pasteable_cmd(cmd))
    try:
        cmd_output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        if e.output:
            logger.debug('Output from command: '+e.output.decode())
        logger.non_critical_error(f'Failed to run {cmd[0]}, error {e.returncode}')
        return False
    if cmd_output.strip():
        logger.debug('- Output from command:\n'+cmd_output.decode())
    return True


class Navigate_Results_ModernOptions(BaseOptions):
    def __init__(self):
        with document:
            self.output = GS.def_global_output
            """ *Filename for the output (%i=html, %x=navigate) """
            self.link_from_root = ''
            """ *The name of a file to create at the main output directory linking to the home page """
            self.skip_not_run = False
            """ Skip outputs with `run_by_default: false` """
            self.logo = Optionable
            """ [string|boolean=''] PNG file to use as logo, use false to remove.
                The KiBot logo is used by default """
            self.logo_url = 'https://github.com/INTI-CMNB/KiBot/'
            """ Target link when clicking the logo """
            self.title = ''
            """ Title for the page, when empty KiBot will try using the schematic or PCB title.
                If they are empty the name of the project, schematic or PCB file is used.
                You can use %X values and KiCad variables here """
            self.title_url = Optionable
            """ [string|boolean=''] Target link when clicking the title, use false to remove.
                KiBot will try with the origin of the current git repo when empty """
            self.nav_bar = True
            """ Add a side navigation bar to quickly access to the outputs """
            self.render_markdown = True
            """ If True, markdown files are rendered; otherwise, they are treated like other files """
        super().__init__()
        self._expand_id = 'navigate'
        self._expand_ext = 'html'
        self._variant_name = self._find_variant_name()
    def config(self, parent):
        super().config(parent)
        # Logo
        if isinstance(self.logo, bool):
            self.logo = '' if self.logo else None
        elif self.logo:
            self.logo = os.path.abspath(self.logo)
            if not os.path.isfile(self.logo):
                raise KiPlotConfigurationError('Missing logo file `{}`'.format(self.logo))
            try:
                self._logo_data, _, _, _ = read_png(self.logo, logger)
            except TypeError as e:
                raise KiPlotConfigurationError(f'Only PNG images are supported for the logo ({e})')
        if self.logo == '':
            # Internal logo
            self._logo_data = base64.b64decode(KIBOT_LOGO)
        elif self.logo is None:
            self._logo_data = ''
        # Title URL
        if isinstance(self.title_url, bool):
            self.title_url = '' if self.title_url else None

    def add_to_tree(self, cat, out, o_tree):
        # Add `out` to `o_tree` in the `cat` category
        if cat == '.':
            # Place output directly at the root level
            o_tree[out.name] = out
        else:
            cat = cat.split('/')
            node = o_tree
            for c in cat:
                if c not in node:
                    # New category
                    node[c] = {}
                node = node[c]
            node[out.name] = out

    def svg_to_png(self, svg_file, png_file, width):
        cmd = [self.rsvg_command, '-w', str(width), '-f', 'png', '-o', png_file, svg_file]
        return _run_command(cmd)

    def copy(self, img, width):
        """ Copy an SVG icon to the images/ dir.
            Tries to convert it to PNG. """
        img_w = "{}_{}".format(os.path.basename(img), width)
        if img_w in self.copied_images:
            # Already copied, just return its name
            return self.copied_images[img_w]
        src = os.path.join(self.img_src_dir, img+'.svg') if not img.endswith('.svg') else img
        dst = os.path.join(self.out_dir, 'images', img_w)
        id = img_w
        if self.rsvg_command is not None and self.svg_to_png(src, dst+'.png', width):
            img_w += '.png'
        else:
            copy2(src, dst+'.svg')
            img_w += '.svg'
        name = os.path.join('images', img_w)
        self.copied_images[id] = name
        return name

    def can_be_converted(self, ext):
        if ext in IMAGEABLES_SVG and self.rsvg_command is None:
            logger.warning(W_MISSTOOL+"Missing SVG to PNG converter")
            return False
        if ext in IMAGEABLES_GS and not self.ps2img_avail:
            logger.warning(W_MISSTOOL+"Missing PS/PDF to PNG converter")
            return False
        if ext in IMAGEABLES_SIMPLE and self.convert_command is None:
            logger.warning(W_MISSTOOL+"Missing ImageMagick converter")
            return False
        return ext in IMAGEABLES_SVG or ext in IMAGEABLES_GS or ext in IMAGEABLES_SIMPLE

    def compose_image(self, file, ext, img, out_name, no_icon=False):
        if not os.path.isfile(file):
            logger.warning(W_NOTYET+"{} not yet generated, using an icon".format(os.path.relpath(file)))
            return False, None, None
        if self.convert_command is None:
            return False, None, None
        # Create a unique name using the output name and the generated file name
        bfname = os.path.splitext(os.path.basename(file))[0]
        fname = os.path.join(self.out_dir, 'images', out_name+'_'+bfname+'.png')
        # Full path for the icon image
        icon = os.path.join(self.out_dir, img)
        if ext == 'pdf':
            # Only page 1
            file += '[0]'
        if ext == 'svg':
            tmp_name = GS.tmp_file(suffix='.png')
            logger.debug('Temporal convert: {} -> {}'.format(file, tmp_name))
            if not self.svg_to_png(file, tmp_name, BIG_ICON):
                return False, None, None
            file = tmp_name
        cmd = [self.convert_command, file,
               # Size for the big icons (width)
               '-resize', str(BIG_ICON)+'x']
        if ext == 'ps':
            # ImageMagick 6.9.11 (and also the one in Debian 11) rotates the PS
            cmd.extend(['-rotate', '90'])
        if not no_icon:
            cmd.extend([  # Add the file type icon
                        icon,
                        # At the bottom right
                        '-gravity', 'south-east',
                        # This is a composition, not 2 images
                        '-composite'])
        cmd.append(fname)
        res = _run_command(cmd)
        if ext == 'svg':
            logger.debug('Removing temporal {}'.format(tmp_name))
            os.remove(tmp_name)
        return res, fname, os.path.relpath(fname, start=self.out_dir)

    def get_image_for_file(self, file, out_name, no_icon=False, image=None):
        ext = os.path.splitext(file)[1][1:].lower()
        wide = False
        # Copy the icon for this file extension
        icon_name = 'folder' if os.path.isdir(file) else EXT_IMAGE.get(ext, 'unknown')
        img = self.copy(image or icon_name, MID_ICON)
        # Full name for the file
        file_full = file
        # Just the file, to display it
        file = os.path.basename(file)
        # The icon size
        height = width = MID_ICON
        # Check if this file can be represented by an image
        if self.can_be_converted(ext):
            # Try to compose the image of the file with the icon
            ok, fimg, new_img = self.compose_image(file_full, ext, img, 'cat_'+out_name, no_icon)
            if ok:
                # It was converted, replace the icon by the composited image
                img = new_img
                # Compute its size
                try:
                    _, width, height, _ = read_png(fimg, logger)
                except TypeError:
                    width = height = 0
                # We are using the big size
                wide = True
        # Now add the image with its file name as caption
        ext_img = '<img src="{}" alt="{}" width="{}" height="{}">'.format(img, file, width, height)
        file = ('<table class="out-img"><tr><td>{}</td></tr><tr><td class="{}">{}</td></tr></table>'.
                format(ext_img, 'td-normal' if no_icon else 'td-small', out_name if no_icon else file))
        return file, wide

    def add_nav_bar(self, f, prev):
        if self.nav_bar:
            f.write(SCRIPT_NAV_BAR)

    def write_head(self, f, title):
        f.write('<!DOCTYPE html>\n')
        f.write('<html lang="en">\n')
        f.write('<head>\n')
        f.write(' <title>{}</title>\n'.format(title if title else 'Main page'))
        f.write(' <meta charset="UTF-8">\n')  # UTF-8 encoding for unicode support
        f.write(' <link rel="stylesheet" href="styles.css">\n')
        f.write(' <link rel="icon" href="favicon.ico">\n')
        # Include Markdown-it
        f.write(' <script src="https://cdn.jsdelivr.net/npm/markdown-it/dist/markdown-it.min.js"></script>\n')
        f.write('</head>\n')
        f.write('<body>\n')
        f.write(self.sidenav)
        f.write(self.top_menu)
        f.write('<div id="main">\n')

    def generate_cat_page_for(self, name, node, prev, category):
        logger.debug('- Categories: ' + str(node.keys()))
        with open(os.path.join(self.out_dir, name), 'wt') as f:
            self.write_head(f, category)
            name, ext = os.path.splitext(name)

            # Start a vertically aligned container for categories
            f.write('<div class="categories-container">\n')

            for cat, content in node.items():
                if not isinstance(content, dict):
                    continue

                pname = name + '_' + cat + ext
                self.generate_page_for(content, pname, name, category + '/' + cat)

                # Wrap the entire box in the <a> tag to make it clickable
                f.write(f'''
                <a href="{pname}" class="category-box">
                    <span class="category-title">{cat}</span>
                </a>
                ''')

            # Close the container
            f.write('</div>\n')

            # Generate outputs below the categories
            self.generate_outputs(f, node)
            self.add_nav_bar(f, prev)
            f.write(SCRIPT)
            f.write('</body>\n</html>\n')

    def adjust_image_paths(self, md_content, current_dir, html_output_dir):
        """
        Adjusts image paths in markdown content to be relative to the HTML output directory.

        Args:
            md_content (str): Raw markdown content.
            current_dir (str): Directory of the markdown file.
            html_output_dir (str): Absolute directory where the HTML file is generated.

        Returns:
            str: Updated markdown content with adjusted image paths.
        """
        import re

        image_pattern = r'!\[.*?\]\((.*?)\)'  # Markdown image paths: ![Alt text](path/to/image.png)
        html_img_pattern = r'<img\s+[^>]*src="([^"]+)"'  # HTML img src="path/to/image.png"

        def replace_path(match):
            original_path = match.group(1)

            # Skip absolute URLs or paths
            if original_path.startswith(('http://', 'https://', '/')):
                return match.group(0)

            # Convert relative path to absolute and back to relative for the HTML output directory
            abs_path = os.path.abspath(os.path.join(current_dir, original_path))
            rel_path = os.path.relpath(abs_path, html_output_dir)

            # Replace the path with the new relative path
            return match.group(0).replace(original_path, rel_path)

        # Replace Markdown image paths
        md_content = re.sub(image_pattern, replace_path, md_content)

        # Replace HTML <img> tag paths
        md_content = re.sub(html_img_pattern, replace_path, md_content)

        return md_content

    def generate_outputs(self, f, node):
        """
        Generates the output table dynamically, grouping items into separate categories.
        Respects the `render_markdown` option for markdown files.
        """
        for oname, out in node.items():
            if isinstance(out, dict):
                continue  # Skip subcategories here, handled separately

            # Start a container for the category
            f.write(f'<div class="output-virtual-box" id="{oname}">\n')  # Virtual box used to hold id
            f.write('<div class="output-comment">{}</div>\n'.format(out.comment or oname))

            out_dir = get_output_dir(out.dir, out, dry=True)
            targets, icons = out.get_navigate_targets(out_dir)

            # Start the items container
            f.write('<div class="items-container">\n')

            for tg, icon in zip(targets, icons if icons else [None] * len(targets)):
                tg_rel = os.path.relpath(os.path.abspath(tg), start=self.out_dir)
                ext = os.path.splitext(tg)[1].lower()

                if ext == '.md' and self.render_markdown:  # Render markdown only if enabled
                    # Read markdown content
                    with open(tg, 'r', encoding='utf-8') as md_file:
                        md_content = md_file.read()

                    # Adjust image paths in markdown
                    md_content = self.adjust_image_paths(md_content, os.path.dirname(tg), self.out_dir)

                    # Embed raw markdown into a div
                    f.write(f'''
                        <div class="markdown-content" style="display: none;">{md_content}</div>
                    ''')
                else:
                    # Handle other files (icons, images, etc.)
                    img, wide = self.get_image_for_file(tg, oname, image=icon)

                    cell_class = "wide" if wide else ""

                    # Make the entire output-box clickable
                    f.write(f'''
                        <div class="output-box {cell_class}" onclick="location.href='{tg_rel}'">
                            <a href="{tg_rel}" class="filename">{img}</a>
                            <p class="output-name">{oname}</p>
                        </div>
                    ''')

            # Close the items container and category box
            f.write('</div>\n</div>\n')

    def generate_end_page_for(self, name, node, prev, category):
        logger.debug('- Outputs: '+str(node.keys()))
        with open(os.path.join(self.out_dir, name), 'wt') as f:
            self.write_head(f, category)
            name, ext = os.path.splitext(name)
            self.generate_outputs(f, node)
            self.add_nav_bar(f, prev)
            f.write(SCRIPT)
            f.write('</body>\n</html>\n')

    def generate_page_for(self, node, name, prev=None, category=''):
        logger.debug('Generating page for ' + name)
        self.top_menu = self.generate_top_menu(category)  # Update top menu with the current folder name
        if isinstance(list(node.values())[0], dict):
            self.generate_cat_page_for(name, node, prev, category)
        else:
            self.generate_end_page_for(name, node, prev, category)

    def get_targets(self, out_dir):
        # Listing all targets is too complex, we list the most relevant
        # This is good enough to compress the result
        name = self._parent.expand_filename(out_dir, self.output)
        files = [os.path.join(out_dir, 'images'),
                 os.path.join(out_dir, 'styles.css'),
                 os.path.join(out_dir, 'favicon.ico')]
        if self.link_from_root:
            files.append(os.path.join(GS.out_dir, self.link_from_root))
        self.out_dir = out_dir
        self.get_html_names(self.create_tree(), name, files)
        return files

    def get_html_names_cat(self, name, node, prev, category, files):
        files.append(os.path.join(self.out_dir, name))
        name, ext = os.path.splitext(name)
        for cat, content in node.items():
            if not isinstance(content, dict):
                continue
            pname = name+'_'+cat+ext
            self.get_html_names(content, pname, files, name, category+'/'+cat)

    def get_html_names(self, node, name, files, prev=None, category=''):
        if isinstance(list(node.values())[0], dict):
            self.get_html_names_cat(name, node, prev, category, files)
        else:
            files.append(os.path.join(self.out_dir, name))

    def create_tree(self):
        o_tree = {}
        BasePreFlight.configure_all()
        for n in BasePreFlight.get_in_use_names():
            pre = BasePreFlight.get_preflight(n)
            cat = force_list(pre.get_category())
            if not cat:
                continue
            for c in cat:
                self.add_to_tree(c, pre, o_tree)
        for o in RegOutput.get_outputs():
            if not o.run_by_default and self.skip_not_run:
                # Skip outputs that aren't generated in a regular run
                continue
            config_output(o)
            cat = o.category
            if cat is None:
                continue
            for c in cat:
                self.add_to_tree(c, o, o_tree)
        return o_tree

    def generate_sidenav_one(self, node, lvl, name, ext):
        indent = ' ' * lvl
        code = f"{indent}<ul class='sidenav-category'>\n"
        for k, v in node.items():
            if isinstance(v, dict):  # Folder (category)
                folder_id = f'folder-{name}-{k}'.replace(' ', '-').lower()
                code += (
                    f"{indent}  <li class='folder'>"
                    f"<span onclick='toggleFolder(this)'>"
                    f"<span class='chevron'></span> {k}</span>\n"
                    f"{indent}    <ul id='{folder_id}' class='folder-contents' style='display:none;'>\n"
                )
                code += self.generate_sidenav_one(v, lvl + 1, name + '_' + k, ext)
                code += f"{indent}    </ul>\n  </li>\n"
            else:  # File (output)
                code += f"{indent}  <li><a href='{name}{ext}#{v.name}' class='sidenav-output'>{v.name}</a></li>\n"
        code += f"{indent}</ul>\n"
        return code

    def generate_sidenav(self, node, name):
        name, ext = os.path.splitext(name)
        code = '''
        <div id="theSideNav" class="sidenav">
            <!-- Search bar with autocomplete -->
            <div id="search-container">
                <input type="text" id="search-bar" placeholder="Search outputs..." autocomplete="off">
                <ul id="autocomplete-list"></ul>
            </div>
        '''
        code += self.generate_sidenav_one(node, 0, name, ext)
        code += '</div>\n'
        code += """
        <script>
        document.addEventListener("DOMContentLoaded", function () {
            const searchBar = document.getElementById("search-bar");
            const autocompleteList = document.getElementById("autocomplete-list");
            const outputLinks = document.querySelectorAll(".sidenav-output");

            // Collect output names and their hrefs
            const outputs = Array.from(outputLinks).map(link => ({
                name: link.textContent.trim(),
                href: link.getAttribute("href")
            }));

            // Update autocomplete suggestions
            function updateAutocomplete(query) {
                // Clear previous suggestions
                autocompleteList.innerHTML = "";

                // Filter and display matching outputs
                const matches = outputs.filter(output =>
                    output.name.toLowerCase().includes(query.toLowerCase())
                );

                matches.forEach(match => {
                    const listItem = document.createElement("li");
                    listItem.textContent = match.name;
                    listItem.addEventListener("click", () => {
                        window.location.href = match.href; // Redirect to the selected output
                    });
                    autocompleteList.appendChild(listItem);
                });

                // Hide the list if there are no matches
                autocompleteList.style.display = matches.length ? "block" : "none";
            }

            // Add event listeners to the search bar
            searchBar.addEventListener("input", () => {
                const query = searchBar.value.trim();
                if (query) {
                    updateAutocomplete(query);
                } else {
                    autocompleteList.innerHTML = ""; // Clear suggestions
                    autocompleteList.style.display = "none";
                }
            });

            // Hide autocomplete list when clicking outside
            document.addEventListener("click", (event) => {
                if (!searchBar.contains(event.target) && !autocompleteList.contains(event.target)) {
                    autocompleteList.style.display = "none";
                }
            });
        });
        </script>
        """
        return code

    def generate_top_menu(self, category=''):
        """
        Generates the top menu with Back, Forward, Home, sidenav buttons, and a logo.
        Displays the current folder name dynamically next to the forward arrow with wrapping for '/'.
        Adds revision, variant, and company information.
        """
        fsize = f'{TITLE_HEIGHT}px'
        logo_height = f'{TITLE_HEIGHT}px'
        small_font_size = f'{int(TITLE_HEIGHT) - 8}px'  # Smaller font for revision/variant and company
        smallest_font_size = f'{int(TITLE_HEIGHT) - 16}px'
        code = '<div id="topmenu" class="topmenu">\n'
        code += '  <table style="width:100%; table-layout: fixed; height:100%;">\n'
        code += '    <tr style="vertical-align: middle;">\n'

        # Left-aligned section (sidenav button, Back/Forward buttons, and category path)
        code += '      <td style="width: 33%;" align="left">\n'
        if self.nav_bar:
            code += f'        <span id="open-sidenav" style="font-size:{fsize};cursor:pointer" onclick="openNav()">&#9776;</span>\n'
            code += f'        <span id="close-sidenav" style="font-size:{fsize};cursor:pointer;display:none;" onclick="closeNav()">⨉</span>\n'
        code += f'        <button id="back-button" onclick="history.back()" style="font-size:{fsize};">↩</button>\n'
        code += f'        <button id="forward-button" onclick="history.forward()" style="font-size:{fsize};">↪</button>\n'

        # Display the current folder name (category path)
        if category:  # Display the current folder name
            code += f'''
            <span style="
                font-size:{small_font_size};
                margin-left: 10px;
                color: var(--text-color-accent); /* Use dynamic variable */
                position: relative;
                top: -5px; /* Add -5px vertical offset */
                white-space: normal; /* Allow wrapping */
                word-break: keep-all; /* Prevent breaking at arbitrary places */
                overflow-wrap: normal; /* Allow wrapping only where explicitly defined */
            ">
                {category.lstrip('/').replace('/', '/<wbr>')}
            </span>
            '''
        code += '      </td>\n'

        # Centered title with company below
        code += '      <td style="width: 33%;" align="center">\n'
        if self._solved_title:
            if self.title_url:
                code += f'        <a href="{self.title_url}" style="text-decoration: none; color: inherit;">\n'
            code += f'        <span style="font-size:{fsize};">{self._solved_title}</span>\n'
            if self.title_url:
                code += '        </a>\n'
        # Add company information
        code += f'''
            <div style="
                font-size:{smallest_font_size};
                color: var(--text-color-accent);
                text-align: center;
                margin-top: 5px;">
                {self._solved_company}
            </div>
        '''
        code += '      </td>\n'

        # Right-aligned section (Logo, Revision/Variant, Toggle, and Home button)
        code += '      <td style="width: 33%;" align="right">\n'

        # Revision and Variant
        code += f'''
            <div style="
                display: inline-block;
                text-align: left;
                position: relative;
                top: 5px; /* Add 5px vertical offset */
                font-size:{smallest_font_size};
                color: var(--text-color-accent);
                margin-right: 20px; /* Space to the left of the logo */
            ">
                <div style="margin-bottom: 5px;">Rev. {self._solved_revision}</div>
                Variant: {self._variant_name}
            </div>
        '''

        # Add the logo
        if self.logo is not None:
            img_name = os.path.join('images', 'logo.png')
            if self.logo_url:
                code += f'        <a href="{self.logo_url}" style="margin-right: 10px;">\n'
            code += f'        <img src="{img_name}" alt="Logo" style="max-height: {logo_height}; vertical-align: middle; display: inline-block; position: relative; top: -5px;">\n'
            if self.logo_url:
                code += '        </a>\n'

        # Add the toggle
        code += '''
            <label class="theme-switch">
                <input type="checkbox" id="themeToggle" onchange="toggleTheme()">
                <span></span>
            </label>
        '''
        code += f'        <button id="home-button" onclick="location.href=\'{self.home}\'" style="font-size:{fsize};">🏠︎</button>\n'
        code += '      </td>\n'

        code += '    </tr>\n'
        code += '  </table>\n'
        code += '</div>\n'
        return code

    def solve_title(self):
        base_title = None
        if GS.sch:
            base_title = GS.sch.get_title()
        if GS.board and not base_title:
            tb = GS.board.GetTitleBlock()
            base_title = tb.GetTitle()
        if not base_title:
            base_title = GS.pro_basename or GS.sch_basename or GS.pcb_basename or 'Unknown'
        text = self.expand_filename_sch(self.title if self.title else '+')
        if text[0] == '+':
            text = base_title+text[1:]
        self._solved_title = text
        # Now the URL
        if self.title_url is not None and not self.title_url:
            # Empty but not None
            self._git_command = self.check_tool('Git')
            if self._git_command:
                res = ''
                try:
                    res = run_command([self._git_command, 'remote', 'get-url', 'origin'], just_raise=True)
                except subprocess.CalledProcessError:
                    pass
                if res:
                    self.title_url = res

    def solve_revision(self):
        base_rev = None
        if GS.sch:
            GS.load_sch()
            GS.load_sch_title_block()
            base_rev = GS.sch_rev
        if GS.board and not base_rev:
            tb = GS.board.GetTitleBlock()
            base_rev = tb.GetRevision()
        if not base_rev:
            base_rev = 'Unknown'
        self._solved_revision = base_rev

    def solve_company(self):
        base_comp = None
        if GS.sch:
            GS.load_sch()
            GS.load_sch_title_block()
            base_comp = GS.sch_comp
        if GS.board and not base_comp:
            tb = GS.board.GetTitleBlock()
            base_comp = tb.GetCompany()
        if not base_comp:
            base_comp = 'Unknown'
        self._solved_company = base_comp

    def run(self, name):
        self.out_dir = os.path.dirname(name)
        self.img_src_dir = GS.get_resource_path('images')
        self.img_dst_dir = os.path.join(self.out_dir, 'images')
        os.makedirs(self.img_dst_dir, exist_ok=True)
        self.copied_images = {}
        name = os.path.basename(name)
        # Create a tree with all the outputs
        o_tree = self.create_tree()
        logger.debug('Collected outputs:\n'+pprint.pformat(o_tree))
        if not o_tree:
            logger.warning(W_NOOUTPUTS+'No outputs for navigate results')
            return
        with open(os.path.join(self.out_dir, 'styles.css'), 'wt') as f:
            top_margin = TITLE_HEIGHT
            f.write(STYLE.replace('@TOP_MAR@', str(top_margin)))
        self.rsvg_command = self.check_tool('rsvg1')
        self.convert_command = self.check_tool('ImageMagick')
        self.ps2img_avail = self.check_tool('Ghostscript')
        # Create the pages
        self.home = name
        self.back_img = self.copy('back', MID_ICON)
        self.home_img = self.copy('home', MID_ICON)
        copy2(os.path.join(self.img_src_dir, 'favicon.ico'), os.path.join(self.out_dir, 'favicon.ico'))
        # Copy the logo image
        if self.logo is not None:
            with open(os.path.join(self.out_dir, 'images', 'logo.png'), 'wb') as f:
                f.write(self._logo_data)
        self.solve_title()
        self.solve_revision()
        self.solve_company()
        self.sidenav = self.generate_sidenav(o_tree, name) if self.nav_bar else ''
        self.top_menu = self.generate_top_menu()
        self.generate_page_for(o_tree, name)
        # Link it?
        if self.link_from_root:
            redir_file = os.path.join(GS.out_dir, self.link_from_root)
            rel_start = os.path.relpath(os.path.join(self.out_dir, name), start=GS.out_dir)
            logger.debug('Creating redirector: {} -> {}'.format(redir_file, rel_start))
            with open(redir_file, 'wt') as f:
                f.write('<html>\n<head>\n<meta http-equiv="refresh" content="0; {}"/>'.format(rel_start))
                f.write('</head>\n</html>')


@output_class
class Navigate_Results_Modern(BaseOutput):  # noqa: F821
    """ Navigate Results
        Generates a web page to navigate the generated outputs """
    def __init__(self):
        super().__init__()
        # Make it low priority so it gets created after all the other outputs
        self.priority = 10
        with document:
            self.options = Navigate_Results_ModernOptions
            """ *[dict={}] Options for the `navigate_results_modern` output """
        # The help is inherited and already mentions the default priority
        self.fix_priority_help()
        self._any_related = True

    @staticmethod
    def get_conf_examples(name, layers):
        outs = BaseOutput.simple_conf_examples(name, 'Web page to browse the results', 'Browse')  # noqa: F821
        outs[0]['options'] = {'link_from_root': 'index.html', 'skip_not_run': True}
        return outs
