import { Line } from '@react-three/drei'
import { useFrame, useThree } from '@react-three/fiber'
import { useMemo, useRef } from 'react'
import type { Group, Mesh } from 'three'
import type { Theme } from '../theme/context'
import { GLOBE_RADIUS, meridian, parallel, routeArcs } from './globeGeometry'
import { globeColors } from './globeColors'

const NARROW_WIDTH = 6
const MERIDIANS = Array.from({ length: 12 }, (_, i) => -180 + i * 30)
const PARALLELS = [-60, -30, 0, 30, 60]

function scrollProgress(): number {
  const max = document.documentElement.scrollHeight - window.innerHeight
  return max > 0 ? Math.min(window.scrollY / max, 1) : 0
}

export function Globe({ segments, theme }: { segments: number; theme: Theme }) {
  const group = useRef<Group>(null)
  const dots = useRef<(Mesh | null)[]>([])
  const colors = globeColors(theme)
  const arcs = useMemo(() => routeArcs(), [])
  const arcPoints = useMemo(() => arcs.map((curve) => curve.getPoints(48)), [arcs])
  const { viewport } = useThree()
  const narrow = viewport.width < NARROW_WIDTH

  useFrame(({ pointer, clock }, delta) => {
    const g = group.current
    if (!g) return
    const ease = Math.min(delta * 1.5, 1)
    const progress = scrollProgress()
    const baseX = narrow ? 0 : viewport.width * 0.27
    const baseY = narrow ? viewport.height * 0.24 : 0
    g.position.x += (baseX + pointer.x * 0.3 - g.position.x) * ease
    g.position.y += (baseY + pointer.y * 0.2 - progress * 1.4 - g.position.y) * ease
    g.rotation.y += delta * 0.1
    g.rotation.x += (0.35 + pointer.y * 0.15 - g.rotation.x) * ease
    dots.current.forEach((dot, i) => {
      if (dot) dot.position.copy(arcs[i].getPoint((clock.elapsedTime * 0.18 + i * 0.2) % 1))
    })
  })

  return (
    <group ref={group} scale={narrow ? 0.62 : 1.0}>
      <mesh>
        <sphereGeometry args={[GLOBE_RADIUS, segments, Math.round(segments * 0.75)]} />
        <meshPhysicalMaterial color={colors.sphere} transparent opacity={colors.opacity} metalness={0.2} roughness={0.6} clearcoat={0.2} />
      </mesh>
      {PARALLELS.map((lat) => (
        <Line key={`p${lat}`} points={parallel(lat)} color={colors.lines} lineWidth={0.6} transparent opacity={0.35} />
      ))}
      {MERIDIANS.map((lng) => (
        <Line key={`m${lng}`} points={meridian(lng)} color={colors.lines} lineWidth={0.6} transparent opacity={0.35} />
      ))}
      {arcPoints.map((points, i) => (
        <group key={i}>
          <Line points={points} color={colors.arcs} lineWidth={1.6} />
          <mesh ref={(m) => { dots.current[i] = m }}>
            <sphereGeometry args={[0.035, 12, 12]} />
            <meshBasicMaterial color={colors.dot} />
          </mesh>
        </group>
      ))}
    </group>
  )
}
