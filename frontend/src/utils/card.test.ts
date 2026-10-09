import { describe, it, expect } from 'vitest'
import { cardNumberDigits, formatCardNumber, isCardNumberValid, isExpiryValid, formatExpiry, isCvvValid, isCardholderValid } from './card'

describe('card number', () => {
  it('keeps at most 16 digits and groups them by four', () => {
    expect(cardNumberDigits('4111 1111-1111 1111 99')).toBe('4111111111111111')
    expect(formatCardNumber('4111111111111111')).toBe('4111 1111 1111 1111')
    expect(formatCardNumber('41111')).toBe('4111 1')
    expect(formatCardNumber('abcd')).toBe('')
  })

  it('accepts a 16 digit number that passes the Luhn check', () => {
    expect(isCardNumberValid('4111 1111 1111 1111')).toBe(true)
    expect(isCardNumberValid('5555 5555 5555 4444')).toBe(true)
  })

  it('rejects a wrong check digit, a short number and an empty one', () => {
    expect(isCardNumberValid('4111 1111 1111 1112')).toBe(false)
    expect(isCardNumberValid('4111 1111 1111')).toBe(false)
    expect(isCardNumberValid('')).toBe(false)
  })
})

describe('expiry', () => {
  const now = new Date(2026, 9, 9) // 9 October 2026

  it('formats as MM/YY while typing', () => {
    expect(formatExpiry('1')).toBe('1')
    expect(formatExpiry('12')).toBe('12')
    expect(formatExpiry('123')).toBe('12/3')
    expect(formatExpiry('12/2799')).toBe('12/27')
  })

  it('accepts this month and later, up to 20 years ahead', () => {
    expect(isExpiryValid('10/26', now)).toBe(true)
    expect(isExpiryValid('01/27', now)).toBe(true)
    expect(isExpiryValid('10/46', now)).toBe(true)
  })

  it('rejects a past month, month 00 and 13, a far future year and an incomplete value', () => {
    expect(isExpiryValid('09/26', now)).toBe(false)
    expect(isExpiryValid('00/28', now)).toBe(false)
    expect(isExpiryValid('13/28', now)).toBe(false)
    expect(isExpiryValid('11/46', now)).toBe(false)
    expect(isExpiryValid('1/2', now)).toBe(false)
  })
})

describe('cvv and cardholder', () => {
  it('needs 3 digits', () => {
    expect(isCvvValid('123')).toBe(true)
    expect(isCvvValid('12')).toBe(false)
    expect(isCvvValid('12a')).toBe(false)
    expect(isCvvValid('1234')).toBe(false)
  })

  it('needs a name of letters, spaces, dots, apostrophes or hyphens, at least 2 characters', () => {
    expect(isCardholderValid('ALISHER NAVOIY')).toBe(true)
    expect(isCardholderValid("O'Neil-Smith Jr.")).toBe(true)
    expect(isCardholderValid('A')).toBe(false)
    expect(isCardholderValid('J0hn')).toBe(false)
    expect(isCardholderValid('  ')).toBe(false)
  })
})
