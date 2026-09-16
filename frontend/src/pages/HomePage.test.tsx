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

  it('renders the search input', () => {
    render(
      <BrowserRouter>
        <HomePage />
      </BrowserRouter>
    )
    expect(screen.getByPlaceholderText('Where are you going?')).toBeInTheDocument()
    expect(screen.getByText('Search')).toBeInTheDocument()
  })

  it('renders the features section', () => {
    render(
      <BrowserRouter>
        <HomePage />
      </BrowserRouter>
    )
    expect(screen.getByText('Why Choose TICKBRON?')).toBeInTheDocument()
    expect(screen.getByText('Verified Properties')).toBeInTheDocument()
    expect(screen.getByText('Secure Payments')).toBeInTheDocument()
    expect(screen.getByText('24/7 Support')).toBeInTheDocument()
  })
})
