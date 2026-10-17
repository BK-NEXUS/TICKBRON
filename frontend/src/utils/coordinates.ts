export interface Coordinates {
  lat: number
  lng: number
}

const inRange = (value: number, limit: number) => Number.isFinite(value) && Math.abs(value) <= limit

const toNumber = (value: unknown): number =>
  typeof value === 'number' ? value : typeof value === 'string' && value.trim() !== '' ? Number(value) : NaN

/** A valid point from what the API sends (decimal strings) or a form holds; null when missing or out of range. */
export function toCoordinates(lat: unknown, lng: unknown): Coordinates | null {
  const latitude = toNumber(lat)
  const longitude = toNumber(lng)
  return inRange(latitude, 90) && inRange(longitude, 180) ? { lat: latitude, lng: longitude } : null
}

/** 6 decimals, as the backend stores them; a longitude dragged past the date line wraps around. */
export function roundCoordinate(value: number, axis: 'lat' | 'lng' = 'lat'): number {
  const wrapped = axis === 'lng' ? ((((value + 180) % 360) + 360) % 360) - 180 : value
  return Math.round(wrapped * 1e6) / 1e6
}
