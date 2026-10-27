import L from 'leaflet'
import { SATELLITE_ATTRIBUTION, SATELLITE_URL, TILE_ATTRIBUTION, TILE_URL } from './mapTiles'

type MapLayer = 'street' | 'satellite'

const STORAGE_KEY = 'tickbron.mapLayer'

export interface MapLayerLabels {
  group: string
  street: string
  satellite: string
}

// Browser storage can be blocked: the choice is then only for this map
function storedLayer(): MapLayer {
  try {
    return localStorage.getItem(STORAGE_KEY) === 'satellite' ? 'satellite' : 'street'
  } catch {
    return 'street'
  }
}

function remember(layer: MapLayer) {
  try { localStorage.setItem(STORAGE_KEY, layer) } catch { /* the choice just is not remembered */ }
}

/**
 * The map's pictures: the street map, or satellite pictures chosen with a two-button switch in the
 * corner (as on map sites). The choice is remembered for the next map. A `map--satellite` class on the
 * map lets the styles leave the pictures alone in the dark theme.
 */
export function addBaseLayers(map: L.Map, labels: MapLayerLabels): void {
  const layers: Record<MapLayer, L.TileLayer> = {
    street: L.tileLayer(TILE_URL, { attribution: TILE_ATTRIBUTION, maxZoom: 19 }),
    satellite: L.tileLayer(SATELLITE_URL, { attribution: SATELLITE_ATTRIBUTION, maxZoom: 19 }),
  }
  let current: MapLayer = storedLayer()
  const container = map.getContainer()
  const buttons = {} as Record<MapLayer, HTMLButtonElement>

  const show = (next: MapLayer) => {
    map.removeLayer(layers[current])
    current = next
    layers[next].addTo(map)
    container.classList.toggle('map--satellite', next === 'satellite')
    for (const name of ['street', 'satellite'] as const) buttons[name].setAttribute('aria-pressed', String(name === next))
  }

  const control = new L.Control({ position: 'topright' })
  control.onAdd = () => {
    const group = L.DomUtil.create('div', 'map-layer-switch leaflet-bar')
    group.setAttribute('role', 'group')
    group.setAttribute('aria-label', labels.group)
    for (const name of ['street', 'satellite'] as const) {
      const button = L.DomUtil.create('button', 'map-layer-switch__button', group)
      button.type = 'button'
      button.textContent = labels[name]
      buttons[name] = button
      button.addEventListener('click', () => { if (name !== current) { show(name); remember(name) } })
    }
    // A click on the switch must not reach the map (it would move it or pick a place)
    L.DomEvent.disableClickPropagation(group)
    return group
  }
  control.addTo(map)

  layers[current].addTo(map)
  container.classList.toggle('map--satellite', current === 'satellite')
  for (const name of ['street', 'satellite'] as const) buttons[name].setAttribute('aria-pressed', String(name === current))
}
