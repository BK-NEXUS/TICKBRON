import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

const read = (file: string) => readFileSync(resolve(__dirname, file), 'utf-8')
const refresh = read('refresh.css')

describe('design refresh styles', () => {
  it('is loaded after the surfaces', () => {
    const main = read('../main.tsx')
    expect(main.indexOf("'./styles/refresh.css'")).toBeGreaterThan(main.indexOf("'./styles/surfaces.css'"))
  })

  it('uses tokens only, no raw hex colours', () => {
    expect(refresh.replace(/rgba\([^)]*\)/g, '')).not.toMatch(/#[0-9a-fA-F]{3,8}\b/)
  })

  it('shows the panel menu as a side column on desktop and one scrolling row on phones', () => {
    expect(refresh).toMatch(/@media \(min-width: 1100px\) \{\s*\.dashboard-layout \{[^}]*grid-template-columns: 232px minmax\(0, 1fr\)/)
    expect(refresh).toMatch(/@media \(max-width: 1099px\) {[\s\S]*?flex-direction: row;[\s\S]*?flex-wrap: nowrap;[\s\S]*?overflow-x: auto/)
  })

  it('moves every transform effect behind the reduced-motion and real-pointer queries', () => {
    const outside = refresh.replace(/@media \(prefers-reduced-motion: no-preference\) \{[\s\S]*?\n\}\n/g, '')
      .replace(/@media \(hover: hover\)[^{]*\{[\s\S]*?\n\}\n/g, '')
    expect(outside).not.toMatch(/:hover[^{]*\{[^}]*transform/)
    expect(outside).not.toMatch(/transition:/)
  })

  it('keeps the hero scene off phones', () => {
    expect(refresh).toMatch(/\.hero-scene \{\s*display: none/)
    expect(refresh).toMatch(/@media \(min-width: 1100px\) \{\s*\.hero-scene \{\s*display: block/)
  })
})

describe('design refresh round 2', () => {
  it('shows a one-point statistics chart as a bar of limited width', () => {
    expect(refresh).toMatch(/\.bar-chart-item \{\s*max-width: 96px/)
  })

  it('turns the count bars into pills and stacks the property meta two by two on phones', () => {
    expect(refresh).toMatch(/\.users-count,\s*\.customers-count \{[^}]*border-radius: var\(--radius-pill\)/)
    expect(refresh).toMatch(/@media \(max-width: 767px\) \{\s*\.property-detail-header-meta \{\s*display: grid;\s*grid-template-columns: repeat\(2/)
  })

  it('gives empty photo placeholders the lattice', () => {
    expect(refresh).toMatch(/\.property-card-image-placeholder,[\s\S]*?repeating-linear-gradient\(45deg/)
  })
})

describe('design refresh round 3 (map)', () => {
  it('draws the price pin with a tail and the cluster in three sizes', () => {
    expect(refresh).toMatch(/\.map-pin::after \{[^}]*rotate\(45deg\)/)
    expect(refresh).toMatch(/\.map-cluster--md \{/)
    expect(refresh).toMatch(/\.map-cluster--lg \{/)
  })

  it('darkens the tiles in the dark theme, by the system setting and by the chosen theme', () => {
    expect(refresh).toMatch(/prefers-color-scheme: dark\) \{\s*:root:not\(\[data-theme="light"\]\) \.leaflet-container:not\(\.map--satellite\) \.leaflet-tile-pane \{\s*filter: invert\(1\)/)
    expect(refresh).toMatch(/:root\[data-theme="dark"\] \.leaflet-container:not\(\.map--satellite\) \.leaflet-tile-pane \{\s*filter: invert\(1\)/)
  })

  it('styles the street map / satellite switch as one pill with the chosen button filled', () => {
    expect(refresh).toMatch(/\.map-layer-switch__button\[aria-pressed="true"\] \{[^}]*background: var\(--color-primary\)/)
    expect(refresh).toMatch(/\.map-layer-switch__button:focus-visible \{/)
  })

  it('keeps the pin scale effect to a real mouse and allowed motion', () => {
    expect(refresh).toMatch(/@media \(hover: hover\) and \(pointer: fine\) and \(prefers-reduced-motion: no-preference\) \{\s*\.map-pin:hover/)
  })
})

describe('design refresh round 3 (hotel card)', () => {
  it('keeps the public hotel card flush and its price row on one line, apart from the owner card', () => {
    expect(refresh).toMatch(/\.property-card\.tilt-card \{\s*padding: 0;\s*gap: 0;/)
    expect(refresh).toMatch(/\.property-card\.tilt-card \.property-card-footer \{\s*justify-content: space-between/)
  })

  it('shows compact rows next to the map without the details and the button', () => {
    expect(refresh).toMatch(/\.properties-map-list \.property-card \{\s*display: grid;\s*grid-template-columns: 112px/)
    expect(refresh).toMatch(/\.properties-map-list \.property-card-cta \{\s*display: none/)
  })
})

describe('design refresh round 3 (phones)', () => {
  it('lists one hotel per row on phones', () => {
    expect(refresh).toMatch(/@media \(max-width: 599px\) \{\s*\.search-results-grid \{\s*grid-template-columns: minmax\(0, 1fr\)/)
  })
})

describe('design refresh: phone spacing', () => {
  const tokens = read('tokens.css')
  const chat = read('chat.css')

  it('keeps the room the floating bottom navigation needs in one token that counts the safe area', () => {
    expect(tokens).toMatch(/--mobile-nav-clearance:\s*calc\(\d+px \+ env\(safe-area-inset-bottom\)\)/)
  })

  it('leaves that room under the footer, so the last line is never behind the navigation', () => {
    expect(refresh).toMatch(/@media \(max-width: 767px\) \{[\s\S]*?\.footer \{\s*margin-bottom: 0;\s*padding-bottom: var\(--mobile-nav-clearance\)/)
  })

  it('puts air between the sections and between the two buttons of an information page', () => {
    expect(refresh).toMatch(/\.info-page-section \{\s*margin-top: var\(--spacing-lg\)/)
    expect(refresh).toMatch(/\.info-page-footer \{\s*margin: var\(--spacing-md\) 0 0/)
  })

  it('gives "Forgot password?" a full-size tap target with a gap above it', () => {
    expect(refresh).toMatch(/\.auth-forgot-link \{[^}]*min-height: 44px[^}]*margin-top: var\(--spacing-xs\)/)
  })

  it('keeps the chat message box clear of the navigation with a gap', () => {
    expect(chat).toMatch(/\.chat-thread__list \{\s*height: clamp\(240px, calc\(100dvh - 490px\), 420px\)/)
  })

  it('shows the three numbers of an ad (views, clicks, click rate) side by side, also on a phone', () => {
    expect(refresh).toMatch(/\.renewal-facts--stats \{\s*grid-template-columns: repeat\(3, minmax\(0, 1fr\)\)/)
  })

  it('keeps the export buttons of the owner bookings clear of the text above and the filters below', () => {
    expect(refresh).toMatch(/\.bookings-view-header \.status-csv \{\s*margin: var\(--spacing-sm\) 0 var\(--spacing-md\)/)
  })

  it('keeps the two-step setup readable on a phone: a QR code no wider than the card, two columns of backup codes, 44 px link buttons', () => {
    expect(refresh).toMatch(/\.qr-code \{[^}]*width: min\(100%, 240px\)/)
    expect(refresh).toMatch(/\.two-factor-codes \{[^}]*grid-template-columns: repeat\(2, minmax\(0, 1fr\)\)/)
    expect(refresh).toMatch(/\.auth-link-button \{[^}]*min-height: 44px/)
  })

  it('stacks the two-step reset question of the admin user list and keeps its buttons apart', () => {
    expect(refresh).toMatch(/\.user-card \.user-card-footer \{\s*flex-wrap: wrap/)
    expect(refresh).toMatch(/\.user-two-factor-block \{\s*flex: 1 1 100%/)
    expect(refresh).toMatch(/\.user-two-factor-reset \{[^}]*flex-direction: column[^}]*max-width: 28rem/)
    expect(refresh).toMatch(/\.user-two-factor-actions \{[^}]*flex-wrap: wrap[^}]*gap: var\(--spacing-sm\)/)
  })

  it('lays out the star split of an owner hotel as label, bar and count', () => {
    expect(refresh).toMatch(/\.owner-rating-split-row \{\s*display: grid;\s*grid-template-columns: 3rem minmax\(0, 1fr\) 2\.5rem/)
  })
})
