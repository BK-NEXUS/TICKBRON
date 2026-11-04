import { describe, expect, it } from 'vitest'
import { fibonacciSphere, GLOBE_RADIUS, routeArcs, routeEndpoints } from './globeGeometry'

describe('fibonacciSphere', () => {
  it('returns the requested number of distinct points on the sphere surface', () => {
    const points = fibonacciSphere(500)
    expect(points).toHaveLength(500)
    for (const p of points) expect(p.length()).toBeCloseTo(GLOBE_RADIUS, 5)
    const keys = new Set(points.map((p) => `${p.x.toFixed(4)},${p.y.toFixed(4)},${p.z.toFixed(4)}`))
    expect(keys.size).toBe(500)
  })

  it('spreads points over both hemispheres', () => {
    const points = fibonacciSphere(200)
    expect(points.some((p) => p.y > 1)).toBe(true)
    expect(points.some((p) => p.y < -1)).toBe(true)
  })
})

describe('routes', () => {
  it('has one endpoint per arc destination plus the origin, all on the surface', () => {
    const endpoints = routeEndpoints()
    expect(endpoints).toHaveLength(routeArcs().length + 1)
    for (const p of endpoints) expect(p.length()).toBeCloseTo(GLOBE_RADIUS, 5)
  })
})
