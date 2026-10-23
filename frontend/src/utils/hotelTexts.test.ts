import { describe, it, expect } from 'vitest'
import { emptyHotelTexts, hasHotelName, hotelTextsFromApi, hotelTextsToApi } from './hotelTexts'

describe('hotelTexts', () => {
  it('starts empty and without a name', () => {
    expect(hasHotelName(emptyHotelTexts())).toBe(false)
  })

  it('a name of spaces is no name', () => {
    const form = emptyHotelTexts()
    form.en.name = '   '
    expect(hasHotelName(form)).toBe(false)
    expect(hotelTextsToApi(form)).toEqual({})
  })

  it('sends only the languages that have a name, trimmed', () => {
    const form = emptyHotelTexts()
    form.uz = { name: ' Oltin Vodiy ', description: ' Markazda ' }
    form.ru.description = 'only a description'
    expect(hasHotelName(form)).toBe(true)
    expect(hotelTextsToApi(form)).toEqual({ uz: { name: 'Oltin Vodiy', description: 'Markazda' } })
  })

  it('fills the form from what the API saved', () => {
    const form = hotelTextsFromApi({ en: { name: 'Hotel', description: 'Quiet' } })
    expect(form.en).toEqual({ name: 'Hotel', description: 'Quiet' })
    expect(form.ru).toEqual({ name: '', description: '' })
    expect(hotelTextsFromApi(undefined)).toEqual(emptyHotelTexts())
  })
})
