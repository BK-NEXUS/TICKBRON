import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'

export type Theme = 'system' | 'light' | 'dark'
type EffectiveTheme = 'light' | 'dark'

const STORAGE_KEY = 'tickbron.theme'
const DARK_QUERY = '(prefers-color-scheme: dark)'

interface ThemeValue {
  theme: Theme
  /** What is on screen: the chosen theme, or the system setting while none is chosen */
  effectiveTheme: EffectiveTheme
  setTheme: (theme: Theme) => void
}

// Browser storage can be blocked: the choice then lasts only until the page is closed
const readStored = (): Theme => {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    return stored === 'light' || stored === 'dark' ? stored : 'system'
  } catch {
    return 'system'
  }
}

const systemPrefersDark = () => typeof window.matchMedia === 'function' && window.matchMedia(DARK_QUERY).matches

const ThemeContext = createContext<ThemeValue>({ theme: 'system', effectiveTheme: 'light', setTheme: () => {} })

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setThemeState] = useState<Theme>(readStored)
  const [systemDark, setSystemDark] = useState(systemPrefersDark)

  useEffect(() => {
    if (typeof window.matchMedia !== 'function') return
    const query = window.matchMedia(DARK_QUERY)
    const update = (event: MediaQueryListEvent) => setSystemDark(event.matches)
    query.addEventListener('change', update)
    return () => query.removeEventListener('change', update)
  }, [])

  // "system" leaves the attribute off so the stylesheet's media query decides
  useEffect(() => {
    const root = document.documentElement
    if (theme === 'system') root.removeAttribute('data-theme')
    else root.setAttribute('data-theme', theme)
  }, [theme])

  const setTheme = useCallback((next: Theme) => {
    setThemeState(next)
    try {
      localStorage.setItem(STORAGE_KEY, next)
    } catch { /* the choice just is not remembered */ }
  }, [])

  const value = useMemo<ThemeValue>(
    () => ({ theme, effectiveTheme: theme === 'system' ? (systemDark ? 'dark' : 'light') : theme, setTheme }),
    [theme, systemDark, setTheme],
  )
  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
}

// eslint-disable-next-line react-refresh/only-export-components
export const useTheme = () => useContext(ThemeContext)
