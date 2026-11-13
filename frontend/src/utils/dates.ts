/**
 * Backend "búgin" ushın paydalanatuǵın waqıt zonası (settings.BUSINESS_TIME_ZONE, common/dates.py).
 * Bron sanaları oǵan qarata bahalanadı, sol sebepli aldıńǵı waqıt zonasındaǵı mehman Tashkent te aldınan ótip
 * ketken kúnge usınılmawı kerek: bos orın sorawı biykar etiler edi.
 */
export const BUSINESS_TIME_ZONE = 'Asia/Tashkent'

/** Búgingi sana (YYYY-MM-DD) is waqıt zonasında, brauzerdiki emes */
export function businessToday(now: Date = new Date()): string {
  return new Intl.DateTimeFormat('en-CA', {
    timeZone: BUSINESS_TIME_ZONE, year: 'numeric', month: '2-digit', day: '2-digit',
  }).format(now)
}

/** Jergilikli waqıttaǵı YYYY-MM-DD */
export function toLocalDate(date: Date): string {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
}

/** "Mon, Sep 28" */
export function formatDay(date: string): string {
  const [year, month, day] = date.split('-').map(Number)
  return new Date(year, month - 1, day).toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })
}

/** sana +/- n kún (n teris bolıwı múmkin), YYYY-MM-DD retinde */
export function addDays(date: string, days: number): string {
  const [year, month, day] = date.split('-').map(Number)
  return toLocalDate(new Date(year, month - 1, day + days))
}

/** Turıwdıń hár túni: [checkIn, checkOut) */
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
