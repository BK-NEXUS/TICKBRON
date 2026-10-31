// Admin API adapter for admin moderation and management
// Integrates with backend admin endpoints from Checkpoint 18

import { parseApiError } from '../utils/errorHandler'
import { apiFetch, fetchAllPages } from '../utils/api'
import { translateNow } from '../i18n/translateNow'
import { API_BASE_URL } from '../utils/apiBase'
import type { CommissionOwnerPage, CommissionOwnerRow, CommissionStatement } from './commissionTypes'

// Admin Property types from backend contract
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
  city_ref?: number | null
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

// Admin User types from backend contract
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
  /** Where the owner's hotels will appear (Geography ids) */
  country_ref: number
  region_ref: number
  city_ref: number
  /** What the site takes from each booking of this owner, "0" to "100" */
  commission_percent: string
}

/** The body of a new administrator: no place and no commission; `role` is the only thing that sets the rights */
export type CreateAdminRequest = Omit<CreateHotelOwnerRequest, 'country_ref' | 'region_ref' | 'city_ref' | 'commission_percent'> & {
  role: 'staff' | 'super_admin'
}

/** A new phone number and/or e-mail for an account (PATCH /api/v1/admin-panel/users/{id}/contact/) */
export interface ContactChange {
  email?: string
  phone_number?: string
}

export type ReviewStatus = 'pending' | 'approved' | 'rejected'

/** A guest review for the staff: the reviewer's address is shown here and nowhere public */
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

// Admin Amenity types from backend contract
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

// Admin Amenity Category types from backend contract
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

// Admin Customer types from backend contract (Checkpoint 24)
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
  page?: number
  page_size?: number
  sort_by?: string
  sort_order?: 'asc' | 'desc'
}

// Admin Customer Profile types from backend contract (Checkpoint 25)
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

// Admin Statistics types from backend contract (Checkpoint 26)
export interface RegistrationStatistics {
  type: 'rolling_12_months' | 'calendar_year'
  data: Array<{
    period: string
    count: number
  }>
}

// Backend responses (admin_panel/views.py); the adapter maps them to the shapes above
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

// Admin Support Lookup types from backend contract (Checkpoint 23)
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
  /** First booking item's room type and rate plan; null when the booking has no items */
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

// API Response types
export interface ApiResponse<T> {
  data: T | null
  error: string | null
}

export interface ApprovePropertyResult extends ApiResponse<AdminProperty> {
  /** Parts a hotel still lacks (room, rate, photo) when approval is refused */
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

  /** GET a paginated list endpoint and return the items of every page */
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

      // Handle 204 No Content (DELETE operations)
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

  // Guest review moderation

  /** One page of reviews by status (pending is the default on the server), as the staff sees them */
  async getReviews(status: ReviewStatus, page = 1): Promise<ApiResponse<AdminReviewsPage>> {
    const { data, error } = await this.request<{ count: number; next: string | null; results: AdminReview[] }>(
      `/api/v1/admin-panel/reviews/?status=${status}&page=${page}`)
    return data
      ? { data: { count: data.count, hasMore: Boolean(data.next), results: data.results }, error: null }
      : { data: null, error }
  }

  /** Approve (shown on the hotel page, counted in its scores) or reject a review */
  async decideReview(id: number, decision: 'approve' | 'reject'): Promise<ApiResponse<AdminReview>> {
    const { data, error } = await this.request<AdminReview>(`/api/v1/admin-panel/reviews/${id}/${decision}/`, { method: 'POST' })
    return { data, error }
  }

  // Admin Property Moderation Methods

  /**
   * List all properties for moderation
   * Integrates with GET /api/v1/admin-panel/properties/ endpoint
   */
  async getProperties(): Promise<ApiResponse<AdminProperty[]>> {
    return this.requestAll<AdminProperty>('/api/v1/admin-panel/properties/')
  }

  /**
   * Approve or reject property
   * Integrates with POST /api/v1/admin-panel/properties/{id}/approve/ endpoint
   */
  async approveProperty(id: number, requestData: ApprovePropertyRequest): Promise<ApprovePropertyResult> {
    const { data, error, errorBody } = await this.request<AdminProperty>(`/api/v1/admin-panel/properties/${id}/approve/`, {
      method: 'POST',
      body: JSON.stringify(requestData),
    })
    return { data, error, missing: missingParts(errorBody) }
  }

  /**
   * Suspend property
   * Integrates with POST /api/v1/admin-panel/properties/{id}/suspend/ endpoint
   */
  async suspendProperty(id: number): Promise<ApiResponse<AdminProperty>> {
    return this.request<AdminProperty>(`/api/v1/admin-panel/properties/${id}/suspend/`, {
      method: 'POST',
    })
  }

  // Admin User Management Methods

  /**
   * List all users for management
   * Integrates with GET /api/v1/admin-panel/users/ endpoint
   */
  async getUsers(): Promise<ApiResponse<AdminUser[]>> {
    return this.request<AdminUser[]>('/api/v1/admin-panel/users/', {
      method: 'GET',
    })
  }

  /**
   * Create hotel-owner account (super-admin only)
   * Integrates with POST /api/v1/admin-panel/users/create-hotel-owner/ endpoint
   */
  async createHotelOwner(ownerData: CreateHotelOwnerRequest): Promise<ApiResponse<CreateHotelOwnerResponse>> {
    return this.request<CreateHotelOwnerResponse>('/api/v1/admin-panel/users/create-hotel-owner/', {
      method: 'POST',
      body: JSON.stringify(ownerData),
    })
  }

  /**
   * Add another administrator (super-admin only; the account is staff, never a super-admin)
   * Integrates with POST /api/v1/admin-panel/users/create-admin/ endpoint
   */
  async createAdmin(adminData: CreateAdminRequest): Promise<ApiResponse<CreateHotelOwnerResponse>> {
    return this.request<CreateHotelOwnerResponse>('/api/v1/admin-panel/users/create-admin/', {
      method: 'POST',
      body: JSON.stringify(adminData),
    })
  }

  /**
   * Reset another account's two-step sign-in after a lost phone (super-admin only).
   * `code` is the super admin's OWN current app code. Integrates with POST /api/v1/admin-panel/users/{id}/2fa-reset/
   */
  async resetTwoFactor(userId: number, code: string): Promise<ApiResponse<AdminUser>> {
    return this.request<AdminUser>(`/api/v1/admin-panel/users/${userId}/2fa-reset/`, {
      method: 'POST',
      body: JSON.stringify({ code }),
    })
  }

  /**
   * Change the phone number and/or e-mail of an account (super admin or staff; staff only for guests and owners).
   * Integrates with PATCH /api/v1/admin-panel/users/{id}/contact/
   */
  async changeContact(userId: number, change: ContactChange): Promise<ApiResponse<AdminUser>> {
    return this.request<AdminUser>(`/api/v1/admin-panel/users/${userId}/contact/`, {
      method: 'PATCH',
      body: JSON.stringify(change),
    })
  }

  // Commission

  /** GET /api/v1/admin-panel/commission/: hotel owners with percent, this month and unpaid commission */
  async getCommissionOwners({ search, page = 1 }: { search?: string; page?: number } = {}): Promise<ApiResponse<CommissionOwnerPage>> {
    const params = new URLSearchParams({ page: String(page) })
    if (search) params.set('search', search)
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

  /** PUT .../commission/{ownerId}/rate/ (super admin): the percent from this month on */
  async setCommissionPercent(ownerId: number, percent: string): Promise<ApiResponse<CommissionStatement>> {
    return this.request<CommissionStatement>(`/api/v1/admin-panel/commission/${ownerId}/rate/`, {
      method: 'PUT',
      body: JSON.stringify({ percent }),
    })
  }

  /** POST .../commission/{ownerId}/months/{YYYY-MM}/paid/: the owner paid that ended month */
  async confirmCommissionMonth(ownerId: number, month: string): Promise<ApiResponse<CommissionStatement>> {
    return this.request<CommissionStatement>(`/api/v1/admin-panel/commission/${ownerId}/months/${month}/paid/`, { method: 'POST' })
  }

  /** DELETE on the same URL: take the confirmation back */
  async undoCommissionMonth(ownerId: number, month: string): Promise<ApiResponse<CommissionStatement>> {
    return this.request<CommissionStatement>(`/api/v1/admin-panel/commission/${ownerId}/months/${month}/paid/`, { method: 'DELETE' })
  }

  // Admin Amenity Management Methods

  /**
   * List all amenities
   * Integrates with GET /api/v1/admin-panel/amenities/ endpoint
   */
  async getAmenities(): Promise<ApiResponse<AdminAmenity[]>> {
    return this.requestAll<AdminAmenity>('/api/v1/admin-panel/amenities/')
  }

  /**
   * Create amenity
   * Integrates with POST /api/v1/admin-panel/amenities/ endpoint
   */
  async createAmenity(amenityData: CreateAmenityRequest): Promise<ApiResponse<AdminAmenity>> {
    return this.request<AdminAmenity>('/api/v1/admin-panel/amenities/', {
      method: 'POST',
      body: JSON.stringify(amenityData),
    })
  }

  /**
   * Update amenity
   * Integrates with PATCH /api/v1/admin-panel/amenities/{id}/ endpoint
   */
  async updateAmenity(id: number, amenityData: UpdateAmenityRequest): Promise<ApiResponse<AdminAmenity>> {
    return this.request<AdminAmenity>(`/api/v1/admin-panel/amenities/${id}/`, {
      method: 'PATCH',
      body: JSON.stringify(amenityData),
    })
  }

  /**
   * Delete amenity (soft delete)
   * Integrates with DELETE /api/v1/admin-panel/amenities/{id}/ endpoint
   */
  async deleteAmenity(id: number): Promise<ApiResponse<null>> {
    return this.request<null>(`/api/v1/admin-panel/amenities/${id}/`, {
      method: 'DELETE',
    })
  }

  // Admin Amenity Category Management Methods

  /**
   * List amenity categories
   * Integrates with GET /api/v1/admin-panel/amenities/categories/ endpoint
   */
  async getAmenityCategories(): Promise<ApiResponse<AdminAmenityCategory[]>> {
    return this.requestAll<AdminAmenityCategory>('/api/v1/admin-panel/amenities/categories/')
  }

  /**
   * Create amenity category
   * Integrates with POST /api/v1/admin-panel/amenities/categories/ endpoint
   */
  async createAmenityCategory(categoryData: CreateAmenityCategoryRequest): Promise<ApiResponse<AdminAmenityCategory>> {
    return this.request<AdminAmenityCategory>('/api/v1/admin-panel/amenities/categories/', {
      method: 'POST',
      body: JSON.stringify(categoryData),
    })
  }

  /**
   * Update amenity category
   * Integrates with PATCH /api/v1/admin-panel/amenities/categories/{id}/ endpoint
   */
  async updateAmenityCategory(id: number, categoryData: UpdateAmenityCategoryRequest): Promise<ApiResponse<AdminAmenityCategory>> {
    return this.request<AdminAmenityCategory>(`/api/v1/admin-panel/amenities/categories/${id}/`, {
      method: 'PATCH',
      body: JSON.stringify(categoryData),
    })
  }

  /**
   * Delete amenity category (soft delete)
   * Integrates with DELETE /api/v1/admin-panel/amenities/categories/{id}/ endpoint
   */
  async deleteAmenityCategory(id: number): Promise<ApiResponse<null>> {
    return this.request<null>(`/api/v1/admin-panel/amenities/categories/${id}/`, {
      method: 'DELETE',
    })
  }

  // Admin Customers Directory Methods (Checkpoint 24)

  /**
   * List customers directory with search, pagination, and sorting
   * Integrates with GET /api/v1/admin-panel/customers/ endpoint
   */
  async getCustomers(params?: GetCustomersParams): Promise<ApiResponse<AdminCustomersResponse>> {
    const queryParams = new URLSearchParams()
    if (params?.search) queryParams.append('search', params.search)
    if (params?.page) queryParams.append('page', params.page.toString())
    if (params?.page_size) queryParams.append('page_size', params.page_size.toString())
    if (params?.sort_by) queryParams.append('sort_by', params.sort_by)
    if (params?.sort_order) queryParams.append('sort_order', params.sort_order)

    const endpoint = `/api/v1/admin-panel/customers/${queryParams.toString() ? `?${queryParams.toString()}` : ''}`
    return this.request<AdminCustomersResponse>(endpoint)
  }

  // Admin Customer Profile Methods (Checkpoint 25)

  /**
   * Get customer profile with bookings and internal notes
   * Integrates with GET /api/v1/admin-panel/customers/{id}/ endpoint
   */
  async getCustomerProfile(customerId: number, params?: GetCustomerProfileParams): Promise<ApiResponse<AdminCustomerProfile>> {
    const queryParams = new URLSearchParams()
    if (params?.booking_filter) queryParams.append('booking_filter', params.booking_filter)

    const endpoint = `/api/v1/admin-panel/customers/${customerId}/${queryParams.toString() ? `?${queryParams.toString()}` : ''}`
    return this.request<AdminCustomerProfile>(endpoint)
  }

  /**
   * Create internal note for customer
   * Integrates with POST /api/v1/admin-panel/customers/{id}/notes/ endpoint
   */
  async createInternalNote(customerId: number, noteData: CreateNoteRequest): Promise<ApiResponse<InternalNote>> {
    return this.request<InternalNote>(`/api/v1/admin-panel/customers/${customerId}/notes/`, {
      method: 'POST',
      body: JSON.stringify(noteData),
    })
  }

  /**
   * Update internal note
   * Integrates with PUT /api/v1/admin-panel/customers/{id}/notes/{note_id}/ endpoint
   */
  async updateInternalNote(customerId: number, noteId: number, noteData: UpdateNoteRequest): Promise<ApiResponse<InternalNote>> {
    return this.request<InternalNote>(`/api/v1/admin-panel/customers/${customerId}/notes/${noteId}/`, {
      method: 'PUT',
      body: JSON.stringify(noteData),
    })
  }

  /**
   * Delete internal note (soft delete)
   * Integrates with DELETE /api/v1/admin-panel/customers/{id}/notes/{note_id}/ endpoint
   */
  async deleteInternalNote(customerId: number, noteId: number): Promise<ApiResponse<null>> {
    return this.request<null>(`/api/v1/admin-panel/customers/${customerId}/notes/${noteId}/`, {
      method: 'DELETE',
    })
  }

  // Admin Statistics Methods (Checkpoint 26)

  /**
   * Get registration statistics
   * Integrates with GET /api/v1/admin-panel/statistics/registrations/ endpoint
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
   * Get top bookers leaderboard
   * Integrates with GET /api/v1/admin-panel/statistics/top-bookers/ endpoint
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

  // Admin Support Lookup Methods (Checkpoint 23)

  /**
   * Look up booking by reference code for support
   * Integrates with GET /api/v1/admin-panel/bookings/lookup/ endpoint
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

// Export singleton instance
export const adminAdapter = new AdminAdapter()

// Export class for testing
export { AdminAdapter }
