import { useEffect, useRef } from 'react'

const FINE_POINTER = '(hover: hover) and (pointer: fine) and (prefers-reduced-motion: no-preference)'

/**
 * Elementti kursor tárepke `maxDeg` gradusqa shekem iyiledi: elementte --tilt-x hám --tilt-y belgileydi hám
 * CSS (`.tilt-card`) olardı 3D buraw ǵa aylandıradı. Sensorlı ekranlarda, haqıyqıy kursorsız, yamasa
 * paydalanıwshı háreketti azaytıwdı sorasa hesh nárse islemeydi.
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
