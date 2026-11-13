// Baylanıs mánisleri paydalanıwshılar tárepinen teriledi; silteme tek siltemeniń jolın yamasa
// hostın ózgerte almaytuǵın mánisten quriladı.
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

/**
 * Nomerge qońıraw etetuǵın tel: silteme; tek plus hám sanlar qaladı, sol sebepli teriligen hesh nárse siltemeni ózgerte
 * almaydı.
 */
export function phoneLink(value: string): string | null {
  const dialled = value.replace(/[^0-9+]/g, '')
  return /^\+?\d{7,15}$/.test(dialled) ? `tel:${dialled}` : null
}
