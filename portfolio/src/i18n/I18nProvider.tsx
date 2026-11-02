import { useCallback, useMemo, useState, type ReactNode } from 'react'
import { I18nContext, type I18nValue } from './context'
import { dictionaries, LANGS, type Lang } from './dictionaries'

const STORAGE_KEY = 'lang'
const DEFAULT_LANG: Lang = 'uz'

function isLang(value: string | null): value is Lang {
  return LANGS.some((l) => l === value)
}

// Storage can be blocked (private mode), so every access is guarded.
function readStoredLang(): Lang {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    return isLang(stored) ? stored : DEFAULT_LANG
  } catch {
    return DEFAULT_LANG
  }
}

function storeLang(lang: Lang): void {
  try {
    localStorage.setItem(STORAGE_KEY, lang)
  } catch {
    // Persisting the choice is a convenience only.
  }
}

export function I18nProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Lang>(readStoredLang)

  const setLang = useCallback((next: Lang) => {
    setLangState(next)
    storeLang(next)
  }, [])

  const value = useMemo<I18nValue>(
    () => ({ lang, setLang, t: (key) => dictionaries[lang][key] ?? key }),
    [lang, setLang],
  )

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>
}
