import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react'
import { flushSync } from 'react-dom'
import { ThemeContext, type Origin, type Theme, type ThemeValue } from './context'

const STORAGE_KEY = 'theme'
const REVEAL_MS = 700

function isTheme(value: string | null): value is Theme {
  return value === 'dark' || value === 'light'
}

// Storage can be blocked (private mode), so every access is guarded.
function readInitialTheme(): Theme {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (isTheme(stored)) return stored
  } catch {
    // Fall through to the system preference.
  }
  return window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark'
}

function storeTheme(theme: Theme): void {
  try {
    localStorage.setItem(STORAGE_KEY, theme)
  } catch {
    // Persisting the choice is a convenience only.
  }
}

function revealFrom(origin: Origin): void {
  const radius = Math.hypot(Math.max(origin.x, window.innerWidth - origin.x), Math.max(origin.y, window.innerHeight - origin.y))
  document.documentElement.animate(
    { clipPath: [`circle(0px at ${origin.x}px ${origin.y}px)`, `circle(${radius}px at ${origin.x}px ${origin.y}px)`] },
    { duration: REVEAL_MS, easing: 'cubic-bezier(0.2, 0.7, 0.1, 1)', pseudoElement: '::view-transition-new(root)' },
  )
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setTheme] = useState<Theme>(readInitialTheme)

  useEffect(() => {
    document.documentElement.dataset.theme = theme
  }, [theme])

  const toggle = useCallback(
    (origin?: Origin) => {
      const next: Theme = theme === 'dark' ? 'light' : 'dark'
      const apply = () => {
        flushSync(() => setTheme(next))
        document.documentElement.dataset.theme = next
        storeTheme(next)
      }
      const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches
      if (reduced || typeof document.startViewTransition !== 'function') {
        apply()
        return
      }
      const transition = document.startViewTransition(apply)
      if (origin) void transition.ready.then(() => revealFrom(origin)).catch(() => {})
    },
    [theme],
  )

  const value = useMemo<ThemeValue>(() => ({ theme, toggle }), [theme, toggle])
  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
}
