import { CircleCheck } from 'lucide-react'
import { useI18n } from '../i18n/I18nContext'
import { BUSINESS_TIME_ZONE } from '../utils/dates'

/** What the money part says: a percent after the free window, a percent at any time, or nothing back. */
function useRefundLine() {
  const { t } = useI18n()
  return (percent: number, afterFreeWindow: boolean) => {
    if (percent === 0) return t(afterFreeWindow ? 'cancel.nonRefundableAfter' : 'cancel.nonRefundable')
    return t(afterFreeWindow ? 'cancel.refundAfter' : 'cancel.refundPercent', { percent })
  }
}

interface CancellationNoteProps {
  /** The end of the free window (ISO datetime) or null; a window that is already over counts as none */
  freeUntil: string | null
  /** Percent of the payment refunded after the free window, or at any time without one */
  percentAfter: number
}

/** What a booking or a quote promises about cancelling. The backend decides the refund; this only tells it. */
export function CancellationNote({ freeUntil, percentAfter }: CancellationNoteProps) {
  const { t, formatDate } = useI18n()
  const refundLine = useRefundLine()
  const free = freeUntil !== null && new Date(freeUntil).getTime() > Date.now()
  return (
    <div data-testid="cancellation-note" className={`cancellation-note${free ? ' cancellation-note--free' : ''}`}>
      {free && (
        <p className="cancellation-note-badge">
          <CircleCheck size={16} aria-hidden="true" />{' '}
          {t('cancel.freeUntil', {
            date: formatDate(freeUntil, {
              day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit', timeZone: BUSINESS_TIME_ZONE,
            }),
          })}
        </p>
      )}
      <p className="cancellation-note-line">{refundLine(percentAfter, free)}</p>
    </div>
  )
}

interface PlanCancellationNoteProps {
  freeCancellation?: boolean
  freeCancelHours?: number | null
  refundPercent?: number
}

/** What a rate plan offers before dates are chosen: the badge and how long before the check-in day it lasts. */
export function PlanCancellationNote({ freeCancellation, freeCancelHours, refundPercent }: PlanCancellationNoteProps) {
  const { t, tp } = useI18n()
  const refundLine = useRefundLine()
  if (freeCancellation === undefined && refundPercent === undefined) return null
  return (
    <div data-testid="cancellation-note" className={`cancellation-note${freeCancellation ? ' cancellation-note--free' : ''}`}>
      {freeCancellation && (
        <p className="cancellation-note-badge">
          <CircleCheck size={16} aria-hidden="true" /> {t('cancel.badge')}
          {freeCancelHours !== null && freeCancelHours !== undefined && <> · {tp('cancel.hoursBefore', freeCancelHours)}</>}
        </p>
      )}
      {refundPercent !== undefined && <p className="cancellation-note-line">{refundLine(refundPercent, Boolean(freeCancellation))}</p>}
    </div>
  )
}
