import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { HomePage } from './HomePage'

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

  it('renders the search input with proper accessibility', () => {
    render(
      <BrowserRouter>
        <HomePage />
      </BrowserRouter>
    )
    const searchInput = screen.getByLabelText('Search destination')
    expect(searchInput).toBeInTheDocument()
    expect(searchInput).toHaveAttribute('type', 'text')
    expect(searchInput).toHaveAttribute('placeholder', 'Where are you going?')
  })

  it('renders the search button', () => {
    render(
      <BrowserRouter>
        <HomePage />
      </BrowserRouter>
    )
    expect(screen.getByText('Search')).toBeInTheDocument()
  })

  it('renders hero statistics', () => {
    render(
      <BrowserRouter>
        <HomePage />
      </BrowserRouter>
    )
    expect(screen.getByText('50K+')).toBeInTheDocument()
    expect(screen.getByText('Properties Listed')).toBeInTheDocument()
    expect(screen.getByText('100K+')).toBeInTheDocument()
    expect(screen.getByText('Happy Guests')).toBeInTheDocument()
    expect(screen.getByText('120+')).toBeInTheDocument()
    expect(screen.getByText('Countries')).toBeInTheDocument()
    expect(screen.getByText('4.9')).toBeInTheDocument()
    expect(screen.getByText('Average Rating')).toBeInTheDocument()
  })

  it('renders the popular destinations section', () => {
    render(
      <BrowserRouter>
        <HomePage />
      </BrowserRouter>
    )
    expect(screen.getByText('Popular Destinations')).toBeInTheDocument()
    expect(screen.getByText('Explore our most sought-after locations')).toBeInTheDocument()
    expect(screen.getByText('Paris')).toBeInTheDocument()
    expect(screen.getByText('Tokyo')).toBeInTheDocument()
    expect(screen.getByText('New York')).toBeInTheDocument()
    expect(screen.getByText('London')).toBeInTheDocument()
  })

  it('renders destination property counts', () => {
    render(
      <BrowserRouter>
        <HomePage />
      </BrowserRouter>
    )
    expect(screen.getByText('1250 properties')).toBeInTheDocument()
    expect(screen.getByText('980 properties')).toBeInTheDocument()
    expect(screen.getByText('1100 properties')).toBeInTheDocument()
    expect(screen.getByText('890 properties')).toBeInTheDocument()
  })

  it('renders the property types section', () => {
    render(
      <BrowserRouter>
        <HomePage />
      </BrowserRouter>
    )
    expect(screen.getByText('Property Types')).toBeInTheDocument()
    expect(screen.getByText('Find the perfect accommodation for your needs')).toBeInTheDocument()
    expect(screen.getByText('Apartments')).toBeInTheDocument()
    expect(screen.getByText('Houses')).toBeInTheDocument()
    expect(screen.getByText('Villas')).toBeInTheDocument()
    expect(screen.getByText('Studios')).toBeInTheDocument()
  })

  it('renders property type descriptions', () => {
    render(
      <BrowserRouter>
        <HomePage />
      </BrowserRouter>
    )
    expect(screen.getByText('Modern city living spaces')).toBeInTheDocument()
    expect(screen.getByText('Spacious family homes')).toBeInTheDocument()
    expect(screen.getByText('Luxury vacation retreats')).toBeInTheDocument()
    expect(screen.getByText('Compact urban spaces')).toBeInTheDocument()
  })

  it('renders the enhanced features section', () => {
    render(
      <BrowserRouter>
        <HomePage />
      </BrowserRouter>
    )
    expect(screen.getByText('Why Choose TICKBRON?')).toBeInTheDocument()
    expect(screen.getByText('Experience the difference with our premium service')).toBeInTheDocument()
    expect(screen.getByText('Verified Properties')).toBeInTheDocument()
    expect(screen.getByText('Secure Payments')).toBeInTheDocument()
    expect(screen.getByText('24/7 Support')).toBeInTheDocument()
    expect(screen.getByText('Best Price Guarantee')).toBeInTheDocument()
    expect(screen.getByText('Global Coverage')).toBeInTheDocument()
    expect(screen.getByText('Easy Booking')).toBeInTheDocument()
  })

  it('renders the testimonials section', () => {
    render(
      <BrowserRouter>
        <HomePage />
      </BrowserRouter>
    )
    expect(screen.getByText('What Our Guests Say')).toBeInTheDocument()
    expect(screen.getByText('Real experiences from real travelers')).toBeInTheDocument()
    expect(screen.getByText('Sarah Johnson')).toBeInTheDocument()
    expect(screen.getByText('Michael Chen')).toBeInTheDocument()
    expect(screen.getByText('Emma Wilson')).toBeInTheDocument()
  })

  it('renders testimonial content', () => {
    render(
      <BrowserRouter>
        <HomePage />
      </BrowserRouter>
    )
    expect(screen.getByText('New York, USA')).toBeInTheDocument()
    expect(screen.getByText('Singapore')).toBeInTheDocument()
    expect(screen.getByText('London, UK')).toBeInTheDocument()
  })

  it('renders the CTA section', () => {
    render(
      <BrowserRouter>
        <HomePage />
      </BrowserRouter>
    )
    expect(screen.getByText('Ready to Start Your Journey?')).toBeInTheDocument()
    expect(screen.getByText('Join millions of travelers who trust TICKBRON for their accommodations')).toBeInTheDocument()
    expect(screen.getByText('Browse Properties')).toBeInTheDocument()
    expect(screen.getByText('List Your Property')).toBeInTheDocument()
  })

  it('renders CTA buttons with correct classes', () => {
    render(
      <BrowserRouter>
        <HomePage />
      </BrowserRouter>
    )
    const browseButton = screen.getByText('Browse Properties')
    const listButton = screen.getByText('List Your Property')
    expect(browseButton).toBeInTheDocument()
    expect(listButton).toBeInTheDocument()
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
