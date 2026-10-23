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
