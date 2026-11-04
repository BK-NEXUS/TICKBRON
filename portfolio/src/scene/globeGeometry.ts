import { QuadraticBezierCurve3, Vector3 } from 'three'

export const GLOBE_RADIUS = 1.5

export function latLngToVector(lat: number, lng: number, radius = GLOBE_RADIUS): Vector3 {
  const phi = ((90 - lat) * Math.PI) / 180
  const theta = ((lng + 180) * Math.PI) / 180
  return new Vector3(-radius * Math.sin(phi) * Math.cos(theta), radius * Math.cos(phi), radius * Math.sin(phi) * Math.sin(theta))
}

const TASHKENT: [number, number] = [41.3, 69.2]
const DESTINATIONS: [number, number][] = [
  [51.5, -0.1],
  [25.2, 55.3],
  [1.35, 103.8],
  [40.7, -74],
  [35.7, 139.7],
]

// Arcs are lifted off the surface so they read as routes, not scratches.
export function routeArcs(): QuadraticBezierCurve3[] {
  const start = latLngToVector(...TASHKENT)
  return DESTINATIONS.map((dest) => {
    const end = latLngToVector(...dest)
    const control = start.clone().add(end).multiplyScalar(0.5).setLength(GLOBE_RADIUS * 1.6)
    return new QuadraticBezierCurve3(start, control, end)
  })
}

export function routeEndpoints(): Vector3[] {
  return [TASHKENT, ...DESTINATIONS].map(([lat, lng]) => latLngToVector(lat, lng))
}

// Even spacing keeps the dotted surface calm, with no pole clustering like a lat/long grid.
export function fibonacciSphere(count: number, radius = GLOBE_RADIUS): Vector3[] {
  const golden = Math.PI * (3 - Math.sqrt(5))
  return Array.from({ length: count }, (_, i) => {
    const y = 1 - ((i + 0.5) / count) * 2
    const ring = Math.sqrt(1 - y * y)
    const theta = golden * i
    return new Vector3(Math.cos(theta) * ring * radius, y * radius, Math.sin(theta) * ring * radius)
  })
}
