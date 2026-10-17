import { describe, it, expect } from 'vitest'
import { roundCoordinate, toCoordinates } from './coordinates'

describe('toCoordinates', () => {
  it('reads numbers and the decimal strings the API sends', () => {
    expect(toCoordinates('41.311081', '69.279737')).toEqual({ lat: 41.311081, lng: 69.279737 })
    expect(toCoordinates(39.5, 64.4)).toEqual({ lat: 39.5, lng: 64.4 })
  })

  it('returns null when a value is missing or not a number', () => {
    expect(toCoordinates(undefined, 64)).toBeNull()
    expect(toCoordinates(41, null)).toBeNull()
    expect(toCoordinates('', '')).toBeNull()
    expect(toCoordinates('abc', '64')).toBeNull()
    expect(toCoordinates(NaN, 64)).toBeNull()
  })

  it('returns null outside the valid ranges', () => {
    expect(toCoordinates(91, 10)).toBeNull()
    expect(toCoordinates(-91, 10)).toBeNull()
    expect(toCoordinates(10, 181)).toBeNull()
    expect(toCoordinates(10, -181)).toBeNull()
  })

  it('keeps the poles, the date line and zero', () => {
    expect(toCoordinates(90, 180)).toEqual({ lat: 90, lng: 180 })
    expect(toCoordinates(0, 0)).toEqual({ lat: 0, lng: 0 })
  })
})

describe('roundCoordinate', () => {
  it('rounds to the 6 decimals the backend stores', () => {
    expect(roundCoordinate(41.31108149999)).toBe(41.311081)
    expect(roundCoordinate(69.2797375)).toBe(69.279738)
  })

  it('wraps a longitude dragged past the date line', () => {
    expect(roundCoordinate(190.5, 'lng')).toBe(-169.5)
    expect(roundCoordinate(-181, 'lng')).toBe(179)
  })
})
