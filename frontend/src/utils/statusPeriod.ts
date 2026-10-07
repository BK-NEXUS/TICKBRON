// Period choices of the Status sections and the client-side check of a custom range.
// The backend validates again and its message is shown when it disagrees.

export interface DateRange {
  /** YYYY-MM-DD */
  from: string
  to: string
}

export const STATUS_PRESET_PERIODS = [
  { value: 'today', label: 'Today' },
  { value: 'last_7_days', label: 'Last 7 days' },
  { value: 'last_30_days', label: 'Last 30 days' },
  { value: 'this_year', label: 'This year' },
  { value: 'last_5_years', label: 'Last 5 years' },
  { value: 'last_10_years', label: 'Last 10 years' },
] as const

export const CUSTOM_RANGE_MAX_YEARS = 20

const TEXT = {
  both: 'Choose both dates.',
  order: '"From" must not be after "To".',
  tooLong: `The range can be at most ${CUSTOM_RANGE_MAX_YEARS} years.`,
}

function addYears(isoDate: string, years: number): string {
  const [year, month, day] = isoDate.split('-').map(Number)
  return new Date(Date.UTC(year + years, month - 1, day)).toISOString().slice(0, 10)
}

/** Returns the message to show, or null when the range is acceptable */
export function validateCustomRange(from: string, to: string): string | null {
  if (!from || !to) return TEXT.both
  if (from > to) return TEXT.order
  if (to > addYears(from, CUSTOM_RANGE_MAX_YEARS)) return TEXT.tooLong
  return null
}
