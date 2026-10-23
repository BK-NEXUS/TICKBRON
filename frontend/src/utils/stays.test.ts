import { describe, it, expect } from 'vitest'
import { overlapsOwnStay } from './stays'

const own = [{ check_in: '2026-11-05', check_out: '2026-11-10', status: 'confirmed' }]

describe('overlapsOwnStay', () => {
  it.each([
    ['2026-11-05', '2026-11-10'], ['2026-11-07', '2026-11-08'], ['2026-11-03', '2026-11-06'],
    ['2026-11-09', '2026-11-12'], ['2026-11-01', '2026-11-20'],
  ])('refuses %s to %s, which shares a night', (checkIn, checkOut) => {
    expect(overlapsOwnStay(own, checkIn, checkOut)).toBe(true)
  })

  it.each([['2026-11-10', '2026-11-12'], ['2026-11-01', '2026-11-05'], ['2026-12-01', '2026-12-03']])(
    'allows %s to %s: it starts the day the stay ends, ends the day it starts, or is far away', (checkIn, checkOut) => {
      expect(overlapsOwnStay(own, checkIn, checkOut)).toBe(false)
    })

  it('ignores cancelled, completed and no-show stays and an empty list', () => {
    for (const status of ['cancelled', 'completed', 'no_show']) {
      expect(overlapsOwnStay([{ ...own[0], status }], '2026-11-06', '2026-11-08')).toBe(false)
    }
    expect(overlapsOwnStay([], '2026-11-06', '2026-11-08')).toBe(false)
  })

  it('counts a pending booking like a confirmed one', () => {
    expect(overlapsOwnStay([{ ...own[0], status: 'pending' }], '2026-11-06', '2026-11-08')).toBe(true)
  })
})
