import { useI18n } from '../i18n/I18nContext'
import type { ExchangeRateInfo } from '../adapters/bookingAdapter'

interface PriceApproxProps {
  /** Backend ten `base_price_uzs_approx`: pútin som qatar retinde, kurs ele joq bolsa null */
  approx?: string | null
  rate?: ExchangeRateInfo | null
  /** CBU kursı sanası hám eskirgen kurs eskertpesi (mehmanxana beti; kartalar ıqsham qaladı) */
  showRate?: boolean
}

/** Dollarda bahalanǵan mehmanxananıń bahası janında "≈ 1 177 295 som". Maǵlıwmat ushın: alınatuǵın summa bronnan keledi. */
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
