import { useI18n } from '../i18n/I18nContext'
import type { PeriodRange } from '../adapters/statusAdapter'

import { STATUS_NOTE } from '../utils/statusNote'

interface StatusStayedNoteProps {
  /** Dáwir oynadan aldın pitkende jasırıladı; hárdayım kórsetiw ushın qaldırıń */
  periodRange?: PeriodRange
  /** Testler ushın; ádetde házir */
  today?: Date
}

function isoDate(date: Date): string {
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${date.getFullYear()}-${month}-${day}`
}

/** Jaqın dáwirlerdiń "stayed" sanları janındaǵı kishi eskertiw */
export function StatusStayedNote({ periodRange, today = STATUS_NOTE.businessDate() }: StatusStayedNoteProps) {
  const { t } = useI18n()
  const windowStart = new Date(today)
  windowStart.setDate(windowStart.getDate() - STATUS_NOTE.windowDays)
  if (periodRange?.to && periodRange.to < isoDate(windowStart)) return null
  return <p role="note" className="status-note">{t('status.stayedNote', { days: STATUS_NOTE.windowDays })}</p>
}
