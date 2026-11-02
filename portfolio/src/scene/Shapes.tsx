import { Float } from '@react-three/drei'
import { useFrame } from '@react-three/fiber'
import { useRef } from 'react'
import type { Mesh } from 'three'
import { shapeLayout, type ShapeSpec } from './shapeLayout'

const COLORS = ['#7c6cff', '#4fd1ff', '#c06bff']

function Shape({ spec, color }: { spec: ShapeSpec; color: string }) {
  const mesh = useRef<Mesh>(null)
  useFrame((_, delta) => {
    if (!mesh.current) return
    mesh.current.rotation.x += delta * spec.speed
    mesh.current.rotation.y += delta * spec.speed * 0.8
  })

  return (
    <Float speed={1} rotationIntensity={0.4} floatIntensity={1.2}>
      <mesh ref={mesh} position={spec.position} scale={spec.scale}>
        {spec.kind === 'icosahedron' && <icosahedronGeometry args={[1, 0]} />}
        {spec.kind === 'octahedron' && <octahedronGeometry args={[1, 0]} />}
        {spec.kind === 'torus' && <torusGeometry args={[0.8, 0.3, 16, 40]} />}
        <meshPhysicalMaterial
          color={color}
          transparent
          opacity={0.38}
          roughness={0.15}
          metalness={0.2}
          clearcoat={1}
          emissive={color}
          emissiveIntensity={0.25}
        />
      </mesh>
    </Float>
  )
}

export function Shapes({ count }: { count: number }) {
  return (
    <>
      {shapeLayout(count).map((spec, i) => (
        <Shape key={i} spec={spec} color={COLORS[i % COLORS.length]} />
      ))}
    </>
  )
}
