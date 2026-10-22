export const LANGUAGES = [
  { code: 'uz', name: "O'zbekcha" },
  { code: 'ru', name: 'Русский' },
  { code: 'en', name: 'English' },
] as const

// To add a currency: one line here, `currency.<CODE>` in the three catalogs, and the same code in the
// backend registry (backend/common/money.py CURRENCIES). `decimals` is the smallest price unit.
export const CURRENCIES = [
  { code: 'UZS', symbol: "so'm", decimals: 0 },
  { code: 'USD', symbol: '$', decimals: 2 },
  { code: 'KZT', symbol: '₸', decimals: 0 },
  { code: 'RUB', symbol: '₽', decimals: 0 },
] as const

export type Language = (typeof LANGUAGES)[number]['code']
export type Currency = (typeof CURRENCIES)[number]['code']

export const DEFAULT_LANGUAGE: Language = 'uz'
export const DEFAULT_CURRENCY: Currency = 'UZS'

export const isLanguage = (value: unknown): value is Language =>
  LANGUAGES.some((language) => language.code === value)

export const isCurrency = (value: unknown): value is Currency =>
  CURRENCIES.some((currency) => currency.code === value)
