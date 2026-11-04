import { useFrame } from '@react-three/fiber'
import { useMemo, useRef } from 'react'
import { Quaternion, Vector3, type Mesh, type MeshBasicMaterial } from 'three'

const FORWARD = new Vector3(0, 0, 1)
const PULSE_SECONDS = 2.6

// A ring that expands and fades at each city, lying flat on the surface.
export function CityPulse({ position, color, offset }: { position: Vector3; color: string; offset: number }) {
  const ring = useRef<Mesh>(null)
  const material = useRef<MeshBasicMaterial>(null)
  const quaternion = useMemo(() => new Quaternion().setFromUnitVectors(FORWARD, position.clone().normalize()), [position])

  useFrame(({ clock }) => {
    const phase = ((clock.elapsedTime + offset) % PULSE_SECONDS) / PULSE_SECONDS
    ring.current?.scale.setScalar(0.4 + phase * 2.2)
    if (material.current) material.current.opacity = (1 - phase) * 0.7
  })

  return (
    <group position={position} quaternion={quaternion}>
      <mesh>
        <circleGeometry args={[0.035, 16]} />
        <meshBasicMaterial color={color} />
      </mesh>
      <mesh ref={ring}>
        <ringGeometry args={[0.07, 0.085, 40]} />
        <meshBasicMaterial ref={material} color={color} transparent depthWrite={false} />
      </mesh>
    </group>
  )
}
