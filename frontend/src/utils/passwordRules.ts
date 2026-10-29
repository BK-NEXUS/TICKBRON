/** Shortest password the backend accepts (AUTH_PASSWORD_VALIDATORS); the server checks the rest. */
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

/** The first rule the password breaks (same rules as the backend: length, a letter, a digit, a special character). */
export function passwordFormatProblem(password: string, minLength = MIN_PASSWORD_LENGTH): PasswordFormatProblem | null {
  if (password.length < minLength) return 'short'
  if (!/\p{L}/u.test(password)) return 'noLetter'
  if (!/\p{Nd}/u.test(password)) return 'noDigit'
  if (!/[^\p{L}\p{N}\s]/u.test(password)) return 'noSpecial'
  return null
}

/** The first problem the browser can see before sending a new password, or null. */
export function newPasswordProblem(password: string, confirmation: string): NewPasswordProblem | null {
  if (password !== confirmation) return 'mismatch'
  return passwordFormatProblem(password)
}
