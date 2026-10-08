import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { PaymentProcessing } from './PaymentProcessing'
import { PaymentProvider, PaymentStatus } from '../adapters/paymentAdapter'

describe('PaymentProcessing', () => {
  it('should render payment processing with pending status', () => {
    render(
      <PaymentProcessing
        provider={'payme' as PaymentProvider}
        amount={100.00}
        currency="USD"
        status={'pending' as PaymentStatus}
      />
    )

    expect(screen.getByText('Processing Payment')).toBeInTheDocument()
    expect(screen.getByText('Initializing payment...')).toBeInTheDocument()
  })

  it('should render payment processing with processing status', () => {
    render(
      <PaymentProcessing
        provider={'payme' as PaymentProvider}
        amount={100.00}
        currency="USD"
        status={'processing' as PaymentStatus}
      />
    )

    expect(screen.getByText('Processing Payment')).toBeInTheDocument()
    expect(screen.getByText('Processing payment via Payme...')).toBeInTheDocument()
  })

  it('should render payment processing with completed status', () => {
    render(
      <PaymentProcessing
        provider={'payme' as PaymentProvider}
        amount={100.00}
        currency="USD"
        status={'completed' as PaymentStatus}
      />
    )

    expect(screen.getByText('Payment Successful')).toBeInTheDocument()
    expect(screen.getByText('Payment completed successfully!')).toBeInTheDocument()
  })

  it('should render payment processing with failed status', () => {
    render(
      <PaymentProcessing
        provider={'payme' as PaymentProvider}
        amount={100.00}
        currency="USD"
        status={'failed' as PaymentStatus}
      />
    )

    expect(screen.getByText('Payment Failed')).toBeInTheDocument()
    expect(screen.getByText('Payment failed. Please try again.')).toBeInTheDocument()
  })

  it('should display custom message when provided', () => {
    render(
      <PaymentProcessing
        provider={'payme' as PaymentProvider}
        amount={100.00}
        currency="USD"
        status={'processing' as PaymentStatus}
        message="Custom processing message"
      />
    )

    expect(screen.getByText('Custom processing message')).toBeInTheDocument()
  })

  it('should display provider name correctly', () => {
    render(
      <PaymentProcessing
        provider={'click' as PaymentProvider}
        amount={100.00}
        currency="USD"
        status={'processing' as PaymentStatus}
      />
    )

    expect(screen.getByText('Click')).toBeInTheDocument()
  })

  it('should display formatted amount', () => {
    render(
      <PaymentProcessing
        provider={'payme' as PaymentProvider}
        amount={100.00}
        currency="USD"
        status={'processing' as PaymentStatus}
      />
    )

    expect(screen.getByText('$100')).toBeInTheDocument()
  })

  it('should display payment status', () => {
    render(
      <PaymentProcessing
        provider={'payme' as PaymentProvider}
        amount={100.00}
        currency="USD"
        status={'completed' as PaymentStatus}
      />
    )

    expect(screen.getByText('Completed')).toBeInTheDocument()
  })

  it('should have proper ARIA attributes', () => {
    render(
      <PaymentProcessing
        provider={'payme' as PaymentProvider}
        amount={100.00}
        currency="USD"
        status={'processing' as PaymentStatus}
      />
    )

    const message = screen.getByText('Processing payment via Payme...')
    expect(message).toHaveAttribute('role', 'status')
    expect(message).toHaveAttribute('aria-live', 'polite')
  })

  it('should show spinner for pending and processing status', () => {
    const { rerender } = render(
      <PaymentProcessing
        provider={'payme' as PaymentProvider}
        amount={100.00}
        currency="USD"
        status={'pending' as PaymentStatus}
      />
    )

    expect(screen.getByText('Initializing payment...')).toBeInTheDocument()

    rerender(
      <PaymentProcessing
        provider={'payme' as PaymentProvider}
        amount={100.00}
        currency="USD"
        status={'processing' as PaymentStatus}
      />
    )

    expect(screen.getByText('Processing payment via Payme...')).toBeInTheDocument()
  })

  it('should show status icon for completed status', () => {
    const { container } = render(
      <PaymentProcessing
        provider={'payme' as PaymentProvider}
        amount={100.00}
        currency="USD"
        status={'completed' as PaymentStatus}
      />
    )

    expect(container.querySelector('.payment-processing-status-icon .lucide-circle-check')).toBeInTheDocument()
  })

  it('should show status icon for failed status', () => {
    const { container } = render(
      <PaymentProcessing
        provider={'payme' as PaymentProvider}
        amount={100.00}
        currency="USD"
        status={'failed' as PaymentStatus}
      />
    )

    expect(container.querySelector('.payment-processing-status-icon .lucide-circle-x')).toBeInTheDocument()
  })
})
