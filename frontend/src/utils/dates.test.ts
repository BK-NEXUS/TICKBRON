import { describe, it, expect } from 'vitest'
import { addDays, businessToday, toLocalDate } from './dates'

describe('businessToday', () => {
  it('is the date in Tashkent, which is five hours ahead of UTC', () => {
    expect(businessToday(new Date('2026-10-10T18:59:59Z'))).toBe('2026-10-10')
    expect(businessToday(new Date('2026-10-10T19:00:00Z'))).toBe('2026-10-11')
    expect(businessToday(new Date('2026-10-10T23:30:00Z'))).toBe('2026-10-11')
  })

  it('does not depend on the browser time zone', () => {
    // The same instant is 10 Oct in Los Angeles and 11 Oct in Tashkent; the backend uses Tashkent
    const instant = new Date('2026-10-11T03:00:00Z')
    expect(businessToday(instant)).toBe('2026-10-11')
  })

  it('crosses a year end the way the backend does', () => {
    expect(businessToday(new Date('2026-12-31T19:00:00Z'))).toBe('2027-01-01')
  })

  it('defaults to now', () => {
    expect(businessToday()).toMatch(/^\d{4}-\d{2}-\d{2}$/)
  })
})

describe('local date helpers', () => {
  it('formats a local date and adds days across a month end', () => {
    expect(toLocalDate(new Date(2026, 0, 31))).toBe('2026-01-31')
    expect(addDays('2026-01-31', 1)).toBe('2026-02-01')
    expect(addDays('2026-03-01', -1)).toBe('2026-02-28')
  })
})
