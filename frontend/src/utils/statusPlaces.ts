// Admin Status tereńlewiniń mámleket hám region qatarları: URL kilti hám bet tilindegi at.
import type { Language } from '../i18n/options'
import { geographyName } from '../adapters/geographyAdapter'

/** Status API mámleketsiz yamasa regionsız mehmanxanalar ushın paydalanatuǵın URL bólegi. */
export const UNSPECIFIED_KEY = 'unspecified'

export interface StatusPlace {
  /** ISO kod (mámleket) yamasa region id si tekst retinde; hesh nárse joq topar ushın "unspecified" */
  key: string
  names: { name_uz: string; name_ru: string; name_en: string }
}

export const countryPlace = (row: { code: string | null; name_uz: string; name_ru: string; name_en: string }): StatusPlace =>
  ({ key: row.code ?? UNSPECIFIED_KEY, names: row })

export const regionPlace = (row: { id: number | null; name_uz: string; name_ru: string; name_en: string }): StatusPlace =>
  ({ key: row.id === null ? UNSPECIFIED_KEY : String(row.id), names: row })

/** Bet tilindegi at; "Unspecified" topar `unspecified` oqıydı (awdarılǵan tekst). */
export function placeLabel(place: StatusPlace, language: Language, unspecified: string): string {
  return place.key === UNSPECIFIED_KEY ? unspecified : geographyName(place.names, language)
}
