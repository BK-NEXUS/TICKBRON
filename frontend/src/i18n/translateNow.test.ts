import { describe, it, expect, afterEach } from 'vitest'
import { translateNow } from './translateNow'
import { setActiveLanguage } from './languageChoice'
import { uz } from './messages/uz'
import { ru } from './messages/ru'
import { en } from './messages/en'

describe('translateNow: text for plain code that has no React context', () => {
  afterEach(() => setActiveLanguage('en'))

  it.each([
    ['en', en], ['uz', uz], ['ru', ru],
  ] as const)('speaks the page language (%s)', (language, catalog) => {
    setActiveLanguage(language)
    expect(translateNow('apiError.network')).toBe(catalog['apiError.network'])
  })

  it('fills in values', () => {
    setActiveLanguage('en')
    expect(translateNow('apiError.retryAfter', { seconds: 30 })).toBe('Too many requests. Please try again in 30 seconds.')
  })

  it('has the three languages for every apiError text', () => {
    const keys = Object.keys(en).filter((key) => key.startsWith('apiError.'))
    expect(keys.length).toBeGreaterThan(10)
    for (const key of keys) {
      expect(uz[key as keyof typeof uz], key).toBeTruthy()
      expect(ru[key as keyof typeof ru], key).toBeTruthy()
    }
  })
})
