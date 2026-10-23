# Plan: design refresh, round 1 (2026-10-23)

Owner request: improve the look of the whole project (also the admin panel), take ideas from other sites, add some 3D that costs little.

## Ideas taken from research
- Hotel sites 2026 ([mediaboom](https://mediaboom.com/news/hotel-website-design-trends/), [hooray](https://lab.hooray.agency/12-must-follow-hotel-website-design-trends-in-2026/)): one clear booking path above the fold, mobile first, real photos, decorative shapes that lead the eye to the call to action.
- Admin dashboards ([AdminLTE guide](https://adminlte.io/?p=6708), [setproduct](https://setproduct.com/blog/dashboard-ui-design)): fixed left menu, lean navigation, content gets the space, do not wrap every number in its own bordered card.
- 3D ([learnwithhasan](https://learnwithhasan.com/js-libraries/css-3d-transforms/), [three.js forum](https://discourse.threejs.org/t/will-native-three-js-geometry-perform-better-thant-css3dobject/31102)): CSS 3D transforms are enough for tilt cards and a layered hero and need no library; three.js only for a real 3D scene, and it would add weight to an image-heavy site. Decision: CSS only.
The brand palette (gold, cream, ink) is the client's and stays.

## Done in round 1 (`frontend/src/styles/refresh.css`, loaded last, tokens only)
- Admin and owner panels: side menu on desktop (>= 1100 px), one scrolling row on phones (was 12 full-width rows), smaller page title.
- Search form: the Search button takes the free grid slot (results page form is about 100 px shorter); on phones paired fields sit side by side (the home form fits one screen).
- Home hero: lattice pattern and three gold arches at different depths that turn with the mouse (`HeroScene`, `useTilt`); hidden below 1100 px.
- Property cards tilt towards the mouse and zoom the photo on hover; destination cards lift. Only with a real mouse and without reduced motion.
- No new dependency (JS +2 kB).

## Not done yet (next rounds, owner decides what first)
- Property detail page (gallery, sticky booking card), search results filters, booking page.
- Admin lists and detail screens inside the panel (tables, cards with gold outline), owner panel inner screens.
- Dark theme check of the new parts by eye; empty/failed photo placeholders (a gradient with the logo instead of a broken image icon).

## Round 4 (2026-10-23): owner panel, rooms and room photos
- (styles in `frontend/src/styles/panels.css`) The room list, the room form and the hotel details/tags of the owner dashboard had no styles; now styled (cards with a photo area, form in sections, 2 columns that become 1 on phones).
- New: room photos (see HANDOFF.md).
- Statistics screens (same file `panels.css`): long amounts wrap inside their card without splitting digits, sections keep their distance, chart bars carry short labels ("$54.2M", full amount in the title; `formatMoneyCompact`), the tallest bar's label is no longer cut, cards are 2 by 2 on phones, and the small Status tables fit a phone (they shared the 800 px minimum width of the customers table).
- Button audit: see HANDOFF.md.

## Round 2 (2026-10-23, same file `refresh.css`)
- Admin screens: shorter page header (badge on the same line), smaller view titles, the "Total users: N" bands are small pills, tighter table cells.
- Statistics chart: a month with one data point is a bar of at most 96 px (it was a full-width wall).
- Property page: smaller gaps between sections, the type/guests/bedrooms/bathrooms row is 2 x 2 on phones (was 4 rows), sections have less padding on phones.
- Empty photos (hotel card, gallery, destination card) show a soft panel with the lattice instead of a flat beige box.
- Checked by screenshots at 1440 and 390 px in the light and the dark theme (property page, admin users, customers, statistics).
- Still open: the customers table has 12 columns and scrolls sideways inside its card on 1440 px (Status and actions are at the far right); booking page and owner inner screens not reviewed by eye.
