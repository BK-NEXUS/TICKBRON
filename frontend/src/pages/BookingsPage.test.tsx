import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import { BookingsPage } from './BookingsPage'
import { accountAdapter } from '../adapters/accountAdapter'
import { AuthProvider, useAuth } from '../contexts/AuthContext'
import { settle } from '../test/utils'

// Mock adapters
vi.mock('../adapters/accountAdapter')
vi.mock('../contexts/AuthContext', () => ({
  useAuth: vi.fn(),
  AuthProvider: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}))

const mockAccountAdapter = accountAdapter as {
  getBookings: ReturnType<typeof vi.fn>
}
const mockUseAuth = useAuth as ReturnType<typeof vi.fn>

const mockBookings = [
  {
    id: 1,
    guest: 1,
    guest_name: 'John Doe',
    property: 1,
    property_name: 'Test Property 1',
    status: 'confirmed',
    payment_status: 'paid',
    check_in: '2025-02-01',
    check_out: '2025-02-05',
    number_of_nights: 4,
    guest_count: 2,
    total_price: 400,
    currency: 'USD',
    confirmation_code: 'ABC123',
    booking_items: [],
    created_at: '2025-01-15T10:00:00Z',
    updated_at: '2025-01-15T10:00:00Z',
  },
  {
    id: 2,
    guest: 1,
    guest_name: 'John Doe',
    property: 2,
    property_name: 'Test Property 2',
    status: 'completed',
    payment_status: 'paid',
    check_in: '2025-01-10',
    check_out: '2025-01-15',
    number_of_nights: 5,
    guest_count: 2,
    total_price: 500,
    currency: 'USD',
    confirmation_code: 'DEF456',
    booking_items: [],
    created_at: '2025-01-01T10:00:00Z',
    updated_at: '2025-01-16T10:00:00Z',
  },
  {
    id: 3,
    guest: 1,
    guest_name: 'John Doe',
    property: 3,
    property_name: 'Test Property 3',
    status: 'cancelled',
    payment_status: 'refunded',
    check_in: '2025-01-20',
    check_out: '2025-01-25',
    number_of_nights: 5,
    guest_count: 2,
    total_price: 500,
    currency: 'USD',
    confirmation_code: 'GHI789',
    cancelled_at: '2025-01-18T10:00:00Z',
    cancellation_reason: 'Changed plans',
    booking_items: [],
    created_at: '2025-01-15T10:00:00Z',
    updated_at: '2025-01-18T10:00:00Z',
  },
]

const renderWithRouter = (component: React.ReactElement) => {
  return render(
    <MemoryRouter initialEntries={[{ pathname: '/bookings' }]}>
      <AuthProvider>
        <Routes>
          <Route path="/bookings" element={component} />
          <Route path="/login" element={<div>Login Page</div>} />
          <Route path="/" element={<div>Home Page</div>} />
          <Route path="/property/:id" element={<div>Property Page</div>} />
        </Routes>
      </AuthProvider>
    </MemoryRouter>
  )
}

describe('BookingsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // Mock clipboard API
    Object.assign(navigator, {
      clipboard: {
        writeText: vi.fn().mockResolvedValue(undefined),
      },
    })
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

      renderWithRouter(<BookingsPage />)

      await waitFor(() => {
        expect(screen.getByText('Sign in required')).toBeInTheDocument()
      })
      expect(screen.getByText('Please sign in to view your booking history.')).toBeInTheDocument()
      expect(screen.getByText('Sign In')).toBeInTheDocument()
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

      mockAccountAdapter.getBookings.mockImplementation(() => new Promise(() => {}))

      renderWithRouter(<BookingsPage />)

      expect(screen.getByText('Loading bookings...')).toBeInTheDocument()
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

      mockAccountAdapter.getBookings.mockResolvedValue({
        data: null,
        error: 'Network error',
      })

      renderWithRouter(<BookingsPage />)

      await waitFor(() => {
        expect(screen.getByText('Network error')).toBeInTheDocument()
      })
      expect(screen.getByText('Try Again')).toBeInTheDocument()
    })
  })

  describe('Empty state', () => {
    it('should show empty state when no bookings', async () => {
      mockUseAuth.mockReturnValue({
        user: { id: 1, email: 'test@example.com' },
        isAuthenticated: true,
        isLoading: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        refreshUser: vi.fn(),
      })

      mockAccountAdapter.getBookings.mockResolvedValue({
        data: [],
        error: null,
      })

      renderWithRouter(<BookingsPage />)

      await waitFor(() => {
        expect(screen.getByText('No bookings yet')).toBeInTheDocument()
      })
      expect(screen.getByText('Start exploring amazing properties and book your first stay.')).toBeInTheDocument()
      expect(screen.getByText('Search Properties')).toBeInTheDocument()
    })
  })

  describe('Bookings list', () => {
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

      mockAccountAdapter.getBookings.mockResolvedValue({
        data: mockBookings,
        error: null,
      })
    })

    it('should render bookings list', async () => {
      renderWithRouter(<BookingsPage />)

      await waitFor(() => {
        expect(screen.getByText('My Bookings')).toBeInTheDocument()
      })
      expect(screen.getByText('Test Property 1')).toBeInTheDocument()
      expect(screen.getByText('Test Property 2')).toBeInTheDocument()
      expect(screen.getByText('Test Property 3')).toBeInTheDocument()
    })

    it('should display booking details', async () => {
      renderWithRouter(<BookingsPage />)

      await waitFor(() => {
        expect(screen.getByText('Test Property 1')).toBeInTheDocument()
      })

      expect(screen.getByText('ABC123')).toBeInTheDocument()
      expect(screen.getAllByText('Booking Reference:')).toHaveLength(3)
      expect(screen.getAllByText('Check-in:')).toHaveLength(3)
      // Dates are shown for people, not as ISO strings (E2E UX 13)
      expect(screen.getByText('Feb 1, 2025')).toBeInTheDocument()
      expect(screen.queryByText('2025-02-01')).not.toBeInTheDocument()
      expect(screen.getAllByText('Check-out:')).toHaveLength(3)
      expect(screen.getByText('Feb 5, 2025')).toBeInTheDocument()
      expect(screen.getAllByText('Nights:')).toHaveLength(3)
      expect(screen.getByText('4')).toBeInTheDocument()
      expect(screen.getAllByText('Guests:')).toHaveLength(3)
      expect(screen.getAllByText('2')).toHaveLength(3)
      expect(screen.getAllByText('Total:')).toHaveLength(3)
      expect(screen.getByText('$400 USD')).toBeInTheDocument()
    })

    it('should display copy button for booking reference code', async () => {
      renderWithRouter(<BookingsPage />)

      await waitFor(() => {
        expect(screen.getByText('Test Property 1')).toBeInTheDocument()
      })

      const copyButtons = screen.getAllByTitle('Copy booking reference code')
      expect(copyButtons).toHaveLength(3)
    })

    it('should copy booking reference code when copy button is clicked', async () => {
      renderWithRouter(<BookingsPage />)

      await waitFor(() => {
        expect(screen.getByText('Test Property 1')).toBeInTheDocument()
      })

      const copyButtons = screen.getAllByTitle('Copy booking reference code')
      fireEvent.click(copyButtons[0])

      expect(navigator.clipboard.writeText).toHaveBeenCalledWith('ABC123')
      // Let the page finish loading inside the test
      await settle()
    })

    it('should show copied state after successful copy', async () => {
      renderWithRouter(<BookingsPage />)

      await waitFor(() => {
        expect(screen.getByText('Test Property 1')).toBeInTheDocument()
      })

      const copyButtons = screen.getAllByTitle('Copy booking reference code')
      fireEvent.click(copyButtons[0])

      await waitFor(() => {
        expect(document.querySelectorAll('.booking-card-copy-btn .lucide-check')).toHaveLength(1)
      })
    })

    it('should display booking status', async () => {
      renderWithRouter(<BookingsPage />)

      await waitFor(() => {
        expect(screen.getByText('Test Property 1')).toBeInTheDocument()
      })

      // Filter buttons (4) + copy buttons (3) = 7 total buttons
      expect(screen.getAllByRole('button')).toHaveLength(7)
    })

    it('should display payment status', async () => {
      renderWithRouter(<BookingsPage />)

      await waitFor(() => {
        expect(screen.getByText('Test Property 1')).toBeInTheDocument()
      })

      expect(screen.getAllByText(/Payment:/)).toHaveLength(3)
    })
  })

  describe('Filter functionality', () => {
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

      mockAccountAdapter.getBookings.mockResolvedValue({
        data: mockBookings,
        error: null,
      })
    })

    it('should filter by all bookings', async () => {
      renderWithRouter(<BookingsPage />)

      await waitFor(() => {
        expect(screen.getByText('My Bookings')).toBeInTheDocument()
      })

      expect(screen.getByText('Test Property 1')).toBeInTheDocument()
      expect(screen.getByText('Test Property 2')).toBeInTheDocument()
      expect(screen.getByText('Test Property 3')).toBeInTheDocument()
      expect(screen.getAllByText('ABC123')).toHaveLength(1)
      expect(screen.getAllByText('DEF456')).toHaveLength(1)
      expect(screen.getAllByText('GHI789')).toHaveLength(1)
      expect(screen.getAllByText('Booking Reference:')).toHaveLength(3)
    })

    it('should filter by upcoming bookings', async () => {
      renderWithRouter(<BookingsPage />)

      await waitFor(() => {
        expect(screen.getByText('My Bookings')).toBeInTheDocument()
      })

      const upcomingButton = screen.getByLabelText('Show upcoming bookings')
      fireEvent.click(upcomingButton)

      await waitFor(() => {
        expect(mockAccountAdapter.getBookings).toHaveBeenCalled()
        const lastCall = mockAccountAdapter.getBookings.mock.calls[mockAccountAdapter.getBookings.mock.calls.length - 1]
        expect(lastCall[0]).toBe('confirmed')
      })
    })

    it('should filter by completed bookings', async () => {
      renderWithRouter(<BookingsPage />)

      await waitFor(() => {
        expect(screen.getByText('My Bookings')).toBeInTheDocument()
      })

      const completedButton = screen.getByLabelText('Show completed bookings')
      fireEvent.click(completedButton)

      await waitFor(() => {
        expect(mockAccountAdapter.getBookings).toHaveBeenCalled()
        const lastCall = mockAccountAdapter.getBookings.mock.calls[mockAccountAdapter.getBookings.mock.calls.length - 1]
        expect(lastCall[0]).toBe('completed')
      })
    })

    it('should filter by cancelled bookings', async () => {
      renderWithRouter(<BookingsPage />)

      await waitFor(() => {
        expect(screen.getByText('My Bookings')).toBeInTheDocument()
      })

      const cancelledButton = screen.getByLabelText('Show cancelled bookings')
      fireEvent.click(cancelledButton)

      await waitFor(() => {
        expect(mockAccountAdapter.getBookings).toHaveBeenCalled()
        const lastCall = mockAccountAdapter.getBookings.mock.calls[mockAccountAdapter.getBookings.mock.calls.length - 1]
        expect(lastCall[0]).toBe('cancelled')
      })
    })
  })
})
