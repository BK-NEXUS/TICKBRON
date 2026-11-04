import { createContext, useContext } from 'react'

export type Theme = 'dark' | 'light'
export type Origin = { x: number; y: number }

export type ThemeValue = { theme: Theme; toggle: (origin?: Origin) => void }

export const ThemeContext = createContext<ThemeValue | null>(null)

export function useTheme(): ThemeValue {
  const ctx = useContext(ThemeContext)
  if (!ctx) throw new Error('useTheme must be used inside ThemeProvider')
  return ctx
}
