import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { NearbyPlaces } from './NearbyPlaces'
import { NearbyPlace } from '../adapters/searchAdapter'

describe('NearbyPlaces', () => {
  const mockPlaces: NearbyPlace[] = [
    {
      id: 1,
      name: 'Central Park',
      category: 'Park',
      distance: 0.3,
      distance_unit: 'km',
      rating: 4.8,
      address: 'Manhattan, NY',
    },
    {
      id: 2,
      name: 'Times Square',
      category: 'Landmark',
      distance: 1.2,
      distance_unit: 'km',
      rating: 4.5,
      address: 'Manhattan, NY',
    },
    {
      id: 3,
      name: 'Grand Central Terminal',
      category: 'Transportation',
      distance: 0.8,
      distance_unit: 'km',
      rating: 4.7,
    },
  ]

  it('renders empty state when no places provided', () => {
    render(<NearbyPlaces places={[]} />)
    
    expect(screen.getByText('No nearby places information available')).toBeInTheDocument()
  })

  it('renders nearby places section title', () => {
    render(<NearbyPlaces places={mockPlaces} />)
    
    expect(screen.getByText("What's Nearby")).toBeInTheDocument()
  })

  it('renders place items with correct information', () => {
    render(<NearbyPlaces places={mockPlaces} />)
    
    expect(screen.getByText('Central Park')).toBeInTheDocument()
    expect(screen.getByText('Times Square')).toBeInTheDocument()
    expect(screen.getByText('Grand Central Terminal')).toBeInTheDocument()
  })

  it('renders place categories', () => {
    render(<NearbyPlaces places={mockPlaces} />)
    
    expect(screen.getByText('Park')).toBeInTheDocument()
    expect(screen.getByText('Landmark')).toBeInTheDocument()
    expect(screen.getByText('Transportation')).toBeInTheDocument()
  })

  it('renders place distances with units', () => {
    render(<NearbyPlaces places={mockPlaces} />)
    
    expect(screen.getByText('0.3 km')).toBeInTheDocument()
    expect(screen.getByText('1.2 km')).toBeInTheDocument()
    expect(screen.getByText('0.8 km')).toBeInTheDocument()
  })

  it('renders place ratings when available', () => {
    render(<NearbyPlaces places={mockPlaces} />)
    
    expect(screen.getByText('★ 4.8')).toBeInTheDocument()
    expect(screen.getByText('★ 4.5')).toBeInTheDocument()
    expect(screen.getByText('★ 4.7')).toBeInTheDocument()
  })

  it('renders place addresses when available', () => {
    render(<NearbyPlaces places={mockPlaces} />)
    
    expect(screen.getAllByText('Manhattan, NY').length).toBeGreaterThan(0)
  })

  it('sorts places by distance (ascending)', () => {
    render(<NearbyPlaces places={mockPlaces} />)
    
    const placeElements = screen.getAllByTestId(/nearby-place-item/i)
    expect(placeElements[0]).toHaveTextContent('Central Park')
    expect(placeElements[1]).toHaveTextContent('Grand Central Terminal')
    expect(placeElements[2]).toHaveTextContent('Times Square')
  })

  it('handles places without rating', () => {
    const placesWithoutRating: NearbyPlace[] = [
      {
        id: 1,
        name: 'Unknown Place',
        category: 'Other',
        distance: 1.0,
        distance_unit: 'km',
      },
    ]
    
    render(<NearbyPlaces places={placesWithoutRating} />)
    
    expect(screen.getByText('Unknown Place')).toBeInTheDocument()
    expect(screen.queryByText(/★/)).not.toBeInTheDocument()
  })

  it('handles places without address', () => {
    const placesWithoutAddress: NearbyPlace[] = [
      {
        id: 1,
        name: 'Place Without Address',
        category: 'Other',
        distance: 1.0,
        distance_unit: 'km',
        rating: 4.0,
      },
    ]
    
    const { container } = render(<NearbyPlaces places={placesWithoutAddress} />)
    
    expect(screen.getByText('Place Without Address')).toBeInTheDocument()
    // Verify no address paragraph elements are rendered
    const addressElements = container.querySelectorAll('.nearby-place-item-address')
    expect(addressElements.length).toBe(0)
  })
})
