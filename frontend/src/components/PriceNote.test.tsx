/** A currency without a rate must not silently show another one: the guest is told which currency has no rate yet. */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { PriceNote } from './PriceNote'
import { PropertyCard } from './PropertyCard'
import { RatePlanCard } from './RatePlanCard'
import { RoomCard } from './RoomCard'
import { I18nProvider } from '../i18n/I18nContext'
import type { Property, RatePlan, RoomType } from '../adapters/propertyAdapter'

vi.mock('react-router', () => ({ useNavigate: () => vi.fn() }))

const prices = {
  USD: { amount: '60.00', source: 'main' }, UZS: { amount: '750000.00', source: 'owner' },
  KZT: { amount: '29388.00', source: 'converted' }, RUB: { amount: null, source: 'converted' },
}
const plan = { id: 1, name: 'Standard Rate', slug: 'standard', rate_type: 'standard', description: '', base_price: 60, currency: 'USD',
  min_nights: 1, max_nights: 30, is_active: true, cancellation_policy: 'flexible', deposit_required: false, prices } as unknown as RatePlan
const room = { id: 1, name: 'Double', base_price: 60, currency: 'USD', max_occupancy: 2, rate_plans: [plan] } as unknown as RoomType
const property = { id: 1, owner_id: 1, property_type: { id: 1, name: 'Hotel', slug: 'hotel' }, status: 'active', max_guests: 2, bedrooms: 1,
  bathrooms: 1, address_line1: '1 Main', city: 'Tashkent', country: 'Uzbekistan', base_price: 60, currency: 'USD', has_wifi: true,
  has_parking: false, has_ac: true, has_heating: true, has_elevator: false, prices,
  translations: [{ language: 'en', name: 'Silk Road Hotel', description: '' }] } as unknown as Property

const show = (code: string, ui: JSX.Element) => {
  localStorage.setItem('tickbron.currency', code)
  return render(<I18nProvider>{ui}</I18nProvider>)
}

describe('PriceNote', () => {
  beforeEach(() => { localStorage.clear(); localStorage.setItem('tickbron.language', 'en') })

  it('says which currency has no rate yet when another currency is shown instead', () => {
    show('RUB', <PriceNote shown={{ amount: '60', currency: 'USD', approximate: false }} />)
    expect(screen.getByText('RUB rate is not available yet')).toBeInTheDocument()
  })

  it('says nothing when the price is in the chosen currency', () => {
    show('USD', <PriceNote shown={{ amount: '60', currency: 'USD', approximate: false }} />)
    expect(screen.queryByText(/not available yet/)).not.toBeInTheDocument()
  })

  it('is on a hotel card, a room and a rate plan when the chosen currency has no rate', () => {
    for (const ui of [<PropertyCard key="p" property={property} />, <RoomCard key="r" room={room} />, <RatePlanCard key="t" ratePlan={plan} />]) {
      const { unmount } = show('RUB', ui)
      expect(screen.getByText('RUB rate is not available yet')).toBeInTheDocument()
      unmount()
    }
  })

  it('is not on the cards when the currency has a price (a conversion or the own one)', () => {
    for (const code of ['KZT', 'UZS', 'USD']) {
      const { unmount } = show(code, <PropertyCard property={property} />)
      expect(screen.queryByText(/not available yet/)).not.toBeInTheDocument()
      unmount()
    }
  })
})
