import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

const read = (file: string) => readFileSync(resolve(__dirname, file), 'utf-8')
const surfaces = read('surfaces.css')

describe('shared surfaces', () => {
  it('is loaded after the component styles', () => {
    const main = read('../main.tsx')
    expect(main.indexOf("'./styles/surfaces.css'")).toBeGreaterThan(main.indexOf("'./styles/index.css'"))
  })

  it('uses tokens only, no raw colours except the translucent ink backdrop and alert tints', () => {
    const withoutBackdrops = surfaces.replace(/rgba\([^)]*\)/g, '')
    expect(withoutBackdrops).not.toMatch(/#[0-9a-fA-F]{3,8}\b/)
  })

  it('gives cards a large radius and the selected card a coloured border', () => {
    expect(surfaces).toMatch(/\.property-card,[\s\S]*?\{\s*border-radius: var\(--radius-xl\)/)
    expect(surfaces).toMatch(/\.room-card--selected,\s*\.rate-plan-card--selected \{\s*border: 2px solid var\(--color-gold\)/)
  })

  it('blurs the modal backdrop', () => {
    expect(surfaces).toMatch(/\.modal-overlay,[\s\S]*?backdrop-filter: blur\(6px\)/)
  })

  it('makes the header and the bottom navigation floating pills', () => {
    expect(surfaces).toMatch(/\.header-container \{[^}]*border-radius: var\(--radius-pill\)/)
    expect(surfaces).toMatch(/\.mobile-bottom-navigation \{[^}]*border-radius: var\(--radius-pill\)/)
    expect(surfaces).toMatch(/\.mobile-bottom-navigation \{[^}]*env\(safe-area-inset-bottom\)/)
  })

  it('keeps control borders at the accessible token and focus visible', () => {
    expect(surfaces).toContain('border: 1px solid var(--color-border-control)')
    expect(surfaces).toContain('outline: 2px solid var(--color-focus)')
  })

  it('defines the alert variants that the app already uses', () => {
    for (const name of ['.alert', '.alert-error', '.alert-success']) expect(surfaces).toContain(`${name} {`)
  })
})
