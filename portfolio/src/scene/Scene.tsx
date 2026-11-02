import { Canvas } from '@react-three/fiber'
import { Globe } from './Globe'
import { Shapes } from './Shapes'
import { useScrollCamera } from './useScrollCamera'

function Rig() {
  useScrollCamera()
  return null
}

export default function Scene({ shapeCount, dpr }: { shapeCount: number; dpr: number }) {
  return (
    <div className="scene" aria-hidden="true">
      <Canvas dpr={dpr} camera={{ position: [0, 0, 6], fov: 55 }} gl={{ antialias: true, alpha: true }}>
        <ambientLight intensity={0.6} />
        <pointLight position={[5, 5, 5]} intensity={40} color="#9a8cff" />
        <pointLight position={[-5, -3, 2]} intensity={25} color="#4fd1ff" />
        <Globe />
        <Shapes count={shapeCount} />
        <Rig />
      </Canvas>
    </div>
  )
}
