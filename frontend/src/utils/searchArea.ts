import type { MapArea } from '../components/PropertiesMap'
import { toCoordinates } from './coordinates'

const MAX_RADIUS_KM = 100

/** The map area of a search URL (`lat`, `lng`, `radius` in km); null unless all three are valid. */
export function areaFromUrl(params: URLSearchParams): MapArea | null {
  const point = toCoordinates(params.get('lat'), params.get('lng'))
  const radius = Number(params.get('radius'))
  if (!point || !Number.isFinite(radius) || radius < 1 || radius > MAX_RADIUS_KM) return null
  return { ...point, radius }
}

/** A search around the map area replaces the destination text; dates, guests and filters stay. */
export function areaToUrl(current: URLSearchParams, area: MapArea): URLSearchParams {
  const next = new URLSearchParams(current)
  next.delete('destination')
  next.set('lat', String(area.lat))
  next.set('lng', String(area.lng))
  next.set('radius', String(area.radius))
  return next
}
