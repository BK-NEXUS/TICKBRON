import { useState } from 'react'
import { PaymentProvider } from '../adapters/paymentAdapter'

interface PaymentMethodSelectorProps {
  selectedProvider: PaymentProvider | null
  onProviderSelect: (provider: PaymentProvider) => void
  disabled?: boolean
}

/**
 * PaymentMethodSelector component for selecting payment provider
 * Supports Payme, Click, and Visa payment methods
 */
export function PaymentMethodSelector({ selectedProvider, onProviderSelect, disabled }: PaymentMethodSelectorProps) {
  const [focusedProvider, setFocusedProvider] = useState<PaymentProvider | null>(null)

  const paymentMethods = [
    {
      id: 'payme' as PaymentProvider,
      name: 'Payme',
      description: 'Fast and secure mobile payments',
      icon: '📱',
      popular: true,
    },
    {
      id: 'click' as PaymentProvider,
      name: 'Click',
      description: 'Uzbekistan\'s leading payment system',
      icon: '💳',
      popular: false,
    },
    {
      id: 'visa' as PaymentProvider,
      name: 'Visa',
      description: 'Global credit and debit cards',
      icon: '💼',
      popular: false,
    },
  ]

  const handleProviderClick = (provider: PaymentProvider) => {
    if (!disabled) {
      onProviderSelect(provider)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent, provider: PaymentProvider) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault()
      handleProviderClick(provider)
    }
  }

  return (
    <div className="payment-method-selector">
      <h3 className="payment-method-selector-title">Select Payment Method</h3>
      <div className="payment-method-selector-grid">
        {paymentMethods.map((method) => (
          <div
            key={method.id}
            className={`payment-method-card ${
              selectedProvider === method.id ? 'payment-method-card--selected' : ''
            } ${
              focusedProvider === method.id ? 'payment-method-card--focused' : ''
            } ${
              disabled ? 'payment-method-card--disabled' : ''
            }`}
            onClick={() => handleProviderClick(method.id)}
            onKeyDown={(e) => handleKeyDown(e, method.id)}
            onFocus={() => setFocusedProvider(method.id)}
            onBlur={() => setFocusedProvider(null)}
            tabIndex={disabled ? -1 : 0}
            role="radio"
            aria-checked={selectedProvider === method.id}
            aria-disabled={disabled}
          >
            <div className="payment-method-card-icon">{method.icon}</div>
            <div className="payment-method-card-content">
              <div className="payment-method-card-name">
                {method.name}
                {method.popular && (
                  <span className="payment-method-card-badge">Popular</span>
                )}
              </div>
              <div className="payment-method-card-description">
                {method.description}
              </div>
            </div>
            {selectedProvider === method.id && (
              <div className="payment-method-card-check" aria-hidden="true">
                ✓
              </div>
            )}
          </div>
        ))}
      </div>
      {selectedProvider && (
        <div className="payment-method-selector-selected">
          <span className="payment-method-selector-selected-label">
            Selected: {paymentMethods.find(m => m.id === selectedProvider)?.name}
          </span>
        </div>
      )}
    </div>
  )
}
