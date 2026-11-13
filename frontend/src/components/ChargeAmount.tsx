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

/** Mehmannan alınatuǵın summa, backend saqlaǵanday (dollarda bahalanǵan mehmanxana ushın som snapshot ı). */
export function ChargeMain({ booking }: ChargeProps) {
  const { formatMoney } = useI18n()
  const charge = chargeOf(booking)
  return <>{formatMoney(charge.amount, charge.currency, { minDecimals: 0, maxDecimals: 2 })}</>
}

/**
 * Mehmanxana basqa valyutada bahalanǵanda alınatuǵın summa menen birge keletuǵın nárse: mehmanxananıń óz bahası
 * "≈" den keyin, CBU kursı sanası, hám sol kurs eskirgen bolıwı múmkin bolsa eskertiw. Óz valyutasında
 * alınatuǵın bron ushın hesh nárse. Barlıq sanlar backend ten keledi; bul jerde hesh nárse konvertaciyalanbaydı.
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
