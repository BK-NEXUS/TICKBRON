import { describe, it, expect } from 'vitest'
import { validateCustomRange, STATUS_PRESET_PERIODS } from './statusPeriod'
import { periodLabel } from './statusFormat'

describe('validateCustomRange', () => {
  it('accepts from <= to, also the same day', () => {
    expect(validateCustomRange('2026-01-01', '2026-03-01')).toBeNull()
    expect(validateCustomRange('2026-01-01', '2026-01-01')).toBeNull()
  })

  it('needs both dates', () => {
    expect(validateCustomRange('', '2026-03-01')).toBe('Choose both dates.')
    expect(validateCustomRange('2026-01-01', '')).toBe('Choose both dates.')
  })

  it('refuses a "to" before the "from"', () => {
    expect(validateCustomRange('2026-03-01', '2026-01-01')).toBe('"From" must not be after "To".')
  })

  it('allows exactly 20 years and refuses more', () => {
    expect(validateCustomRange('2006-10-07', '2026-10-07')).toBeNull()
    expect(validateCustomRange('2006-10-06', '2026-10-07')).toBe('The range can be at most 20 years.')
  })

  it('handles 29 February as the start', () => {
    expect(validateCustomRange('2004-02-29', '2024-02-29')).toBeNull()
    expect(validateCustomRange('2004-02-29', '2024-03-01')).toBe('The range can be at most 20 years.')
  })
})

describe('preset periods', () => {
  it('has a readable label for each', () => {
    expect(STATUS_PRESET_PERIODS.map(p => p.value)).toEqual(
      ['today', 'last_7_days', 'last_30_days', 'this_year', 'last_5_years', 'last_10_years'])
    STATUS_PRESET_PERIODS.forEach(p => expect(periodLabel(p.value)).toBe(p.label))
  })

  it('labels a custom range with its dates', () => {
    expect(periodLabel('custom', { from: '2026-01-01', to: '2026-03-01' })).toBe('2026-01-01 – 2026-03-01')
    expect(periodLabel('custom')).toBe('Custom range')
  })
})
