// Ashıq geografiya sózligi: Country > Region > City.
// Contract: .ai/API_CONTRACT.md, "Geography: Country > Region > City" bólimi.
import { apiFetch } from '../utils/api'
import { readApiError } from '../utils/errorHandler'
import type { Language } from '../i18n/options'
import { translateNow } from '../i18n/translateNow'
import { API_BASE_URL } from '../utils/apiBase'

export interface GeographyNames {
  name_uz: string
  name_ru: string
  name_en: string
}

export interface GeographyCountry extends GeographyNames {
  id: number
  code: string
  currency: string
  hotel_count: number
  image_url: string | null
}

export interface GeographyRegion extends GeographyNames {
  id: number
  hotel_count: number
  image_url: string | null
}

type Result<T> = { data: T | null; error: string | null }

/** Bet tilindegi at; sol at bos bolsa inglizsha. */
export function geographyName(row: GeographyNames, language: Language): string {
  return row[`name_${language}`].trim() || row.name_en
}

export class GeographyAdapter {
  constructor(private baseUrl: string = API_BASE_URL) {}

  private async get<T>(path: string): Promise<Result<T>> {
    try {
      const response = await apiFetch(`${this.baseUrl}${path}`)
      if (!response.ok) {
        return { data: null, error: (await readApiError(response)).message }
      }
      return { data: await response.json(), error: null }
    } catch (error) {
      return { data: null, error: error instanceof Error ? error.message : translateNow('apiError.networkOccurred') }
    }
  }

  getCountries(): Promise<Result<GeographyCountry[]>> {
    return this.get('/api/v1/geography/countries/')
  }

  getRegions(countryCode: string): Promise<Result<GeographyRegion[]>> {
    return this.get(`/api/v1/geography/countries/${encodeURIComponent(countryCode)}/regions/`)
  }
}

export const geographyAdapter = new GeographyAdapter()
