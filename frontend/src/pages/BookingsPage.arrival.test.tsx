/**
 * Cash at the hotel: "My bookings" shows the arrival time the guest gave, what happens if they do not
 * come, and the booking cancelled because they did not.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { BookingsPage } from './BookingsPage'
import { accountAdapter } from '../adapters/accountAdapter'
import { useAuth } from '../contexts/AuthContext'
import { addDays, businessToday } from '../utils/dates'

vi.mock('../adapters/accountAdapter')
vi.mock('../adapters/bookingAdapter', async importOriginal => ({
  ...(await importOriginal<typeof import('../adapters/bookingAdapter')>()),
  bookingAdapter: { getCancelPreview: vi.fn(), cancelBooking: vi.fn() },
}))
vi.mock('../contexts/AuthContext', () => ({ useAuth: vi.fn() }))

const mockAccountAdapter = accountAdapter as unknown as { getBookings: ReturnType<typeof vi.fn> }

const booking = (over: object) => ({
  id: 1, guest: 1, guest_name: 'John Doe', property: 1, property_name: 'Test Property', status: 'confirmed',
  payment_status: 'pending', check_in: addDays(businessToday(), 5), check_out: addDays(businessToday(), 7),
  number_of_nights: 2, guest_count: 2, total_price: 400, currency: 'USD', confirmation_code: 'ABC123',
  booking_items: [], created_at: '2025-01-15T10:00:00Z', updated_at: '2025-01-15T10:00:00Z', ...over,
})

function show(rows: object[]) {
  mockAccountAdapter.getBookings.mockResolvedValue({ data: rows, error: null })
  vi.mocked(useAuth).mockReturnValue({
    user: { id: 1, email: 'test@example.com' }, isAuthenticated: true, isLoading: false,
    login: vi.fn(), register: vi.fn(), logout: vi.fn(), refreshUser: vi.fn(),
  } as never)
  render(<MemoryRouter><BookingsPage /></MemoryRouter>)
}

describe('BookingsPage arrival', () => {
  beforeEach(() => vi.clearAllMocks())

  it('shows the arrival time and the 2 hour rule of an upcoming confirmed booking', async () => {
    show([booking({ expected_arrival_time: '10:30:00' })])
    expect(await screen.findByText('10:30')).toBeInTheDocument()
    expect(screen.getByText(/If you do not arrive at 10:30, we wait 2 more hours/)).toBeInTheDocument()
  })

  it('shows "Pay at the hotel" for a booking nobody has paid online', async () => {
    show([booking({ expected_arrival_time: '10:30:00' })])
    expect(await screen.findByText('Payment: Pay at the hotel')).toBeInTheDocument()
  })

  it('says the hotel marked the guest as arrived and drops the warning', async () => {
    show([booking({ expected_arrival_time: '10:30:00', arrived_at: '2025-02-01T10:40:00Z' })])
    expect(await screen.findByText('The hotel marked you as arrived.')).toBeInTheDocument()
    expect(screen.queryByText(/we wait 2 more hours/)).not.toBeInTheDocument()
  })

  it('explains a booking cancelled because the guest did not arrive', async () => {
    show([booking({ status: 'cancelled', cancellation_reason: 'no_arrival', expected_arrival_time: '10:30:00' })])
    expect(await screen.findByText('Cancelled: you did not arrive in time.')).toBeInTheDocument()
    expect(screen.queryByText(/we wait 2 more hours/)).not.toBeInTheDocument()
  })

  it('an old booking without an arrival time shows no arrival line', async () => {
    show([booking({ expected_arrival_time: null })])
    await waitFor(() => expect(screen.getByText('ABC123')).toBeInTheDocument())
    expect(screen.queryByText(/we wait 2 more hours/)).not.toBeInTheDocument()
    expect(screen.queryByText('Arrival time')).not.toBeInTheDocument()
  })
})
