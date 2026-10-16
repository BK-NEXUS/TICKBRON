# Logo: clean vector alternative (not used by the app)

A redraw of the TICKBRON logo as clean SVG (three towers with a side face, two palms, the name and
tagline as outlines of Cinzel, SIL Open Font License, see `fonts/`). Made on 2026-10-16 as an
alternative to the pencil-drawing look. The owner found it too plain, so the app keeps the client's
drawing (`frontend/public/brand/*.webp`, made by `frontend/tools/make_logo.py`).

To try it: copy the SVG files to `frontend/public/brand/`, point `LOGO_FILES` in
`frontend/src/components/BrandLogo.tsx` to them, and update `frontend/src/brandAssets.test.ts`.
`make_logo_svg.py` writes into `frontend/public/brand/` when run from `frontend/` (needs `fonttools`,
and the `fonts/` folder next to it); `render_icons.mjs` builds the favicon files from `favicon.svg`.
