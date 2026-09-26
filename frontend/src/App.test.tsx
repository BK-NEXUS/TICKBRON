import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import App from './App'

// Every module App.tsx loads with React.lazy. lazy() needs a default export,
// and tsc/vite build do not catch a missing one (the page only breaks at runtime).
const lazyModules = {
  HomePage: () => import('./pages/HomePage'),
  SearchResultsPage: () => import('./pages/SearchResultsPage'),
  PropertyDetailPage: () => import('./pages/PropertyDetailPage'),
  BookingPage: () => import('./pages/BookingPage'),
  LoginPage: () => import('./pages/LoginPage'),
  RegisterPage: () => import('./pages/RegisterPage'),
  BookingsPage: () => import('./pages/BookingsPage'),
  FavoritesPage: () => import('./pages/FavoritesPage'),
  ProfilePage: () => import('./pages/ProfilePage'),
  PartnerDashboardPage: () => import('./pages/PartnerDashboardPage'),
  AdminDashboardPage: () => import('./pages/AdminDashboardPage'),
  AdminCustomerProfile: () => import('./components/AdminCustomerProfile'),
  SupportLookupPage: () => import('./pages/SupportLookupPage'),
  NotFoundPage: () => import('./pages/NotFoundPage'),
}

describe('lazy-loaded pages', () => {
  it.each(Object.entries(lazyModules))('%s has a default export', async (name, load) => {
    const mod = (await load()) as Record<string, unknown>
    expect(typeof mod.default).toBe('function')
    expect(mod.default).toBe(mod[name])
  })
})

describe('App routing', () => {
  beforeEach(() => {
    // Anonymous visitor: /auth/me returns 401, everything else an empty list
    vi.stubGlobal('fetch', vi.fn(async (url: string) => {
      if (String(url).includes('/auth/me/')) {
        return new Response(JSON.stringify({ detail: 'Authentication credentials were not provided.' }), { status: 401 })
      }
      return new Response(JSON.stringify({ results: [], count: 0 }), { status: 200 })
    }))
    vi.spyOn(console, 'error').mockImplementation(() => {})
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    vi.restoreAllMocks()
    window.history.pushState({}, '', '/')
  })

  it.each([
    ['/login', /phone/i],
    ['/register', /register|sign up|create/i],
    ['/no-such-page', /404|not found/i],
  ])('renders %s without falling into the error boundary', async (path, expected) => {
    window.history.pushState({}, '', path)
    render(<App />)

    await waitFor(() => expect(screen.getAllByText(expected).length).toBeGreaterThan(0))
    expect(screen.queryByText('Something went wrong')).not.toBeInTheDocument()
  })
})

describe('Admin and partner route guards', () => {
  const baseUser = {
    id: 7, email: 'someone@example.com', first_name: '', last_name: '', full_name: 'Some One',
    is_active: true, date_joined: '2026-01-01T00:00:00Z', email_verified: false, two_factor_enabled: false,
  }
  const guest = { ...baseUser, role: null, is_staff: false, is_superuser: false }
  const owner = { ...baseUser, role: 'hotel-owner', is_staff: false, is_superuser: false }
  const staff = { ...baseUser, role: null, is_staff: true, is_superuser: false }

  const visitAs = (user: object | null, path: string) => {
    vi.stubGlobal('fetch', vi.fn(async (url: string) => {
      if (String(url).includes('/auth/me/')) {
        return user
          ? new Response(JSON.stringify(user), { status: 200 })
          : new Response(JSON.stringify({ detail: 'Authentication credentials were not provided.' }), { status: 401 })
      }
      return new Response(JSON.stringify({ results: [], count: 0 }), { status: 200 })
    }))
    window.history.pushState({}, '', path)
    render(<App />)
  }

  const expectAccessDenied = async () => {
    expect(await screen.findByRole('heading', { level: 1, name: 'Access Denied' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Back to Home' })).toHaveAttribute('href', '/')
  }

  beforeEach(() => {
    vi.spyOn(console, 'error').mockImplementation(() => {})
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    vi.restoreAllMocks()
    window.history.pushState({}, '', '/')
  })

  it.each(['/admin', '/admin/support', '/admin/customers/1', '/partner'])(
    'a regular user sees Access Denied on %s', async (path) => {
      visitAs(guest, path)
      await expectAccessDenied()
    })

  it.each(['/admin', '/admin/support', '/admin/customers/1', '/partner'])(
    'an anonymous visitor sees Access Denied with a sign-in link on %s', async (path) => {
      visitAs(null, path)
      await expectAccessDenied()
      expect(screen.getByRole('link', { name: 'Sign In' })).toHaveAttribute('href', '/login')
    })

  it.each(['/admin', '/admin/support', '/admin/customers/1'])(
    'a hotel owner sees Access Denied on %s', async (path) => {
      visitAs(owner, path)
      await expectAccessDenied()
    })

  it('a hotel owner can open the partner panel', async () => {
    visitAs(owner, '/partner')
    expect(await screen.findByRole('heading', { name: 'Partner Dashboard' })).toBeInTheDocument()
    expect(screen.queryByText('Access Denied')).not.toBeInTheDocument()
  })

  it.each([
    ['/admin', 'Admin Dashboard'],
    ['/partner', 'Partner Dashboard'],
  ])('staff can open %s', async (path, heading) => {
    visitAs(staff, path)
    expect(await screen.findByRole('heading', { name: heading })).toBeInTheDocument()
    expect(screen.queryByText('Access Denied')).not.toBeInTheDocument()
  })
})
