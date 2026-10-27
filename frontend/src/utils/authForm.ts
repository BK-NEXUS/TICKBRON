const EMAIL_SHAPE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

/** The first problem with the typed fields; the site words it, not the browser, so it follows the page language. */
export function authFormProblem(fields: string[], email: string): 'required' | 'email' | null {
  if (fields.some((value) => !value.trim())) return 'required'
  return EMAIL_SHAPE.test(email.trim()) ? null : 'email'
}
