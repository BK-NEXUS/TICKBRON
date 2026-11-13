// Tańlanǵan valyutadaǵı bahalar ushın kórsetiw járdemshileri (R16). Backend hár summanı esaplaydı;
// bular tek onıń qaysı summasın kórsetiwdi tańlaydı.
import type { RatePlan, RoomType } from '../adapters/propertyAdapter'

export interface ShownPrice {
  amount: string
  currency: string
  /** CBU kursı boyınsha konvertaciya ("≈" menen kórsetiledi), iye kirgizgen baha emes */
  approximate: boolean
}

/** Plannıń `currency` degi bahası; backend te joq bolsa onıń tiykarǵı bahası (ele kurs joq, eski API) */
export function priceIn(plan: Pick<RatePlan, 'base_price' | 'currency' | 'prices'>, currency: string): ShownPrice {
  const entry = plan.prices?.[currency]
  if (entry?.amount) {
    return { amount: entry.amount, currency, approximate: entry.source === 'converted' }
  }
  return { amount: String(plan.base_price), currency: plan.currency, approximate: false }
}

/** Xonanıń rate plan ları arasındaǵı `currency` degi eń arzan bahası; anıqlap bolmasa xonanıń óz bahası */
export function roomFromPrice(room: Pick<RoomType, 'base_price' | 'currency' | 'rate_plans'>, currency: string): ShownPrice {
  const own: ShownPrice = { amount: String(room.base_price), currency: room.currency, approximate: false }
  const plans = room.rate_plans ?? []
  const shown = plans.map(plan => plan.prices?.[currency])
  if (plans.length === 0 || shown.some(entry => !entry?.amount)) return own
  const lowest = shown.reduce((best, entry) => (Number(entry?.amount) < Number(best?.amount) ? entry : best))
  return { amount: lowest?.amount ?? own.amount, currency, approximate: lowest?.source === 'converted' }
}

/** `currency` degi kalendar túni: sol tún ushın backend tiń summası, bolmasa túnniń óz bahası */
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

/** Mehmanxana betindegi "dan" bahası: `currency` degi eń arzan xona bahası; anıqlap bolmasa mehmanxananıń óz bahası */
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
