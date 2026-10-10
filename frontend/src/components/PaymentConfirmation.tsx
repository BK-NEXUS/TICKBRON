import { useState } from 'react'
import { Check, Copy, Mail, Smartphone } from 'lucide-react'
import { PaymentTransaction, PaymentProvider } from '../adapters/paymentAdapter'
import { useI18n } from '../i18n/I18nContext'
import type { NoShowRefundInfo } from '../adapters/noShowAdapter'
import { NoShowRefundNote } from './NoShowRefundNote'

interface PaymentConfirmationProps {
  payment: PaymentTransaction
  bookingDetails: {
    property_name: string
    check_in: string
    check_out: string
    confirmation_code: string
  }
  /** R12b: the no-show refund promise of the booking, repeated here */
  noShowRefund?: NoShowRefundInfo
  onViewBookings: () => void
  onBackToProperty: () => void
}

/**
 * PaymentConfirmation component for displaying successful payment confirmation
 * Shows payment details, booking information, and next steps
 */
const STATUS_NAMES = ['pending', 'processing', 'completed', 'failed', 'refunded', 'partially_refunded'] as const

export function PaymentConfirmation({ 
  payment, 
  bookingDetails, 
  noShowRefund,
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

  const { t, formatMoney, formatDate: formatLocalDate } = useI18n()

  const formatDate = (dateString: string): string =>
    formatLocalDate(dateString, { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })

  const statusText = (STATUS_NAMES as readonly string[]).includes(payment.status)
    ? t(`pay.statusName.${payment.status as (typeof STATUS_NAMES)[number]}`)
    : payment.status.charAt(0).toUpperCase() + payment.status.slice(1)

  const formatAmount = (amount: number | string, currency: string): string => {
    return formatMoney(amount, currency, { minDecimals: 0, maxDecimals: 0 })
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
        <div className="payment-confirmation-icon" aria-hidden="true">✓</div>
        <h2 className="payment-confirmation-title">{t('pay.confirmTitle')}</h2>
        <p className="payment-confirmation-subtitle">
          {t('pay.confirmText')}
        </p>
      </div>

      <div className="payment-confirmation-content">
        <div className="payment-confirmation-section">
          <h3 className="payment-confirmation-section-title">{t('pay.detailsTitle')}</h3>
          <div className="payment-confirmation-details">
            <div className="payment-confirmation-item">
              <span className="payment-confirmation-label">{t('pay.transactionId')}</span>
              <span className="payment-confirmation-value">{payment.idempotency_key}</span>
            </div>
            <div className="payment-confirmation-item">
              <span className="payment-confirmation-label">{t('pay.provider')}</span>
              <span className="payment-confirmation-value">{getProviderName(payment.provider)}</span>
            </div>
            <div className="payment-confirmation-item">
              <span className="payment-confirmation-label">{t('pay.amountPaid')}</span>
              <span className="payment-confirmation-value payment-confirmation-value--amount">
                {formatAmount(payment.amount, payment.currency)}
              </span>
            </div>
            <div className="payment-confirmation-item">
              <span className="payment-confirmation-label">{t('pay.paymentDate')}</span>
              <span className="payment-confirmation-value">
                {formatDate(payment.created_at)}
              </span>
            </div>
            <div className="payment-confirmation-item">
              <span className="payment-confirmation-label">{t('pay.statusLabel')}</span>
              <span className="payment-confirmation-value payment-confirmation-value--status">
                {statusText}
              </span>
            </div>
          </div>
        </div>

        <div className="payment-confirmation-section">
          <h3 className="payment-confirmation-section-title">{t('pay.bookingTitle')}</h3>
          <div className="payment-confirmation-details">
            <div className="payment-confirmation-item payment-confirmation-item--code">
              <span className="payment-confirmation-label">{t('pay.reference')}</span>
              <div className="payment-confirmation-code-container">
                <span className="payment-confirmation-value payment-confirmation-value--code payment-confirmation-value--monospace">
                  {bookingDetails.confirmation_code}
                </span>
                <button
                  className="payment-confirmation-copy-btn"
                  onClick={handleCopyCode}
                  aria-label={t('pay.copyLabel')}
                  title={t('pay.copyLabel')}
                >
                  {copied ? <Check size={16} aria-hidden="true" /> : <Copy size={16} aria-hidden="true" />}
                  {copied ? t('pay.copied') : t('pay.copy')}
                </button>
              </div>
            </div>
            <div className="payment-confirmation-item">
              <span className="payment-confirmation-label">{t('pay.property')}</span>
              <span className="payment-confirmation-value">{bookingDetails.property_name}</span>
            </div>
            <div className="payment-confirmation-item">
              <span className="payment-confirmation-label">{t('pay.checkIn')}</span>
              <span className="payment-confirmation-value">{formatDate(bookingDetails.check_in)}</span>
            </div>
            <div className="payment-confirmation-item">
              <span className="payment-confirmation-label">{t('pay.checkOut')}</span>
              <span className="payment-confirmation-value">{formatDate(bookingDetails.check_out)}</span>
            </div>
          </div>
          <NoShowRefundNote info={noShowRefund} />
        </div>

        <div className="payment-confirmation-info">
          <div className="payment-confirmation-info-item">
            <div className="payment-confirmation-info-icon" aria-hidden="true"><Mail size={24} /></div>
            <div className="payment-confirmation-info-text">
              <strong>{t('pay.emailSent')}</strong>
              <p>{t('pay.emailText')}</p>
            </div>
          </div>
          <div className="payment-confirmation-info-item">
            <div className="payment-confirmation-info-icon" aria-hidden="true"><Smartphone size={24} /></div>
            <div className="payment-confirmation-info-text">
              <strong>{t('pay.manage')}</strong>
              <p>{t('pay.manageText')}</p>
            </div>
          </div>
        </div>
      </div>

      <div className="payment-confirmation-actions">
        <button 
          className="btn btn-primary btn-large"
          onClick={onViewBookings}
          aria-label={t('pay.viewBookingsLabel')}
        >
          {t('pay.viewBookings')}
        </button>
        <button 
          className="btn btn-secondary"
          onClick={onBackToProperty}
          aria-label={t('pay.backToPropertyLabel')}
        >
          {t('pay.backToProperty')}
        </button>
      </div>
    </div>
  )
}
