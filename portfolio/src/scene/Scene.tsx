import { Canvas } from '@react-three/fiber'
import type { Theme } from '../theme/context'
import { Globe } from './Globe'

export default function Scene({ segments, dpr, theme }: { segments: number; dpr: number; theme: Theme }) {
  return (
    <div className="scene" aria-hidden="true">
      <Canvas dpr={dpr} camera={{ position: [0, 0, 6], fov: 45 }} gl={{ antialias: true, alpha: true }}>
        <hemisphereLight args={[theme === 'dark' ? '#cfdcff' : '#ffffff', theme === 'dark' ? '#050810' : '#c7d3ee', 1.1]} />
        <pointLight position={[4, 3, 4]} intensity={45} color="#6ea3ff" />
        <pointLight position={[-5, -2, 3]} intensity={25} color="#ffffff" />
        <Globe segments={segments} theme={theme} />
      </Canvas>
    </div>
  )
}
