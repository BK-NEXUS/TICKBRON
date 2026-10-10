/**
 * The time zone the backend uses for "today" (settings.BUSINESS_TIME_ZONE, common/dates.py).
 * Booking dates are judged against it, so a guest in an earlier time zone must not be offered
 * a day that is already past in Tashkent: the availability request would be refused.
 */
export const BUSINESS_TIME_ZONE = 'Asia/Tashkent'

/** Today's date (YYYY-MM-DD) in the business time zone, not the browser's */
export function businessToday(now: Date = new Date()): string {
  return new Intl.DateTimeFormat('en-CA', {
    timeZone: BUSINESS_TIME_ZONE, year: 'numeric', month: '2-digit', day: '2-digit',
  }).format(now)
}

/** YYYY-MM-DD in local time */
export function toLocalDate(date: Date): string {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
}

/** "Mon, Sep 28" */
export function formatDay(date: string): string {
  const [year, month, day] = date.split('-').map(Number)
  return new Date(year, month - 1, day).toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })
}

/** date +/- n days (n may be negative), as YYYY-MM-DD */
export function addDays(date: string, days: number): string {
  const [year, month, day] = date.split('-').map(Number)
  return toLocalDate(new Date(year, month - 1, day + days))
}

/** Every night of a stay: [checkIn, checkOut) */
export function nightsBetween(checkIn: string, checkOut: string): string[] {
  const nights: string[] = []
  const [year, month, day] = checkIn.split('-').map(Number)
  const current = new Date(year, month - 1, day)
  while (toLocalDate(current) < checkOut) {
    nights.push(toLocalDate(current))
    current.setDate(current.getDate() + 1)
  }
  return nights
}
