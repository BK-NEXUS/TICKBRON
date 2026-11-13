interface Chargeable {
  total_price: number | string
  currency: string
  charge_amount?: string
  charge_currency?: string
}

/**
 * Mehmannan bron ushın ne alınatuǵını, backend saqlaǵanday (tólem oǵan sáykes bolıwı kerek).
 * UZS alıw snapshot ınan aldın jasalǵan bronda ol joq: onıń alınatuǵını óz valyutasındaǵı bahası.
 */
export function chargeOf(booking: Chargeable): { amount: string; currency: string } {
  if (booking.charge_amount && booking.charge_currency) {
    return { amount: booking.charge_amount, currency: booking.charge_currency }
  }
  return { amount: String(booking.total_price), currency: booking.currency }
}
