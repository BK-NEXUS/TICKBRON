import { describe, it, expect } from 'vitest'
import { chargeOf } from './charge'

describe('chargeOf', () => {
  it('is the charge snapshot of the booking (what the backend will accept as the payment)', () => {
    expect(chargeOf({ total_price: 200, currency: 'USD', charge_amount: '2354590.00', charge_currency: 'UZS' }))
      .toEqual({ amount: '2354590.00', currency: 'UZS' })
  })

  it('falls back to the booking price for a booking without charge fields (charge = price)', () => {
    expect(chargeOf({ total_price: 500, currency: 'USD' })).toEqual({ amount: '500', currency: 'USD' })
    expect(chargeOf({ total_price: '450000.00', currency: 'UZS' })).toEqual({ amount: '450000.00', currency: 'UZS' })
  })

  it('does not mix half a snapshot with the price', () => {
    expect(chargeOf({ total_price: 500, currency: 'USD', charge_amount: '2354590.00' })).toEqual({ amount: '500', currency: 'USD' })
    expect(chargeOf({ total_price: 500, currency: 'USD', charge_currency: 'UZS' })).toEqual({ amount: '500', currency: 'USD' })
  })

  it('treats an empty charge amount as missing', () => {
    expect(chargeOf({ total_price: 500, currency: 'USD', charge_amount: '', charge_currency: 'UZS' })).toEqual({ amount: '500', currency: 'USD' })
  })
})
