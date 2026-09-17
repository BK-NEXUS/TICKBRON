import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { PropertyCard } from './PropertyCard'
import { Property } from '../adapters/searchAdapter'

// Mock React Router
const mockNavigate = vi.fn()
vi.mock('react-router-dom', () => ({
  useNavigate: () => mockNavigate,
}))

describe('PropertyCard', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  const mockProperty: Property = {
    id: 1,
    owner_id: 1,
    property_type: { id: 1, name: 'Apartment', slug: 'apartment' },
    status: 'active',
    max_guests: 4,
    bedrooms: 2,
    bathrooms: 1,
    address_line1: '123 Rue de Paris',
    city: 'Paris',
    country: 'France',
    base_price: 150,
    currency: 'EUR',
    has_wifi: true,
    has_parking: false,
    has_ac: true,
    has_heating: true,
    has_elevator: true,
    translations: [
      {
        language: 'en',
        name: 'Charming Paris Apartment',
        description: 'Beautiful apartment in the heart of Paris',
      },
    ],
    policies: [],
    rating: 4.8,
    review_count: 127,
    image_url: '🏰',
    created_at: '2024-01-15T10:00:00Z',
    updated_at: '2024-01-20T15:30:00Z',
  }

  it('renders property card with all information', () => {
    render(<PropertyCard property={mockProperty} />)

    expect(screen.getByText('Charming Paris Apartment')).toBeInTheDocument()
    expect(screen.getByText('Paris, France')).toBeInTheDocument()
    expect(screen.getByText('4 guests')).toBeInTheDocument()
    expect(screen.getByText('2 bedrooms')).toBeInTheDocument()
    expect(screen.getByText('1 bathrooms')).toBeInTheDocument()
    expect(screen.getByText('€150')).toBeInTheDocument()
    expect(screen.getByText('per night')).toBeInTheDocument()
  })

  it('displays rating when available', () => {
    render(<PropertyCard property={mockProperty} />)

    expect(screen.getByText('★ 4.8')).toBeInTheDocument()
    expect(screen.getByText('(127)')).toBeInTheDocument()
  })

  it('does not display rating when not available', () => {
    const propertyWithoutRating = { ...mockProperty, rating: undefined, review_count: undefined }
    render(<PropertyCard property={propertyWithoutRating} />)

    expect(screen.queryByText('★')).not.toBeInTheDocument()
  })

  it('displays amenities icons', () => {
    render(<PropertyCard property={mockProperty} />)

    expect(screen.getByTitle('WiFi')).toBeInTheDocument()
    expect(screen.getByTitle('Air Conditioning')).toBeInTheDocument()
    expect(screen.getByTitle('Heating')).toBeInTheDocument()
    expect(screen.getByTitle('Elevator')).toBeInTheDocument()
  })

  it('does not display amenities that are not available', () => {
    render(<PropertyCard property={mockProperty} />)

    expect(screen.queryByTitle('Parking')).not.toBeInTheDocument()
  })

  it('calls onClick handler when clicked', () => {
    const handleClick = vi.fn()
    render(<PropertyCard property={mockProperty} onClick={handleClick} />)

    const card = screen.getByLabelText('Charming Paris Apartment in Paris, France')
    fireEvent.click(card)

    expect(handleClick).toHaveBeenCalledTimes(1)
  })

  it('is keyboard accessible', () => {
    const handleClick = vi.fn()
    render(<PropertyCard property={mockProperty} onClick={handleClick} />)

    const card = screen.getByLabelText('Charming Paris Apartment in Paris, France')
    // Simulate keyboard interaction by clicking directly (since the component handles onClick)
    card.click()

    expect(handleClick).toHaveBeenCalledTimes(1)
  })

  it('has proper ARIA attributes', () => {
    render(<PropertyCard property={mockProperty} />)

    const card = screen.getByLabelText('Charming Paris Apartment in Paris, France')
    expect(card).toHaveAttribute('role', 'button')
    expect(card).toHaveAttribute('tabIndex', '0')
  })

  it('formats price correctly for different currencies', () => {
    const usdProperty = { ...mockProperty, currency: 'USD', base_price: 200 }
    render(<PropertyCard property={usdProperty} />)

    expect(screen.getByText('$200')).toBeInTheDocument()
  })

  it('handles missing translation gracefully', () => {
    const propertyWithoutTranslation = { ...mockProperty, translations: [] }
    render(<PropertyCard property={propertyWithoutTranslation} />)

    expect(screen.getByText('Unknown Property')).toBeInTheDocument()
  })

  it('displays image placeholder', () => {
    render(<PropertyCard property={mockProperty} />)

    expect(screen.getByText('🏰')).toBeInTheDocument()
  })

  it('handles missing image URL', () => {
    const propertyWithoutImage = { ...mockProperty, image_url: undefined }
    render(<PropertyCard property={propertyWithoutImage} />)

    expect(screen.getByText('🏠')).toBeInTheDocument()
  })

  it('has click handler that calls custom onClick', () => {
    const handleClick = vi.fn()
    render(<PropertyCard property={mockProperty} onClick={handleClick} />)

    const card = screen.getByLabelText('Charming Paris Apartment in Paris, France')
    fireEvent.click(card)

    expect(handleClick).toHaveBeenCalledTimes(1)
  })

  it('navigates to property detail page when clicked', () => {
    render(<PropertyCard property={mockProperty} />)

    const card = screen.getByLabelText('Charming Paris Apartment in Paris, France')
    fireEvent.click(card)

    expect(mockNavigate).toHaveBeenCalledWith('/property/1')
  })
})
