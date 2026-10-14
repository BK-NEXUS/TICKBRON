import { createContext, useContext, useEffect, useRef } from 'react'

export interface Crumb {
  label: string
  /** Where the crumb leads; the last crumb (the current page) has none */
  to?: string
  /** An in-page level (e.g. a partner dashboard view): a button instead of a link */
  onClick?: () => void
}

interface BreadcrumbContextValue {
  trail: Crumb[] | null
  setTrail: (trail: Crumb[] | null) => void
}

export const BreadcrumbContext = createContext<BreadcrumbContextValue>({ trail: null, setTrail: () => {} })

/**
 * Give the current page its own trail after Home, e.g. [{ label: 'Tashkent', to }, { label: 'Hotel' }].
 * Pass null while the data is loading (the route's default trail shows meanwhile).
 */
export function usePageTrail(trail: Crumb[] | null) {
  const { setTrail } = useContext(BreadcrumbContext)
  // Labels and links decide when the trail changed (onClick handlers are new functions every render)
  const key = JSON.stringify(trail?.map(crumb => [crumb.label, crumb.to ?? null, !!crumb.onClick]) ?? null)
  const latest = useRef(trail)
  latest.current = trail
  useEffect(() => {
    // Clicks call the handler from the latest render, not the one from when the labels last changed
    setTrail(latest.current?.map((crumb, index) =>
      crumb.onClick ? { ...crumb, onClick: () => latest.current?.[index]?.onClick?.() } : crumb
    ) ?? null)
  }, [key, setTrail])
  useEffect(() => () => setTrail(null), [setTrail])
}
