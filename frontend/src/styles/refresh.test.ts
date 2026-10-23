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
