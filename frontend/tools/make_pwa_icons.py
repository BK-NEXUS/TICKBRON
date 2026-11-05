"""Builds the app icons the web app manifest points to (public/brand/icon-*.png) from the client logo.

Run from frontend/ with any Python that has Pillow:  python tools/make_pwa_icons.py
"""
from pathlib import Path

from PIL import Image

BRAND = Path(__file__).resolve().parent.parent / "public" / "brand"
CREAM = (242, 237, 231, 255)  # --color-cream, the same colour as the theme and background in manifest.webmanifest


def icon(mark: Image.Image, size: int, mark_share: float) -> Image.Image:
    width = round(size * mark_share)
    scaled = mark.resize((width, round(mark.height * width / mark.width)), Image.LANCZOS)
    canvas = Image.new("RGBA", (size, size), CREAM)
    canvas.alpha_composite(scaled, ((size - scaled.width) // 2, (size - scaled.height) // 2))
    return canvas.convert("RGB")


def main() -> None:
    mark = Image.open(BRAND / "tickbron-mark.webp").convert("RGBA")
    icon(mark, 192, 0.74).save(BRAND / "icon-192.png", optimize=True)
    icon(mark, 512, 0.74).save(BRAND / "icon-512.png", optimize=True)
    # Maskable: the phone may cut away the outer 20%, so the mark stays well inside the middle
    icon(mark, 512, 0.56).save(BRAND / "icon-maskable-512.png", optimize=True)


if __name__ == "__main__":
    main()
