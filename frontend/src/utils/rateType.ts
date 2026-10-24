import type { MessageKey } from '../i18n/messages/en'

const KNOWN_TYPES = ['standard', 'non_refundable', 'early_bird', 'last_minute', 'long_stay', 'seasonal', 'corporate', 'promo'] as const

/** The readable name of a rate plan type; a type without a translation shows its code as words */
export function rateTypeLabel(rateType: string, t: (key: MessageKey) => string): string {
  if ((KNOWN_TYPES as readonly string[]).includes(rateType)) return t(`rate.${rateType}` as MessageKey)
  return rateType
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}
