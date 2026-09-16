// Mock adapter for search results
// TODO: Replace with real backend API integration when search endpoint is implemented
// This adapter provides mock data based on the backend Property models from Backend Checkpoint 05

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
  translations: PropertyTranslation[]
  policies: PropertyPolicy[]
  rating?: number
  review_count?: number
  image_url?: string
  created_at: string
  updated_at: string
}

export interface SearchParams {
  destination?: string
  check_in?: string
  check_out?: string
  guests?: number
  adults?: number
  children?: number
  rooms?: number
  property_type?: string
  min_price?: number
  max_price?: number
  amenities?: string[]
  sort_by?: string
}

export interface SearchResponse {
  results: Property[]
  total: number
  page: number
  per_page: number
  has_next: boolean
  has_previous: boolean
}

// Mock property types based on backend PropertyType model
const MOCK_PROPERTY_TYPES: PropertyType[] = [
  { id: 1, name: 'Apartment', slug: 'apartment' },
  { id: 2, name: 'House', slug: 'house' },
  { id: 3, name: 'Villa', slug: 'villa' },
  { id: 4, name: 'Studio', slug: 'studio' },
  { id: 5, name: 'Condo', slug: 'condo' },
]

// Mock properties based on backend Property model structure
const MOCK_PROPERTIES: Property[] = [
  {
    id: 1,
    owner_id: 1,
    property_type: MOCK_PROPERTY_TYPES[0],
    status: 'active',
    max_guests: 4,
    bedrooms: 2,
    bathrooms: 1,
    address_line1: '123 Rue de Paris',
    city: 'Paris',
    state: 'Île-de-France',
    postal_code: '75001',
    country: 'France',
    latitude: 48.8566,
    longitude: 2.3522,
    base_price: 150,
    currency: 'EUR',
    total_area: 75,
    floor_number: 3,
    has_elevator: true,
    has_parking: false,
    has_wifi: true,
    has_ac: true,
    has_heating: true,
    translations: [
      {
        language: 'en',
        name: 'Charming Paris Apartment',
        description: 'Beautiful apartment in the heart of Paris with stunning views of the Eiffel Tower. Perfect for couples and small families.',
        address_line1: '123 Rue de Paris',
      },
    ],
    policies: [
      {
        policy_type: 'check_in',
        title: 'Check-in Policy',
        description: 'Check-in from 3:00 PM to 8:00 PM',
        is_strict: false,
      },
      {
        policy_type: 'cancellation',
        title: 'Cancellation Policy',
        description: 'Free cancellation up to 48 hours before check-in',
        is_strict: false,
      },
    ],
    rating: 4.8,
    review_count: 127,
    image_url: '🏰',
    created_at: '2024-01-15T10:00:00Z',
    updated_at: '2024-01-20T15:30:00Z',
  },
  {
    id: 2,
    owner_id: 2,
    property_type: MOCK_PROPERTY_TYPES[1],
    status: 'active',
    max_guests: 6,
    bedrooms: 3,
    bathrooms: 2,
    address_line1: '456 Sakura Street',
    city: 'Tokyo',
    state: 'Tokyo',
    postal_code: '100-0001',
    country: 'Japan',
    latitude: 35.6762,
    longitude: 139.6503,
    base_price: 200,
    currency: 'JPY',
    total_area: 120,
    floor_number: 2,
    has_elevator: true,
    has_parking: true,
    has_wifi: true,
    has_ac: true,
    has_heating: true,
    translations: [
      {
        language: 'en',
        name: 'Modern Tokyo House',
        description: 'Spacious modern house in a quiet Tokyo neighborhood. Traditional Japanese design with modern amenities.',
        address_line1: '456 Sakura Street',
      },
    ],
    policies: [
      {
        policy_type: 'check_in',
        title: 'Check-in Policy',
        description: 'Check-in from 2:00 PM to 9:00 PM',
        is_strict: false,
      },
      {
        policy_type: 'cancellation',
        title: 'Cancellation Policy',
        description: 'Free cancellation up to 24 hours before check-in',
        is_strict: true,
      },
    ],
    rating: 4.9,
    review_count: 89,
    image_url: '🗼',
    created_at: '2024-01-10T08:00:00Z',
    updated_at: '2024-01-18T12:00:00Z',
  },
  {
    id: 3,
    owner_id: 3,
    property_type: MOCK_PROPERTY_TYPES[2],
    status: 'active',
    max_guests: 8,
    bedrooms: 4,
    bathrooms: 3,
    address_line1: '789 Central Park West',
    city: 'New York',
    state: 'New York',
    postal_code: '10024',
    country: 'USA',
    latitude: 40.7829,
    longitude: -73.9654,
    base_price: 450,
    currency: 'USD',
    total_area: 250,
    floor_number: 1,
    has_elevator: false,
    has_parking: true,
    has_wifi: true,
    has_ac: true,
    has_heating: true,
    translations: [
      {
        language: 'en',
        name: 'Luxury Manhattan Villa',
        description: 'Stunning villa overlooking Central Park. Luxury amenities and breathtaking views.',
        address_line1: '789 Central Park West',
      },
    ],
    policies: [
      {
        policy_type: 'check_in',
        title: 'Check-in Policy',
        description: 'Check-in from 4:00 PM to 10:00 PM',
        is_strict: true,
      },
      {
        policy_type: 'cancellation',
        title: 'Cancellation Policy',
        description: 'Strict cancellation policy - 50% refund up to 7 days before check-in',
        is_strict: true,
      },
    ],
    rating: 4.7,
    review_count: 203,
    image_url: '🏙️',
    created_at: '2024-01-05T14:00:00Z',
    updated_at: '2024-01-22T09:00:00Z',
  },
  {
    id: 4,
    owner_id: 4,
    property_type: MOCK_PROPERTY_TYPES[3],
    status: 'active',
    max_guests: 2,
    bedrooms: 1,
    bathrooms: 1,
    address_line1: '321 Baker Street',
    city: 'London',
    state: 'England',
    postal_code: 'NW1 6XE',
    country: 'UK',
    latitude: 51.5238,
    longitude: -0.1586,
    base_price: 120,
    currency: 'GBP',
    total_area: 35,
    floor_number: 2,
    has_elevator: true,
    has_parking: false,
    has_wifi: true,
    has_ac: false,
    has_heating: true,
    translations: [
      {
        language: 'en',
        name: 'Cozy London Studio',
        description: 'Charming studio apartment in historic London. Perfect for business travelers and couples.',
        address_line1: '321 Baker Street',
      },
    ],
    policies: [
      {
        policy_type: 'check_in',
        title: 'Check-in Policy',
        description: 'Check-in from 3:00 PM to 7:00 PM',
        is_strict: false,
      },
      {
        policy_type: 'cancellation',
        title: 'Cancellation Policy',
        description: 'Flexible cancellation - full refund up to 24 hours before check-in',
        is_strict: false,
      },
    ],
    rating: 4.6,
    review_count: 156,
    image_url: '🏰',
    created_at: '2024-01-12T11:00:00Z',
    updated_at: '2024-01-19T16:00:00Z',
  },
  {
    id: 5,
    owner_id: 5,
    property_type: MOCK_PROPERTY_TYPES[0],
    status: 'active',
    max_guests: 3,
    bedrooms: 1,
    bathrooms: 1,
    address_line1: '555 Market Street',
    city: 'San Francisco',
    state: 'California',
    postal_code: '94105',
    country: 'USA',
    latitude: 37.7749,
    longitude: -122.4194,
    base_price: 180,
    currency: 'USD',
    total_area: 55,
    floor_number: 5,
    has_elevator: true,
    has_parking: false,
    has_wifi: true,
    has_ac: true,
    has_heating: true,
    translations: [
      {
        language: 'en',
        name: 'SF Tech Hub Apartment',
        description: 'Modern apartment in San Francisco tech district. Perfect for professionals and startup teams.',
        address_line1: '555 Market Street',
      },
    ],
    policies: [
      {
        policy_type: 'check_in',
        title: 'Check-in Policy',
        description: 'Check-in from 2:00 PM to 8:00 PM',
        is_strict: false,
      },
      {
        policy_type: 'cancellation',
        title: 'Cancellation Policy',
        description: 'Moderate cancellation - full refund up to 48 hours before check-in',
        is_strict: false,
      },
    ],
    rating: 4.5,
    review_count: 78,
    image_url: '🌉',
    created_at: '2024-01-08T09:00:00Z',
    updated_at: '2024-01-21T13:00:00Z',
  },
  {
    id: 6,
    owner_id: 6,
    property_type: MOCK_PROPERTY_TYPES[1],
    status: 'active',
    max_guests: 5,
    bedrooms: 2,
    bathrooms: 2,
    address_line1: '888 Sydney Harbour',
    city: 'Sydney',
    state: 'New South Wales',
    postal_code: '2000',
    country: 'Australia',
    latitude: -33.8688,
    longitude: 151.2093,
    base_price: 250,
    currency: 'AUD',
    total_area: 100,
    floor_number: 1,
    has_elevator: false,
    has_parking: true,
    has_wifi: true,
    has_ac: true,
    has_heating: false,
    translations: [
      {
        language: 'en',
        name: 'Sydney Harbour House',
        description: 'Beautiful house with stunning harbour views. Perfect for families and groups.',
        address_line1: '888 Sydney Harbour',
      },
    ],
    policies: [
      {
        policy_type: 'check_in',
        title: 'Check-in Policy',
        description: 'Check-in from 3:00 PM to 9:00 PM',
        is_strict: false,
      },
      {
        policy_type: 'cancellation',
        title: 'Cancellation Policy',
        description: 'Free cancellation up to 72 hours before check-in',
        is_strict: false,
      },
    ],
    rating: 4.8,
    review_count: 112,
    image_url: '🦘',
    created_at: '2024-01-14T10:00:00Z',
    updated_at: '2024-01-23T14:00:00Z',
  },
]

/**
 * Mock search adapter that simulates backend search API
 * This will be replaced by real API integration when the backend search endpoint is implemented
 */
export class SearchAdapter {
  /**
   * Search properties based on search parameters
   * @param params - Search parameters from URL state
   * @returns Promise with search results
   */
  static async searchProperties(params: SearchParams): Promise<SearchResponse> {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 500))

    let filteredProperties = [...MOCK_PROPERTIES]

    // Filter by destination (city match)
    if (params.destination) {
      const destinationLower = params.destination.toLowerCase()
      filteredProperties = filteredProperties.filter(property =>
        property.city.toLowerCase().includes(destinationLower) ||
        property.country.toLowerCase().includes(destinationLower) ||
        property.translations[0]?.name.toLowerCase().includes(destinationLower)
      )
    }

    // Filter by property type
    if (params.property_type) {
      filteredProperties = filteredProperties.filter(property =>
        property.property_type.slug === params.property_type
      )
    }

    // Filter by guest capacity
    if (params.guests) {
      filteredProperties = filteredProperties.filter(property =>
        property.max_guests >= params.guests!
      )
    }

    // Filter by price range
    if (params.min_price !== undefined) {
      filteredProperties = filteredProperties.filter(property =>
        property.base_price >= params.min_price!
      )
    }

    if (params.max_price !== undefined) {
      filteredProperties = filteredProperties.filter(property =>
        property.base_price <= params.max_price!
      )
    }

    // Filter by amenities
    if (params.amenities && params.amenities.length > 0) {
      filteredProperties = filteredProperties.filter(property => {
        return params.amenities!.every(amenity => {
          switch (amenity) {
            case 'wifi':
              return property.has_wifi
            case 'parking':
              return property.has_parking
            case 'ac':
              return property.has_ac
            case 'heating':
              return property.has_heating
            case 'elevator':
              return property.has_elevator
            default:
              return true
          }
        })
      })
    }

    // Sort results
    if (params.sort_by) {
      switch (params.sort_by) {
        case 'price_low':
          filteredProperties.sort((a, b) => a.base_price - b.base_price)
          break
        case 'price_high':
          filteredProperties.sort((a, b) => b.base_price - a.base_price)
          break
        case 'rating':
          filteredProperties.sort((a, b) => (b.rating || 0) - (a.rating || 0))
          break
        case 'reviews':
          filteredProperties.sort((a, b) => (b.review_count || 0) - (a.review_count || 0))
          break
        default:
          // Default: relevance (no sorting for mock)
          break
      }
    }

    return {
      results: filteredProperties,
      total: filteredProperties.length,
      page: 1,
      per_page: 20,
      has_next: false,
      has_previous: false,
    }
  }

  /**
   * Get property by ID
   * @param id - Property ID
   * @returns Promise with property details
   */
  static async getPropertyById(id: number): Promise<Property | null> {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 300))

    const property = MOCK_PROPERTIES.find(p => p.id === id)
    return property || null
  }

  /**
   * Get available property types
   * @returns Promise with property types
   */
  static async getPropertyTypes(): Promise<PropertyType[]> {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 200))

    return MOCK_PROPERTY_TYPES
  }
}