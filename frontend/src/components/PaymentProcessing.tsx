import { PaymentProvider, PaymentStatus } from '../adapters/paymentAdapter'
import { CircleCheck, CircleX, CreditCard, Hourglass, Undo2, type LucideIcon } from 'lucide-react'
import { useI18n } from '../i18n/I18nContext'

interface PaymentProcessingProps {
  provider: PaymentProvider
  amount: number | string
  currency: string
  status: PaymentStatus
  message?: string
}

/**
 * PaymentProcessing component for displaying payment processing state
 * Shows loading animation and status updates during payment processing
 */
export function PaymentProcessing({ provider, amount, currency, status, message }: PaymentProcessingProps) {
  const { t, formatMoney } = useI18n()
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
    
    return currentStatus === 'processing'
      ? t('pay.status.processing', { provider: getProviderName(provider) })
      : t(`pay.status.${currentStatus}`)
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
          {isProcessing ? t('pay.processingTitle') : isSuccess ? t('pay.successTitle') : t('pay.failedTitle')}
        </h3>
        
        <p className="payment-processing-message" role="status" aria-live="polite">
          {getStatusMessage(status)}
        </p>
        
        <div className="payment-processing-details">
          <div className="payment-processing-detail">
            <span className="payment-processing-detail-label">{t('pay.provider')}</span>
            <span className="payment-processing-detail-value">{getProviderName(provider)}</span>
          </div>
          <div className="payment-processing-detail">
            <span className="payment-processing-detail-label">{t('pay.amount')}</span>
            <span className="payment-processing-detail-value">
              {formatMoney(amount, currency, { minDecimals: 0, maxDecimals: 0 })}
            </span>
          </div>
          <div className="payment-processing-detail">
            <span className="payment-processing-detail-label">{t('pay.statusLabel')}</span>
            <span className={`payment-processing-detail-value payment-processing-detail-value--${status}`}>
              {status.charAt(0).toUpperCase() + status.slice(1)}
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}
