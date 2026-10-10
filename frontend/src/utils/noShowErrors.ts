import type { MessageKey } from '../i18n/messages/en'

const KNOWN_CODES = [
  'not_reportable_status', 'too_early', 'window_closed', 'report_exists', 'not_found', 'not_pending',
  'not_decided', 'booking_not_reportable', 'inventory_unavailable', 'refund_refused',
] as const

/** Message key for a no-show error: a known backend code, a bad comment, or the generic message. */
export function noShowErrorKey(code: string | null, fieldErrors?: Record<string, string[]> | null): MessageKey {
  if (code && (KNOWN_CODES as readonly string[]).includes(code)) return `noShow.error.${code}` as MessageKey
  if (fieldErrors && ('comment' in fieldErrors || 'decision_comment' in fieldErrors)) return 'noShow.error.commentInvalid' as MessageKey
  return 'noShow.error.generic' as MessageKey
}
