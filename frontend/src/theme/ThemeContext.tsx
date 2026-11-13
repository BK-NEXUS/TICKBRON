import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'

export type Theme = 'system' | 'light' | 'dark'
type EffectiveTheme = 'light' | 'dark'

const STORAGE_KEY = 'tickbron.theme'
const DARK_QUERY = '(prefers-color-scheme: dark)'

interface ThemeValue {
  theme: Theme
  /** Ekranda ne bar: tańlanǵan tema, yamasa hesh biri tańlanbaǵanda sistema sazlaması */
  effectiveTheme: EffectiveTheme
  setTheme: (theme: Theme) => void
}

// Brauzer saqlawı bloklanǵan bolıwı múmkin: sonda tańlaw tek bet jabılǵansha turadı
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

  // "system" atributtı qaldıradı, sonda stylesheet tiń media query si sheshedi
  useEffect(() => {
    const root = document.documentElement
    if (theme === 'system') root.removeAttribute('data-theme')
    else root.setAttribute('data-theme', theme)
  }, [theme])

  const setTheme = useCallback((next: Theme) => {
    setThemeState(next)
    try {
      localStorage.setItem(STORAGE_KEY, next)
    } catch { /* tańlaw tek yadta saqlanbaydı */ }
  }, [])

  const value = useMemo<ThemeValue>(
    () => ({ theme, effectiveTheme: theme === 'system' ? (systemDark ? 'dark' : 'light') : theme, setTheme }),
    [theme, systemDark, setTheme],
  )
  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
}

// eslint-disable-next-line react-refresh/only-export-components
export const useTheme = () => useContext(ThemeContext)
