import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { render, screen, fireEvent, within } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { PropertiesMapView } from './PropertiesMapView'
import { I18nProvider } from '../i18n/I18nContext'
import type { Property } from '../adapters/propertyAdapter'

const property = (id: number, name: string, latitude: unknown, longitude: unknown, price: number): Property => ({
  id, owner_id: 1, property_type: { id: 1, name: 'Hotel', slug: 'hotel' }, status: 'active',
  max_guests: 2, bedrooms: 1, bathrooms: 1, address_line1: 'Street', city: 'Tashkent', country: 'Uzbekistan',
  base_price: price, currency: 'USD', has_wifi: true, has_parking: false, has_ac: true, has_heating: false, has_elevator: false,
  translations: [{ language: 'en', name, description: '' }], policies: [],
  latitude, longitude, created_at: '2026-01-01T00:00:00Z', updated_at: '2026-01-01T00:00:00Z',
} as unknown as Property)

const alpha = property(1, 'Alpha Hotel', '41.311081', '69.279737', 60)
const beta = property(2, 'Beta Hotel', '39.654823', '66.97567', 55)
const gamma = property(3, 'Gamma Hotel', null, null, 40)

const scrollIntoView = vi.fn()

function renderView(properties: Property[], wide = true) {
  localStorage.setItem('tickbron.language', 'en')
  window.matchMedia = vi.fn().mockReturnValue({ matches: wide, addEventListener: vi.fn(), removeEventListener: vi.fn() }) as unknown as typeof window.matchMedia
  return render(
    <I18nProvider><MemoryRouter><PropertiesMapView properties={properties} onSearchArea={vi.fn()} /></MemoryRouter></I18nProvider>,
  )
}

const listItem = (name: string) => screen.getByRole('list', { name: 'Properties on the map' }).querySelector(`[data-property-name="${name}"]`) as HTMLElement

describe('PropertiesMapView', () => {
  const originalMatchMedia = window.matchMedia
  beforeEach(() => {
    localStorage.clear()
    scrollIntoView.mockClear()
    Element.prototype.scrollIntoView = scrollIntoView
    Object.defineProperty(HTMLElement.prototype, 'clientWidth', { configurable: true, get: () => 800 })
    Object.defineProperty(HTMLElement.prototype, 'clientHeight', { configurable: true, get: () => 500 })
  })
  afterEach(() => {
    window.matchMedia = originalMatchMedia
    delete (HTMLElement.prototype as unknown as Record<string, unknown>).clientWidth
    delete (HTMLElement.prototype as unknown as Record<string, unknown>).clientHeight
  })

  it('lists every property next to the map, also the ones without a location', () => {
    renderView([alpha, beta, gamma])
    const list = screen.getByRole('list', { name: 'Properties on the map' })
    expect(within(list).getAllByRole('listitem')).toHaveLength(3)
    expect(within(list).getByText('Gamma Hotel')).toBeInTheDocument()
    expect(within(listItem('Gamma Hotel')).getByText('No location on the map')).toBeInTheDocument()
    expect(screen.getByRole('region', { name: 'Map of properties' })).toBeInTheDocument()
  })

  it('pointing at a card in the list marks its pin on the map', () => {
    renderView([alpha, beta])
    fireEvent.mouseEnter(listItem('Beta Hotel'))
    expect(screen.getByRole('button', { name: 'Beta Hotel, $55' })).toHaveClass('map-pin--hover')
    fireEvent.mouseLeave(listItem('Beta Hotel'))
    expect(screen.getByRole('button', { name: 'Beta Hotel, $55' })).not.toHaveClass('map-pin--hover')
  })

  it('keyboard focus on a card marks its pin as well', () => {
    renderView([alpha, beta])
    fireEvent.focus(listItem('Alpha Hotel'))
    expect(screen.getByRole('button', { name: 'Alpha Hotel, $60' })).toHaveClass('map-pin--hover')
    fireEvent.blur(listItem('Alpha Hotel'))
    expect(screen.getByRole('button', { name: 'Alpha Hotel, $60' })).not.toHaveClass('map-pin--hover')
  })

  it('choosing a pin marks and scrolls to its card in the list, and shows no second card under the map', () => {
    renderView([alpha, beta])
    fireEvent.click(screen.getByRole('button', { name: 'Beta Hotel, $55' }))
    expect(listItem('Beta Hotel')).toHaveAttribute('aria-current', 'true')
    expect(listItem('Alpha Hotel')).not.toHaveAttribute('aria-current')
    expect(scrollIntoView).toHaveBeenCalled()
    expect(screen.queryByTestId('map-selected-card')).toBeNull()
  })

  it('on a narrow screen the card appears under the map, because the list is far below', () => {
    renderView([alpha, beta], false)
    fireEvent.click(screen.getByRole('button', { name: 'Beta Hotel, $55' }))
    expect(screen.getByTestId('map-selected-card')).toBeInTheDocument()
  })
})
