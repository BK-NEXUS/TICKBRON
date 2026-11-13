import { useEffect } from 'react'
import { blocksNumberKey } from '../utils/inputFilters'

/** Ilovadaǵı hár san qutısı ushın bir listener: eksponent háripleri yamasa belgiler joq (Ctrl/Cmd qısqa jolları qaladı). */
export function useNumberKeyGuard(): void {
  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      const target = event.target
      if (!(target instanceof HTMLInputElement) || target.type !== 'number') return
      if (event.ctrlKey || event.metaKey || event.altKey) return
      if (blocksNumberKey(event.key)) event.preventDefault()
    }
    document.addEventListener('keydown', onKeyDown)
    return () => document.removeEventListener('keydown', onKeyDown)
  }, [])
}
