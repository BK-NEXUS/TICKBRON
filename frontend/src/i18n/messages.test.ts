import { describe, it, expect } from 'vitest'
import { en as enCatalog } from './messages/en'
import { uz } from './messages/uz'
import { ru } from './messages/ru'

const en = enCatalog as Record<string, string>
const placeholders = (text: string) => (text.match(/\{\w+\}/g) ?? []).sort()

// Plural forms ("guests.one", ".few", ".many") may differ by language: Russian has four, Uzbek one.
// Every base needs ".other" everywhere, and every form of a base keeps the same placeholders.
const FORM = /\.(one|few|many)$/
const baseKeys = (catalog: Record<string, string>) =>
  [...new Set(Object.keys(catalog).map((key) => key.replace(FORM, '').replace(/\.other$/, '')))].sort()

describe('message catalogs', () => {
  it.each([['uz', uz], ['ru', ru]])('%s has exactly the keys of en (plural forms aside)', (_name, catalog) => {
    expect(baseKeys(catalog)).toEqual(baseKeys(en))
  })

  it.each([['en', en], ['uz', uz], ['ru', ru]])('%s has the ".other" form of every plural', (_name, catalog) => {
    const keys = Object.keys(catalog)
    for (const key of keys.filter((k) => FORM.test(k))) {
      expect(keys, key).toContain(key.replace(FORM, '.other'))
    }
  })

  it.each([['uz', uz], ['ru', ru]])('%s keeps the placeholders of en', (_name, catalog) => {
    const texts = catalog as Record<string, string>
    for (const key of Object.keys(texts)) {
      const reference = en[key] ?? en[key.replace(FORM, '.other')]
      expect(placeholders(texts[key]), key).toEqual(placeholders(reference))
    }
  })

  it('has no empty text', () => {
    for (const catalog of [en, uz, ru]) {
      for (const [key, text] of Object.entries(catalog)) expect(text.trim(), key).not.toBe('')
    }
  })
})
