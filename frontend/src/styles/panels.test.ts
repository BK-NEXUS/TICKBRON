import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

const read = (file: string) => readFileSync(resolve(__dirname, file), 'utf-8')
const refresh = read('panels.css')

describe('panel styles', () => {
  it('are loaded after the design refresh styles', () => {
    const main = read('../main.tsx')
    expect(main.indexOf("'./styles/panels.css'")).toBeGreaterThan(main.indexOf("'./styles/refresh.css'"))
  })

  it('use tokens only, no raw hex colours', () => {
    expect(refresh.replace(/rgba\([^)]*\)/g, '')).not.toMatch(/#[0-9a-fA-F]{3,8}\b/)
  })
})

describe('owner panel', () => {
  it('styles the room list as a grid of cards with a photo area and a flag for rooms without photos', () => {
    expect(refresh).toMatch(/\.room-types-grid \{\s*display: grid/)
    expect(refresh).toMatch(/\.room-type-card-media \{[^}]*aspect-ratio: 16 \/ 9/)
    expect(refresh).toMatch(/\.room-type-no-photos \{[^}]*border: 1px dashed var\(--color-warning\)/)
  })

  it('styles the room form as sections, two columns that become one on phones', () => {
    expect(refresh).toMatch(/\.rooms-form-section \{[^}]*border-radius: var\(--radius-xl\)/)
    expect(refresh).toMatch(/\.rooms-form \.form-row \{\s*display: grid;\s*grid-template-columns: repeat\(2/)
    expect(refresh).toMatch(/@media \(max-width: 599px\) \{\s*\.rooms-form \.form-row \{\s*grid-template-columns: minmax\(0, 1fr\)/)
  })

  it('lays out the owner hotel cards with a details grid and inline amenity tags', () => {
    expect(refresh).toMatch(/\.partner-dashboard-page \.property-details \{\s*display: grid/)
    expect(refresh).toMatch(/\.partner-dashboard-page \.property-amenities \{\s*display: flex;\s*flex-direction: row;\s*flex-wrap: wrap/)
  })
})

describe('flex direction', () => {
  it('sets row direction where wrapping is meant, because the generic form group is a column', () => {
    expect(refresh).toMatch(/\.rooms-form \.checkbox-group \{\s*flex-direction: row;\s*flex-wrap: wrap/)
    expect(refresh).toMatch(/\.partner-dashboard-page \.property-amenities \{\s*display: flex;\s*flex-direction: row;\s*flex-wrap: wrap/)
  })
})

describe('statistics', () => {
  it('lets long amounts wrap inside their card and spaces the sections apart', () => {
    expect(refresh).toMatch(/\.status-card-value \{\s*overflow-wrap: break-word/)
    expect(refresh).toMatch(/\.admin-status-overview section \+ section \{\s*margin-top: var\(--spacing-xl\)/)
  })

  it('shows the statistics cards two by two on phones and keeps the twelve bars readable', () => {
    expect(refresh).toMatch(/@media \(max-width: 599px\) \{\s*\/\*[^*]*\*\/\s*\.status-cards \{\s*grid-template-columns: repeat\(2, minmax\(0, 1fr\)\)/)
    expect(refresh).toMatch(/\.status-chart \.bar-chart \{\s*min-width: 480px/)
  })
})

describe('small tables', () => {
  it('lets the small Status tables fit a phone although the customers table keeps its width', () => {
    expect(refresh).toMatch(/@media \(max-width: 767px\) \{\s*\.customers-table\.status-table \{\s*min-width: 0/)
  })
})

