from lxml import etree
from copy import deepcopy
import codecs
from typing import Optional

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

SVG_NAMESPACE = "http://www.w3.org/2000/svg"
XLINK_NAMESPACE = "http://www.w3.org/1999/xlink"
SVG = "{%s}" % SVG_NAMESPACE
XLINK = "{%s}" % XLINK_NAMESPACE
NSMAP = {None: SVG_NAMESPACE, "xlink": XLINK_NAMESPACE}


class FigureElement(object):
    """Base class representing single figure element"""

    def __init__(self, xml_element, defs=None):

        self.root = xml_element

    def moveto(self, x, y, scale_x=1, scale_y=None):
        """Move and scale element.

        Parameters
        ----------
        x, y : float
             displacement in x and y coordinates in user units ('px').
        scale_x : float
             x-direction scaling factor. To scale down scale_x < 1,  scale up scale_x > 1.
        scale_y : (optional) float
             y-direction scaling factor. To scale down scale_y < 1,  scale up scale_y > 1.
             If set to default (None), then scale_y=scale_x.
        """
        if scale_y is None:
            scale_y = scale_x
        self.root.set(
            "transform",
            "translate(%s, %s) scale(%s %s) %s"
            % (x, y, scale_x, scale_y, self.root.get("transform") or ""),
        )

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
        self.root.set(
            "transform",
            "%s rotate(%f %f %f)" % (self.root.get("transform") or "", angle, x, y),
        )

    def skew(self, x=0, y=0):
        """Skew the element by x and y degrees
        Convenience function which calls skew_x and skew_y

        Parameters
        ----------
        x,y : float, float
            skew angle in degrees (default 0)

            If an x/y angle is given as zero degrees, that transformation is omitted.
        """
        if x != 0:
            self.skew_x(x)
        if y != 0:
            self.skew_y(y)

        return self

    def skew_x(self, x):
        """Skew element along the x-axis by the given angle.

        Parameters
        ----------
        x : float
            x-axis skew angle in degrees
        """
        self.root.set(
            "transform", "%s skewX(%f)" % (self.root.get("transform") or "", x)
        )
        return self

    def skew_y(self, y):
        """Skew element along the y-axis by the given angle.

        Parameters
        ----------
        y : float
            y-axis skew angle in degrees
        """
        self.root.set(
            "transform", "%s skewY(%f)" % (self.root.get("transform") or "", y)
        )
        return self

    def scale(self, x=0, y=None):
        """Scale element separately across the two axes x and y.
            If y is not provided, it is assumed equal to x (according to the
            W3 specification).

        Parameters
        ----------
        x : float
            x-axis scaling factor. To scale down x < 1, scale up x > 1.
        y : (optional) float
            y-axis scaling factor. To scale down y < 1, scale up y > 1.

        """
        self.moveto(0, 0, x, y)
        return self

    def __getitem__(self, i):
        return FigureElement(self.root.getchildren()[i])

    def copy(self):
        """Make a copy of the element"""
        return deepcopy(self.root)

    def tostr(self):
        """String representation of the element"""
        return etree.tostring(self.root, pretty_print=True)

    def find_id(self, element_id):
        """Find element by its id.

        Parameters
        ----------
        element_id : str
            ID of the element to find

        Returns
        -------
        FigureElement
            one of the children element with the given ID."""
        find = etree.XPath("//*[@id=$id]")
        return FigureElement(find(self.root, id=element_id)[0])


class TextElement(FigureElement):
    """Text element.

    Corresponds to SVG ``<text>`` tag."""

    def __init__(
        self,
        x,
        y,
        text: str,
        size: int = 8,
        font="Verdana",
        weight="normal",
        letterspacing=0,
        anchor="start",
        color="black",
        lengthAdjust=None,
        textLength=None,
    ):
        attrs = {
            "x": str(x),
            "y": str(y),
            "font-size": str(size),
            "font-family": font,
            "font-weight": weight,
            "letter-spacing": str(letterspacing),
            "text-anchor": str(anchor),
            "fill": str(color),
        }
        if lengthAdjust is not None:
            attrs['lengthAdjust'] = lengthAdjust
        if textLength is not None:
            attrs['textLength'] = textLength
        txt = etree.Element(SVG + "text", attrs)
        txt.text = text
        FigureElement.__init__(self, txt)


class ImageElement(FigureElement):
    """Inline image element.

    Corresponds to SVG ``<image>`` tag. Image data encoded as base64 string.
    """

    def __init__(self, stream, width: int, height, format="png"):
        base64str = codecs.encode(stream.read(), "base64").rstrip()
        uri = "data:image/{};base64,{}".format(format, base64str.decode("ascii"))
        attrs = {"width": str(width), "height": str(height), XLINK + "href": uri}
        img = etree.Element(SVG + "image", attrs)
        FigureElement.__init__(self, img)


class LineElement(FigureElement):
    """Line element.

    Corresponds to SVG ``<path>`` tag. It handles only piecewise
    straight segments
    """

    def __init__(self, points, width: int = 1, color="black"):
        linedata = "M{} {} ".format(*points[0])
        linedata += " ".join(("L{} {}".format(*x) for x in points[1:]))
        line = etree.Element(
            SVG + "path", {"d": linedata, "stroke-width": str(width), "stroke": color}
        )
        FigureElement.__init__(self, line)


class RectElement(FigureElement):
    """Rectangle element.

    Corresponds to SVG ``<rect>`` tag.
    """

    def __init__(self, x, y, w, h, color="black"):
        line = etree.Element(
            SVG + "rect", {"x": str(x), "y": str(y), "width": str(w), "height": str(h), "fill": color}
        )
        FigureElement.__init__(self, line)


class GroupElement(FigureElement):
    """Group element.

    Container for other elements. Corresponds to SVG ``<g>`` tag.
    """

    def __init__(self, element_list, attrib=None):
        new_group = etree.Element(SVG + "g", attrib=attrib)
        for e in element_list:
            if isinstance(e, FigureElement):
                new_group.append(e.root)
            else:
                new_group.append(e)
        self.root = new_group


class SVGFigure(object):
    """SVG Figure.

    It setups standalone SVG tree. It corresponds to SVG ``<svg>`` tag.
    """

    def __init__(self, width: Optional[int] = None, height=None):
        self.root = etree.Element(SVG + "svg", nsmap=NSMAP)
        self.root.set("version", "1.1")

        self._width = 0
        self._height = 0

        if width:
            try:
                self.width = width  # this goes to @width.setter a few lines down
            except AttributeError:
                # int or str
                self._width = width

        if height:
            try:
                self.height = height  # this goes to @height.setter a few lines down
            except AttributeError:
                self._height = height

    @property
    def width(self):
        """Figure width"""
        return self.root.get("width")

    @width.setter
    def width(self, value):
        self._width = value.value
        self.root.set("width", str(value))
        self.root.set("viewBox", "0 0 %s %s" % (self._width, self._height))

    @property
    def height(self):
        """Figure height"""
        return self.root.get("height")

    @height.setter
    def height(self, value):
        self._height = value.value
        self.root.set("height", str(value))
        self.root.set("viewBox", "0 0 %s %s" % (self._width, self._height))

    def append(self, element):
        """Append new element to the SVG figure"""
        try:
            self.root.append(element.root)
        except AttributeError:
            self.root.append(GroupElement(element).root)

    def insert(self, element, pos=0):
        """Insert new element to the SVG figure, default is at the beginning"""
        try:
            self.root.insert(pos, element.root)
        except AttributeError:
            self.root.insert(pos, GroupElement(element).root)

    def getroot(self):
        """Return the root element of the figure.

        The root element is a group of elements after stripping the toplevel
        ``<svg>`` tag.

        Returns
        -------
        GroupElement
            All elements of the figure without the ``<svg>`` tag.
        """
        if "class" in self.root.attrib:
            attrib = {"class": self.root.attrib["class"]}
        else:
            attrib = None
        return GroupElement(self.root.getchildren(), attrib=attrib)

    def to_str(self):
        """
        Returns a string of the SVG figure.
        """
        return etree.tostring(
            self.root, xml_declaration=True, standalone=True, pretty_print=True
        )

    def save(self, fname, encoding=None):
        """
        Save figure to a file
        Default encoding is "ASCII" when None is specified, as dictated by lxml .
        """
        out = etree.tostring(
            self.root,
            xml_declaration=True,
            standalone=True,
            pretty_print=True,
            encoding=encoding,
        )
        with open(fname, "wb") as fid:
            fid.write(out)

    def find_id(self, element_id):
        """Find elements with the given ID"""
        find = etree.XPath("//*[@id=$id]")
        return FigureElement(find(self.root, id=element_id)[0])

    def get_size(self):
        """Get figure size"""
        return self.root.get("width"), self.root.get("height")

    def set_size(self, size: int):
        """Set figure size"""
        w, h = size
        self.root.set("width", w)
        self.root.set("height", h)


def fromfile(fname):
    """Open SVG figure from file.

    Parameters
    ----------
    fname : str
        name of the SVG file

    Returns
    -------
    SVGFigure
        newly created :py:class:`SVGFigure` initialised with the file content
    """
    fig = SVGFigure()
    with open(fname) as fid:
        svg_file = etree.parse(fid, parser=etree.XMLParser(huge_tree=True))

    fig.root = svg_file.getroot()
    return fig


def fromstring(text: str):
    """Create a SVG figure from a string.

    Parameters
    ----------
    text : str
        string representing the SVG content. Must be valid SVG.

    Returns
    -------
    SVGFigure
        newly created :py:class:`SVGFigure` initialised with the string
        content.
    """
    fig = SVGFigure()
    svg = etree.fromstring(text.encode(), parser=etree.XMLParser(huge_tree=True))

    fig.root = svg

    return fig


def from_mpl(fig, savefig_kw=None):
    """Create a SVG figure from a ``matplotlib`` figure.

    Parameters
    ----------
    fig : matplotlib.Figure instance

    savefig_kw : dict
         keyword arguments to be passed to matplotlib's
         `savefig`



    Returns
    -------
    SVGFigure
        newly created :py:class:`SVGFigure` initialised with the string
        content.


    Examples
    --------

    If you want to overlay the figure on another SVG, you may want to pass
    the `transparent` option:

    >>> from svgutils import transform
    >>> import matplotlib.pyplot as plt
    >>> fig = plt.figure()
    >>> line, = plt.plot([1,2])
    >>> svgfig = transform.from_mpl(fig,
    ...              savefig_kw=dict(transparent=True))
    >>> svgfig.getroot()
    <svgutils.transform.GroupElement object at ...>


    """

    fid = StringIO()
    if savefig_kw is None:
        savefig_kw = {}

    try:
        fig.savefig(fid, format="svg", **savefig_kw)
    except ValueError:
        raise (ValueError, "No matplotlib SVG backend")
    fid.seek(0)
    fig = fromstring(fid.read())

    # workaround mpl units bug
    w, h = fig.get_size()
    fig.set_size((w.replace("pt", ""), h.replace("pt", "")))

    return fig
