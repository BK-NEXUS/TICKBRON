import { en, type Catalog, type MessageKey } from './messages/en'
import { uz } from './messages/uz'
import { ru } from './messages/ru'
import { getActiveLanguage } from './languageChoice'
import type { Language } from './options'

export type Params = Record<string, string | number>

export const CATALOGS: Record<Language, Catalog> = { uz, ru, en }

export function translate(language: Language, key: string, params?: Params): string {
  // Bir katalogta joq kilt inglizshege, keyin kiltiń ózine qaytadı
  const text = CATALOGS[language][key] ?? (en as Catalog)[key] ?? key
  if (!params) return text
  return text.replace(/\{(\w+)\}/g, (match, name: string) => (name in params ? String(params[name]) : match))
}

/** Bet házir qaysı tilde bolsa sol tildegi tekst, React konteksti joq ápiwayı kod (API wrapper ler, utility ler) ushın */
export function translateNow(key: MessageKey, params?: Params): string {
  return translate(getActiveLanguage(), key, params)
}
