import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { PropertyLocationMap } from './PropertyLocationMap'
import { I18nProvider } from '../i18n/I18nContext'

function renderMap(latitude: unknown, longitude: unknown) {
  localStorage.setItem('tickbron.language', 'en')
  return render(<I18nProvider><PropertyLocationMap latitude={latitude} longitude={longitude} name="Hotel Alpha" /></I18nProvider>)
}

describe('PropertyLocationMap', () => {
  beforeEach(() => {
    localStorage.clear()
    Object.defineProperty(HTMLElement.prototype, 'clientWidth', { configurable: true, get: () => 600 })
    Object.defineProperty(HTMLElement.prototype, 'clientHeight', { configurable: true, get: () => 300 })
  })
  afterEach(() => {
    delete (HTMLElement.prototype as unknown as Record<string, unknown>).clientWidth
    delete (HTMLElement.prototype as unknown as Record<string, unknown>).clientHeight
  })

  it('shows a map with one pin at the property, from the decimal strings the API sends', () => {
    const { container } = renderMap('41.311081', '69.279737')
    expect(screen.getByRole('region', { name: 'Map: where Hotel Alpha is' })).toBeInTheDocument()
    const pins = container.querySelectorAll('.leaflet-marker-icon')
    expect(pins).toHaveLength(1)
    expect(pins[0]).toHaveAttribute('title', 'Hotel Alpha')
  })

  it('credits OpenStreetMap, as the tile licence requires', () => {
    const { container } = renderMap(41.3, 69.2)
    expect(container.querySelector('.leaflet-control-attribution')).toHaveTextContent('OpenStreetMap')
  })

  it('links to a larger map of the same spot, opening safely in a new tab', () => {
    renderMap('41.311081', '69.279737')
    const link = screen.getByRole('link', { name: 'Open a larger map' })
    expect(link).toHaveAttribute('href', 'https://www.openstreetmap.org/?mlat=41.311081&mlon=69.279737#map=16/41.311081/69.279737')
    expect(link).toHaveAttribute('target', '_blank')
    expect(link).toHaveAttribute('rel', expect.stringContaining('noopener'))
  })

  it('draws nothing when the property has no location or a wrong one', () => {
    const missing = renderMap(null, null)
    expect(missing.container).toBeEmptyDOMElement()
    missing.unmount()
    const wrong = renderMap('95', '10')
    expect(wrong.container).toBeEmptyDOMElement()
  })
})
