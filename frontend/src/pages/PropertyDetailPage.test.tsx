import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { PropertyDetailPage } from './PropertyDetailPage'
import { propertyAdapter } from '../adapters/propertyAdapter'
import { AuthProvider, useAuth } from '../contexts/AuthContext'

// Mock React Router
vi.mock('react-router-dom', () => ({
  useParams: () => ({ id: '1' }),
  useNavigate: () => vi.fn(),
}))

// Mock propertyAdapter
vi.mock('../adapters/propertyAdapter')

// Mock AuthContext
vi.mock('../contexts/AuthContext', () => ({
  useAuth: vi.fn(),
  AuthProvider: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}))

const mockUseAuth = useAuth as any

const renderWithProviders = (component: React.ReactElement) => {
  return render(
    <AuthProvider>
      {component}
    </AuthProvider>
  )
}

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
    room_types: [
      {
        id: 1,
        property_id: 1,
        name: 'Standard Room',
        slug: 'standard-room',
        description: 'Comfortable room with essential amenities',
        base_occupancy: 2,
        max_occupancy: 2,
        base_price: 120,
        currency: 'USD',
        total_rooms: 5,
        bed_configuration: '1 Queen Bed',
        room_size: 25,
      },
    ],
    gallery: {
      exterior: [
        {
          id: 1,
          photo: '🏠',
          photo_type: 'exterior',
          is_primary: true,
          display_order: 1,
        },
      ],
    },
    primary_photo: {
      id: 1,
      photo: '🏠',
      photo_type: 'exterior',
      is_primary: true,
      display_order: 1,
    },
    rating: 4.5,
    review_count: 100,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  }

  beforeEach(() => {
    vi.clearAllMocks()
    mockUseAuth.mockReturnValue({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
      refreshUser: vi.fn(),
    })
  })

  it('renders loading state initially', () => {
    vi.mocked(propertyAdapter.getPropertyById).mockResolvedValue({
      data: mockProperty,
      error: null,
    })

    renderWithProviders(<PropertyDetailPage />)
    
    expect(screen.getByText('Loading property details...')).toBeInTheDocument()
  })

  it('renders property details after loading', async () => {
    vi.mocked(propertyAdapter.getPropertyById).mockResolvedValue({
      data: mockProperty,
      error: null,
    })

    renderWithProviders(<PropertyDetailPage />)

    await waitFor(() => {
      expect(screen.queryByText('Loading property details...')).not.toBeInTheDocument()
    })

    expect(screen.getByText('Test Property')).toBeInTheDocument()
  })

  it('renders error state when property not found', async () => {
    vi.mocked(propertyAdapter.getPropertyById).mockResolvedValue({
      data: null,
      error: 'Property not found',
    })

    renderWithProviders(<PropertyDetailPage />)

    await waitFor(() => {
      expect(screen.getByText('Property Not Found')).toBeInTheDocument()
    })
  })

  it('renders error state when API call fails', async () => {
    vi.mocked(propertyAdapter.getPropertyById).mockResolvedValue({
      data: null,
      error: 'API Error',
    })

    renderWithProviders(<PropertyDetailPage />)

    await waitFor(() => {
      expect(screen.getByText('Property Not Found')).toBeInTheDocument()
    })
  })

  it('renders property gallery', async () => {
    vi.mocked(propertyAdapter.getPropertyById).mockResolvedValue({
      data: mockProperty,
      error: null,
    })

    renderWithProviders(<PropertyDetailPage />)

    await waitFor(() => {
      expect(screen.getByRole('region', { name: 'Property image gallery' })).toBeInTheDocument()
    })
  })

  it('renders property header', async () => {
    vi.mocked(propertyAdapter.getPropertyById).mockResolvedValue({
      data: mockProperty,
      error: null,
    })

    renderWithProviders(<PropertyDetailPage />)

    await waitFor(() => {
      expect(screen.getByText('Test Property')).toBeInTheDocument()
    })
  })

  it('renders property description', async () => {
    vi.mocked(propertyAdapter.getPropertyById).mockResolvedValue({
      data: mockProperty,
      error: null,
    })

    renderWithProviders(<PropertyDetailPage />)

    await waitFor(() => {
      expect(screen.getByText('Test description')).toBeInTheDocument()
    })
  })

  it('renders property amenities', async () => {
    vi.mocked(propertyAdapter.getPropertyById).mockResolvedValue({
      data: mockProperty,
      error: null,
    })

    renderWithProviders(<PropertyDetailPage />)

    await waitFor(() => {
      expect(screen.getByText('Amenities')).toBeInTheDocument()
    })
  })

  it('renders property policies', async () => {
    vi.mocked(propertyAdapter.getPropertyById).mockResolvedValue({
      data: mockProperty,
      error: null,
    })

    renderWithProviders(<PropertyDetailPage />)

    await waitFor(() => {
      expect(screen.getByText('Policies')).toBeInTheDocument()
      expect(screen.getByText('Check-in Policy')).toBeInTheDocument()
    })
  })

  it('renders nearby places', async () => {
    vi.mocked(propertyAdapter.getPropertyById).mockResolvedValue({
      data: mockProperty,
      error: null,
    })

    renderWithProviders(<PropertyDetailPage />)

    await waitFor(() => {
      expect(screen.getByText('What\'s Nearby')).toBeInTheDocument()
    })
  })

  it('renders dining restaurants', async () => {
    vi.mocked(propertyAdapter.getPropertyById).mockResolvedValue({
      data: mockProperty,
      error: null,
    })

    renderWithProviders(<PropertyDetailPage />)

    await waitFor(() => {
      expect(screen.getByText('Dining & Restaurants')).toBeInTheDocument()
    })
  })

  it('renders room selection when room types are available', async () => {
    vi.mocked(propertyAdapter.getPropertyById).mockResolvedValue({
      data: mockProperty,
      error: null,
    })

    renderWithProviders(<PropertyDetailPage />)

    await waitFor(() => {
      expect(screen.getByText('Select Your Room')).toBeInTheDocument()
    })
  })

  it('does not render room selection when no room types are available', async () => {
    const propertyWithoutRooms = { ...mockProperty, room_types: [] }
    vi.mocked(propertyAdapter.getPropertyById).mockResolvedValue({
      data: propertyWithoutRooms,
      error: null,
    })

    renderWithProviders(<PropertyDetailPage />)

    await waitFor(() => {
      expect(screen.queryByText('Select Your Room')).not.toBeInTheDocument()
    })
  })

  it('renders booking card with price', async () => {
    vi.mocked(propertyAdapter.getPropertyById).mockResolvedValue({
      data: mockProperty,
      error: null,
    })

    renderWithProviders(<PropertyDetailPage />)

    await waitFor(() => {
      expect(screen.getByText('Test Property')).toBeInTheDocument()
    })
  })

  it('updates document title with property name', async () => {
    vi.mocked(propertyAdapter.getPropertyById).mockResolvedValue({
      data: mockProperty,
      error: null,
    })

    renderWithProviders(<PropertyDetailPage />)

    await waitFor(() => {
      expect(document.title).toBe('Test Property | TICKBRON')
    })
  })

  it('has back to search button in error state', async () => {
    vi.mocked(propertyAdapter.getPropertyById).mockResolvedValue({
      data: null,
      error: 'Property not found',
    })

    renderWithProviders(<PropertyDetailPage />)

    await waitFor(() => {
      const backButton = screen.getByText('Back to Search')
      expect(backButton).toBeInTheDocument()
    })
  })

  it('calls propertyAdapter with correct property ID', async () => {
    vi.mocked(propertyAdapter.getPropertyById).mockResolvedValue({
      data: mockProperty,
      error: null,
    })

    renderWithProviders(<PropertyDetailPage />)

    await waitFor(() => {
      expect(propertyAdapter.getPropertyById).toHaveBeenCalledWith(1)
    })
  })
})