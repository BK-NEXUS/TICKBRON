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
 * Brauzerdiń qáwipsiz derekinen tosınarlıq parol; tańlawdı buzatuǵın baytlar ótkizip jiberiledi.
 * Ol hárdayım háripti, sandı hám arnawlı belgini alıp júredi, backend talap etkenindey; birin
 * taslap ketken tańlaw taslanadı (túzetilmeydi), sol sebepli hár jaramlı parol birdey itimallıqqa iye.
 */
export function generatePassword(length: number): string {
  if (length < 3) throw new RangeError('A password needs room for a letter, a digit and a special character')
  let password = randomString(length)
  while (!hasEveryKind(password)) password = randomString(length)
  return password
}
