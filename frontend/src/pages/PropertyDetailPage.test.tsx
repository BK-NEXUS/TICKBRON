import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { PropertyDetailPage } from './PropertyDetailPage'
import { SearchAdapter } from '../adapters/searchAdapter'

// Mock React Router
vi.mock('react-router-dom', () => ({
  useParams: () => ({ id: '1' }),
  useNavigate: () => vi.fn(),
}))

// Mock SearchAdapter
vi.mock('../adapters/searchAdapter')

describe('PropertyDetailPage', () => {
  const mockProperty = {
    id: 1,
    owner_id: 1,
    property_type: { id: 1, name: 'Apartment', slug: 'apartment' },
    status: 'active',
    max_guests: 4,
    bedrooms: 2,
    bathrooms: 1,
    address_line1: '123 Test Street',
    city: 'Test City',
    country: 'Test Country',
    base_price: 100,
    currency: 'USD',
    has_elevator: true,
    has_parking: false,
    has_wifi: true,
    has_ac: true,
    has_heating: true,
    translations: [
      {
        language: 'en',
        name: 'Test Property',
        description: 'Test description',
      },
    ],
    policies: [
      {
        policy_type: 'check_in',
        title: 'Check-in Policy',
        description: 'Check-in from 3:00 PM',
        is_strict: false,
      },
    ],
    amenities: [
      {
        amenity: {
          id: 1,
          category: { id: 1, name: 'Kitchen', slug: 'kitchen', description: 'Kitchen amenities', icon: '🍳', sort_order: 1 },
          name: 'WiFi',
          slug: 'wifi',
          description: 'High-speed internet',
          icon: '📶',
          is_searchable: true,
          sort_order: 1,
        },
        is_available: true,
      },
    ],
    nearby_places: [
      {
        id: 1,
        name: 'Test Park',
        category: 'Park',
        distance: 0.5,
        distance_unit: 'km',
        rating: 4.5,
        address: '123 Park St',
      },
    ],
    restaurants: [
      {
        id: 1,
        name: 'Test Restaurant',
        cuisine: 'Italian',
        distance: 0.3,
        distance_unit: 'km',
        rating: 4.7,
        price_range: '$$',
        address: '456 Food Ave',
      },
    ],
    rating: 4.5,
    review_count: 100,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders loading state initially', () => {
    vi.mocked(SearchAdapter.getPropertyById).mockResolvedValue(mockProperty)

    render(<PropertyDetailPage />)
    
    expect(screen.getByText('Loading property details...')).toBeInTheDocument()
  })

  it('renders property details after loading', async () => {
    vi.mocked(SearchAdapter.getPropertyById).mockResolvedValue(mockProperty)

    render(<PropertyDetailPage />)

    await waitFor(() => {
      expect(screen.queryByText('Loading property details...')).not.toBeInTheDocument()
    })

    expect(screen.getByText('Test Property')).toBeInTheDocument()
  })

  it('renders error state when property not found', async () => {
    vi.mocked(SearchAdapter.getPropertyById).mockResolvedValue(null)

    render(<PropertyDetailPage />)

    await waitFor(() => {
      expect(screen.getByText('Property Not Found')).toBeInTheDocument()
    })
  })

  it('renders error state when API call fails', async () => {
    vi.mocked(SearchAdapter.getPropertyById).mockRejectedValue(new Error('API Error'))

    render(<PropertyDetailPage />)

    await waitFor(() => {
      expect(screen.getByText('Property Not Found')).toBeInTheDocument()
    })
  })

  it('renders property gallery', async () => {
    vi.mocked(SearchAdapter.getPropertyById).mockResolvedValue(mockProperty)

    render(<PropertyDetailPage />)

    await waitFor(() => {
      expect(screen.getByRole('region', { name: 'Property image gallery' })).toBeInTheDocument()
    })
  })

  it('renders property header', async () => {
    vi.mocked(SearchAdapter.getPropertyById).mockResolvedValue(mockProperty)

    render(<PropertyDetailPage />)

    await waitFor(() => {
      expect(screen.getByText('Test Property')).toBeInTheDocument()
    })
  })

  it('renders property description', async () => {
    vi.mocked(SearchAdapter.getPropertyById).mockResolvedValue(mockProperty)

    render(<PropertyDetailPage />)

    await waitFor(() => {
      expect(screen.getByText('Test description')).toBeInTheDocument()
    })
  })

  it('renders property amenities', async () => {
    vi.mocked(SearchAdapter.getPropertyById).mockResolvedValue(mockProperty)

    render(<PropertyDetailPage />)

    await waitFor(() => {
      expect(screen.getByText('Amenities')).toBeInTheDocument()
    })
  })

  it('renders property policies', async () => {
    vi.mocked(SearchAdapter.getPropertyById).mockResolvedValue(mockProperty)

    render(<PropertyDetailPage />)

    await waitFor(() => {
      expect(screen.getByText('Policies')).toBeInTheDocument()
      expect(screen.getByText('Check-in Policy')).toBeInTheDocument()
    })
  })

  it('renders nearby places', async () => {
    vi.mocked(SearchAdapter.getPropertyById).mockResolvedValue(mockProperty)

    render(<PropertyDetailPage />)

    await waitFor(() => {
      expect(screen.getByText('What\'s Nearby')).toBeInTheDocument()
    })
  })

  it('renders dining restaurants', async () => {
    vi.mocked(SearchAdapter.getPropertyById).mockResolvedValue(mockProperty)

    render(<PropertyDetailPage />)

    await waitFor(() => {
      expect(screen.getByText('Dining & Restaurants')).toBeInTheDocument()
    })
  })

  it('renders booking card with price', async () => {
    vi.mocked(SearchAdapter.getPropertyById).mockResolvedValue(mockProperty)

    render(<PropertyDetailPage />)

    await waitFor(() => {
      expect(screen.getByText(/\$100/)).toBeInTheDocument()
      expect(screen.getByText('per night')).toBeInTheDocument()
    })
  })

  it('updates document title with property name', async () => {
    vi.mocked(SearchAdapter.getPropertyById).mockResolvedValue(mockProperty)

    render(<PropertyDetailPage />)

    await waitFor(() => {
      expect(document.title).toBe('Test Property | TICKBRON')
    })
  })

  it('has back to search button in error state', async () => {
    vi.mocked(SearchAdapter.getPropertyById).mockResolvedValue(null)

    render(<PropertyDetailPage />)

    await waitFor(() => {
      const backButton = screen.getByText('Back to Search')
      expect(backButton).toBeInTheDocument()
    })
  })

  it('calls SearchAdapter with correct property ID', async () => {
    vi.mocked(SearchAdapter.getPropertyById).mockResolvedValue(mockProperty)

    render(<PropertyDetailPage />)

    await waitFor(() => {
      expect(SearchAdapter.getPropertyById).toHaveBeenCalledWith(1)
    })
  })
})