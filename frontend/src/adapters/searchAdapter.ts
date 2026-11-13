// Izlew nátiyjeleri ushın mock adapter
// TODO: Izlew endpoint i ámelge asırılǵanda haqıyqıy backend API integraciyası menen almastırıń
// Bul adapter Backend Checkpoint 05 degi backend Property model lerine tiykarlanǵan mock maǵlıwmat beredi

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
  /** R9: mehmanxana iyesi belgileydi; VIP xonalar birinshi keledi */
  is_vip?: boolean
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

export interface DateInventory {
  id: number
  rate_plan_id: number
  date: string
  available_rooms: number
  booked_rooms: number
  price: number
  currency: string
  is_available: boolean
  minimum_stay: number
  maximum_stay: number
  notes?: string
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
  amenities?: PropertyAmenity[]
  nearby_places?: NearbyPlace[]
  restaurants?: Restaurant[]
  room_types?: RoomType[]
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

// Backend PropertyType modeline tiykarlanǵan mock mehmanxana túrleri
const MOCK_PROPERTY_TYPES: PropertyType[] = [
  { id: 1, name: 'Apartment', slug: 'apartment' },
  { id: 2, name: 'House', slug: 'house' },
  { id: 3, name: 'Villa', slug: 'villa' },
  { id: 4, name: 'Studio', slug: 'studio' },
  { id: 5, name: 'Condo', slug: 'condo' },
]

// Backend Property model dúzilisine tiykarlanǵan mock mehmanxanalar
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
    image_url: '',
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
    image_url: '',
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
    image_url: '',
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
    image_url: '',
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
    image_url: '',
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
    image_url: '',
    created_at: '2024-01-14T10:00:00Z',
    updated_at: '2024-01-23T14:00:00Z',
  },
]

// Backend AmenityCategory modeline tiykarlanǵan mock amenity kategoriyaları
const MOCK_AMENITY_CATEGORIES: AmenityCategory[] = [
  { id: 1, name: 'Kitchen', slug: 'kitchen', description: 'Kitchen amenities', icon: '', sort_order: 1 },
  { id: 2, name: 'Bathroom', slug: 'bathroom', description: 'Bathroom amenities', icon: '', sort_order: 2 },
  { id: 3, name: 'Entertainment', slug: 'entertainment', description: 'Entertainment options', icon: '', sort_order: 3 },
  { id: 4, name: 'Safety', slug: 'safety', description: 'Safety features', icon: '', sort_order: 4 },
  { id: 5, name: 'Outdoor', slug: 'outdoor', description: 'Outdoor spaces', icon: '', sort_order: 5 },
]

// Backend Amenity modeline tiykarlanǵan mock amenity ler
const MOCK_AMENITIES: Amenity[] = [
  { id: 1, category: MOCK_AMENITY_CATEGORIES[0], name: 'WiFi', slug: 'wifi', description: 'High-speed internet', icon: '', is_searchable: true, sort_order: 1 },
  { id: 2, category: MOCK_AMENITY_CATEGORIES[0], name: 'Kitchen', slug: 'kitchen', description: 'Full kitchen', icon: '', is_searchable: true, sort_order: 2 },
  { id: 3, category: MOCK_AMENITY_CATEGORIES[1], name: 'Air Conditioning', slug: 'ac', description: 'Climate control', icon: '', is_searchable: true, sort_order: 3 },
  { id: 4, category: MOCK_AMENITY_CATEGORIES[1], name: 'Heating', slug: 'heating', description: 'Central heating', icon: '', is_searchable: true, sort_order: 4 },
  { id: 5, category: MOCK_AMENITY_CATEGORIES[2], name: 'TV', slug: 'tv', description: 'Flat-screen TV', icon: '', is_searchable: true, sort_order: 5 },
  { id: 6, category: MOCK_AMENITY_CATEGORIES[3], name: 'Smoke Alarm', slug: 'smoke-alarm', description: 'Smoke detector', icon: '', is_searchable: false, sort_order: 6 },
  { id: 7, category: MOCK_AMENITY_CATEGORIES[3], name: 'First Aid Kit', slug: 'first-aid', description: 'First aid supplies', icon: '', is_searchable: false, sort_order: 7 },
  { id: 8, category: MOCK_AMENITY_CATEGORIES[4], name: 'Parking', slug: 'parking', description: 'Free parking', icon: '', is_searchable: true, sort_order: 8 },
  { id: 9, category: MOCK_AMENITY_CATEGORIES[4], name: 'Balcony', slug: 'balcony', description: 'Private balcony', icon: '', is_searchable: true, sort_order: 9 },
  { id: 10, category: MOCK_AMENITY_CATEGORIES[0], name: 'Washer', slug: 'washer', description: 'Washing machine', icon: '', is_searchable: true, sort_order: 10 },
]

// Mock jaqındaǵı orınlar
const MOCK_NEARBY_PLACES: NearbyPlace[] = [
  { id: 1, name: 'Central Park', category: 'Park', distance: 0.3, distance_unit: 'km', rating: 4.8, address: 'Manhattan, NY' },
  { id: 2, name: 'Times Square', category: 'Landmark', distance: 1.2, distance_unit: 'km', rating: 4.5, address: 'Manhattan, NY' },
  { id: 3, name: 'Grand Central Terminal', category: 'Transportation', distance: 0.8, distance_unit: 'km', rating: 4.7, address: 'Manhattan, NY' },
  { id: 4, name: 'Museum of Modern Art', category: 'Museum', distance: 0.5, distance_unit: 'km', rating: 4.9, address: 'Manhattan, NY' },
  { id: 5, name: 'Empire State Building', category: 'Landmark', distance: 1.5, distance_unit: 'km', rating: 4.6, address: 'Manhattan, NY' },
]

// Mock restoranlar
const MOCK_RESTAURANTS: Restaurant[] = [
  { id: 1, name: 'Le Bernardin', cuisine: 'French', distance: 0.2, distance_unit: 'km', rating: 4.9, price_range: '$$$$', address: '155 W 51st St' },
  { id: 2, name: 'Joe\'s Pizza', cuisine: 'Italian', distance: 0.1, distance_unit: 'km', rating: 4.5, price_range: '$', address: '7 Carmine St' },
  { id: 3, name: 'Xi\'an Famous Foods', cuisine: 'Chinese', distance: 0.3, distance_unit: 'km', rating: 4.7, price_range: '$$', address: 'multiple locations' },
  { id: 4, name: 'Katz\'s Delicatessen', cuisine: 'American', distance: 0.4, distance_unit: 'km', rating: 4.8, price_range: '$$', address: '205 E Houston St' },
  { id: 5, name: 'Tatiana by Kwame Onwuachi', cuisine: 'African', distance: 0.6, distance_unit: 'km', rating: 4.6, price_range: '$$$', address: 'Lincoln Center' },
]

// Backend RoomType modeline tiykarlanǵan mock xona túrleri
const MOCK_ROOM_TYPES: RoomType[] = [
  {
    id: 1,
    property_id: 1,
    name: 'Standard Room',
    slug: 'standard-room',
    description: 'Comfortable room with essential amenities',
    base_occupancy: 2,
    max_occupancy: 2,
    base_price: 120,
    currency: 'EUR',
    total_rooms: 5,
    bed_configuration: '1 Queen Bed',
    room_size: 25,
  },
  {
    id: 2,
    property_id: 1,
    name: 'Deluxe Room',
    slug: 'deluxe-room',
    description: 'Spacious room with city views',
    base_occupancy: 2,
    max_occupancy: 3,
    base_price: 180,
    currency: 'EUR',
    total_rooms: 3,
    bed_configuration: '1 King Bed',
    room_size: 35,
  },
  {
    id: 3,
    property_id: 1,
    name: 'Suite',
    slug: 'suite',
    description: 'Luxury suite with separate living area',
    base_occupancy: 2,
    max_occupancy: 4,
    base_price: 280,
    currency: 'EUR',
    total_rooms: 2,
    bed_configuration: '1 King Bed + Sofa Bed',
    room_size: 55,
  },
  {
    id: 4,
    property_id: 2,
    name: 'Japanese Style Room',
    slug: 'japanese-style-room',
    description: 'Traditional Japanese room with tatami',
    base_occupancy: 2,
    max_occupancy: 4,
    base_price: 150,
    currency: 'JPY',
    total_rooms: 4,
    bed_configuration: '2 Futon Beds',
    room_size: 30,
  },
  {
    id: 5,
    property_id: 2,
    name: 'Modern Western Room',
    slug: 'modern-western-room',
    description: 'Contemporary room with modern amenities',
    base_occupancy: 2,
    max_occupancy: 3,
    base_price: 200,
    currency: 'JPY',
    total_rooms: 3,
    bed_configuration: '1 Queen Bed',
    room_size: 28,
  },
]

// Backend RatePlan modeline tiykarlanǵan mock rate plan lar
const MOCK_RATE_PLANS: RatePlan[] = [
  {
    id: 1,
    room_type_id: 1,
    name: 'Standard Rate',
    slug: 'standard-rate',
    rate_type: 'standard',
    description: 'Standard flexible rate with free cancellation',
    base_price: 120,
    currency: 'EUR',
    min_nights: 1,
    max_nights: 30,
    is_active: true,
    cancellation_policy: 'Free cancellation up to 48 hours before check-in',
    deposit_required: false,
  },
  {
    id: 2,
    room_type_id: 1,
    name: 'Non-Refundable Rate',
    slug: 'non-refundable-rate',
    rate_type: 'non_refundable',
    description: 'Discounted rate with no free cancellation',
    base_price: 100,
    currency: 'EUR',
    min_nights: 2,
    max_nights: 30,
    is_active: true,
    cancellation_policy: 'No free cancellation',
    deposit_required: false,
  },
  {
    id: 3,
    room_type_id: 2,
    name: 'Deluxe Standard Rate',
    slug: 'deluxe-standard-rate',
    rate_type: 'standard',
    description: 'Standard rate for deluxe rooms',
    base_price: 180,
    currency: 'EUR',
    min_nights: 1,
    max_nights: 30,
    is_active: true,
    cancellation_policy: 'Free cancellation up to 48 hours before check-in',
    deposit_required: false,
  },
  {
    id: 4,
    room_type_id: 3,
    name: 'Suite Standard Rate',
    slug: 'suite-standard-rate',
    rate_type: 'standard',
    description: 'Standard rate for suites',
    base_price: 280,
    currency: 'EUR',
    min_nights: 1,
    max_nights: 30,
    is_active: true,
    cancellation_policy: 'Free cancellation up to 72 hours before check-in',
    deposit_required: true,
    deposit_percentage: 20,
  },
  {
    id: 5,
    room_type_id: 4,
    name: 'Japanese Room Rate',
    slug: 'japanese-room-rate',
    rate_type: 'standard',
    description: 'Standard rate for Japanese style rooms',
    base_price: 150,
    currency: 'JPY',
    min_nights: 1,
    max_nights: 14,
    is_active: true,
    cancellation_policy: 'Free cancellation up to 24 hours before check-in',
    deposit_required: false,
  },
]

// Backend DateInventory modeline tiykarlanǵan mock date inventory
const MOCK_DATE_INVENTORY: DateInventory[] = []

// Keyingi 30 kún ushın mock date inventory jaratıw
function generateMockDateInventory() {
  const today = new Date()
  const inventory: DateInventory[] = []
  
  MOCK_RATE_PLANS.forEach(ratePlan => {
    for (let i = 0; i < 30; i++) {
      const date = new Date(today)
      date.setDate(today.getDate() + i)
      const dateStr = date.toISOString().split('T')[0]
      
      // 0 hám jámi xonalar aralıǵında tosınarlıq bos orın
      const availableRooms = Math.floor(Math.random() * 3) + 1
      const bookedRooms = Math.floor(Math.random() * availableRooms)
      
      inventory.push({
        id: inventory.length + 1,
        rate_plan_id: ratePlan.id,
        date: dateStr,
        available_rooms: availableRooms,
        booked_rooms: bookedRooms,
        price: ratePlan.base_price + (Math.random() > 0.7 ? 20 : 0), // Tosınarlıq baha ózgerisi
        currency: ratePlan.currency,
        is_available: availableRooms > bookedRooms,
        minimum_stay: ratePlan.min_nights,
        maximum_stay: ratePlan.max_nights,
        notes: i === 0 ? 'Check-in available from 3:00 PM' : undefined,
      })
    }
  })
  
  return inventory
}

MOCK_DATE_INVENTORY.push(...generateMockDateInventory())

// Mehmanxana ushın amenity lerdi alıw járdemshi funkciyası
function getPropertyAmenities(propertyId: number): PropertyAmenity[] {
  // Demo maqsetinde túrli mehmanxanalarǵa túrli amenity lerdi beriw
  const baseAmenities = [
    { amenity: MOCK_AMENITIES[0], is_available: true }, // WiFi
    { amenity: MOCK_AMENITIES[2], is_available: true }, // Kondicioner
    { amenity: MOCK_AMENITIES[3], is_available: true }, // Jılıtıw
    { amenity: MOCK_AMENITIES[5], is_available: true }, // Tútin signalizaciyası
    { amenity: MOCK_AMENITIES[6], is_available: true }, // Birinshi járdem apteshkası
  ]
  
  // Mehmanxanaǵa tán amenity lerdi qosıw
  if (propertyId === 1) {
    return [
      ...baseAmenities,
      { amenity: MOCK_AMENITIES[1], is_available: true }, // Asxana
      { amenity: MOCK_AMENITIES[4], is_available: true }, // TV
      { amenity: MOCK_AMENITIES[8], is_available: false }, // Parking (joq)
    ]
  } else if (propertyId === 2) {
    return [
      ...baseAmenities,
      { amenity: MOCK_AMENITIES[1], is_available: true }, // Asxana
      { amenity: MOCK_AMENITIES[7], is_available: true }, // Parking
      { amenity: MOCK_AMENITIES[9], is_available: true }, // Kir juwatuǵın mashina
    ]
  }
  
  return baseAmenities
}

// Mehmanxana ushın xona túrlerin alıw járdemshi funkciyası
function getPropertyRoomTypes(propertyId: number): RoomType[] {
  return MOCK_ROOM_TYPES.filter(room => room.property_id === propertyId)
}

// Xona túri ushın rate plan lardı alıw járdemshi funkciyası
function getRatePlansForRoomType(roomTypeId: number): RatePlan[] {
  return MOCK_RATE_PLANS.filter(plan => plan.room_type_id === roomTypeId && plan.is_active)
}

// Rate plan ushın date inventory di alıw járdemshi funkciyası
function getDateInventoryForRatePlan(ratePlanId: number): DateInventory[] {
  return MOCK_DATE_INVENTORY.filter(inventory => inventory.rate_plan_id === ratePlanId)
}

/**
 * Backend izlew API ın uqsatatuǵın mock izlew adapteri
 * Backend izlew endpoint i ámelge asırılǵanda ol haqıyqıy API integraciyası menen almastırıladı
 */
export class SearchAdapter {
  /**
   * Izlew parametrleri boyınsha mehmanxanalardı izlew
   * @param params - URL jaǵdayınan izlew parametrleri
   * @returns Izlew nátiyjeleri menen Promise
   */
  static async searchProperties(params: SearchParams): Promise<SearchResponse> {
    // API kechikiwin uqsatıw
    await new Promise(resolve => setTimeout(resolve, 500))

    let filteredProperties = [...MOCK_PROPERTIES]

    // Barar orın (qala sáykesligi) boyınsha filterlew
    if (params.destination) {
      const destinationLower = params.destination.toLowerCase()
      filteredProperties = filteredProperties.filter(property =>
        property.city.toLowerCase().includes(destinationLower) ||
        property.country.toLowerCase().includes(destinationLower) ||
        property.translations[0]?.name.toLowerCase().includes(destinationLower)
      )
    }

    // Mehmanxana túri boyınsha filterlew
    if (params.property_type) {
      filteredProperties = filteredProperties.filter(property =>
        property.property_type.slug === params.property_type
      )
    }

    // Mehmanlar sıyımlılıǵı boyınsha filterlew
    if (params.guests) {
      filteredProperties = filteredProperties.filter(property =>
        property.max_guests >= params.guests!
      )
    }

    // Baha aralıǵı boyınsha filterlew
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

    // Amenity ler boyınsha filterlew
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

    // Nátiyjelerdi tártiplew
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
          // Ádetde: relevance (mock ushın tártiplew joq)
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
   * Mehmanxananı ID boyınsha alıw
   * @param id - Mehmanxana ID si
   * @returns Mehmanxana tolıq maǵlıwmatı menen Promise
   */
  static async getPropertyById(id: number): Promise<Property | null> {
    // API kechikiwin uqsatıw
    await new Promise(resolve => setTimeout(resolve, 300))

    const property = MOCK_PROPERTIES.find(p => p.id === id)
    if (!property) return null

    // Mehmanxana tolıq maǵlıwmatı beti ushın keńeytilgen maǵlıwmat qosıw
    return {
      ...property,
      amenities: getPropertyAmenities(id),
      nearby_places: MOCK_NEARBY_PLACES,
      restaurants: MOCK_RESTAURANTS,
      room_types: getPropertyRoomTypes(id),
    }
  }

  /**
   * Bar mehmanxana túrlerin alıw
   * @returns Mehmanxana túrleri menen Promise
   */
  static async getPropertyTypes(): Promise<PropertyType[]> {
    // API kechikiwin uqsatıw
    await new Promise(resolve => setTimeout(resolve, 200))

    return MOCK_PROPERTY_TYPES
  }

  /**
   * Xona túri ushın rate plan lardı alıw
   * @param roomTypeId - Xona túri ID si
   * @returns Rate plan lar menen Promise
   */
  static async getRatePlansForRoomType(roomTypeId: number): Promise<RatePlan[]> {
    // API kechikiwin uqsatıw
    await new Promise(resolve => setTimeout(resolve, 200))

    return getRatePlansForRoomType(roomTypeId)
  }

  /**
   * Rate plan ushın date inventory di alıw
   * @param ratePlanId - Rate plan ID si
   * @param startDate - Baslanıw sanası (ISO formatı)
   * @param endDate - Pitiw sanası (ISO formatı)
   * @returns Date inventory menen Promise
   */
  static async getDateInventoryForRatePlan(
    ratePlanId: number,
    startDate?: string,
    endDate?: string
  ): Promise<DateInventory[]> {
    // API kechikiwin uqsatıw
    await new Promise(resolve => setTimeout(resolve, 200))

    let inventory = getDateInventoryForRatePlan(ratePlanId)

    // Berilgen bolsa sana aralıǵı boyınsha filterlew
    if (startDate) {
      inventory = inventory.filter(item => item.date >= startDate)
    }
    if (endDate) {
      inventory = inventory.filter(item => item.date <= endDate)
    }

    return inventory
  }
}