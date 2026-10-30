/** R16: a hotel card shows its "from" price in the chosen currency (≈ for a conversion). The amounts come from the backend. */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render } from '@testing-library/react'
import { PropertyCard } from './PropertyCard'
import { I18nProvider } from '../i18n/I18nContext'
import type { Property } from '../adapters/propertyAdapter'

vi.mock('react-router', () => ({ useNavigate: () => vi.fn() }))

const property = (patch: Partial<Property> = {}) => ({
  id: 1, owner_id: 1, property_type: { id: 1, name: 'Hotel', slug: 'hotel' }, status: 'active', max_guests: 2,
  bedrooms: 1, bathrooms: 1, address_line1: '1 Main', city: 'Tashkent', country: 'Uzbekistan',
  base_price: 60, currency: 'USD', base_price_uzs_approx: '762000.00', has_wifi: true, has_parking: false, has_ac: true,
  has_heating: true, has_elevator: false, translations: [{ language: 'en', name: 'Silk Road Hotel', description: '' }],
  prices: {
    USD: { amount: '60.00', source: 'main' }, UZS: { amount: '750000.00', source: 'owner' },
    KZT: { amount: '29388.00', source: 'converted' }, RUB: { amount: null, source: 'converted' },
  },
  ...patch,
}) as Property

const priceText = (currency: string, item: Property) => {
  localStorage.setItem('tickbron.language', 'en')
  localStorage.setItem('tickbron.currency', currency)
  const { container } = render(<I18nProvider><PropertyCard property={item} /></I18nProvider>)
  return container.querySelector('.property-card-price')
}

describe('PropertyCard price in the chosen currency', () => {
  beforeEach(() => localStorage.clear())

  it('the owner\'s own so\'m price, without the old "≈ so\'m" line', () => {
    const price = priceText('UZS', property())
    expect(price?.querySelector('.property-card-price-value')).toHaveTextContent(/^750.000.UZS$/)
    expect(price?.querySelector('.price-approx')).toBeNull()
  })

  it('a converted tenge price carries ≈', () => {
    expect(priceText('KZT', property())?.querySelector('.property-card-price-value')).toHaveTextContent(/^≈ .*29,388$/)
  })

  it('the hotel\'s own price in its own currency', () => {
    expect(priceText('USD', property())?.querySelector('.property-card-price-value')).toHaveTextContent(/^\$60$/)
  })

  it('an API without price lists keeps the old card: own price and the ≈ so\'m line', () => {
    const price = priceText('KZT', property({ prices: undefined }))
    expect(price?.querySelector('.property-card-price-value')).toHaveTextContent(/^\$60$/)
    expect(price?.querySelector('.price-approx')).toHaveTextContent(/762.000/)
  })
})
