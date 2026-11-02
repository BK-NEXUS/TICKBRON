import { useState, type PointerEvent, type ReactNode } from 'react'
import { useReducedMotion } from '../hooks/useReducedMotion'

const MAX_TILT_DEG = 8

export function TiltCard({ children, className = '' }: { children: ReactNode; className?: string }) {
  const reduced = useReducedMotion()
  const [transform, setTransform] = useState('')

  const onMove = (e: PointerEvent<HTMLDivElement>) => {
    if (reduced || e.pointerType === 'touch') return
    const box = e.currentTarget.getBoundingClientRect()
    const x = (e.clientX - box.left) / box.width - 0.5
    const y = (e.clientY - box.top) / box.height - 0.5
    setTransform(`perspective(900px) rotateX(${(-y * MAX_TILT_DEG * 2).toFixed(2)}deg) rotateY(${(x * MAX_TILT_DEG * 2).toFixed(2)}deg)`)
  }

  return (
    <div
      className={`tilt-card ${className}`}
      style={transform ? { transform } : undefined}
      onPointerMove={onMove}
      onPointerLeave={() => setTransform('')}
    >
      {children}
    </div>
  )
}
