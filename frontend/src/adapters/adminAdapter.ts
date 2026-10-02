// Admin API adapter for admin moderation and management
// Integrates with backend admin endpoints from Checkpoint 18

import { readApiError } from '../utils/errorHandler'
import { apiFetch, fetchAllPages } from '../utils/api'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

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
}

export interface CreateHotelOwnerRequest {
  email: string
  first_name: string
  last_name: string
  phone_number?: string
  password: string
  password_confirm: string
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

// Admin Payment Transaction types from backend contract
export interface AdminPaymentTransaction {
  id: number
  booking: number
  provider: string
  amount: number
  currency: string
  status: string
  payment_method_token?: string
  client_ip?: string
  user_agent?: string
  provider_response?: string
  created_at: string
  updated_at: string
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
  total_amount_paid: number
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
    phone_verified: boolean
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
  payments: Array<{
    id: number
    booking_id: number
    provider: string
    amount: number
    currency: string
    status: string
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

// Admin Geography types (G5-G6)
export interface GeographyCountry {
  id: number
  code: string // ISO2 code
  name_en: string
  name_uz: string
  name_ru: string
  currency: string
  is_active: boolean
  sort_order: number
  hotel_count?: number
  regions?: GeographyRegion[]
  created_at: string
  updated_at: string
}

export interface GeographyRegion {
  id: number
  country: number
  country_code?: string
  name_en: string
  name_uz: string
  name_ru: string
  slug: string
  is_active: boolean
  sort_order: number
  hotel_count?: number
  cities?: GeographyCity[]
  created_at: string
  updated_at: string
}

export interface GeographyCity {
  id: number
  region: number
  region_id?: number
  name_en: string
  name_uz: string
  name_ru: string
  slug: string
  is_active: boolean
  sort_order: number
  hotel_count?: number
  created_at: string
  updated_at: string
}

// Admin Geography CRUD request types
export interface CreateGeographyCountryRequest {
  code: string
  name_en: string
  name_uz: string
  name_ru: string
  currency: string
  is_active?: boolean
  sort_order?: number
}

export interface UpdateGeographyCountryRequest {
  name_en?: string
  name_uz?: string
  name_ru?: string
  currency?: string
  is_active?: boolean
  sort_order?: number
}

export interface CreateGeographyRegionRequest {
  country: number
  name_en: string
  name_uz: string
  name_ru: string
  slug?: string
  is_active?: boolean
  sort_order?: number
}

export interface UpdateGeographyRegionRequest {
  name_en?: string
  name_uz?: string
  name_ru?: string
  slug?: string
  is_active?: boolean
  sort_order?: number
}

export interface CreateGeographyCityRequest {
  region: number
  name_en: string
  name_uz: string
  name_ru: string
  slug?: string
  is_active?: boolean
  sort_order?: number
}

export interface UpdateGeographyCityRequest {
  name_en?: string
  name_uz?: string
  name_ru?: string
  slug?: string
  is_active?: boolean
  sort_order?: number
}

// Reorder request type
export interface ReorderGeographyRequest {
  items: Array<{ id: number; sort_order: number }>
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

class AdminAdapter {
  private baseUrl: string

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl
  }

  /** GET a paginated list endpoint and return the items of every page */
  private async requestAll<T>(endpoint: string): Promise<ApiResponse<T[]>> {
    const { data, error } = await fetchAllPages<T>(`${this.baseUrl}${endpoint}`, {
      errorMessages: { 401: 'Authentication required', 403: 'Admin or staff role required', 404: 'Resource not found' },
    })
    return { data, error }
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
        const apiError = await readApiError(response, { 401: 'Authentication required', 403: 'Admin or staff role required', 404: 'Resource not found' })
        return { data: null, error: apiError.message }
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
        error: error instanceof Error ? error.message : 'Network error occurred',
      }
    }
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
  async approveProperty(id: number, requestData: ApprovePropertyRequest): Promise<ApiResponse<AdminProperty>> {
    return this.request<AdminProperty>(`/api/v1/admin-panel/properties/${id}/approve/`, {
      method: 'POST',
      body: JSON.stringify(requestData),
    })
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

  // Admin Payment Monitoring Methods

  /**
   * List payment transactions for monitoring
   * Integrates with GET /api/v1/admin-panel/payments/transactions/ endpoint
   */
  async getPaymentTransactions(status?: string, provider?: string): Promise<ApiResponse<AdminPaymentTransaction[]>> {
    const params = new URLSearchParams()
    if (status) params.append('status', status)
    if (provider) params.append('provider', provider)

    const endpoint = `/api/v1/admin-panel/payments/transactions/${params.toString() ? `?${params.toString()}` : ''}`
    return this.request<AdminPaymentTransaction[]>(endpoint)
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
   * Get customer profile with bookings, payments, and internal notes
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

  // Admin Geography Methods (G5-G6)

  /**
   * List all countries with regions and cities (tree structure)
   * Integrates with GET /api/v1/admin-panel/geography/countries/ endpoint
   */
  async getGeographyTree(): Promise<ApiResponse<GeographyCountry[]>> {
    return this.request<GeographyCountry[]>('/api/v1/admin-panel/geography/countries/', {
      method: 'GET',
    })
  }

  /**
   * Get a single country by code
   * Integrates with GET /api/v1/admin-panel/geography/countries/{code}/ endpoint
   */
  async getCountry(code: string): Promise<ApiResponse<GeographyCountry>> {
    return this.request<GeographyCountry>(`/api/v1/admin-panel/geography/countries/${code}/`, {
      method: 'GET',
    })
  }

  /**
   * Create a new country
   * Integrates with POST /api/v1/admin-panel/geography/countries/ endpoint
   */
  async createCountry(countryData: CreateGeographyCountryRequest): Promise<ApiResponse<GeographyCountry>> {
    return this.request<GeographyCountry>('/api/v1/admin-panel/geography/countries/', {
      method: 'POST',
      body: JSON.stringify(countryData),
    })
  }

  /**
   * Update a country
   * Integrates with PATCH /api/v1/admin-panel/geography/countries/{code}/ endpoint
   */
  async updateCountry(code: string, countryData: UpdateGeographyCountryRequest): Promise<ApiResponse<GeographyCountry>> {
    return this.request<GeographyCountry>(`/api/v1/admin-panel/geography/countries/${code}/`, {
      method: 'PATCH',
      body: JSON.stringify(countryData),
    })
  }

  /**
   * Delete (hide) a country
   * Integrates with DELETE /api/v1/admin-panel/geography/countries/{code}/ endpoint
   */
  async deleteCountry(code: string): Promise<ApiResponse<null>> {
    return this.request<null>(`/api/v1/admin-panel/geography/countries/${code}/`, {
      method: 'DELETE',
    })
  }

  /**
   * Reorder countries
   * Integrates with POST /api/v1/admin-panel/geography/countries/reorder/ endpoint
   */
  async reorderCountries(reorderData: ReorderGeographyRequest): Promise<ApiResponse<GeographyCountry[]>> {
    return this.request<GeographyCountry[]>('/api/v1/admin-panel/geography/countries/reorder/', {
      method: 'POST',
      body: JSON.stringify(reorderData),
    })
  }

  /**
   * List regions for a country
   * Integrates with GET /api/v1/admin-panel/geography/countries/{code}/regions/ endpoint
   */
  async getRegions(countryCode: string): Promise<ApiResponse<GeographyRegion[]>> {
    return this.request<GeographyRegion[]>(`/api/v1/admin-panel/geography/countries/${countryCode}/regions/`, {
      method: 'GET',
    })
  }

  /**
   * Get a single region by ID
   * Integrates with GET /api/v1/admin-panel/geography/regions/{id}/ endpoint
   */
  async getRegion(id: number): Promise<ApiResponse<GeographyRegion>> {
    return this.request<GeographyRegion>(`/api/v1/admin-panel/geography/regions/${id}/`, {
      method: 'GET',
    })
  }

  /**
   * Create a new region
   * Integrates with POST /api/v1/admin-panel/geography/regions/ endpoint
   */
  async createRegion(regionData: CreateGeographyRegionRequest): Promise<ApiResponse<GeographyRegion>> {
    return this.request<GeographyRegion>('/api/v1/admin-panel/geography/regions/', {
      method: 'POST',
      body: JSON.stringify(regionData),
    })
  }

  /**
   * Update a region
   * Integrates with PATCH /api/v1/admin-panel/geography/regions/{id}/ endpoint
   */
  async updateRegion(id: number, regionData: UpdateGeographyRegionRequest): Promise<ApiResponse<GeographyRegion>> {
    return this.request<GeographyRegion>(`/api/v1/admin-panel/geography/regions/${id}/`, {
      method: 'PATCH',
      body: JSON.stringify(regionData),
    })
  }

  /**
   * Delete (hide) a region
   * Integrates with DELETE /api/v1/admin-panel/geography/regions/{id}/ endpoint
   */
  async deleteRegion(id: number): Promise<ApiResponse<null>> {
    return this.request<null>(`/api/v1/admin-panel/geography/regions/${id}/`, {
      method: 'DELETE',
    })
  }

  /**
   * Reorder regions within a country
   * Integrates with POST /api/v1/admin-panel/geography/countries/{code}/regions/reorder/ endpoint
   */
  async reorderRegions(countryCode: string, reorderData: ReorderGeographyRequest): Promise<ApiResponse<GeographyRegion[]>> {
    return this.request<GeographyRegion[]>(`/api/v1/admin-panel/geography/countries/${countryCode}/regions/reorder/`, {
      method: 'POST',
      body: JSON.stringify(reorderData),
    })
  }

  /**
   * List cities for a region
   * Integrates with GET /api/v1/admin-panel/geography/regions/{id}/cities/ endpoint
   */
  async getCities(regionId: number): Promise<ApiResponse<GeographyCity[]>> {
    return this.request<GeographyCity[]>(`/api/v1/admin-panel/geography/regions/${regionId}/cities/`, {
      method: 'GET',
    })
  }

  /**
   * Get a single city by ID
   * Integrates with GET /api/v1/admin-panel/geography/cities/{id}/ endpoint
   */
  async getCity(id: number): Promise<ApiResponse<GeographyCity>> {
    return this.request<GeographyCity>(`/api/v1/admin-panel/geography/cities/${id}/`, {
      method: 'GET',
    })
  }

  /**
   * Create a new city
   * Integrates with POST /api/v1/admin-panel/geography/cities/ endpoint
   */
  async createCity(cityData: CreateGeographyCityRequest): Promise<ApiResponse<GeographyCity>> {
    return this.request<GeographyCity>('/api/v1/admin-panel/geography/cities/', {
      method: 'POST',
      body: JSON.stringify(cityData),
    })
  }

  /**
   * Update a city
   * Integrates with PATCH /api/v1/admin-panel/geography/cities/{id}/ endpoint
   */
  async updateCity(id: number, cityData: UpdateGeographyCityRequest): Promise<ApiResponse<GeographyCity>> {
    return this.request<GeographyCity>(`/api/v1/admin-panel/geography/cities/${id}/`, {
      method: 'PATCH',
      body: JSON.stringify(cityData),
    })
  }

  /**
   * Delete (hide) a city
   * Integrates with DELETE /api/v1/admin-panel/geography/cities/{id}/ endpoint
   */
  async deleteCity(id: number): Promise<ApiResponse<null>> {
    return this.request<null>(`/api/v1/admin-panel/geography/cities/${id}/`, {
      method: 'DELETE',
    })
  }

  /**
   * Reorder cities within a region
   * Integrates with POST /api/v1/admin-panel/geography/regions/{id}/cities/reorder/ endpoint
   */
  async reorderCities(regionId: number, reorderData: ReorderGeographyRequest): Promise<ApiResponse<GeographyCity[]>> {
    return this.request<GeographyCity[]>(`/api/v1/admin-panel/geography/regions/${regionId}/cities/reorder/`, {
      method: 'POST',
      body: JSON.stringify(reorderData),
    })
  }
}

// Export singleton instance
export const adminAdapter = new AdminAdapter()

// Export class for testing
export { AdminAdapter }
