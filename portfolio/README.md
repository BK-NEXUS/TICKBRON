# Portfolio

Static 3D portfolio site (Vite, React, TypeScript, Three.js). No backend.
Black, white and blue design with a day/night switch (the choice is remembered; the system preference is the default).

## Run

```bash
npm install
npm run dev        # development
npm test           # unit and component tests
npm run build      # static output in dist/
```

## Replace the sample details

All personal content is in `src/data/profile.ts` (name, certificates, website, social links, statistics).
The sample data there is a placeholder; links point to `example.com`.
Text translations (UZ/EN/RU) are in `src/i18n/dictionaries.ts`.

## Screenshots at 390px and 1440px

```bash
npm run build && npx vite preview --port 4173 &
node scripts/screenshots.mjs   # fails if the page scrolls horizontally at 390px
```

## Deploy

Upload `dist/` to Vercel, Netlify or Cloudflare Pages (build command `npm run build`, output `dist`).

## Accessibility and motion

`prefers-reduced-motion` turns off the 3D scene and animations (static gradient stays).
On screens under 768px the scene uses fewer shapes and a lower pixel ratio.
If WebGL is unavailable, the gradient backdrop and all content still show.
