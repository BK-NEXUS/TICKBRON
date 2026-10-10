import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { propertyAdapter } from '../adapters/propertyAdapter'
import { BrowserRouter, MemoryRouter, Routes, Route } from 'react-router-dom'
import { HomePage } from './HomePage'

// The home page asks the backend for banners; these tests are about the rest of the page,
// so the request never answers (no state change after a synchronous test has ended)
vi.mock('../adapters/promotionAdapter', () => ({
  promotionAdapter: { getHomePromotions: vi.fn(() => new Promise(() => {})), trackClick: vi.fn() },
}))

// The hotel lists and the property-type strip ask the backend too: no answer in these tests either
vi.mock('../adapters/propertyAdapter', () => ({
  propertyAdapter: {
    searchProperties: vi.fn(() => new Promise(() => {})),
    getFilterOptions: vi.fn(() => new Promise(() => {})),
  },
}))

describe('HomePage', () => {
  it('renders the hero section', () => {
    render(
      <BrowserRouter>
        <HomePage />
      </BrowserRouter>
    )
    expect(screen.getByText('Find Your Perfect Stay')).toBeInTheDocument()
    expect(screen.getByText('Discover unique homes and experiences around the world')).toBeInTheDocument()
  })

  it('renders the search form with proper accessibility', () => {
    render(
      <BrowserRouter>
        <HomePage />
      </BrowserRouter>
    )
    const destinationInput = screen.getByLabelText('Destination')
    expect(destinationInput).toBeInTheDocument()
    expect(destinationInput).toHaveAttribute('type', 'text')
    expect(destinationInput).toHaveAttribute('placeholder', 'Where are you going?')
  })

  it('renders the search form button', () => {
    render(
      <BrowserRouter>
        <HomePage />
      </BrowserRouter>
    )
    const searchButton = screen.getByRole('button', { name: 'Search' })
    expect(searchButton).toBeInTheDocument()
  })

  it('renders search form with all required fields', () => {
    render(
      <BrowserRouter>
        <HomePage />
      </BrowserRouter>
    )
    expect(screen.getByLabelText('Destination')).toBeInTheDocument()
    expect(screen.getByLabelText('Check-in')).toBeInTheDocument()
    expect(screen.getByLabelText('Check-out')).toBeInTheDocument()
    expect(screen.getByLabelText('Guests')).toBeInTheDocument()
    expect(screen.getByLabelText('Adults')).toBeInTheDocument()
    expect(screen.getByLabelText('Children')).toBeInTheDocument()
    expect(screen.getByLabelText('Rooms')).toBeInTheDocument()
  })

  it('has no invented numbers, destinations or testimonials any more', () => {
    render(
      <BrowserRouter>
        <HomePage />
      </BrowserRouter>
    )
    for (const fake of ['50K+', '100K+', '120+', 'Paris', 'Tokyo', 'Sarah Johnson', 'Michael Chen', 'Join millions']) {
      expect(screen.queryByText(new RegExp(fake))).not.toBeInTheDocument()
    }
  })

  it('does not offer "List Your Property": owner accounts are created by a super-admin', () => {
    render(
      <BrowserRouter>
        <HomePage />
      </BrowserRouter>
    )
    expect(screen.getByText('Browse all hotels')).toBeInTheDocument()
    expect(screen.queryByText(/list your property/i)).not.toBeInTheDocument()
  })

  it('Browse all hotels opens the list of all properties', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/search" element={<h1>All properties page</h1>} />
        </Routes>
      </MemoryRouter>
    )
    fireEvent.click(screen.getByText('Browse all hotels'))
    expect(screen.getByRole('heading', { name: 'All properties page' })).toBeInTheDocument()
  })

  it('asks for the top rated and the cheapest hotels, eight each', () => {
    render(
      <BrowserRouter>
        <HomePage />
      </BrowserRouter>
    )
    expect(propertyAdapter.searchProperties).toHaveBeenCalledWith({ sort: 'rating', page_size: 8 })
    expect(propertyAdapter.searchProperties).toHaveBeenCalledWith({ sort: 'price_asc', page_size: 8 })
    expect(propertyAdapter.getFilterOptions).toHaveBeenCalled()
  })

  it('maintains semantic HTML structure', () => {
    render(
      <BrowserRouter>
        <HomePage />
      </BrowserRouter>
    )
    // Check for proper heading hierarchy
    const headings = screen.getAllByRole('heading')
    expect(headings.length).toBeGreaterThan(0)
    
    // Check for proper section structure
    const homePage = screen.getByText('Find Your Perfect Stay').closest('.home-page')
    expect(homePage).toBeInTheDocument()
  })
})
