import { useEffect } from 'react'
import { blocksNumberKey } from '../utils/inputFilters'

/** One listener for every number box in the app: no exponent letters or signs (Ctrl/Cmd shortcuts stay). */
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
