import L from 'leaflet'
import { SATELLITE_ATTRIBUTION, SATELLITE_URL, TILE_ATTRIBUTION, TILE_URL } from './mapTiles'

type MapLayer = 'street' | 'satellite'

const STORAGE_KEY = 'tickbron.mapLayer'

export interface MapLayerLabels {
  group: string
  street: string
  satellite: string
}

// Brauzer saqlawı bloklanǵan bolıwı múmkin: sonda tańlaw tek usı karta ushın
function storedLayer(): MapLayer {
  try {
    return localStorage.getItem(STORAGE_KEY) === 'satellite' ? 'satellite' : 'street'
  } catch {
    return 'street'
  }
}

function remember(layer: MapLayer) {
  try { localStorage.setItem(STORAGE_KEY, layer) } catch { /* tańlaw tek yadta saqlanbaydı */ }
}

/**
 * Kartanıń súwretleri: kóshe kartası, yamasa buryshtaǵı eki túymeli almastırǵısh penen tańlanatuǵın sputnik
 * súwretleri (karta saytlarındaǵıday). Tańlaw keyingi karta ushın yadta saqlanadı. Kartadaǵı `map--satellite`
 * klası stillerge qarańǵı temada súwretlerge tiymewge múmkinshilik beredi.
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
    // Almastırǵıshqa klik kartaǵa jetpewi kerek (ol kartanı jılıstırar yamasa orın tańlar edi)
    L.DomEvent.disableClickPropagation(group)
    return group
  }
  control.addTo(map)

  layers[current].addTo(map)
  container.classList.toggle('map--satellite', current === 'satellite')
  for (const name of ['street', 'satellite'] as const) buttons[name].setAttribute('aria-pressed', String(name === current))
}
