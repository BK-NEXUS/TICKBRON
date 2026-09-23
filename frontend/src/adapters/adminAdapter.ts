// Admin API adapter for admin moderation and management
// Integrates with backend admin endpoints from Checkpoint 18

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
        if (response.status === 401) {
          return { data: null, error: 'Authentication required' }
        }
        if (response.status === 403) {
          return { data: null, error: 'Admin or staff role required' }
        }
        if (response.status === 404) {
          return { data: null, error: 'Resource not found' }
        }
        const errorData = await response.json().catch(() => ({}))
        const errorMessage = 
          errorData.detail || 
          errorData.error || 
          `HTTP ${response.status}: ${response.statusText}`
        return { data: null, error: errorMessage }
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
    return this.request<AdminProperty[]>('/api/v1/admin-panel/properties/', {
      method: 'GET',
    })
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
    return this.request<AdminAmenity[]>('/api/v1/admin-panel/amenities/', {
      method: 'GET',
    })
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
    return this.request<AdminAmenityCategory[]>('/api/v1/admin-panel/amenities/categories/', {
      method: 'GET',
    })
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
}

// Export singleton instance
export const adminAdapter = new AdminAdapter()

// Export class for testing
export { AdminAdapter }
