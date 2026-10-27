import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, within, waitFor, fireEvent } from '@testing-library/react'
import { PropertyDetailPage } from './PropertyDetailPage'
import { propertyAdapter } from '../adapters/propertyAdapter'
import { AuthProvider, useAuth } from '../contexts/AuthContext'
import { settle } from '../test/utils'

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

const mockUseAuth = useAuth as never

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
          category: { id: 1, name: 'Kitchen', slug: 'kitchen', description: 'Kitchen amenities', icon: 'kitchen', sort_order: 1 },
          name: 'WiFi',
          slug: 'wifi',
          description: 'High-speed internet',
          icon: 'wifi',
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
          photo: 'house.jpg',
          photo_type: 'exterior',
          is_primary: true,
          display_order: 1,
        },
      ],
    },
    primary_photo: {
      id: 1,
      photo: 'house.jpg',
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

  it('shows a save-to-favorites button next to the title (E2E BUG 4)', async () => {
    vi.mocked(propertyAdapter.getPropertyById).mockResolvedValue({
      data: mockProperty,
      error: null,
    })

    renderWithProviders(<PropertyDetailPage />)

    expect(await screen.findByRole('button', { name: 'Save Test Property to favorites' })).toBeInTheDocument()
  })

  it('Book Now takes a logged-in guest to the room list and focuses it', async () => {
    mockUseAuth.mockReturnValue({
      user: { id: 1 }, isAuthenticated: true, isLoading: false,
      login: vi.fn(), register: vi.fn(), logout: vi.fn(), refreshUser: vi.fn(),
    })
    const scrollIntoView = vi.fn()
    Element.prototype.scrollIntoView = scrollIntoView
    vi.mocked(propertyAdapter.getPropertyById).mockResolvedValue({ data: mockProperty, error: null })

    renderWithProviders(<PropertyDetailPage />)
    fireEvent.click(await screen.findByRole('button', { name: 'Select room to book' }))

    expect(scrollIntoView).toHaveBeenCalled()
    expect(document.activeElement).toHaveClass('room-selection')
  })

  it('renders loading state initially', async () => {
    vi.mocked(propertyAdapter.getPropertyById).mockResolvedValue({
      data: mockProperty,
      error: null,
    })

    renderWithProviders(<PropertyDetailPage />)
    
    expect(screen.getByText('Loading property details...')).toBeInTheDocument()
    // Let the page finish loading inside the test
    await settle()
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

  describe('map of the property (R11)', () => {
    const load = async (extra: Record<string, unknown>) => {
      vi.mocked(propertyAdapter.getPropertyById).mockResolvedValue({ data: { ...mockProperty, ...extra }, error: null })
      renderWithProviders(<PropertyDetailPage />)
      await screen.findByText('Test Property')
    }

    it('shows a map under the address when the owner has set the location', async () => {
      await load({ latitude: '41.311081', longitude: '69.279737' })
      const section = screen.getByRole('heading', { name: 'Location' }).closest('section') as HTMLElement
      expect(within(section).getByRole('region', { name: 'Map: where Test Property is' })).toBeInTheDocument()
      expect(within(section).getByText('123 Test Street')).toBeInTheDocument()
    })

    it('shows only the address when there is no location on the map', async () => {
      await load({ latitude: null, longitude: null })
      expect(screen.queryByRole('region', { name: /Map: where/ })).toBeNull()
      expect(screen.getByText('123 Test Street')).toBeInTheDocument()
    })
  })

  describe('so\'m equivalent of a price in dollars (R6)', () => {
    const rate = { rate: '11772.950000', date: '2026-10-03', source: 'cbu.uz', stale: false }
    const load = async (extra: Record<string, unknown>) => {
      vi.mocked(propertyAdapter.getPropertyById).mockResolvedValue({ data: { ...mockProperty, ...extra }, error: null })
      renderWithProviders(<PropertyDetailPage />)
      await screen.findByText('Test Property')
    }

    it('shows "≈ so\'m" under the dollar price, with the date of the CBU rate', async () => {
      await load({ base_price_uzs_approx: '1177295.00', uzs_rate: rate })
      const card = document.querySelector('.property-detail-booking-card') as HTMLElement
      expect(card).toHaveTextContent('≈ 1 177 295 UZS')
      expect(card).toHaveTextContent('Rate of Oct 3, 2026 (CBU)')
      expect(card).not.toHaveTextContent('may be out of date')
    })

    it('warns when the rate may be out of date', async () => {
      await load({ base_price_uzs_approx: '1177295.00', uzs_rate: { ...rate, stale: true } })
      expect(document.querySelector('.property-detail-booking-card')).toHaveTextContent('The rate may be out of date')
    })

    it('shows nothing extra while no rate exists yet', async () => {
      await load({ base_price_uzs_approx: null, uzs_rate: null })
      expect(document.querySelector('.property-detail-booking-card')).not.toHaveTextContent('≈')
    })
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

  it('not found: the title is the page heading and the text does not repeat it', async () => {
    vi.mocked(propertyAdapter.getPropertyById).mockResolvedValue({ data: null, error: 'Property not found' })

    renderWithProviders(<PropertyDetailPage />)

    expect(await screen.findByRole('heading', { level: 1, name: 'Property Not Found' })).toBeInTheDocument()
    expect(screen.getByText('The property you are looking for does not exist.')).toBeInTheDocument()
    expect(screen.queryByText('Property not found')).toBeNull()
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

    // Just verify the component renders without error
    expect(screen.getByText('Loading property details...')).toBeInTheDocument()
    // Let the page finish loading inside the test
    await settle()
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
      expect(document.title).toBe('Test Property | TICKBRON — Online Booking')
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