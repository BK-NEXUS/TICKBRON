// Tekst qutıları ushın teriw filterleri: durıs bola almaytuǵın nárse hesh qashan kórsetilmeydi. Backend birdey qaǵıydalardı
// tekseredi.

const PERSON_NAME_MAX = 100
const PHONE_DIGITS_MAX = 15

/** Qálegen alfavit háripleri, bos orın, defis, nuqta hám ózbek atlarında paydalanılatuǵın apostroflar (' ʻ ʼ ’) */
export const cleanPersonName = (value: string): string =>
  value.replace(/[^\p{L}\p{M} .'ʻʼ’-]/gu, '').slice(0, PERSON_NAME_MAX)

/** Mámleket, region hám qala atları: san joq; "Tashkent (city)" ushın jaqshalarǵa ruxsat */
export const cleanPlaceName = (value: string): string =>
  value.replace(/[^\p{L}\p{M} .'ʻʼ’()-]/gu, '').slice(0, PERSON_NAME_MAX)

/**  bas plus penen sanlar (E.164: eń kóbi 15 san) */
export function cleanPhone(value: string): string {
  const digits = value.replace(/\D/g, '').slice(0, PHONE_DIGITS_MAX)
  return value.trimStart().startsWith('+') ? `+${digits}` : digits
}

/** Plus, mámleket kodı hám 8 den 15 ke shekem san; nomer haqıyqatında bar ma degendi server sheshedi */
export const isPhoneValid = (value: string): boolean => /^\+\d{8,15}$/.test(value.replace(/[\s\-.()]/g, ''))

/** San qutısı qabıllamawı kerek klavishler: eksponent háripleri hám belgiler (bul jerde hesh bir baha yamasa san teris emes) */
export const blocksNumberKey = (key: string): boolean => ['e', 'E', '+', '-'].includes(key)

const PERSON_NAME_FIELDS = new Set(['first_name', 'last_name', 'full_name'])
const PHONE_FIELDS = new Set(['phone', 'phone_number', 'whatsapp'])

/** Forma maydanı atı boyınsha filter, sonda bir ózgeris handler i pútkil formaǵa xızmet ete aladı */
export function cleanField(name: string, value: string): string {
  if (PERSON_NAME_FIELDS.has(name)) return cleanPersonName(value)
  if (PHONE_FIELDS.has(name)) return cleanPhone(value)
  return value
}
