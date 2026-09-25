# Frontend: client logo and brand colors (2026-09-25, Kolya's agent)

Commit: `kolya - frontend: apply client logo and brand colors`. Styling and logo placement only; no layout or logic changes.

## Palette (`frontend/src/styles/index.css` `:root`)

Measured from the client logo: gold bright `#DCB969`, gold base `#BC9C59`, ink `#3E382D`, cream `#F2EDE7`.
Legacy token names from design checkpoint D1 are kept, so components did not change.

| Token | Value | Role |
|---|---|---|
| `--color-gold-bright` / `--color-primary` | `#DCB969` | Primary button fill (always with ink text) |
| `--color-primary-hover` | `#C9AD6E` | Primary button hover fill |
| `--color-gold` | `#BC9C59` | Decorative only (tints, focus rings) |
| `--color-gold-dark` / `--color-pomegranate` | `#715A2C` | Text-safe gold: links, accents, selected states (white text on it) |
| `--color-primary-dark` | `#5A4722` | Link hover text |
| `--color-ink` / `--color-deep-ink` / `--color-text-primary` | `#3E382D` | Text |
| `--color-registan-teal` / `--color-secondary` | `#4F4637` | Secondary fills (pagination, toggles, hero gradient) |
| `--color-secondary-dark` | `#2B261E` | Secondary hover |
| `--color-cream` / `--color-chalk-stone` / `--color-background-alt` | `#F2EDE7` | Header, footer, auth page, alt sections |
| `--color-cloud-white` / `--color-background` | `#FFFFFF` | Cards, page body |
| `--color-text-secondary` | `#655D4F` | |
| `--color-text-tertiary` | `#726858` | |
| `--color-hairline` / `--color-border` | `#E2D8C8` | |
| `--color-alert-red` / `--color-error` | `#B02626` | Error (kept separate from brand) |
| `--color-sprout-green` / `--color-success` | `#386D4D` | Success (kept separate from brand) |
| `--color-saffron` / `--color-warning` | `#7D5518` | Warning / pending |

## Contrast (WCAG 2.1, AA needs 4.5:1 for normal text)

| Text | Background | Ratio |
|---|---|---|
| Ink `#3E382D` | white / cream | 11.61 / 9.98 |
| Ink | gold-bright `#DCB969` (primary button) | 6.19 |
| Ink | `#C9AD6E` (primary button hover) | 5.36 |
| Gold-dark `#715A2C` (links, accents) | white / cream / 10% gold tint | 6.56 / 5.64 / 6.03 |
| Primary-dark `#5A4722` (link hover) | cream | 7.65 |
| White | gold-dark `#715A2C` (selected tabs, badges, avatars) | 6.56 |
| White | secondary `#4F4637` | 9.28 |
| Secondary text `#655D4F` | white / cream | 6.50 / 5.58 |
| Tertiary text `#726858` | white / cream | 5.47 / 4.70 |
| Error `#B02626` | white / cream / 10% error tint | 6.66 / 5.73 / 5.64 |
| White | error `#B02626` | 6.66 |
| Success `#386D4D` | white / 10% success tint | 6.06 / 5.26 |
| White | success `#386D4D` | 6.06 |
| Warning `#7D5518` / white on it | white | 6.59 |
| Not used: white on gold-bright | | 1.88 (fails) |
| Not used: gold-base text on cream | | 2.24 (fails) |

All 94 text/background pairs declared in the same CSS rule were checked by script; every one is at least 4.5:1.
Also fixed on the way (pre-existing failures): WhatsApp/Telegram contact buttons (`#075E54`, `#0068A5`), test-mode banner text, disabled pagination text.

## Logo

- One reference: `BRAND_LOGO_SRC` in `frontend/src/components/BrandLogo.tsx` (`/brand/tickbron-logo.jpg`). Replace that file, or change the constant, to swap in a transparent/SVG/horizontal version.
- Placements, all on a cream background so the JPG's paper edges do not show: header (44px, next to the "TICKBRON" heading), footer (112px), login and register pages (168px, centered above the form card).
- Temporary favicon: `public/brand/favicon.ico`, `favicon-32.png`, `apple-touch-icon.png`, cropped from the three-building mark.

## Needed from the client

- A simplified vector icon for the favicon (the sketch detail is lost at 16-32px).
- A transparent PNG or SVG logo (the current JPG only works on cream).
- A horizontal logo for the header.
- A web-optimized size: the current JPG is 1254x1254, 325 KB, loaded even for the 44px header logo.
