#!/usr/bin/env python3
# Author: Jan Mrázek
# License: MIT
# Modified for KiBot by Salvador E. Tropea
# Equivalent to v1.4.0

from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
import json
import math
import os
import re
import sysconfig
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Set, Tuple, Union

from ..gs import GS
from .. import log

logger = log.get_logger()

# KiBot: numpy is optional
try:
    import numpy as np
    WITH_NUMPY = True
    try:
        import numpy.typing
        Matrix = np.typing.NDArray[np.float32]
    except ImportError:
        Matrix = List[List[float]]
except ImportError:
    from . import np
    WITH_NUMPY = False
    Matrix = List[List[float]]
from .unit import read_resistance   # KiBot: our value parser
from .pcbdraw_kicad_hal import export_pcb_svg_layers, load_board_data, BoardSide, Bounds, Component, DrillHole  # KiBot
# import svgpathtools # type: ignore   KiBot: svgpathtools is optional and we have a copy
from lxml import etree, objectify # type: ignore

Numeric = Union[int, float]
Point = Tuple[Numeric, Numeric]
Box = Tuple[Numeric, Numeric, Numeric, Numeric]


class BoardOutlineError(RuntimeError):
    """Raised when Edge.Cuts does not describe closed board contours."""


PKG_BASE = os.path.dirname(__file__)

etree.register_namespace("xlink", "http://www.w3.org/1999/xlink")


default_style = {
    "copper": "#417e5a",
    "board": "#4ca06c",
    "silk": "#f0f0f0",
    "pads": "#b5ae30",
    "outline": "#000000",
    "clad": "#9c6b28",
    "vcut": "#bf2600",
    "paste": "#8a8a8a",
    "highlight-on-top": False,
    "highlight-style": "stroke:none;fill:#ff0000;opacity:0.5;",
    "highlight-padding": 1.5,
    "highlight-offset": 0,
    "tht-resistor-band-colors": {
        -3: '#ff69b4',
        -2: '#d9d9d9',
        -1: '#ffc800',
        0: '#000000',
        1: '#805500',
        2: '#ff0000',
        3: '#ff8000',
        4: '#ffff00',
        5: '#00cc11',
        6: '#0000cc',
        7: '#cc00cc',
        8: '#666666',
        9: '#cccccc',
        '1%': '#805500',
        '2%': '#ff0000',
        '0.05%': '#ff8000',
        '0.02%': '#ffff00',
        '0.5%': '#00cc11',
        '0.25%': '#0000cc',
        '0.1%': '#cc00cc',
        '0.01%': '#666666',
        '0.05%': '#666666',
        '5%': '#ffc800',
        '10%': '#d9d9d9',
        '20%': '#ffe598',
    }
}

float_re = r'([-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?)'

class SvgPathItem:
    def __init__(self, path: str) -> None:
        path = re.sub(r"([MLA])(-?\d+)", r"\1 \2", path)
        path_elems = re.split("[, ]", path)
        path_elems = list(filter(lambda x: x, path_elems))
        if path_elems[0] != "M":
            raise SyntaxError("Only paths with absolute position are supported")
        self.start: Point = tuple(map(float, path_elems[1:3])) # type: ignore
        self.end: Point = (0, 0)
        self.args: Optional[List[Numeric]] = None
        path_elems = path_elems[3:]
        if path_elems[0] == "L":
            x = float(path_elems[1])
            y = float(path_elems[2])
            self.end = (x, y)
            self.type = path_elems[0]
            self.args = None
        elif path_elems[0] == "A":
            args = list(map(float, path_elems[1:8]))
            self.end = (args[5], args[6])
            self.args = args[0:5]
            self.type = path_elems[0]
        else:
            raise SyntaxError("Unsupported path element " + path_elems[0])

    @staticmethod
    def is_same(p1: Point, p2: Point) -> bool:
        dx = p1[0] - p2[0]
        dy = p1[1] - p2[1]
        pseudo_distance = dx*dx + dy*dy
        if GS.ki7:
            return pseudo_distance < 0.01 ** 2
        return pseudo_distance < 100 ** 2  # KiCad 5 and 6

    def format(self, first: bool) -> str:
        ret = ""
        if first:
            ret += " M {} {} ".format(*self.start)
        ret += self.type
        if self.args:
            ret += " " + " ".join(map(lambda x: str(x).rstrip('0').rstrip('.'), self.args))
        ret += " {} {} ".format(*self.end)
        return ret

    def flip(self) -> None:
        self.start, self.end = self.end, self.start
        if self.type == "A":
            assert(self.args is not None)
            self.args[4] = 1 if self.args[4] < 0.5 else 0

    def __str__(self) -> str:
        return f"{self.start} - {self.end} {self.type}"

def matrix(data: List[List[Numeric]]) -> Matrix:
    return np.array(data, dtype=np.float32)

def pseudo_distance(a: Point, b: Point) -> Numeric:
    a0 = a[0] - b[0]
    a1 = a[1] - b[1]
    return a0*a0 + a1*a1

def get_closest(reference: Point, elems: List[Point]) -> int:
    try:
        return elems.index(reference)
    except ValueError:
        return int(np.argmin([pseudo_distance(reference, x) for x in elems]))

# Pure Python implementation is slightly slower (i.e. 12.5 vs 11 s or 6.8 vs 5.2 s)
class PointIndex:
    """Spatial index for fast endpoint matching during contour building."""

    def __init__(self, elements: List[SvgPathItem]) -> None:
        self._elements = elements
        n = len(elements)
        self._active = np.ones(n, dtype=bool)
        self._starts = np.array([(e.start[0], e.start[1]) for e in elements]) if n > 0 else np.empty((0, 2))
        self._ends = np.array([(e.end[0], e.end[1]) for e in elements]) if n > 0 else np.empty((0, 2))
        self._start_index: Dict[Point, Set[int]] = defaultdict(set)
        self._end_index: Dict[Point, Set[int]] = defaultdict(set)
        for i, e in enumerate(elements):
            self._start_index[e.start].add(i)
            self._end_index[e.end].add(i)

    def has_active(self) -> bool:
        return bool(np.any(self._active))

    def pop_first_active(self) -> SvgPathItem:
        """Remove and return the first active element (seed for new contour)."""
        i = int(np.argmax(self._active))
        self._mark_used(i)
        return self._elements[i]

    def find_by_end(self, ref: Point) -> Optional[SvgPathItem]:
        return self._take(ref, self._ends, self._end_index, flip=False)

    def find_by_start(self, ref: Point) -> Optional[SvgPathItem]:
        return self._take(ref, self._starts, self._start_index, flip=False)

    def find_by_start_flipped(self, ref: Point) -> Optional[SvgPathItem]:
        return self._take(ref, self._starts, self._start_index, flip=True)

    def find_by_end_flipped(self, ref: Point) -> Optional[SvgPathItem]:
        return self._take(ref, self._ends, self._end_index, flip=True)

    def _take(self, ref: Point, points: "np.ndarray[Any, Any]",
              index: Dict[Point, Set[int]], flip: bool) -> Optional[SvgPathItem]:
        """Find an active element matching ref, mark it used, optionally flip."""
        i = self._find(ref, points, index)
        if i is None:
            return None
        self._mark_used(i)
        if flip:
            self._elements[i].flip()
        return self._elements[i]

    def _find(self, ref: Point, points: "np.ndarray[Any, Any]",
              index: Dict[Point, Set[int]]) -> Optional[int]:
        # Fast path: exact dict lookup
        candidates = index.get(ref)
        if candidates:
            for idx in candidates:
                if self._active[idx]:
                    return idx

        # KiBot: provide a pure Python implementation that doesn't need numpy
        if WITH_NUMPY:
            # Slow path: vectorized numpy distance on active elements
            active_idx = np.where(self._active)[0]
            if len(active_idx) == 0:
                return None
            diffs = points[active_idx] - np.array(ref)
            sq_dists = diffs[:, 0]**2 + diffs[:, 1]**2
            best = np.argmin(sq_dists)
            if sq_dists[best] < 0.0001:  # 0.01^2, matches SvgPathItem.is_same
                return int(active_idx[best])
        else:
            # Slow path: Standard Python distance on active elements
            best_idx = None
            min_sq_dist = float('inf')
            ref_x, ref_y = ref[0], ref[1]

            for i, is_active in enumerate(self._active):
                if not is_active:
                    continue

                p = points[i]
                dx = p[0] - ref_x
                dy = p[1] - ref_y

                sq_dist = dx*dx + dy*dy

                if sq_dist < min_sq_dist:
                    min_sq_dist = sq_dist
                    best_idx = i

            if best_idx is not None and min_sq_dist < 0.0001:  # 0.01^2
                return best_idx

        return None

    def _mark_used(self, i: int) -> None:
        self._active[i] = False
        self._start_index[self._elements[i].start].discard(i)
        self._end_index[self._elements[i].end].discard(i)

def extract_arg(args: List[Any], index: int, default: Any=None) -> Any:
    """
    Return n-th element of array or default if out of range
    """
    if index >= len(args):
        return default
    return args[index]

def to_trans_matrix(transform: str) -> Matrix:
    """
    Given SVG transformation string returns corresponding matrix
    """
    m = matrix([[1, 0, 0], [0, 1, 0], [0, 0, 1]])
    if transform is None:
        return m
    trans = re.findall(r'[a-z]+?\(.*?\)', transform)
    for t in trans:
        op, args = t.split('(')
        args = [float(x) for x in re.findall(float_re, args)]
        if op == 'matrix':
            m = np.matmul(m, matrix([
                [args[0], args[2], args[4]],
                [args[1], args[3], args[5]],
                [0, 0, 1]]))
        if op == 'translate':
            x = args[0]
            y = extract_arg(args, 1, 0)
            m = np.matmul(m, matrix([
                [1, 0, x],
                [0, 1, y],
                [0, 0, 1]]))
        if op == 'scale':
            x = args[0]
            y = extract_arg(args, 1, 1)
            m = np.matmul(m, matrix([
                [x, 0, 0],
                [0, y, 0],
                [0, 0, 1]]))
        if op == 'rotate':
            cosa: float = math.cos(math.radians(args[0]))
            sina: float = math.sin(math.radians(args[0]))
            if len(args) != 1:
                x, y = args[1:3]
                m = np.matmul(m, matrix([
                    [1, 0, x],
                    [0, 1, y],
                    [0, 0, 1]]))
            m = np.matmul(m, matrix([
                [cosa, -sina, 0],
                [sina, cosa, 0],
                [0, 0, 1]]))
            if len(args) != 1:
                m = np.matmul(m, matrix([
                    [1, 0, -x],
                    [0, 1, -y],
                    [0, 0, 1]]))
        tana: float = math.tan(math.radians(args[0]))
        if op == 'skewX':
            m = np.matmul(m, matrix([
                [1, tana, 0],
                [0, 1, 0],
                [0, 0, 1]]))
        if op == 'skewY':
            m = np.matmul(m, matrix([
                [1, 0, 0],
                [tana, 1, 0],
                [0, 0, 1]]))
    return m

def collect_transformation(element: etree.Element, root: Optional[etree.Element]=None) -> Matrix:
    """
    Collect all the transformation applied to an element and return it as matrix
    """
    if root is None:
        if element.getparent() is not None:
            m = collect_transformation(element.getparent(), root)
        else:
            m = matrix([[1, 0, 0], [0, 1, 0], [0, 0, 1]])
    else:
        if element.getparent() != root:
            m = collect_transformation(element.getparent(), root)
        else:
            m = matrix([[1, 0, 0], [0, 1, 0], [0, 0, 1]])
    if "transform" not in element.attrib:
        return m
    trans = element.attrib["transform"]
    # There is a strange typing behavior in CI, ignore it at the moment
    return np.matmul(m, to_trans_matrix(trans)) # type: ignore

def element_position(element: etree.Element, root: Optional[etree.Element]=None) -> Point:
    position = matrix([
        [element.attrib["x"]],
        [element.attrib["y"]],
        [1]])
    r = root
    trans = collect_transformation(element, root=r)
    position = np.matmul(trans, position)
    return position[0][0] / position[2][0], position[1][0] / position[2][0]

def get_global_datapaths() -> List[str]:
    paths = []
    share = os.path.join('share', 'pcbdraw')
    scheme_names = sysconfig.get_scheme_names()
    if os.name == 'posix':
        if 'posix_user' in scheme_names:
            paths.append(os.path.join(sysconfig.get_path('data', 'posix_user'), share))
        if 'posix_prefix' in scheme_names:
            paths.append(os.path.join(sysconfig.get_path('data', 'posix_prefix'), share))
    elif os.name == 'nt':
        if 'nt_user' in scheme_names:
            paths.append(os.path.join(sysconfig.get_path('data', 'nt_user'), share))
        if 'nt' in scheme_names:
            paths.append(os.path.join(sysconfig.get_path('data', 'nt'), share))
    if len(paths) == 0:
        paths.append(os.path.join(sysconfig.get_path('data'), share))
    return paths

def find_data_file(name: str, extension: str, data_paths: List[str], subdir: Optional[str]=None) -> Optional[str]:
    if not name.endswith(extension):
        name += extension
    if os.path.isfile(name):
        return name
    for path in data_paths:
        if subdir is not None:
            fname = os.path.join(path, subdir, name)
            if os.path.isfile(fname):
                return fname
        fname = os.path.join(path, name)
        if os.path.isfile(fname):
            return fname
    return None

def internal_to_mm(val: int) -> float:
    return val / 1000000.0

def mm_to_internal(val: float) -> int:
    return int(val * 1000000)

def to_internal_units(val: str) -> int:
    """Read an SVG length and return integer PcbDraw internal units."""
    x = float_re + r'\s*(pt|pc|mm|cm|in)?'
    value, unit = re.findall(x, val)[0]
    value = float(value)
    if unit == "" or unit == "px":
        return mm_to_internal(value * 25.4 / 96)
    if unit == "pt":
        return mm_to_internal(value * 25.4 / 72)
    if unit == "pc":
        return mm_to_internal(value * 25.4 / 6)
    if unit == "mm":
        return mm_to_internal(value)
    if unit == "cm":
        return mm_to_internal(value * 10)
    if unit == "in":
        return mm_to_internal(25.4 * value)
    raise RuntimeError(f"Unknown units in '{val}'")

def to_user_units(val: str) -> float:
    x = float_re + r'\s*(pt|pc|mm|cm|in)?'
    value_str, unit = re.findall(x, val)[0]
    value = float(value_str)
    if unit == "" or unit == "px":
        return value
    if unit == "pt":
        return 1.25 * value
    if unit == "pc":
        return 15 * value
    if unit == "mm":
        return 3.543307 * value
    if unit == "cm":
        return 35.43307 * value
    if unit == "in":
        return 90
    raise RuntimeError(f"Unknown units in '{val}'")


def make_XML_identifier(s: str) -> str:
    """
    Given a name, strip invalid characters from XML identifier
    """
    s = re.sub('[^0-9a-zA-Z_]', '', s)
    s = re.sub('^[^a-zA-Z_]+', '', s)
    return s

def read_svg_unique(source: Union[str, bytes], prefix: str) -> etree.Element:
    root, _ = read_svg_unique2(source, prefix)
    return root

def read_svg_unique2(source: Union[str, bytes], prefix: str) -> etree.Element:
    parser = etree.XMLParser(huge_tree=True)
    if isinstance(source, bytes):
        content = source.decode("utf-8")
        root = etree.fromstring(source, parser)
    else:
        root = etree.parse(source, parser).getroot()
        with open(source) as svg_file:
            content = svg_file.read()
    # We have to ensure all Ids in SVG are unique. Let's make it nasty by
    # collecting all ids and doing search & replace
    # Potentially dangerous (can break user text)
    ids = []
    for el in root.getiterator():
        if "id" in el.attrib and el.attrib["id"] != "origin":
            ids.append(el.attrib["id"])
    for i in ids:
        content = content.replace("#"+i, "#" + prefix + i)
    root = etree.fromstring(str.encode(content), parser)
    for el in root.getiterator():
        if "id" in el.attrib and el.attrib["id"] != "origin":
            el.attrib["id"] = prefix + el.attrib["id"]
    return root, prefix

def extract_svg_content(root: etree.Element) -> List[etree.Element]:
    # Remove SVG namespace to ease our lives and change ids
    for el in root.getiterator():
        if '}' in str(el.tag):
            el.tag = el.tag.split('}', 1)[1]
    return [ x for x in root if x.tag and x.tag not in ["title", "desc"]]

def strip_style_svg(root: etree.Element, keys: List[str], forbidden_colors: List[str]) -> bool:
    elements_to_remove = []
    normalized_forbidden_colors = {color.lower() for color in forbidden_colors}

    def process_element(el: etree.Element, inherited_opacity: Dict[str, str],
                        inherited_suppression: Dict[str, bool]) -> None:
        effective_opacity = dict(inherited_opacity)
        suppression = dict(inherited_suppression)

        if "style" in el.attrib:
            s = el.attrib["style"].strip().split(";")
            styles: Dict[str, str] = {}
            for x in s:
                if len(x) == 0:
                    continue
                key, val = tuple(x.split(":", 1))
                key = key.strip()
                val = val.strip()
                styles[key] = val

            fill = styles.get("fill", "").lower()
            stroke = styles.get("stroke", "").lower()
            if fill in normalized_forbidden_colors or stroke in normalized_forbidden_colors:
                elements_to_remove.append(el)

            for paint in ("fill", "stroke"):
                opacity = f"{paint}-opacity"
                if opacity in styles:
                    effective_opacity[paint] = styles[opacity]

                if paint not in keys:
                    suppression[paint] = False
                    continue

                value = styles.get(paint)
                normalized_value = value.lower() if value is not None else None
                if normalized_value == "none":
                    # KiCAD 9+ uses "fill: none"/"stroke: none" instead of
                    # zero opacity. Removing the paint property would make the
                    # element inherit the layer color, so preserve its absence
                    # through opacity instead.
                    styles[opacity] = "0"
                    del styles[paint]
                    suppression[paint] = True
                elif value is not None:
                    del styles[paint]
                    if inherited_suppression[paint] and opacity not in styles:
                        # A visible child can override a parent's "none" paint.
                        # Reset the zero opacity introduced on the parent to the
                        # opacity the child inherited in the source SVG.
                        styles[opacity] = effective_opacity[paint]
                    suppression[paint] = False

            el.attrib["style"] = ";" \
                .join([f"{key}: {val}" for key, val in styles.items() if key not in keys]) \
                .replace("  ", " ") \
                .strip()

        for child in el:
            process_element(child, effective_opacity, suppression)

    process_element(
        root,
        inherited_opacity={"fill": "1", "stroke": "1"},
        inherited_suppression={"fill": False, "stroke": False},
    )

    for el in elements_to_remove:
        parent = el.getparent()
        if parent is not None:
            parent.remove(el)
    return root in elements_to_remove

def empty_svg(**attrs: str) -> etree.ElementTree:
    document = etree.ElementTree(etree.fromstring(
        """<?xml version="1.0"?>
        <!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
        <svg xmlns="http://www.w3.org/2000/svg" version="1.1"
            width="29.7002cm" height="21.0007cm" viewBox="0 0 116930 82680 ">
            <title>Picture generated by PcbDraw </title>
            <desc>Picture generated by PcbDraw</desc>
        </svg>"""))
    root = document.getroot()
    for key, value in attrs.items():
        root.attrib[key] = value
    return document

def get_board_polygon(svg_elements: etree.Element) -> etree.Element:
    """
    Connect independent Edge.Cuts segments into closed board contours.

    Malformed contours are rejected instead of being implicitly closed by the
    SVG fill operation, which would produce a misleading board rendering.
    """
    elements = []
    path = ""
    for group in svg_elements:
        for svg_element in group:
            if svg_element.tag == "path":
                p = svg_element.attrib["d"]
                # Handle closed polygon paths (M x,y x,y ... Z)
                # that some KiCAD versions emit for Edge.Cuts
                polygon_pts = re.findall(
                    r"(-?[\d.]+)[, ](-?[\d.]+)", p)
                if p.strip().startswith("M") and p.strip().endswith("Z") and len(polygon_pts) >= 3:
                    # Decompose closed polygon into line segments
                    polygon_pts.append(polygon_pts[0])
                    for i in range(len(polygon_pts) - 1):
                        sx, sy = polygon_pts[i]
                        ex, ey = polygon_pts[i + 1]
                        elements.append(SvgPathItem(f"M {sx} {sy} L {ex} {ey}"))
                else:
                    elements.append(SvgPathItem(p))
            elif svg_element.tag == "circle":
                # Convert circle to path
                att = svg_element.attrib
                s = " M {0} {1} m-{2} 0 a {2} {2} 0 1 0 {3} 0 a {2} {2} 0 1 0 -{3} 0 ".format(
                    att["cx"], att["cy"], att["r"], 2 * float(att["r"]))
                path += s
    path = get_best_path_new(elements, path) if GS.ki7 else get_best_path(elements, path)
    e = etree.Element("path", d=path, style="fill-rule: evenodd;")
    return e

def get_best_path_new(elements, path):
    index = PointIndex(elements)
    while index.has_active():
        outline = [index.pop_first_active()]
        size = 0
        while size != len(outline) and index.has_active():
            size = len(outline)

            e = index.find_by_end(outline[0].start)
            if e is not None:
                outline.insert(0, e)
                continue

            e = index.find_by_start_flipped(outline[0].start)
            if e is not None:
                outline.insert(0, e)
                continue

            e = index.find_by_start(outline[-1].end)
            if e is not None:
                outline.append(e)
                continue

            e = index.find_by_end_flipped(outline[-1].end)
            if e is not None:
                outline.append(e)
                continue

        start = outline[0].start
        end = outline[-1].end
        if not SvgPathItem.is_same(start, end):
            gap = math.sqrt(pseudo_distance(start, end))
            raise BoardOutlineError(
                "Board outline is not closed: "
                f"{gap:.3f} mm gap between {end} and {start}"
            )

        for i, x in enumerate(outline):
            path += x.format(first=(i == 0))
    if not path:
        raise BoardOutlineError("Board has no closed outline on Edge.Cuts")

    return path

# KiBot: solution for KiCad 6
def get_best_path(elements, path):
    while len(elements) > 0:
        # Initiate seed for the outline
        outline = [elements[0]]
        elements = elements[1:]
        size = 0
        # Append new segments to the ends of outline until there is none to append.
        while size != len(outline) and len(elements) > 0:
            size = len(outline)

            i = get_closest(outline[0].start, [x.end for x in elements])
            if SvgPathItem.is_same(outline[0].start, elements[i].end):
                outline.insert(0, elements[i])
                del elements[i]
                continue

            i = get_closest(outline[0].start, [x.start for x in elements])
            if SvgPathItem.is_same(outline[0].start, elements[i].start):
                e = elements[i]
                e.flip()
                outline.insert(0, e)
                del elements[i]
                continue

            i = get_closest(outline[-1].end, [x.start for x in elements])
            if SvgPathItem.is_same(outline[-1].end, elements[i].start):
                outline.insert(0, elements[i])
                del elements[i]
                continue

            i = get_closest(outline[-1].end, [x.end for x in elements])
            if SvgPathItem.is_same(outline[-1].end, elements[i].end):
                e = elements[i]
                e.flip()
                outline.insert(0, e)
                del elements[i]
                continue
        # ...then, append it to path.
        first = True
        for x in outline:
            path += x.format(first)
            first = False
    return path

def load_style(style_file: str) -> Dict[str, Any]:
    try:
        with open(style_file, "r") as f:
            style = json.load(f)
    except IOError:
        raise RuntimeError("Cannot open style " + style_file)
    if not isinstance(style, dict):
        raise RuntimeError("Stylesheet has to be a dictionary")
    required = set(["copper", "board", "clad", "silk", "pads", "outline",
        "vcut", "highlight-style", "highlight-offset", "highlight-on-top",
        "highlight-padding"])
    missing = required - set(style.keys())
    if missing:
        raise RuntimeError("Missing following keys in style {}: {}"
                                .format(style_file, ", ".join(missing)))
    return style

def load_remapping(remap_file: str) -> Dict[str, Tuple[str, str]]:
    def readMapping(s: str) -> Tuple[str, str]:
        x = s.split(":")
        if len(x) != 2:
            raise RuntimeError(f"Invalid remmaping value {s}")
        return x[0], x[1]
    if remap_file is None:
        return {}
    try:
        with open(remap_file, "r") as f:
            j = json.load(f)
            if not isinstance(j, dict):
                raise RuntimeError("Invalid format of remapping file")
            return {ref: readMapping(val) for ref, val in j.items()}
    except IOError:
        raise RuntimeError("Cannot open remapping file " + remap_file)

def merge_bbox(left: Box, right: Box) -> Box:
    """
    Merge bounding boxes in format (xmin, xmax, ymin, ymax)
    """
    return tuple([
        f(l, r) for l, r, f in zip(left, right, [min, max, min, max])
    ]) # type: ignore

def hack_is_valid_bbox(box: Any): # type: ignore
    return all(-1e15 < c < 1e15 for c in box)


# KiBot: We don't use svg_geometry_bounds because we can ask KiCad about it

def remove_empty_elems(tree: etree.Element) -> None:
    """
    Given SVG tree, remove empty groups and defs
    """
    for elem in tree:
        remove_empty_elems(elem)
    toDel = []
    for elem in tree:
        if elem.tag in ["g", "defs"] and len(elem.getchildren()) == 0:
            toDel.append(elem)
    for elem in toDel:
        tree.remove(elem)

def remove_inkscape_annotation(tree: etree.Element) -> None:
    for elem in tree:
        remove_inkscape_annotation(elem)
    for key in tree.attrib.keys():
        if "inkscape" in key:
            tree.attrib.pop(key)
    # Comments have callable tag...
    if not callable(tree.tag):
        objectify.deannotate(tree, cleanup_namespaces=True)

def drill_svg_path(drill: DrillHole) -> str:
    """Return the SVG path for a round or slotted drill."""
    width, height = drill.size.width, drill.size.height
    if width > height:
        straight, diameter = width - height, height
        return (
            f"M {-straight / 2} {-diameter / 2} "
            f"A {diameter / 2} {diameter / 2} 0 1 1 "
            f"{-straight / 2} {diameter / 2} "
            f"L {straight / 2} {diameter / 2} "
            f"A {diameter / 2} {diameter / 2} 0 1 1 "
            f"{straight / 2} {-diameter / 2} Z"
        )
    straight, diameter = height - width, width
    return (
        f"M {-diameter / 2} {straight / 2} "
        f"A {diameter / 2} {diameter / 2} 0 1 1 "
        f"{diameter / 2} {straight / 2} "
        f"L {diameter / 2} {-straight / 2} "
        f"A {diameter / 2} {diameter / 2} 0 1 1 "
        f"{-diameter / 2} {-straight / 2} Z"
    )

@dataclass
class PlotAction:
    name: str
    layer: int  # KiBot: we never use the CLI, so we always use layer IDs
    process: Callable[[str, bytes], None]

@dataclass
class ResistorValue:
    value: Optional[str] = None
    flip_bands: bool=False


@dataclass(frozen=True)
class ResistorColorCode:
    band_count: int
    colors: Tuple[Union[int, str], ...]


def resistor_color_code(
    resistance: Decimal, tolerance: str
) -> ResistorColorCode:
    """Calculate standard color-band keys for a resistance and tolerance."""
    if resistance < 0:
        raise ValueError("resistance cannot be negative")
    if resistance == 0:
        return ResistorColorCode(1, (0,))

    try:
        tolerance_value = Decimal(tolerance.removesuffix("%"))
    except (InvalidOperation, ValueError) as error:
        raise ValueError(f"invalid resistor tolerance {tolerance}") from error

    significant_count = 3 if tolerance_value <= 2 else 2
    multiplier = resistance.adjusted() - significant_count + 1
    significant = int(resistance.scaleb(-multiplier))
    digits = tuple(
        int(digit) for digit in f"{significant:0{significant_count}d}"
    )
    if len(digits) != significant_count or multiplier not in range(-3, 10):
        raise ValueError(
            f"resistance {resistance} is outside the supported color-code range"
        )

    colors: Tuple[Union[int, str], ...] = (*digits, multiplier)
    if tolerance != "20%":
        colors += (tolerance,)
    return ResistorColorCode(significant_count + 2, colors)


class PlotInterface:
    def render(self, plotter: PcbPlotter) -> None:
        raise NotImplementedError("Plot interface wasn't implemented")


# KiBot: we have an "only_mask" option that is simplified using this:
SUBSTRATE_ELEMENTS = {
    "board": (GS.Edge_Cuts, GS.Edge_Cuts),
    "clad": (GS.F_Mask, GS.B_Mask),
    "copper": (GS.F_Cu, GS.B_Cu),
    "pads": (GS.F_Cu, GS.B_Cu),
    "pads-mask": (GS.F_Mask, GS.B_Mask),
    "silk": (GS.F_SilkS, GS.B_SilkS),
    "outline": (GS.Edge_Cuts, GS.Edge_Cuts)
}
ELEMENTS_USED = (
    # Normal plot, all the elements
    ("board", "clad", "copper", "pads", "pads-mask", "silk", "outline"),
    # Solder mask plot
    ("board", "pads-mask")
)


@dataclass
class PlotSubstrate(PlotInterface):
    drill_holes: bool = True
    copper: bool = True
    outline_width: int = mm_to_internal(0.1)
    only_mask: bool = False  # KiBot: used to just get the pads-mask

    def render(self, plotter: PcbPlotter) -> None:
        self._plotter = plotter # ...so we don't have to pass it explicitly
        SUBSTRATE_PROCESS = {
            "board": self._process_baselayer,
            "clad": self._process_layer,
            "copper": self._process_layer,
            "pads": self._process_layer,
            "pads-mask": self._process_mask,
            "silk": self._process_layer,
            "outline": self._process_outline
        }

        to_plot: List[PlotAction] = []
        # KiBot: This loop uses the SUBSTRATE_ELEMENTS, SUBSTRATE_PROCESS and ELEMENTS_USED
        for e in ELEMENTS_USED[self.only_mask]:
            if self.copper or e != "copper":
                to_plot.append(PlotAction(e, SUBSTRATE_ELEMENTS[e][plotter.render_back], SUBSTRATE_PROCESS[e]))

        self._container = etree.Element("g", id="substrate")
        self._container.attrib["clip-path"] = "url(#cut-off)"
        self._boardsize = self._plotter.board_bounds
        self._plotter.execute_plot_plan(to_plot)

        if self.drill_holes:
            self._build_hole_mask()
            self._container.attrib["mask"] = "url(#hole-mask)"
        self._plotter.append_board_element(self._container)

    def _process_layer(self, name: str, source: bytes) -> None:
        layer = etree.SubElement(self._container, "g", id="substrate-" + name,
            style="fill:{0}; stroke:{0};".format(self._plotter.get_style(name)))
        if name == "pads":
            layer.attrib["mask"] = "url(#pads-mask)"
        if name == "silk":
            layer.attrib["mask"] = "url(#pads-mask-silkscreen)"
        for element in extract_svg_content(read_svg_unique(source, self._plotter.unique_prefix())):
            if not strip_style_svg(element, keys=["fill", "stroke"],
                                   forbidden_colors=["#ffffff"]):
                layer.append(element)

    def _process_outline(self, name: str, source: bytes) -> None:
        if self.outline_width == 0:
            return
        layer = etree.SubElement(self._container, "g", id="substrate-" + name,
            style="fill:{0}; stroke:{0}; stroke-width: {1}".format(
                self._plotter.get_style(name),
                self._plotter.internal_to_svg(self.outline_width)))
        if name == "pads":
            layer.attrib["mask"] = "url(#pads-mask)"
        if name == "silk":
            layer.attrib["mask"] = "url(#pads-mask-silkscreen)"
        for element in extract_svg_content(read_svg_unique(source, self._plotter.unique_prefix())):
            if not strip_style_svg(element, keys=["fill", "stroke", "stroke-width"],
                                   forbidden_colors=["#ffffff"]):
                layer.append(element)
        for hole in self._plotter.board_data.holes:
            position = (hole.position.x, hole.position.y)
            if hole.size.width == 0 or hole.size.height == 0:
                continue
            el = etree.SubElement(layer, "path")
            el.attrib["d"] = drill_svg_path(hole)
            el.attrib["transform"] = "translate({} {}) rotate({})".format(
                position[0], position[1], -hole.orientation_degrees)

    def _process_baselayer(self, name: str, source: bytes) -> None:
        board_polygon = get_board_polygon(
            extract_svg_content(
                read_svg_unique(source, self._plotter.unique_prefix())))

        clipPath = self._plotter.get_def_slot(tag_name="clipPath", id="cut-off")
        clipPath.append(board_polygon)

        layer = etree.SubElement(self._container, "g", id="substrate-"+name,
            style="fill:{0}; stroke:{0};".format(self._plotter.get_style(name)))
        layer.append(deepcopy(board_polygon))
        for element in extract_svg_content(read_svg_unique(source, self._plotter.unique_prefix())):
            if not strip_style_svg(element, keys=["fill", "stroke"],
                                  forbidden_colors=["#ffffff"]):
                layer.append(element)

    def _process_mask(self, name: str, source: bytes) -> None:
        mask = self._plotter.get_def_slot(tag_name="mask", id=name)
        for element in extract_svg_content(read_svg_unique(source, self._plotter.unique_prefix())):
            for item in element.getiterator():
                if "style" in item.attrib:
                    # KiCAD plots in black, for mask we need white
                    item.attrib["style"] = item.attrib["style"].replace("#000000", "#ffffff")
            mask.append(element)
        silkMask = self._plotter.get_def_slot(tag_name="mask", id=f"{name}-silkscreen")
        etree.SubElement(silkMask, "rect", attrib={
            "x": str(self._boardsize.x),
            "y": str(self._boardsize.y),
            "width": str(self._boardsize.width),
            "height": str(self._boardsize.height),
            "fill": "white"
        })
        for element in extract_svg_content(read_svg_unique(source, self._plotter.unique_prefix())):
            # KiCAD plots black, no need to change fill
            silkMask.append(element)

    def _build_hole_mask(self) -> None:
        mask = self._plotter.get_def_slot(tag_name="mask", id="hole-mask")
        container = etree.SubElement(mask, "g")

        bb = self._plotter.board_bounds
        bg = etree.SubElement(container, "rect", x="0", y="0", fill="white")
        bg.attrib["x"] = str(bb.x)
        bg.attrib["y"] = str(bb.y)
        bg.attrib["width"] = str(bb.width)
        bg.attrib["height"] = str(bb.height)

        for hole in self._plotter.board_data.holes:
            position = (hole.position.x, hole.position.y)
            size = (hole.size.width, hole.size.height)
            if size[0] > 0 and size[1] > 0:
                if size[0] < size[1]:
                    stroke = size[0]
                    length = size[1] - size[0]
                    points = "{} {} {} {}".format(0, -length / 2, 0, length / 2)
                else:
                    stroke = size[1]
                    length = size[0] - size[1]
                    points = "{} {} {} {}".format(-length / 2, 0, length / 2, 0)
                el = etree.SubElement(container, "polyline")
                el.attrib["stroke-linecap"] = "round"
                el.attrib["stroke"] = "black"
                el.attrib["stroke-width"] = str(stroke)
                el.attrib["points"] = points
                el.attrib["transform"] = "translate({} {}) rotate({})".format(
                    position[0], position[1], -hole.orientation_degrees)

@dataclass
class PlacedComponentInfo:
    id: str
    origin: Tuple[float, float]
    svg_offset: Tuple[float, float]
    scale: Tuple[float, float]
    size: Tuple[float, float]

@dataclass
class PlotComponents(PlotInterface):
    filter: Callable[[str], bool] = lambda x: True # Components to show
    highlight: Callable[[str], bool] = lambda x: False # References to highlight
    remapping: Callable[[str, str, str], Tuple[str, str]] = lambda ref, lib, name: (lib, name)
    resistor_values: Dict[str, ResistorValue] = field(default_factory=dict)
    no_warn_back: bool = False   # KiBot: Used to supress warnings on the back side

    def render(self, plotter: PcbPlotter) -> None:
        self._plotter = plotter
        self._prefix = plotter.unique_prefix()
        self._used_components: Dict[str, PlacedComponentInfo] = {}
        for component in plotter.components(invert_side=False):
            self._append_component(component)
        for component in plotter.components(invert_side=True):
            self._append_component(component, template_suffix=".back")

    def _get_unique_name(
        self, lib: str, name: str, value: str, properties: Mapping[str, str]
    ) -> str:
        tolerance = properties.get("tol", properties.get("tolerance", ""))
        return f"{self._prefix}_{lib}__{name}_{value}_{tolerance}"

    def _append_component(
        self, component: Component, template_suffix: str = ""
    ) -> None:
        lib = component.library
        name = component.footprint + template_suffix
        ref = component.reference
        value = component.value
        properties = component.properties
        if not self.filter(ref) or name == "":
            return
        # Override resistor values
        if ref in self.resistor_values:
            v = self.resistor_values[ref].value
            if v is not None:
                value = v

        lib, name = self.remapping(ref, lib, name)

        unique_name = self._get_unique_name(lib, name, value, properties)
        if unique_name in self._used_components:
            component_info = self._used_components[unique_name]
            component_element = etree.Element("use",
                attrib={"{http://www.w3.org/1999/xlink}href": "#" + component_info.id})
        else:
            ret = self._create_component(lib, name, ref, value, properties)
            if ret is None:
                # KiBot: Implementation for back side warning supression
                if name[-5:] != '.back' or not self.no_warn_back:
                    self._plotter.yield_warning("component", f"Component {lib}:{name} has no footprint.")
                return
            component_element, component_info = ret
            self._used_components[unique_name] = component_info

        self._plotter.append_component_element(etree.Comment(f"{lib}:{name}:{ref}"))
        group = etree.Element("g")
        group.append(component_element)
        ci = component_info
        group.attrib["transform"] = \
            f"translate({component.position.x} {component.position.y}) " + \
            f"scale({ci.scale[0]}, {ci.scale[1]}) " + \
            f"rotate({-component.rotation_degrees}) " + \
            f"translate({-ci.origin[0]} {-ci.origin[1]})"
        self._plotter.append_component_element(group)

        if self.highlight(ref):
            self._build_highlight(component, component_info)

    def _create_component(
        self, lib: str, name: str, ref: str, value: str,
        properties: Mapping[str, str],
    ) \
                             -> Optional[Tuple[etree.Element, PlacedComponentInfo]]:
        f = self._plotter._get_model_file(lib, name)
        if f is None:
            return None
        xml_id = make_XML_identifier(
            self._get_unique_name(lib, name, value, properties)
        )
        component_element = etree.Element("g", attrib={"id": xml_id})

        svg_tree, id_prefix = read_svg_unique2(f, self._plotter.unique_prefix())
        for x in extract_svg_content(svg_tree):
            if x.tag in ["namedview", "metadata"]:
                continue
            component_element.append(x)
        origin_x: Numeric = 0
        origin_y: Numeric = 0
        origin = component_element.find(".//*[@id='origin']")
        if origin is not None:
            origin_x, origin_y = element_position(origin, root=component_element)
            origin.getparent().remove(origin)
        else:
            self._plotter.yield_warning("origin", f"component: Component {lib}:{name} has no origin")
        svg_scale_x, svg_scale_y, svg_offset_x, svg_offset_y = self._component_to_board_scale_and_offset(svg_tree)
        component_info = PlacedComponentInfo(
            id=xml_id,
            origin=(origin_x, origin_y),
            svg_offset=(svg_offset_x, svg_offset_y),
            scale=(svg_scale_x, svg_scale_y),
            size=(to_internal_units(svg_tree.attrib["width"]),
                  to_internal_units(svg_tree.attrib["height"]))
        )
        self._apply_resistor_code(
            component_element, id_prefix, ref, value, properties
        )
        return component_element, component_info

    def _component_to_board_scale_and_offset(self, svg: etree.Element) \
            -> Tuple[float, float, float, float]:
        width = self._plotter.internal_to_svg(to_internal_units(svg.attrib["width"]))
        height = self._plotter.internal_to_svg(to_internal_units(svg.attrib["height"]))
        x, y, vw, vh = [float(x) for x in svg.attrib["viewBox"].split()]
        return width / vw, height / vh, x, y

    def _build_highlight(self, component: Component,
                         info: PlacedComponentInfo) -> None:
        ref = component.reference
        padding = mm_to_internal(self._plotter.get_style("highlight-padding"))
        h = etree.Element("rect", id=f"h_{ref}",
            x=str(self._plotter.internal_to_svg(-padding)),
            y=str(self._plotter.internal_to_svg(-padding)),
            width=str(self._plotter.internal_to_svg(int(info.size[0] + 2 * padding))),
            height=str(self._plotter.internal_to_svg(int(info.size[1] + 2 * padding))),
            style=self._plotter.get_style("highlight-style"))
        h.attrib["transform"] = \
            f"translate({component.position.x} {component.position.y}) " + \
            f"rotate({-component.rotation_degrees}) " + \
            f"translate({-(info.origin[0] - info.svg_offset[0]) * info.scale[0]}, {-(info.origin[1] - info.svg_offset[1]) * info.scale[1]})"
        self._plotter.append_highlight_element(h)

    def _apply_resistor_code(
        self, root: etree.Element, id_prefix: str, ref: str, value: str,
        properties: Optional[Mapping[str, str]] = None,
    ) -> None:
        if root.find(f".//*[@id='{id_prefix}res_band1']") is None:
            return
        try:
            res, tolerance = self._get_resistance_from_value(
                value, properties or {}
            )
            code = resistor_color_code(res, tolerance)
            if code.band_count == 1:
                zero_band = root.find(f".//*[@id='{id_prefix}res_zeroband']")
                if zero_band is not None:
                    self._set_resistor_band(zero_band, self._plotter.get_style(
                        "tht-resistor-band-colors", 0))
                    return
                fallback = (0, 0, 0) if tolerance == "20%" \
                    else (0, 0, 0, tolerance)
                code = ResistorColorCode(4, fallback)

            prefix = "res_5band" if code.band_count == 5 else "res_band"
            if root.find(f".//*[@id='{id_prefix}{prefix}1']") is None:
                raise UserWarning(
                    f"component template does not support {code.band_count}-band codes"
                )
            resistor_colors = [
                self._plotter.get_style("tht-resistor-band-colors", color)
                for color in code.colors
            ]

            if ref in self.resistor_values:
                if self.resistor_values[ref].flip_bands:
                    resistor_colors.reverse()

            for res_i, res_c in enumerate(resistor_colors):
                band = root.find(
                    f".//*[@id='{id_prefix}{prefix}{res_i + 1}']"
                )
                assert band is not None
                self._set_resistor_band(band, res_c)
        except (UserWarning, ValueError) as e:
            self._plotter.yield_warning("resistor", f"Cannot color-code resistor {ref}: {e}")
            return

    @staticmethod
    def _set_resistor_band(band: etree.Element, color: str) -> None:
        styles = dict(
            entry.split(":", 1) for entry in band.attrib["style"].split(";")
            if entry
        )
        styles["fill"] = color
        styles["display"] = "inline"
        band.attrib["style"] = ";".join(
            f"{key}:{value}" for key, value in styles.items()
        )

    # KiBot: This function is diferent because we have:
    # 1. Configurable tolerance field
    # 2. Default tolerance
    # 3. A complex parser that can get the tolerance from the value
    def _get_resistance_from_value(
        self, value: str, properties: Optional[Mapping[str, str]] = None
    ) -> Tuple[Decimal, str]:
        normalized_properties = {
            name.lower(): property_value
            for name, property_value in (properties or {}).items()
        }
        # KiBot: We have options to select the fields used for tolerance.
        #        The defaults matches upstream (tol, tolerance)
        # tolerance = normalized_properties.get(
        #     "tol", normalized_properties.get("tolerance")
        # )
        tolerance = next(filter(lambda x: x, map(normalized_properties.get, GS.global_field_tolerance)), None)
        if tolerance is not None:
            tolerance = tolerance.strip().replace(" ", "")  # 5 % -> 5%
        resistance_value = value

        # KiBot: our version of `read_resistance` can also extract the tolerance
        try:
            res, tolerance_from_value = read_resistance(resistance_value)
            if tolerance_from_value is not None:
                tolerance_from_value = str(tolerance_from_value)+"%"
        except ValueError:
            raise UserWarning(f"Invalid resistor value {resistance_value}")

        if tolerance is not None and tolerance_from_value is not None and tolerance != tolerance_from_value:
            raise UserWarning(f"Inconsistent tolerance {tolerance} vs {tolerance_from_value}")
        elif tolerance is None:
            if tolerance_from_value is None:
                tolerance = str(GS.global_default_resistor_tolerance)+"%"
            else:
                tolerance = tolerance_from_value

        colors = self._plotter.get_style("tht-resistor-band-colors")
        if not isinstance(colors, dict):
            raise RuntimeError(
                "Invalid style specified, tht-resistor-band-colors should be "
                f"dictionary, got {type(colors)}"
            )
        if tolerance != "20%" and tolerance not in colors:
            raise UserWarning(f"Invalid resistor tolerance {tolerance}")
            tolerance = "5%"
        return res, tolerance


@dataclass
class PlotPlaceholders(PlotInterface):
    def render(self, plotter: PcbPlotter) -> None:
        self._plotter = plotter
        for component in plotter.components(invert_side=False):
            self._append_placeholder(component)

    def _append_placeholder(self, component: Component) -> None:
        one_mm = self._plotter.one_mm
        half_mm = one_mm / 2
        p = etree.Element("rect",
            x=str(component.position.x - half_mm),
            y=str(component.position.y - half_mm),
            width=str(one_mm), height=str(one_mm), style="fill:red;")
        self._plotter.append_component_element(p)

@dataclass
class PlotVCuts(PlotInterface):
    layer: int = GS.Cmts_User   # KiBot: we never use the CLI, so we always use layer IDs

    def render(self, plotter: PcbPlotter) -> None:
        self._plotter = plotter
        self._plotter.execute_plot_plan([
            PlotAction("vcuts", self.layer, self._process_vcuts)
        ])

    def _process_vcuts(self, name: str, source: bytes) -> None:
        layer = etree.Element("g", id="substrate-vcuts",
            style="fill:{0}; stroke:{0};".format(self._plotter.get_style("vcut")))
        for element in extract_svg_content(read_svg_unique(source, self._plotter.unique_prefix())):
            if not strip_style_svg(element, keys=["fill", "stroke"],
                                   forbidden_colors=["#ffffff"]):
                layer.append(element)
        self._plotter.append_board_element(layer)

@dataclass
class PlotPaste(PlotInterface):
    def render(self, plotter: PcbPlotter) -> None:
        plan: List[PlotAction] = []
        if plotter.render_back:
            plan = [PlotAction("paste", GS.B_Paste, self._process_paste)]
        else:
            plan = [PlotAction("paste", GS.F_Paste, self._process_paste)]
        self._plotter = plotter
        self._plotter.execute_plot_plan(plan)

    def _process_paste(self, name: str, source: bytes) -> None:
        layer = etree.Element("g", id="substrate-paste",
            style="fill:{0}; stroke:{0};".format(self._plotter.get_style("paste")))
        for element in extract_svg_content(read_svg_unique(source, self._plotter.unique_prefix())):
            if not strip_style_svg(element, keys=["fill", "stroke"],
                                   forbidden_colors=["#ffffff"]):
                layer.append(element)
        self._plotter.append_board_element(layer)


class PcbPlotter:
    """
    PcbPlotter encapsulates all the machinery with PcbDraw plotting of SVG. It
    mainly serves as a builder (to step-by-step specify all options) and also to
    avoid passing many arguments between auxiliary functions
    KiBot:
    board: is a KiCad object, not a filename
    edge_only: Use the PCB edge when asking the BBox to KiCad
    exclude_width: When `edge_only` is enabled and `compute_bbox` is false excludes the line widths
    svg_precision: Precision for older versions

    """
    def __init__(self, board, edge_only=False, svg_precision=4, exclude_width=False):
        self._unique_counter: int = 1
        self.board = board
        self.svg_precision = svg_precision  # KiCad 6 SVG scale (1 mm == 10 ** svg_precision)
        self.edge_only = edge_only
        self.exclude_width = exclude_width
        self.internal_to_svg = GS.to_mm if GS.ki7 else self._ki2svg_v6
        self.svg_to_mm = self._float_to_str_mm if GS.ki7 else self._svg_to_mm_v6
        self.board_data = load_board_data(board, self.internal_to_svg, exclude_width)
        # KiBot: Avoid computing the bounds, trust KiCad
        self.board_bounds = self.board_data.bounds
        self.render_back: bool = False
        self.mirror: bool = False
        self.plot_plan: List[PlotInterface] = [
            PlotSubstrate(),
            PlotComponents(),
        ]

        self.data_path: List[str] = [] # Base paths for libraries lookup
        self.libs: List[str] = [] # Names of available libraries
        self._libs_path: List[str] = []

        self.style: Any = {}     # Color scheme
        self.margin: tuple = (0, 0, 0, 0)  # KiBot: Margin of the resulting document, we use 4 values, not just 1
        self.compute_bbox: bool = False  # KiBot: Adjust the bbox using the SVG drawings, default in upstream

        self.yield_warning: Callable[[str, str], None] = lambda tag, msg: None # Handle warnings

    # KiBot: KiCad 6 SVG precision
    @property
    def svg_precision(self) -> int:
        return self._svg_precision

    @svg_precision.setter
    def svg_precision(self, value: int) -> None:
        # We need a setter as KiCAD silently clamps the value, so we also have
        # to clamp.
        if value < 3:
            value = 3
        if value > 6:
            value = 6
        self._svg_precision = value
        self._svg_divider = 10 ** (6 - self.svg_precision)
        self._svg_divider_mm = 10 ** self.svg_precision
        self.one_mm = 1.0 if GS.ki7 else round(1 * self._svg_divider_mm)

    def plot(self) -> etree.ElementTree:
        """
        Plot the board based on the arguments stored in this class. Returns
        SVG tree that you can either save or post-process as you wish.
        """
        self._build_libs_path()
        self._setup_document(self.render_back, self.mirror)
        for plotter in self.plot_plan:
            plotter.render(self)
        remove_empty_elems(self._document.getroot())
        remove_inkscape_annotation(self._document.getroot())
        # KiBot: When compute_bbox is True we analyze the SVG, otherwise we ask KiCad
        self._shrink_svg(self._document, self.margin, compute_bbox=self.compute_bbox,
                         mirrored=self.render_back ^ self.mirror)
        return self._document


    def components(self, invert_side: bool = False) -> Iterable[Component]:
        """Yield components on the selected render side."""
        render_back = not self.render_back if invert_side else self.render_back
        side = BoardSide.BACK if render_back else BoardSide.FRONT
        return (component for component in self.board_data.components
                if component.side is side)

    def get_def_slot(self, tag_name: str, id: str) -> etree.SubElement:
        """
        Creates a new definition slot and returns the tag
        """
        return etree.SubElement(self._defs, tag_name, id=id)

    def append_board_element(self, element: etree.Element) -> None:
        """
        Add new element into the board container
        """
        self._board_cont.append(element)

    def append_component_element(self, element: etree.Element) -> None:
        """
        Add new element into board container
        """
        self._comp_cont.append(element)

    def append_highlight_element(self, element: etree.Element) -> None:
        """
        Add new element into highlight container
        """
        self._high_cont.append(element)

    def setup_builtin_data_path(self) -> None:
        """
        Add PcbDraw built-in libraries to the search path for libraries
        """
        self.data_path.append(os.path.join(PKG_BASE, "resources"))

    def setup_global_data_path(self) -> None:
        """
        Add global installation paths to the search path for libraries.
        """
        self.data_path += get_global_datapaths()

    def setup_arbitrary_data_path(self, path: str) -> None:
        """
        Add an arbitrary data path
        """
        self.data_path.append(os.path.realpath(path))

    def setup_env_data_path(self) -> None:
        """
        Add search paths from the env variable PCBDRAW_LIB_PATH
        """
        paths = os.environ.get("PCBDRAW_LIB_PATH", "").split(":")
        self.data_path += filter(lambda x: len(x) > 0, paths)

    def resolve_style(self, name: str) -> None:
        """
        Given a name of style, find the corresponding file and load it
        """
        path = self._find_data_file(name, ".json", "styles")
        if path is None:
            err_msg = "Cannot locate resource "+name
            if not os.path.isabs(name):
                err_msg += "; explored paths:\n"+"\n".join([f"- {x}" for x in self.data_path])
            raise RuntimeError(err_msg)
        self.style = load_style(path)

    def unique_prefix(self) -> str:
        pref = f"pref_{self._unique_counter}"
        self._unique_counter += 1
        return pref

    def _find_data_file(self, name: str, extension: str, subdir: str) -> Optional[str]:
        return find_data_file(name, extension, self.data_path, subdir)

    def _build_libs_path(self) -> None:
        self._libs_path = []
        for l in self.libs:
            self._libs_path += [os.path.join(p, l) for p in self.data_path]
        for l in self.libs:
            self._libs_path += [os.path.join(p, "footprints", l) for p in self.data_path]
        self._libs_path = [x for x in self._libs_path if os.path.exists(x)]

    def _get_model_file(self, lib: str, name: str) -> Optional[str]:
        """
        Find model file in the configured libraries. If it doesn't exists,
        return None.
        """
        for path in self._libs_path:
            f = os.path.join(path, lib, name + ".svg")
            if os.path.isfile(f):
                return f
        return None

    def get_style(self, *args: Union[str, int]) -> Any:
        try:
            value: Any = self.style
            for key in args:
                value = value[key]
            return value
        except KeyError:
            try:
                value = default_style
                for key in args:
                    value = value[key]  # type: ignore[index]
                return value
            except KeyError as e:
                raise UserWarning(f"Invalid argument for get_style : {args[0]}, {args[1]}")

    def execute_plot_plan(self, to_plot: List[PlotAction]) -> None:
        """Export each requested layer and pass its SVG bytes to the processor."""
        canonical_actions = [
            (action, action.layer)  # KiBot: we already have layer IDs, no need to translate the strings
            for action in to_plot
        ]
        layers = [layer for _, layer in canonical_actions]
        exported = export_pcb_svg_layers(self.board, layers, self.svg_precision)  # KiBot: plot from the object, not file
        for action, layer in canonical_actions:
            action.process(action.name, exported[layer])

    def _ki2svg_v6(self, x: int) -> float:
        """
        Convert dimensions from KiCAD to SVG. This method assumes the dimensions
        use self.svg_precision.
        """
        return x / self._svg_divider

    def _svg_to_mm_v6(self, x: float) -> str:
        return f"{x / self._svg_divider_mm:.3f}mm"

    def _float_to_str_mm(self, x: float) -> str:
        return f"{x:.3f}mm"

    def _shrink_svg(self, svg: etree.ElementTree, margin: tuple, compute_bbox: bool=False, mirrored: bool = False) -> None:
        """
        Shrink the SVG canvas to the size of the drawing. Add margin in
        PcbDraw internal units.
        """
        root = svg.getroot()
        if compute_bbox:
            logger.debug("Computing SVG viewBox usning compute_bbox")
            # compute_bbox is the mechanism used by upstream.
            # The KiBot option is size_detection = 'svg_paths'
            # Is slow and prone to errors, this is the fixed v1.4.0 code

            # We have to overcome the limitation of different base types between
            # PcbDraw and svgpathtools
            from xml.etree.ElementTree import fromstring as xmlParse

            from lxml.etree import tostring as serializeXml # type: ignore
            tree = xmlParse(serializeXml(svg))

            # As we cannot interpret mask cropping, we cannot simply take all paths
            # from source document (as e.g., silkscreen outside PCB) would enlarge
            # the canvas. Instead, we take bounding box of the substrate and
            # components separately
            from . import svgpathtools # type: ignore
            paths = []
            components = tree.find(".//*[@id='componentContainer']")
            if components is not None:
                paths += svgpathtools.document.flattened_paths(components)
            substrate = tree.find(".//*[@id='cut-off']")
            substrate_paths = []
            if substrate is not None:
                substrate_paths = svgpathtools.document.flattened_paths(substrate)

            boxes = []
            for x in paths:
                box = x.bbox()
                if not hack_is_valid_bbox(box):
                    continue
                boxes.append(box)
            for x in substrate_paths:
                box = x.bbox()
                if not hack_is_valid_bbox(box):
                    continue
                if mirrored:
                    # The substrate is in <defs> and not affected by the group
                    # scale(-1,1) transform, so mirror its x-range to match.
                    box = (-box[1], -box[0], box[2], box[3])
                boxes.append(box)

            if len(boxes) == 0:
                return
            bbox = boxes[0]
            for box in boxes[1:]:
                bbox = merge_bbox(bbox, box)
            bbox = list(bbox)
        else:
            # This is for the size_detection = 'kicad_*' KiBot option
            # Here we just let KiCad compute the bbox instead of computing it using the SVG elements
            # Faster, any error is a KiCad bug
            if self.edge_only:
                logger.debug("Computing SVG viewBox using edge_only")
                # For just the PCB edge we use the box computed by load_board_data
                bb = self.board_bounds
                bbox = [bb.x, bb.x+bb.width, bb.y, bb.y+bb.height]
            else:
                logger.debug("Computing SVG viewBox using full PCB")
                # For the full size we include text and various layers
                if self.render_back:
                    layers = set((GS.Edge_Cuts, GS.B_Mask, GS.B_Cu, GS.B_SilkS, GS.B_Fab))
                else:
                    layers = set((GS.Edge_Cuts, GS.F_Mask, GS.F_Cu, GS.F_SilkS, GS.F_Fab))
                bb = GS.compute_boundary_layers_k6(self.board, layers)
                bbox = [self.internal_to_svg(bb[0]), self.internal_to_svg(bb[2]),
                        self.internal_to_svg(bb[1]), self.internal_to_svg(bb[3])]
            if mirrored:
                bbox = [-bbox[1], -bbox[0], bbox[2], bbox[3]]
        logger.debug(f"Computed bbox: {bbox}")

        # Apply the margin
        # KiBot: 4 values, not 1
        bbox[0] -= self.internal_to_svg(margin[0])
        bbox[1] += self.internal_to_svg(margin[1])
        bbox[2] -= self.internal_to_svg(margin[2])
        bbox[3] += self.internal_to_svg(margin[3])

        root.attrib["viewBox"] = "{} {} {} {}".format(
            bbox[0], bbox[2],
            bbox[1] - bbox[0], bbox[3] - bbox[2]
        )
        root.attrib["width"] = self.svg_to_mm(bbox[1] - bbox[0])
        root.attrib["height"] = self.svg_to_mm(bbox[3] - bbox[2])

    def _setup_document(self, render_back: bool, mirror: bool) -> None:
        bb = self.board_bounds
        transform_string = ""
        # kicad-cli SVG coordinates are millimetres. PcbDraw's existing layout
        # code uses integer internal units, converted here at the document edge.
        if render_back ^ mirror:
            transform_string = "scale(-1,1)"
            self._document = empty_svg(
                width=self.svg_to_mm(bb.width),
                height=self.svg_to_mm(bb.height),
                viewBox=f"{-bb.width - bb.x} {bb.y} {bb.width} {bb.height}")
        else:
            self._document = empty_svg(
                width=self.svg_to_mm(bb.width),
                height=self.svg_to_mm(bb.height),
                viewBox=f"{bb.x} {bb.y} {bb.width} {bb.height}")

        self._defs = etree.SubElement(self._document.getroot(), "defs")
        self._board_cont = etree.SubElement(self._document.getroot(), "g", transform=transform_string)
        if self.get_style("highlight-on-top"):
            self._comp_cont = etree.SubElement(self._document.getroot(), "g", transform=transform_string)
            self._high_cont = etree.SubElement(self._document.getroot(), "g", transform=transform_string)
        else:
            self._high_cont = etree.SubElement(self._document.getroot(), "g", transform=transform_string)
            self._comp_cont = etree.SubElement(self._document.getroot(), "g", transform=transform_string)

        self._board_cont.attrib["id"] = "boardContainer"
        self._comp_cont.attrib["id"] = "componentContainer"
        self._high_cont.attrib["id"] = "highlightContainer"
