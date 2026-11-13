import type { PropertyTexts } from '../adapters/partnerAdapter'

export const HOTEL_TEXT_LANGUAGES = ['uz', 'ru', 'en'] as const
export type HotelTextLanguage = (typeof HOTEL_TEXT_LANGUAGES)[number]

/** Hár til ushın bir at hám bir táripleme, formada terilgenindey (toltırılmaǵanlar ushın bos qatarlar). */
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

/** Atı bar tiller; atı joq til taslanıp ketedi (API bar nárseni saqlaydı). */
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
