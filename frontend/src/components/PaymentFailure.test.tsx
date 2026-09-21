import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { PaymentFailure } from './PaymentFailure'
import { PaymentProvider } from '../adapters/paymentAdapter'

describe('PaymentFailure', () => {
  const mockOnRetry = vi.fn()
  const mockOnCancel = vi.fn()
  const mockOnTryDifferentMethod = vi.fn()

  beforeEach(() => {
    mockOnRetry.mockClear()
    mockOnCancel.mockClear()
    mockOnTryDifferentMethod.mockClear()
  })

  it('should render payment failure header', () => {
    render(
      <PaymentFailure
        provider={'payme' as PaymentProvider}
        amount={100.00}
        currency="USD"
        onRetry={mockOnRetry}
        onCancel={mockOnCancel}
        onTryDifferentMethod={mockOnTryDifferentMethod}
      />
    )

    expect(screen.getByText('Payment Failed')).toBeInTheDocument()
    expect(screen.getByText("We couldn't process your payment")).toBeInTheDocument()
  })

  it('should display default error message for Payme', () => {
    render(
      <PaymentFailure
        provider={'payme' as PaymentProvider}
        amount={100.00}
        currency="USD"
        onRetry={mockOnRetry}
        onCancel={mockOnCancel}
        onTryDifferentMethod={mockOnTryDifferentMethod}
      />
    )

    expect(screen.getByText(/Payment failed. Please check your Payme account/)).toBeInTheDocument()
  })

  it('should display custom error message when provided', () => {
    render(
      <PaymentFailure
        provider={'payme' as PaymentProvider}
        amount={100.00}
        currency="USD"
        error="Custom error message"
        onRetry={mockOnRetry}
        onCancel={mockOnCancel}
        onTryDifferentMethod={mockOnTryDifferentMethod}
      />
    )

    expect(screen.getByText('Custom error message')).toBeInTheDocument()
  })

  it('should display payment details', () => {
    render(
      <PaymentFailure
        provider={'payme' as PaymentProvider}
        amount={100.00}
        currency="USD"
        onRetry={mockOnRetry}
        onCancel={mockOnCancel}
        onTryDifferentMethod={mockOnTryDifferentMethod}
      />
    )

    expect(screen.getByText('Payme')).toBeInTheDocument()
    expect(screen.getByText('$100')).toBeInTheDocument()
  })

  it('should display helpful tips for Payme', () => {
    render(
      <PaymentFailure
        provider={'payme' as PaymentProvider}
        amount={100.00}
        currency="USD"
        onRetry={mockOnRetry}
        onCancel={mockOnCancel}
        onTryDifferentMethod={mockOnTryDifferentMethod}
      />
    )

    expect(screen.getByText('What you can try:')).toBeInTheDocument()
    expect(screen.getByText(/Ensure you have sufficient funds in your Payme account/)).toBeInTheDocument()
    expect(screen.getByText(/Check your internet connection/)).toBeInTheDocument()
  })

  it('should display helpful tips for Click', () => {
    render(
      <PaymentFailure
        provider={'click' as PaymentProvider}
        amount={100.00}
        currency="USD"
        onRetry={mockOnRetry}
        onCancel={mockOnCancel}
        onTryDifferentMethod={mockOnTryDifferentMethod}
      />
    )

    expect(screen.getByText(/Ensure you have sufficient funds in your Click account/)).toBeInTheDocument()
  })

  it('should display helpful tips for Visa', () => {
    render(
      <PaymentFailure
        provider={'visa' as PaymentProvider}
        amount={100.00}
        currency="USD"
        onRetry={mockOnRetry}
        onCancel={mockOnCancel}
        onTryDifferentMethod={mockOnTryDifferentMethod}
      />
    )

    expect(screen.getByText(/Check your card details are correct/)).toBeInTheDocument()
    expect(screen.getByText(/Ensure you have sufficient funds/)).toBeInTheDocument()
  })

  it('should display support message', () => {
    render(
      <PaymentFailure
        provider={'payme' as PaymentProvider}
        amount={100.00}
        currency="USD"
        onRetry={mockOnRetry}
        onCancel={mockOnCancel}
        onTryDifferentMethod={mockOnTryDifferentMethod}
      />
    )

    expect(screen.getByText(/If the problem persists, please contact our support team/)).toBeInTheDocument()
  })

  it('should call onRetry when Try Again button is clicked', () => {
    render(
      <PaymentFailure
        provider={'payme' as PaymentProvider}
        amount={100.00}
        currency="USD"
        onRetry={mockOnRetry}
        onCancel={mockOnCancel}
        onTryDifferentMethod={mockOnTryDifferentMethod}
      />
    )

    const retryButton = screen.getByText('Try Again')
    fireEvent.click(retryButton)

    expect(mockOnRetry).toHaveBeenCalled()
  })

  it('should call onTryDifferentMethod when Try Different Payment Method button is clicked', () => {
    render(
      <PaymentFailure
        provider={'payme' as PaymentProvider}
        amount={100.00}
        currency="USD"
        onRetry={mockOnRetry}
        onCancel={mockOnCancel}
        onTryDifferentMethod={mockOnTryDifferentMethod}
      />
    )

    const tryDifferentButton = screen.getByText('Try Different Payment Method')
    fireEvent.click(tryDifferentButton)

    expect(mockOnTryDifferentMethod).toHaveBeenCalled()
  })

  it('should call onCancel when Cancel Booking button is clicked', () => {
    render(
      <PaymentFailure
        provider={'payme' as PaymentProvider}
        amount={100.00}
        currency="USD"
        onRetry={mockOnRetry}
        onCancel={mockOnCancel}
        onTryDifferentMethod={mockOnTryDifferentMethod}
      />
    )

    const cancelButton = screen.getByText('Cancel Booking')
    fireEvent.click(cancelButton)

    expect(mockOnCancel).toHaveBeenCalled()
  })

  it('should have proper ARIA attributes', () => {
    render(
      <PaymentFailure
        provider={'payme' as PaymentProvider}
        amount={100.00}
        currency="USD"
        onRetry={mockOnRetry}
        onCancel={mockOnCancel}
        onTryDifferentMethod={mockOnTryDifferentMethod}
      />
    )

    const errorSection = screen.getByText('Error:').closest('.payment-failure-error')
    expect(errorSection).toHaveAttribute('role', 'alert')
    expect(errorSection).toHaveAttribute('aria-live', 'assertive')

    const retryButton = screen.getByText('Try Again')
    expect(retryButton).toHaveAttribute('aria-label', 'Retry payment')

    const tryDifferentButton = screen.getByText('Try Different Payment Method')
    expect(tryDifferentButton).toHaveAttribute('aria-label', 'Try a different payment method')

    const cancelButton = screen.getByText('Cancel Booking')
    expect(cancelButton).toHaveAttribute('aria-label', 'Cancel booking')
  })

  it('should display different providers correctly', () => {
    render(
      <PaymentFailure
        provider={'click' as PaymentProvider}
        amount={100.00}
        currency="USD"
        onRetry={mockOnRetry}
        onCancel={mockOnCancel}
        onTryDifferentMethod={mockOnTryDifferentMethod}
      />
    )

    expect(screen.getByText('Click')).toBeInTheDocument()
  })

  it('should display different currencies correctly', () => {
    render(
      <PaymentFailure
        provider={'payme' as PaymentProvider}
        amount={85.00}
        currency="EUR"
        onRetry={mockOnRetry}
        onCancel={mockOnCancel}
        onTryDifferentMethod={mockOnTryDifferentMethod}
      />
    )

    expect(screen.getByText('€85')).toBeInTheDocument()
  })
})
