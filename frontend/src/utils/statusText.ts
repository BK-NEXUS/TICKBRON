import type { MessageKey } from '../i18n/messages/en'

type StatusGroup = 'status.booking' | 'status.payment'

/** API den status bet tilinde; bul ilova ele bilmeytuǵını bas háripi menen kórsetiledi, hesh qashan kilt retinde emes. */
export function statusText(group: StatusGroup, status: string, t: (key: MessageKey) => string): string {
  const key = `${group}.${status}` as MessageKey
  const known = t(key) !== key
  return known ? t(key) : status.charAt(0).toUpperCase() + status.slice(1)
}
