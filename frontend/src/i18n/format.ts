import type { Language } from './options'

const NBSP = ' '
const UZS_SUFFIX: Record<Language, string> = { uz: "so'm", ru: 'сум', en: 'UZS' }

export interface MoneyOptions {
  minDecimals?: number
  maxDecimals?: number
}

// Toparlaw qolda isleniledi, sol sebepli nátiyje brauzer yamasa Node tiń ICU maǵlıwmatına baylanıslı emes
const group = (digits: string, separator: string) => digits.replace(/\B(?=(\d{3})+(?!\d))/g, separator)

function formatOther(value: number, currency: string, options: MoneyOptions): string {
  const digits: Intl.NumberFormatOptions = {}
  if (options.minDecimals !== undefined) digits.minimumFractionDigits = options.minDecimals
  if (options.maxDecimals !== undefined) digits.maximumFractionDigits = options.maxDecimals
  try {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency, ...digits }).format(value)
  } catch {
    // ISO 4217 kodı emes: sol qalpında kórsetiw
    return `${currency} ${new Intl.NumberFormat('en-US', { minimumFractionDigits: 2, ...digits }).format(value)}`
  }
}

/**
 * Tek kórsetiw ushın: hár summanı backend esaplaydı. API qaytaratuǵın onlıq qatarlardı qabıllaydı.
 * UZS pútin sum menen bet tilindegi sóz menen jazıladı; basqa hár kod inglizsha usılda.
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
