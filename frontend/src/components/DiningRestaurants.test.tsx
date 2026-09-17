import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { DiningRestaurants } from './DiningRestaurants'
import { Restaurant } from '../adapters/searchAdapter'

describe('DiningRestaurants', () => {
  const mockRestaurants: Restaurant[] = [
    {
      id: 1,
      name: 'Le Bernardin',
      cuisine: 'French',
      distance: 0.2,
      distance_unit: 'km',
      rating: 4.9,
      price_range: '$$$$',
      address: '155 W 51st St',
    },
    {
      id: 2,
      name: "Joe's Pizza",
      cuisine: 'Italian',
      distance: 0.1,
      distance_unit: 'km',
      rating: 4.5,
      price_range: '$',
      address: '7 Carmine St',
    },
    {
      id: 3,
      name: "Xi'an Famous Foods",
      cuisine: 'Chinese',
      distance: 0.3,
      distance_unit: 'km',
      rating: 4.7,
      price_range: '$$',
      address: 'multiple locations',
    },
  ]

  it('renders empty state when no restaurants provided', () => {
    render(<DiningRestaurants restaurants={[]} />)
    
    expect(screen.getByText('No restaurant information available')).toBeInTheDocument()
  })

  it('renders dining restaurants section title', () => {
    render(<DiningRestaurants restaurants={mockRestaurants} />)
    
    expect(screen.getByText('Dining & Restaurants')).toBeInTheDocument()
  })

  it('renders restaurant items with correct information', () => {
    render(<DiningRestaurants restaurants={mockRestaurants} />)
    
    expect(screen.getByText('Le Bernardin')).toBeInTheDocument()
    expect(screen.getByText("Joe's Pizza")).toBeInTheDocument()
    expect(screen.getByText("Xi'an Famous Foods")).toBeInTheDocument()
  })

  it('renders restaurant cuisines', () => {
    render(<DiningRestaurants restaurants={mockRestaurants} />)
    
    expect(screen.getByText('French')).toBeInTheDocument()
    expect(screen.getByText('Italian')).toBeInTheDocument()
    expect(screen.getByText('Chinese')).toBeInTheDocument()
  })

  it('renders restaurant distances with units', () => {
    render(<DiningRestaurants restaurants={mockRestaurants} />)
    
    expect(screen.getByText('0.2 km')).toBeInTheDocument()
    expect(screen.getByText('0.1 km')).toBeInTheDocument()
    expect(screen.getByText('0.3 km')).toBeInTheDocument()
  })

  it('renders restaurant ratings when available', () => {
    render(<DiningRestaurants restaurants={mockRestaurants} />)
    
    expect(screen.getByText('★ 4.9')).toBeInTheDocument()
    expect(screen.getByText('★ 4.5')).toBeInTheDocument()
    expect(screen.getByText('★ 4.7')).toBeInTheDocument()
  })

  it('renders restaurant price ranges', () => {
    render(<DiningRestaurants restaurants={mockRestaurants} />)
    
    expect(screen.getByText('$$$$')).toBeInTheDocument()
    expect(screen.getByText('$')).toBeInTheDocument()
    expect(screen.getByText('$$')).toBeInTheDocument()
  })

  it('renders formatted price range labels', () => {
    render(<DiningRestaurants restaurants={mockRestaurants} />)
    
    const priceLabels = screen.getAllByText(/Fine dining|Budget-friendly|Moderate/).filter(el => el.className === 'dining-restaurant-item-price-label')
    expect(priceLabels.some(el => el.textContent === 'Fine dining')).toBe(true)
    expect(priceLabels.some(el => el.textContent === 'Budget-friendly')).toBe(true)
    expect(priceLabels.some(el => el.textContent === 'Moderate')).toBe(true)
  })

  it('renders restaurant addresses when available', () => {
    render(<DiningRestaurants restaurants={mockRestaurants} />)
    
    expect(screen.getByText('155 W 51st St')).toBeInTheDocument()
    expect(screen.getByText('7 Carmine St')).toBeInTheDocument()
    expect(screen.getByText('multiple locations')).toBeInTheDocument()
  })

  it('sorts restaurants by distance (ascending)', () => {
    render(<DiningRestaurants restaurants={mockRestaurants} />)
    
    const restaurantElements = screen.getAllByTestId(/dining-restaurant-item/i)
    expect(restaurantElements[0]).toHaveTextContent("Joe's Pizza")
    expect(restaurantElements[1]).toHaveTextContent('Le Bernardin')
    expect(restaurantElements[2]).toHaveTextContent("Xi'an Famous Foods")
  })

  it('handles restaurants without rating', () => {
    const restaurantsWithoutRating: Restaurant[] = [
      {
        id: 1,
        name: 'Unknown Restaurant',
        cuisine: 'Unknown',
        distance: 1.0,
        distance_unit: 'km',
        price_range: '$$',
      },
    ]
    
    render(<DiningRestaurants restaurants={restaurantsWithoutRating} />)
    
    expect(screen.getByText('Unknown Restaurant')).toBeInTheDocument()
    expect(screen.queryByText(/★/)).not.toBeInTheDocument()
  })

  it('handles restaurants without address', () => {
    const restaurantsWithoutAddress: Restaurant[] = [
      {
        id: 1,
        name: 'Restaurant Without Address',
        cuisine: 'Unknown',
        distance: 1.0,
        distance_unit: 'km',
        rating: 4.0,
        price_range: '$$',
      },
    ]
    
    render(<DiningRestaurants restaurants={restaurantsWithoutAddress} />)
    
    expect(screen.getByText('Restaurant Without Address')).toBeInTheDocument()
  })

  it('formats price range labels correctly', () => {
    const allPriceRanges: Restaurant[] = [
      { id: 1, name: 'Budget Place', cuisine: 'Test', distance: 1, distance_unit: 'km', price_range: '$' },
      { id: 2, name: 'Moderate Place', cuisine: 'Test', distance: 1, distance_unit: 'km', price_range: '$$' },
      { id: 3, name: 'Expensive Place', cuisine: 'Test', distance: 1, distance_unit: 'km', price_range: '$$$' },
      { id: 4, name: 'Fine Dining Place', cuisine: 'Test', distance: 1, distance_unit: 'km', price_range: '$$$$' },
    ]
    
    render(<DiningRestaurants restaurants={allPriceRanges} />)
    
    expect(screen.getByText('Budget-friendly')).toBeInTheDocument()
    expect(screen.getByText('Moderate')).toBeInTheDocument()
    expect(screen.getByText('Expensive')).toBeInTheDocument()
    expect(screen.getByText('Fine dining')).toBeInTheDocument()
  })
})
