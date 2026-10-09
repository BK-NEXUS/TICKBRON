import type { Currency, Language } from './options'

const NBSP = ' '
const UZS_SUFFIX: Record<Language, string> = { uz: "so'm", ru: 'сум', en: 'UZS' }

// Grouping is done by hand so the output does not depend on the ICU data of the browser or Node
const group = (digits: string, separator: string) => digits.replace(/\B(?=(\d{3})+(?!\d))/g, separator)

/** Display only: the backend computes every amount. Accepts the decimal strings the API returns. */
export function formatMoney(amount: number | string, currency: Currency, language: Language): string {
  const value = Number(amount)
  if (!Number.isFinite(value)) return '—'

  const sign = value < 0 ? '-' : ''
  if (currency === 'UZS') {
    const whole = String(Math.round(Math.abs(value)))
    return `${sign}${group(whole, NBSP)}${NBSP}${UZS_SUFFIX[language]}`
  }
  const [whole, cents] = Math.abs(value).toFixed(2).split('.')
  return `${sign}$${group(whole, ',')}.${cents}`
}
