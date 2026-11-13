/** Backend qabıllaytuǵın eń qısqa parol (AUTH_PASSWORD_VALIDATORS); qalǵanın server tekseredi. */
export const MIN_PASSWORD_LENGTH = 8

export type PasswordFormatProblem = 'short' | 'noLetter' | 'noDigit' | 'noSpecial'
export type NewPasswordProblem = 'mismatch' | PasswordFormatProblem

export const PASSWORD_PROBLEM_MESSAGE = {
  mismatch: 'auth.errorPasswordMismatch',
  short: 'auth.errorPasswordShort',
  noLetter: 'auth.errorPasswordLetter',
  noDigit: 'auth.errorPasswordDigit',
  noSpecial: 'auth.errorPasswordSpecial',
} as const satisfies Record<NewPasswordProblem, string>

/** Parol buzatuǵın birinshi qaǵıyda (backend penen birdey qaǵıydalar: uzınlıq, háripler, san, arnawlı belgi). */
export function passwordFormatProblem(password: string, minLength = MIN_PASSWORD_LENGTH): PasswordFormatProblem | null {
  if (password.length < minLength) return 'short'
  if (!/\p{L}/u.test(password)) return 'noLetter'
  if (!/\p{Nd}/u.test(password)) return 'noDigit'
  if (!/[^\p{L}\p{N}\s]/u.test(password)) return 'noSpecial'
  return null
}

/** Jańa parol jiberilmesten aldın brauzer kóre alatuǵın birinshi mashqala, yamasa null. */
export function newPasswordProblem(password: string, confirmation: string): NewPasswordProblem | null {
  if (password !== confirmation) return 'mismatch'
  return passwordFormatProblem(password)
}
