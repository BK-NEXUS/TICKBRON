import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import L from 'leaflet'
import { addBaseLayers } from './mapLayers'
import { SATELLITE_URL, TILE_URL } from './mapTiles'

const labels = { group: 'Map type', street: 'Map', satellite: 'Satellite' }
const origin = (url: string) => new URL(url.replace('{z}/{x}/{y}', '0/0/0').replace('{z}/{y}/{x}', '0/0/0')).origin

function makeMap() {
  const container = document.createElement('div')
  document.body.appendChild(container)
  const map = L.map(container, { center: [41.3, 69.3], zoom: 5, zoomControl: false })
  addBaseLayers(map, labels)
  return { map, container }
}

const tileHosts = (container: HTMLElement) =>
  Array.from(container.querySelectorAll<HTMLImageElement>('img.leaflet-tile')).map(tile => new URL(tile.src).origin)

const button = (container: HTMLElement, name: string) =>
  Array.from(container.querySelectorAll<HTMLButtonElement>('.map-layer-switch button')).find(b => b.textContent === name) as HTMLButtonElement

describe('addBaseLayers: street map and satellite, like the switch of a map site', () => {
  beforeEach(() => {
    localStorage.clear()
    Object.defineProperty(HTMLElement.prototype, 'clientWidth', { configurable: true, get: () => 800 })
    Object.defineProperty(HTMLElement.prototype, 'clientHeight', { configurable: true, get: () => 500 })
  })
  afterEach(() => { document.body.innerHTML = ''; vi.restoreAllMocks() })

  it('starts with the street map and offers both, as a labelled group of two toggle buttons', () => {
    const { container } = makeMap()
    expect(new Set(tileHosts(container))).toEqual(new Set([origin(TILE_URL)]))
    expect(container.querySelector('.map-layer-switch')).toHaveAttribute('role', 'group')
    expect(container.querySelector('.map-layer-switch')).toHaveAttribute('aria-label', 'Map type')
    expect(button(container, 'Map')).toHaveAttribute('aria-pressed', 'true')
    expect(button(container, 'Satellite')).toHaveAttribute('aria-pressed', 'false')
    expect(container).not.toHaveClass('map--satellite')
  })

  it('switches to satellite pictures and back, keeping the credit of the picture source', () => {
    const { container } = makeMap()

    button(container, 'Satellite').click()
    expect(new Set(tileHosts(container))).toEqual(new Set([origin(SATELLITE_URL)]))
    expect(container).toHaveClass('map--satellite')
    expect(button(container, 'Satellite')).toHaveAttribute('aria-pressed', 'true')
    expect(button(container, 'Map')).toHaveAttribute('aria-pressed', 'false')
    expect(container.querySelector('.leaflet-control-attribution')).toHaveTextContent('Esri')

    button(container, 'Map').click()
    expect(new Set(tileHosts(container))).toEqual(new Set([origin(TILE_URL)]))
    expect(container).not.toHaveClass('map--satellite')
    expect(container.querySelector('.leaflet-control-attribution')).toHaveTextContent('OpenStreetMap')
  })

  it('remembers the choice for the next map', () => {
    const first = makeMap()
    button(first.container, 'Satellite').click()
    expect(localStorage.getItem('tickbron.mapLayer')).toBe('satellite')

    const second = makeMap()
    expect(new Set(tileHosts(second.container))).toEqual(new Set([origin(SATELLITE_URL)]))
    expect(button(second.container, 'Satellite')).toHaveAttribute('aria-pressed', 'true')
  })

  it('ignores a stored value it does not know', () => {
    localStorage.setItem('tickbron.mapLayer', 'hybrid')
    const { container } = makeMap()
    expect(button(container, 'Map')).toHaveAttribute('aria-pressed', 'true')
  })

  it('works when the browser blocks storage', () => {
    vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => { throw new Error('blocked') })
    vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => { throw new Error('blocked') })
    const { container } = makeMap()
    button(container, 'Satellite').click()
    expect(button(container, 'Satellite')).toHaveAttribute('aria-pressed', 'true')
  })

  it('a click on the switch does not move the map', () => {
    const { map, container } = makeMap()
    const click = vi.fn()
    map.on('click', click)
    button(container, 'Satellite').click()
    expect(click).not.toHaveBeenCalled()
  })
})
