# coding=utf-8
"""SVG definitions designed for easy SVG composing

Features:
    * allow for wildcard import
    * defines a mini language for SVG composing
    * short but readable names
    * easy nesting
    * method chaining
    * no boilerplate code (reading files, extracting objects from svg,
                           transversing XML tree)
    * universal methods applicable to all element types
    * don't have to learn python
"""

import os
import re

from . import transform

CONFIG = {
    "svg.file_path": ".",
    "figure.save_path": ".",
    "image.file_path": ".",
    "text.position": (0, 0),
    "text.size": 8,
    "text.weight": "normal",
    "text.font": "Verdana",
}


class Element(transform.FigureElement):
    """Base class for new SVG elements."""

    def rotate(self, angle: float, x=0, y=0):
        """Rotate element by given angle around given pivot.

        Parameters
        ----------
        angle : float
            rotation angle in degrees
        x, y : float
            pivot coordinates in user coordinate system (defaults to top-left
            corner of the figure)
        """
        super(Element, self).rotate(angle, x, y)
        return self

    def move(self, x, y):
        """Move the element by x, y.

        Parameters
        ----------
        x,y : int, str
           amount of horizontal and vertical shift

        Notes
        -----
        The x, y can be given with a unit (for example, "3px",  "5cm"). If no
        unit is given the user unit is assumed ("px"). In SVG all units are
        defined in relation to the user unit [1]_.

        .. [1] W3C SVG specification:
           https://www.w3.org/TR/SVG/coords.html#Units
        """
        self.moveto(x, y)
        return self

    def find_id(self, element_id):
        """Find a single element with the given ID.

        Parameters
        ----------
        element_id : str
            ID of the element to find

        Returns
        -------
        found element
        """
        element = transform.FigureElement.find_id(self, element_id)
        return Element(element.root)

    def find_ids(self, element_ids):
        """Find elements with given IDs.

        Parameters
        ----------
        element_ids : list of strings
            list of IDs to find

        Returns
        -------
        a new `Panel` object which contains all the found elements.
        """
        elements = [transform.FigureElement.find_id(self, eid) for eid in element_ids]
        return Panel(*elements)


class SVG(Element):
    """SVG from file.

    Parameters
    ----------
    fname : str
       full path to the file
    fix_mpl : bool
        replace pt units with px units to fix files created with matplotlib
    """

    def __init__(self, fname=None, fix_mpl=False):
        if fname:
            fname = os.path.join(CONFIG["svg.file_path"], fname)
            svg = transform.fromfile(fname)
            if fix_mpl:
                w, h = svg.get_size()
                svg.set_size((w.replace("pt", ""), h.replace("pt", "")))
            super(SVG, self).__init__(svg.getroot().root)

            # if height/width is in % units, we can't store the absolute values
            if svg.width.endswith("%"):
                self._width = None
            else:
                self._width = Unit(svg.width).to("px")
            if svg.height.endswith("%"):
                self._height = None
            else:
                self._height = Unit(svg.height).to("px")

    @property
    def width(self):
        """Get width of the svg file in px"""
        if self._width:
            return self._width.value

    @property
    def height(self):
        """Get height of the svg file in px"""
        if self._height:
            return self._height.value


class MplFigure(SVG):
    """Matplotlib figure

    Parameters
    ----------
    fig : matplotlib Figure instance
        instance of Figure to be converted
    kws :
        keyword arguments passed to matplotlib's savefig method
    """

    def __init__(self, fig, **kws):
        svg = transform.from_mpl(fig, savefig_kw=kws)
        self.root = svg.getroot().root


class Image(Element):
    """Raster or vector image

    Parameters
    ----------
    width : float
    height : float
        image dimensions
    fname : str
        full path to the file
    """

    def __init__(self, width: int, height, fname):
        fname = os.path.join(CONFIG["image.file_path"], fname)
        _, fmt = os.path.splitext(fname)
        fmt = fmt.lower()[1:]
        with open(fname, "rb") as fid:
            img = transform.ImageElement(fid, width, height, fmt)
        self.root = img.root


class Text(Element):
    """Text element.

    Parameters
    ----------
    text : str
       content
    x, y : float or str
       Text position. If unit is not given it will assume user units (px).
    size : float, optional
       Font size.
    weight : str, optional
       Font weight. It can be one of: normal, bold, bolder or lighter.
    font : str, optional
       Font family.
    """

    def __init__(self, text: str, x=None, y=None, **kwargs):
        params = {
            "size": CONFIG["text.size"],
            "weight": CONFIG["text.weight"],
            "font": CONFIG["text.font"],
        }
        if x is None or y is None:
            x, y = CONFIG["text.position"]
        params.update(kwargs)
        element = transform.TextElement(x, y, text, **params)
        Element.__init__(self, element.root)


class Panel(Element):
    """Figure panel.

    Panel is a group of elements that can be transformed together. Usually
    it relates to a labeled figure panel.

    Parameters
    ----------
    svgelements : objects deriving from Element class
        one or more elements that compose the panel

    Notes
    -----
    The grouped elements need to be properly arranged in scale and position.
    """

    def __init__(self, *svgelements):
        element = transform.GroupElement(svgelements)
        Element.__init__(self, element.root)

    def __iter__(self):
        elements = self.root.getchildren()
        return (Element(el) for el in elements)


class Line(Element):
    """Line element connecting given points.

    Parameters
    ----------
    points : sequence of tuples
        List of point x,y coordinates.
    width : float, optional
        Line width.
    color : str, optional
        Line color. Any of the HTML/CSS color definitions are allowed.
    """

    def __init__(self, points, width: int = 1, color="black"):
        element = transform.LineElement(points, width=width, color=color)
        Element.__init__(self, element.root)


class Grid(Element):
    """Line grid with coordinate labels to facilitate placement of new
    elements.

    Parameters
    ----------
    dx : float
       Spacing between the vertical lines.
    dy : float
       Spacing between horizontal lines.
    size : float or str
       Font size of the labels.

    Notes
    -----
    This element is mainly useful for manual placement of the elements.
    """

    def __init__(self, dx, dy, size: int = 8):
        self.size = size
        lines = self._gen_grid(dx, dy)
        element = transform.GroupElement(lines)
        Element.__init__(self, element.root)

    def _gen_grid(self, dx, dy, width: float = 0.5):
        xmax, ymax = 1000, 1000
        x, y = 0, 0
        lines = []
        txt = []
        while x < xmax:
            lines.append(transform.LineElement([(x, 0), (x, ymax)], width=width))
            txt.append(transform.TextElement(x, dy / 2, str(x), size=self.size))
            x += dx
        while y < ymax:
            lines.append(transform.LineElement([(0, y), (xmax, y)], width=width))
            txt.append(transform.TextElement(0, y, str(y), size=self.size))
            y += dy
        return lines + txt


class Figure(Panel):
    """Main figure class.

    This should be always the top class of all the generated SVG figures.

    Parameters
    ----------
    width, height : float or str
        Figure size. If unit is not given, user units (px) are assumed.
    """

    def __init__(self, width: int, height, *svgelements):
        Panel.__init__(self, *svgelements)
        self.width = Unit(width)
        self.height = Unit(height)

    def save(self, fname):
        """Save figure to SVG file.

        Parameters
        ----------
        fname : str
            Full path to file.
        """
        element = transform.SVGFigure(self.width, self.height)
        element.append(self)
        element.save(os.path.join(CONFIG["figure.save_path"], fname))

    def tostr(self):
        """Export SVG as a string"""
        element = transform.SVGFigure(self.width, self.height)
        element.append(self)
        svgstr = element.to_str()
        return svgstr

    def _repr_svg_(self):
        return self.tostr().decode("ascii")

    def tile(self, ncols, nrows):
        """Automatically tile the panels of the figure.

        This will re-arranged all elements of the figure (first in the
        hierarchy) so that they will uniformly cover the figure area.

        Parameters
        ----------
        ncols, nrows : type
            The number of columns and rows to arrange the elements into.


        Notes
        -----
        ncols * nrows must be larger or equal to number of
        elements, otherwise some elements will go outside the figure borders.
        """
        dx = (self.width / ncols).to("px").value
        dy = (self.height / nrows).to("px").value
        ix, iy = 0, 0
        for el in self:
            el.move(dx * ix, dy * iy)
            ix += 1
            if ix >= ncols:
                ix = 0
                iy += 1
            if iy > nrows:
                break
        return self


class Unit:
    """Implementation of SVG units and conversions between them.

    Parameters
    ----------
    measure : str
        value with unit (for example, '2cm')
    """

    per_inch = {"px": 90, "cm": 2.54, "mm": 25.4, "pt": 72.0}

    def __init__(self, measure):
        try:
            self.value = float(measure)
            self.unit = "px"
        except ValueError:
            m = re.match(r"([0-9]+\.?[0-9]*)([a-z]+)", measure)
            value, unit = m.groups()
            self.value = float(value)
            self.unit = unit

    def to(self, unit):
        """Convert to a given unit.

        Parameters
        ----------
        unit : str
           Name of the unit to convert to.

        Returns
        -------
        u : Unit
            new Unit object with the requested unit and computed value.
        """
        u = Unit("0cm")
        u.value = self.value / self.per_inch[self.unit] * self.per_inch[unit]
        u.unit = unit
        return u

    def __str__(self) -> str:
        return "{}{}".format(self.value, self.unit)

    def __repr__(self) -> str:
        return "Unit({})".format(str(self))

    def __mul__(self, number: int):
        u = Unit("0cm")
        u.value = self.value * number
        u.unit = self.unit
        return u

    def __truediv__(self, number: int):
        return self * (1.0 / number)

    def __div__(self, number: int):
        return self * (1.0 / number)
