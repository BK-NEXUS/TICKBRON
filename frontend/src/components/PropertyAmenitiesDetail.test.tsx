import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { PropertyAmenitiesDetail } from './PropertyAmenitiesDetail'
import { PropertyAmenity } from '../adapters/searchAdapter'

describe('PropertyAmenitiesDetail', () => {
  const mockAmenities: PropertyAmenity[] = [
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
    {
      amenity: {
        id: 2,
        category: { id: 1, name: 'Kitchen', slug: 'kitchen', description: 'Kitchen amenities', icon: 'kitchen', sort_order: 1 },
        name: 'Kitchen',
        slug: 'kitchen',
        description: 'Full kitchen',
        icon: 'kitchen',
        is_searchable: true,
        sort_order: 2,
      },
      is_available: true,
    },
    {
      amenity: {
        id: 3,
        category: { id: 2, name: 'Bathroom', slug: 'bathroom', description: 'Bathroom amenities', icon: 'bathroom', sort_order: 2 },
        name: 'Air Conditioning',
        slug: 'ac',
        description: 'Climate control',
        icon: 'ac',
        is_searchable: true,
        sort_order: 3,
      },
      is_available: false,
      notes: 'Under maintenance',
    },
  ]

  it('renders empty state when no amenities provided', () => {
    render(<PropertyAmenitiesDetail amenities={[]} />)
    
    expect(screen.getByText('No amenities information available')).toBeInTheDocument()
  })

  it('renders amenities grouped by category', () => {
    render(<PropertyAmenitiesDetail amenities={mockAmenities} />)
    
    expect(screen.getByText('Amenities')).toBeInTheDocument()
    expect(screen.getAllByRole('heading', { level: 3 })[0]).toHaveTextContent('Kitchen')
    expect(screen.getAllByRole('heading', { level: 3 })[1]).toHaveTextContent('Bathroom')
  })

  it('renders amenity items with correct information', () => {
    render(<PropertyAmenitiesDetail amenities={mockAmenities} />)
    
    expect(screen.getByText('WiFi')).toBeInTheDocument()
    expect(screen.getByText('High-speed internet')).toBeInTheDocument()
    const amenityNames = screen.getAllByText(/WiFi|Kitchen/).filter(el => el.className === 'property-amenity-item-name')
    expect(amenityNames.some(el => el.textContent === 'Kitchen')).toBe(true)
    expect(screen.getByText('Full kitchen')).toBeInTheDocument()
  })

  it('renders unavailable amenities with status indicator', () => {
    render(<PropertyAmenitiesDetail amenities={mockAmenities} />)
    
    expect(screen.getByText('Air Conditioning')).toBeInTheDocument()
    expect(screen.getByText('Not available')).toBeInTheDocument()
  })

  it('renders amenity notes when provided', () => {
    render(<PropertyAmenitiesDetail amenities={mockAmenities} />)
    
    expect(screen.getByText('Note: Under maintenance')).toBeInTheDocument()
  })

  it('renders category icons', () => {
    const { container } = render(<PropertyAmenitiesDetail amenities={mockAmenities} />)
    
    expect(container.querySelector('.property-amenities-category-icon .lucide-utensils')).toBeInTheDocument()
    expect(container.querySelector('.property-amenities-category-icon .lucide-shower-head')).toBeInTheDocument()
  })

  it('renders amenity icons', () => {
    const { container } = render(<PropertyAmenitiesDetail amenities={mockAmenities} />)
    
    expect(container.querySelector('.property-amenity-item-icon .lucide-wifi')).toBeInTheDocument()
    expect(container.querySelector('.property-amenity-item-icon .lucide-snowflake')).toBeInTheDocument()
  })

  it('sorts amenities by category sort order', () => {
    render(<PropertyAmenitiesDetail amenities={mockAmenities} />)
    
    const categories = screen.getAllByRole('heading', { level: 3 })
    expect(categories[0]).toHaveTextContent('Kitchen')
    expect(categories[1]).toHaveTextContent('Bathroom')
  })

  it('sorts amenities within category by sort order', () => {
    render(<PropertyAmenitiesDetail amenities={mockAmenities} />)
    
    const amenityNames = screen.getAllByText(/WiFi|Kitchen/).filter(el => el.className === 'property-amenity-item-name')
    expect(amenityNames[0]).toHaveTextContent('WiFi')
    expect(amenityNames[1]).toHaveTextContent('Kitchen')
  })
})
