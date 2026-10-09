export const LANGUAGES = [
  { code: 'uz', name: "O'zbekcha" },
  { code: 'ru', name: 'Русский' },
  { code: 'en', name: 'English' },
] as const

export const CURRENCIES = [
  { code: 'UZS', symbol: "so'm" },
  { code: 'USD', symbol: '$' },
] as const

export type Language = (typeof LANGUAGES)[number]['code']
export type Currency = (typeof CURRENCIES)[number]['code']

export const DEFAULT_LANGUAGE: Language = 'uz'
export const DEFAULT_CURRENCY: Currency = 'UZS'

export const isLanguage = (value: unknown): value is Language =>
  LANGUAGES.some((language) => language.code === value)

export const isCurrency = (value: unknown): value is Currency =>
  CURRENCIES.some((currency) => currency.code === value)
