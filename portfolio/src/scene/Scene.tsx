import { Canvas } from '@react-three/fiber'
import { Blob } from './Blob'

export default function Scene({ segments, dpr }: { segments: number; dpr: number }) {
  return (
    <div className="scene" aria-hidden="true">
      <Canvas dpr={dpr} camera={{ position: [0, 0, 6], fov: 45 }} gl={{ antialias: true, alpha: true }}>
        <hemisphereLight args={["#dfe8d0", "#0a0a0a", 1.1]} />
        <pointLight position={[4, 3, 4]} intensity={260} color="#c8ff3d" />
        <pointLight position={[-5, -2, 3]} intensity={160} color="#ffffff" />
        <pointLight position={[0, 4, -3]} intensity={120} color="#8affc1" />
        <Blob segments={segments} />
      </Canvas>
    </div>
  )
}
