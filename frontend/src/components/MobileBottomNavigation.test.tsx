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
    const { container } = render(
      <MemoryRouter>
        <MobileBottomNavigation />
      </MemoryRouter>
    )

    expect(container.querySelector('.lucide-search')).toBeInTheDocument()
    expect(container.querySelector('.lucide-calendar-days')).toBeInTheDocument()
    expect(container.querySelector('.lucide-heart')).toBeInTheDocument()
    expect(container.querySelector('.lucide-user')).toBeInTheDocument()
  })

  it('has proper accessibility attributes', () => {
    const { container } = render(
      <MemoryRouter>
        <MobileBottomNavigation />
      </MemoryRouter>
    )

    const nav = screen.getByRole('navigation')
    expect(nav).toHaveAttribute('aria-label', 'Main navigation')

    const icons = container.querySelectorAll('.mobile-bottom-nav-icon')
    expect(icons).toHaveLength(4)
    icons.forEach(icon => {
      expect(icon).toHaveAttribute('aria-hidden', 'true')
    })
  })
})
