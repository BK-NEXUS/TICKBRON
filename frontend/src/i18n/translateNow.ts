import { en, type Catalog, type MessageKey } from './messages/en'
import { uz } from './messages/uz'
import { ru } from './messages/ru'
import { getActiveLanguage } from './languageChoice'
import type { Language } from './options'

export type Params = Record<string, string | number>

export const CATALOGS: Record<Language, Catalog> = { uz, ru, en }

export function translate(language: Language, key: string, params?: Params): string {
  // A key missing in one catalog falls back to English, then to the key itself
  const text = CATALOGS[language][key] ?? (en as Catalog)[key] ?? key
  if (!params) return text
  return text.replace(/\{(\w+)\}/g, (match, name: string) => (name in params ? String(params[name]) : match))
}

/** Text in the language the page is in right now, for plain code (API wrappers, utilities) with no React context */
export function translateNow(key: MessageKey, params?: Params): string {
  return translate(getActiveLanguage(), key, params)
}
