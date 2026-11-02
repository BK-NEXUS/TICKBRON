import { MeshDistortMaterial } from '@react-three/drei'
import { useFrame, useThree } from '@react-three/fiber'
import { useRef } from 'react'
import type { Mesh } from 'three'

const MOBILE_WIDTH = 6

function scrollProgress(): number {
  const max = document.documentElement.scrollHeight - window.innerHeight
  return max > 0 ? Math.min(window.scrollY / max, 1) : 0
}

// One calm centerpiece: it drifts toward the pointer and turns as the page scrolls.
export function Blob({ segments }: { segments: number }) {
  const mesh = useRef<Mesh>(null)
  const { viewport } = useThree()
  const narrow = viewport.width < MOBILE_WIDTH

  useFrame(({ pointer }, delta) => {
    const m = mesh.current
    if (!m) return
    const ease = Math.min(delta * 1.5, 1)
    const progress = scrollProgress()
    const baseX = narrow ? 0 : viewport.width * 0.24
    const baseY = narrow ? viewport.height * 0.18 : 0
    m.position.x += (baseX + pointer.x * 0.5 - m.position.x) * ease
    m.position.y += (baseY + pointer.y * 0.35 - progress * 1.2 - m.position.y) * ease
    m.rotation.y += delta * 0.12
    m.rotation.x += (progress * Math.PI - m.rotation.x) * ease * 0.5
  })

  return (
    <mesh ref={mesh} scale={narrow ? 1.25 : 1.6}>
      <icosahedronGeometry args={[1, Math.round(segments / 16)]} />
      <MeshDistortMaterial
        color="#262a22"
        metalness={0.7}
        roughness={0.42}
        distort={0.38}
        speed={1.1}
        clearcoat={1}
        clearcoatRoughness={0.1}
      />
    </mesh>
  )
}
