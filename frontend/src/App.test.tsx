import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import App from './App'

// Mock the lazy-loaded components
vi.mock('./pages/HomePage', () => ({
  HomePage: () => <div>Home Page</div>,
}))

vi.mock('./pages/SearchResultsPage', () => ({
  SearchResultsPage: () => <div>Search Results Page</div>,
}))

vi.mock('./pages/PropertyDetailPage', () => ({
  PropertyDetailPage: () => <div>Property Detail Page</div>,
}))

vi.mock('./pages/BookingPage', () => ({
  BookingPage: () => <div>Booking Page</div>,
}))

vi.mock('./pages/LoginPage', () => ({
  LoginPage: () => <div>Login Page</div>,
}))

vi.mock('./pages/RegisterPage', () => ({
  RegisterPage: () => <div>Register Page</div>,
}))

vi.mock('./pages/BookingsPage', () => ({
  BookingsPage: () => <div>Bookings Page</div>,
}))

vi.mock('./pages/FavoritesPage', () => ({
  FavoritesPage: () => <div>Favorites Page</div>,
}))

vi.mock('./pages/ProfilePage', () => ({
  ProfilePage: () => <div>Profile Page</div>,
}))

vi.mock('./pages/PartnerDashboardPage', () => ({
  PartnerDashboardPage: () => <div>Partner Dashboard Page</div>,
}))

vi.mock('./pages/AdminDashboardPage', () => ({
  AdminDashboardPage: () => <div>Admin Dashboard Page</div>,
}))

vi.mock('./pages/NotFoundPage', () => ({
  NotFoundPage: () => <div>Not Found Page</div>,
}))

describe('App', () => {
  it('renders loading state initially', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <App />
      </MemoryRouter>
    )

    expect(screen.getByText('Loading...')).toBeInTheDocument()
  })

  it('renders home page after loading', async () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <App />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('Home Page')).toBeInTheDocument()
    })
  })

  it('renders search results page for /search route', async () => {
    render(
      <MemoryRouter initialEntries={['/search']}>
        <App />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('Search Results Page')).toBeInTheDocument()
    })
  })

  it('renders property detail page for /property/:id route', async () => {
    render(
      <MemoryRouter initialEntries={['/property/123']}>
        <App />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('Property Detail Page')).toBeInTheDocument()
    })
  })

  it('renders booking page for /booking route', async () => {
    render(
      <MemoryRouter initialEntries={['/booking']}>
        <App />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('Booking Page')).toBeInTheDocument()
    })
  })

  it('renders login page for /login route', async () => {
    render(
      <MemoryRouter initialEntries={['/login']}>
        <App />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('Login Page')).toBeInTheDocument()
    })
  })

  it('renders register page for /register route', async () => {
    render(
      <MemoryRouter initialEntries={['/register']}>
        <App />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('Register Page')).toBeInTheDocument()
    })
  })

  it('renders bookings page for /bookings route', async () => {
    render(
      <MemoryRouter initialEntries={['/bookings']}>
        <App />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('Bookings Page')).toBeInTheDocument()
    })
  })

  it('renders favorites page for /favorites route', async () => {
    render(
      <MemoryRouter initialEntries={['/favorites']}>
        <App />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('Favorites Page')).toBeInTheDocument()
    })
  })

  it('renders profile page for /profile route', async () => {
    render(
      <MemoryRouter initialEntries={['/profile']}>
        <App />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('Profile Page')).toBeInTheDocument()
    })
  })

  it('renders partner dashboard page for /partner route', async () => {
    render(
      <MemoryRouter initialEntries={['/partner']}>
        <App />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('Partner Dashboard Page')).toBeInTheDocument()
    })
  })

  it('renders admin dashboard page for /admin route', async () => {
    render(
      <MemoryRouter initialEntries={['/admin']}>
        <App />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('Admin Dashboard Page')).toBeInTheDocument()
    })
  })

  it('renders not found page for unknown routes', async () => {
    render(
      <MemoryRouter initialEntries={['/unknown-route']}>
        <App />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('Not Found Page')).toBeInTheDocument()
    })
  })
})
