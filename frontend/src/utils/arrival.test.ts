import { describe, it, expect } from 'vitest'
import { ARRIVAL_GRACE_HOURS, DEFAULT_ARRIVAL_TIME, formatArrivalTime, isArrivalPassed } from './arrival'

describe('arrival time helpers', () => {
  it('formats the API time as HH:MM', () => {
    expect(formatArrivalTime('10:30:00')).toBe('10:30')
    expect(formatArrivalTime('09:05')).toBe('09:05')
  })

  it('has the same wait as the backend and a sensible default', () => {
    expect(ARRIVAL_GRACE_HOURS).toBe(2)
    expect(DEFAULT_ARRIVAL_TIME).toBe('14:00')
  })

  // 2026-11-03 10:00 UTC is 15:00 in Tashkent
  const now = new Date('2026-11-03T10:00:00Z')

  it('a time that has passed today in Tashkent is refused', () => {
    expect(isArrivalPassed('2026-11-03', '14:00', now)).toBe(true)
    expect(isArrivalPassed('2026-11-03', '15:00', now)).toBe(true)
  })

  it('a later time today is fine', () => {
    expect(isArrivalPassed('2026-11-03', '15:01', now)).toBe(false)
  })

  it('any time on another day is fine', () => {
    expect(isArrivalPassed('2026-11-04', '06:00', now)).toBe(false)
  })
})
