/** Shortest password the backend accepts (AUTH_PASSWORD_VALIDATORS); the server checks the rest. */
export const MIN_PASSWORD_LENGTH = 12

export type NewPasswordProblem = 'mismatch' | 'short'

/** The first problem the browser can see before sending a new password, or null. */
export function newPasswordProblem(password: string, confirmation: string): NewPasswordProblem | null {
  if (password !== confirmation) return 'mismatch'
  if (password.length < MIN_PASSWORD_LENGTH) return 'short'
  return null
}
