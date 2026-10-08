import { PaymentProvider, PaymentStatus } from '../adapters/paymentAdapter'
import { CircleCheck, CircleX, CreditCard, Hourglass, Undo2, type LucideIcon } from 'lucide-react'

interface PaymentProcessingProps {
  provider: PaymentProvider
  amount: number
  currency: string
  status: PaymentStatus
  message?: string
}

/**
 * PaymentProcessing component for displaying payment processing state
 * Shows loading animation and status updates during payment processing
 */
export function PaymentProcessing({ provider, amount, currency, status, message }: PaymentProcessingProps) {
  const getProviderName = (provider: PaymentProvider): string => {
    const names: Record<PaymentProvider, string> = {
      payme: 'Payme',
      click: 'Click',
      visa: 'Visa',
    }
    return names[provider]
  }

  const getStatusMessage = (currentStatus: PaymentStatus): string => {
    if (message) return message
    
    const messages: Record<PaymentStatus, string> = {
      pending: 'Initializing payment...',
      processing: `Processing payment via ${getProviderName(provider)}...`,
      completed: 'Payment completed successfully!',
      failed: 'Payment failed. Please try again.',
      refunded: 'Payment has been refunded.',
      partially_refunded: 'Payment has been partially refunded.',
    }
    return messages[currentStatus]
  }

  const getStatusIcon = (currentStatus: PaymentStatus): LucideIcon => {
    const icons: Record<PaymentStatus, LucideIcon> = {
      pending: Hourglass,
      processing: CreditCard,
      completed: CircleCheck,
      failed: CircleX,
      refunded: Undo2,
      partially_refunded: Undo2,
    }
    return icons[currentStatus]
  }

  const StatusIcon = getStatusIcon(status)
  const isProcessing = status === 'pending' || status === 'processing'
  const isSuccess = status === 'completed'

  return (
    <div className="payment-processing">
      <div className="payment-processing-icon">
        {isProcessing ? (
          <div className="payment-processing-spinner" aria-hidden="true">
            <div className="spinner"></div>
          </div>
        ) : (
          <div className="payment-processing-status-icon" aria-hidden="true">
            <StatusIcon size={48} />
          </div>
        )}
      </div>
      
      <div className="payment-processing-content">
        <h3 className="payment-processing-title">
          {isProcessing ? 'Processing Payment' : isSuccess ? 'Payment Successful' : 'Payment Failed'}
        </h3>
        
        <p className="payment-processing-message" role="status" aria-live="polite">
          {getStatusMessage(status)}
        </p>
        
        <div className="payment-processing-details">
          <div className="payment-processing-detail">
            <span className="payment-processing-detail-label">Provider:</span>
            <span className="payment-processing-detail-value">{getProviderName(provider)}</span>
          </div>
          <div className="payment-processing-detail">
            <span className="payment-processing-detail-label">Amount:</span>
            <span className="payment-processing-detail-value">
              {new Intl.NumberFormat('en-US', {
                style: 'currency',
                currency,
                minimumFractionDigits: 0,
                maximumFractionDigits: 0,
              }).format(amount)}
            </span>
          </div>
          <div className="payment-processing-detail">
            <span className="payment-processing-detail-label">Status:</span>
            <span className={`payment-processing-detail-value payment-processing-detail-value--${status}`}>
              {status.charAt(0).toUpperCase() + status.slice(1)}
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}
