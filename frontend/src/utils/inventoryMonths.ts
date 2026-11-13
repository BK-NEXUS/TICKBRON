/** Eń keminde bir sanası bar aylar ("2030-01"), eń eskisi birinshi */
export function monthsOf(dates: string[]): string[] {
  return [...new Set(dates.map(date => date.slice(0, 7)))].sort()
}

/** Dizim ashılatuǵın ay: ele pitpegen birinshisi; hámmesi pitken bolsa sońǵısı */
export function openingMonth(months: string[], today: string): string {
  return months.find(month => month >= today.slice(0, 7)) ?? months[months.length - 1]
}
