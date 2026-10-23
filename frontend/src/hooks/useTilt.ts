import { useEffect, useRef } from 'react'

const FINE_POINTER = '(hover: hover) and (pointer: fine) and (prefers-reduced-motion: no-preference)'

/**
 * Tilts an element towards the pointer by up to `maxDeg` degrees: it sets --tilt-x and --tilt-y on the element and
 * the CSS (`.tilt-card`) turns them into a 3D rotation. Does nothing on touch screens, without a real pointer, or
 * when the user asked for reduced motion.
 */
export function useTilt<T extends HTMLElement>(maxDeg = 5) {
  const ref = useRef<T>(null)

  useEffect(() => {
    const element = ref.current
    if (!element || typeof window.matchMedia !== 'function' || !window.matchMedia(FINE_POINTER).matches) return

    const onMove = (event: PointerEvent) => {
      const box = element.getBoundingClientRect()
      if (box.width === 0 || box.height === 0) return
      const x = (event.clientX - box.left) / box.width - 0.5
      const y = (event.clientY - box.top) / box.height - 0.5
      element.style.setProperty('--tilt-x', `${(-y * maxDeg).toFixed(2)}deg`)
      element.style.setProperty('--tilt-y', `${(x * maxDeg).toFixed(2)}deg`)
    }
    const onLeave = () => {
      element.style.removeProperty('--tilt-x')
      element.style.removeProperty('--tilt-y')
    }
    element.addEventListener('pointermove', onMove)
    element.addEventListener('pointerleave', onLeave)
    return () => {
      element.removeEventListener('pointermove', onMove)
      element.removeEventListener('pointerleave', onLeave)
      onLeave()
    }
  }, [maxDeg])

  return ref
}
