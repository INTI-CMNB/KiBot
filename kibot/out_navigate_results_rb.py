# -*- coding: utf-8 -*-
# Copyright (c) 2022-2025 Salvador E. Tropea
# Copyright (c) 2022-2025 Nguyen Vincent
# Copyright (c) 2022-2025 Instituto Nacional de Tecnología Industrial
# Contributed by Nguyen Vincent (@nguyen-v)
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)
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
import os
from .registrable import RegOutput
from .out_any_navigate_results import Any_Navigate_ResultsOptions, CAT_IMAGE, EXT_IMAGE, CAT_REP
from .macros import macros, document, output_class  # noqa: F401
from .kiplot import get_output_dir
from .misc import read_png
from . import log

logger = log.get_logger()

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

button, #open-navbar, #close-navbar {
    background: none;
    border: none;
    color: var(--dark-text-color);
    cursor: pointer;
    transition: color 0.3s ease;
    user-select: none;
}

body.light-mode #topmenu button,
body.light-mode #topmenu #open-navbar,
body.light-mode #topmenu #close-navbar {
    color: var(--light-text-color);
}

body.dark-mode #topmenu button,
body.dark-mode #topmenu #open-navbar,
body.dark-mode #topmenu #close-navbar {
    color: var(--dark-text-color);
}

button {
    font-size: 20px;
    margin: 0 10px;
}

#open-navbar, #close-navbar {
    width: 36px;
    height: 36px;
    line-height: 36px;
    text-align: center;
    font-size: 28px;
    margin-left: 15px;
}

/* Hover effects */

button:hover, #open-navbar:hover, #close-navbar:hover {
    color: var(--dark-hover-color);
}

body.dark-mode #topmenu button:hover,
body.dark-mode #topmenu #open-navbar:hover,
body.dark-mode #topmenu #close-navbar:hover {
    color: var(--dark-hover-color);
}

body.light-mode #topmenu button:hover,
body.light-mode #topmenu #open-navbar:hover,
body.light-mode #topmenu #close-navbar:hover {
    color: var(--light-hover-color);
}

/* Active effects */

button:active, #open-navbar:active, #close-navbar:active {
    color: var(--dark-hover-color-act);
    transition: none;
}

body.dark-mode #topmenu button:active,
body.dark-mode #topmenu #open-navbar:active,
body.dark-mode #topmenu #close-navbar:active {
    color: var(--dark-hover-color-act);
}

body.light-mode #topmenu button:active,
body.light-mode #topmenu #open-navbar:active,
body.light-mode #topmenu #close-navbar:active {
    color: var(--light-hover-color-act);
}

/* Sidebar Navigation ======================================================= */

.navbar {
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
    padding-bottom: 40px;
}


body.dark-mode .navbar {
    background-color: var(--dark-bg-color-banner);
}

body.light-mode .navbar {
    background-color: var(--light-bg-color-banner);
}

.navbar > ul:first-child {
    margin-top: 20px; /* Padding between top menu and first element of navbar */
}

/* Side Navigation Outputs -------------------------------------------------- */

.navbar-output {
    padding: 8px 30px;
    text-decoration: none;
    font-size: 16px;
    color: var(--dark-text-color);
    display: block;
    transition: color 0.3s ease;
    border-radius: 4px;
}

body.light-mode .navbar-output {
    color: var(--light-text-color);
}

body.dark-mode .navbar-output {
    color: var(--dark-text-color);
}

/* Hover effects */

.navbar-output:hover {
    color: var(--dark-hover-color);
    background-color: var(--dark-banner-hover);
}

body.dark-mode .navbar-output:hover {
    color: var(--dark-hover-color);
    background-color: var(--dark-banner-hover);
}

body.light-mode .navbar-output:hover {
    color: var(--light-hover-color);
    background-color: var(--light-banner-hover);
}

/* Active effects */

.navbar-output:active {
    color: var(--dark-hover-color-act);
}

body.dark-mode .navbar-output:active {
    color: var(--dark-hover-color-act);
}

body.light-mode .navbar-output:active {
    color: var(--light-hover-color-act);
}

/* Side Navigation Categories ----------------------------------------------- */

.navbar-category {
    list-style: none;
    padding: 0;
    margin: 0;
    user-select: none; /* Prevent text selection */
}

.navbar-category .folder > span {
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

.navbar-category .folder-contents {
    list-style: none;
    margin-left: 20px;
    padding: 0;
}

body.dark-mode .navbar-category .folder > span {
    color: var(--dark-text-color-accent);
}

body.light-mode .navbar-category .folder > span {
    color: var(--light-text-color);
}

/* Hover effects */

.navbar-category .folder > span:hover {
    background-color: var(--dark-banner-hover);
    color: var(--dark-hover-color);
}

body.dark-mode .navbar-category .folder > span:hover {
    color: var(--dark-hover-color);
    background-color: var(--dark-banner-hover);
}

body.light-mode .navbar-category .folder > span:hover {
    color: var(--light-hover-color);
    background-color: var(--light-banner-hover);
}

/* Active effects */

.navbar-category .folder > span:active {
    color: var(--dark-hover-color);
    transition: none;
}

body.dark-mode .navbar-category .folder > span:active {
    color: var(--dark-hover-color-act);
}

body.light-mode .navbar-category .folder > span:active {
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

/* Kibot version ------------------------------------------------------------ */

.generator {
    text-align: right;
    font-size: 0.6em;
    text-decoration: none;
}

.generator a {
    text-decoration: none; /* Removes the underline */
}

/* Dark Mode: Regular Text */
body.dark-mode .generator {
    color: var(--dark-text-color-accent);
}

/* Dark Mode: Hyperlinks */
body.dark-mode .generator a {
    color: var(--dark-hover-color); /* Hyperlink */
}

/* Light Mode: Regular Text */
body.light-mode .generator {
    color: var(--light-text-color-accent);
}

/* Light Mode: Hyperlinks */
body.light-mode .generator a {
    color: var(--light-hover-color); /* Hyperlink */
}

/* Category boxes (folder) -------------------------------------------------- */

.category-box {
    z-index: 1000;
    background-color: var(--dark-bg-color-banner);
    border: 1px solid var(--dark-bg-color-banner);
    border-radius: 8px;
    padding: 16px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    width: 400px;
    height: 140;
    text-decoration: none;
    transition: background-color 0.3s ease, transform 0.2s ease;
    margin-bottom: 0px;
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

.category-box img {
    margin-top: 10px;
    max-width: 100%;
    max-height: 100%;
    height: auto;
    margin-bottom: 10px;
}

.category-title {
    font-size: 1.4em;
    font-weight: 500;
    text-align: center;
    color: #e5e5e5;
    text-decoration: none;
    display: inline-block;
    margin-top: 0px;
    margin-bottom: 0px;
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
    z-index: 999;
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
    pointer-events: none; /* Make it non-interactive */
}

.output-virtual-box > * {
    pointer-events: auto; /* Allow its children to remain interactive */
}

/* Some files (e.g. PDF, PNG) have wider output boxes */

.output-box.wide {
    width: 400px;
    height: auto;
}

.output-box img {
    margin-top: 10px;
    max-width: 100%;
    max-height: 100%;
    height: auto;
    margin-bottom: 0px;
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
    margin-top: 0px;
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
    margin-bottom: 7px;
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

body.dark-mode .navbar {
    scrollbar-color: var(--dark-banner-hover) var(--dark-bg-color);
}

body.light-mode .navbar {
    scrollbar-color: var(--light-banner-hover) var(--light-bg-color);
}

/* WebKit Scrollbar Styles */
body::-webkit-scrollbar, .navbar::-webkit-scrollbar {
    width: 12px;
    height: 12px;
}

body::-webkit-scrollbar-thumb, .navbar::-webkit-scrollbar-thumb {
    border-radius: 6px;
    background: var(--dark-banner-hover);
    border: 2px solid var(--dark-bg-color);
}

body::-webkit-scrollbar-track, .navbar::-webkit-scrollbar-track {
    border-radius: 6px;
    background: var(--dark-bg-color);
}

body.dark-mode::-webkit-scrollbar-thumb:hover, .navbar.dark-mode::-webkit-scrollbar-thumb:hover {
    background: #44475a !important;
}

body.light-mode::-webkit-scrollbar-thumb, .navbar.light-mode::-webkit-scrollbar-thumb {
    background: var(--light-banner-hover);
    border: 2px solid var(--light-bg-color);
}

body.light-mode::-webkit-scrollbar-track, .navbar.light-mode::-webkit-scrollbar-track {
    background: var(--light-bg-color);
}

body.light-mode::-webkit-scrollbar-thumb:hover, .navbar.light-mode::-webkit-scrollbar-thumb:hover {
    background: #909090 !important;
}

body::-webkit-scrollbar-corner, .navbar::-webkit-scrollbar-corner {
    background: var(--dark-bg-color);
}

/* Markdown ================================================================= */

.markdown-content {
    font-family: Roboto, sans-serif;
    line-height: 1.6;
    padding: 15px;
    border-radius: 5px;
    max-width: calc(100% - 180px);
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

.markdown-content pre::-webkit-scrollbar {
    height: 12px; /* Horizontal scrollbar height */
}

.markdown-content pre::-webkit-scrollbar-thumb {
    background: var(--dark-banner-hover); /* Match other scrollbar thumb color */
    border-radius: 6px; /* Round edges */
    border: 2px solid var(--dark-bg-color); /* Outer border matches background */
}

.markdown-content pre::-webkit-scrollbar-track {
    background: var(--dark-bg-color); /* Match the background color */
    border-radius: 6px;
}

body.light-mode .markdown-content pre::-webkit-scrollbar-thumb {
    background: var(--light-banner-hover); /* Light mode thumb color */
    border: 2px solid var(--light-bg-color); /* Light mode border */
}

body.light-mode .markdown-content pre::-webkit-scrollbar-track {
    background: var(--light-bg-color); /* Light mode track background */
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

.highlighted {
    background-color: var(--light-banner-hover); /* Same as hover background */
    color: var(--light-hover-color); /* Same as hover text color */
}

body.dark-mode .highlighted {
    background-color: var(--dark-banner-hover); /* Same as hover background */
    color: var(--dark-hover-color); /* Same as hover text color */
}

/* New classes to remove transitions on page load =========================== */

body.no-transition,
.no-transition .output-box,
body.no-transition .theme-switch span,
body.no-transition button,
body.no-transition #close-navbar,
body.no-transition #home-button,
body.no-transition #back-button,
body.no-transition #forward-button,
body.no-transition #topmenu,
body.no-transition .navbar-category .folder > span,
body.no-transition .navbar-output,
body.no-transition .category-box,
#search-bar {
    transition: none !important; /* Disable transition during page load */
}

"""
SCRIPT_NAV_BAR = """
<script>

// Side Navigation functions ===================================================

function openNav() {
    const navbar = document.getElementById("theSideNav");
    const main = document.getElementById("main");

    navbar.style.width = "360px";
    navbar.style.paddingLeft = "20px";
    main.style.marginLeft = "360px";
    document.getElementById("open-navbar").style.display = "none";
    document.getElementById("close-navbar").style.display = "inline-block";
}

function closeNav() {
    const navbar = document.getElementById("theSideNav");
    const main = document.getElementById("main");

    navbar.style.width = "0"; // Close the navbar
    navbar.style.paddingLeft = "0"; // Reset padding
    main.style.marginLeft = "0"; // Reset page content position
    document.getElementById("open-navbar").style.display = "inline-block";
    document.getElementById("close-navbar").style.display = "none";
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
    const navbar = document.getElementById("theSideNav");
    const isOpen = navbar.style.width !== "0px"; // Check if navbar is open

    // Save the state of each folder
    const folderStates = Array.from(document.querySelectorAll(".folder")).map(folder => ({
        id: folder.querySelector("span").textContent.trim(), // Use folder name as identifier
        isOpen: folder.classList.contains("open") // Check if folder is open
    }));

    // Save the navbar and folder states to localStorage
    localStorage.setItem("navbarState", JSON.stringify({ isOpen, folderStates }));
}

function restorenavbarState() {
    const savedState = localStorage.getItem("navbarState");
    if (savedState) {
        const { isOpen, folderStates } = JSON.parse(savedState);
        const navbar = document.getElementById("theSideNav");
        const main = document.getElementById("main");

        // Temporarily disable animations on page load so elements don't move
        navbar.style.transition = "none";
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
            navbar.style.transition = "";
            main.style.transition = "";
            chevrons.forEach(chevron => {
                chevron.style.transition = "";
            });
        }, 100);
    }
}

function saveSidenavScrollPosition() {
    const navbar = document.getElementById("theSideNav");
    const scrollPosition = navbar.scrollTop;
    localStorage.setItem("navbarScrollPosition", scrollPosition);
}

function restoreSidenavScrollPosition() {
    const navbar = document.getElementById("theSideNav");
    const savedPosition = localStorage.getItem("navbarScrollPosition");
    if (savedPosition !== null) {
        navbar.scrollTop = parseInt(savedPosition, 10);
    }
}

function adjustSidenavOffset() {
    const topMenu = document.getElementById("topmenu");
    const navbar = document.getElementById("theSideNav");

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
document.addEventListener("DOMContentLoaded", restorenavbarState);

function initializeSearchBar(searchContainerId, outputSelector) {
    const searchContainer = document.getElementById(searchContainerId);
    if (!searchContainer) return; // Exit if container is not found

    const searchBar = searchContainer.querySelector('#search-bar');
    const autocompleteList = searchContainer.querySelector('#autocomplete-list');
    const outputLinks = document.querySelectorAll(outputSelector);

    // Collect output names and their hrefs
    const outputs = Array.from(outputLinks).map(link => ({
        name: link.textContent.trim(),
        href: link.getAttribute("href"),
    }));

    let highlightedIndex = -1; // Index of the currently highlighted item

    function adjustAutocompleteWidth() {
        const searchBarWidth = searchBar.offsetWidth;
        autocompleteList.style.width = `${searchBarWidth}px`;
    }

    function updateAutocomplete(query) {
        autocompleteList.innerHTML = ""; // Clear suggestions
        highlightedIndex = -1; // Reset highlighting

        const matches = outputs.filter(output =>
            output.name.toLowerCase().includes(query.toLowerCase())
        );

        matches.forEach(match => {
            const listItem = document.createElement("li");
            listItem.textContent = match.name;
            listItem.addEventListener("click", () => {
                window.location.href = match.href;
            });
            autocompleteList.appendChild(listItem);
        });

        autocompleteList.style.display = matches.length ? "block" : "none";
    }

    function highlightItem(index) {
        const items = autocompleteList.querySelectorAll("li");
        items.forEach((item, i) => {
            if (i === index) {
                item.classList.add("highlighted");
                item.scrollIntoView({ block: "nearest" });
            } else {
                item.classList.remove("highlighted");
            }
        });
    }

    // Add event listeners for search bar input and keydown
    searchBar.addEventListener("input", () => {
        const query = searchBar.value.trim();
        if (query) updateAutocomplete(query);
        else {
            autocompleteList.innerHTML = "";
            autocompleteList.style.display = "none";
        }
    });

    searchBar.addEventListener("keydown", (event) => {
        const items = autocompleteList.querySelectorAll("li");
        if (!items.length) return;

        if (event.key === "ArrowDown") {
            event.preventDefault();
            highlightedIndex = (highlightedIndex + 1) % items.length;
            highlightItem(highlightedIndex);
        } else if (event.key === "ArrowUp") {
            event.preventDefault();
            highlightedIndex = (highlightedIndex - 1 + items.length) % items.length;
            highlightItem(highlightedIndex);
        } else if (event.key === "Enter" && highlightedIndex >= 0) {
            event.preventDefault();
            items[highlightedIndex].click();
        }
    });

    // Hide suggestions when clicking outside
    document.addEventListener("click", (event) => {
        if (!searchBar.contains(event.target) && !autocompleteList.contains(event.target)) {
            autocompleteList.style.display = "none";
        }
    });

    // Adjust width on window resize
    adjustAutocompleteWidth();
    window.addEventListener("resize", adjustAutocompleteWidth);
}

// Initialize search functionality
document.addEventListener("DOMContentLoaded", () => {
    initializeSearchBar("search-container", ".navbar-output");
});

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
</script>
"""

SCRIPT_MARKDOWN = """
<script>
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
</script>
"""


class Navigate_Results_RBOptions(Any_Navigate_ResultsOptions):
    def __init__(self):
        super().__init__()
        self.header = True
        self._style = STYLE
        self._big_icon = 512
        self.logo_force_height = 50
        self.add_to_doc('logo_force_height', 'Using -1 a default height of 50 is used')

    def get_image_for_cat(self, cat, pname):
        if self.display_category_images:
            img = None
            if cat in CAT_REP and self.convert_command is not None:
                outs_rep = CAT_REP[cat]
                rep_file = None
                # Look in all outputs
                for o in RegOutput.get_outputs():
                    if not o.run_by_default and self.skip_not_run:
                        # Skip outputs that aren't generated in a regular run
                        continue
                    if o.type in outs_rep:
                        out_dir = get_output_dir(o.dir, o, dry=True)
                        targets = o.get_targets(out_dir)
                        for tg in targets:
                            ext = os.path.splitext(tg)[1][1:].lower()
                            if os.path.isfile(tg) and self.can_be_converted(ext):
                                rep_file = tg
                                break
                        if rep_file:
                            break
                if rep_file:
                    cat_img, _ = self.get_image_for_file(rep_file, cat, no_icon=True, is_category=True, category_path=pname)
                    return cat_img

            if cat in CAT_IMAGE:
                img = self.copy(CAT_IMAGE[cat], self._big_icon)
                # Include the category name with the category-title class
                cat_img = (
                    f'''<div class="category-box" onclick="location.href='{pname}'">'''
                    f'  <img src="{img}" alt="{cat}" width="{self._big_icon}" height="{self._big_icon}">'
                    f'  <p class="category-title">{cat}</p>'
                    f'</div>'
                )
                return cat_img

        return (f'''
        <div class="category-box" onclick="location.href='{pname}'">
            <p class="category-title">{cat}</p>
        </div>
        ''')  # Fallback if no image

    def get_image_for_file(self, file, out_name, no_icon=False, is_category=False, category_path='', image=None):
        tg_rel = os.path.relpath(os.path.abspath(file), start=self.out_dir)
        ext = os.path.splitext(file)[1][1:].lower()
        wide = False
        # Copy the icon for this file extension
        icon_name = 'folder' if os.path.isdir(file) else EXT_IMAGE.get(ext, 'unknown')
        img = self.copy(image or icon_name, self._mid_icon)
        # Full name for the file
        file_full = file
        # Just the file, to display it
        file = os.path.basename(file)
        # The icon size
        height = width = self._mid_icon
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
        # file = ('<table class="out-img"><tr><td>{}</td></tr><tr><td class="{}">{}</td></tr></table>'.
        #         format(ext_img, 'td-normal' if no_icon else 'td-small', out_name if no_icon else file))

        cell_class = "wide" if wide else ""

        # Make the entire output-box clickable
        file_name = file
        if is_category:
            file = f'''\n        <div class="category-box" onclick="location.href='{category_path}'">\n'''
        else:
            file = f'''\n        <div class="output-box {cell_class}" onclick="location.href='{tg_rel}'">\n'''

        file += (f'''            {ext_img}\n''')

        if is_category:
            file += (f'''            <p class="category-title">{out_name}</p>\n''')
        else:
            file += (f'''            <p class="filename">{file_name}</p>\n''')
            file += (f'''            <p class="output-name">{out_name}</p>\n''')

        file += '''        </div>\n'''
        return file, wide

    def generate_cat_page_for(self, name, node, prev, category):
        logger.debug('- Categories: ' + str(node.keys()))
        with open(os.path.join(self.out_dir, name), 'wt') as f:
            self.write_head(f, category)
            name, ext = os.path.splitext(name)

            f.write('<div class="items-container">\n')
            # f.write('<div>\n')

            for cat, content in node.items():
                if not isinstance(content, dict):
                    continue

                pname = name + '_' + cat + ext
                self.generate_page_for(content, pname, name, category + '/' + cat)

                # f.write('''<div onclick="location.href='{}'">{}</div>'''.format(pname, self.get_image_for_cat(cat)))
                f.write('''<div>{}</div>'''.format(self.get_image_for_cat(cat, pname)))

            # f.write('</div>\n')
            f.write('</div>\n')

            # Generate outputs below the categories
            self.generate_outputs(f, node)
            if self.nav_bar:
                f.write(SCRIPT_NAV_BAR)
            if self.render_markdown:
                f.write(SCRIPT_MARKDOWN)
            f.write(SCRIPT)
            self.write_kibot_version(f)
            f.write('</body>\n</html>\n')

    def generate_outputs(self, f, node):
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
                    output_cell, wide = self.get_image_for_file(tg, oname, image=icon)

                    f.write(output_cell)

            # Close the items container and category box
            f.write('</div>\n</div>\n')

    def generate_end_page_for(self, name, node, prev, category):
        logger.debug('- Outputs: '+str(node.keys()))
        with open(os.path.join(self.out_dir, name), 'wt') as f:
            self.write_head(f, category)
            name, ext = os.path.splitext(name)
            self.generate_outputs(f, node)
            if self.nav_bar:
                f.write(SCRIPT_NAV_BAR)
            if self.render_markdown:
                f.write(SCRIPT_MARKDOWN)
            f.write(SCRIPT)
            self.write_kibot_version(f)
            f.write('</body>\n</html>\n')

    def generate_page_for(self, node, name, prev=None, category=''):
        logger.debug('Generating page for ' + name)
        self.top_menu = self.generate_top_menu(category)  # Update top menu with the current folder name
        if isinstance(list(node.values())[0], dict):
            self.generate_cat_page_for(name, node, prev, category)
        else:
            self.generate_end_page_for(name, node, prev, category)

    def generate_navbar_one(self, node, lvl, name, ext):
        indent = ' ' * lvl
        code = f"{indent}<ul class='navbar-category'>\n"
        for k, v in node.items():
            if isinstance(v, dict):  # Folder (category)
                folder_id = f'folder-{name}-{k}'.replace(' ', '-').lower()
                code += (
                    f"{indent}  <li class='folder'>"
                    f"<span onclick='toggleFolder(this)'>"
                    f"<span class='chevron'></span> {k}</span>\n"
                    f"{indent}    <ul id='{folder_id}' class='folder-contents' style='display:none;'>\n"
                )
                code += self.generate_navbar_one(v, lvl + 1, name + '_' + k, ext)
                code += f"{indent}    </ul>\n  </li>\n"
            else:  # File (output)
                code += f"{indent}  <li><a href='{name}{ext}#{v.name}' class='navbar-output'>{v.name}</a></li>\n"
        code += f"{indent}</ul>\n"
        return code

    def generate_navbar(self, node, name):
        name, ext = os.path.splitext(name)
        code = '''
        <div id="theSideNav" class="navbar">
            <!-- Search bar container -->
            <div id="search-container">
                <input type="text" id="search-bar" placeholder="Search outputs..." autocomplete="off">
                <ul id="autocomplete-list"></ul>
            </div>
        '''
        code += self.generate_navbar_one(node, 0, name, ext)
        code += '</div>\n'
        return code

    def generate_top_menu(self, category=''):
        """
        Generates the top menu with clickable category paths and an up arrow button
        that navigates to the root page if the current path is the category name.
        """
        fsize = f'{self._title_height}px'
        fsize_up = f'{self._title_height+14}px'
        small_font_size = f'{int(self._title_height) - 12}px'
        smallest_font_size = f'{int(self._title_height) - 16}px'

        code = '''
        <div id="topmenu" class="topmenu">
        '''

        # Left Section (Buttons + Path)
        code += '<div style="display: flex; align-items: center; flex: 1; min-width: 0; gap: 10px;">\n'
        if self.nav_bar:
            code += (f'<span id="open-navbar" style="font-size:{fsize};cursor:pointer;" '
                     f'onclick="openNav()">&#9776;</span>\n')
            code += (f'<span id="close-navbar" style="font-size:{fsize};cursor:pointer;display:none;" '
                     f'onclick="closeNav()">⨉</span>\n')
        code += f'<button id="back-button" onclick="history.back()" style="font-size:{fsize};">↩</button>\n'
        code += f'<button id="forward-button" onclick="history.forward()" style="font-size:{fsize};">↪</button>\n'

        # Up and Home Buttons
        parent_path = '/'.join(category.strip('/').split('/')[:-1]) if category else None
        if parent_path is not None:
            target_file = self.get_html_names_for_path(parent_path, *os.path.splitext(self.home)) if parent_path else self.home
            code += (f'<button id="up-button" onclick="location.href=\'{target_file}\'" '
                     f'style="font-size:{fsize_up}; position: relative; top: -3px;">⌅</button>\n')
        else:
            code += (
                f'<button id="up-button" disabled '
                f'style="font-size:{fsize_up}; color: gray; cursor: not-allowed; '
                f'position: relative; top: -3px;">'
                '⌅</button>\n'
            )

        code += (
            f'<button id="home-button" onclick="location.href=\'{self.home}\'" '
            f'style="font-size:{self._title_height-5}px; position: relative; top: -2px;">'
            '🏠︎</button>\n'
        )

        # Category Path
        if category:
            path_parts = category.lstrip('/').split('/')
            path_links = []
            current_path = ''
            name, ext = os.path.splitext(self.home)
            for part in path_parts:
                current_path += f'{part}/'
                html_file_name = self.get_html_names_for_path(current_path.rstrip('/'), name, ext)
                path_links.append(f'<a href="{html_file_name}" style="text-decoration:none;color:inherit;">{part}</a>')
            clickable_path = '/<wbr>'.join(path_links)
            code += f'''
            <span style="
                font-size:{small_font_size};
                color: var(--text-color-accent);
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
                flex: 1;
            ">
                {clickable_path}
            </span>\n'''

        code += '</div>\n'

        # Center Section (Title + Company Name)
        code += '<div style="text-align: center; flex: 1; min-width: 200px;">\n'
        if self._solved_title:
            if self.title_url:
                code += f'<a href="{self.title_url}" style="text-decoration: none; color: inherit;">\n'
            code += f'<span style="font-size:{fsize};">{self._solved_title}</span>\n'
            if self.title_url:
                code += '</a>\n'
        code += f'''
            <div style="
                font-size:{smallest_font_size};
                color: var(--text-color-accent);
                margin-top: 5px;">
                {self._solved_company}
            </div>
        '''
        code += '</div>\n'

        # Right Section (Logo, Revision/Variant, Theme Toggle)
        code += (
            '<div style="display: flex; align-items: center; flex: 1; '
            'justify-content: flex-end; min-width: 0; gap: 10px; '
            'padding-right: 10px;">\n'
        )
        code += f'''
            <div style="
                text-align: left;
                font-size:{smallest_font_size};
                margin-right: 10px;
                color: var(--text-color-accent);">
                <div style="margin-bottom: 5px;">Rev. {self._solved_revision}</div>
                <div>Variant: {self._variant_name}</div>
            </div>\n'''
        if self.logo is not None:
            img_name = os.path.join('images', 'logo.png')
            if self.logo_url:
                code += f'<a href="{self.logo_url}" style="margin-right: 10px;">\n'
            code += (f'<img src="{img_name}" alt="Logo" '
                     f'style="max-height: {str(self._logo_h)}px; max-width: {str(self._logo_w)}px;">\n')
            if self.logo_url:
                code += '</a>\n'

        # Move the Theme Toggle Left
        code += '''
            <label class="theme-switch" style="
                position: relative;
                margin-right: 10px; /* Move toggle slightly left */
                max-width: 100%; /* Prevent overflow */
            ">
                <input type="checkbox" id="themeToggle" onchange="toggleTheme()">
                <span></span>
            </label>
        '''
        code += '</div>\n'
        code += '</div>\n'
        return code


@output_class
class Navigate_Results_RB(BaseOutput):  # noqa: F821
    """ Navigate Results
        Generates a web page to navigate the generated outputs """
    def __init__(self):
        super().__init__()
        # Make it low priority so it gets created after all the other outputs
        self.priority = 10
        with document:
            self.options = Navigate_Results_RBOptions
            """ *[dict={}] Options for the `navigate_results_rb` output """
        # The help is inherited and already mentions the default priority
        self.fix_priority_help()
        self._any_related = True

    @staticmethod
    def get_conf_examples(name, layers):
        outs = BaseOutput.simple_conf_examples(name, 'Web page to browse the results', 'Browse')  # noqa: F821
        outs[0]['options'] = {'link_from_root': 'index.html', 'skip_not_run': True}
        return outs
