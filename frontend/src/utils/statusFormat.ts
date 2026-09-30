// Number formatting for the Status sections (admin and partner): thousand separators,
// one amount per currency (never added together).

import type { Money, StatusMonth } from '../adapters/statusAdapter'

const COUNT = new Intl.NumberFormat('en-US')
const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
const MONTH_NAMES = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August',
  'September', 'October', 'November', 'December']

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

/** "2026-04" -> "Apr" */
export function monthLabel(month: string): string {
  return MONTHS[Number(month.slice(5, 7)) - 1] ?? month
}

/** "all" -> "All time", "2026" -> "2026", "2026-04" -> "April 2026" */
export function periodLabel(period: string): string {
  if (period === 'all') return 'All time'
  if (/^\d{4}-\d{2}$/.test(period)) return `${MONTH_NAMES[Number(period.slice(5)) - 1]} ${period.slice(0, 4)}`
  return period
}

export function formatDate(value: string): string {
  // Date-only strings are calendar days: format them without a time zone shift
  const date = /^\d{4}-\d{2}-\d{2}$/.test(value) ? new Date(`${value}T00:00:00`) : new Date(value)
  return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })
}

/** Currencies with revenue in a monthly series, the largest total first (the chart's default) */
export function chartCurrencies(months: StatusMonth[]): string[] {
  const sums = new Map<string, number>()
  months.forEach(month => month.revenue.forEach(({ currency, amount }) => {
    sums.set(currency, (sums.get(currency) ?? 0) + Number(amount))
  }))
  return [...sums.entries()].sort((a, b) => b[1] - a[1]).map(([currency]) => currency)
}
