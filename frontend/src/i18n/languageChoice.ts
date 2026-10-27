import { DEFAULT_LANGUAGE, isLanguage, type Language } from './options'

export const LANGUAGE_KEY = 'tickbron.language'

// Browser storage can be blocked (private window, site data off): the app must work without it
export const readStored = (key: string): string | null => {
  try { return localStorage.getItem(key) } catch { return null }
}

export const writeStored = (key: string, value: string) => {
  try { localStorage.setItem(key, value) } catch { /* the choice just is not remembered */ }
}

/** The remembered language, else the browser's when the site has it, else the default */
export function initialLanguage(): Language {
  const stored = readStored(LANGUAGE_KEY)
  if (isLanguage(stored)) return stored
  const browser = (typeof navigator === 'undefined' ? '' : navigator.language).slice(0, 2).toLowerCase()
  return isLanguage(browser) ? browser : DEFAULT_LANGUAGE
}

let active: Language | null = null

/** The provider tells plain code (the API wrapper) which language the page is in right now */
export function setActiveLanguage(language: Language): void {
  active = language
}

export function getActiveLanguage(): Language {
  return active ?? initialLanguage()
}
