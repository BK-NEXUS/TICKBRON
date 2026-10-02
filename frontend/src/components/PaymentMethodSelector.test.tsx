import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { PaymentMethodSelector } from './PaymentMethodSelector'
import { PaymentProvider } from '../adapters/paymentAdapter'

describe('PaymentMethodSelector', () => {
  const mockOnProviderSelect = vi.fn()

  beforeEach(() => {
    mockOnProviderSelect.mockClear()
  })

  it('should render payment method selector with title', () => {
    render(
      <PaymentMethodSelector
        selectedProvider={null}
        onProviderSelect={mockOnProviderSelect}
      />
    )

    expect(screen.getByText('Select Payment Method')).toBeInTheDocument()
  })

  it('should render all payment methods', () => {
    render(
      <PaymentMethodSelector
        selectedProvider={null}
        onProviderSelect={mockOnProviderSelect}
      />
    )

    expect(screen.getByText('Payme')).toBeInTheDocument()
    expect(screen.getByText('Click')).toBeInTheDocument()
    expect(screen.getByText('Visa')).toBeInTheDocument()
  })

  it('should show popular badge on Payme', () => {
    render(
      <PaymentMethodSelector
        selectedProvider={null}
        onProviderSelect={mockOnProviderSelect}
      />
    )

    expect(screen.getByText('Popular')).toBeInTheDocument()
  })

  it('should call onProviderSelect when a payment method is clicked', () => {
    render(
      <PaymentMethodSelector
        selectedProvider={null}
        onProviderSelect={mockOnProviderSelect}
      />
    )

    const paymeCard = screen.getByText('Payme').closest('.payment-method-card')
    fireEvent.click(paymeCard!)

    expect(mockOnProviderSelect).toHaveBeenCalledWith('payme')
  })

  it('should not call onProviderSelect when disabled', () => {
    render(
      <PaymentMethodSelector
        selectedProvider={null}
        onProviderSelect={mockOnProviderSelect}
        disabled={true}
      />
    )

    const paymeCard = screen.getByText('Payme').closest('.payment-method-card')
    fireEvent.click(paymeCard!)

    expect(mockOnProviderSelect).not.toHaveBeenCalled()
  })

  it('should show selected state for selected provider', () => {
    render(
      <PaymentMethodSelector
        selectedProvider={'payme' as PaymentProvider}
        onProviderSelect={mockOnProviderSelect}
      />
    )

    const paymeCard = screen.getByText('Payme').closest('.payment-method-card')
    expect(paymeCard).toHaveClass('payment-method-card--selected')
  })

  it('should show checkmark for selected provider', () => {
    render(
      <PaymentMethodSelector
        selectedProvider={'payme' as PaymentProvider}
        onProviderSelect={mockOnProviderSelect}
      />
    )

    // Check for the check icon SVG (lucide check icon) - it has aria-hidden="true" so use class selector
    const checkIcon = screen.getByTestId('payment-method-check')
    expect(checkIcon).toBeInTheDocument()
  })

  it('should show selected provider label when provider is selected', () => {
    render(
      <PaymentMethodSelector
        selectedProvider={'payme' as PaymentProvider}
        onProviderSelect={mockOnProviderSelect}
      />
    )

    expect(screen.getByText('Selected: Payme')).toBeInTheDocument()
  })

  it('should handle keyboard navigation with Enter key', () => {
    render(
      <PaymentMethodSelector
        selectedProvider={null}
        onProviderSelect={mockOnProviderSelect}
      />
    )

    const paymeCard = screen.getByText('Payme').closest('.payment-method-card')
    fireEvent.keyDown(paymeCard!, { key: 'Enter' })

    expect(mockOnProviderSelect).toHaveBeenCalledWith('payme')
  })

  it('should handle keyboard navigation with Space key', () => {
    render(
      <PaymentMethodSelector
        selectedProvider={null}
        onProviderSelect={mockOnProviderSelect}
      />
    )

    const paymeCard = screen.getByText('Payme').closest('.payment-method-card')
    fireEvent.keyDown(paymeCard!, { key: ' ' })

    expect(mockOnProviderSelect).toHaveBeenCalledWith('payme')
  })

  it('should have proper ARIA attributes', () => {
    render(
      <PaymentMethodSelector
        selectedProvider={'payme' as PaymentProvider}
        onProviderSelect={mockOnProviderSelect}
      />
    )

    const paymeCard = screen.getByText('Payme').closest('.payment-method-card')
    expect(paymeCard).toHaveAttribute('role', 'radio')
    expect(paymeCard).toHaveAttribute('aria-checked', 'true')
    expect(paymeCard).toHaveAttribute('tabIndex', '0')
  })

  it('should have aria-disabled when disabled', () => {
    render(
      <PaymentMethodSelector
        selectedProvider={null}
        onProviderSelect={mockOnProviderSelect}
        disabled={true}
      />
    )

    const paymeCard = screen.getByText('Payme').closest('.payment-method-card')
    expect(paymeCard).toHaveAttribute('aria-disabled', 'true')
    expect(paymeCard).toHaveAttribute('tabIndex', '-1')
  })
})
