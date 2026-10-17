import { useEffect, useState } from 'react'

const supported = () => typeof window !== 'undefined' && typeof window.matchMedia === 'function'

/** Whether a CSS media query matches right now, updated when the screen changes (false without matchMedia). */
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
