import { useI18n } from '../i18n/I18nContext'
import type { ShownPrice } from '../utils/price'

/**
 * Shown under a price when the guest's chosen currency has no rate yet and the price is in another currency:
 * the amount and its sign are the hotel's own, and this says why they are not in the chosen currency.
 */
export function PriceNote({ shown }: { shown: Pick<ShownPrice, 'currency'> }) {
  const { t, currency } = useI18n()
  if (shown.currency === currency) return null
  return <small className="price-note">{t('price.noRate', { currency })}</small>
}
