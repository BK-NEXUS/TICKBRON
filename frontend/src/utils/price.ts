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
