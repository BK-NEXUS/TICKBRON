// Public Geography API adapter for DestinationsPage and HomePage
// Integrates with backend public geography endpoints from GEOGRAPHY_PLAN.md

import { readApiError } from '../utils/errorHandler'
import { apiFetch } from '../utils/api'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export interface PublicCountry {
  id: number
  code: string // ISO2 code
  name_en: string
  name_uz: string
  name_ru: string
  currency: string
  is_active: boolean
  sort_order: number
  hotel_count: number
  regions?: PublicRegion[]
  created_at: string
  updated_at: string
}

export interface PublicRegion {
  id: number
  country: number
  country_code?: string
  name_en: string
  name_uz: string
  name_ru: string
  slug: string
  is_active: boolean
  sort_order: number
  hotel_count: number
  cities?: PublicCity[]
  created_at: string
  updated_at: string
}

export interface PublicCity {
  id: number
  region: number
  region_id?: number
  name_en: string
  name_uz: string
  name_ru: string
  slug: string
  is_active: boolean
  sort_order: number
  hotel_count: number
  created_at: string
  updated_at: string
}

// Language type for choosing which name to display
export type GeographyLanguage = 'en' | 'uz' | 'ru'

// Helper type for getting localized name
export type LocalizedName = {
  en: string
  uz: string
  ru: string
}

export interface GetCountriesParams {
  language?: GeographyLanguage
}

export interface GetRegionsParams {
  countryCode: string
  language?: GeographyLanguage
}

export interface GetCitiesParams {
  regionId: number
  language?: GeographyLanguage
}

class GeographyAdapter {
  private baseUrl: string

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<{ data: T | null; error: string | null }> {
    const url = `${this.baseUrl}${endpoint}`

    const defaultOptions: RequestInit = {
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
      },
      ...options,
    }

    try {
      const response = await apiFetch(url, defaultOptions)

      if (!response.ok) {
        const apiError = await readApiError(response, {
          401: 'Authentication required',
          403: 'Access denied',
          404: 'Resource not found',
        })
        return { data: null, error: apiError.message }
      }

      // Handle 204 No Content
      if (response.status === 204) {
        return { data: null as T, error: null }
      }

      const data = await response.json()
      return { data, error: null }
    } catch (error) {
      return {
        data: null,
        error: error instanceof Error ? error.message : 'Network error occurred',
      }
    }
  }

  /**
   * Get all active countries with hotel counts
   * Integrates with GET /api/v1/geography/countries/ endpoint
   */
  async getCountries(params?: GetCountriesParams): Promise<{ data: PublicCountry[] | null; error: string | null }> {
    const queryParams = new URLSearchParams()
    if (params?.language) queryParams.append('language', params.language)

    const endpoint = `/api/v1/geography/countries/${queryParams.toString() ? `?${queryParams.toString()}` : ''}`
    return this.request<PublicCountry[]>(endpoint)
  }

  /**
   * Get all active regions for a country with hotel counts
   * Integrates with GET /api/v1/geography/countries/{code}/regions/ endpoint
   */
  async getRegions(params: GetRegionsParams): Promise<{ data: PublicRegion[] | null; error: string | null }> {
    const queryParams = new URLSearchParams()
    if (params.language) queryParams.append('language', params.language)

    const endpoint = `/api/v1/geography/countries/${params.countryCode}/regions/${queryParams.toString() ? `?${queryParams.toString()}` : ''}`
    return this.request<PublicRegion[]>(endpoint)
  }

  /**
   * Get all active cities for a region with hotel counts
   * Integrates with GET /api/v1/geography/regions/{id}/cities/ endpoint
   */
  async getCities(params: GetCitiesParams): Promise<{ data: PublicCity[] | null; error: string | null }> {
    const queryParams = new URLSearchParams()
    if (params.language) queryParams.append('language', params.language)

    const endpoint = `/api/v1/geography/regions/${params.regionId}/cities/${queryParams.toString() ? `?${queryParams.toString()}` : ''}`
    return this.request<PublicCity[]>(endpoint)
  }

  /**
   * Get a single country by code
   * Integrates with GET /api/v1/geography/countries/{code}/ endpoint
   */
  async getCountry(code: string, language?: GeographyLanguage): Promise<{ data: PublicCountry | null; error: string | null }> {
    const queryParams = new URLSearchParams()
    if (language) queryParams.append('language', language)

    const endpoint = `/api/v1/geography/countries/${code}/${queryParams.toString() ? `?${queryParams.toString()}` : ''}`
    return this.request<PublicCountry>(endpoint)
  }

  /**
   * Get a single region by ID
   * Integrates with GET /api/v1/geography/regions/{id}/ endpoint
   */
  async getRegion(id: number, language?: GeographyLanguage): Promise<{ data: PublicRegion | null; error: string | null }> {
    const queryParams = new URLSearchParams()
    if (language) queryParams.append('language', language)

    const endpoint = `/api/v1/geography/regions/${id}/${queryParams.toString() ? `?${queryParams.toString()}` : ''}`
    return this.request<PublicRegion>(endpoint)
  }

  /**
   * Get a single city by ID
   * Integrates with GET /api/v1/geography/cities/{id}/ endpoint
   */
  async getCity(id: number, language?: GeographyLanguage): Promise<{ data: PublicCity | null; error: string | null }> {
    const queryParams = new URLSearchParams()
    if (language) queryParams.append('language', language)

    const endpoint = `/api/v1/geography/cities/${id}/${queryParams.toString() ? `?${queryParams.toString()}` : ''}`
    return this.request<PublicCity>(endpoint)
  }

  /**
   * Get the localized name for a country/region/city based on the current language
   * Falls back to English if the requested language is not available
   */
  static getLocalizedName(item: { name_en: string; name_uz: string; name_ru: string }, language: GeographyLanguage): string {
    const nameMap: Record<GeographyLanguage, string> = {
      en: item.name_en,
      uz: item.name_uz,
      ru: item.name_ru,
    }
    return nameMap[language] || item.name_en
  }
}

// Export singleton instance
export const geographyAdapter = new GeographyAdapter()

// Export class for testing
export { GeographyAdapter }