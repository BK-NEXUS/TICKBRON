import { describe, it, expect } from 'vitest'
import { nightPriceIn, priceIn, propertyFromPrice, roomFromPrice } from './price'
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

describe('nightPriceIn: a calendar night in the chosen currency', () => {
  const night = { price: 60, currency: 'USD', prices: { USD: '60.00', UZS: '862500.00', KZT: '31050.00', RUB: null }, converted_currencies: ['KZT'] }

  it('takes the amount of the backend and marks a converted currency', () => {
    expect(nightPriceIn(night, 'UZS')).toEqual({ amount: '862500.00', currency: 'UZS', approximate: false })
    expect(nightPriceIn(night, 'KZT')).toEqual({ amount: '31050.00', currency: 'KZT', approximate: true })
  })

  it('falls back to the night\'s own price when the backend has no amount (no rate) or no price list', () => {
    expect(nightPriceIn(night, 'RUB')).toEqual({ amount: '60', currency: 'USD', approximate: false })
    expect(nightPriceIn({ price: 60, currency: 'USD' }, 'UZS')).toEqual({ amount: '60', currency: 'USD', approximate: false })
  })
})

describe('propertyFromPrice: the price on the hotel page', () => {
  const property = { base_price: 60, currency: 'USD' }
  const rooms = (...amounts: string[]) => amounts.map(amount => ({
    base_price: 60, currency: 'USD',
    rate_plans: [{ base_price: 60, currency: 'USD', prices: { UZS: { amount, source: 'owner' as const } } }],
  })) as unknown as RoomType[]

  it('is the lowest of the rooms\' prices in the chosen currency', () => {
    expect(propertyFromPrice(property, rooms('900000.00', '750000.00'), 'UZS'))
      .toEqual({ amount: '750000.00', currency: 'UZS', approximate: false })
  })

  it('is the hotel\'s own price when a room cannot tell or there are no rooms', () => {
    expect(propertyFromPrice(property, rooms('900000.00'), 'KZT')).toEqual({ amount: '60', currency: 'USD', approximate: false })
    expect(propertyFromPrice(property, [], 'UZS')).toEqual({ amount: '60', currency: 'USD', approximate: false })
  })
})
