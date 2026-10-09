import { describe, it, expect } from 'vitest'
import { formatMoney } from './format'

const NBSP = ' '

describe('formatMoney', () => {
  it('formats UZS with space-grouped thousands and the language suffix', () => {
    expect(formatMoney(1250000, 'UZS', 'uz')).toBe(`1${NBSP}250${NBSP}000${NBSP}so'm`)
    expect(formatMoney(1250000, 'UZS', 'ru')).toBe(`1${NBSP}250${NBSP}000${NBSP}сум`)
    expect(formatMoney(1250000, 'UZS', 'en')).toBe(`1${NBSP}250${NBSP}000${NBSP}UZS`)
  })

  it('rounds UZS to whole sums', () => {
    expect(formatMoney('99999.6', 'UZS', 'uz')).toBe(`100${NBSP}000${NBSP}so'm`)
  })

  it('formats USD with two decimals in every language', () => {
    expect(formatMoney(1250, 'USD', 'en')).toBe('$1,250.00')
    expect(formatMoney('45.5', 'USD', 'ru')).toBe('$45.50')
  })

  it('accepts decimal strings from the API', () => {
    expect(formatMoney('300000.00', 'UZS', 'uz')).toBe(`300${NBSP}000${NBSP}so'm`)
  })

  it('keeps the sign of negative amounts', () => {
    expect(formatMoney(-50000, 'UZS', 'uz')).toBe(`-50${NBSP}000${NBSP}so'm`)
    expect(formatMoney(-5, 'USD', 'en')).toBe('-$5.00')
  })

  it('shows a dash for a value that is not a number', () => {
    expect(formatMoney('abc', 'UZS', 'uz')).toBe('—')
  })
})
