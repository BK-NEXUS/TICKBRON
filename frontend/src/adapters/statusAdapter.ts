// Status sections API adapter: admin panel /api/v1/admin-panel/status/, partner panel /api/v1/partner/status/
// Contract: .ai/API_CONTRACT.md "admin Status" (Status plan S2/S3). A booking counts when it is
// confirmed or completed; it belongs to the period of its check-in date; revenue is per currency.

import { readApiError } from '../utils/errorHandler'
import { apiFetch } from '../utils/api'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
const STATUS_URL = `${API_BASE_URL}/api/v1/admin-panel/status`

/** 'all' | 'YYYY' | 'YYYY-MM' */
export type StatusPeriod = string

/** One currency's total; amount is a decimal string. Currencies are never added together. */
export interface Money {
  currency: string
  amount: string
}

interface RankedRow {
  rank: number
  bookings: number
  guests: number
  revenue: Money[]
}

export interface StatusCountry extends RankedRow {
  country: string
  hotels: number
}

export interface StatusRegion extends RankedRow {
  region: string
  hotels: number
}

export interface StatusHotel extends RankedRow {
  id: number
  name: string
  city: string
  status: string
}

export interface StatusPage<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
  period: StatusPeriod
}

export interface StatusTotals {
  bookings: number
  guests: number
  revenue: Money[]
}

export interface StatusMonth extends StatusTotals {
  /** YYYY-MM */
  month: string
}

export interface StatusHotelDetail {
  hotel: {
    id: number
    name: string
    status: string
    address: string
    city: string
    region: string
    country: string
    registered_at: string
    owner: { id: number; name: string; email: string; phone: string | null }
  }
  period: StatusPeriod
  totals: StatusTotals
  year: number
  available_years: number[]
  monthly: StatusMonth[]
}

export interface StatusUser {
  rank: number
  id: number
  full_name: string
  first_name: string | null
  last_name: string | null
  phone: string | null
  email: string
  bookings: number
  total_spent: Money[]
  /** YYYY-MM-DD: check-in of the latest counted booking */
  last_booking_date: string
}

export interface PartnerStatusProperty extends StatusTotals {
  id: number
  name: string
  city: string
  region: string
  country: string
  status: string
}

/** GET /api/v1/partner/status/ (the owner's own properties only). Contract: S4 */
export interface PartnerStatus {
  /** YYYY-MM-DD: when the owner's account was created */
  since: string
  period: StatusPeriod
  totals: StatusTotals
  properties: PartnerStatusProperty[]
  year: number
  available_years: number[]
  monthly: StatusMonth[]
}

export interface StatusListParams {
  period: StatusPeriod
  search?: string
  page?: number
}

export interface StatusResponse<T> {
  data: T | null
  error: string | null
}

const ERROR_MESSAGES = { 401: 'Authentication required', 403: 'Admin or staff role required', 404: 'Not found' }
const PARTNER_ERROR_MESSAGES = { ...ERROR_MESSAGES, 403: 'Hotel owner role required' }

function query(params: Record<string, string | number | undefined>): string {
  const search = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== '') search.append(key, String(value))
  })
  const text = search.toString()
  return text ? `?${text}` : ''
}

async function request<T>(
  url: string,
  init: RequestInit = { method: 'GET' },
  errorMessages: Record<number, string> = ERROR_MESSAGES,
): Promise<StatusResponse<T>> {
  try {
    const response = await apiFetch(url, {
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      ...init,
    })
    if (!response.ok) {
      const apiError = await readApiError(response, errorMessages)
      return { data: null, error: apiError.message }
    }
    return { data: (await response.json()) as T, error: null }
  } catch (error) {
    return { data: null, error: error instanceof Error ? error.message : 'Network error occurred' }
  }
}

const listQuery = ({ period, search, page }: StatusListParams) => query({ period, search, page })

export const statusAdapter = {
  getCountries(params: StatusListParams) {
    return request<StatusPage<StatusCountry>>(`${STATUS_URL}/countries/${listQuery(params)}`)
  },

  getRegions(country: string, params: StatusListParams) {
    return request<StatusPage<StatusRegion> & { country: string }>(
      `${STATUS_URL}/countries/${encodeURIComponent(country)}/regions/${listQuery(params)}`)
  },

  getHotels(country: string, region: string, params: StatusListParams) {
    return request<StatusPage<StatusHotel> & { country: string; region: string }>(
      `${STATUS_URL}/countries/${encodeURIComponent(country)}/regions/${encodeURIComponent(region)}/hotels/${listQuery(params)}`)
  },

  getHotelDetail(hotelId: number, params: { period: StatusPeriod; year?: number }) {
    return request<StatusHotelDetail>(`${STATUS_URL}/hotels/${hotelId}/${query(params)}`)
  },

  getUsers(params: StatusListParams) {
    return request<StatusPage<StatusUser>>(`${STATUS_URL}/users/${listQuery(params)}`)
  },

  getPartnerStatus(params: { period: StatusPeriod; year?: number }) {
    return request<PartnerStatus>(
      `${API_BASE_URL}/api/v1/partner/status/${query(params)}`, { method: 'GET' }, PARTNER_ERROR_MESSAGES)
  },

  /** Admin sets a property's region (blank clears it: "Unspecified"). Contract: S1 */
  setPropertyRegion(propertyId: number, state: string) {
    return request<{ id: number; state: string | null }>(
      `${API_BASE_URL}/api/v1/admin-panel/properties/${propertyId}/region/`,
      { method: 'PATCH', body: JSON.stringify({ state }) },
    )
  },
}
