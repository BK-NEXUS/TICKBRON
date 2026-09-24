// Partner API adapter for hotel-owner property management
// Integrates with backend partner endpoints from Checkpoint 18

import { readApiError } from '../utils/errorHandler'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

// Property types from backend contract
export interface PartnerProperty {
  id: number
  owner: number
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
  created_at: string
  updated_at: string
}

export interface CreatePropertyRequest {
  property_type: number
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
}

export interface UpdatePropertyRequest {
  property_type?: number
  max_guests?: number
  bedrooms?: number
  bathrooms?: number
  address_line1?: string
  address_line2?: string
  city?: string
  state?: string
  postal_code?: string
  country?: string
  latitude?: number
  longitude?: number
  base_price?: number
  currency?: string
  total_area?: number
  floor_number?: number
  has_elevator?: boolean
  has_parking?: boolean
  has_wifi?: boolean
  has_ac?: boolean
  has_heating?: boolean
}

// Room Type types from backend contract
export interface PartnerRoomType {
  id: number
  property: number
  name: string
  slug: string
  description: string
  base_occupancy: number
  max_occupancy: number
  base_price: number
  currency: string
  total_rooms: number
  bed_configuration: string
  room_size?: number
  created_at: string
  updated_at: string
}

export interface CreateRoomTypeRequest {
  property: number
  name: string
  slug: string
  description: string
  base_occupancy: number
  max_occupancy: number
  base_price: number
  currency: string
  total_rooms: number
  bed_configuration: string
  room_size?: number
}

export interface UpdateRoomTypeRequest {
  name?: string
  slug?: string
  description?: string
  base_occupancy?: number
  max_occupancy?: number
  base_price?: number
  currency?: string
  total_rooms?: number
  bed_configuration?: string
  room_size?: number
}

// Rate Plan types from backend contract
export interface PartnerRatePlan {
  id: number
  room_type: number
  name: string
  slug: string
  rate_type: string
  description: string
  base_price: number
  currency: string
  min_nights: number
  max_nights: number
  is_active: boolean
  cancellation_policy: string
  deposit_required: boolean
  deposit_percentage?: number
  advance_booking_days?: number
  created_at: string
  updated_at: string
}

export interface CreateRatePlanRequest {
  room_type: number
  name: string
  slug: string
  rate_type: string
  description: string
  base_price: number
  currency: string
  min_nights: number
  max_nights: number
  is_active: boolean
  cancellation_policy: string
  deposit_required: boolean
  deposit_percentage?: number
  advance_booking_days?: number
}

export interface UpdateRatePlanRequest {
  name?: string
  slug?: string
  rate_type?: string
  description?: string
  base_price?: number
  currency?: string
  min_nights?: number
  max_nights?: number
  is_active?: boolean
  cancellation_policy?: string
  deposit_required?: boolean
  deposit_percentage?: number
  advance_booking_days?: number
}

// Date Inventory types from backend contract
export interface PartnerDateInventory {
  id: number
  rate_plan: number
  date: string
  available_rooms: number
  booked_rooms: number
  price: number
  currency: string
  is_available: boolean
  minimum_stay: number
  maximum_stay: number
  notes?: string
  created_at: string
  updated_at: string
}

export interface CreateDateInventoryRequest {
  rate_plan: number
  date: string
  available_rooms: number
  price: number
  currency: string
  is_available: boolean
  minimum_stay: number
  maximum_stay: number
  notes?: string
}

export interface UpdateDateInventoryRequest {
  available_rooms?: number
  price?: number
  currency?: string
  is_available?: boolean
  minimum_stay?: number
  maximum_stay?: number
  notes?: string
}

// Photo Upload types from backend contract
export interface PropertyPhoto {
  id: number
  property: number
  photo: string
  photo_type: string
  caption?: string
  is_primary: boolean
  display_order: number
  alt_text?: string
  created_at: string
  updated_at: string
}

export interface UploadPhotoRequest {
  photo: File
  photo_type: string
  caption?: string
  is_primary?: boolean
  display_order?: number
  alt_text?: string
}

// Partner Booking types from backend contract
export interface PartnerBooking {
  id: number
  guest: number
  guest_name: string
  property: number
  property_name: string
  status: string
  payment_status: string
  check_in: string
  check_out: string
  number_of_nights: number
  guest_count: number
  total_price: number
  currency: string
  special_requests?: string
  confirmation_code: string
  created_at: string
  updated_at: string
}

// API Response types
export interface ApiResponse<T> {
  data: T | null
  error: string | null
}

class PartnerAdapter {
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
      const response = await fetch(url, defaultOptions)
      
      if (!response.ok) {
        const apiError = await readApiError(response, { 401: 'Authentication required', 403: 'Hotel-owner role required', 404: 'Resource not found' })
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

  // Property Management Methods

  /**
   * Create a new property
   * Integrates with POST /api/v1/partner/properties/ endpoint
   */
  async createProperty(propertyData: CreatePropertyRequest): Promise<ApiResponse<PartnerProperty>> {
    return this.request<PartnerProperty>('/api/v1/partner/properties/', {
      method: 'POST',
      body: JSON.stringify(propertyData),
    })
  }

  /**
   * List hotel-owner's properties
   * Integrates with GET /api/v1/partner/properties/ endpoint
   */
  async getProperties(): Promise<ApiResponse<PartnerProperty[]>> {
    return this.request<PartnerProperty[]>('/api/v1/partner/properties/', {
      method: 'GET',
    })
  }

  /**
   * Update a property
   * Integrates with PATCH /api/v1/partner/properties/{id}/ endpoint
   */
  async updateProperty(id: number, propertyData: UpdatePropertyRequest): Promise<ApiResponse<PartnerProperty>> {
    return this.request<PartnerProperty>(`/api/v1/partner/properties/${id}/`, {
      method: 'PATCH',
      body: JSON.stringify(propertyData),
    })
  }

  /**
   * Delete a property (soft delete)
   * Integrates with DELETE /api/v1/partner/properties/{id}/ endpoint
   */
  async deleteProperty(id: number): Promise<ApiResponse<null>> {
    return this.request<null>(`/api/v1/partner/properties/${id}/`, {
      method: 'DELETE',
    })
  }

  // Room Type Management Methods

  /**
   * Create a new room type
   * Integrates with POST /api/v1/partner/rooms/ endpoint
   */
  async createRoomType(roomTypeData: CreateRoomTypeRequest): Promise<ApiResponse<PartnerRoomType>> {
    return this.request<PartnerRoomType>('/api/v1/partner/rooms/', {
      method: 'POST',
      body: JSON.stringify(roomTypeData),
    })
  }

  /**
   * List hotel-owner's room types
   * Integrates with GET /api/v1/partner/rooms/ endpoint
   */
  async getRoomTypes(): Promise<ApiResponse<PartnerRoomType[]>> {
    return this.request<PartnerRoomType[]>('/api/v1/partner/rooms/', {
      method: 'GET',
    })
  }

  /**
   * Update a room type
   * Integrates with PATCH /api/v1/partner/rooms/{id}/ endpoint
   */
  async updateRoomType(id: number, roomTypeData: UpdateRoomTypeRequest): Promise<ApiResponse<PartnerRoomType>> {
    return this.request<PartnerRoomType>(`/api/v1/partner/rooms/${id}/`, {
      method: 'PATCH',
      body: JSON.stringify(roomTypeData),
    })
  }

  /**
   * Delete a room type (soft delete)
   * Integrates with DELETE /api/v1/partner/rooms/{id}/ endpoint
   */
  async deleteRoomType(id: number): Promise<ApiResponse<null>> {
    return this.request<null>(`/api/v1/partner/rooms/${id}/`, {
      method: 'DELETE',
    })
  }

  // Rate Plan Management Methods

  /**
   * Create a new rate plan
   * Integrates with POST /api/v1/partner/rates/ endpoint
   */
  async createRatePlan(ratePlanData: CreateRatePlanRequest): Promise<ApiResponse<PartnerRatePlan>> {
    return this.request<PartnerRatePlan>('/api/v1/partner/rates/', {
      method: 'POST',
      body: JSON.stringify(ratePlanData),
    })
  }

  /**
   * List hotel-owner's rate plans
   * Integrates with GET /api/v1/partner/rates/ endpoint
   */
  async getRatePlans(): Promise<ApiResponse<PartnerRatePlan[]>> {
    return this.request<PartnerRatePlan[]>('/api/v1/partner/rates/', {
      method: 'GET',
    })
  }

  /**
   * Update a rate plan
   * Integrates with PATCH /api/v1/partner/rates/{id}/ endpoint
   */
  async updateRatePlan(id: number, ratePlanData: UpdateRatePlanRequest): Promise<ApiResponse<PartnerRatePlan>> {
    return this.request<PartnerRatePlan>(`/api/v1/partner/rates/${id}/`, {
      method: 'PATCH',
      body: JSON.stringify(ratePlanData),
    })
  }

  /**
   * Delete a rate plan (soft delete)
   * Integrates with DELETE /api/v1/partner/rates/{id}/ endpoint
   */
  async deleteRatePlan(id: number): Promise<ApiResponse<null>> {
    return this.request<null>(`/api/v1/partner/rates/${id}/`, {
      method: 'DELETE',
    })
  }

  // Date Inventory Management Methods

  /**
   * Create date inventory
   * Integrates with POST /api/v1/partner/inventory/ endpoint
   */
  async createDateInventory(inventoryData: CreateDateInventoryRequest): Promise<ApiResponse<PartnerDateInventory>> {
    return this.request<PartnerDateInventory>('/api/v1/partner/inventory/', {
      method: 'POST',
      body: JSON.stringify(inventoryData),
    })
  }

  /**
   * List hotel-owner's date inventory
   * Integrates with GET /api/v1/partner/inventory/ endpoint
   */
  async getDateInventory(): Promise<ApiResponse<PartnerDateInventory[]>> {
    return this.request<PartnerDateInventory[]>('/api/v1/partner/inventory/', {
      method: 'GET',
    })
  }

  /**
   * Update date inventory
   * Integrates with PATCH /api/v1/partner/inventory/{id}/ endpoint
   */
  async updateDateInventory(id: number, inventoryData: UpdateDateInventoryRequest): Promise<ApiResponse<PartnerDateInventory>> {
    return this.request<PartnerDateInventory>(`/api/v1/partner/inventory/${id}/`, {
      method: 'PATCH',
      body: JSON.stringify(inventoryData),
    })
  }

  /**
   * Delete date inventory (soft delete)
   * Integrates with DELETE /api/v1/partner/inventory/{id}/ endpoint
   */
  async deleteDateInventory(id: number): Promise<ApiResponse<null>> {
    return this.request<null>(`/api/v1/partner/inventory/${id}/`, {
      method: 'DELETE',
    })
  }

  // Photo Upload Methods

  /**
   * Upload property photo
   * Integrates with POST /api/v1/partner/properties/{id}/photos/ endpoint
   */
  async uploadPropertyPhoto(propertyId: number, photoData: UploadPhotoRequest): Promise<ApiResponse<PropertyPhoto>> {
    const formData = new FormData()
    formData.append('photo', photoData.photo)
    formData.append('photo_type', photoData.photo_type)
    if (photoData.caption) formData.append('caption', photoData.caption)
    if (photoData.is_primary !== undefined) formData.append('is_primary', photoData.is_primary.toString())
    if (photoData.display_order !== undefined) formData.append('display_order', photoData.display_order.toString())
    if (photoData.alt_text) formData.append('alt_text', photoData.alt_text)

    const url = `${this.baseUrl}/api/v1/partner/properties/${propertyId}/photos/`
    
    try {
      const response = await fetch(url, {
        method: 'POST',
        credentials: 'include',
        body: formData,
      })

      if (!response.ok) {
        const apiError = await readApiError(response, { 401: 'Authentication required', 403: 'Hotel-owner role required', 404: 'Property not found' })
        return { data: null, error: apiError.message }
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

  // Partner Bookings Methods

  /**
   * List bookings for hotel-owner's properties
   * Integrates with GET /api/v1/partner/bookings/ endpoint
   */
  async getPartnerBookings(status?: string, paymentStatus?: string): Promise<ApiResponse<PartnerBooking[]>> {
    const params = new URLSearchParams()
    if (status) params.append('status', status)
    if (paymentStatus) params.append('payment_status', paymentStatus)

    const endpoint = `/api/v1/partner/bookings/${params.toString() ? `?${params.toString()}` : ''}`
    return this.request<PartnerBooking[]>(endpoint)
  }
}

// Export singleton instance
export const partnerAdapter = new PartnerAdapter()

// Export class for testing
export { PartnerAdapter }
