import type { MessageKey } from '../i18n/messages/en'

type StatusGroup = 'status.booking' | 'status.payment'

/** A status from the API in the page language; one this app does not know yet is shown capitalized, never as a key. */
export function statusText(group: StatusGroup, status: string, t: (key: MessageKey) => string): string {
  const key = `${group}.${status}` as MessageKey
  const known = t(key) !== key
  return known ? t(key) : status.charAt(0).toUpperCase() + status.slice(1)
}
