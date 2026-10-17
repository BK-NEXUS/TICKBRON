import { describe, it, expect } from 'vitest'
import { areaFromUrl, areaToUrl } from './searchArea'

const params = (query: string) => new URLSearchParams(query)

describe('areaFromUrl', () => {
  it('reads a centre and a radius', () => {
    expect(areaFromUrl(params('lat=41.3&lng=69.2&radius=12'))).toEqual({ lat: 41.3, lng: 69.2, radius: 12 })
  })

  it('is null when any part is missing, not a number or out of range', () => {
    expect(areaFromUrl(params('lat=41.3&lng=69.2'))).toBeNull()
    expect(areaFromUrl(params('lat=abc&lng=69.2&radius=5'))).toBeNull()
    expect(areaFromUrl(params('lat=91&lng=69.2&radius=5'))).toBeNull()
    expect(areaFromUrl(params('lat=41&lng=181&radius=5'))).toBeNull()
    expect(areaFromUrl(params('lat=41&lng=69&radius=0'))).toBeNull()
    expect(areaFromUrl(params('lat=41&lng=69&radius=101'))).toBeNull()
  })
})

describe('areaToUrl', () => {
  it('sets the area and drops the destination text, keeping dates and filters', () => {
    const next = areaToUrl(params('destination=Paris&check_in=2026-05-01&min_price=10'), { lat: 41.3, lng: 69.2, radius: 12 })
    expect(next.get('lat')).toBe('41.3')
    expect(next.get('lng')).toBe('69.2')
    expect(next.get('radius')).toBe('12')
    expect(next.has('destination')).toBe(false)
    expect(next.get('check_in')).toBe('2026-05-01')
    expect(next.get('min_price')).toBe('10')
  })
})
