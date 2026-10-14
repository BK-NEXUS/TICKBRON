import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { EmptyState } from './EmptyState'

describe('EmptyState', () => {
  it('renders with all props', () => {
    render(
      <MemoryRouter>
        <EmptyState
          icon="ICON"
          title="No bookings yet"
          message="Start exploring amazing properties and book your first stay."
          ctaText="Search Properties"
          ctaLink="/"
        />
      </MemoryRouter>
    )

    expect(screen.getByText('ICON')).toBeInTheDocument()
    expect(screen.getByText('No bookings yet')).toBeInTheDocument()
    expect(screen.getByText('Start exploring amazing properties and book your first stay.')).toBeInTheDocument()
    expect(screen.getByText('Search Properties')).toBeInTheDocument()
  })

  it('renders as a link with correct href', () => {
    render(
      <MemoryRouter>
        <EmptyState
          icon="HEART-ICON"
          title="No favorites yet"
          message="Save your favorite properties to view them here."
          ctaText="Explore Properties"
          ctaLink="/search"
        />
      </MemoryRouter>
    )

    const ctaLink = screen.getByText('Explore Properties')
    expect(ctaLink).toHaveAttribute('href', '/search')
  })

  it('has proper accessibility attributes', () => {
    render(
      <MemoryRouter>
        <EmptyState
          icon="ICON"
          title="No bookings yet"
          message="Start exploring amazing properties and book your first stay."
          ctaText="Search Properties"
          ctaLink="/"
        />
      </MemoryRouter>
    )

    const emptyState = screen.getByRole('status')
    expect(emptyState).toHaveAttribute('aria-live', 'polite')

    const icon = screen.getByText('ICON')
    expect(icon).toHaveAttribute('aria-hidden', 'true')
  })

  it('applies correct CSS classes', () => {
    render(
      <MemoryRouter>
        <EmptyState
          icon="ICON"
          title="No bookings yet"
          message="Start exploring amazing properties and book your first stay."
          ctaText="Search Properties"
          ctaLink="/"
        />
      </MemoryRouter>
    )

    const emptyState = screen.getByRole('status')
    expect(emptyState).toHaveClass('empty-state')

    const title = screen.getByText('No bookings yet')
    expect(title).toHaveClass('empty-state-title')

    const message = screen.getByText('Start exploring amazing properties and book your first stay.')
    expect(message).toHaveClass('empty-state-message')

    const cta = screen.getByText('Search Properties')
    expect(cta).toHaveClass('btn', 'btn-primary', 'empty-state-cta')
  })

  it('renders its title as an h2 by default and as the page h1 when it is the whole screen', () => {
    const { rerender } = render(
      <MemoryRouter><EmptyState icon="i" title="Nothing yet" message="m" ctaText="Go" onClick={() => {}} /></MemoryRouter>,
    )
    expect(screen.getByRole('heading', { level: 2, name: 'Nothing yet' })).toBeInTheDocument()

    rerender(
      <MemoryRouter><EmptyState icon="i" title="Sign in required" message="m" ctaText="Go" onClick={() => {}} headingLevel={1} /></MemoryRouter>,
    )
    expect(screen.getByRole('heading', { level: 1, name: 'Sign in required' })).toBeInTheDocument()
  })
})
