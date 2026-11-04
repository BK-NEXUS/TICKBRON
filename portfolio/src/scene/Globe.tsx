import { Line } from '@react-three/drei'
import { useFrame, useThree } from '@react-three/fiber'
import { useMemo, useRef } from 'react'
import type { Group, Mesh } from 'three'
import type { Theme } from '../theme/context'
import { Atmosphere } from './Atmosphere'
import { CityPulse } from './CityPulse'
import { fibonacciSphere, GLOBE_RADIUS, routeArcs, routeEndpoints } from './globeGeometry'
import { globeColors } from './globeColors'

const NARROW_WIDTH = 6
const DOTS_PER_SEGMENT = 22

function scrollProgress(): number {
  const max = document.documentElement.scrollHeight - window.innerHeight
  return max > 0 ? Math.min(window.scrollY / max, 1) : 0
}

export function Globe({ segments, theme }: { segments: number; theme: Theme }) {
  const group = useRef<Group>(null)
  const travellers = useRef<(Mesh | null)[]>([])
  const colors = globeColors(theme)
  const arcs = useMemo(() => routeArcs(), [])
  const arcPoints = useMemo(() => arcs.map((curve) => curve.getPoints(64)), [arcs])
  const endpoints = useMemo(() => routeEndpoints(), [])
  const dots = useMemo(
    () => new Float32Array(fibonacciSphere(segments * DOTS_PER_SEGMENT).flatMap((p) => [p.x, p.y, p.z])),
    [segments],
  )
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
    travellers.current.forEach((dot, i) => {
      if (dot) dot.position.copy(arcs[i].getPoint((clock.elapsedTime * 0.18 + i * 0.2) % 1))
    })
  })

  return (
    <group ref={group} scale={narrow ? 0.62 : 1.0}>
      <Atmosphere theme={theme} />
      <mesh>
        <sphereGeometry args={[GLOBE_RADIUS * 0.992, 64, 48]} />
        <meshStandardMaterial color={colors.sphere} roughness={0.75} metalness={0.1} />
      </mesh>
      <points>
        <bufferGeometry>
          <bufferAttribute attach="attributes-position" args={[dots, 3]} />
        </bufferGeometry>
        <pointsMaterial color={colors.lines} size={0.026} sizeAttenuation transparent opacity={0.9} depthWrite={false} />
      </points>
      {arcPoints.map((points, i) => (
        <group key={i}>
          <Line points={points} color={colors.arcs} lineWidth={1.6} />
          <mesh ref={(m) => { travellers.current[i] = m }}>
            <sphereGeometry args={[0.035, 12, 12]} />
            <meshBasicMaterial color={colors.dot} />
          </mesh>
        </group>
      ))}
      {endpoints.map((p, i) => (
        <CityPulse key={i} position={p} color={colors.dot} offset={i * 0.45} />
      ))}
    </group>
  )
}
