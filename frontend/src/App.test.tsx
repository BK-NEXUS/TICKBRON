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
