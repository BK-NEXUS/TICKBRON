/** The months ("2030-01") that have at least one date, oldest first */
export function monthsOf(dates: string[]): string[] {
  return [...new Set(dates.map(date => date.slice(0, 7)))].sort()
}

/** The month a list opens on: the first one that is not already over; the last one when all are */
export function openingMonth(months: string[], today: string): string {
  return months.find(month => month >= today.slice(0, 7)) ?? months[months.length - 1]
}
