import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, fireEvent, within } from '@testing-library/react'
import { MemoryRouter, Routes, Route, useLocation } from 'react-router-dom'
import { BreadcrumbProvider, Breadcrumbs, usePageTrail } from './Breadcrumbs'
import { rememberSearch, searchUrlForCity } from '../utils/searchFilters'

function Where() {
  const location = useLocation()
  return <div data-testid="where">{location.pathname + location.search}</div>
}

function PropertyPage() {
  usePageTrail([
    { label: 'Tashkent', to: searchUrlForCity('Tashkent') },
    { label: 'Hotel Tashkent' },
  ])
  return <h1>Property</h1>
}

const renderAt = (entries: string[], index = entries.length - 1) =>
  render(
    <MemoryRouter initialEntries={entries} initialIndex={index}>
      <BreadcrumbProvider>
        <Breadcrumbs />
        <Where />
        <Routes>
          <Route path="/" element={<h1>Home</h1>} />
          <Route path="/search" element={<h1>Search</h1>} />
          <Route path="/bookings" element={<h1>Bookings</h1>} />
          <Route path="/admin/support" element={<h1>Support</h1>} />
          <Route path="/property/:id" element={<PropertyPage />} />
        </Routes>
      </BreadcrumbProvider>
    </MemoryRouter>
  )

const trail = () => within(screen.getByRole('navigation', { name: 'Breadcrumb' }))

describe('Breadcrumbs', () => {
  beforeEach(() => {
    window.sessionStorage.clear()
  })

  it('is not shown on the home page', () => {
    renderAt(['/'])
    expect(screen.queryByRole('navigation', { name: 'Breadcrumb' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Back' })).not.toBeInTheDocument()
  })

  it('shows Home › page for a simple page', () => {
    renderAt(['/bookings'])
    expect(trail().getByRole('link', { name: 'Home' })).toHaveAttribute('href', '/')
    expect(trail().getByText('My Bookings')).toHaveAttribute('aria-current', 'page')
  })

  it('the login page has a trail back home', () => {
    render(
      <MemoryRouter initialEntries={['/login']}>
        <Breadcrumbs />
      </MemoryRouter>
    )
    expect(trail().getByRole('link', { name: 'Home' })).toHaveAttribute('href', '/')
    expect(trail().getByText('Sign In')).toHaveAttribute('aria-current', 'page')
    expect(screen.getByRole('button', { name: 'Back' })).toBeInTheDocument()
  })

  it('names nested admin pages', () => {
    renderAt(['/admin/support'])
    expect(trail().getByRole('link', { name: 'Admin Dashboard' })).toHaveAttribute('href', '/admin')
    expect(trail().getByText('Support Lookup')).toHaveAttribute('aria-current', 'page')
  })

  it('shows the destination on the search page', () => {
    renderAt(['/search?destination=Samarkand'])
    expect(trail().getByText('Samarkand')).toHaveAttribute('aria-current', 'page')
  })

  it('lets a page give its own trail: Home › Tashkent › Hotel', () => {
    renderAt(['/property/3'])
    expect(trail().getByRole('link', { name: 'Home' })).toBeInTheDocument()
    expect(trail().getByRole('link', { name: 'Tashkent' })).toHaveAttribute('href', '/search?destination=Tashkent')
    expect(trail().getByText('Hotel Tashkent')).toHaveAttribute('aria-current', 'page')
  })

  it('the city crumb returns to the last search for that city, with its filters', () => {
    rememberSearch('destination=Tashkent&guests=2&features=wifi&sort=price_asc')
    renderAt(['/property/3'])
    expect(trail().getByRole('link', { name: 'Tashkent' })).toHaveAttribute(
      'href', '/search?destination=Tashkent&guests=2&features=wifi&sort=price_asc'
    )
  })

  it('a remembered search for another city is not used', () => {
    rememberSearch('destination=Bukhara&features=wifi')
    renderAt(['/property/3'])
    expect(trail().getByRole('link', { name: 'Tashkent' })).toHaveAttribute('href', '/search?destination=Tashkent')
  })

  it('Back goes to the previous page, keeping its filters', () => {
    renderAt(['/search?destination=Tashkent&features=wifi', '/property/3'])
    fireEvent.click(screen.getByRole('button', { name: 'Back' }))
    expect(screen.getByTestId('where')).toHaveTextContent('/search?destination=Tashkent&features=wifi')
  })

  it('Back without history goes one level up the trail', () => {
    renderAt(['/property/3'])
    fireEvent.click(screen.getByRole('button', { name: 'Back' }))
    expect(screen.getByTestId('where')).toHaveTextContent('/search?destination=Tashkent')
  })

  it('Back on a top-level page without history goes home', () => {
    renderAt(['/bookings'])
    fireEvent.click(screen.getByRole('button', { name: 'Back' }))
    expect(screen.getByTestId('where')).toHaveTextContent(/^\/$/)
  })

  it('in-page levels: a crumb can be a button, and Back steps up one level inside the page', () => {
    const toProperties = vi.fn()
    const toRooms = vi.fn()
    function Dashboard() {
      usePageTrail([
        { label: 'Partner Dashboard', onClick: toProperties },
        { label: 'Hotel Tashkent', onClick: toRooms },
        { label: 'Deluxe King' },
      ])
      return <h1>Dashboard</h1>
    }
    render(
      <MemoryRouter initialEntries={['/', '/partner']} initialIndex={1}>
        <BreadcrumbProvider>
          <Breadcrumbs />
          <Where />
          <Routes>
            <Route path="/partner" element={<Dashboard />} />
          </Routes>
        </BreadcrumbProvider>
      </MemoryRouter>
    )

    fireEvent.click(trail().getByRole('button', { name: 'Partner Dashboard' }))
    expect(toProperties).toHaveBeenCalledTimes(1)

    fireEvent.click(screen.getByRole('button', { name: 'Back' }))
    expect(toRooms).toHaveBeenCalledTimes(1)
    // Still on the page: Back did not leave the dashboard
    expect(screen.getByTestId('where')).toHaveTextContent('/partner')
  })
})
