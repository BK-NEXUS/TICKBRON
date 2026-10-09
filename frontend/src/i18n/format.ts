import type { Language } from './options'

const NBSP = ' '
const UZS_SUFFIX: Record<Language, string> = { uz: "so'm", ru: 'сум', en: 'UZS' }

export interface MoneyOptions {
  minDecimals?: number
  maxDecimals?: number
}

// Grouping is done by hand so the output does not depend on the ICU data of the browser or Node
const group = (digits: string, separator: string) => digits.replace(/\B(?=(\d{3})+(?!\d))/g, separator)

function formatOther(value: number, currency: string, options: MoneyOptions): string {
  const digits: Intl.NumberFormatOptions = {}
  if (options.minDecimals !== undefined) digits.minimumFractionDigits = options.minDecimals
  if (options.maxDecimals !== undefined) digits.maximumFractionDigits = options.maxDecimals
  try {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency, ...digits }).format(value)
  } catch {
    // Not an ISO 4217 code: show it as it is
    return `${currency} ${new Intl.NumberFormat('en-US', { minimumFractionDigits: 2, ...digits }).format(value)}`
  }
}

/**
 * Display only: the backend computes every amount. Accepts the decimal strings the API returns.
 * UZS is written in whole sums with the word of the page language; every other code the English way.
 */
export function formatMoney(
  amount: number | string,
  currency: string,
  language: Language,
  options: MoneyOptions = {},
): string {
  const value = Number(amount)
  if (!Number.isFinite(value)) return '—'

  if (currency === 'UZS') {
    const sign = value < 0 ? '-' : ''
    return `${sign}${group(String(Math.round(Math.abs(value))), NBSP)}${NBSP}${UZS_SUFFIX[language]}`
  }
  return formatOther(value, currency, options)
}
