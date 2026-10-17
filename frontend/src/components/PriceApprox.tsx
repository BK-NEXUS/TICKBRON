import { useI18n } from '../i18n/I18nContext'
import type { ExchangeRateInfo } from '../adapters/bookingAdapter'

interface PriceApproxProps {
  /** `base_price_uzs_approx` from the backend: whole so'm as a string, null while no rate exists yet */
  approx?: string | null
  rate?: ExchangeRateInfo | null
  /** The date of the CBU rate and the out-of-date warning (the property page; cards stay compact) */
  showRate?: boolean
}

/** "≈ 1 177 295 so'm" next to the price of a hotel priced in dollars. Informational: the charge comes from the booking. */
export function PriceApprox({ approx, rate, showRate = false }: PriceApproxProps) {
  const { t, formatMoney, formatDate } = useI18n()
  if (approx === null || approx === undefined) return null
  return (
    <span className="price-approx">
      <span className="price-approx-amount">
        {t('charge.approx', { amount: formatMoney(approx, 'UZS', { minDecimals: 0, maxDecimals: 0 }) })}
      </span>
      {showRate && rate?.date && <small className="charge-rate">{t('charge.rateOf', { date: formatDate(rate.date) })}</small>}
      {showRate && rate?.stale && <small className="charge-stale">{t('charge.rateStale')}</small>}
    </span>
  )
}
