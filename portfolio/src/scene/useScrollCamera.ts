import { useFrame } from '@react-three/fiber'

const SCROLL_DEPTH = 9

// Easing toward the target keeps camera movement soft instead of tracking every wheel tick.
export function useScrollCamera(): void {
  useFrame(({ camera }, delta) => {
    const max = document.documentElement.scrollHeight - window.innerHeight
    const progress = max > 0 ? Math.min(window.scrollY / max, 1) : 0
    const targetY = -progress * SCROLL_DEPTH
    camera.position.y += (targetY - camera.position.y) * Math.min(delta * 2, 1)
    camera.lookAt(0, camera.position.y - 0.5, -4)
  })
}
