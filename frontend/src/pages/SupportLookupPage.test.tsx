import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { SupportLookupPage } from './SupportLookupPage'
import { AuthProvider } from '../contexts/AuthContext'
import { adminAdapter } from '../adapters/adminAdapter'

// Mock the admin adapter
vi.mock('../adapters/adminAdapter', () => ({
  adminAdapter: {
    lookupBookingByReferenceCode: vi.fn(),
  },
}))

// Mock the auth context
const mockAuthContext = {
  user: {
    id: 1,
    email: 'admin@example.com',
    first_name: 'Admin',
    last_name: 'User',
    is_staff: true,
    is_superuser: true,
  },
  isAuthenticated: true,
  login: vi.fn(),
  logout: vi.fn(),
}

vi.mock('../contexts/AuthContext', () => ({
  useAuth: () => mockAuthContext,
  AuthProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}))

describe('SupportLookupPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should render the support lookup page', () => {
    render(
      <AuthProvider>
        <SupportLookupPage />
      </AuthProvider>
    )

    expect(screen.getByText('Support Lookup')).toBeInTheDocument()
    expect(screen.getByText('Look up booking details by reference code')).toBeInTheDocument()
  })

  it('should show authentication required when not authenticated', () => {
    mockAuthContext.isAuthenticated = false
    mockAuthContext.user = null

    render(
      <AuthProvider>
        <SupportLookupPage />
      </AuthProvider>
    )

    expect(screen.getByText('Authentication required')).toBeInTheDocument()
    expect(screen.getByText('Please sign in to access the support lookup tool.')).toBeInTheDocument()
  })

  it('should show access denied for non-staff users', () => {
    mockAuthContext.isAuthenticated = true
    mockAuthContext.user = {
      id: 2,
      email: 'user@example.com',
      first_name: 'Regular',
      last_name: 'User',
      is_staff: false,
      is_superuser: false,
    }

    render(
      <AuthProvider>
        <SupportLookupPage />
      </AuthProvider>
    )

    expect(screen.getByText('Access Denied')).toBeInTheDocument()
    expect(screen.getByText('You do not have permission to access the support lookup tool.')).toBeInTheDocument()
  })

  it('should render search form for staff users', () => {
    mockAuthContext.isAuthenticated = true
    mockAuthContext.user = {
      id: 1,
      email: 'admin@example.com',
      first_name: 'Admin',
      last_name: 'User',
      is_staff: true,
      is_superuser: false,
    }

    render(
      <AuthProvider>
        <SupportLookupPage />
      </AuthProvider>
    )

    expect(screen.getByLabelText('Reference Code')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Look Up Booking' })).toBeInTheDocument()
  })

  it('should show validation error when searching with empty reference code', async () => {
    mockAuthContext.isAuthenticated = true
    mockAuthContext.user = {
      id: 1,
      email: 'admin@example.com',
      first_name: 'Admin',
      last_name: 'User',
      is_staff: true,
      is_superuser: false,
    }

    render(
      <AuthProvider>
        <SupportLookupPage />
      </AuthProvider>
    )

    const searchButton = screen.getByRole('button', { name: 'Look Up Booking' })
    await userEvent.click(searchButton)

    await waitFor(() => {
      expect(screen.getByText('Please enter a reference code')).toBeInTheDocument()
    })
  })

  it('should display booking details when found', async () => {
    mockAuthContext.isAuthenticated = true
    mockAuthContext.user = {
      id: 1,
      email: 'admin@example.com',
      first_name: 'Admin',
      last_name: 'User',
      is_staff: true,
      is_superuser: false,
    }

    const mockBooking = {
      id: 1,
      reference_code: 'ABC123',
      status: 'confirmed',
      payment_status: 'paid',
      check_in: '2024-10-01T00:00:00Z',
      check_out: '2024-10-03T00:00:00Z',
      number_of_nights: 2,
      total_price: 200,
      currency: 'USD',
      property: {
        id: 1,
        name: 'Tashkent Hotel',
        city: 'Tashkent',
        country: 'Uzbekistan',
        address_line1: '123 Main St',
      },
      room: {
        id: 1,
        name: 'Deluxe Room',
        room_type: 'deluxe',
      },
      customer: {
        id: 1,
        full_name: 'John Doe',
        email: 'john@example.com',
        phone_number: '+998901234567',
        whatsapp: '+998901234567',
        telegram: '@johndoe',
        preferred_contact_method: 'email',
      },
      created_at: '2024-09-01T00:00:00Z',
      updated_at: '2024-09-01T00:00:00Z',
    }

    ;(adminAdapter.lookupBookingByReferenceCode as any).mockResolvedValue({
      data: mockBooking,
      error: null,
    })

    render(
      <AuthProvider>
        <SupportLookupPage />
      </AuthProvider>
    )

    const referenceInput = screen.getByLabelText('Reference Code')
    await userEvent.type(referenceInput, 'ABC123')

    const searchButton = screen.getByRole('button', { name: 'Look Up Booking' })
    await userEvent.click(searchButton)

    await waitFor(() => {
      expect(screen.getByText('Booking Details')).toBeInTheDocument()
      expect(screen.getByText('ABC123')).toBeInTheDocument()
      expect(screen.getByText('John Doe')).toBeInTheDocument()
      expect(screen.getByText('Tashkent Hotel')).toBeInTheDocument()
    })
  })

  it('should display empty state when booking not found', async () => {
    mockAuthContext.isAuthenticated = true
    mockAuthContext.user = {
      id: 1,
      email: 'admin@example.com',
      first_name: 'Admin',
      last_name: 'User',
      is_staff: true,
      is_superuser: false,
    }

    ;(adminAdapter.lookupBookingByReferenceCode as any).mockResolvedValue({
      data: null,
      error: null,
    })

    render(
      <AuthProvider>
        <SupportLookupPage />
      </AuthProvider>
    )

    const referenceInput = screen.getByLabelText('Reference Code')
    await userEvent.type(referenceInput, 'INVALID')

    const searchButton = screen.getByRole('button', { name: 'Look Up Booking' })
    await userEvent.click(searchButton)

    await waitFor(() => {
      expect(screen.getByText('No booking found with reference code "INVALID"')).toBeInTheDocument()
    })
  })

  it('should display error message when API call fails', async () => {
    mockAuthContext.isAuthenticated = true
    mockAuthContext.user = {
      id: 1,
      email: 'admin@example.com',
      first_name: 'Admin',
      last_name: 'User',
      is_staff: true,
      is_superuser: false,
    }

    ;(adminAdapter.lookupBookingByReferenceCode as any).mockResolvedValue({
      data: null,
      error: 'Failed to look up booking',
    })

    render(
      <AuthProvider>
        <SupportLookupPage />
      </AuthProvider>
    )

    const referenceInput = screen.getByLabelText('Reference Code')
    await userEvent.type(referenceInput, 'ABC123')

    const searchButton = screen.getByRole('button', { name: 'Look Up Booking' })
    await userEvent.click(searchButton)

    await waitFor(() => {
      expect(screen.getByText('Failed to look up booking')).toBeInTheDocument()
    })
  })

  it('should convert reference code to uppercase', async () => {
    mockAuthContext.isAuthenticated = true
    mockAuthContext.user = {
      id: 1,
      email: 'admin@example.com',
      first_name: 'Admin',
      last_name: 'User',
      is_staff: true,
      is_superuser: false,
    }

    const mockBooking = {
      id: 1,
      reference_code: 'ABC123',
      status: 'confirmed',
      payment_status: 'paid',
      check_in: '2024-10-01T00:00:00Z',
      check_out: '2024-10-03T00:00:00Z',
      number_of_nights: 2,
      total_price: 200,
      currency: 'USD',
      property: {
        id: 1,
        name: 'Tashkent Hotel',
        city: 'Tashkent',
        country: 'Uzbekistan',
        address_line1: '123 Main St',
      },
      room: {
        id: 1,
        name: 'Deluxe Room',
        room_type: 'deluxe',
      },
      customer: {
        id: 1,
        full_name: 'John Doe',
        email: 'john@example.com',
        phone_number: '+998901234567',
        whatsapp: '+998901234567',
        telegram: '@johndoe',
        preferred_contact_method: 'email',
      },
      created_at: '2024-09-01T00:00:00Z',
      updated_at: '2024-09-01T00:00:00Z',
    }

    ;(adminAdapter.lookupBookingByReferenceCode as any).mockResolvedValue({
      data: mockBooking,
      error: null,
    })

    render(
      <AuthProvider>
        <SupportLookupPage />
      </AuthProvider>
    )

    const referenceInput = screen.getByLabelText('Reference Code')
    await userEvent.type(referenceInput, 'abc123')

    await waitFor(() => {
      expect(referenceInput).toHaveValue('ABC123')
    })
  })
})
