# -*- coding: utf-8; -*-
"""Colorize terminal output.

Use Colorama if available; works on any OS.

If not available, and OS is a *nix, use ANSI escape codes.
"""

__all__ = ["setcolor", "colorize", "ColorScheme",
           "Fore", "Back", "Style"]

try:
    from colorama import Back, Fore, Style  # type: ignore[import]
    from colorama import init as colorama_init  # type: ignore[import]
    colorama_init()
except ImportError:  # pragma: no cover
    # The `ansi` module is a slightly modified, POSIX-only,
    # vendored version from Colorama. Useful e.g. in Docker
    # images that don't have the library available.
    from .ansi import Fore, Back, Style  # noqa: F811

# TODO: Get rid of this hack if Colorama adds these styles later.
# Inject some styles missing from Colorama 0.4.4
_additional_styles = (("ITALIC", "\33[3m"),
                      ("URL", "\33[4m"),  # underline plus possibly a special color (depends on terminal app)
                      ("BLINK", "\33[5m"),
                      ("BLINK2", "\33[6m"))  # same effect as BLINK?
for _name, _value in _additional_styles:
    if not hasattr(Style, _name):
        setattr(Style, _name, _value)
del _name, _value

from .bunch import Bunch


def setcolor(*colors, reset=True):
    """Set color for terminal display.

    Returns a string that, when printed into a terminal, sets the style
    and color.

    If `reset=True`, reset style and color before setting the requested
    style and color.

    If `reset=False`, augment current style and color. E.g. if `Style.BRIGHT`
    is already active, and you set `Fore.BLUE`, the style will remain BRIGHT,
    and color will be BLUE.

    For available `colors`, see `Fore`, `Back` and `Style`.

    Each entry can also be a tuple (arbitrarily nested), which is useful
    for defining compound styles.

    **CAUTION**: The specified style and color remain in effect until another
    explicit call to `setcolor`. To reset, use `setcolor()`.

    If you want to colorize a piece of text so that the color and style
    auto-reset after your text, use `colorize` instead.
    """
    def _setcolor(color):
        if isinstance(color, (list, tuple)):
            return "".join(_setcolor(elt) for elt in color)
        return color
    out = [_setcolor(Style.RESET_ALL)] if reset else []
    out.append(_setcolor(colors))
    return "".join(out)


def colorize(text: str, *colors) -> str:
    """Colorize string `text` for terminal display.

    Always reset style and color at the start of `text`, as well as after it.

    Returns `text`, augmented with color and style commands for terminals.

    For available `colors`, see `Fore`, `Back` and `Style`.

    Usage::

        print(colorize("I'm new here", Fore.GREEN))
        print(colorize("I'm bold and bluetiful", Style.BRIGHT, Fore.BLUE))

    Each entry can also be a tuple (arbitrarily nested), which is useful
    for defining compound styles::

        BRIGHT_BLUE = (Style.BRIGHT, Fore.BLUE)
        ...
        print(colorize("I'm bold and bluetiful, too", BRIGHT_BLUE))

    **CAUTION**: Does not nest. If you want to set a color and style
    until further notice, use `setcolor` instead.
    """
    return "{}{}{}".format(setcolor(colors),
                           text,
                           setcolor())


class ColorScheme(Bunch):
    """The color scheme for terminal output in `mcpyrate`'s debug utilities.

    This is just a bunch of constants. To change the colors, simply assign new
    values to them. Changes take effect immediately for any new output.

    To replace the whole color scheme at once, fill in a suitable `Bunch`, and
    then use the `replace` method. If you need to get the names of all settings
    programmatically, call the `keys` method.

    Don't replace the color scheme object itself; all the use sites
    from-import it.

    See `Fore`, `Back`, `Style` for valid values. To make a compound style,
    place the values into a tuple.

    The defaults are designed to fit the "Solarized" (Zenburn-like) theme
    of `gnome-terminal`, with "Show bold text in bright colors" set to OFF.
    But they work also with "Tango", and indeed with most themes.
    """
    def __init__(self):
        super().__init__()

        # ------------------------------------------------------------
        # unparse

        self.LINENUMBER = Style.DIM

        self.LANGUAGEKEYWORD = (Style.BRIGHT, Fore.YELLOW)  # for, if, import, ...
        self.BUILTINEXCEPTION = Fore.CYAN  # TypeError, ValueError, Warning, ...
        self.BUILTINOTHER = Style.BRIGHT  # str, property, print, ...

        self.DEFNAME = (Style.BRIGHT, Fore.CYAN)  # name of a function or class being defined
        self.DECORATOR = Fore.LIGHTBLUE_EX

        # These can be highlighted differently although Python 3.8+ uses `Constant` for all.
        self.STRING = Fore.GREEN
        self.NUMBER = Fore.GREEN
        self.NAMECONSTANT = Fore.GREEN  # True, False, None

        # Macro names are syntax-highlighted when a macro expander instance is
        # running and is provided to `unparse`, so it can query for bindings.
        # `step_expansion` does that automatically.
        #
        # So they won't yet be highlighted during dialect AST transforms,
        # because at that point, there is no *macro* expander.
        self.MACRONAME = Fore.BLUE

        self.INVISIBLENODE = Style.DIM  # AST node with no surface syntax repr (`Module`, `Expr`)

        # AST markers for data-driven communication within the macro expander
        self.ASTMARKER = Style.DIM  # the "$AstMarker" title
        self.ASTMARKERCLASS = Fore.YELLOW  # the actual marker type name

        # ------------------------------------------------------------
        # format_bindings, step_expansion, StepExpansion

        self.HEADING1 = (Style.BRIGHT, Fore.LIGHTBLUE_EX)  # main heading
        self.HEADING2 = Fore.LIGHTBLUE_EX  # subheading (filenames, tree ids, ...)
        self.SOURCEFILENAME = Style.BRIGHT

        # format_bindings
        self.GREYEDOUT = Style.DIM  # if no bindings

        # StepExpansion
        self.ATTENTION = (Style.BRIGHT, Fore.GREEN)  # "DialectExpander debug mode", "PHASE 0"
        self.TRANSFORMERKIND = (Style.BRIGHT, Fore.GREEN)  # "source", "AST"
        self.DIALECTTRANSFORMERNAME = (Style.BRIGHT, Fore.YELLOW)

        # ------------------------------------------------------------
        # dump

        self.NODETYPE = (Style.BRIGHT, Fore.LIGHTBLUE_EX)
        self.FIELDNAME = Fore.YELLOW
        self.BAREVALUE = Fore.GREEN

        # ------------------------------------------------------------
        # runtests
        self.TESTHEADING = self.HEADING1
        self.TESTPASS = (Style.BRIGHT, Fore.GREEN)
        self.TESTFAIL = (Style.BRIGHT, Fore.RED)
        self.TESTERROR = (Style.BRIGHT, Fore.YELLOW)
ColorScheme = ColorScheme()  # type: ignore[assignment, misc]
