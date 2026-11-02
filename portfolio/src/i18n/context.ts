import { createContext, useContext } from 'react'
import type { Lang } from './dictionaries'

export type I18nValue = { lang: Lang; setLang: (lang: Lang) => void; t: (key: string) => string }

export const I18nContext = createContext<I18nValue | null>(null)

export function useI18n(): I18nValue {
  const ctx = useContext(I18nContext)
  if (!ctx) throw new Error('useI18n must be used inside I18nProvider')
  return ctx
}
