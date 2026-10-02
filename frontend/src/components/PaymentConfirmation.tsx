import { useState } from 'react'
import { PaymentTransaction, PaymentProvider } from '../adapters/paymentAdapter'
import { Icon } from '../components/Icon'
import { getIcon } from '../components/icons'

interface PaymentConfirmationProps {
  payment: PaymentTransaction
  bookingDetails: {
    property_name: string
    check_in: string
    check_out: string
    confirmation_code: string
  }
  onViewBookings: () => void
  onBackToProperty: () => void
}

/**
 * PaymentConfirmation component for displaying successful payment confirmation
 * Shows payment details, booking information, and next steps
 */
export function PaymentConfirmation({ 
  payment, 
  bookingDetails, 
  onViewBookings, 
  onBackToProperty 
}: PaymentConfirmationProps) {
  const [copied, setCopied] = useState(false)

  const getProviderName = (provider: PaymentProvider): string => {
    const names: Record<PaymentProvider, string> = {
      payme: 'Payme',
      click: 'Click',
      visa: 'Visa',
    }
    return names[provider]
  }

  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    })
  }

  const formatAmount = (amount: number, currency: string): string => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency,
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount)
  }

  const handleCopyCode = async () => {
    try {
      await navigator.clipboard.writeText(bookingDetails.confirmation_code)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (error) {
      console.error('Failed to copy code:', error)
    }
  }

  return (
    <div className="payment-confirmation">
      <div className="payment-confirmation-header">
        <div className="payment-confirmation-icon" aria-hidden="true"><Icon icon={getIcon('check-circle')} size={48} /></div>
        <h2 className="payment-confirmation-title">Payment Successful!</h2>
        <p className="payment-confirmation-subtitle">
          Your payment has been processed successfully
        </p>
      </div>

      <div className="payment-confirmation-content">
        <div className="payment-confirmation-section">
          <h3 className="payment-confirmation-section-title">Payment Details</h3>
          <div className="payment-confirmation-details">
            <div className="payment-confirmation-item">
              <span className="payment-confirmation-label">Transaction ID:</span>
              <span className="payment-confirmation-value">{payment.idempotency_key}</span>
            </div>
            <div className="payment-confirmation-item">
              <span className="payment-confirmation-label">Provider:</span>
              <span className="payment-confirmation-value">{getProviderName(payment.provider)}</span>
            </div>
            <div className="payment-confirmation-item">
              <span className="payment-confirmation-label">Amount Paid:</span>
              <span className="payment-confirmation-value payment-confirmation-value--amount">
                {formatAmount(payment.amount, payment.currency)}
              </span>
            </div>
            <div className="payment-confirmation-item">
              <span className="payment-confirmation-label">Payment Date:</span>
              <span className="payment-confirmation-value">
                {formatDate(payment.created_at)}
              </span>
            </div>
            <div className="payment-confirmation-item">
              <span className="payment-confirmation-label">Status:</span>
              <span className="payment-confirmation-value payment-confirmation-value--status">
                {payment.status.charAt(0).toUpperCase() + payment.status.slice(1)}
              </span>
            </div>
          </div>
        </div>

        <div className="payment-confirmation-section">
          <h3 className="payment-confirmation-section-title">Booking Details</h3>
          <div className="payment-confirmation-details">
            <div className="payment-confirmation-item payment-confirmation-item--code">
              <span className="payment-confirmation-label">Booking Reference:</span>
              <div className="payment-confirmation-code-container">
                <span className="payment-confirmation-value payment-confirmation-value--code payment-confirmation-value--monospace">
                  {bookingDetails.confirmation_code}
                </span>
                <button
                  className="payment-confirmation-copy-btn"
                  onClick={handleCopyCode}
                  aria-label="Copy booking reference code"
                  title="Copy booking reference code"
                >
                  {copied ? <Icon icon={getIcon('check')} size={14} /> : <Icon icon={getIcon('copy')} size={14} />}
                  <span>{copied ? 'Copied' : 'Copy'}</span>
                </button>
              </div>
            </div>
            <div className="payment-confirmation-item">
              <span className="payment-confirmation-label">Property:</span>
              <span className="payment-confirmation-value">{bookingDetails.property_name}</span>
            </div>
            <div className="payment-confirmation-item">
              <span className="payment-confirmation-label">Check-in:</span>
              <span className="payment-confirmation-value">{formatDate(bookingDetails.check_in)}</span>
            </div>
            <div className="payment-confirmation-item">
              <span className="payment-confirmation-label">Check-out:</span>
              <span className="payment-confirmation-value">{formatDate(bookingDetails.check_out)}</span>
            </div>
          </div>
        </div>

        <div className="payment-confirmation-info">
          <div className="payment-confirmation-info-item">
            <div className="payment-confirmation-info-icon" aria-hidden="true"><Icon icon={getIcon('mail')} size={24} /></div>
            <div className="payment-confirmation-info-text">
              <strong>Confirmation email sent</strong>
              <p>You will receive a confirmation email with your booking details shortly.</p>
            </div>
          </div>
          <div className="payment-confirmation-info-item">
            <div className="payment-confirmation-info-icon" aria-hidden="true"><Icon icon={getIcon('smartphone')} size={24} /></div>
            <div className="payment-confirmation-info-text">
              <strong>Manage your booking</strong>
              <p>You can view and manage your booking from your account at any time.</p>
            </div>
          </div>
        </div>
      </div>

      <div className="payment-confirmation-actions">
        <button 
          className="btn btn-primary btn-large"
          onClick={onViewBookings}
          aria-label="View my bookings"
        >
          View My Bookings
        </button>
        <button 
          className="btn btn-secondary"
          onClick={onBackToProperty}
          aria-label="Return to property page"
        >
          Back to Property
        </button>
      </div>
    </div>
  )
}
