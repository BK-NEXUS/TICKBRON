import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
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

function renderMap(properties: Property[], extra: Partial<React.ComponentProps<typeof PropertiesMap>> = {}) {
  localStorage.setItem('tickbron.language', 'en')
  return render(
    <I18nProvider>
      <MemoryRouter initialEntries={['/search']}>
        <Routes>
          <Route path="/search" element={<PropertiesMap properties={properties} {...extra} />} />
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
    expect(screen.getByRole('button', { name: 'Alpha Hotel, $60' })).toHaveClass('map-pin--active')
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

  describe('pins that would cover each other', () => {
    const alphaTwin = property(4, 'Alpha Twin Hotel', { latitude: '41.311082', longitude: '69.279738' }, 70)

    it('are shown as one numbered group instead of lying on top of each other', () => {
      const { container } = renderMap([alpha, alphaTwin, beta])
      const group = container.querySelector('.map-cluster') as HTMLElement
      expect(group).toHaveTextContent('2')
      expect(group).toHaveAccessibleName('2 properties here: zoom in to see them')
      expect(screen.queryByRole('button', { name: 'Alpha Hotel, $60' })).toBeNull()
      expect(screen.getByRole('button', { name: 'Beta Hotel, $55' })).toBeInTheDocument()
    })

    it('a small group has the plain bubble, a group of ten or more a bigger one, fifty or more the biggest', () => {
      const crowd = (count: number) => Array.from({ length: count }, (_, i) =>
        property(100 + i, `Crowd ${i}`, { latitude: `41.3110${String(i % 10)}`, longitude: `69.2797${String(Math.floor(i / 10))}` }))

      const small = renderMap([alpha, alphaTwin])
      const bubble = small.container.querySelector('.map-cluster') as HTMLElement
      expect(bubble.classList.contains('map-cluster--md')).toBe(false)
      expect(bubble.classList.contains('map-cluster--lg')).toBe(false)
      small.unmount()

      const medium = renderMap(crowd(12))
      expect(medium.container.querySelector('.map-cluster')).toHaveClass('map-cluster--md')
      medium.unmount()

      const large = renderMap(crowd(55))
      expect(large.container.querySelector('.map-cluster')).toHaveClass('map-cluster--lg')
    })

    it('a lone pin is not grouped', () => {
      const { container } = renderMap([alpha, beta])
      expect(container.querySelector('.map-cluster')).toBeNull()
    })
  })

  describe('working with a list next to the map', () => {
    it('a pin the list is pointing at is marked and in front', () => {
      renderMap([alpha, beta], { highlightedId: 2 })
      const pin = screen.getByRole('button', { name: 'Beta Hotel, $55' })
      expect(pin).toHaveClass('map-pin--hover')
      const icon = (name: string) => screen.getByRole('button', { name }).closest('.leaflet-marker-icon') as HTMLElement
      expect(Number(icon('Beta Hotel, $55').style.zIndex)).toBeGreaterThan(Number(icon('Alpha Hotel, $60').style.zIndex))
    })

    it('the mark moves when the list points at another property', () => {
      const { rerender } = renderMap([alpha, beta], { highlightedId: 2 })
      rerender(
        <I18nProvider>
          <MemoryRouter><PropertiesMap properties={[alpha, beta]} highlightedId={1} /></MemoryRouter>
        </I18nProvider>,
      )
      expect(screen.getByRole('button', { name: 'Alpha Hotel, $60' })).toHaveClass('map-pin--hover')
      expect(screen.getByRole('button', { name: 'Beta Hotel, $55' })).not.toHaveClass('map-pin--hover')
    })

    it('tells the page which pin was chosen, and when the card is closed', () => {
      const onSelectedChange = vi.fn()
      renderMap([alpha, beta], { onSelectedChange })
      fireEvent.click(screen.getByRole('button', { name: 'Alpha Hotel, $60' }))
      expect(onSelectedChange).toHaveBeenLastCalledWith(1)
      fireEvent.click(screen.getByRole('button', { name: 'Close' }))
      expect(onSelectedChange).toHaveBeenLastCalledWith(null)
    })

    it('can leave the property card to the list', () => {
      renderMap([alpha, beta], { showSelectedCard: false })
      fireEvent.click(screen.getByRole('button', { name: 'Alpha Hotel, $60' }))
      expect(screen.queryByTestId('map-selected-card')).toBeNull()
      expect(screen.getByRole('button', { name: 'Alpha Hotel, $60' })).toHaveClass('map-pin--active')
    })
  })

  describe('search this area', () => {
    const zoomIn = (container: HTMLElement) => fireEvent.click(container.querySelector('.leaflet-control-zoom-in') as HTMLElement)

    it('is offered only after the guest moves the map, and only when the page can use it', () => {
      const first = renderMap([alpha, beta], { onSearchArea: vi.fn() })
      expect(screen.queryByRole('button', { name: 'Search this area' })).toBeNull()
      zoomIn(first.container)
      expect(screen.getByRole('button', { name: 'Search this area' })).toBeInTheDocument()
    })

    it('is not offered without a handler', () => {
      const { container } = renderMap([alpha, beta])
      zoomIn(container)
      expect(screen.queryByRole('button', { name: 'Search this area' })).toBeNull()
    })

    it('hands over the visible area as a centre and a radius in kilometres, then goes away', () => {
      const onSearchArea = vi.fn()
      const { container } = renderMap([alpha, beta], { onSearchArea })
      zoomIn(container)
      fireEvent.click(screen.getByRole('button', { name: 'Search this area' }))
      expect(onSearchArea).toHaveBeenCalledTimes(1)
      const area = onSearchArea.mock.calls[0][0]
      expect(area.lat).toBeGreaterThan(38)
      expect(area.lat).toBeLessThan(43)
      expect(area.radius).toBeGreaterThanOrEqual(1)
      expect(area.radius).toBeLessThanOrEqual(100)
      expect(Number.isInteger(area.radius)).toBe(true)
      expect(screen.queryByRole('button', { name: 'Search this area' })).toBeNull()
    })

    it('new results do not count as the guest moving the map', () => {
      const { container, rerender } = renderMap([alpha], { onSearchArea: vi.fn() })
      rerender(
        <I18nProvider>
          <MemoryRouter><PropertiesMap properties={[alpha, beta]} onSearchArea={vi.fn()} /></MemoryRouter>
        </I18nProvider>,
      )
      expect(container.querySelector('.leaflet-container')).not.toBeNull()
      expect(screen.queryByRole('button', { name: 'Search this area' })).toBeNull()
    })
  })

  it('draws the OpenStreetMap attribution the tile licence requires', () => {
    const { container } = renderMap([alpha])
    expect(container.querySelector('.leaflet-control-attribution')).toHaveTextContent('OpenStreetMap')
  })
})
