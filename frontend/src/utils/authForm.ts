const EMAIL_SHAPE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

/** Terilgen maydanlardıń birinshi mashqalası; onı sayt jazadı, brauzer emes, sol sebepli ol bet tilin izleydi. */
export function authFormProblem(fields: string[], email: string): 'required' | 'email' | null {
  if (fields.some((value) => !value.trim())) return 'required'
  return EMAIL_SHAPE.test(email.trim()) ? null : 'email'
}
