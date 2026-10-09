import type { MessageKey } from '../i18n/messages/en'
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

  const { t, formatMoney } = useI18n()

  const formatAmount = (amount: number, currency: string): string => {
    return formatMoney(amount, currency, { minDecimals: 0, maxDecimals: 0 })
  }

  const getErrorMessage = (error?: string): string => {
    if (error) return error
    
    return t(`pay.failDefault.${provider}`)
  }

  const getHelpfulTips = (provider: PaymentProvider): string[] => {
    const tips: Record<PaymentProvider, MessageKey[]> = {
      payme: ['pay.tip.funds.payme', 'pay.tip.internet', 'pay.tip.active.payme'],
      click: ['pay.tip.funds.click', 'pay.tip.internet', 'pay.tip.active.click'],
      visa: ['pay.tip.cardDetails', 'pay.tip.funds.visa', 'pay.tip.expired', 'pay.tip.bank'],
    }
    return tips[provider].map(key => t(key))
  }

  const helpfulTips = getHelpfulTips(provider)

  return (
    <div className="payment-failure">
      <div className="payment-failure-header">
        <div className="payment-failure-icon" aria-hidden="true"><CircleX size={48} /></div>
        <h2 className="payment-failure-title">{t('pay.failTitle')}</h2>
        <p className="payment-failure-subtitle">
          {t('pay.failText')}
        </p>
      </div>

      <div className="payment-failure-content">
        <div className="payment-failure-error" role="alert" aria-live="assertive">
          <div className="payment-failure-error-icon" aria-hidden="true"><TriangleAlert size={24} /></div>
          <div className="payment-failure-error-text">
            <strong>{t('pay.errorLabel')}</strong>
            <p>{getErrorMessage(error)}</p>
          </div>
        </div>

        <div className="payment-failure-details">
          <div className="payment-failure-detail">
            <span className="payment-failure-detail-label">{t('pay.provider')}</span>
            <span className="payment-failure-detail-value">{getProviderName(provider)}</span>
          </div>
          <div className="payment-failure-detail">
            <span className="payment-failure-detail-label">{t('pay.amount')}</span>
            <span className="payment-failure-detail-value">
              {formatAmount(amount, currency)}
            </span>
          </div>
        </div>

        <div className="payment-failure-tips">
          <h3 className="payment-failure-tips-title">{t('pay.tips')}</h3>
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
            {t('pay.support')}
          </p>
        </div>
      </div>

      <div className="payment-failure-actions">
        <button 
          className="btn btn-primary btn-large"
          onClick={onRetry}
          aria-label={t('pay.retryLabel')}
        >
          {t('pay.retry')}
        </button>
        <button 
          className="btn btn-secondary"
          onClick={onTryDifferentMethod}
          aria-label={t('pay.differentMethodLabel')}
        >
          {t('pay.differentMethod')}
        </button>
        <button 
          className="btn btn-link"
          onClick={onCancel}
          aria-label={t('pay.cancelBookingLabel')}
        >
          {t('pay.cancelBooking')}
        </button>
      </div>
    </div>
  )
}
