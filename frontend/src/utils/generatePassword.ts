const CHARSET = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*'

function randomString(length: number): string {
  const limit = 256 - (256 % CHARSET.length)
  let password = ''
  while (password.length < length) {
    for (const byte of crypto.getRandomValues(new Uint8Array(length))) {
      if (byte < limit && password.length < length) password += CHARSET[byte % CHARSET.length]
    }
  }
  return password
}

const hasEveryKind = (password: string) => /[A-Za-z]/.test(password) && /[0-9]/.test(password) && /[!@#$%^&*]/.test(password)

/**
 * Random password from the browser's secure source; bytes that would skew the pick are skipped.
 * It always holds a letter, a digit and a special character, as the backend requires; a draw that
 * misses one is thrown away (not patched), so every valid password stays equally likely.
 */
export function generatePassword(length: number): string {
  if (length < 3) throw new RangeError('A password needs room for a letter, a digit and a special character')
  let password = randomString(length)
  while (!hasEveryKind(password)) password = randomString(length)
  return password
}
