/* eslint-disable react-refresh/only-export-components -- the provider, its hooks and helpers belong together */
import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import type { MessageKey, PluralKey } from './messages/en'
import { CATALOGS, translate, type Params } from './translateNow'
import { formatMoney as formatMoneyFor, type MoneyOptions } from './format'
import {
  DEFAULT_CURRENCY, isCurrency, type Currency, type Language,
} from './options'
import { LANGUAGE_KEY, initialLanguage, readStored, setActiveLanguage, writeStored } from './languageChoice'

const LOCALES: Record<Language, string> = { uz: 'uz-UZ', ru: 'ru-RU', en: 'en-US' }
const CURRENCY_KEY = 'tickbron.currency'

interface I18nValue {
  language: Language
  currency: Currency
  setLanguage: (language: Language) => void
  setCurrency: (currency: Currency) => void
  t: (key: MessageKey, params?: Params) => string
  /** San menen tekst: tildiń kóplik formasın tańlaydı ("x.one", "x.few", ..., "x.other"); {count} toltırıladı */
  tp: (base: PluralKey, count: number, params?: Params) => string
  /** Bet tilindegi sana ("2026-10-09" yamasa Date); bos yamasa jaramsız bolsa '' */
  formatDate: (value: string | Date, options?: Intl.DateTimeFormatOptions) => string
  /** Bet tilindegi mámleket atı (inglizsha atlar ilovanıń óz dizimnen keledi) */
  regionName: (code: string, fallback: string) => string
  /** Bet tilindegi "Mon, Sep 28" */
  formatDay: (value: string | Date) => string
  /** Summa qaysı valyutada bolsa sol valyutada; tańlanǵan valyuta tek hesh nárse berilmegende */
  formatMoney: (amount: number | string, currency?: string, options?: MoneyOptions) => string
}

function initialCurrency(): Currency {
  const stored = readStored(CURRENCY_KEY)
  return isCurrency(stored) ? stored : DEFAULT_CURRENCY
}

function translatePlural(language: Language, base: string, count: number, params?: Params): string {
  const form = new Intl.PluralRules(LOCALES[language]).select(count)
  const key = CATALOGS[language][`${base}.${form}`] !== undefined ? `${base}.${form}` : `${base}.other`
  return translate(language, key, { count, ...params })
}

function parseDate(value: string | Date): Date | null {
  // Waqıtsız sana kalendar kúnniń ózi, UTC yarım tún emes
  const day = typeof value === 'string' ? value.match(/^(\d{4})-(\d{2})-(\d{2})$/) : null
  const date = day ? new Date(Number(day[1]), Number(day[2]) - 1, Number(day[3])) : new Date(value)
  return Number.isNaN(date.getTime()) ? null : date
}

const DAY_FORMAT: Intl.DateTimeFormatOptions = { weekday: 'short', month: 'short', day: 'numeric' }

function buildValue(
  language: Language,
  currency: Currency,
  setLanguage: (language: Language) => void,
  setCurrency: (currency: Currency) => void,
): I18nValue {
  return {
    language,
    currency,
    setLanguage,
    setCurrency,
    t: (key, params) => translate(language, key, params),
    tp: (base, count, params) => translatePlural(language, base, count, params),
    formatDate: (value, options = { day: 'numeric', month: 'short', year: 'numeric' }) => {
      const date = value ? parseDate(value) : null
      return date ? new Intl.DateTimeFormat(LOCALES[language], options).format(date) : ''
    },
    regionName: (code, fallback) => {
      if (language === 'en') return fallback
      try {
        return new Intl.DisplayNames(LOCALES[language], { type: 'region' }).of(code) ?? fallback
      } catch {
        return fallback
      }
    },
    formatDay: (value) => {
      const date = value ? parseDate(value) : null
      return date ? new Intl.DateTimeFormat(LOCALES[language], DAY_FORMAT).format(date) : ''
    },
    formatMoney: (amount, forCurrency = currency, options) => formatMoneyFor(amount, forCurrency, language, options),
  }
}

// Komponent provider siz kórsetilgende paydalanıladı (izolyaciyalanǵan testler): inglizsha tekst, UZS
const I18nContext = createContext<I18nValue>(buildValue('en', DEFAULT_CURRENCY, () => {}, () => {}))

/** Bettiń i18n i berilmegen ápiwayı funkciyalar (utility ler, testler) ushın inglizsha tekst hám sanalar */
export const englishI18n: I18nValue = buildValue('en', DEFAULT_CURRENCY, () => {}, () => {})
export type { I18nValue }

export function I18nProvider({ children }: { children: ReactNode }) {
  const [language, setLanguageState] = useState<Language>(initialLanguage)
  const [currency, setCurrencyState] = useState<Currency>(initialCurrency)

  useEffect(() => {
    document.documentElement.lang = language
    setActiveLanguage(language)
  }, [language])

  const setLanguage = useCallback((next: Language) => {
    setLanguageState(next)
    writeStored(LANGUAGE_KEY, next)
  }, [])
  const setCurrency = useCallback((next: Currency) => {
    setCurrencyState(next)
    writeStored(CURRENCY_KEY, next)
  }, [])

  const value = useMemo(
    () => buildValue(language, currency, setLanguage, setCurrency),
    [language, currency, setLanguage, setCurrency],
  )
  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>
}

export const useI18n = () => useContext(I18nContext)

type TextTree = { readonly [name: string]: MessageKey | TextTree | ((...args: never[]) => unknown) }
type Translated<T> = {
  -readonly [K in keyof T]: T[K] extends MessageKey
    ? string
    : T[K] extends (...args: never[]) => unknown ? T[K] : T[K] extends object ? Translated<T[K]> : T[K]
}

/** Xabar kilt leri aǵashın belgileydi (ishki obyektlerge ruxsat); `useTexts` ushın literal kilt túrlerin saqlaydı. */
export const textKeys = <const T extends TextTree>(tree: T): T => tree

// Xabar kilti bolmaǵan qatarlar (mısalı 'day' sıyaqlı id ler) ózgerissiz qaytadı, sol sebepli aǵash ekewin de alıp júre aladı
function translateNode(node: unknown, t: (key: MessageKey) => string): unknown {
  if (typeof node === 'string') return t(node as MessageKey)
  if (Array.isArray(node)) return node.map(item => translateNode(item, t))
  if (node !== null && typeof node === 'object') {
    return Object.fromEntries(Object.entries(node).map(([name, value]) => [name, translateNode(value, t)]))
  }
  return node
}

/**
 * Xabar kilt leri aǵashın birden awdaradı: `const TEXT = useTexts(TEXT_KEYS)` `TEXT.title` shaqırıwların ózgerissiz saqlaydı.
 */
export function useTexts<T extends TextTree>(tree: T): Translated<T> {
  const { t } = useI18n()
  return translateNode(tree, t) as Translated<T>
}
