import { useFrame } from '@react-three/fiber'
import { useRef } from 'react'
import type { Group } from 'three'

export function Globe() {
  const group = useRef<Group>(null)
  useFrame((_, delta) => {
    if (group.current) group.current.rotation.y += delta * 0.12
  })

  return (
    <group ref={group} position={[2.6, 0.4, -2]}>
      <mesh>
        <sphereGeometry args={[1.6, 32, 24]} />
        <meshBasicMaterial color="#4fd1ff" wireframe transparent opacity={0.28} />
      </mesh>
      <mesh scale={0.96}>
        <sphereGeometry args={[1.6, 32, 24]} />
        <meshStandardMaterial color="#1b1750" transparent opacity={0.55} />
      </mesh>
    </group>
  )
}
