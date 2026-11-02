import { useEffect, useState } from 'react'
import { useReducedMotion } from '../hooks/useReducedMotion'

const DURATION_MS = 1600

export function Counter({ value }: { value: number }) {
  const reduced = useReducedMotion()
  const [shown, setShown] = useState(0)

  useEffect(() => {
    if (reduced) return
    let frame = 0
    const start = performance.now()
    const tick = (now: number) => {
      const progress = Math.min((now - start) / DURATION_MS, 1)
      const eased = 1 - Math.pow(1 - progress, 3)
      setShown(Math.round(value * eased))
      if (progress < 1) frame = requestAnimationFrame(tick)
    }
    frame = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(frame)
  }, [value, reduced])

  return <span>{reduced ? value : shown}</span>
}
