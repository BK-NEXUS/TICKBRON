// Status bólimleri API adapteri: admin panel /api/v1/admin-panel/status/, partner panel /api/v1/partner/status/
// Contract: .ai/API_CONTRACT.md "admin Status" (Status reje S2/S3). Bron tastıyıqlanǵan yamasa
// juwmaqlanǵan bolsa esaplanadı; ol kiriw sanası dáwirine tiyisli; dáramat hár valyuta boyınsha.

import { readApiError } from '../utils/errorHandler'
import { apiFetch } from '../utils/api'
import { translateNow } from '../i18n/translateNow'
import { API_BASE_URL } from '../utils/apiBase'

const STATUS_URL = `${API_BASE_URL}/api/v1/admin-panel/status`

/**
 * 'all' | 'today' | 'last_7_days' | 'last_30_days' | 'this_year' | 'last_5_years' | 'last_10_years' | 'custom' | 'YYYY' |
 * 'YYYY-MM'
 */
export type StatusPeriod = string

export type StatusGranularity = 'day' | 'week' | 'month' | 'year'

/** Shegarası kiretuǵın ISO sanalar; pútkil waqıt ushın null */
export interface PeriodRange {
  from: string | null
  to: string | null
}

/** Bir valyutanıń jıyındısı; amount onlıq qatar. Valyutalar hesh qashan qosılmaydı. */
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

/** Orınnıń úsh tildegi atları; "Unspecified" topar úshewinde de inglizsha sózdi alıp júredi. */
interface PlaceNames {
  name_uz: string
  name_ru: string
  name_en: string
}

export interface StatusCountry extends RankedRow, PlaceNames {
  /** ISO kod, "Unspecified" topar ushın null (sonda URL bólegi "unspecified") */
  code: string | null
  country: string
  hotels: number
}

export interface StatusRegion extends RankedRow, PlaceNames {
  /** Region id si, "Unspecified" topar ushın null (sonda URL bólegi "unspecified") */
  id: number | null
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

/** R12a mehmanxana, paydalanıwshı hám iye kórinisleriniń jıynaqları; `stayed` tiykarǵı san, `counted` bólek */
export interface StatusFullTotals extends StatusTotals {
  stayed: number
  counted: number
  unique_customers: number
  nights: number
  room_nights: number
  no_show: number
  no_show_reported: number
  upcoming: number
  booking_value: Money[]
  booking_status: BookingStatusCounts
}

export interface StatusSeriesRow {
  /** Kún hám hápte ushın YYYY-MM-DD, ay ushın YYYY-MM, jıl ushın YYYY */
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

/** R12 qosımshaları: tek oqıw tuwındı sanlar; dárejeler procent qatarları, bóliwge hesh nárse bolmasa null */
export interface StatusInsights {
  cancellation_rate: string | null
  occupancy_rate: string | null
  average_booking_value: Money[]
  average_stay_nights: string | null
  /** Bron jasalǵannan kiriwge shekemgi kúnler ortashası (Status v2) */
  average_lead_days: string | null
  /** Birneshe ret bronlaǵan mehmanlardıń procenti (Status v2) */
  repeat_guest_pct: string | null
  previous_period: {
    range: PeriodRange
    totals: { bookings: number; guests: number; nights: number; stayed: number; revenue: Money[] }
  } | null
  change_pct: {
    bookings: string | null
    guests: string | null
    nights: string | null
    stayed: string | null
    revenue: { currency: string; pct: string | null }[]
  } | null
}

/** Iyeniń regiondaǵı aktiv mehmanxanalar arasındaǵı orni (API 5 mehmanxanadan tómende jasıradı) */
export interface StatusRank {
  position: number
  of: number
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
  insights: StatusInsights
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
  /** "4.50", yamasa tastıyıqlanǵan sharh joq bolsa null */
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
  /** YYYY-MM-DD: eń sońǵı counted bronnıń kiriwi */
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

/**
 * Mehmanlar bir mehmanxananı qalay bahalaydı: tastıyıqlanǵan sharhlar, pútkil waqıt. `average` bir onlıq belgili tekst, sharh
 * joq bolsa null.
 */
export interface ReviewRating {
  count: number
  average: string | null
}

export interface ReviewSummary extends ReviewRating {
  /** Neshe sharh 1, 2, 3, 4 hám 5 juldız bergeni */
  distribution: number[]
  categories: Record<'cleanliness' | 'location' | 'value' | 'amenities' | 'service', string | null>
}

export interface PartnerStatusProperty extends StatusTotals {
  rating: ReviewRating
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

/** Iyeniń sanlarınıń bir kalendar ayı (Status v2) */
export interface MonthBlock {
  /** YYYY-MM */
  month: string
  range: { from: string; to: string }
  bookings: number
  guests: number
  revenue: Money[]
}

/** Bet qaysı dáwirdi kórsetpesin, usı ay aldınǵı ayǵa hám keyingi 7 kúnge qarata (Status v2) */
export interface MonthComparison {
  current: MonthBlock
  previous: MonthBlock
  change_pct: { bookings: string | null; guests: string | null; revenue: { currency: string; pct: string | null }[] }
  next_7_days: { bookings: number; guests: number }
}

/** GET /partner/status/rooms/ tiń bir xona túri (Status v2) */
export interface RoomStatusRow {
  room_type_id: number
  name: string
  property: { id: number; name: string | null }
  total_rooms: number
  bookings: number
  room_nights: number
  revenue: Money[]
  /** Barlıq counted xona túri bronlarınıń procenti; joq bolsa null */
  share_pct: string | null
  /** Procent; pútkil waqıt yamasa xonalarsız null */
  occupancy_rate: string | null
}

export interface PartnerRoomsStatus {
  period: StatusPeriod
  period_range: PeriodRange
  rows: RoomStatusRow[]
}

/** Admin sholıwındaǵı eń bánt regionlardıń biri */
export interface OverviewRegion extends PlaceNames {
  id: number | null
  hotels: number
  bookings: number
  guests: number
}

/** GET /api/v1/admin-panel/status/overview/ (pútkil platforma; Status v2) */
export interface AdminOverview {
  period: StatusPeriod
  period_range: PeriodRange
  months: MonthComparison
  totals: StatusFullTotals
  insights: StatusInsights
  /** No-show bolǵan bronlardıń procenti; bron joq bolsa null */
  no_show_rate: string | null
  /** Usı ayda, aldınǵı ayda hám dáwirde dizimnen ótken mehmanlar (staff emes) (pútkil waqıt ushın null) */
  new_users: { current_month: number; previous_month: number; in_period: number | null }
  hotels: { total: number; active: number }
  top_regions: OverviewRegion[]
  top_room_types: RoomStatusRow[]
  year: number
  available_years: number[]
  monthly: StatusMonth[]
}

/** GET /api/v1/partner/status/ (tek iyeniń óz mehmanxanaları). Contract: S4 */
export interface PartnerStatus {
  /** YYYY-MM-DD: iyeniń akkaunt ı jaratılǵan waqıt */
  since: string
  period: StatusPeriod
  period_range: PeriodRange
  totals: StatusFullTotals
  insights: StatusInsights
  properties: PartnerStatusProperty[]
  granularity: StatusGranularity
  series: StatusSeriesRow[]
  reconciliation: StatusReconciliation
  months: MonthComparison
  year: number
  available_years: number[]
  monthly: StatusMonth[]
}

/** GET /api/v1/partner/status/hotels/{id}/ (tek óz mehmanxana) */
export interface PartnerHotelStatus extends Omit<StatusHotelDetail, 'hotel'> {
  hotel: { id: number; name: string; status: string; address: string; city: string; region: string; country: string }
  rank: StatusRank | null
  reviews: ReviewSummary
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
  /** Telefonnıń tek sońǵı 4 sanı */
  /** Tolıq nomer, sonda mehmanxana keshikken mehmanǵa qońıraw ete aladı; tek búgin hám erteńgi keliwlerde */
  phone: string
  /** Mehmanxanada naqd: mehmann qashan keletuǵının aytqan ('HH:MM'); eski bronlarda null */
  expected_arrival_time: string | null
  /** Mehmanxana mehmandı kelgen dep belgilegen waqıt */
  arrived_at: string | null
}

export interface PartnerArrivalsPage {
  count: number
  next: string | null
  previous: string | null
  results: PartnerArrival[]
  day: ArrivalsDay
  date: string
}

export type ExportFormat = 'csv' | 'xlsx'

export interface CsvFile {
  blob: Blob
  filename: string
}

export interface StatusPeriodParams {
  period: StatusPeriod
  /** YYYY-MM-DD; tek "custom" dáwir menen jiberiledi */
  from?: string
  to?: string
  granularity?: StatusGranularity
}

export interface StatusListParams extends StatusPeriodParams {
  search?: string
  /** Attıń birinshi háripi (yamasa '#'): tek mehmanxanalar hám mehmanlar dizimleri qabıllaydı */
  letter?: string
  page?: number
}

export interface AdminHotelsParams extends StatusListParams {
  /** revenue | bookings | guests | nights | rating | created_at, kemeyiw ushın "-" prefiksi */
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
  /** Sátsiz juwaptıń HTTP statusı, mısalı basqa iyeniń mehmanxanası ushın 404 */
  status?: number
}

// Getterler: tekst qátelik bolǵanda, bet sol waqıtta qaysı tilde bolsa sol tilde tańlanadı
const ERROR_MESSAGES = {
  get 401() { return translateNow('apiError.authRequired') },
  get 403() { return translateNow('apiError.adminRequired') },
  404: 'Not found',
}
const PARTNER_ERROR_MESSAGES = {
  get 401() { return translateNow('apiError.authRequired') },
  403: 'Hotel owner role required',
  404: 'Not found',
}

function query(params: Record<string, string | number | undefined>): string {
  const search = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== '') search.append(key, String(value))
  })
  const text = search.toString()
  return text ? `?${text}` : ''
}

type QueryValues = Record<string, string | number | undefined>

/** Iyeniń bronlar ekranı filterleri; eksport sol filterlerdi alıp júredi */
export interface PartnerBookingsExportFilters {
  status?: string
  paymentStatus?: string
  reportableOnly?: boolean
}

/** from hám to tek custom dáwirge tiyisli; basqa dáwirler olardı itibarǵa almaydı */
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
    return { response: null, error: error instanceof Error ? error.message : translateNow('apiError.networkOccurred') }
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
    return { data: null, error: parseError instanceof Error ? parseError.message : translateNow('apiError.networkOccurred') }
  }
}

function filenameFrom(response: Response, fallback: string): string {
  const match = /filename="?([^";]+)"?/.exec(response.headers.get('Content-Disposition') ?? '')
  return match ? match[1] : fallback
}

/**
 * CSV hám Excel apiFetch arqalı ótedi (session cookie + CSRF) hám blob retinde qaytadı; ápiwayı silteme auth header lerin alıp
 * júrmeydi
 */
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
    return { data: null, error: readError instanceof Error ? readError.message : translateNow('apiError.networkOccurred') }
  }
}

const listValues = ({ search, letter, page, ...period }: StatusListParams): QueryValues =>
  ({ ...periodValues(period), search, letter, page })

const listQuery = (params: StatusListParams) => query(listValues(params))

const hotelsValues = ({ ordering, pageSize, country, region, status, ...list }: AdminHotelsParams): QueryValues =>
  ({ ...listValues(list), ordering, page_size: pageSize, country, region, status })

const detailQuery = ({ year, ...period }: StatusDetailParams) => query({ ...periodValues(period), year })

/** Eksport pútkil dizimdi qaplaydı, sol sebepli hesh qashan betti alıp júrmeydi */
const exportValues = (values: QueryValues, format: ExportFormat): QueryValues =>
  ({ ...values, page: undefined, export: format })

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

  exportAdminHotels(params: AdminHotelsParams, format: ExportFormat = 'csv') {
    return requestCsv(`${STATUS_URL}/hotels/${query(exportValues(hotelsValues(params), format))}`, `status_hotels.${format}`)
  },

  getHotelDetail(hotelId: number, params: StatusDetailParams) {
    return request<StatusHotelDetail>(`${STATUS_URL}/hotels/${hotelId}/${detailQuery(params)}`)
  },

  getUsers(params: StatusListParams) {
    return request<StatusPage<StatusUser>>(`${STATUS_URL}/users/${listQuery(params)}`)
  },

  exportUsers(params: StatusListParams, format: ExportFormat = 'csv') {
    return requestCsv(`${STATUS_URL}/users/${query(exportValues(listValues(params), format))}`, `status_users.${format}`)
  },

  getUserDetail(userId: number, { page, ...period }: UserDetailParams) {
    return request<StatusUserDetail>(`${STATUS_URL}/users/${userId}/${query({ ...periodValues(period), page })}`)
  },

  exportUserHistory(userId: number, period: StatusPeriodParams, format: ExportFormat = 'csv') {
    return requestCsv(
      `${STATUS_URL}/users/${userId}/${query({ ...periodValues(period), export: format })}`,
      `status_user_${userId}_history.${format}`)
  },

  getAdminOverview(params: StatusPeriodParams & { year?: number }) {
    const { year, ...period } = params
    return request<AdminOverview>(`${STATUS_URL}/overview/${query({ ...periodValues(period), year })}`, { method: 'GET' }, ERROR_MESSAGES)
  },

  getPartnerStatus(params: StatusDetailParams) {
    return request<PartnerStatus>(`${PARTNER_URL}/${detailQuery(params)}`, { method: 'GET' }, PARTNER_ERROR_MESSAGES)
  },

  exportPartnerBookings(filters: PartnerBookingsExportFilters, format: ExportFormat = 'csv') {
    const { status, paymentStatus, reportableOnly } = filters
    return requestCsv(
      `${API_BASE_URL}/api/v1/partner/bookings/${query({
        status, payment_status: paymentStatus, reportable: reportableOnly ? 'true' : undefined, export: format })}`,
      `partner_bookings.${format}`, PARTNER_ERROR_MESSAGES)
  },

  exportPartnerReconciliation(period: StatusPeriodParams, format: ExportFormat = 'csv') {
    return requestCsv(
      `${PARTNER_URL}/${query({ ...periodValues(period), export: format })}`,
      `partner_reconciliation.${format}`, PARTNER_ERROR_MESSAGES)
  },

  getPartnerHotel(hotelId: number, params: StatusDetailParams) {
    return request<PartnerHotelStatus>(
      `${PARTNER_URL}/hotels/${hotelId}/${detailQuery(params)}`, { method: 'GET' }, PARTNER_ERROR_MESSAGES)
  },

  getPartnerRooms(params: StatusPeriodParams & { property?: number }) {
    const { property, ...period } = params
    return request<PartnerRoomsStatus>(
      `${PARTNER_URL}/rooms/${query({ ...periodValues(period), property })}`, { method: 'GET' }, PARTNER_ERROR_MESSAGES)
  },

  getPartnerArrivals({ day, property, page }: { day?: ArrivalsDay; property?: number; page?: number }) {
    return request<PartnerArrivalsPage>(
      `${PARTNER_URL}/arrivals/${query({ day, property, page })}`, { method: 'GET' }, PARTNER_ERROR_MESSAGES)
  },

  /** Admin mehmanxananıń mámleketin hám regionın id boyınsha belgileydi (ekewi null bolsa tazalanadı: "Unspecified"). */
  setPropertyLocation(propertyId: number, location: { country_ref: number | null; region_ref: number | null }) {
    return request<{ id: number; country_ref: number | null; region_ref: number | null }>(
      `${API_BASE_URL}/api/v1/admin-panel/properties/${propertyId}/region/`,
      { method: 'PATCH', body: JSON.stringify(location) },
    )
  },
}
