import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import { en, type Catalog, type MessageKey, type PluralKey } from './messages/en'
import { uz } from './messages/uz'
import { ru } from './messages/ru'
import { formatMoney as formatMoneyFor, type MoneyOptions } from './format'
import {
  DEFAULT_CURRENCY, DEFAULT_LANGUAGE, isCurrency, isLanguage, type Currency, type Language,
} from './options'

const CATALOGS: Record<Language, Catalog> = { uz, ru, en }
const LOCALES: Record<Language, string> = { uz: 'uz-UZ', ru: 'ru-RU', en: 'en-US' }
const LANGUAGE_KEY = 'tickbron.language'
const CURRENCY_KEY = 'tickbron.currency'

type Params = Record<string, string | number>

interface I18nValue {
  language: Language
  currency: Currency
  setLanguage: (language: Language) => void
  setCurrency: (currency: Currency) => void
  t: (key: MessageKey, params?: Params) => string
  /** Text with a number: picks the plural form of the language ("x.one", "x.few", ..., "x.other"); {count} is filled in */
  tp: (base: PluralKey, count: number, params?: Params) => string
  /** A date ("2026-10-09" or a Date) in the page language; '' when empty or invalid */
  formatDate: (value: string | Date, options?: Intl.DateTimeFormatOptions) => string
  /** In the currency the amount is in; the selected currency only when none is given */
  formatMoney: (amount: number | string, currency?: string, options?: MoneyOptions) => string
}

// Browser storage can be blocked (private window, site data off): the app must work without it
const readStored = (key: string): string | null => {
  try { return localStorage.getItem(key) } catch { return null }
}
const writeStored = (key: string, value: string) => {
  try { localStorage.setItem(key, value) } catch { /* the choice just is not remembered */ }
}

function initialLanguage(): Language {
  const stored = readStored(LANGUAGE_KEY)
  if (isLanguage(stored)) return stored
  const browser = (typeof navigator === 'undefined' ? '' : navigator.language).slice(0, 2).toLowerCase()
  return isLanguage(browser) ? browser : DEFAULT_LANGUAGE
}

function initialCurrency(): Currency {
  const stored = readStored(CURRENCY_KEY)
  return isCurrency(stored) ? stored : DEFAULT_CURRENCY
}

function translate(language: Language, key: string, params?: Params): string {
  // A key missing in one catalog falls back to English, then to the key itself
  const text = CATALOGS[language][key] ?? (en as Catalog)[key] ?? key
  if (!params) return text
  return text.replace(/\{(\w+)\}/g, (match, name: string) => (name in params ? String(params[name]) : match))
}

function translatePlural(language: Language, base: string, count: number, params?: Params): string {
  const form = new Intl.PluralRules(LOCALES[language]).select(count)
  const key = CATALOGS[language][`${base}.${form}`] !== undefined ? `${base}.${form}` : `${base}.other`
  return translate(language, key, { count, ...params })
}

function parseDate(value: string | Date): Date | null {
  // A date without time is the calendar day itself, not midnight UTC
  const day = typeof value === 'string' ? value.match(/^(\d{4})-(\d{2})-(\d{2})$/) : null
  const date = day ? new Date(Number(day[1]), Number(day[2]) - 1, Number(day[3])) : new Date(value)
  return Number.isNaN(date.getTime()) ? null : date
}

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
    formatMoney: (amount, forCurrency = currency, options) => formatMoneyFor(amount, forCurrency, language, options),
  }
}

// Used when a component renders without the provider (isolated tests): English text, UZS
const I18nContext = createContext<I18nValue>(buildValue('en', DEFAULT_CURRENCY, () => {}, () => {}))

export function I18nProvider({ children }: { children: ReactNode }) {
  const [language, setLanguageState] = useState<Language>(initialLanguage)
  const [currency, setCurrencyState] = useState<Currency>(initialCurrency)

  useEffect(() => {
    document.documentElement.lang = language
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

// eslint-disable-next-line react-refresh/only-export-components
export const useI18n = () => useContext(I18nContext)
