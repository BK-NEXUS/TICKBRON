import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, within } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { PropertiesMap } from './PropertiesMap'
import { I18nProvider } from '../i18n/I18nContext'
import type { Property } from '../adapters/propertyAdapter'

const property = (id: number, name: string, coords: { latitude?: unknown; longitude?: unknown }, price = 60): Property => ({
  id, owner_id: 1, property_type: { id: 1, name: 'Hotel', slug: 'hotel' }, status: 'active',
  max_guests: 2, bedrooms: 1, bathrooms: 1, address_line1: 'Street', city: 'Tashkent', country: 'Uzbekistan',
  base_price: price, currency: 'USD', has_wifi: true, has_parking: false, has_ac: true, has_heating: false, has_elevator: false,
  translations: [{ language: 'en', name, description: '' }], policies: [],
  created_at: '2026-01-01T00:00:00Z', updated_at: '2026-01-01T00:00:00Z',
  ...coords,
} as unknown as Property)

const alpha = property(1, 'Alpha Hotel', { latitude: '41.311081', longitude: '69.279737' }, 60)
const beta = property(2, 'Beta Hotel', { latitude: 39.654823, longitude: 66.97567 }, 55)
const gamma = property(3, 'Gamma Hotel', { latitude: null, longitude: null })

function renderMap(properties: Property[]) {
  localStorage.setItem('tickbron.language', 'en')
  return render(
    <I18nProvider>
      <MemoryRouter initialEntries={['/search']}>
        <Routes>
          <Route path="/search" element={<PropertiesMap properties={properties} />} />
          <Route path="/property/:id" element={<p>Property page {window.location.pathname}</p>} />
        </Routes>
      </MemoryRouter>
    </I18nProvider>,
  )
}

describe('PropertiesMap', () => {
  // jsdom has no layout: give the map a size, so the pins are placed as in a browser
  beforeEach(() => {
    localStorage.clear()
    Object.defineProperty(HTMLElement.prototype, 'clientWidth', { configurable: true, get: () => 800 })
    Object.defineProperty(HTMLElement.prototype, 'clientHeight', { configurable: true, get: () => 500 })
  })

  afterEach(() => {
    delete (HTMLElement.prototype as unknown as Record<string, unknown>).clientWidth
    delete (HTMLElement.prototype as unknown as Record<string, unknown>).clientHeight
  })

  it('puts a price pin on the map for every property that has a location', () => {
    const { container } = renderMap([alpha, beta, gamma])
    expect(container.querySelectorAll('.leaflet-marker-icon')).toHaveLength(2)
    expect(screen.getByRole('button', { name: 'Alpha Hotel, $60' })).toHaveTextContent('$60')
    expect(screen.getByRole('button', { name: 'Beta Hotel, $55' })).toBeInTheDocument()
  })

  it('says how many properties have no location instead of hiding them silently', () => {
    renderMap([alpha, gamma])
    expect(screen.getByText('1 property is not on the map: its owner has not set a location.')).toBeInTheDocument()
  })

  it('says so, and draws no map, when no property has a location', () => {
    const { container } = renderMap([gamma])
    expect(screen.getByText('None of these properties has a location on the map yet.')).toBeInTheDocument()
    expect(container.querySelector('.leaflet-container')).toBeNull()
  })

  it('shows a hint until a pin is chosen, then the property card with a way to open it', () => {
    renderMap([alpha, beta])
    expect(screen.getByText(/Select a price on the map/)).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'Alpha Hotel, $60' }))
    const card = screen.getByTestId('map-selected-card')
    expect(within(card).getByText('Alpha Hotel')).toBeInTheDocument()
    expect(screen.queryByText(/Select a price on the map/)).not.toBeInTheDocument()

    fireEvent.click(card.querySelector('.property-card') as HTMLElement)
    expect(screen.getByText(/Property page/)).toBeInTheDocument()
  })

  it('choosing another pin replaces the card; Close removes it', () => {
    renderMap([alpha, beta])
    fireEvent.click(screen.getByRole('button', { name: 'Alpha Hotel, $60' }))
    fireEvent.click(screen.getByRole('button', { name: 'Beta Hotel, $55' }))
    const card = screen.getByTestId('map-selected-card')
    expect(within(card).getByText('Beta Hotel')).toBeInTheDocument()
    expect(within(card).queryByText('Alpha Hotel')).toBeNull()

    fireEvent.click(screen.getByRole('button', { name: 'Close' }))
    expect(screen.queryByTestId('map-selected-card')).toBeNull()
  })

  it('marks the chosen pin', () => {
    renderMap([alpha, beta])
    fireEvent.click(screen.getByRole('button', { name: 'Alpha Hotel, $60' }))
    expect(screen.getByRole('button', { name: 'Alpha Hotel, $60' }).closest('.leaflet-marker-icon')).toHaveClass('map-pin--active')
  })

  it('the card goes away when its property leaves the results (a new search)', () => {
    const { rerender } = renderMap([alpha, beta])
    fireEvent.click(screen.getByRole('button', { name: 'Alpha Hotel, $60' }))
    rerender(
      <I18nProvider>
        <MemoryRouter><PropertiesMap properties={[beta]} /></MemoryRouter>
      </I18nProvider>,
    )
    expect(screen.queryByTestId('map-selected-card')).toBeNull()
  })

  it('a pin under another pin comes to the front when it is hovered or focused, so it can be tapped', () => {
    renderMap([alpha, beta])
    const icon = (name: string) => screen.getByRole('button', { name }).closest('.leaflet-marker-icon') as HTMLElement
    const zIndex = (name: string) => Number(icon(name).style.zIndex)
    const base = zIndex('Alpha Hotel, $60')

    fireEvent.mouseEnter(screen.getByRole('button', { name: 'Alpha Hotel, $60' }))
    expect(zIndex('Alpha Hotel, $60')).toBeGreaterThan(zIndex('Beta Hotel, $55'))
    fireEvent.mouseLeave(screen.getByRole('button', { name: 'Alpha Hotel, $60' }))
    expect(zIndex('Alpha Hotel, $60')).toBe(base)

    fireEvent.focus(screen.getByRole('button', { name: 'Beta Hotel, $55' }))
    expect(zIndex('Beta Hotel, $55')).toBeGreaterThan(zIndex('Alpha Hotel, $60'))
  })

  it('the chosen pin stays in front', () => {
    renderMap([alpha, beta])
    fireEvent.click(screen.getByRole('button', { name: 'Alpha Hotel, $60' }))
    fireEvent.mouseLeave(screen.getByRole('button', { name: 'Alpha Hotel, $60' }))
    const icon = (name: string) => screen.getByRole('button', { name }).closest('.leaflet-marker-icon') as HTMLElement
    expect(Number(icon('Alpha Hotel, $60').style.zIndex)).toBeGreaterThan(Number(icon('Beta Hotel, $55').style.zIndex))
  })

  it('draws the OpenStreetMap attribution the tile licence requires', () => {
    const { container } = renderMap([alpha])
    expect(container.querySelector('.leaflet-control-attribution')).toHaveTextContent('OpenStreetMap')
  })
})
