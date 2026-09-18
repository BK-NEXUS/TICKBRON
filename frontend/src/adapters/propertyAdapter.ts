// Property API adapter for search and property detail endpoints
// Integrates with backend property endpoints from Checkpoint 10-11

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export interface PropertyType {
  id: number
  name: string
  slug: string
}

export interface PropertyTranslation {
  language: string
  name: string
  description: string
  address_line1?: string
  address_line2?: string
}

export interface PropertyPolicy {
  policy_type: string
  title: string
  description: string
  is_strict: boolean
}

export interface AmenityCategory {
  id: number
  name: string
  slug: string
  description: string
  icon: string
  sort_order: number
}

export interface Amenity {
  id: number
  category: AmenityCategory
  name: string
  slug: string
  description: string
  icon: string
  is_searchable: boolean
  sort_order: number
}

export interface PropertyAmenity {
  amenity: Amenity
  is_available: boolean
  notes?: string
}

export interface PropertyPhoto {
  id: number
  photo: string
  photo_type: string
  caption?: string
  is_primary: boolean
  display_order: number
  alt_text?: string
}

export interface NearbyPlace {
  id: number
  name: string
  category: string
  distance: number
  distance_unit: string
  rating?: number
  address?: string
}

export interface Restaurant {
  id: number
  name: string
  cuisine: string
  distance: number
  distance_unit: string
  rating?: number
  price_range: string
  address?: string
}

export interface RoomType {
  id: number
  property_id: number
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
  photos?: PropertyPhoto[]
  amenities?: PropertyAmenity[]
  rate_plans?: RatePlan[]
}

export interface RatePlan {
  id: number
  room_type_id: number
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

export interface Property {
  id: number
  owner_id: number
  property_type: PropertyType
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
  name?: string
  description?: string
  translations: PropertyTranslation[]
  policies: PropertyPolicy[]
  amenities?: PropertyAmenity[]
  room_types?: RoomType[]
  gallery?: Record<string, PropertyPhoto[]>
  rating?: number
  review_count?: number
  primary_photo?: PropertyPhoto
  nearby_places?: NearbyPlace[]
  restaurants?: Restaurant[]
  created_at: string
  updated_at: string
}

export interface SearchParams {
  q?: string
  location?: string
  lat?: number
  lng?: number
  radius?: number
  min_price?: number
  max_price?: number
  min_guests?: number
  max_guests?: number
  amenities?: number[]
  property_type?: number
  check_in?: string
  check_out?: string
  sort?: string
  page?: number
  page_size?: number
}

export interface SearchResponse {
  count: number
  next: string | null
  previous: string | null
  results: Property[]
  page: number
  page_size: number
  total_pages: number
}

export interface PropertyDetailResponse extends Property {
  gallery: Record<string, PropertyPhoto[]>
  room_types: RoomType[]
  amenities: PropertyAmenity[]
  nearby_places?: NearbyPlace[]
  restaurants?: Restaurant[]
}

export interface ApiError {
  error: string
  details?: string | Record<string, string[]>
}

class PropertyAdapter {
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
        const errorData = await response.json().catch(() => ({}))
        const errorMessage = 
          errorData.detail || 
          errorData.error || 
          `HTTP ${response.status}: ${response.statusText}`
        return { data: null, error: errorMessage }
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
   * Search properties based on search parameters
   * Integrates with GET /api/v1/properties/search/ endpoint
   */
  async searchProperties(params: SearchParams): Promise<{ data: SearchResponse | null; error: string | null }> {
    const queryParams = new URLSearchParams()
    
    if (params.q) queryParams.append('q', params.q)
    if (params.location) queryParams.append('location', params.location)
    if (params.lat !== undefined) queryParams.append('lat', params.lat.toString())
    if (params.lng !== undefined) queryParams.append('lng', params.lng.toString())
    if (params.radius !== undefined) queryParams.append('radius', params.radius.toString())
    if (params.min_price !== undefined) queryParams.append('min_price', params.min_price.toString())
    if (params.max_price !== undefined) queryParams.append('max_price', params.max_price.toString())
    if (params.min_guests !== undefined) queryParams.append('min_guests', params.min_guests.toString())
    if (params.max_guests !== undefined) queryParams.append('max_guests', params.max_guests.toString())
    if (params.amenities && params.amenities.length > 0) {
      queryParams.append('amenities', params.amenities.join(','))
    }
    if (params.property_type !== undefined) queryParams.append('property_type', params.property_type.toString())
    if (params.check_in) queryParams.append('check_in', params.check_in)
    if (params.check_out) queryParams.append('check_out', params.check_out)
    if (params.sort) queryParams.append('sort', params.sort)
    if (params.page !== undefined) queryParams.append('page', params.page.toString())
    if (params.page_size !== undefined) queryParams.append('page_size', params.page_size.toString())

    const queryString = queryParams.toString()
    const endpoint = `/api/v1/properties/search/${queryString ? `?${queryString}` : ''}`
    
    return this.request<SearchResponse>(endpoint)
  }

  /**
   * Get search suggestions for autocomplete
   * Integrates with GET /api/v1/properties/search/suggestions/ endpoint
   */
  async getSearchSuggestions(query: string, limit: number = 5): Promise<{ data: { suggestions: string[] } | null; error: string | null }> {
    const queryParams = new URLSearchParams()
    queryParams.append('q', query)
    queryParams.append('limit', limit.toString())
    
    const endpoint = `/api/v1/properties/search/suggestions/?${queryParams.toString()}`
    
    return this.request<{ suggestions: string[] }>(endpoint)
  }

  /**
   * Get property details by ID
   * Integrates with GET /api/v1/properties/{id}/ endpoint
   */
  async getPropertyById(id: number): Promise<{ data: PropertyDetailResponse | null; error: string | null }> {
    return this.request<PropertyDetailResponse>(`/api/v1/properties/${id}/`)
  }
}

// Export singleton instance
export const propertyAdapter = new PropertyAdapter()

// Export class for testing
export { PropertyAdapter }
