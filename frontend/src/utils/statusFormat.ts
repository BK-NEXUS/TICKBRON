// Number formatting for the Status sections (admin and partner): thousand separators,
// one amount per currency (never added together).

import type { Money } from '../adapters/statusAdapter'
import { STATUS_PRESET_PERIODS } from './statusPeriod'
import { englishI18n, type I18nValue } from '../i18n/I18nContext'

const COUNT = new Intl.NumberFormat('en-US')

export function formatCount(value: number): string {
  return COUNT.format(value)
}

export function formatMoney({ currency, amount }: Money): string {
  const value = Number(amount)
  try {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency, minimumFractionDigits: 2 }).format(value)
  } catch {
    // Not an ISO 4217 code: show it as it is
    return `${currency} ${new Intl.NumberFormat('en-US', { minimumFractionDigits: 2 }).format(value)}`
  }
}

/** "€60.00 · $530.00", or a dash when there is none */
export function formatMoneyList(list: Money[]): string {
  return list.length ? list.map(formatMoney).join(' · ') : '—'
}

/** "2026-04" -> "Apr" (in the page language) */
export function monthLabel(month: string, i18n: I18nValue = englishI18n): string {
  return /^\d{4}-\d{2}$/.test(month) ? i18n.formatDate(`${month}-01`, { month: 'short' }) : month
}

/** "all" -> "All time", "last_7_days" -> "Last 7 days", "2026-04" -> "April 2026", custom -> its dates */
export function periodLabel(
  period: string,
  range?: { from: string | null; to: string | null },
  i18n: I18nValue = englishI18n,
): string {
  if (period === 'all') return i18n.t('status.all')
  if (period === 'custom') return range?.from && range.to ? `${range.from} – ${range.to}` : i18n.t('status.custom')
  const preset = STATUS_PRESET_PERIODS.find(item => item.value === period)
  if (preset) return i18n.t(preset.labelKey)
  if (/^\d{4}-\d{2}$/.test(period)) return i18n.formatDate(`${period}-01`, { month: 'long', year: 'numeric' })
  return period
}

export function formatDate(value: string, i18n: I18nValue = englishI18n): string {
  return i18n.formatDate(value)
}

/** Currencies with revenue in a series, the largest total first (the chart's default) */
export function chartCurrencies(months: { revenue: Money[] }[]): string[] {
  const sums = new Map<string, number>()
  months.forEach(month => month.revenue.forEach(({ currency, amount }) => {
    sums.set(currency, (sums.get(currency) ?? 0) + Number(amount))
  }))
  return [...sums.entries()].sort((a, b) => b[1] - a[1]).map(([currency]) => currency)
}
