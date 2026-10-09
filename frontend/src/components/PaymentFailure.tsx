import { PaymentProvider } from '../adapters/paymentAdapter'
import { CircleX, TriangleAlert } from 'lucide-react'
import { useI18n } from '../i18n/I18nContext'

interface PaymentFailureProps {
  provider: PaymentProvider
  amount: number
  currency: string
  error?: string
  onRetry: () => void
  onCancel: () => void
  onTryDifferentMethod: () => void
}

/**
 * PaymentFailure component for displaying payment failure state
 * Shows error message and provides retry options
 */
export function PaymentFailure({ 
  provider, 
  amount, 
  currency, 
  error, 
  onRetry, 
  onCancel, 
  onTryDifferentMethod 
}: PaymentFailureProps) {
  const getProviderName = (provider: PaymentProvider): string => {
    const names: Record<PaymentProvider, string> = {
      payme: 'Payme',
      click: 'Click',
      visa: 'Visa',
    }
    return names[provider]
  }

  const { formatMoney } = useI18n()

  const formatAmount = (amount: number, currency: string): string => {
    return formatMoney(amount, currency, { minDecimals: 0, maxDecimals: 0 })
  }

  const getErrorMessage = (error?: string): string => {
    if (error) return error
    
    const defaultErrors: Record<PaymentProvider, string> = {
      payme: 'Payment failed. Please check your Payme account and try again.',
      click: 'Payment failed. Please check your Click account and try again.',
      visa: 'Payment failed. Please check your card details and try again.',
    }
    return defaultErrors[provider]
  }

  const getHelpfulTips = (provider: PaymentProvider): string[] => {
    const tips: Record<PaymentProvider, string[]> = {
      payme: [
        'Ensure you have sufficient funds in your Payme account',
        'Check your internet connection',
        'Verify your Payme account is active',
      ],
      click: [
        'Ensure you have sufficient funds in your Click account',
        'Check your internet connection',
        'Verify your Click account is active',
      ],
      visa: [
        'Check your card details are correct',
        'Ensure you have sufficient funds',
        'Verify your card is not expired',
        'Check with your bank if the transaction was declined',
      ],
    }
    return tips[provider]
  }

  const helpfulTips = getHelpfulTips(provider)

  return (
    <div className="payment-failure">
      <div className="payment-failure-header">
        <div className="payment-failure-icon" aria-hidden="true"><CircleX size={48} /></div>
        <h2 className="payment-failure-title">Payment Failed</h2>
        <p className="payment-failure-subtitle">
          We couldn't process your payment
        </p>
      </div>

      <div className="payment-failure-content">
        <div className="payment-failure-error" role="alert" aria-live="assertive">
          <div className="payment-failure-error-icon" aria-hidden="true"><TriangleAlert size={24} /></div>
          <div className="payment-failure-error-text">
            <strong>Error:</strong>
            <p>{getErrorMessage(error)}</p>
          </div>
        </div>

        <div className="payment-failure-details">
          <div className="payment-failure-detail">
            <span className="payment-failure-detail-label">Provider:</span>
            <span className="payment-failure-detail-value">{getProviderName(provider)}</span>
          </div>
          <div className="payment-failure-detail">
            <span className="payment-failure-detail-label">Amount:</span>
            <span className="payment-failure-detail-value">
              {formatAmount(amount, currency)}
            </span>
          </div>
        </div>

        <div className="payment-failure-tips">
          <h3 className="payment-failure-tips-title">What you can try:</h3>
          <ul className="payment-failure-tips-list">
            {helpfulTips.map((tip, index) => (
              <li key={index} className="payment-failure-tips-item">
                {tip}
              </li>
            ))}
          </ul>
        </div>

        <div className="payment-failure-support">
          <p className="payment-failure-support-text">
            If the problem persists, please contact our support team for assistance.
          </p>
        </div>
      </div>

      <div className="payment-failure-actions">
        <button 
          className="btn btn-primary btn-large"
          onClick={onRetry}
          aria-label="Retry payment"
        >
          Try Again
        </button>
        <button 
          className="btn btn-secondary"
          onClick={onTryDifferentMethod}
          aria-label="Try a different payment method"
        >
          Try Different Payment Method
        </button>
        <button 
          className="btn btn-link"
          onClick={onCancel}
          aria-label="Cancel booking"
        >
          Cancel Booking
        </button>
      </div>
    </div>
  )
}
