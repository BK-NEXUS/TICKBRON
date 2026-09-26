/** YYYY-MM-DD in local time */
export function toLocalDate(date: Date): string {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
}

/** "Mon, Sep 28" */
export function formatDay(date: string): string {
  const [year, month, day] = date.split('-').map(Number)
  return new Date(year, month - 1, day).toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })
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
