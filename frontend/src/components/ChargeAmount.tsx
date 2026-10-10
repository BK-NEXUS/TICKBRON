import { useI18n } from '../i18n/I18nContext'
import type { ExchangeRateInfo } from '../adapters/bookingAdapter'
import { chargeOf } from '../utils/charge'

interface ChargedBooking {
  total_price: number | string
  currency: string
  charge_amount?: string
  charge_currency?: string
  exchange_rate?: ExchangeRateInfo | null
}

interface ChargeProps {
  booking: ChargedBooking
}

/** The amount the guest is charged, as the backend stored it (the so'm snapshot for a hotel priced in dollars). */
export function ChargeMain({ booking }: ChargeProps) {
  const { formatMoney } = useI18n()
  const charge = chargeOf(booking)
  return <>{formatMoney(charge.amount, charge.currency, { minDecimals: 0, maxDecimals: 2 })}</>
}

/**
 * What goes with the charge when the hotel is priced in another currency: the hotel's own price after a
 * "≈", the date of the CBU rate, and a warning when that rate may be out of date. Nothing for a booking
 * that is charged in its own currency. All numbers come from the backend; nothing is converted here.
 */
export function ChargeNotes({ booking }: ChargeProps) {
  const { t, formatMoney, formatDate } = useI18n()
  const charge = chargeOf(booking)
  if (charge.currency === booking.currency) return null
  const rate = booking.exchange_rate
  return (
    <div className="charge-notes">
      <span className="charge-approx">
        {t('charge.approx', { amount: formatMoney(booking.total_price, booking.currency, { minDecimals: 0, maxDecimals: 2 }) })}
      </span>
      {rate?.date && <small className="charge-rate">{t('charge.rateOf', { date: formatDate(rate.date) })}</small>}
      {rate?.stale && <small className="charge-stale">{t('charge.rateStale')}</small>}
    </div>
  )
}
