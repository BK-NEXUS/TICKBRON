// Display helpers for prices in the chosen currency (R16). The backend computes every amount;
// these only pick which of its amounts to show.
import type { RatePlan, RoomType } from '../adapters/propertyAdapter'

export interface ShownPrice {
  amount: string
  currency: string
  /** A conversion at the CBU rate (shown with "≈"), not a price the owner entered */
  approximate: boolean
}

/** The plan's price in `currency`; its main price when the backend has none for it (no rate yet, older API) */
export function priceIn(plan: Pick<RatePlan, 'base_price' | 'currency' | 'prices'>, currency: string): ShownPrice {
  const entry = plan.prices?.[currency]
  if (entry?.amount) {
    return { amount: entry.amount, currency, approximate: entry.source === 'converted' }
  }
  return { amount: String(plan.base_price), currency: plan.currency, approximate: false }
}

/** The lowest price of a room across its rate plans in `currency`; the room's own price when that cannot be told */
export function roomFromPrice(room: Pick<RoomType, 'base_price' | 'currency' | 'rate_plans'>, currency: string): ShownPrice {
  const own: ShownPrice = { amount: String(room.base_price), currency: room.currency, approximate: false }
  const plans = room.rate_plans ?? []
  const shown = plans.map(plan => plan.prices?.[currency])
  if (plans.length === 0 || shown.some(entry => !entry?.amount)) return own
  const lowest = shown.reduce((best, entry) => (Number(entry?.amount) < Number(best?.amount) ? entry : best))
  return { amount: lowest?.amount ?? own.amount, currency, approximate: lowest?.source === 'converted' }
}

/** A calendar night in `currency`: the backend's amount for that night, else the night's own price */
export function nightPriceIn(
  night: { price: number; currency: string; prices?: Record<string, string | null>; converted_currencies?: string[] },
  currency: string,
): ShownPrice {
  const amount = night.prices?.[currency]
  if (amount) {
    return { amount, currency, approximate: night.converted_currencies?.includes(currency) ?? false }
  }
  return { amount: String(night.price), currency: night.currency, approximate: false }
}

/** The "from" price on the hotel page: the lowest room price in `currency`; the hotel's own price when that cannot be told */
export function propertyFromPrice(
  property: { base_price: number; currency: string },
  rooms: Pick<RoomType, 'base_price' | 'currency' | 'rate_plans'>[],
  currency: string,
): ShownPrice {
  const own: ShownPrice = { amount: String(property.base_price), currency: property.currency, approximate: false }
  const shown = rooms.map(room => roomFromPrice(room, currency))
  if (shown.length === 0 || shown.some(price => price.currency !== currency)) return own
  return shown.reduce((best, price) => (Number(price.amount) < Number(best.amount) ? price : best))
}
