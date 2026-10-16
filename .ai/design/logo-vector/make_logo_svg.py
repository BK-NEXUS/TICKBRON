"""
Draws the TICKBRON logo as clean vector SVG (no raster, no sketch texture) into public/brand/.

The design follows the client's pencil drawing (tools/tickbron-logo-source.jpg): a ribbon of three
towers standing on a base line, a palm tree on each side, the name in Roman capitals, a gold rule
with a star, and a tagline. The name and the tagline are converted to outlines (Cinzel, SIL Open
Font License, tools/fonts/), so the SVG needs no font at run time.

  tickbron-logo.svg / tickbron-logo-dark.svg   full lockup, for light and dark pages
  tickbron-mark.svg / tickbron-mark-dark.svg   the symbol alone, for small sizes
  favicon.svg                                  the symbol on a cream rounded square

Run from frontend/:  python3 tools/make_logo_svg.py   (needs fonttools)
then:                node tools/render_icons.mjs      (favicon.ico, favicon-32.png, apple-touch-icon.png)
"""
import math
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont

HERE = Path(__file__).resolve().parent
FONTS = HERE / 'fonts'

W = 942          # width of the drawing
BASE_Y = 501     # centre line of the base of the towers
RIBBON = 24      # thickness of the ribbon (front face)
DEPTH = (15, -10)  # how far the side face reaches (right and up)
DEPTH_STEPS = 15

PALETTES = {
    'light': {
        'gold_top': '#F0CB5A', 'gold_bottom': '#C9962B', 'rim': '#8E6A18',
        'side': '#7A5C1C', 'side_edge': '#5E4614',
        'frond_light': '#D9A92E', 'frond_dark': '#3C3424', 'trunk_top': '#9C7A22', 'trunk_bottom': '#4A3D22',
        'ink': '#2B261C', 'rule': '#C9962B',
    },
    'dark': {
        'gold_top': '#F5D468', 'gold_bottom': '#D3A235', 'rim': '#F8E39A',
        'side': '#9A7A2A', 'side_edge': '#7C5F1D',
        'frond_light': '#E6BC45', 'frond_dark': '#D9CFB8', 'trunk_top': '#D2AE4B', 'trunk_bottom': '#B8AB8E',
        'ink': '#EDE5D2', 'rule': '#D3A235',
    },
}


def fmt(v):
    return f'{v:.1f}'.rstrip('0').rstrip('.')


# ---------------------------------------------------------------- towers
RIBBON_POINTS = [
    (200, BASE_Y), (290, BASE_Y), (290, 180), (356, 180), (356, BASE_Y),
    (424, BASE_Y), (424, 18), (518, 18), (518, BASE_Y),
    (586, BASE_Y), (586, 116), (652, 116), (652, BASE_Y), (742, BASE_Y),
]


def ribbon_path():
    return 'M' + ' L'.join(f'{x} {y}' for x, y in RIBBON_POINTS)


def towers(p):
    d = ribbon_path()
    steps = []
    for k in range(DEPTH_STEPS, 0, -1):
        dx, dy = DEPTH[0] * k / DEPTH_STEPS, DEPTH[1] * k / DEPTH_STEPS
        color = p['side_edge'] if k > DEPTH_STEPS - 2 else p['side']
        steps.append(f'<path d="{d}" transform="translate({fmt(dx)} {fmt(dy)})" stroke="{color}"/>')
    side = f'<g fill="none" stroke-width="{RIBBON}" stroke-linejoin="miter" stroke-linecap="butt">' + ''.join(steps) + '</g>'
    front = (
        f'<path d="{d}" fill="none" stroke="{p["rim"]}" stroke-width="{RIBBON + 3}" stroke-linejoin="miter" stroke-linecap="butt"/>'
        f'<path d="{d}" fill="none" stroke="url(#gold)" stroke-width="{RIBBON - 3}" stroke-linejoin="miter" stroke-linecap="butt"/>'
    )
    return side + front


# ---------------------------------------------------------------- palms
def bezier(p0, p1, p2, t):
    u = 1 - t
    return (u * u * p0[0] + 2 * u * t * p1[0] + t * t * p2[0], u * u * p0[1] + 2 * u * t * p1[1] + t * t * p2[1])


def frond(cx, cy, angle, length, droop, p, teeth=13):
    """
    One palm frond as a feather: a curved spine with a notched edge on both sides.
    The side facing up is gold, the side facing down is dark.
    """
    a = math.radians(angle)
    tip = (cx + length * math.cos(a), cy - length * math.sin(a) + droop)
    ctrl = (cx + length * 0.5 * math.cos(a), cy - length * 0.5 * math.sin(a) - length * 0.2)
    steps = teeth * 2
    spine = [bezier((cx, cy), ctrl, tip, i / steps) for i in range(steps + 1)]
    widest = length * 0.24

    def edge(sign, fullness):
        points = [spine[0]]
        for i in range(1, steps + 1):
            t = i / steps
            (x0, y0), (x1, y1) = spine[i - 1], spine[min(i + 1, steps)]
            tx, ty = x1 - x0, y1 - y0
            norm = math.hypot(tx, ty) or 1
            tx, ty = tx / norm, ty / norm
            nx, ny = -ty * sign, tx * sign
            width = fullness * widest * math.sin(math.pi * t ** 0.85) ** 0.9
            if i % 2 == 1:   # a leaflet tip: reaches out and leans toward the tip of the frond
                x, y = spine[i][0] + nx * width + tx * width * 0.5, spine[i][1] + ny * width + ty * width * 0.5 + width * 0.25
            else:            # the notch between two leaflets
                x, y = spine[i][0] + nx * width * 0.42, spine[i][1] + ny * width * 0.42
            points.append((x, y))
        return points

    def polygon(points, color):
        d = 'M' + ' L'.join(f'{fmt(x)} {fmt(y)}' for x, y in points + spine[::-1]) + 'Z'
        return f'<path d="{d}" fill="{color}"/>'

    # the edge that lies higher on the screen near the middle is the "upper" one: full and gold;
    # the lower one is narrower and dark
    probe = [edge(1, 1.0)[steps // 2][1], edge(-1, 1.0)[steps // 2][1]]
    up_sign = 1 if probe[0] <= probe[1] else -1
    upper, lower = edge(up_sign, 1.0), edge(-up_sign, 0.7)
    vein = 'M' + ' L'.join(f'{fmt(x)} {fmt(y)}' for x, y in spine)
    return (
        polygon(lower, p['frond_dark']) + polygon(upper, p['frond_light'])
        + f'<path d="{vein}" fill="none" stroke="{p["trunk_bottom"]}" stroke-width="1.8" stroke-linecap="round"/>'
    )


FRONDS = [  # angle (degrees, 0 = right, 90 = up), length, droop
    (170, 152, 52), (144, 134, 24), (118, 108, 4), (90, 90, -6), (62, 100, 4), (36, 116, 20), (10, 124, 44),
    (198, 112, 70), (-18, 100, 62),
]


def palm(cx, cy, base, lean, p, mirror=False):
    """A palm with its crown at (cx, cy) and the foot of the trunk at `base`."""
    sign = -1 if mirror else 1
    bx, by = base
    c1 = (bx + lean * sign, by - (by - cy) * 0.45)
    trunk_w_base, trunk_w_top = 20, 9
    pts = [bezier((bx, by), c1, (cx, cy), i / 12) for i in range(13)]
    left, right = [], []
    for i, (x, y) in enumerate(pts):
        j = min(i + 1, 12)
        tx, ty = pts[j][0] - pts[max(i - 1, 0)][0], pts[j][1] - pts[max(i - 1, 0)][1]
        norm = math.hypot(tx, ty) or 1
        nx, ny = -ty / norm, tx / norm
        w = (trunk_w_base + (trunk_w_top - trunk_w_base) * i / 12) / 2
        left.append((x + nx * w, y + ny * w))
        right.append((x - nx * w, y - ny * w))
    outline = 'M' + ' L'.join(f'{fmt(x)} {fmt(y)}' for x, y in left + right[::-1]) + 'Z'
    rings = ''.join(
        f'<path d="M{fmt(left[i][0])} {fmt(left[i][1])} L{fmt(right[i][0])} {fmt(right[i][1])}" stroke="{p["trunk_bottom"]}" stroke-width="1.6" opacity=".55"/>'
        for i in range(2, 12, 2)
    )
    fronds = ''.join(frond(cx, cy, (180 - a) if mirror else a, length, droop, p) for a, length, droop in FRONDS)
    nut = f'<circle cx="{cx}" cy="{cy + 3}" r="7" fill="{p["trunk_top"]}"/>'
    return f'<path d="{outline}" fill="url(#trunk)"/>{rings}{fronds}{nut}'


def symbol(p):
    ground = f'<path d="M130 {BASE_Y + 13} H812" stroke="{p["frond_dark"]}" stroke-width="2" opacity=".35" stroke-linecap="round" fill="none"/>'
    return (
        ground
        + palm(140, 312, (180, BASE_Y + 12), -12, p)
        + palm(802, 312, (762, BASE_Y + 12), -12, p, mirror=True)
        + towers(p)
    )


# ---------------------------------------------------------------- text
class Face:
    def __init__(self, file):
        self.font = TTFont(file)
        self.glyphs = self.font.getGlyphSet()
        self.cmap = self.font.getBestCmap()
        self.upm = self.font['head'].unitsPerEm
        self.cap = self.font['OS/2'].sCapHeight

    def advance(self, ch):
        return self.glyphs[self.cmap[ord(ch)]].width

    def outline(self, text, cap_height, spacing, x_center, baseline):
        """The text as one SVG path, centred on x_center, with `spacing` extra units between letters."""
        scale = cap_height / self.cap
        widths = [self.advance(ch) * scale for ch in text]
        total = sum(widths) + spacing * (len(text) - 1)
        x = x_center - total / 2
        parts = []
        for ch, width in zip(text, widths):
            if ch != ' ':
                pen = SVGPathPen(self.glyphs)
                self.glyphs[self.cmap[ord(ch)]].draw(pen)
                parts.append(f'<path transform="translate({fmt(x)} {fmt(baseline)}) scale({scale:.5f} {-scale:.5f})" d="{pen.getCommands()}"/>')
            x += width + spacing
        return ''.join(parts), total


def fit_spacing(face, text, cap_height, target_width):
    scale = cap_height / face.cap
    natural = sum(face.advance(ch) * scale for ch in text)
    return (target_width - natural) / (len(text) - 1)


def star(cx, cy, r, color):
    k = r * 0.22
    d = f'M{cx} {cy - r} L{cx + k} {cy - k} L{cx + r} {cy} L{cx + k} {cy + k} L{cx} {cy + r} L{cx - k} {cy + k} L{cx - r} {cy} L{cx - k} {cy - k}Z'
    return f'<path d="{d}" fill="{color}"/>'


def lockup(p, name_face, tag_face):
    name_cap, name_base = 96, 668
    name_spacing = fit_spacing(name_face, 'TICKBRON', name_cap, W)
    name, _ = name_face.outline('TICKBRON', name_cap, name_spacing, W / 2, name_base)
    tag_cap, tag_base = 21, 786
    tag_spacing = fit_spacing(tag_face, 'ONLINE BOOKING APP', tag_cap, 640)
    tag, _ = tag_face.outline('ONLINE BOOKING APP', tag_cap, tag_spacing, W / 2, tag_base)
    rule_y = 716
    rules = (
        f'<path d="M142 {rule_y} H414 M528 {rule_y} H800" stroke="{p["rule"]}" stroke-width="2.4" stroke-linecap="round" fill="none"/>'
        + star(471, rule_y, 15, p['rule'])
    )
    return f'<g fill="{p["ink"]}">{name}{tag}</g>{rules}'


def defs(p):
    return (
        '<defs>'
        f'<linearGradient id="gold" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="0" y2="{BASE_Y + 20}">'
        f'<stop offset="0" stop-color="{p["gold_top"]}"/><stop offset="1" stop-color="{p["gold_bottom"]}"/></linearGradient>'
        '<linearGradient id="trunk" x1="0" y1="1" x2="0" y2="0">'
        f'<stop offset="0" stop-color="{p["trunk_bottom"]}"/><stop offset="1" stop-color="{p["trunk_top"]}"/></linearGradient>'
        '</defs>'
    )


def svg(body, p, view_box, title):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{view_box}" role="img" aria-label="{title}">'
        f'<title>{title}</title>{defs(p)}{body}</svg>\n'
    )


def build(theme, out_dir, name_face, tag_face):
    p = PALETTES[theme]
    suffix = '' if theme == 'light' else '-dark'
    mark_view = f'-14 4 {W + 28} {BASE_Y + 40}'
    lockup_view = f'-14 4 {W + 28} {800 - 4}'
    title = 'TICKBRON — Online Booking'
    (out_dir / f'tickbron-mark{suffix}.svg').write_text(svg(symbol(p), p, mark_view, title))
    (out_dir / f'tickbron-logo{suffix}.svg').write_text(svg(symbol(p) + lockup(p, name_face, tag_face), p, lockup_view, title))


def favicon(p):
    """The symbol on a cream rounded square; the symbol is centred and fills most of the width."""
    scale = 0.86 * 100 / (W + 28)
    inner = (f'<g transform="translate({fmt(7 + 14 * scale)} {fmt(50 - (BASE_Y + 40) * scale / 2 - 4 * scale)}) scale({scale:.5f})">'
             + symbol(p) + '</g>')
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
        f'{defs(p)}<rect width="100" height="100" rx="18" fill="#F3EDE5"/>{inner}</svg>\n'
    )


if __name__ == '__main__':
    OUT = HERE.parent / 'public' / 'brand'
    out = OUT
    name = Face(FONTS / 'cinzel-latin-600-normal.woff')
    tag = Face(FONTS / 'cinzel-latin-400-normal.woff')
    for theme in ('light', 'dark'):
        build(theme, out, name, tag)
    (out / 'favicon.svg').write_text(favicon(PALETTES['light']))
    print([f.name for f in sorted(out.glob('*.svg'))])
