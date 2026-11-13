// Status bólimleri ushın san formatlaw (admin hám partner): mıńlıq ajıratıwshılar,
// hár valyuta ushın bir summa (hesh qashan qosılmaydı).

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
    // ISO 4217 kodı emes: sol qalpında kórsetiw
    return `${currency} ${new Intl.NumberFormat('en-US', { minimumFractionDigits: 2 }).format(value)}`
  }
}

/** Grafik belgisi ushın qısqa summa: "$54.2M", "UZS 1.2K" (tolıq summa barnıń title ında qaladı) */
export function formatMoneyCompact({ currency, amount }: Money): string {
  const value = Number(amount)
  try {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency, notation: 'compact', minimumFractionDigits: 0, maximumFractionDigits: 1 }).format(value)
  } catch {
    return `${currency} ${new Intl.NumberFormat('en-US', { notation: 'compact', maximumFractionDigits: 1 }).format(value)}`
  }
}

/** "€60.00 · $530.00", yamasa joq bolsa sızıqsha */
export function formatMoneyList(list: Money[]): string {
  return list.length ? list.map(formatMoney).join(' · ') : '—'
}

/** Bir baǵanada óz sanlarınıń ishinde úziliwi múmkin karta mánisi: bir neshe valyutadaǵı summalar, yamasa bir uzın summa */
export function isLongValue(value: string): boolean {
  return value.length > 14
}

/** "status-card", hám kartaǵa kerek modifikatorlar (tiykarǵı kórinis, uzın mánis ushın eki baǵana) */
export function statusCardClass(value: string, headline = false): string {
  return ['status-card', headline && 'status-card--headline', isLongValue(value) && 'status-card--wide'].filter(Boolean).join(' ')
}

/** "2026-04" -> "Apr" (bet tilinde) */
export function monthLabel(month: string, i18n: I18nValue = englishI18n): string {
  return /^\d{4}-\d{2}$/.test(month) ? i18n.formatDate(`${month}-01`, { month: 'short' }) : month
}

/** "all" -> "Pútkil waqıt", "last_7_days" -> "Sońǵı 7 kún", "2026-04" -> "Aprel 2026", custom -> onıń sanaları */
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

/** Seriyada dáramatı bar valyutalar, eń úlken jıyındı birinshi (grafiktiń ádetdegisi) */
export function chartCurrencies(months: { revenue: Money[] }[]): string[] {
  const sums = new Map<string, number>()
  months.forEach(month => month.revenue.forEach(({ currency, amount }) => {
    sums.set(currency, (sums.get(currency) ?? 0) + Number(amount))
  }))
  return [...sums.entries()].sort((a, b) => b[1] - a[1]).map(([currency]) => currency)
}
