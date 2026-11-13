import { useI18n } from '../i18n/I18nContext'
import type { ShownPrice } from '../utils/price'

/**
 * Mehmannıń tańlaǵan valyutasınıń kursı ele joq hám baha basqa valyutada bolsa baha astında kórsetiledi:
 * summa hám onıń belgisi mehmanxananıń óziki, hám bul olar tańlanǵan valyutada nege emes ekenin aytadı.
 */
export function PriceNote({ shown }: { shown: Pick<ShownPrice, 'currency'> }) {
  const { t, currency } = useI18n()
  if (shown.currency === currency) return null
  return <small className="price-note">{t('price.noRate', { currency })}</small>
}
