import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { BookingsPage } from './BookingsPage'

describe('BookingsPage', () => {
  it('renders empty state with correct content', () => {
    render(
      <MemoryRouter>
        <BookingsPage />
      </MemoryRouter>
    )

    expect(screen.getByText('📅')).toBeInTheDocument()
    expect(screen.getByText('No bookings yet')).toBeInTheDocument()
    expect(screen.getByText('Start exploring amazing properties and book your first stay.')).toBeInTheDocument()
    expect(screen.getByText('Search Properties')).toBeInTheDocument()
  })

  it('has proper page structure', () => {
    const { container } = render(
      <MemoryRouter>
        <BookingsPage />
      </MemoryRouter>
    )

    expect(container.querySelector('.bookings-page')).toBeInTheDocument()
    expect(container.querySelector('.container')).toBeInTheDocument()
  })

  it('links to home page via CTA', () => {
    render(
      <MemoryRouter>
        <BookingsPage />
      </MemoryRouter>
    )

    const ctaLink = screen.getByText('Search Properties')
    expect(ctaLink).toHaveAttribute('href', '/')
  })
})
