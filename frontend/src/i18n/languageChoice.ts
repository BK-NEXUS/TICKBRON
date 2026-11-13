import { DEFAULT_LANGUAGE, isLanguage, type Language } from './options'

export const LANGUAGE_KEY = 'tickbron.language'

// Brauzer saqlawı bloklanǵan bolıwı múmkin (jeke oyna, sayt maǵlıwmatı óshken): ilova onsız islewi kerek
export const readStored = (key: string): string | null => {
  try { return localStorage.getItem(key) } catch { return null }
}

export const writeStored = (key: string, value: string) => {
  try { localStorage.setItem(key, value) } catch { /* tańlaw tek yadta saqlanbaydı */ }
}

/** Yadta saqlanǵan til, bolmasa saytta bar bolsa brauzerdiń tili, bolmasa ádetdegi */
export function initialLanguage(): Language {
  const stored = readStored(LANGUAGE_KEY)
  if (isLanguage(stored)) return stored
  const browser = (typeof navigator === 'undefined' ? '' : navigator.language).slice(0, 2).toLowerCase()
  return isLanguage(browser) ? browser : DEFAULT_LANGUAGE
}

let active: Language | null = null

/** Provider ápiwayı kodqa (API wrapper) bet házir qaysı tilde ekenin aytadı */
export function setActiveLanguage(language: Language): void {
  active = language
}

export function getActiveLanguage(): Language {
  return active ?? initialLanguage()
}
