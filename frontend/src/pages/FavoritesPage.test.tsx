import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import { FavoritesPage } from './FavoritesPage'
import { accountAdapter } from '../adapters/accountAdapter'
import { AuthProvider, useAuth } from '../contexts/AuthContext'

// Mock adapters
vi.mock('../adapters/accountAdapter')
vi.mock('../contexts/AuthContext', () => ({
  useAuth: vi.fn(),
  AuthProvider: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}))

const mockAccountAdapter = accountAdapter as {
  getFavorites: ReturnType<typeof vi.fn>
  removeFavorite: ReturnType<typeof vi.fn>
}
const mockUseAuth = useAuth as ReturnType<typeof vi.fn>

// Backend shape of GET /api/v1/me/favorites/ (FavoriteSerializer)
const mockFavorites = [
  {
    id: 1,
    user: 1,
    property: 1,
    property_translations: [{ language: 'en', name: 'Test Property 1', description: '', address_line1: '1 Main St', city: 'Tashkent' }],
    property_city: 'Tashkent',
    property_country: 'Uzbekistan',
    property_base_price: '100.00',
    property_currency: 'USD',
    property_primary_photo: 'http://example.com/photo1.jpg',
    notes: 'Great place!',
    created_at: '2025-01-15T10:00:00Z',
  },
  {
    id: 2,
    user: 1,
    property: 2,
    property_translations: [{ language: 'en', name: 'Test Property 2', description: '', address_line1: '2 Main St', city: 'Samarkand' }],
    property_city: 'Samarkand',
    property_country: 'Uzbekistan',
    property_base_price: '150.00',
    property_currency: 'USD',
    property_primary_photo: null,
    notes: null,
    created_at: '2025-01-15T10:00:00Z',
  },
]

const renderWithRouter = (component: React.ReactElement) => {
  return render(
    <MemoryRouter initialEntries={[{ pathname: '/favorites' }]}>
      <AuthProvider>
        <Routes>
          <Route path="/favorites" element={component} />
          <Route path="/login" element={<div>Login Page</div>} />
          <Route path="/search" element={<div>Search Page</div>} />
          <Route path="/property/:id" element={<div>Property Page</div>} />
        </Routes>
      </AuthProvider>
    </MemoryRouter>
  )
}

describe('FavoritesPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Authentication redirect', () => {
    it('should redirect to login if not authenticated', async () => {
      mockUseAuth.mockReturnValue({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        refreshUser: vi.fn(),
      })

      renderWithRouter(<FavoritesPage />)

      await waitFor(() => {
        expect(screen.getByText('Sign in required')).toBeInTheDocument()
      })
      expect(screen.getByText('Please sign in to view your favorite properties.')).toBeInTheDocument()
      expect(screen.getByText('Sign In')).toBeInTheDocument()
    })
  })

  describe('Session check', () => {
    it('shows loading, not "Sign in required", while the session is still being checked', () => {
      mockUseAuth.mockReturnValue({
        user: null,
        isAuthenticated: false,
        isLoading: true,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        refreshUser: vi.fn(),
      })

      renderWithRouter(<FavoritesPage />)

      expect(screen.queryByText('Sign in required')).not.toBeInTheDocument()
      expect(screen.getByRole('status')).toBeInTheDocument()
    })
  })

  describe('Loading state', () => {
    it('should show loading state initially', () => {
      mockUseAuth.mockReturnValue({
        user: { id: 1, email: 'test@example.com' },
        isAuthenticated: true,
        isLoading: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        refreshUser: vi.fn(),
      })

      mockAccountAdapter.getFavorites.mockImplementation(() => new Promise(() => {}))

      renderWithRouter(<FavoritesPage />)

      expect(screen.getByText('Loading favorites...')).toBeInTheDocument()
    })
  })

  describe('Error state', () => {
    it('should show error state when API fails', async () => {
      mockUseAuth.mockReturnValue({
        user: { id: 1, email: 'test@example.com' },
        isAuthenticated: true,
        isLoading: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        refreshUser: vi.fn(),
      })

      mockAccountAdapter.getFavorites.mockResolvedValue({
        data: null,
        error: 'Network error',
      })

      renderWithRouter(<FavoritesPage />)

      await waitFor(() => {
        expect(screen.getByText('Network error')).toBeInTheDocument()
      })
      expect(screen.getByText('Try Again')).toBeInTheDocument()
    })
  })

  describe('Empty state', () => {
    it('should show empty state when no favorites', async () => {
      mockUseAuth.mockReturnValue({
        user: { id: 1, email: 'test@example.com' },
        isAuthenticated: true,
        isLoading: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        refreshUser: vi.fn(),
      })

      mockAccountAdapter.getFavorites.mockResolvedValue({
        data: [],
        error: null,
      })

      renderWithRouter(<FavoritesPage />)

      await waitFor(() => {
        expect(screen.getByText('No favorites yet')).toBeInTheDocument()
      })
      expect(screen.getByText('Save your favorite properties to view them here.')).toBeInTheDocument()
      expect(screen.getByText('Explore Properties')).toBeInTheDocument()
    })
  })

  describe('Favorites list', () => {
    beforeEach(() => {
      mockUseAuth.mockReturnValue({
        user: { id: 1, email: 'test@example.com' },
        isAuthenticated: true,
        isLoading: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        refreshUser: vi.fn(),
      })

      mockAccountAdapter.getFavorites.mockResolvedValue({
        data: mockFavorites,
        error: null,
      })
    })

    it('should render favorites list', async () => {
      renderWithRouter(<FavoritesPage />)

      await waitFor(() => {
        expect(screen.getByText('My Favorites')).toBeInTheDocument()
      })
      expect(screen.getByText('2 properties saved')).toBeInTheDocument()
      expect(screen.getByText('Test Property 1')).toBeInTheDocument()
      expect(screen.getByText('Test Property 2')).toBeInTheDocument()
    })

    it('should display property details', async () => {
      renderWithRouter(<FavoritesPage />)

      await waitFor(() => {
        expect(screen.getByText('Test Property 1')).toBeInTheDocument()
      })

      expect(screen.getByText('Tashkent, Uzbekistan')).toBeInTheDocument()
      expect(screen.getByText('$100 / night')).toBeInTheDocument()
      expect(screen.getByText('Great place!')).toBeInTheDocument()
    })

    it('should display property without photo', async () => {
      renderWithRouter(<FavoritesPage />)

      await waitFor(() => {
        expect(screen.getByText('Test Property 2')).toBeInTheDocument()
      })

      expect(screen.getByText('Samarkand, Uzbekistan')).toBeInTheDocument()
      expect(screen.getByText('$150 / night')).toBeInTheDocument()
    })

    it('should remove favorite when remove button clicked', async () => {
      mockAccountAdapter.removeFavorite.mockResolvedValue({
        data: null,
        error: null,
      })

      renderWithRouter(<FavoritesPage />)

      await waitFor(() => {
        expect(screen.getByText('Test Property 1')).toBeInTheDocument()
      })

      const removeButtons = screen.getAllByText('Remove')
      fireEvent.click(removeButtons[0])

      await waitFor(() => {
        expect(mockAccountAdapter.removeFavorite).toHaveBeenCalledWith(1)
      })
    })

    it('should show error when remove fails', async () => {
      mockAccountAdapter.removeFavorite.mockResolvedValue({
        data: null,
        error: 'Failed to remove',
      })

      renderWithRouter(<FavoritesPage />)

      await waitFor(() => {
        expect(screen.getByText('Test Property 1')).toBeInTheDocument()
      })

      const removeButtons = screen.getAllByText('Remove')
      fireEvent.click(removeButtons[0])

      await waitFor(() => {
        expect(screen.getByText('Failed to remove')).toBeInTheDocument()
      })
    })
  })
})
