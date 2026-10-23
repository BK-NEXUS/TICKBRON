import { describe, it, expect } from 'vitest'
import { phoneLink, telegramLink, whatsappLink } from './contactLinks'

describe('telegramLink', () => {
  it('builds a link from a username with or without @', () => {
    expect(telegramLink('@tick_bron')).toBe('https://t.me/tick_bron')
    expect(telegramLink('tick_bron')).toBe('https://t.me/tick_bron')
  })

  it.each(['a/b', 'evil.com/x', '../x', 'name?x=1', 'ab', 'a b c d e', '<script>alert(1)</script>', ''])(
    'refuses %j so the link target cannot be changed',
    (value) => {
      expect(telegramLink(value)).toBeNull()
    },
  )
})

describe('whatsappLink', () => {
  it('keeps digits only', () => {
    expect(whatsappLink('+998 90 123-45-67')).toBe('https://wa.me/998901234567')
  })

  it.each(['', 'abc', '12', '9989012345678901234567'])('refuses %j', (value) => {
    expect(whatsappLink(value)).toBeNull()
  })
})

describe('phoneLink', () => {
  it('keeps the plus and the digits only', () => {
    expect(phoneLink('+998 90 123-45-67')).toBe('tel:+998901234567')
    expect(phoneLink('90 123 45 67')).toBe('tel:901234567')
  })

  it.each(['', 'abc', '12', '+99890123456789012', 'javascript:alert(1)'])('refuses %j', (value) => {
    expect(phoneLink(value)).toBeNull()
  })
})
