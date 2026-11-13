import { useEffect, useState } from 'react'

const supported = () => typeof window !== 'undefined' && typeof window.matchMedia === 'function'

/** CSS media query hazir sáykes keledi me, ekran ózgergende jańalanadı (matchMedia joq bolsa false). */
export function useMatchMedia(query: string): boolean {
  const [matches, setMatches] = useState(() => (supported() ? window.matchMedia(query).matches : false))

  useEffect(() => {
    if (!supported()) return
    const media = window.matchMedia(query)
    const update = (event: { matches: boolean }) => setMatches(event.matches)
    setMatches(media.matches)
    media.addEventListener('change', update)
    return () => media.removeEventListener('change', update)
  }, [query])

  return matches
}
