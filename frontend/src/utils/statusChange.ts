import type { MessageKey } from '../i18n/messages/en'

type Translate = (key: MessageKey, params?: Record<string, string | number>) => string

export interface ChangeText {
  /** Karta ushın qısqa tekst, mısalı "+25.0% vs last month"; salıstırıwǵa hesh nárse bolmasa bos */
  text: string
  tone: 'up' | 'down' | 'same' | 'none'
}

/** Usı aydıń aldınǵı ayǵa qarata procent penen ózgerisi, karta jazıwı retinde (null: aldınǵı ay bos edi). */
export function monthChange(pct: string | null, t: Translate): ChangeText {
  if (pct === null) return { text: t('ownerStatus.change.none'), tone: 'none' }
  const value = Number(pct)
  if (value === 0) return { text: t('ownerStatus.change.same'), tone: 'same' }
  const size = Math.abs(value).toFixed(1)
  return value > 0
    ? { text: t('ownerStatus.change.up', { value: size }), tone: 'up' }
    : { text: t('ownerStatus.change.down', { value: size }), tone: 'down' }
}
