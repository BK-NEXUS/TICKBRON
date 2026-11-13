import type { MapArea } from '../components/PropertiesMap'
import { toCoordinates } from './coordinates'

const MAX_RADIUS_KM = 100

/** Izlew URL ınıń karta aymaǵı (`lat`, `lng`, `radius` km de); úshewi de jaramlı bolmasa null. */
export function areaFromUrl(params: URLSearchParams): MapArea | null {
  const point = toCoordinates(params.get('lat'), params.get('lng'))
  const radius = Number(params.get('radius'))
  if (!point || !Number.isFinite(radius) || radius < 1 || radius > MAX_RADIUS_KM) return null
  return { ...point, radius }
}

/** Karta aymaǵı átirapındaǵı izlew barar orın tekstin almastıradı; sanalar, mehmanlar hám filterler qaladı. */
export function areaToUrl(current: URLSearchParams, area: MapArea): URLSearchParams {
  const next = new URLSearchParams(current)
  next.delete('destination')
  next.set('lat', String(area.lat))
  next.set('lng', String(area.lng))
  next.set('radius', String(area.radius))
  return next
}
