"""
Builds the logo files in public/brand/ from the client's drawing (tools/tickbron-logo-source.jpg).

The drawing is a pencil sketch on cream paper. The paper is removed by "difference matting": the
paper color under the drawing is estimated (dilate away the strokes, blur), and every pixel's alpha
is how much darker than that paper it is, so the pencil texture stays and the box disappears.

  tickbron-logo.webp / tickbron-logo-dark.webp   full lockup (symbol, name, line), light and dark theme
  tickbron-mark.webp / tickbron-mark-dark.webp   the symbol only (towers and palms), for small sizes
  favicon-32.png, apple-touch-icon.png, favicon.ico   the symbol on the cream background

Run from frontend/:  python3 tools/make_logo.py   (needs Pillow and numpy)
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

HERE = Path(__file__).resolve().parent
SOURCE = HERE / 'tickbron-logo-source.jpg'
OUT = HERE.parent / 'public' / 'brand'

CREAM = (243, 237, 229)        # --color-background-alt, the page color behind the logo
INK_ON_DARK = (222, 213, 196)  # the dark pencil lines become this on the dark theme
LOCKUP_WIDTH = 720
MARK_WIDTH = 480


def smoothstep(edge0, edge1, x):
    t = np.clip((x - edge0) / (edge1 - edge0), 0, 1)
    return t * t * (3 - 2 * t)


def paper_estimate(img):
    channels = []
    for channel in img.split():
        bright = channel.filter(ImageFilter.MaxFilter(51)).filter(ImageFilter.GaussianBlur(25))
        channels.append(np.asarray(bright, dtype=np.float64))
    return np.stack(channels, axis=-1)


def matte(source):
    img = Image.open(source).convert('RGB')
    pixels = np.asarray(img, dtype=np.float64)
    paper = paper_estimate(img) * 0.975  # the dilation overshoots the true paper level a little
    darkness = np.clip((paper - pixels) / np.maximum(paper, 1), 0, 1).max(axis=-1)
    alpha = smoothstep(0.07, 0.42, darkness)
    foreground = np.clip((pixels - (1 - alpha[..., None]) * paper) / np.maximum(alpha, 1e-3)[..., None], 0, 255)
    return foreground, alpha


def to_dark_theme(foreground):
    """Gold stays; the near-grey pencil ink turns light so it reads on a dark page."""
    high, low = foreground.max(axis=-1), foreground.min(axis=-1)
    saturation = (high - low) / np.maximum(high, 1)
    ink = (1 - smoothstep(0.28, 0.5, saturation))[..., None]
    return foreground * (1 - ink) + np.array(INK_ON_DARK) * ink


def to_image(foreground, alpha):
    return Image.fromarray(np.dstack([foreground, alpha * 255]).astype(np.uint8), 'RGBA')


def filled_lines(alpha, axis, threshold=0.3, min_pixels=4):
    """Rows (axis=1) or columns (axis=0) that really hold drawing, not a stray speck of paper noise."""
    return (alpha > threshold).sum(axis=axis) >= min_pixels


def content_box(alpha):
    rows = np.where(filled_lines(alpha, axis=1))[0]
    cols = np.where(filled_lines(alpha, axis=0))[0]
    return cols[0], rows[0], cols[-1] + 1, rows[-1] + 1


def symbol_bottom(alpha, min_gap=18):
    """First row after the symbol where the empty band above the name starts."""
    filled = filled_lines(alpha, axis=1)
    run = 0
    for row in range(int(np.argmax(filled)), len(filled)):
        run = 0 if filled[row] else run + 1
        if run >= min_gap:
            return row - run + 1
    return len(filled)


def crop(image, box, margin):
    left, top, right, bottom = box
    pad = int(margin * max(right - left, bottom - top))
    return image.crop((max(left - pad, 0), max(top - pad, 0), min(right + pad, image.width), min(bottom + pad, image.height)))


def save_webp(image, name, width):
    image = image.resize((width, round(image.height * width / image.width)), Image.LANCZOS)
    image.save(OUT / name, 'WEBP', quality=82, method=6)


def square_icon(mark, size):
    """The symbol centred on the cream background, for the favicon and the touch icon."""
    canvas = Image.new('RGBA', (size, size), CREAM + (255,))
    inner = int(size * 0.84)
    scaled = mark.resize((inner, round(mark.height * inner / mark.width)), Image.LANCZOS)
    canvas.alpha_composite(scaled, ((size - scaled.width) // 2, (size - scaled.height) // 2))
    return canvas.convert('RGB')


def main():
    foreground, alpha = matte(SOURCE)
    light, dark = to_image(foreground, alpha), to_image(to_dark_theme(foreground), alpha)

    lockup_box = content_box(alpha)
    mark_box = (lockup_box[0], lockup_box[1], lockup_box[2], symbol_bottom(alpha))
    for suffix, image in (('', light), ('-dark', dark)):
        save_webp(crop(image, lockup_box, 0.03), f'tickbron-logo{suffix}.webp', LOCKUP_WIDTH)
        save_webp(crop(image, mark_box, 0.03), f'tickbron-mark{suffix}.webp', MARK_WIDTH)

    mark = crop(light, mark_box, 0.03)
    square_icon(mark, 180).save(OUT / 'apple-touch-icon.png')
    square_icon(mark, 32).save(OUT / 'favicon-32.png')
    square_icon(mark, 48).save(OUT / 'favicon.ico', sizes=[(16, 16), (32, 32), (48, 48)])
    print('lockup box', [int(v) for v in lockup_box], 'symbol box', [int(v) for v in mark_box])


if __name__ == '__main__':
    main()
