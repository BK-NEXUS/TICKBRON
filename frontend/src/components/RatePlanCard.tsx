import { Check } from 'lucide-react'
import { RatePlan } from '../adapters/propertyAdapter'
import { useI18n } from '../i18n/I18nContext'

interface RatePlanCardProps {
  ratePlan: RatePlan
  onSelect?: (ratePlanId: number) => void
  isSelected?: boolean
}

/**
 * RatePlanCard component for displaying rate plan options
 * Shows rate plan details, pricing, cancellation policy, and deposit information
 */
export function RatePlanCard({ ratePlan, onSelect, isSelected = false }: RatePlanCardProps) {
  const { t, tp, formatMoney } = useI18n()
  const formatPrice = (price: number, currencyCode: string) => {
    return formatMoney(price, currencyCode, { minDecimals: 0, maxDecimals: 0 })
  }

  const formatRateType = (rateType: string) => {
    switch (rateType) {
      case 'standard':
      case 'non_refundable':
      case 'early_bird':
      case 'last_minute':
      case 'long_stay':
      case 'seasonal':
      case 'corporate':
      case 'promo':
        return t(`rate.${rateType}`)
      default:
        return rateType
          .split('_')
          .map(word => word.charAt(0).toUpperCase() + word.slice(1))
          .join(' ')
    }
  }

  return (
    <div 
      className={`rate-plan-card ${isSelected ? 'rate-plan-card--selected' : ''}`}
      onClick={() => onSelect?.(ratePlan.id)}
      role="button"
      tabIndex={0}
      aria-pressed={isSelected}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault()
          onSelect?.(ratePlan.id)
        }
      }}
    >
      <div className="rate-plan-card-header">
        <div className="rate-plan-card-title-group">
          <h3 className="rate-plan-card-name">{ratePlan.name}</h3>
          <span className="rate-plan-card-type">{formatRateType(ratePlan.rate_type)}</span>
        </div>
        <div className="rate-plan-card-price">
          <span className="rate-plan-card-price-value">
            {formatPrice(ratePlan.base_price, ratePlan.currency)}
          </span>
          <span className="rate-plan-card-price-period">{t('room.perNight')}</span>
        </div>
      </div>

      <p className="rate-plan-card-description">{ratePlan.description}</p>

      <div className="rate-plan-card-details">
        <div className="rate-plan-card-detail">
          <span className="rate-plan-card-detail-label">{t('rate.minStay')}</span>
          <span className="rate-plan-card-detail-value">{tp('rooms.nights', ratePlan.min_nights)}</span>
        </div>

        <div className="rate-plan-card-detail">
          <span className="rate-plan-card-detail-label">{t('rate.maxStay')}</span>
          <span className="rate-plan-card-detail-value">{tp('rooms.nights', ratePlan.max_nights)}</span>
        </div>

        <div className="rate-plan-card-detail">
          <span className="rate-plan-card-detail-label">{t('rate.cancellation')}</span>
          <span className="rate-plan-card-detail-value">{ratePlan.cancellation_policy}</span>
        </div>

        {ratePlan.deposit_required && ratePlan.deposit_percentage && (
          <div className="rate-plan-card-detail rate-plan-card-detail--deposit">
            <span className="rate-plan-card-detail-label">{t('rate.deposit')}</span>
            <span className="rate-plan-card-detail-value">{ratePlan.deposit_percentage}%</span>
          </div>
        )}

        {ratePlan.advance_booking_days && (
          <div className="rate-plan-card-detail">
            <span className="rate-plan-card-detail-label">{t('rate.advance')}</span>
            <span className="rate-plan-card-detail-value">{tp('rate.days', ratePlan.advance_booking_days)}</span>
          </div>
        )}
      </div>

      {isSelected && (
        <div className="rate-plan-card-selected-indicator" aria-label={t('rate.selectedLabel')}>
          <Check size={14} aria-hidden="true" /> {t('rate.selected')}
        </div>
      )}
    </div>
  )
}