import { describe, it, expect } from 'vitest'
import { formatCount, formatMoney, formatMoneyCompact, formatMoneyList, monthLabel, periodLabel } from './statusFormat'

describe('statusFormat', () => {
  it('formats counts with thousand separators', () => {
    expect(formatCount(0)).toBe('0')
    expect(formatCount(1234567)).toBe('1,234,567')
  })

  it('formats one amount with its currency and separators', () => {
    expect(formatMoney({ currency: 'USD', amount: '1234.5' })).toBe('$1,234.50')
    expect(formatMoney({ currency: 'KZT', amount: '50000.00' })).toMatch(/^KZT\s?50,000\.00$/)
  })

  it('lists every currency, never adding them up', () => {
    expect(formatMoneyList([
      { currency: 'EUR', amount: '60.00' },
      { currency: 'USD', amount: '530.00' },
    ])).toBe('€60.00 · $530.00')
  })

  it('shows a dash when there is no revenue', () => {
    expect(formatMoneyList([])).toBe('—')
  })

  it('names months and periods', () => {
    expect(monthLabel('2026-04')).toBe('Apr')
    expect(periodLabel('all')).toBe('All time')
    expect(periodLabel('2026')).toBe('2026')
    expect(periodLabel('2026-04')).toBe('April 2026')
  })

  it('formatMoneyCompact: a short amount for chart labels', () => {
    expect(formatMoneyCompact({ currency: 'USD', amount: '54201950.00' })).toBe('$54.2M')
    expect(formatMoneyCompact({ currency: 'USD', amount: '1500.00' })).toBe('$1.5K')
    expect(formatMoneyCompact({ currency: 'USD', amount: '350.00' })).toBe('$350')
    expect(formatMoneyCompact({ currency: 'UZS', amount: '54201950.00' })).toMatch(/^UZS\s?54\.2M$/)
    expect(formatMoneyCompact({ currency: 'XYZ?', amount: '2500000' })).toBe('XYZ? 2.5M')
  })
})
