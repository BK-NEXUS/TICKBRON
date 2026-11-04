import { useMemo } from 'react'
import { AdditiveBlending, BackSide, Color, NormalBlending } from 'three'
import type { Theme } from '../theme/context'
import { GLOBE_RADIUS } from './globeGeometry'

const VERTEX = `
varying vec3 vNormal;
void main() {
  vNormal = normalize(normalMatrix * normal);
  gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
}`

// Back faces of the shell only: strongest next to the globe's edge, fading outward.
const FRAGMENT = `
uniform vec3 uColor;
uniform float uStrength;
varying vec3 vNormal;
void main() {
  float rim = pow(clamp(-dot(vNormal, vec3(0.0, 0.0, 1.0)), 0.0, 1.0), 2.0);
  gl_FragColor = vec4(uColor, clamp(rim * uStrength, 0.0, 1.0));
}`

export function Atmosphere({ theme }: { theme: Theme }) {
  const uniforms = useMemo(
    () => ({
      uColor: { value: new Color(theme === 'dark' ? '#3d7bff' : '#2a5bd7') },
      uStrength: { value: theme === 'dark' ? 2.4 : 1.4 },
    }),
    [theme],
  )

  return (
    <mesh scale={1.14}>
      <sphereGeometry args={[GLOBE_RADIUS, 48, 36]} />
      <shaderMaterial
        vertexShader={VERTEX}
        fragmentShader={FRAGMENT}
        uniforms={uniforms}
        side={BackSide}
        transparent
        depthWrite={false}
        blending={theme === 'dark' ? AdditiveBlending : NormalBlending}
      />
    </mesh>
  )
}
