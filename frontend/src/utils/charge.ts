interface Chargeable {
  total_price: number | string
  currency: string
  charge_amount?: string
  charge_currency?: string
}

/**
 * What the guest is charged for a booking, exactly as the backend stored it (the payment must match it).
 * A booking made before the UZS charge snapshot has none: its charge is its price in its own currency.
 */
export function chargeOf(booking: Chargeable): { amount: string; currency: string } {
  if (booking.charge_amount && booking.charge_currency) {
    return { amount: booking.charge_amount, currency: booking.charge_currency }
  }
  return { amount: String(booking.total_price), currency: booking.currency }
}
