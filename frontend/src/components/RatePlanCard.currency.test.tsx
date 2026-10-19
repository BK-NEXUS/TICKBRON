/**
 * R16: a rate plan shows its price in the currency the guest chose: the owner's own price as it is,
 * a conversion with ≈. The amounts come from the backend.
 */
import { describe, it, expect, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { RatePlanCard } from './RatePlanCard'
import { RoomCard } from './RoomCard'
import { I18nProvider } from '../i18n/I18nContext'
import type { RatePlan, RoomType } from '../adapters/propertyAdapter'

const plan = (patch: Partial<RatePlan> = {}) => ({
  id: 1, name: 'Standard Rate', slug: 'standard', rate_type: 'standard', description: '', base_price: 60,
  currency: 'USD', min_nights: 1, max_nights: 30, is_active: true, cancellation_policy: 'flexible',
  deposit_required: false,
  prices: {
    USD: { amount: '60.00', source: 'main' },
    UZS: { amount: '750000.00', source: 'owner' },
    KZT: { amount: '29388.00', source: 'converted' },
    RUB: { amount: null, source: 'converted' },
  },
  ...patch,
}) as RatePlan

const inCurrency = (code: string, ui: JSX.Element) => {
  localStorage.setItem('tickbron.currency', code)
  return render(<I18nProvider>{ui}</I18nProvider>)
}

describe('prices in the chosen currency', () => {
  beforeEach(() => {
    localStorage.clear()
    localStorage.setItem('tickbron.language', 'en')
  })

  it('the owner\'s own so\'m price, with no ≈', () => {
    const { container } = inCurrency('UZS', <RatePlanCard ratePlan={plan()} />)
    expect(container.querySelector('.rate-plan-card-price-value')).toHaveTextContent(/^750.000.UZS$/)
  })

  it('a converted tenge price carries ≈', () => {
    const { container } = inCurrency('KZT', <RatePlanCard ratePlan={plan()} />)
    expect(container.querySelector('.rate-plan-card-price-value')).toHaveTextContent(/^≈ .*29,388$/)
  })

  it('the main price in its own currency', () => {
    const { container } = inCurrency('USD', <RatePlanCard ratePlan={plan()} />)
    expect(container.querySelector('.rate-plan-card-price-value')).toHaveTextContent(/^\$60$/)
  })

  it('shows the main price when the backend has no amount for the chosen currency yet', () => {
    const { container } = inCurrency('RUB', <RatePlanCard ratePlan={plan()} />)
    expect(container.querySelector('.rate-plan-card-price-value')).toHaveTextContent(/^\$60$/)
  })

  it('a room shows the lowest price of its rate plans in the chosen currency', () => {
    const cheap = plan({
      id: 2, prices: {
        USD: { amount: '50.00', source: 'main' }, UZS: { amount: '600000.00', source: 'owner' },
        KZT: { amount: '23000.00', source: 'owner' }, RUB: { amount: '4000.00', source: 'owner' },
      },
    })
    const room = {
      id: 1, name: 'Deluxe', slug: 'deluxe', description: '', base_occupancy: 2, max_occupancy: 2, base_price: 60,
      currency: 'USD', total_rooms: 3, bed_configuration: '1 King', rate_plans: [plan(), cheap],
    } as RoomType
    const { container } = inCurrency('UZS', <RoomCard room={room} />)
    expect(container.querySelector('.room-card-price-value')).toHaveTextContent(/^600.000.UZS$/)
  })
})
