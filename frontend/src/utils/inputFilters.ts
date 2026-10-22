// Typing filters for text boxes: what cannot be valid is never shown. The backend validates the same rules.

const PERSON_NAME_MAX = 100
const PHONE_DIGITS_MAX = 15

/** Letters of any alphabet, space, hyphen, dot and the apostrophes used in Uzbek names (' ʻ ʼ ’) */
export const cleanPersonName = (value: string): string =>
  value.replace(/[^\p{L}\p{M} .'ʻʼ’-]/gu, '').slice(0, PERSON_NAME_MAX)

/** Country, region and city names: no digits; parentheses are allowed for "Tashkent (city)" */
export const cleanPlaceName = (value: string): string =>
  value.replace(/[^\p{L}\p{M} .'ʻʼ’()-]/gu, '').slice(0, PERSON_NAME_MAX)

/** Digits with an optional leading plus (E.164: at most 15 digits) */
export function cleanPhone(value: string): string {
  const digits = value.replace(/\D/g, '').slice(0, PHONE_DIGITS_MAX)
  return value.trimStart().startsWith('+') ? `+${digits}` : digits
}

/** A plus, a country code and 8 to 15 digits; whether the number really exists is the server's call */
export const isPhoneValid = (value: string): boolean => /^\+\d{8,15}$/.test(value.replace(/[\s\-.()]/g, ''))

/** Keys a number box must not accept: exponent letters and signs (no price or count here is negative) */
export const blocksNumberKey = (key: string): boolean => ['e', 'E', '+', '-'].includes(key)

const PERSON_NAME_FIELDS = new Set(['first_name', 'last_name', 'full_name'])
const PHONE_FIELDS = new Set(['phone', 'phone_number', 'whatsapp'])

/** Filter by form field name, so one change handler can serve a whole form */
export function cleanField(name: string, value: string): string {
  if (PERSON_NAME_FIELDS.has(name)) return cleanPersonName(value)
  if (PHONE_FIELDS.has(name)) return cleanPhone(value)
  return value
}
