// Contact values are typed by users; a link is built only from a value that cannot
// change the link's path or host.
const TELEGRAM_USERNAME = /^[A-Za-z0-9_]{5,32}$/
const WHATSAPP_DIGITS = /^\d{7,15}$/

export function telegramLink(value: string): string | null {
  const username = value.startsWith('@') ? value.slice(1) : value
  return TELEGRAM_USERNAME.test(username) ? `https://t.me/${username}` : null
}

export function whatsappLink(value: string): string | null {
  const digits = value.replace(/[^0-9]/g, '')
  return WHATSAPP_DIGITS.test(digits) ? `https://wa.me/${digits}` : null
}
