// Admin moderation hám basqarıw ushın admin API adapteri
// Checkpoint 18 degi backend admin endpoint leri menen birlesedi

import { parseApiError } from '../utils/errorHandler'
import { apiFetch, fetchAllPages } from '../utils/api'
import { translateNow } from '../i18n/translateNow'
import { API_BASE_URL } from '../utils/apiBase'
import type { CommissionOwnerPage, CommissionOwnerRow, CommissionStatement } from './commissionTypes'

// Backend contract tan Admin Property túrleri
export interface AdminProperty {
  id: number
  owner: number
  owner_name?: string
  property_type: number
  status: string
  max_guests: number
  bedrooms: number
  bathrooms: number
  address_line1: string
  address_line2?: string
  city: string
  state?: string
  postal_code?: string
  country: string
  country_ref?: number | null
  region_ref?: number | null
  latitude?: number
  longitude?: number
  base_price: number
  currency: string
  total_area?: number
  floor_number?: number
  has_elevator: boolean
  has_parking: boolean
  has_wifi: boolean
  has_ac: boolean
  has_heating: boolean
  approved_by?: number
  approved_at?: string
  rejection_reason?: string
  created_at: string
  updated_at: string
}

export interface ApprovePropertyRequest {
  rejection_reason?: string
}

// Backend contract tan Admin User túrleri
export interface AdminUser {
  id: number
  email: string
  first_name: string
  last_name: string
  full_name: string
  phone_number?: string
  is_active: boolean
  is_staff: boolean
  is_superuser: boolean
  role: string
  date_joined: string
  last_login?: string
  two_factor_enabled: boolean
}

export interface CreateHotelOwnerRequest {
  email: string
  first_name: string
  last_name: string
  phone_number: string
  password: string
  password_confirm: string
  /** Iyeniń mehmanxanaları qayerde kórinedi (Geography id leri) */
  country_ref: number
  region_ref: number
  /** Sayt usı iyeniń hár bronınan ne aladı, "0" den "100" ge shekem */
  commission_percent: string
}

/** Jańa administrator denesi: orın hám komissiya joq; huquqlardı belgilewshi jalǵız nárse `role` */
export type CreateAdminRequest = Omit<CreateHotelOwnerRequest, 'country_ref' | 'region_ref' | 'commission_percent'> & {
  role: 'staff' | 'super_admin'
}

/** Akkauntiń jańa telefon nomeri hám/yamasa e-mail ı (PATCH /api/v1/admin-panel/users/{id}/contact/) */
/** Panel dizimniń bir beti */
export interface AdminPage<T> {
  count: number
  hasMore: boolean
  results: T[]
}

export interface AdminUsersParams {
  /** Kórsetilgen attıń birinshi háripi, yamasa '#' */
  letter?: string
  search?: string
  role?: 'guest' | 'owner' | 'staff' | 'super_admin'
  page?: number
}

export interface AdminPropertiesParams {
  letter?: string
  status?: string
  search?: string
  page?: number
}

export interface ContactChange {
  email?: string
  phone_number?: string
}

export type ReviewStatus = 'pending' | 'approved' | 'rejected'

/** Staff ushın mehmann sharhı: sharh jazıwshınıń mánzili usı jerde kórsetiledi, ashıq jerde emes */
export interface AdminReview {
  id: number
  property: number
  property_name: string
  reviewer: string
  reviewer_email: string
  stay_month: string | null
  overall_rating: number
  title: string
  comment: string
  status: ReviewStatus
  created_at: string
  reviewed_at: string | null
}

export interface AdminReviewsPage {
  count: number
  hasMore: boolean
  results: AdminReview[]
}

export interface CreateHotelOwnerResponse {
  id: number
  email: string
  first_name: string
  last_name: string
  full_name: string
  phone_number?: string
  is_active: boolean
  role: string
  date_joined: string
}

// Backend contract tan Admin Amenity túrleri
export interface AdminAmenity {
  id: number
  category: number
  category_name?: string
  name: string
  slug: string
  description: string
  icon: string
  is_searchable: boolean
  sort_order: number
  created_at: string
  updated_at: string
}

export interface CreateAmenityRequest {
  category: number
  name: string
  slug: string
  description: string
  icon: string
  is_searchable: boolean
  sort_order: number
}

export interface UpdateAmenityRequest {
  category?: number
  name?: string
  slug?: string
  description?: string
  icon?: string
  is_searchable?: boolean
  sort_order?: number
}

// Backend contract tan Admin Amenity Category túrleri
export interface AdminAmenityCategory {
  id: number
  name: string
  slug: string
  description: string
  icon: string
  sort_order: number
  created_at: string
  updated_at: string
}

export interface CreateAmenityCategoryRequest {
  name: string
  slug: string
  description: string
  icon: string
  sort_order: number
}

export interface UpdateAmenityCategoryRequest {
  name?: string
  slug?: string
  description?: string
  icon?: string
  sort_order?: number
}

// Backend contract tan Admin Customer túrleri (Checkpoint 24)
export interface AdminCustomer {
  id: number
  registration_date: string
  full_name: string
  phone: string
  email: string
  whatsapp?: string
  telegram?: string
  preferred_contact_method: string
  total_booking_count: number
  last_booking_date?: string
  customer_status: string
}

export interface AdminCustomersResponse {
  count: number
  next: string | null
  previous: string | null
  results: AdminCustomer[]
}

export interface GetCustomersParams {
  search?: string
  /** Kórsetilgen attıń birinshi háripi, yamasa '#' */
  letter?: string
  page?: number
  page_size?: number
  sort_by?: string
  sort_order?: 'asc' | 'desc'
}

// Backend contract tan Admin Customer Profile túrleri (Checkpoint 25)
export interface AdminCustomerProfile {
  customer: {
    id: number
    email: string
    first_name: string
    last_name: string
    full_name: string
    phone_number: string
    whatsapp?: string
    telegram?: string
    preferred_contact_method: string
    date_joined: string
    last_login?: string
    is_active: boolean
    email_verified: boolean
  }
  bookings: Array<{
    id: number
    reference_code: string
    status: string
    payment_status: string
    check_in: string
    check_out: string
    number_of_nights: number
    total_price: number
    currency: string
    property_name: string
    property_city: string
    created_at: string
  }>
  internal_notes: Array<{
    id: number
    customer: number
    author: number
    author_name: string
    author_email: string
    note: string
    created_at: string
    updated_at: string
  }>
  last_activity?: string
}

export interface GetCustomerProfileParams {
  booking_filter?: 'all' | 'upcoming' | 'completed' | 'cancelled'
}

export interface InternalNote {
  id: number
  customer: number
  author: number
  author_name: string
  author_email: string
  note: string
  created_at: string
  updated_at: string
}

export interface CreateNoteRequest {
  note: string
}

export interface UpdateNoteRequest {
  note: string
}

// Backend contract tan Admin Statistics túrleri (Checkpoint 26)
export interface RegistrationStatistics {
  type: 'rolling_12_months' | 'calendar_year'
  data: Array<{
    period: string
    count: number
  }>
}

// Backend juwapları (admin_panel/views.py); adapter olardı joqarıdaǵı formalarǵa sáykeslestiredi
interface RegistrationStatisticsResponse {
  type: 'rolling_12_months' | 'calendar_year'
  start_date?: string
  end_date?: string
  statistics: Array<{ period: string; count: number }>
}

interface TopBookersResponse {
  period: string
  limit: number
  leaderboard: TopBooker[]
}

interface SupportLookupResponse {
  booking: {
    id: number
    reference_code: string
    status: string
    payment_status: string
    check_in: string
    check_out: string
    number_of_nights: number
    total_price: string
    currency: string
    created_at: string
    updated_at: string
    booking_items: Array<{
      room_type: { id: number; name: string }
      rate_plan: { id: number; name: string }
    }>
  }
  customer: SupportLookupBooking['customer']
  property: SupportLookupBooking['property'] & Record<string, unknown>
}

export interface GetRegistrationStatisticsParams {
  type?: 'rolling_12_months' | 'calendar_year'
}

export interface TopBooker {
  rank: number
  customer_id: number
  customer_name: string
  completed_booking_count: number
}

export interface GetTopBookersParams {
  period?: 'this_month' | 'this_year' | 'all_time'
  limit?: number
}

// Backend contract tan Admin Support Lookup túrleri (Checkpoint 23)
export interface SupportLookupBooking {
  id: number
  reference_code: string
  status: string
  payment_status: string
  check_in: string
  check_out: string
  number_of_nights: number
  total_price: number
  currency: string
  property: {
    id: number
    name: string
    city: string
    country: string
    address_line1: string
  }
  /** Birinshi bron elementiniń xona túri hám rate plan ı; bronda element joq bolsa null */
  room: {
    id: number
    name: string
    rate_plan: string
  } | null
  customer: {
    id: number
    full_name: string
    email: string
    phone_number: string
    whatsapp?: string
    telegram?: string
    preferred_contact_method: string
  }
  created_at: string
  updated_at: string
}

export interface GetSupportLookupParams {
  reference_code: string
}

// API Response túrleri
export interface ApiResponse<T> {
  data: T | null
  error: string | null
}

export interface ApprovePropertyResult extends ApiResponse<AdminProperty> {
  /** Tastıyıqlaw biykar etilgende mehmanxanada ele jetispeytuǵın bólimler (xona, baha, súwret) */
  missing?: string[]
}

function missingParts(body: unknown): string[] | undefined {
  const missing = (body as { missing?: unknown } | null)?.missing
  return Array.isArray(missing) && missing.every((part) => typeof part === 'string') ? missing : undefined
}

class AdminAdapter {
  private baseUrl: string

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl
  }

  /** Betlerge bólingen dizim endpoint ine GET hám hár bettiń elementlerin qaytarıw */
  /** Betlerge bólingen dizimniń bir beti: qatarlar, jámi neshe ekeni hám taǵı bir bet bar ma */
  private async requestPage<T>(endpoint: string, params: Record<string, string | number | undefined>): Promise<ApiResponse<AdminPage<T>>> {
    const query = new URLSearchParams()
    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined && value !== '') query.set(key, String(value))
    }
    const { data, error } = await this.request<{ count: number; next: string | null; results: T[] }>(`${endpoint}?${query.toString()}`)
    return data
      ? { data: { count: data.count, hasMore: Boolean(data.next), results: data.results }, error: null }
      : { data: null, error }
  }

  private async requestAll<T>(endpoint: string): Promise<ApiResponse<T[]>> {
    const { data, error } = await fetchAllPages<T>(`${this.baseUrl}${endpoint}`, {
      errorMessages: { 401: translateNow('apiError.authRequired'), 403: translateNow('apiError.adminRequired'), 404: translateNow('apiError.notFound') },
    })
    return { data, error }
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<{ data: T | null; error: string | null; errorBody?: unknown }> {
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
        const errorBody: unknown = await response.json().catch(() => undefined)
        const apiError = parseApiError(response, errorBody, { 401: translateNow('apiError.authRequired'), 403: translateNow('apiError.adminRequired'), 404: translateNow('apiError.notFound') })
        return { data: null, error: apiError.message, errorBody }
      }

      // 204 No Content di islew (DELETE ámelleri)
      if (response.status === 204) {
        return { data: null as T, error: null }
      }

      const data = await response.json()
      return { data, error: null }
    } catch (error) {
      return {
        data: null,
        error: error instanceof Error ? error.message : translateNow('apiError.networkOccurred'),
      }
    }
  }

  // Mehmann sharhların moderation

  /** Status boyınsha sharhlardıń bir beti (serverde ádetde pending), staff kóretuǵınday */
  async getReviews(status: ReviewStatus, page = 1): Promise<ApiResponse<AdminReviewsPage>> {
    const { data, error } = await this.request<{ count: number; next: string | null; results: AdminReview[] }>(
      `/api/v1/admin-panel/reviews/?status=${status}&page=${page}`)
    return data
      ? { data: { count: data.count, hasMore: Boolean(data.next), results: data.results }, error: null }
      : { data: null, error }
  }

  /** Sharhtı tastıyıqlaw (mehmanxana betinde kórsetiledi, bahalarına qosıladı) yamasa biykar etiw */
  async decideReview(id: number, decision: 'approve' | 'reject'): Promise<ApiResponse<AdminReview>> {
    const { data, error } = await this.request<AdminReview>(`/api/v1/admin-panel/reviews/${id}/${decision}/`, { method: 'POST' })
    return { data, error }
  }

  // Admin mehmanxana moderation metodları

  /**
   * Moderation ushın mehmanxanalardıń bir beti, eń jańası birinshi
   * GET /api/v1/admin-panel/properties/ endpoint i menen birlesedi
   */
  async getProperties({ letter, status, search, page = 1 }: AdminPropertiesParams = {}): Promise<ApiResponse<AdminPage<AdminProperty>>> {
    return this.requestPage<AdminProperty>('/api/v1/admin-panel/properties/', { letter, status, search, page })
  }

  /**
   * Mehmanxananı tastıyıqlaw yamasa biykar etiw
   * POST /api/v1/admin-panel/properties/{id}/approve/ endpoint i menen birlesedi
   */
  async approveProperty(id: number, requestData: ApprovePropertyRequest): Promise<ApprovePropertyResult> {
    const { data, error, errorBody } = await this.request<AdminProperty>(`/api/v1/admin-panel/properties/${id}/approve/`, {
      method: 'POST',
      body: JSON.stringify(requestData),
    })
    return { data, error, missing: missingParts(errorBody) }
  }

  /**
   * Mehmanxananı toqtatıw
   * POST /api/v1/admin-panel/properties/{id}/suspend/ endpoint i menen birlesedi
   */
  async suspendProperty(id: number): Promise<ApiResponse<AdminProperty>> {
    return this.request<AdminProperty>(`/api/v1/admin-panel/properties/${id}/suspend/`, {
      method: 'POST',
    })
  }

  // Admin paydalanıwshılardı basqarıw metodları

  /**
   * Paydalanıwshılardıń kórsetilgen atı alfavit tártibinde bir beti
   * GET /api/v1/admin-panel/users/ endpoint i menen birlesedi
   */
  async getUsers({ letter, search, role, page = 1 }: AdminUsersParams = {}): Promise<ApiResponse<AdminPage<AdminUser>>> {
    return this.requestPage<AdminUser>('/api/v1/admin-panel/users/', { letter, search, role, page })
  }

  /**
   * Mehmanxana iyesi akkaunt ın jaratıw (tek super-admin)
   * POST /api/v1/admin-panel/users/create-hotel-owner/ endpoint i menen birlesedi
   */
  async createHotelOwner(ownerData: CreateHotelOwnerRequest): Promise<ApiResponse<CreateHotelOwnerResponse>> {
    return this.request<CreateHotelOwnerResponse>('/api/v1/admin-panel/users/create-hotel-owner/', {
      method: 'POST',
      body: JSON.stringify(ownerData),
    })
  }

  /**
   * Basqa administrator qosıw (tek super-admin; akkaunt staff, hesh qashan super-admin emes)
   * POST /api/v1/admin-panel/users/create-admin/ endpoint i menen birlesedi
   */
  async createAdmin(adminData: CreateAdminRequest): Promise<ApiResponse<CreateHotelOwnerResponse>> {
    return this.request<CreateHotelOwnerResponse>('/api/v1/admin-panel/users/create-admin/', {
      method: 'POST',
      body: JSON.stringify(adminData),
    })
  }

  /**
   * Telefon joǵalǵannan keyin basqa akkauntıń eki basqıshlı kirisiwin qayta ornatıw (tek super-admin).
   * `code` super admin niń ÓZ házirgi ilova kodı. POST /api/v1/admin-panel/users/{id}/2fa-reset/ penen birlesedi
   */
  async resetTwoFactor(userId: number, code: string): Promise<ApiResponse<AdminUser>> {
    return this.request<AdminUser>(`/api/v1/admin-panel/users/${userId}/2fa-reset/`, {
      method: 'POST',
      body: JSON.stringify({ code }),
    })
  }

  /**
   * Akkauntıń telefon nomerin hám/yamasa e-mail ın ózgertiw (super admin yamasa staff; staff tek mehmanlar hám iyeler ushın).
   * PATCH /api/v1/admin-panel/users/{id}/contact/ penen birlesedi
   */
  async changeContact(userId: number, change: ContactChange): Promise<ApiResponse<AdminUser>> {
    return this.request<AdminUser>(`/api/v1/admin-panel/users/${userId}/contact/`, {
      method: 'PATCH',
      body: JSON.stringify(change),
    })
  }

  // Komissiya

  /** GET /api/v1/admin-panel/commission/: procenti, usı ayı hám tólenbegen komissiyası menen mehmanxana iyeleri */
  async getCommissionOwners({ search, letter, page = 1 }: { search?: string; letter?: string; page?: number } = {}): Promise<ApiResponse<CommissionOwnerPage>> {
    const params = new URLSearchParams({ page: String(page) })
    if (search) params.set('search', search)
    if (letter) params.set('letter', letter)
    const { data, error } = await this.request<{ count: number; next: string | null; results: CommissionOwnerRow[] }>(
      `/api/v1/admin-panel/commission/?${params.toString()}`)
    return data
      ? { data: { count: data.count, hasMore: Boolean(data.next), results: data.results }, error: null }
      : { data: null, error }
  }

  /** GET /api/v1/admin-panel/commission/{ownerId}/ */
  async getCommissionStatement(ownerId: number): Promise<ApiResponse<CommissionStatement>> {
    return this.request<CommissionStatement>(`/api/v1/admin-panel/commission/${ownerId}/`)
  }

  /** PUT .../commission/{ownerId}/rate/ (super admin): usı aydan baslap procent */
  async setCommissionPercent(ownerId: number, percent: string): Promise<ApiResponse<CommissionStatement>> {
    return this.request<CommissionStatement>(`/api/v1/admin-panel/commission/${ownerId}/rate/`, {
      method: 'PUT',
      body: JSON.stringify({ percent }),
    })
  }

  /** POST .../commission/{ownerId}/months/{YYYY-MM}/paid/: iye sol pitken ayın tóledi */
  async confirmCommissionMonth(ownerId: number, month: string): Promise<ApiResponse<CommissionStatement>> {
    return this.request<CommissionStatement>(`/api/v1/admin-panel/commission/${ownerId}/months/${month}/paid/`, { method: 'POST' })
  }

  /** Sol URL ge DELETE: tastıyıqlawdı qaytarıp alıw */
  async undoCommissionMonth(ownerId: number, month: string): Promise<ApiResponse<CommissionStatement>> {
    return this.request<CommissionStatement>(`/api/v1/admin-panel/commission/${ownerId}/months/${month}/paid/`, { method: 'DELETE' })
  }

  // Admin amenity di basqarıw metodları

  /**
   * Barlıq amenity lerdi dizimlew
   * GET /api/v1/admin-panel/amenities/ endpoint i menen birlesedi
   */
  async getAmenities(): Promise<ApiResponse<AdminAmenity[]>> {
    return this.requestAll<AdminAmenity>('/api/v1/admin-panel/amenities/')
  }

  /**
   * Amenity jaratıw
   * POST /api/v1/admin-panel/amenities/ endpoint i menen birlesedi
   */
  async createAmenity(amenityData: CreateAmenityRequest): Promise<ApiResponse<AdminAmenity>> {
    return this.request<AdminAmenity>('/api/v1/admin-panel/amenities/', {
      method: 'POST',
      body: JSON.stringify(amenityData),
    })
  }

  /**
   * Amenity di jańalaw
   * PATCH /api/v1/admin-panel/amenities/{id}/ endpoint i menen birlesedi
   */
  async updateAmenity(id: number, amenityData: UpdateAmenityRequest): Promise<ApiResponse<AdminAmenity>> {
    return this.request<AdminAmenity>(`/api/v1/admin-panel/amenities/${id}/`, {
      method: 'PATCH',
      body: JSON.stringify(amenityData),
    })
  }

  /**
   * Amenity di óshiriw (soft delete)
   * DELETE /api/v1/admin-panel/amenities/{id}/ endpoint i menen birlesedi
   */
  async deleteAmenity(id: number): Promise<ApiResponse<null>> {
    return this.request<null>(`/api/v1/admin-panel/amenities/${id}/`, {
      method: 'DELETE',
    })
  }

  // Admin amenity kategoriyasın basqarıw metodları

  /**
   * Amenity kategoriyaların dizimlew
   * GET /api/v1/admin-panel/amenities/categories/ endpoint i menen birlesedi
   */
  async getAmenityCategories(): Promise<ApiResponse<AdminAmenityCategory[]>> {
    return this.requestAll<AdminAmenityCategory>('/api/v1/admin-panel/amenities/categories/')
  }

  /**
   * Amenity kategoriyası jaratıw
   * POST /api/v1/admin-panel/amenities/categories/ endpoint i menen birlesedi
   */
  async createAmenityCategory(categoryData: CreateAmenityCategoryRequest): Promise<ApiResponse<AdminAmenityCategory>> {
    return this.request<AdminAmenityCategory>('/api/v1/admin-panel/amenities/categories/', {
      method: 'POST',
      body: JSON.stringify(categoryData),
    })
  }

  /**
   * Amenity kategoriyasın jańalaw
   * PATCH /api/v1/admin-panel/amenities/categories/{id}/ endpoint i menen birlesedi
   */
  async updateAmenityCategory(id: number, categoryData: UpdateAmenityCategoryRequest): Promise<ApiResponse<AdminAmenityCategory>> {
    return this.request<AdminAmenityCategory>(`/api/v1/admin-panel/amenities/categories/${id}/`, {
      method: 'PATCH',
      body: JSON.stringify(categoryData),
    })
  }

  /**
   * Amenity kategoriyasın óshiriw (soft delete)
   * DELETE /api/v1/admin-panel/amenities/categories/{id}/ endpoint i menen birlesedi
   */
  async deleteAmenityCategory(id: number): Promise<ApiResponse<null>> {
    return this.request<null>(`/api/v1/admin-panel/amenities/categories/${id}/`, {
      method: 'DELETE',
    })
  }

  // Admin mijozlar dizimi metodları (Checkpoint 24)

  /**
   * Izlew, betlew hám tártiplew menen mijozlar dizimin dizimlew
   * GET /api/v1/admin-panel/customers/ endpoint i menen birlesedi
   */
  async getCustomers(params?: GetCustomersParams): Promise<ApiResponse<AdminCustomersResponse>> {
    const queryParams = new URLSearchParams()
    if (params?.search) queryParams.append('search', params.search)
    if (params?.letter) queryParams.append('letter', params.letter)
    if (params?.page) queryParams.append('page', params.page.toString())
    if (params?.page_size) queryParams.append('page_size', params.page_size.toString())
    if (params?.sort_by) queryParams.append('sort_by', params.sort_by)
    if (params?.sort_order) queryParams.append('sort_order', params.sort_order)

    const endpoint = `/api/v1/admin-panel/customers/${queryParams.toString() ? `?${queryParams.toString()}` : ''}`
    return this.request<AdminCustomersResponse>(endpoint)
  }

  // Admin mijoz profili metodları (Checkpoint 25)

  /**
   * Bronlar hám ishki jazbalar menen mijoz profilin alıw
   * GET /api/v1/admin-panel/customers/{id}/ endpoint i menen birlesedi
   */
  async getCustomerProfile(customerId: number, params?: GetCustomerProfileParams): Promise<ApiResponse<AdminCustomerProfile>> {
    const queryParams = new URLSearchParams()
    if (params?.booking_filter) queryParams.append('booking_filter', params.booking_filter)

    const endpoint = `/api/v1/admin-panel/customers/${customerId}/${queryParams.toString() ? `?${queryParams.toString()}` : ''}`
    return this.request<AdminCustomerProfile>(endpoint)
  }

  /**
   * Mijoz ushın ishki jazba jaratıw
   * POST /api/v1/admin-panel/customers/{id}/notes/ endpoint i menen birlesedi
   */
  async createInternalNote(customerId: number, noteData: CreateNoteRequest): Promise<ApiResponse<InternalNote>> {
    return this.request<InternalNote>(`/api/v1/admin-panel/customers/${customerId}/notes/`, {
      method: 'POST',
      body: JSON.stringify(noteData),
    })
  }

  /**
   * Ishki jazbanı jańalaw
   * PUT /api/v1/admin-panel/customers/{id}/notes/{note_id}/ endpoint i menen birlesedi
   */
  async updateInternalNote(customerId: number, noteId: number, noteData: UpdateNoteRequest): Promise<ApiResponse<InternalNote>> {
    return this.request<InternalNote>(`/api/v1/admin-panel/customers/${customerId}/notes/${noteId}/`, {
      method: 'PUT',
      body: JSON.stringify(noteData),
    })
  }

  /**
   * Ishki jazbanı óshiriw (soft delete)
   * DELETE /api/v1/admin-panel/customers/{id}/notes/{note_id}/ endpoint i menen birlesedi
   */
  async deleteInternalNote(customerId: number, noteId: number): Promise<ApiResponse<null>> {
    return this.request<null>(`/api/v1/admin-panel/customers/${customerId}/notes/${noteId}/`, {
      method: 'DELETE',
    })
  }

  // Admin statistika metodları (Checkpoint 26)

  /**
   * Dizimnen ótiw statistikasın alıw
   * GET /api/v1/admin-panel/statistics/registrations/ endpoint i menen birlesedi
   */
  async getRegistrationStatistics(params?: GetRegistrationStatisticsParams): Promise<ApiResponse<RegistrationStatistics>> {
    const queryParams = new URLSearchParams()
    if (params?.type) queryParams.append('type', params.type)

    const endpoint = `/api/v1/admin-panel/statistics/registrations/${queryParams.toString() ? `?${queryParams.toString()}` : ''}`
    const { data, error } = await this.request<RegistrationStatisticsResponse>(endpoint)
    if (!data) return { data: null, error }
    return { data: { type: data.type, data: data.statistics }, error: null }
  }

  /**
   * Eń kóp bronlaǵan mijozlar reytingin alıw
   * GET /api/v1/admin-panel/statistics/top-bookers/ endpoint i menen birlesedi
   */
  async getTopBookers(params?: GetTopBookersParams): Promise<ApiResponse<TopBooker[]>> {
    const queryParams = new URLSearchParams()
    if (params?.period) queryParams.append('period', params.period)
    if (params?.limit) queryParams.append('limit', params.limit.toString())

    const endpoint = `/api/v1/admin-panel/statistics/top-bookers/${queryParams.toString() ? `?${queryParams.toString()}` : ''}`
    const { data, error } = await this.request<TopBookersResponse>(endpoint)
    if (!data) return { data: null, error }
    return { data: data.leaderboard, error: null }
  }

  // Admin Support Lookup metodları (Checkpoint 23)

  /**
   * Qollap-quwatlaw ushın bronnı reference code boyınsha izlew
   * GET /api/v1/admin-panel/bookings/lookup/ endpoint i menen birlesedi
   */
  async lookupBookingByReferenceCode(params: GetSupportLookupParams): Promise<ApiResponse<SupportLookupBooking>> {
    const queryParams = new URLSearchParams()
    queryParams.append('reference_code', params.reference_code)

    const endpoint = `/api/v1/admin-panel/bookings/lookup/?${queryParams.toString()}`
    const { data, error } = await this.request<SupportLookupResponse>(endpoint)
    if (!data) return { data: null, error }

    const { booking, customer, property } = data
    const firstItem = booking.booking_items[0]
    return {
      data: {
        id: booking.id,
        reference_code: booking.reference_code,
        status: booking.status,
        payment_status: booking.payment_status,
        check_in: booking.check_in,
        check_out: booking.check_out,
        number_of_nights: booking.number_of_nights,
        total_price: Number(booking.total_price),
        currency: booking.currency,
        property: {
          id: property.id,
          name: property.name,
          city: property.city,
          country: property.country,
          address_line1: property.address_line1,
        },
        room: firstItem
          ? { id: firstItem.room_type.id, name: firstItem.room_type.name, rate_plan: firstItem.rate_plan.name }
          : null,
        customer,
        created_at: booking.created_at,
        updated_at: booking.updated_at,
      },
      error: null,
    }
  }
}

// Singleton nusqasın eksport etiw
export const adminAdapter = new AdminAdapter()

// Testlew ushın klasstı eksport etiw
export { AdminAdapter }
