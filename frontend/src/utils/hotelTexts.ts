import type { PropertyTexts } from '../adapters/partnerAdapter'

export const HOTEL_TEXT_LANGUAGES = ['uz', 'ru', 'en'] as const
export type HotelTextLanguage = (typeof HOTEL_TEXT_LANGUAGES)[number]

/** One name and one description per language, as typed in the form (empty strings for what is not filled). */
export type HotelTextsForm = Record<HotelTextLanguage, { name: string; description: string }>

export const emptyHotelTexts = (): HotelTextsForm => ({
  uz: { name: '', description: '' },
  ru: { name: '', description: '' },
  en: { name: '', description: '' },
})

export function hotelTextsFromApi(saved: PropertyTexts | undefined): HotelTextsForm {
  const form = emptyHotelTexts()
  for (const language of HOTEL_TEXT_LANGUAGES) {
    const row = saved?.[language]
    if (row) form[language] = { name: row.name, description: row.description }
  }
  return form
}

/** The languages with a name; a language without a name is left out (the API keeps what it has). */
export function hotelTextsToApi(form: HotelTextsForm): PropertyTexts {
  const texts: PropertyTexts = {}
  for (const language of HOTEL_TEXT_LANGUAGES) {
    const name = form[language].name.trim()
    if (name) texts[language] = { name, description: form[language].description.trim() }
  }
  return texts
}

export const hasHotelName = (form: HotelTextsForm): boolean =>
  HOTEL_TEXT_LANGUAGES.some(language => form[language].name.trim() !== '')
