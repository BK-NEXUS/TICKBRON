import type { MessageKey } from '../i18n/messages/en'

type Translate = (key: MessageKey, params?: Record<string, string | number>) => string

export interface ChangeText {
  /** Short text for the card, e.g. "+25.0% vs last month"; empty when there is nothing to compare with */
  text: string
  tone: 'up' | 'down' | 'same' | 'none'
}

/** The change in percent of this month against last month, as a card caption (null: last month was empty). */
export function monthChange(pct: string | null, t: Translate): ChangeText {
  if (pct === null) return { text: t('ownerStatus.change.none'), tone: 'none' }
  const value = Number(pct)
  if (value === 0) return { text: t('ownerStatus.change.same'), tone: 'same' }
  const size = Math.abs(value).toFixed(1)
  return value > 0
    ? { text: t('ownerStatus.change.up', { value: size }), tone: 'up' }
    : { text: t('ownerStatus.change.down', { value: size }), tone: 'down' }
}
