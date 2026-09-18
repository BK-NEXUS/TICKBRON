import { RatePlan } from '../adapters/propertyAdapter'

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
  const formatPrice = (price: number, currencyCode: string) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currencyCode,
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(price)
  }

  const formatRateType = (rateType: string) => {
    switch (rateType) {
      case 'standard':
        return 'Standard'
      case 'non_refundable':
        return 'Non-Refundable'
      case 'early_bird':
        return 'Early Bird'
      case 'last_minute':
        return 'Last Minute'
      case 'long_stay':
        return 'Long Stay'
      case 'seasonal':
        return 'Seasonal'
      case 'corporate':
        return 'Corporate'
      case 'promo':
        return 'Promotional'
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
          <span className="rate-plan-card-price-period">per night</span>
        </div>
      </div>

      <p className="rate-plan-card-description">{ratePlan.description}</p>

      <div className="rate-plan-card-details">
        <div className="rate-plan-card-detail">
          <span className="rate-plan-card-detail-label">Minimum Stay</span>
          <span className="rate-plan-card-detail-value">{ratePlan.min_nights} night{ratePlan.min_nights !== 1 ? 's' : ''}</span>
        </div>

        <div className="rate-plan-card-detail">
          <span className="rate-plan-card-detail-label">Maximum Stay</span>
          <span className="rate-plan-card-detail-value">{ratePlan.max_nights} night{ratePlan.max_nights !== 1 ? 's' : ''}</span>
        </div>

        <div className="rate-plan-card-detail">
          <span className="rate-plan-card-detail-label">Cancellation</span>
          <span className="rate-plan-card-detail-value">{ratePlan.cancellation_policy}</span>
        </div>

        {ratePlan.deposit_required && ratePlan.deposit_percentage && (
          <div className="rate-plan-card-detail rate-plan-card-detail--deposit">
            <span className="rate-plan-card-detail-label">Deposit Required</span>
            <span className="rate-plan-card-detail-value">{ratePlan.deposit_percentage}%</span>
          </div>
        )}

        {ratePlan.advance_booking_days && (
          <div className="rate-plan-card-detail">
            <span className="rate-plan-card-detail-label">Advance Booking</span>
            <span className="rate-plan-card-detail-value">{ratePlan.advance_booking_days} days</span>
          </div>
        )}
      </div>

      {isSelected && (
        <div className="rate-plan-card-selected-indicator" aria-label="Selected rate plan">
          ✓ Selected
        </div>
      )}
    </div>
  )
}