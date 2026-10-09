// Checks for the TEST MODE card form. The card values stay in the form's own state: nothing here is
// logged, stored or sent. Real payments use the Payme / Click / Visa pages, never this form.

const CARD_LENGTH = 16
const MAX_YEARS_AHEAD = 20

export const cardNumberDigits = (input: string): string => input.replace(/\D/g, '').slice(0, CARD_LENGTH)

export const formatCardNumber = (input: string): string => cardNumberDigits(input).replace(/(\d{4})(?=\d)/g, '$1 ')

function passesLuhn(digits: string): boolean {
  let sum = 0
  for (let i = 0; i < digits.length; i += 1) {
    let digit = Number(digits[digits.length - 1 - i])
    if (i % 2 === 1) {
      digit *= 2
      if (digit > 9) digit -= 9
    }
    sum += digit
  }
  return sum % 10 === 0
}

export const isCardNumberValid = (input: string): boolean => {
  const digits = cardNumberDigits(input)
  return digits.length === CARD_LENGTH && passesLuhn(digits)
}

export function formatExpiry(input: string): string {
  const digits = input.replace(/\D/g, '').slice(0, 4)
  return digits.length > 2 ? `${digits.slice(0, 2)}/${digits.slice(2)}` : digits
}

/** MM/YY, this month or later, at most 20 years ahead */
export function isExpiryValid(input: string, now: Date = new Date()): boolean {
  const match = input.match(/^(\d{2})\/(\d{2})$/)
  if (!match) return false
  const month = Number(match[1])
  const year = 2000 + Number(match[2])
  if (month < 1 || month > 12) return false
  const monthsFromNow = (year - now.getFullYear()) * 12 + (month - 1 - now.getMonth())
  return monthsFromNow >= 0 && monthsFromNow <= MAX_YEARS_AHEAD * 12
}

export const isCvvValid = (input: string): boolean => /^\d{3}$/.test(input)

export const isCardholderValid = (input: string): boolean => /^[\p{L}][\p{L} .'-]*$/u.test(input.trim()) && input.trim().length >= 2
