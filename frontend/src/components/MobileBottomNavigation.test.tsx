import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { MobileBottomNavigation } from './MobileBottomNavigation'

describe('MobileBottomNavigation', () => {
  it('renders all 4 navigation items', () => {
    render(
      <MemoryRouter>
        <MobileBottomNavigation />
      </MemoryRouter>
    )

    expect(screen.getByRole('navigation', { name: 'Main navigation' })).toBeInTheDocument()
    expect(screen.getByText('Search')).toBeInTheDocument()
    expect(screen.getByText('My Bookings')).toBeInTheDocument()
    expect(screen.getByText('Favorites')).toBeInTheDocument()
    expect(screen.getByText('Profile')).toBeInTheDocument()
  })

  it('highlights the active route', () => {
    render(
      <MemoryRouter initialEntries={['/bookings']}>
        <MobileBottomNavigation />
      </MemoryRouter>
    )

    const bookingsLink = screen.getByText('My Bookings').closest('a')
    expect(bookingsLink).toHaveClass('mobile-bottom-nav-link--active')
    expect(bookingsLink).toHaveAttribute('aria-current', 'page')
  })

  it('shows search as active on home route', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <MobileBottomNavigation />
      </MemoryRouter>
    )

    const searchLink = screen.getByText('Search').closest('a')
    expect(searchLink).toHaveClass('mobile-bottom-nav-link--active')
    expect(searchLink).toHaveAttribute('aria-current', 'page')
  })

  it('includes icons for each navigation item', () => {
    render(
      <MemoryRouter>
        <MobileBottomNavigation />
      </MemoryRouter>
    )

    expect(screen.getByText('🔍')).toBeInTheDocument()
    expect(screen.getByText('📅')).toBeInTheDocument()
    expect(screen.getByText('❤️')).toBeInTheDocument()
    expect(screen.getByText('👤')).toBeInTheDocument()
  })

  it('has proper accessibility attributes', () => {
    render(
      <MemoryRouter>
        <MobileBottomNavigation />
      </MemoryRouter>
    )

    const nav = screen.getByRole('navigation')
    expect(nav).toHaveAttribute('aria-label', 'Main navigation')

    const icons = screen.getAllByText(/🔍|📅|❤️|👤/)
    icons.forEach(icon => {
      expect(icon).toHaveAttribute('aria-hidden', 'true')
    })
  })
})
