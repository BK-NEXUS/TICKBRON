// Public geography dictionary: Country > Region > City.
// Contract: .ai/API_CONTRACT.md, section "Geography: Country > Region > City".
import { apiFetch } from '../utils/api'
import { readApiError } from '../utils/errorHandler'
import type { Language } from '../i18n/options'
import { translateNow } from '../i18n/translateNow'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

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

export interface GeographyCity extends GeographyNames {
  id: number
  hotel_count: number
}

type Result<T> = { data: T | null; error: string | null }

/** The name in the page language; English when that name is blank. */
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

  getCities(regionId: number): Promise<Result<GeographyCity[]>> {
    return this.get(`/api/v1/geography/regions/${regionId}/cities/`)
  }
}

export const geographyAdapter = new GeographyAdapter()
