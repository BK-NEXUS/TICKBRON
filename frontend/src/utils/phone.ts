// Phone numbers are kept in E.164 ("+998901234567") and shown grouped
// ("+998 90 123 45 67"). Only Uzbekistan for now; a country selector adds
// entries to PHONE_COUNTRIES and passes the chosen code to these helpers.

export interface PhoneCountry {
  code: string
  name: string
  flag: string
  dialCode: string
  /** Digits after the country code */
  nationalLength: number
  /** How the national digits are grouped for display */
  groups: number[]
}

export const PHONE_COUNTRIES = {
  UZ: { code: 'UZ', name: 'Uzbekistan', flag: '🇺🇿', dialCode: '998', nationalLength: 9, groups: [2, 3, 2, 2] },
} satisfies Record<string, PhoneCountry>

export type PhoneCountryCode = keyof typeof PHONE_COUNTRIES

export const DEFAULT_PHONE_COUNTRY: PhoneCountryCode = 'UZ'

function nationalDigits(input: string, country: PhoneCountry): string {
  let digits = input.replace(/\D/g, '')
  // The country code is there when the number was typed or pasted in full
  const hasCountryCode = input.trim().startsWith('+') || digits.length > country.nationalLength
  if (hasCountryCode && digits.startsWith(country.dialCode)) {
    digits = digits.slice(country.dialCode.length)
  }
  return digits.slice(0, country.nationalLength)
}

/** What the user typed -> E.164 value, cut at a complete number; '' when there are no digits. */
export function toPhoneValue(input: string, countryCode: PhoneCountryCode = DEFAULT_PHONE_COUNTRY): string {
  const country = PHONE_COUNTRIES[countryCode]
  const national = nationalDigits(input, country)
  return national ? `+${country.dialCode}${national}` : ''
}

/**
 * E.164 value -> "+998 90 123 45 67" (partial numbers too). A stored number from
 * another country is shown as it is, so it is never silently rewritten.
 */
export function formatPhone(value: string, countryCode: PhoneCountryCode = DEFAULT_PHONE_COUNTRY): string {
  const country = PHONE_COUNTRIES[countryCode]
  const prefix = `+${country.dialCode}`
  if (!value || !value.startsWith(prefix)) return value || ''

  const national = value.slice(prefix.length)
  const parts = [prefix]
  let position = 0
  for (const size of country.groups) {
    if (position >= national.length) break
    parts.push(national.slice(position, position + size))
    position += size
  }
  return parts.join(' ')
}

export function isValidPhone(value: string, countryCode: PhoneCountryCode = DEFAULT_PHONE_COUNTRY): boolean {
  const country = PHONE_COUNTRIES[countryCode]
  return new RegExp(`^\\+${country.dialCode}\\d{${country.nationalLength}}$`).test(value)
}

export function phoneExample(countryCode: PhoneCountryCode = DEFAULT_PHONE_COUNTRY): string {
  const country = PHONE_COUNTRIES[countryCode]
  return formatPhone(`+${country.dialCode}${'901234567890'.slice(0, country.nationalLength)}`, countryCode)
}

export function phoneErrorMessage(countryCode: PhoneCountryCode = DEFAULT_PHONE_COUNTRY): string {
  return `Enter a valid phone number, e.g. ${phoneExample(countryCode)}`
}
