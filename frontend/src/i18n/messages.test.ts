import { describe, it, expect } from 'vitest'
import { en } from './messages/en'
import { uz } from './messages/uz'
import { ru } from './messages/ru'

const placeholders = (text: string) => (text.match(/\{\w+\}/g) ?? []).sort()

describe('message catalogs', () => {
  it.each([['uz', uz], ['ru', ru]])('%s has exactly the keys of en', (_name, catalog) => {
    expect(Object.keys(catalog).sort()).toEqual(Object.keys(en).sort())
  })

  it.each([['uz', uz], ['ru', ru]])('%s keeps the placeholders of en', (_name, catalog) => {
    for (const key of Object.keys(en) as (keyof typeof en)[]) {
      expect(placeholders(catalog[key]), key).toEqual(placeholders(en[key]))
    }
  })

  it('has no empty text', () => {
    for (const catalog of [en, uz, ru]) {
      for (const [key, text] of Object.entries(catalog)) expect(text.trim(), key).not.toBe('')
    }
  })
})
