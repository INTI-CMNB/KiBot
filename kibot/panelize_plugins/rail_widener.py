"""
Rail widener KiKit FramingPlugin.

Builds the normal KiKit rail/frame (whichever `type` the user actually asked
for) and then unions in a solid rectangular patch at one or more outer panel
corners. The patch is meant to give pick-and-place photoelectric sensors a
bigger flat target than the configured rail width would otherwise provide,
without growing the panel's outer outline and without ever overlapping the
actual board(s):

- `width` (depth, perpendicular to the nearest rail edge) and `length`
  (extent along the rail edge) grow the patch as far as requested, towards
  the board. The backstop is the board outline itself, expanded by `gap`:
  whatever part of the patch would come closer than `gap` to a board gets
  clipped away (geometric subtraction), so it can never cut into, touch or
  grow past the board regardless of rail `width`.

  KiKit runs its own reverse-tab-fillet pass right after framing
  (`buildTabFillets`, driven by `tabs.fillet`) that rounds the transition
  between *any* new frame material - including this patch - and the board,
  which would otherwise silently eat into (or fully close) our gap. We
  compensate by adding `tabs.fillet` to the clip distance, so the gap that
  survives after KiKit's own pass matches what was actually requested.

  The patch also introduces one new concave ("step") corner where it returns
  to the normal rail width - unlike the panel's own outer corners this isn't
  touched by `framing.fillet`, yet it needs the same treatment: a sharp
  concave corner isn't actually millable with a round tool, same reason the
  rest of the rail is filleted. We add an exact tangent-arc patch (radius =
  `framing.fillet`) at that one point only - computed directly from the
  known corner/step geometry, not a broad buffer operation - so nothing else
  (the gap to the board, the panel's true outer corner, pre-existing tab
  notches) can be affected.

Driven by KiBot's `panelize.framing.widenercorners/widenerwidth/widenerlength`
options (see PanelizeFraming.config() in kibot/out_panelize.py), which set
`framing.type: plugin` and point `code`/`arg` at this class.
"""
import json
from shapely.geometry import box, Point
from shapely.ops import unary_union
from kikit.plugin import FramingPlugin
from kikit.panelize_ui_impl import buildFraming as kikit_build_framing

# Index into panel.panelCorners() -> [topLeft, topRight, bottomLeft, bottomRight]
_CORNER_INDEX = {'tl': 0, 'tr': 1, 'bl': 2, 'br': 3}
# Direction the patch grows from the corner point, towards the panel interior
_CORNER_SIGN = {'tl': (1, 1), 'tr': (-1, 1), 'bl': (1, -1), 'br': (-1, -1)}
# Which axis is the rail's thin (thickness) direction near each corner, for a given base type
_DEPTH_AXIS = {'railstb': 'y', 'railslr': 'x', 'frame': 'y', 'tightframe': 'y'}


class RailWidenerFramingPlugin(FramingPlugin):
    def __init__(self, preset, userArg):
        super().__init__(preset, userArg)
        self.arg = json.loads(userArg)

    def buildDummyFramingSubstrates(self, substrates):
        # The widener only adds material at the outer corners, it doesn't
        # affect where tabs/partition lines should be computed
        return substrates

    def buildFraming(self, panel):
        framingPreset = self.preset['framing']
        base_type = self.arg['type']
        if base_type not in ('railstb', 'railslr', 'frame', 'tightframe'):
            raise ValueError(f'Rail widener: unsupported base framing type `{base_type}`')

        # Delegate to KiKit's own dispatcher (with `type` restored to the real
        # base type) so we track whatever KiKit version is installed instead
        # of duplicating its per-type builder call signatures here
        inner_preset = dict(self.preset)
        inner_preset['framing'] = dict(framingPreset)
        inner_preset['framing']['type'] = base_type
        cuts = list(kikit_build_framing(inner_preset, panel))

        depth = self.arg['width']
        length = self.arg['length']
        # KiKit's own buildTabFillets() runs after buildFraming() and rounds
        # the join between any new frame material and the board using this
        # radius, which would otherwise eat into (or fully swallow) our gap
        tabs_fillet = self.preset.get('tabs', {}).get('fillet', 0) or 0
        gap = self.arg['gap'] + tabs_fillet
        boards = unary_union([s.substrates for s in panel.substrates]) if panel.substrates else None
        if boards is not None and gap > 0:
            boards = boards.buffer(gap)

        fillet = framingPreset['fillet']
        rail_width = framingPreset['width']
        minx, miny, maxx, maxy = panel.panelBBox()
        panel_w, panel_h = maxx - minx, maxy - miny
        corners = panel.panelCorners()
        for name in self.arg['corners']:
            corner = corners[_CORNER_INDEX[name]]
            sx, sy = _CORNER_SIGN[name]
            axis_y = _DEPTH_AXIS[base_type] == 'y'
            if axis_y:
                dx = min(length, panel_w / 2)
                dy = depth
            else:
                dx = depth
                dy = min(length, panel_h / 2)
            x0, x1 = sorted((corner.x, corner.x + sx * dx))
            y0, y1 = sorted((corner.y, corner.y + sy * dy))
            patch = box(x0, y0, x1, y1)
            if boards is not None:
                # Never let the patch come closer than `gap` to an actual
                # board, no matter how deep it was requested to grow
                patch = patch.difference(boards)
            panel.appendSubstrate(patch)

            # Exact tangent-arc fillet at the single concave step point, only
            # when there actually is a step (patch deeper/longer than the
            # plain rail) and it doesn't reach all the way to the next corner
            if fillet > 0 and depth > rail_width and (dx if axis_y else dy) < (panel_w / 2 if axis_y else panel_h / 2):
                if axis_y:
                    px, py = corner.x + sx * dx, corner.y + sy * rail_width
                else:
                    px, py = corner.x + sx * rail_width, corner.y + sy * dy
                cx, cy = px + sx * fillet, py + sy * fillet
                square = box(min(px, cx), min(py, cy), max(px, cx), max(py, cy))
                fillet_patch = square.difference(Point(cx, cy).buffer(fillet, quad_segs=32))
                panel.appendSubstrate(fillet_patch)

        return cuts
