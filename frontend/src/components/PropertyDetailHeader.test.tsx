import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { PropertyDetailHeader } from './PropertyDetailHeader'
import { Property } from '../adapters/searchAdapter'

describe('PropertyDetailHeader', () => {
  const mockProperty: Property = {
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
        name: 'Test Property Name',
        description: 'Test description',
      },
    ],
    policies: [],
    rating: 4.5,
    review_count: 100,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  }

  it('renders the property name', () => {
    render(<PropertyDetailHeader property={mockProperty} />)
    
    const title = screen.getByText('Test Property Name')
    expect(title).toBeInTheDocument()
  })

  it('renders the property location', () => {
    render(<PropertyDetailHeader property={mockProperty} />)
    
    const location = screen.getByText('Test City, Test Country')
    expect(location).toBeInTheDocument()
  })

  it('renders the rating when available', () => {
    render(<PropertyDetailHeader property={mockProperty} />)
    
    const rating = screen.getByText('★ 4.5')
    expect(rating).toBeInTheDocument()
  })

  it('renders the review count', () => {
    render(<PropertyDetailHeader property={mockProperty} />)
    
    const reviews = screen.getByText('(100 reviews)')
    expect(reviews).toBeInTheDocument()
  })

  it('renders the property type', () => {
    render(<PropertyDetailHeader property={mockProperty} />)
    
    const propertyType = screen.getByText('Apartment')
    expect(propertyType).toBeInTheDocument()
  })

  it('renders the guest capacity', () => {
    render(<PropertyDetailHeader property={mockProperty} />)
    
    const guests = screen.getByText('4')
    expect(guests).toBeInTheDocument()
  })

  it('renders the bedroom count', () => {
    render(<PropertyDetailHeader property={mockProperty} />)
    
    const bedrooms = screen.getAllByText('2')
    expect(bedrooms.length).toBeGreaterThan(0)
  })

  it('renders the bathroom count', () => {
    render(<PropertyDetailHeader property={mockProperty} />)
    
    const bathrooms = screen.getByText('1')
    expect(bathrooms).toBeInTheDocument()
  })

  it('handles missing rating gracefully', () => {
    const propertyWithoutRating = { ...mockProperty, rating: undefined }
    render(<PropertyDetailHeader property={propertyWithoutRating} />)
    
    const rating = screen.queryByText(/★/)
    expect(rating).not.toBeInTheDocument()
  })

  it('handles missing translation gracefully', () => {
    const propertyWithoutTranslation = { 
      ...mockProperty, 
      translations: [] 
    }
    render(<PropertyDetailHeader property={propertyWithoutTranslation} />)
    
    const title = screen.getByText('Property')
    expect(title).toBeInTheDocument()
  })

  it('renders meta information labels', () => {
    render(<PropertyDetailHeader property={mockProperty} />)
    
    expect(screen.getByText('Property Type')).toBeInTheDocument()
    expect(screen.getByText('Guests')).toBeInTheDocument()
    expect(screen.getByText('Bedrooms')).toBeInTheDocument()
    expect(screen.getByText('Bathrooms')).toBeInTheDocument()
  })

  it('renders header with proper semantic structure', () => {
    const { container } = render(<PropertyDetailHeader property={mockProperty} />)
    
    const header = container.querySelector('header')
    expect(header).toBeInTheDocument()
    expect(header).toHaveClass('property-detail-header')
  })
})