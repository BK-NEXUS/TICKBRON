// Status sections API adapter: admin panel /api/v1/admin-panel/status/, partner panel /api/v1/partner/status/
// Contract: .ai/API_CONTRACT.md "admin Status" (Status plan S2/S3). A booking counts when it is
// confirmed or completed; it belongs to the period of its check-in date; revenue is per currency.

import { readApiError } from '../utils/errorHandler'
import { apiFetch } from '../utils/api'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
const STATUS_URL = `${API_BASE_URL}/api/v1/admin-panel/status`

/** 'all' | 'today' | 'last_7_days' | 'last_30_days' | 'this_year' | 'last_5_years' | 'last_10_years' | 'custom' | 'YYYY' | 'YYYY-MM' */
export type StatusPeriod = string

export type StatusGranularity = 'day' | 'week' | 'month' | 'year'

/** Inclusive ISO dates; null for the whole time */
export interface PeriodRange {
  from: string | null
  to: string | null
}

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

export interface BookingStatusCounts {
  pending: number
  confirmed: number
  completed: number
  cancelled: number
  expired: number
  no_show: number
  no_show_reported: number
}

/** Totals of R12a hotel, user and owner views; `stayed` is the headline, `counted` is separate */
export interface StatusFullTotals extends StatusTotals {
  stayed: number
  counted: number
  unique_customers: number
  nights: number
  room_nights: number
  no_show: number
  no_show_reported: number
  fully_refunded: number
  upcoming: number
  booking_value: Money[]
  booking_status: BookingStatusCounts
}

export interface StatusSeriesRow {
  /** YYYY-MM-DD for day and week, YYYY-MM for month, YYYY for year */
  period: string
  start: string
  bookings: number
  guests: number
  nights: number
  stayed: number
  revenue: Money[]
}

export interface ReconciliationWindow {
  from: string | null
  to: string | null
  counted: { bookings: number; guests: number }
  stayed: { bookings: number; guests: number }
}

export interface StatusReconciliation {
  today: ReconciliationWindow
  this_week: ReconciliationWindow
  this_month: ReconciliationWindow
  this_year: ReconciliationWindow
  all_time: ReconciliationWindow
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
  period_range: PeriodRange
  totals: StatusFullTotals
  granularity: StatusGranularity
  series: StatusSeriesRow[]
  reconciliation: StatusReconciliation
  year: number
  available_years: number[]
  monthly: StatusMonth[]
}

export interface AdminStatusHotel {
  rank: number
  id: number
  name: string
  city: string
  region_id: number | null
  region: string
  country_code: string
  status: string
  created_at: string
  /** "4.50", or null without approved reviews */
  rating: string | null
  bookings: number
  guests: number
  unique_customers: number
  nights: number
  room_nights: number
  stayed: number
  revenue: Money[]
  booking_value: Money[]
}

export interface AdminHotelsPage extends StatusPage<AdminStatusHotel> {
  period_range: PeriodRange
  ordering: string
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
  guests?: number
  nights?: number
}

export interface StatusUserHotel {
  id: number
  name: string
  city: string
  country: string
  bookings: number
  stayed: number
  nights: number
  guests: number
  spent: Money[]
}

export interface StatusUserBooking {
  id: number
  reference: string
  hotel: { id: number; name: string }
  check_in: string
  check_out: string
  nights: number
  rooms: number
  guests: number
  status: string
  total_price: string
  currency: string
  charge_amount: string | null
  charge_currency: string | null
  paid: Money[]
  refunded: Money[]
}

export interface StatusUserDetail {
  user: {
    id: number
    full_name: string
    first_name: string | null
    last_name: string | null
    phone: string | null
    email: string
    date_joined: string
  }
  period: StatusPeriod
  period_range: PeriodRange
  totals: StatusFullTotals
  hotels_visited: number
  hotels: StatusUserHotel[]
  history: Omit<StatusPage<StatusUserBooking>, 'period'>
}

export interface PartnerStatusProperty extends StatusTotals {
  unique_customers: number
  nights: number
  room_nights: number
  stayed: number
  booking_value: Money[]
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
  period_range: PeriodRange
  totals: StatusFullTotals
  properties: PartnerStatusProperty[]
  granularity: StatusGranularity
  series: StatusSeriesRow[]
  reconciliation: StatusReconciliation
  year: number
  available_years: number[]
  monthly: StatusMonth[]
}

/** GET /api/v1/partner/status/hotels/{id}/ (own hotel only) */
export interface PartnerHotelStatus extends Omit<StatusHotelDetail, 'hotel'> {
  hotel: { id: number; name: string; status: string; address: string; city: string; region: string; country: string }
}

export type ArrivalsDay = 'today' | 'tomorrow'

export interface PartnerArrival {
  id: number
  reference: string
  property: { id: number; name: string }
  guest_name: string
  room_types: string[]
  rooms: number
  nights: number
  guests: number
  check_in: string
  check_out: string
  special_requests: string
  /** Only the last 4 digits of the phone */
  phone_last4: string
}

export interface PartnerArrivalsPage {
  count: number
  next: string | null
  previous: string | null
  results: PartnerArrival[]
  day: ArrivalsDay
  date: string
}

export interface CsvFile {
  blob: Blob
  filename: string
}

export interface StatusPeriodParams {
  period: StatusPeriod
  /** YYYY-MM-DD; sent only with period "custom" */
  from?: string
  to?: string
  granularity?: StatusGranularity
}

export interface StatusListParams extends StatusPeriodParams {
  search?: string
  page?: number
}

export interface AdminHotelsParams extends StatusListParams {
  /** revenue | bookings | guests | nights | rating | created_at, "-" prefix for descending */
  ordering?: string
  pageSize?: number
  country?: string
  region?: string
  status?: string
}

export interface StatusDetailParams extends StatusPeriodParams {
  year?: number
}

export interface UserDetailParams extends StatusPeriodParams {
  page?: number
}

export interface StatusResponse<T> {
  data: T | null
  error: string | null
  /** HTTP status of a failed response, e.g. 404 for another owner's hotel */
  status?: number
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

type QueryValues = Record<string, string | number | undefined>

/** from and to belong to the custom period only; other periods ignore them */
function periodValues({ period, from, to, granularity }: StatusPeriodParams): QueryValues {
  const custom = period === 'custom'
  return { period, from: custom ? from : undefined, to: custom ? to : undefined, granularity }
}

async function send(
  url: string,
  init: RequestInit,
  errorMessages: Record<number, string>,
): Promise<{ response: Response | null; error: string | null; status?: number }> {
  try {
    const response = await apiFetch(url, {
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      ...init,
    })
    if (!response.ok) {
      const apiError = await readApiError(response, errorMessages)
      return { response: null, error: apiError.message, status: response.status }
    }
    return { response, error: null }
  } catch (error) {
    return { response: null, error: error instanceof Error ? error.message : 'Network error occurred' }
  }
}

async function request<T>(
  url: string,
  init: RequestInit = { method: 'GET' },
  errorMessages: Record<number, string> = ERROR_MESSAGES,
): Promise<StatusResponse<T>> {
  const { response, error, status } = await send(url, init, errorMessages)
  if (!response) return { data: null, error, status }
  try {
    return { data: (await response.json()) as T, error: null }
  } catch (parseError) {
    return { data: null, error: parseError instanceof Error ? parseError.message : 'Network error occurred' }
  }
}

function filenameFrom(response: Response, fallback: string): string {
  const match = /filename="?([^";]+)"?/.exec(response.headers.get('Content-Disposition') ?? '')
  return match ? match[1] : fallback
}

/** CSV goes through apiFetch (session cookie + CSRF) and comes back as a blob; a plain link would not carry auth headers */
async function requestCsv(
  url: string,
  fallbackName: string,
  errorMessages: Record<number, string> = ERROR_MESSAGES,
): Promise<StatusResponse<CsvFile>> {
  const { response, error, status } = await send(url, { method: 'GET' }, errorMessages)
  if (!response) return { data: null, error, status }
  try {
    return { data: { blob: await response.blob(), filename: filenameFrom(response, fallbackName) }, error: null }
  } catch (readError) {
    return { data: null, error: readError instanceof Error ? readError.message : 'Network error occurred' }
  }
}

const listValues = ({ search, page, ...period }: StatusListParams): QueryValues =>
  ({ ...periodValues(period), search, page })

const listQuery = (params: StatusListParams) => query(listValues(params))

const hotelsValues = ({ ordering, pageSize, country, region, status, ...list }: AdminHotelsParams): QueryValues =>
  ({ ...listValues(list), ordering, page_size: pageSize, country, region, status })

const detailQuery = ({ year, ...period }: StatusDetailParams) => query({ ...periodValues(period), year })

/** The export covers the whole list, so it never carries a page */
const csvValues = (values: QueryValues): QueryValues => ({ ...values, page: undefined, export: 'csv' })

const PARTNER_URL = `${API_BASE_URL}/api/v1/partner/status`

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

  getAdminHotels(params: AdminHotelsParams) {
    return request<AdminHotelsPage>(`${STATUS_URL}/hotels/${query(hotelsValues(params))}`)
  },

  exportAdminHotels(params: AdminHotelsParams) {
    return requestCsv(`${STATUS_URL}/hotels/${query(csvValues(hotelsValues(params)))}`, 'status_hotels.csv')
  },

  getHotelDetail(hotelId: number, params: StatusDetailParams) {
    return request<StatusHotelDetail>(`${STATUS_URL}/hotels/${hotelId}/${detailQuery(params)}`)
  },

  getUsers(params: StatusListParams) {
    return request<StatusPage<StatusUser>>(`${STATUS_URL}/users/${listQuery(params)}`)
  },

  exportUsers(params: StatusListParams) {
    return requestCsv(`${STATUS_URL}/users/${query(csvValues(listValues(params)))}`, 'status_users.csv')
  },

  getUserDetail(userId: number, { page, ...period }: UserDetailParams) {
    return request<StatusUserDetail>(`${STATUS_URL}/users/${userId}/${query({ ...periodValues(period), page })}`)
  },

  exportUserHistory(userId: number, period: StatusPeriodParams) {
    return requestCsv(
      `${STATUS_URL}/users/${userId}/${query({ ...periodValues(period), export: 'csv' })}`,
      `status_user_${userId}_history.csv`)
  },

  getPartnerStatus(params: StatusDetailParams) {
    return request<PartnerStatus>(`${PARTNER_URL}/${detailQuery(params)}`, { method: 'GET' }, PARTNER_ERROR_MESSAGES)
  },

  exportPartnerReconciliation(period: StatusPeriodParams) {
    return requestCsv(
      `${PARTNER_URL}/${query({ ...periodValues(period), export: 'csv' })}`,
      'partner_reconciliation.csv', PARTNER_ERROR_MESSAGES)
  },

  getPartnerHotel(hotelId: number, params: StatusDetailParams) {
    return request<PartnerHotelStatus>(
      `${PARTNER_URL}/hotels/${hotelId}/${detailQuery(params)}`, { method: 'GET' }, PARTNER_ERROR_MESSAGES)
  },

  getPartnerArrivals({ day, property, page }: { day?: ArrivalsDay; property?: number; page?: number }) {
    return request<PartnerArrivalsPage>(
      `${PARTNER_URL}/arrivals/${query({ day, property, page })}`, { method: 'GET' }, PARTNER_ERROR_MESSAGES)
  },

  /** Admin sets a property's region (blank clears it: "Unspecified"). Contract: S1 */
  setPropertyRegion(propertyId: number, state: string) {
    return request<{ id: number; state: string | null }>(
      `${API_BASE_URL}/api/v1/admin-panel/properties/${propertyId}/region/`,
      { method: 'PATCH', body: JSON.stringify({ state }) },
    )
  },
}
