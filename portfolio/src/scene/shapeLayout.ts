export type ShapeSpec = {
  position: [number, number, number]
  scale: number
  kind: 'icosahedron' | 'torus' | 'octahedron'
  speed: number
}

const KINDS: ShapeSpec['kind'][] = ['icosahedron', 'torus', 'octahedron']

// Deterministic layout: the same count always yields the same scene, so renders are stable.
export function shapeLayout(count: number): ShapeSpec[] {
  return Array.from({ length: count }, (_, i) => {
    const angle = i * 2.399963
    const radius = 3 + (i % 4) * 1.1
    return {
      position: [Math.cos(angle) * radius, -((i / count) * 14) + 2, Math.sin(angle) * radius - 4],
      scale: 0.35 + ((i * 7) % 5) * 0.14,
      kind: KINDS[i % KINDS.length],
      speed: 0.15 + (i % 5) * 0.06,
    }
  })
}
