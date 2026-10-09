// Phone numbers are kept in E.164 ("+998901234567") and shown grouped
// ("+998 90 123 45 67"). The country selector chooses the entry; the backend
// (phonenumbers) stays the final judge of a number.

export interface PhoneCountry {
  code: string
  name: string
  dialCode: string
  /** Fewest and most digits after the country code */
  minLength: number
  maxLength: number
  /** How the national digits are grouped for display; extra digits follow the last group */
  groups: number[]
}

export const PHONE_COUNTRIES = {
  UZ: { code: 'UZ', name: 'Uzbekistan', dialCode: '998', minLength: 9, maxLength: 9, groups: [2, 3, 2, 2] },
  KZ: { code: 'KZ', name: 'Kazakhstan', dialCode: '7', minLength: 10, maxLength: 10, groups: [3, 3, 2, 2] },
  KG: { code: 'KG', name: 'Kyrgyzstan', dialCode: '996', minLength: 9, maxLength: 9, groups: [3, 3, 3] },
  TJ: { code: 'TJ', name: 'Tajikistan', dialCode: '992', minLength: 9, maxLength: 9, groups: [3, 3, 3] },
  TM: { code: 'TM', name: 'Turkmenistan', dialCode: '993', minLength: 8, maxLength: 8, groups: [2, 6] },
  AF: { code: 'AF', name: 'Afghanistan', dialCode: '93', minLength: 9, maxLength: 9, groups: [2, 3, 4] },
  RU: { code: 'RU', name: 'Russia', dialCode: '7', minLength: 10, maxLength: 10, groups: [3, 3, 2, 2] },
  AM: { code: 'AM', name: 'Armenia', dialCode: '374', minLength: 8, maxLength: 8, groups: [2, 3, 3] },
  AT: { code: 'AT', name: 'Austria', dialCode: '43', minLength: 10, maxLength: 11, groups: [3, 4, 4] },
  AZ: { code: 'AZ', name: 'Azerbaijan', dialCode: '994', minLength: 9, maxLength: 9, groups: [2, 3, 2, 2] },
  BY: { code: 'BY', name: 'Belarus', dialCode: '375', minLength: 9, maxLength: 9, groups: [2, 3, 2, 2] },
  BG: { code: 'BG', name: 'Bulgaria', dialCode: '359', minLength: 8, maxLength: 9, groups: [2, 3, 4] },
  BR: { code: 'BR', name: 'Brazil', dialCode: '55', minLength: 10, maxLength: 11, groups: [2, 5, 4] },
  CN: { code: 'CN', name: 'China', dialCode: '86', minLength: 11, maxLength: 11, groups: [3, 4, 4] },
  CZ: { code: 'CZ', name: 'Czechia', dialCode: '420', minLength: 9, maxLength: 9, groups: [3, 3, 3] },
  EG: { code: 'EG', name: 'Egypt', dialCode: '20', minLength: 10, maxLength: 10, groups: [3, 3, 4] },
  FR: { code: 'FR', name: 'France', dialCode: '33', minLength: 9, maxLength: 9, groups: [1, 2, 2, 2, 2] },
  GE: { code: 'GE', name: 'Georgia', dialCode: '995', minLength: 9, maxLength: 9, groups: [3, 3, 3] },
  DE: { code: 'DE', name: 'Germany', dialCode: '49', minLength: 10, maxLength: 11, groups: [3, 4, 4] },
  IN: { code: 'IN', name: 'India', dialCode: '91', minLength: 10, maxLength: 10, groups: [5, 5] },
  ID: { code: 'ID', name: 'Indonesia', dialCode: '62', minLength: 9, maxLength: 12, groups: [3, 4, 4] },
  IR: { code: 'IR', name: 'Iran', dialCode: '98', minLength: 10, maxLength: 10, groups: [3, 3, 4] },
  IL: { code: 'IL', name: 'Israel', dialCode: '972', minLength: 9, maxLength: 9, groups: [2, 3, 4] },
  IT: { code: 'IT', name: 'Italy', dialCode: '39', minLength: 9, maxLength: 10, groups: [3, 3, 4] },
  JP: { code: 'JP', name: 'Japan', dialCode: '81', minLength: 10, maxLength: 10, groups: [2, 4, 4] },
  KW: { code: 'KW', name: 'Kuwait', dialCode: '965', minLength: 8, maxLength: 8, groups: [4, 4] },
  MY: { code: 'MY', name: 'Malaysia', dialCode: '60', minLength: 9, maxLength: 10, groups: [2, 3, 4] },
  NL: { code: 'NL', name: 'Netherlands', dialCode: '31', minLength: 9, maxLength: 9, groups: [2, 3, 4] },
  PK: { code: 'PK', name: 'Pakistan', dialCode: '92', minLength: 10, maxLength: 10, groups: [3, 7] },
  PL: { code: 'PL', name: 'Poland', dialCode: '48', minLength: 9, maxLength: 9, groups: [3, 3, 3] },
  QA: { code: 'QA', name: 'Qatar', dialCode: '974', minLength: 8, maxLength: 8, groups: [4, 4] },
  KR: { code: 'KR', name: 'South Korea', dialCode: '82', minLength: 9, maxLength: 10, groups: [2, 4, 4] },
  SA: { code: 'SA', name: 'Saudi Arabia', dialCode: '966', minLength: 9, maxLength: 9, groups: [2, 3, 4] },
  SG: { code: 'SG', name: 'Singapore', dialCode: '65', minLength: 8, maxLength: 8, groups: [4, 4] },
  ES: { code: 'ES', name: 'Spain', dialCode: '34', minLength: 9, maxLength: 9, groups: [3, 2, 2, 2] },
  SE: { code: 'SE', name: 'Sweden', dialCode: '46', minLength: 7, maxLength: 9, groups: [2, 3, 4] },
  CH: { code: 'CH', name: 'Switzerland', dialCode: '41', minLength: 9, maxLength: 9, groups: [2, 3, 2, 2] },
  TH: { code: 'TH', name: 'Thailand', dialCode: '66', minLength: 9, maxLength: 9, groups: [2, 3, 4] },
  TR: { code: 'TR', name: 'Turkey', dialCode: '90', minLength: 10, maxLength: 10, groups: [3, 3, 2, 2] },
  UA: { code: 'UA', name: 'Ukraine', dialCode: '380', minLength: 9, maxLength: 9, groups: [2, 3, 2, 2] },
  AE: { code: 'AE', name: 'United Arab Emirates', dialCode: '971', minLength: 9, maxLength: 9, groups: [2, 3, 4] },
  GB: { code: 'GB', name: 'United Kingdom', dialCode: '44', minLength: 10, maxLength: 10, groups: [4, 6] },
  US: { code: 'US', name: 'United States', dialCode: '1', minLength: 10, maxLength: 10, groups: [3, 3, 4] },
  VN: { code: 'VN', name: 'Vietnam', dialCode: '84', minLength: 9, maxLength: 9, groups: [2, 3, 4] },
} satisfies Record<string, PhoneCountry>

export type PhoneCountryCode = keyof typeof PHONE_COUNTRIES

export const DEFAULT_PHONE_COUNTRY: PhoneCountryCode = 'UZ'

const COUNTRY_LIST: PhoneCountry[] = Object.values(PHONE_COUNTRIES)

/** Country of an E.164 value, from its dial code (longest first; +7 is Kazakhstan before Russia); null when unknown. */
export function countryFromPhone(value: string): PhoneCountryCode | null {
  if (!value.trim().startsWith('+')) return null
  const digits = value.replace(/\D/g, '')
  const matches = COUNTRY_LIST.filter(country => digits.startsWith(country.dialCode))
  if (!matches.length) return null
  const longest = Math.max(...matches.map(country => country.dialCode.length))
  return matches.find(country => country.dialCode.length === longest)!.code as PhoneCountryCode
}

function nationalDigits(input: string, country: PhoneCountry): string {
  let digits = input.replace(/\D/g, '')
  // The country code is there when the number was typed or pasted in full
  const hasCountryCode = input.trim().startsWith('+') || digits.length > country.maxLength
  if (hasCountryCode && digits.startsWith(country.dialCode)) {
    digits = digits.slice(country.dialCode.length)
  }
  return digits.slice(0, country.maxLength)
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
  if (position < national.length) parts.push(national.slice(position))
  return parts.join(' ')
}

const matchesCountry = (value: string, country: PhoneCountry) =>
  new RegExp(`^\\+${country.dialCode}\\d{${country.minLength},${country.maxLength}}$`).test(value)

/** Complete number of the given country, or of any listed country when none is given. */
export function isValidPhone(value: string, countryCode?: PhoneCountryCode): boolean {
  if (countryCode) return matchesCountry(value, PHONE_COUNTRIES[countryCode])
  return COUNTRY_LIST.some(country => matchesCountry(value, country))
}

export function phoneExample(countryCode: PhoneCountryCode = DEFAULT_PHONE_COUNTRY): string {
  const country = PHONE_COUNTRIES[countryCode]
  return formatPhone(`+${country.dialCode}${'901234567890'.slice(0, country.maxLength)}`, countryCode)
}

export function phoneErrorMessage(countryCode: PhoneCountryCode = DEFAULT_PHONE_COUNTRY): string {
  return `Enter a valid phone number, e.g. ${phoneExample(countryCode)}`
}
