import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

const css = readFileSync(resolve(__dirname, 'index.css'), 'utf-8')
const rule = (selector: string) => css.match(new RegExp(`\n${selector.replace(/[.[\]()]/g, '\\$&')} \\{([^}]*)\\}`))?.[1] ?? ''

describe('long unbroken values stay inside the screen', () => {
  it('lets the hotel page columns shrink below their content, so a calendar cannot widen a phone page', () => {
    const columns = [...css.matchAll(/\.property-detail-content \{[^}]*?grid-template-columns: ([^;]+);/g)].map(match => match[1])

    expect(columns.length).toBeGreaterThan(0)
    for (const value of columns) expect(value, value).toMatch(/minmax\(0, 1fr\)/)
    expect(rule('.property-detail-main')).toContain('min-width: 0')
  })

  it('lets the seven calendar columns shrink, so a price inside a day cannot widen a phone page', () => {
    expect(rule('.availability-calendar-weekdays')).toContain('repeat(7, minmax(0, 1fr))')
    expect(rule('.availability-calendar-days')).toContain('repeat(7, minmax(0, 1fr))')
  })

  it('does not force the calendar days to be square on a phone, where they are taller than the column is wide', () => {
    const phoneRule = [...css.matchAll(/\.availability-calendar-day \{([^}]*)\}/g)].map(match => match[1]).find(body => body.includes('min-height: 50px'))

    expect(phoneRule).toContain('aspect-ratio: auto')
  })

  it('lets the booking detail columns shrink, so a long reference or e-mail cannot widen the support page', () => {
    const columns = [...css.matchAll(/\.booking-details-grid \{[^}]*?grid-template-columns: ([^;]+);/g)].map(match => match[1])

    expect(columns.length).toBeGreaterThan(0)
    for (const value of columns) expect(value, value).toContain('minmax(0, 1fr)')
  })
})
