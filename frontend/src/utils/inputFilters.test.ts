import { describe, it, expect } from 'vitest'
import { cleanField, cleanPersonName, cleanPlaceName, cleanPhone, isPhoneValid, blocksNumberKey } from './inputFilters'

describe('cleanPersonName', () => {
  it('drops digits and symbols but keeps letters of every alphabet, spaces, hyphen, dot and apostrophes', () => {
    expect(cleanPersonName('Olim123')).toBe('Olim')
    expect(cleanPersonName("O'tkir-Bek Jr.")).toBe("O'tkir-Bek Jr.")
    expect(cleanPersonName('Алишер Навоий')).toBe('Алишер Навоий')
    expect(cleanPersonName('Oʻtkir')).toBe('Oʻtkir')
    expect(cleanPersonName('a@b#c$1%')).toBe('abc')
  })
  it('stops at 100 characters', () => {
    expect(cleanPersonName('a'.repeat(150))).toHaveLength(100)
  })
})

describe('cleanPlaceName', () => {
  it('has no digits either, and allows parentheses for names like "Tashkent (city)"', () => {
    expect(cleanPlaceName('Tashkent 2')).toBe('Tashkent ')
    expect(cleanPlaceName('Tashkent (city)')).toBe('Tashkent (city)')
  })
})

describe('cleanPhone', () => {
  it('keeps digits, a leading plus, and at most 15 digits', () => {
    expect(cleanPhone('+998 90 123-45-67abc')).toBe('+998901234567')
    expect(cleanPhone('12+34')).toBe('1234')
    expect(cleanPhone('9'.repeat(20))).toHaveLength(15)
  })
})

describe('blocksNumberKey', () => {
  it('blocks e, E, + and - in a number box, lets digits, dot, comma and control keys through', () => {
    for (const key of ['e', 'E', '+', '-']) expect(blocksNumberKey(key)).toBe(true)
    for (const key of ['1', '.', ',', 'Backspace', 'Tab', 'ArrowLeft']) expect(blocksNumberKey(key)).toBe(false)
  })
})

describe('cleanField', () => {
  it('filters by field name and leaves other fields alone', () => {
    expect(cleanField('first_name', 'Ali9')).toBe('Ali')
    expect(cleanField('full_name', 'Ali 9 Vali')).toBe('Ali  Vali')
    expect(cleanField('whatsapp', '+99 8x9')).toBe('+9989')
    expect(cleanField('special_requests', 'Room 12, high floor')).toBe('Room 12, high floor')
  })
})

describe('isPhoneValid', () => {
  it('needs a plus, a country code and 8 to 15 digits (the server checks the number itself)', () => {
    expect(isPhoneValid('+998901234567')).toBe(true)
    expect(isPhoneValid('+998 90 123 45 67')).toBe(true)
    expect(isPhoneValid('998901234567')).toBe(false)
    expect(isPhoneValid('+99890')).toBe(false)
    expect(isPhoneValid('+9989012345678901')).toBe(false)
    expect(isPhoneValid('')).toBe(false)
  })
})
