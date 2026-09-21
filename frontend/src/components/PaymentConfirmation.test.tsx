import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { PaymentConfirmation } from './PaymentConfirmation'
import { PaymentTransaction, PaymentProvider } from '../adapters/paymentAdapter'

describe('PaymentConfirmation', () => {
  const mockPayment: PaymentTransaction = {
    id: 1,
    idempotency_key: 'test_key_123',
    booking: 100,
    provider: 'payme' as PaymentProvider,
    provider_transaction_id: 'txn_123',
    amount: 100.00,
    currency: 'USD',
    status: 'completed',
    payment_method_token: null,
    provider_response: { success: true },
    error_code: null,
    error_message: null,
    client_ip: '127.0.0.1',
    user_agent: 'test-agent',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  }

  const mockBookingDetails = {
    property_name: 'Test Property',
    check_in: '2024-01-10T00:00:00Z',
    check_out: '2024-01-15T00:00:00Z',
    confirmation_code: 'ABC123',
  }

  const mockOnViewBookings = vi.fn()
  const mockOnBackToProperty = vi.fn()

  beforeEach(() => {
    mockOnViewBookings.mockClear()
    mockOnBackToProperty.mockClear()
  })

  it('should render payment confirmation header', () => {
    render(
      <PaymentConfirmation
        payment={mockPayment}
        bookingDetails={mockBookingDetails}
        onViewBookings={mockOnViewBookings}
        onBackToProperty={mockOnBackToProperty}
      />
    )

    expect(screen.getByText('Payment Successful!')).toBeInTheDocument()
    expect(screen.getByText('Your payment has been processed successfully')).toBeInTheDocument()
  })

  it('should display payment details', () => {
    render(
      <PaymentConfirmation
        payment={mockPayment}
        bookingDetails={mockBookingDetails}
        onViewBookings={mockOnViewBookings}
        onBackToProperty={mockOnBackToProperty}
      />
    )

    expect(screen.getByText('test_key_123')).toBeInTheDocument()
    expect(screen.getByText('Payme')).toBeInTheDocument()
    expect(screen.getByText('$100')).toBeInTheDocument()
    expect(screen.getByText('Completed')).toBeInTheDocument()
  })

  it('should display booking details', () => {
    render(
      <PaymentConfirmation
        payment={mockPayment}
        bookingDetails={mockBookingDetails}
        onViewBookings={mockOnViewBookings}
        onBackToProperty={mockOnBackToProperty}
      />
    )

    expect(screen.getByText('ABC123')).toBeInTheDocument()
    expect(screen.getByText('Test Property')).toBeInTheDocument()
  })

  it('should format dates correctly', () => {
    render(
      <PaymentConfirmation
        payment={mockPayment}
        bookingDetails={mockBookingDetails}
        onViewBookings={mockOnViewBookings}
        onBackToProperty={mockOnBackToProperty}
      />
    )

    expect(screen.getByText('Wednesday, January 10, 2024')).toBeInTheDocument()
    expect(screen.getByText('Monday, January 15, 2024')).toBeInTheDocument()
  })

  it('should display confirmation email info', () => {
    render(
      <PaymentConfirmation
        payment={mockPayment}
        bookingDetails={mockBookingDetails}
        onViewBookings={mockOnViewBookings}
        onBackToProperty={mockOnBackToProperty}
      />
    )

    expect(screen.getByText('Confirmation email sent')).toBeInTheDocument()
    expect(screen.getByText('You will receive a confirmation email with your booking details shortly.')).toBeInTheDocument()
  })

  it('should display manage booking info', () => {
    render(
      <PaymentConfirmation
        payment={mockPayment}
        bookingDetails={mockBookingDetails}
        onViewBookings={mockOnViewBookings}
        onBackToProperty={mockOnBackToProperty}
      />
    )

    expect(screen.getByText('Manage your booking')).toBeInTheDocument()
    expect(screen.getByText('You can view and manage your booking from your account at any time.')).toBeInTheDocument()
  })

  it('should call onViewBookings when View My Bookings button is clicked', () => {
    render(
      <PaymentConfirmation
        payment={mockPayment}
        bookingDetails={mockBookingDetails}
        onViewBookings={mockOnViewBookings}
        onBackToProperty={mockOnBackToProperty}
      />
    )

    const viewBookingsButton = screen.getByText('View My Bookings')
    fireEvent.click(viewBookingsButton)

    expect(mockOnViewBookings).toHaveBeenCalled()
  })

  it('should call onBackToProperty when Back to Property button is clicked', () => {
    render(
      <PaymentConfirmation
        payment={mockPayment}
        bookingDetails={mockBookingDetails}
        onViewBookings={mockOnViewBookings}
        onBackToProperty={mockOnBackToProperty}
      />
    )

    const backButton = screen.getByText('Back to Property')
    fireEvent.click(backButton)

    expect(mockOnBackToProperty).toHaveBeenCalled()
  })

  it('should have proper ARIA labels on buttons', () => {
    render(
      <PaymentConfirmation
        payment={mockPayment}
        bookingDetails={mockBookingDetails}
        onViewBookings={mockOnViewBookings}
        onBackToProperty={mockOnBackToProperty}
      />
    )

    const viewBookingsButton = screen.getByText('View My Bookings')
    const backButton = screen.getByText('Back to Property')

    expect(viewBookingsButton).toHaveAttribute('aria-label', 'View my bookings')
    expect(backButton).toHaveAttribute('aria-label', 'Return to property page')
  })

  it('should display different providers correctly', () => {
    const clickPayment = { ...mockPayment, provider: 'click' as PaymentProvider }
    
    render(
      <PaymentConfirmation
        payment={clickPayment}
        bookingDetails={mockBookingDetails}
        onViewBookings={mockOnViewBookings}
        onBackToProperty={mockOnBackToProperty}
      />
    )

    expect(screen.getByText('Click')).toBeInTheDocument()
  })

  it('should display different currencies correctly', () => {
    const eurPayment = { ...mockPayment, currency: 'EUR', amount: 85.00 }
    
    render(
      <PaymentConfirmation
        payment={eurPayment}
        bookingDetails={mockBookingDetails}
        onViewBookings={mockOnViewBookings}
        onBackToProperty={mockOnBackToProperty}
      />
    )

    expect(screen.getByText('€85')).toBeInTheDocument()
  })
})
