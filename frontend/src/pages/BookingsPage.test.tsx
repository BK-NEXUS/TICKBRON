import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import { BookingsPage } from './BookingsPage'
import { accountAdapter } from '../adapters/accountAdapter'
import { AuthProvider, useAuth } from '../contexts/AuthContext'
import { settle, pageOf } from '../test/utils'
import { bookingAdapter } from '../adapters/bookingAdapter'
import { addDays, businessToday } from '../utils/dates'

// Mock adapters
vi.mock('../adapters/accountAdapter')
vi.mock('../adapters/bookingAdapter', async (importOriginal) => ({
  ...(await importOriginal<typeof import('../adapters/bookingAdapter')>()),
  bookingAdapter: { cancelBooking: vi.fn() },
}))
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
        data: pageOf([]),
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

  describe('Empty screen wording', () => {
    const signedIn = (user: object) => mockUseAuth.mockReturnValue({
      user, isAuthenticated: true, isLoading: false, login: vi.fn(), register: vi.fn(), logout: vi.fn(), refreshUser: vi.fn(),
    })

    it('is the page heading (one h1) for a guest with no bookings', async () => {
      signedIn({ id: 1, email: 'guest@example.com' })
      mockAccountAdapter.getBookings.mockResolvedValue({ data: pageOf([]), error: null })

      renderWithRouter(<BookingsPage />)

      expect(await screen.findByRole('heading', { level: 1, name: 'No bookings yet' })).toBeInTheDocument()
    })

    it('tells an owner these are the stays booked as a guest, and where the hotel bookings are', async () => {
      signedIn({ id: 2, email: 'owner@example.com', role: 'hotel-owner' })
      mockAccountAdapter.getBookings.mockResolvedValue({ data: pageOf([]), error: null })

      renderWithRouter(<BookingsPage />)

      expect(await screen.findByRole('heading', { level: 1, name: 'No bookings yet' })).toBeInTheDocument()
      expect(screen.getByText('These are the stays you booked yourself as a guest. Bookings at your hotels are in the owner panel.')).toBeInTheDocument()
      expect(screen.queryByText(/book your first stay/)).toBeNull()
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
        data: pageOf(mockBookings),
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

    it('shows what was charged in so\'m on a booking priced in dollars, with the hotel price after a ≈', async () => {
      mockAccountAdapter.getBookings.mockResolvedValue({
        data: pageOf([{
          ...mockBookings[0], total_price: 200, currency: 'USD', charge_amount: '2354590.00', charge_currency: 'UZS',
          exchange_rate: { rate: '11772.950000', date: '2025-01-15', source: 'cbu.uz', stale: false },
        }, mockBookings[1]]),
        error: null,
      })
      renderWithRouter(<BookingsPage />)

      await screen.findByText('Test Property 1')
      const card = screen.getByText('Test Property 1').closest('.booking-card') as HTMLElement
      expect(card).toHaveTextContent('2 354 590')
      expect(card.querySelector('.charge-notes')).toHaveTextContent('≈ $200')
      const old = screen.getByText('Test Property 2').closest('.booking-card') as HTMLElement
      expect(old.querySelector('.charge-notes')).toBeNull()
      expect(old).toHaveTextContent('$500')
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
      expect(screen.getByText('$400')).toBeInTheDocument()
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
        data: pageOf(mockBookings),
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

  describe('Cancelling a booking (free, cash at the hotel)', () => {
    const upcoming = (patch = {}) => ({
      ...mockBookings[0], id: 21, property_name: 'Future Hotel', confirmation_code: 'FUT001',
      check_in: addDays(businessToday(), 20), check_out: addDays(businessToday(), 22),
      ...patch,
    })
    const api = vi.mocked(bookingAdapter)

    const open = async (bookings: unknown[]) => {
      mockUseAuth.mockReturnValue({
        user: { id: 1, email: 'test@example.com' }, isAuthenticated: true, isLoading: false,
        login: vi.fn(), register: vi.fn(), logout: vi.fn(), refreshUser: vi.fn(),
      })
      mockAccountAdapter.getBookings.mockResolvedValue({ data: pageOf(bookings), error: null })
      renderWithRouter(<BookingsPage />)
      await screen.findAllByText(/Future Hotel|Test Property|Pending Hotel/)
    }

    beforeEach(() => {
      api.cancelBooking.mockResolvedValue({ data: { ...upcoming(), status: 'cancelled' } as never, error: null })
    })

    it('offers Cancel booking on an upcoming pending or confirmed booking', async () => {
      await open([upcoming(), upcoming({ id: 22, status: 'pending', property_name: 'Pending Hotel' })])
      expect(screen.getAllByRole('button', { name: 'Cancel booking' })).toHaveLength(2)
    })

    it('offers nothing on a completed, cancelled, started or past booking', async () => {
      await open([
        upcoming({ id: 30, status: 'completed' }),
        upcoming({ id: 31, status: 'cancelled' }),
        upcoming({ id: 32, check_in: businessToday(), check_out: addDays(businessToday(), 2) }),
        upcoming({ id: 33, check_in: addDays(businessToday(), -5), check_out: addDays(businessToday(), -3) }),
      ])
      expect(screen.queryByRole('button', { name: 'Cancel booking' })).toBeNull()
    })

    it('asks for confirmation, then cancels and says so', async () => {
      await open([upcoming()])
      fireEvent.click(screen.getByRole('button', { name: 'Cancel booking' }))
      expect(await screen.findByText(/Cancelling is free/)).toBeInTheDocument()
      expect(api.cancelBooking).not.toHaveBeenCalled()

      fireEvent.click(screen.getByRole('button', { name: 'Yes, cancel booking' }))
      expect(await screen.findByText('Booking cancelled.')).toBeInTheDocument()
      expect(screen.queryByRole('dialog')).toBeNull()
      expect(screen.queryByRole('button', { name: 'Cancel booking' })).toBeNull()
      expect(document.querySelector('.booking-card-status')).toHaveTextContent('Cancelled')
    })

    it('Keep booking leaves everything as it was', async () => {
      await open([upcoming()])
      fireEvent.click(screen.getByRole('button', { name: 'Cancel booking' }))
      await screen.findByText(/Cancelling is free/)
      fireEvent.click(screen.getByRole('button', { name: 'Keep booking' }))
      expect(screen.queryByRole('dialog')).toBeNull()
      expect(api.cancelBooking).not.toHaveBeenCalled()
      expect(screen.getByRole('button', { name: 'Cancel booking' })).toBeInTheDocument()
    })
  })
})

describe('BookingsPage pages', () => {
  const booking = (id: number, status = 'confirmed') => ({
    id, guest: 1, guest_name: 'John Doe', property: 1, property_name: `Hotel ${id}`, status, payment_status: 'paid',
    check_in: addDays(businessToday(), 10), check_out: addDays(businessToday(), 12), number_of_nights: 2, guest_count: 2,
    total_price: 100, currency: 'USD', confirmation_code: `REF${id}`, booking_items: [],
    created_at: '2025-01-15T10:00:00Z', updated_at: '2025-01-15T10:00:00Z',
  })
  const firstPage = [booking(1), booking(2)]
  const secondPage = [booking(3)]

  beforeEach(() => {
    vi.clearAllMocks()
    mockUseAuth.mockReturnValue({
      user: { id: 1, email: 'guest@example.com' }, isAuthenticated: true, isLoading: false,
      login: vi.fn(), register: vi.fn(), logout: vi.fn(), refreshUser: vi.fn(),
    })
  })

  it('has no "Show more" button when everything fits on one page', async () => {
    mockAccountAdapter.getBookings.mockResolvedValue({ data: pageOf(firstPage), error: null })
    renderWithRouter(<BookingsPage />)
    await screen.findByText('Hotel 1')
    expect(screen.queryByRole('button', { name: 'Show more bookings' })).not.toBeInTheDocument()
    expect(screen.getByText('Showing 2 of 2')).toBeInTheDocument()
  })

  it('shows the first page, then adds the next one under it', async () => {
    mockAccountAdapter.getBookings
      .mockResolvedValueOnce({ data: { count: 3, next: 'http://x/?page=2', previous: null, results: firstPage }, error: null })
      .mockResolvedValueOnce({ data: { count: 3, next: null, previous: 'http://x/', results: secondPage }, error: null })
    renderWithRouter(<BookingsPage />)
    await screen.findByText('Hotel 1')
    expect(screen.getByText('Showing 2 of 3')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'Show more bookings' }))

    await screen.findByText('Hotel 3')
    expect(screen.getByText('Hotel 1')).toBeInTheDocument()
    expect(mockAccountAdapter.getBookings).toHaveBeenLastCalledWith(undefined, undefined, 2)
    expect(screen.getByText('Showing 3 of 3')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Show more bookings' })).not.toBeInTheDocument()
  })

  it('shows a booking that moved to the next page only once', async () => {
    mockAccountAdapter.getBookings
      .mockResolvedValueOnce({ data: { count: 3, next: 'http://x/?page=2', previous: null, results: firstPage }, error: null })
      .mockResolvedValueOnce({ data: { count: 3, next: null, previous: null, results: [booking(2), booking(3)] }, error: null })
    renderWithRouter(<BookingsPage />)
    await screen.findByText('Hotel 1')
    fireEvent.click(screen.getByRole('button', { name: 'Show more bookings' }))
    await screen.findByText('Hotel 3')
    expect(screen.getAllByText('Hotel 2')).toHaveLength(1)
  })

  it('disables the button while the next page loads', async () => {
    let finish: (value: unknown) => void = () => {}
    mockAccountAdapter.getBookings
      .mockResolvedValueOnce({ data: { count: 3, next: 'http://x/?page=2', previous: null, results: firstPage }, error: null })
      .mockReturnValueOnce(new Promise(resolve => { finish = resolve }))
    renderWithRouter(<BookingsPage />)
    await screen.findByText('Hotel 1')
    fireEvent.click(screen.getByRole('button', { name: 'Show more bookings' }))
    expect(await screen.findByRole('button', { name: 'Loading...' })).toBeDisabled()
    finish({ data: pageOf(secondPage), error: null })
    await screen.findByText('Hotel 3')
  })

  it('keeps the list and offers a retry when the next page fails', async () => {
    mockAccountAdapter.getBookings
      .mockResolvedValueOnce({ data: { count: 3, next: 'http://x/?page=2', previous: null, results: firstPage }, error: null })
      .mockResolvedValueOnce({ data: null, error: 'Network error occurred' })
      .mockResolvedValueOnce({ data: pageOf(secondPage), error: null })
    renderWithRouter(<BookingsPage />)
    await screen.findByText('Hotel 1')
    fireEvent.click(screen.getByRole('button', { name: 'Show more bookings' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('More bookings could not be loaded')
    expect(screen.getByText('Hotel 1')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'Show more bookings' }))
    await screen.findByText('Hotel 3')
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })

  it('starts again from the first page when the filter changes', async () => {
    mockAccountAdapter.getBookings
      .mockResolvedValueOnce({ data: { count: 3, next: 'http://x/?page=2', previous: null, results: firstPage }, error: null })
      .mockResolvedValueOnce({ data: pageOf([booking(9, 'completed')]), error: null })
    renderWithRouter(<BookingsPage />)
    await screen.findByText('Hotel 1')

    fireEvent.click(screen.getByRole('button', { name: 'Show completed bookings' }))

    await screen.findByText('Hotel 9')
    expect(mockAccountAdapter.getBookings).toHaveBeenLastCalledWith('completed')
    expect(screen.queryByText('Hotel 1')).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Show more bookings' })).not.toBeInTheDocument()
  })

  it('keeps the filter buttons when a filter has no bookings, so the guest can switch back', async () => {
    mockAccountAdapter.getBookings
      .mockResolvedValueOnce({ data: pageOf([booking(1)]), error: null })
      .mockResolvedValueOnce({ data: pageOf([]), error: null })
      .mockResolvedValueOnce({ data: pageOf([booking(1)]), error: null })
    renderWithRouter(<BookingsPage />)
    await screen.findByText('Hotel 1')

    fireEvent.click(screen.getByRole('button', { name: 'Show completed bookings' }))

    expect(await screen.findByText('No bookings yet')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Show all bookings' })).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'Show all bookings' }))
    await screen.findByText('Hotel 1')
  })
})
