import { describe, it, expect } from 'vitest'
import { priceIn, roomFromPrice } from './price'
import type { RatePlan, RoomType } from '../adapters/propertyAdapter'

const plan = (patch: Partial<RatePlan> = {}) => ({
  id: 1, base_price: 60, currency: 'USD',
  prices: {
    USD: { amount: '60.00', source: 'main' },
    UZS: { amount: '750000.00', source: 'owner' },
    KZT: { amount: '29388.00', source: 'converted' },
    RUB: { amount: null, source: 'converted' },
  },
  ...patch,
}) as RatePlan

describe('priceIn: the price a guest sees in the chosen currency', () => {
  it('uses the owner\'s own price as it is', () => {
    expect(priceIn(plan(), 'UZS')).toEqual({ amount: '750000.00', currency: 'UZS', approximate: false })
  })

  it('marks a converted price as approximate', () => {
    expect(priceIn(plan(), 'KZT')).toEqual({ amount: '29388.00', currency: 'KZT', approximate: true })
  })

  it('shows the main price when the chosen currency is the main one', () => {
    expect(priceIn(plan(), 'USD')).toEqual({ amount: '60.00', currency: 'USD', approximate: false })
  })

  it('falls back to the main price when the backend has no rate yet', () => {
    expect(priceIn(plan(), 'RUB')).toEqual({ amount: '60', currency: 'USD', approximate: false })
  })

  it('falls back to the main price for an API without price lists', () => {
    expect(priceIn(plan({ prices: undefined }), 'KZT')).toEqual({ amount: '60', currency: 'USD', approximate: false })
  })
})

describe('roomFromPrice: the lowest price of a room across its rate plans', () => {
  const room = (plans: RatePlan[]) => ({ base_price: 55, currency: 'USD', rate_plans: plans }) as RoomType
  const cheaper = plan({
    prices: {
      USD: { amount: '50.00', source: 'main' }, UZS: { amount: '600000.00', source: 'owner' },
      KZT: { amount: '23000.00', source: 'owner' }, RUB: { amount: '4000.00', source: 'owner' },
    },
  })

  it('takes the lowest of the amounts the backend gave in that currency', () => {
    expect(roomFromPrice(room([plan(), cheaper]), 'UZS')).toEqual({ amount: '600000.00', currency: 'UZS', approximate: false })
  })

  it('is approximate when the lowest price is a conversion', () => {
    expect(roomFromPrice(room([plan(), cheaper]), 'KZT')).toEqual({ amount: '23000.00', currency: 'KZT', approximate: false })
    expect(roomFromPrice(room([plan()]), 'KZT')).toEqual({ amount: '29388.00', currency: 'KZT', approximate: true })
  })

  it('shows the room\'s own price when a plan has no amount in the chosen currency or there are no plans', () => {
    expect(roomFromPrice(room([plan(), cheaper]), 'RUB')).toEqual({ amount: '55', currency: 'USD', approximate: false })
    expect(roomFromPrice(room([]), 'UZS')).toEqual({ amount: '55', currency: 'USD', approximate: false })
  })
})
