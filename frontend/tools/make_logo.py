"""
Builds the logo files in public/brand/ from the gold logo sheet (tools/tickbron-logo-sheet.jpg).

The sheet shows the logo on a cream paper background and on a dark textured background. Each
background is removed here, so the logo sits on any page color; the soft shadow under the light
version is kept.

  tickbron-logo.webp / tickbron-logo-dark.webp   full lockup (symbol, name, rule, tagline)
  tickbron-mark.webp / tickbron-mark-dark.webp   the symbol only, for small sizes
  favicon-32.png, apple-touch-icon.png, favicon.ico   the symbol on the cream background

How a background is removed: the background color under the logo is estimated (a heavy blur of
the pixels that are not gold), and every pixel's opacity is how far its color is from that
background. Edge pixels take the color of the gold next to them, so no cream or dark fringe stays.

Run from frontend/:  python3 tools/make_logo.py   (needs Pillow and numpy)
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

HERE = Path(__file__).resolve().parent
SHEET = HERE / 'tickbron-logo-sheet.jpg'
OUT = HERE.parent / 'public' / 'brand'

# Panels of the sheet (left, top, right, bottom), inside the grey gutters
LIGHT_LOCKUP = (2, 2, 510, 436)
DARK_LOCKUP = (522, 2, 1022, 436)

CREAM = (243, 237, 229)  # --color-background-alt, behind the favicon symbol
SHADOW = (58, 40, 12)
UPSCALE = 2
LOCKUP_WIDTH = 760
MARK_WIDTH = 560


def smoothstep(edge0, edge1, x):
    t = np.clip((x - edge0) / (edge1 - edge0), 0, 1)
    return t * t * (3 - 2 * t)


def blur(arr, sigma):
    """Gaussian blur of a float array (one or more channels), done in the frequency domain."""
    if arr.ndim == 3:
        return np.stack([blur(arr[..., c], sigma) for c in range(arr.shape[-1])], axis=-1)
    pad = int(3 * sigma)
    padded = np.pad(arr, pad, mode='reflect')
    fy = np.fft.fftfreq(padded.shape[0])[:, None]
    fx = np.fft.rfftfreq(padded.shape[1])[None, :]
    transfer = np.exp(-2 * (np.pi * sigma) ** 2 * (fx ** 2 + fy ** 2))
    blurred = np.fft.irfft2(np.fft.rfft2(padded) * transfer, s=padded.shape)
    return blurred[pad:-pad, pad:-pad]


def dilate(mask, size):
    img = Image.fromarray((mask * 255).astype(np.uint8), 'L').filter(ImageFilter.MaxFilter(size))
    return np.asarray(img, dtype=np.float64) / 255


def remove_background(panel, dark, keep_shadow):
    """RGBA picture of the logo in `panel`: transparent where the background was."""
    img = panel.resize((panel.width * UPSCALE, panel.height * UPSCALE), Image.LANCZOS)
    pixels = np.asarray(img, dtype=np.float64)
    chroma = pixels.max(axis=-1) - pixels.min(axis=-1)
    art = dilate((chroma > (40 if dark else 78)).astype(np.float64), 25)
    free = 1 - art
    # the background under the logo: blur the free pixels only (normalized convolution)
    background = blur(pixels * free[..., None], 28) / np.maximum(blur(free, 28), 1e-3)[..., None]
    distance = np.linalg.norm(pixels - background, axis=-1)
    alpha = smoothstep(26, 62, distance) if dark else smoothstep(22, 52, distance)
    # faint leftovers (the glow around the sparkles, paper texture) become fully transparent
    alpha = smoothstep(0.35, 0.85, alpha) if dark else smoothstep(0.15, 0.80, alpha)
    # only the area close to real gold stays: smudges of glow farther away than a few pixels go
    lum = pixels @ np.array([0.299, 0.587, 0.114])
    gold = (((lum > 130) | (chroma > 85)) if dark else (distance > 46)).astype(np.float64)
    # a sparkle can leave a patch of odd color inside the gold: close such holes before using the mask
    gold_filled = np.asarray(Image.fromarray((gold * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(31)).filter(ImageFilter.MinFilter(31)), dtype=np.float64) / 255
    alpha = alpha * dilate(np.maximum(gold, gold_filled), 9)
    # drop specks: shrink then grow the opaque part by one pixel
    opened = np.asarray(Image.fromarray((alpha * 255).astype(np.uint8)).filter(ImageFilter.MinFilter(3)).filter(ImageFilter.MaxFilter(3)), dtype=np.float64) / 255
    alpha = np.minimum(alpha, dilate(opened > 0.5, 3))
    # fill the small holes that bright glints leave inside the gold (closing: grow, then shrink)
    grown = Image.fromarray((alpha * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(7)).filter(ImageFilter.MinFilter(7))
    closed = np.asarray(grown, dtype=np.float64) / 255
    alpha = np.maximum(alpha, closed)
    # smooth the stair-steps left on the edges by the steps above
    alpha = smoothstep(0.25, 0.75, blur(alpha, 1.1))
    # color: keep the picture inside, and give edge and filled pixels the color of the gold next to them
    core = (alpha > 0.95).astype(np.float64)
    inner = blur(pixels * core[..., None], 2.0) / np.maximum(blur(core, 2.0), 1e-3)[..., None]
    is_gold = smoothstep(0.5, 0.9, blur(gold, 1.0))
    keep = (smoothstep(0.90, 0.99, alpha) * is_gold)[..., None]
    color = pixels * keep + inner * (1 - keep)
    out_alpha = alpha
    out_color = color
    if keep_shadow:
        bg_lum = background @ np.array([0.299, 0.587, 0.114])
        darker = np.clip((bg_lum - lum) / np.maximum(bg_lum, 1), 0, 1)
        shadow = smoothstep(0.05, 0.22, darker) * (1 - alpha) * (1 - art * 0) * 0.55
        total = alpha + shadow * (1 - alpha)
        out_color = (color * alpha[..., None] + np.array(SHADOW) * (shadow * (1 - alpha))[..., None]) / np.maximum(total, 1e-3)[..., None]
        out_alpha = total
    return Image.fromarray(np.dstack([np.clip(out_color, 0, 255), out_alpha * 255]).astype(np.uint8), 'RGBA')


def filled_lines(alpha, axis, threshold=0.45, min_pixels=6):
    return (alpha > threshold).sum(axis=axis) >= min_pixels


def content_box(alpha):
    rows = np.where(filled_lines(alpha, 1))[0]
    cols = np.where(filled_lines(alpha, 0))[0]
    return cols[0], rows[0], cols[-1] + 1, rows[-1] + 1


def symbol_bottom(alpha, min_gap=14):
    """First row after the symbol where the empty band above the name starts."""
    filled = filled_lines(alpha, 1)
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
    image.save(OUT / name, 'WEBP', quality=88, alpha_quality=100, method=6)


def square_icon(mark, size):
    """The symbol centred on the cream background, for the favicon and the touch icon."""
    canvas = Image.new('RGBA', (size, size), CREAM + (255,))
    inner = int(size * 0.86)
    scaled = mark.resize((inner, round(mark.height * inner / mark.width)), Image.LANCZOS)
    canvas.alpha_composite(scaled, ((size - scaled.width) // 2, (size - scaled.height) // 2))
    return canvas.convert('RGB')


def main():
    sheet = Image.open(SHEET).convert('RGB')
    variants = {
        '': remove_background(sheet.crop(LIGHT_LOCKUP), dark=False, keep_shadow=True),
        '-dark': remove_background(sheet.crop(DARK_LOCKUP), dark=True, keep_shadow=False),
    }
    light_mark = None
    for suffix, image in variants.items():
        alpha = np.asarray(image)[..., 3] / 255
        box = content_box(alpha)
        mark_box = (box[0], box[1], box[2], symbol_bottom(alpha))
        save_webp(crop(image, box, 0.03), f'tickbron-logo{suffix}.webp', LOCKUP_WIDTH)
        mark = crop(image, mark_box, 0.03)
        save_webp(mark, f'tickbron-mark{suffix}.webp', MARK_WIDTH)
        if suffix == '':
            light_mark = mark
    square_icon(light_mark, 180).save(OUT / 'apple-touch-icon.png')
    square_icon(light_mark, 32).save(OUT / 'favicon-32.png')
    square_icon(light_mark, 48).save(OUT / 'favicon.ico', sizes=[(16, 16), (32, 32), (48, 48)])


if __name__ == '__main__':
    main()
