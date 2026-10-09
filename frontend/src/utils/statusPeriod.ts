import { englishI18n, type I18nValue } from '../i18n/I18nContext'
// Period choices of the Status sections and the client-side check of a custom range.
// The backend validates again and its message is shown when it disagrees.

export interface DateRange {
  /** YYYY-MM-DD */
  from: string
  to: string
}

export const STATUS_PRESET_PERIODS = [
  { value: 'today', label: 'Today', labelKey: 'status.today' },
  { value: 'last_7_days', label: 'Last 7 days', labelKey: 'status.last7Days' },
  { value: 'last_30_days', label: 'Last 30 days', labelKey: 'status.last30Days' },
  { value: 'this_year', label: 'This year', labelKey: 'status.thisYear' },
  { value: 'last_5_years', label: 'Last 5 years', labelKey: 'status.last5Years' },
  { value: 'last_10_years', label: 'Last 10 years', labelKey: 'status.last10Years' },
] as const

export const CUSTOM_RANGE_MAX_YEARS = 20

function addYears(isoDate: string, years: number): string {
  const [year, month, day] = isoDate.split('-').map(Number)
  return new Date(Date.UTC(year + years, month - 1, day)).toISOString().slice(0, 10)
}

/** Returns the message to show (in the page language), or null when the range is acceptable */
export function validateCustomRange(from: string, to: string, i18n: I18nValue = englishI18n): string | null {
  if (!from || !to) return i18n.t('status.chooseBoth')
  if (from > to) return i18n.t('status.rangeOrder')
  if (to > addYears(from, CUSTOM_RANGE_MAX_YEARS)) return i18n.t('status.rangeTooLong', { years: CUSTOM_RANGE_MAX_YEARS })
  return null
}
