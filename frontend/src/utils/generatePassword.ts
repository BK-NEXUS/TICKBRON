const CHARSET = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*'

/** Random password from the browser's secure source; bytes that would skew the pick are skipped. */
export function generatePassword(length: number): string {
  const limit = 256 - (256 % CHARSET.length)
  let password = ''
  while (password.length < length) {
    for (const byte of crypto.getRandomValues(new Uint8Array(length))) {
      if (byte < limit && password.length < length) password += CHARSET[byte % CHARSET.length]
    }
  }
  return password
}
