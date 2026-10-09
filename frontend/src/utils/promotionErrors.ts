import type { MessageKey } from '../i18n/messages/en'

const KNOWN_CODES = [
  'overlap', 'bad_dates', 'start_in_past', 'start_too_far', 'too_long', 'bad_priority', 'bad_price',
  'bad_currency', 'note_too_long', 'bad_status', 'already_paid', 'reason_required', 'reason_too_long', 'not_found',
] as const

/** Message key for a backend promotion error code; unknown codes get the generic message. */
export function promotionErrorKey(code: string | null): MessageKey {
  const known = (KNOWN_CODES as readonly string[]).includes(code ?? '')
  return (known ? `promoAdmin.error.${code}` : 'promoAdmin.error.generic') as MessageKey
}
