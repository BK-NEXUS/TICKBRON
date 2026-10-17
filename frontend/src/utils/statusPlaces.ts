// Country and region rows of the admin Status drill-down: URL key and name in the page language.
import type { Language } from '../i18n/options'
import { geographyName } from '../adapters/geographyAdapter'

/** The URL segment the Status API uses for hotels without a country or region. */
export const UNSPECIFIED_KEY = 'unspecified'

export interface StatusPlace {
  /** ISO code (country) or region id as text; "unspecified" for the group without one */
  key: string
  names: { name_uz: string; name_ru: string; name_en: string }
}

export const countryPlace = (row: { code: string | null; name_uz: string; name_ru: string; name_en: string }): StatusPlace =>
  ({ key: row.code ?? UNSPECIFIED_KEY, names: row })

export const regionPlace = (row: { id: number | null; name_uz: string; name_ru: string; name_en: string }): StatusPlace =>
  ({ key: row.id === null ? UNSPECIFIED_KEY : String(row.id), names: row })

/** Name in the page language; the "Unspecified" group reads `unspecified` (a translated text). */
export function placeLabel(place: StatusPlace, language: Language, unspecified: string): string {
  return place.key === UNSPECIFIED_KEY ? unspecified : geographyName(place.names, language)
}
