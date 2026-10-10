import { useState } from 'react'
import type { FormEvent } from 'react'
import { useI18n } from '../i18n/I18nContext'
import { noShowAdapter } from '../adapters/noShowAdapter'
import { noShowErrorKey } from '../utils/noShowErrors'
import { DialogModal } from './DialogModal'

const MIN_LENGTH = 10
const MAX_LENGTH = 500

interface ReportableBooking {
  id: number
  property_name: string
  confirmation_code: string
  check_in: string
  check_out: string
}

interface NoShowReportDialogProps {
  booking: ReportableBooking
  onReported: () => void
  onClose: () => void
}

/** The owner tells staff the guest did not arrive. Staff decide; nothing is refunded here. */
export function NoShowReportDialog({ booking, onReported, onClose }: NoShowReportDialogProps) {
  const { t, formatDate } = useI18n()
  const [comment, setComment] = useState('')
  const [sending, setSending] = useState(false)
  const [errorKey, setErrorKey] = useState<ReturnType<typeof noShowErrorKey> | null>(null)

  const trimmed = comment.trim()
  const canSend = trimmed.length >= MIN_LENGTH && !sending

  const submit = async (event: FormEvent) => {
    event.preventDefault()
    if (!canSend) return
    setSending(true)
    setErrorKey(null)
    const result = await noShowAdapter.reportNoShow(booking.id, trimmed)
    setSending(false)
    if (result.error || !result.data) {
      setErrorKey(noShowErrorKey(result.code, result.fieldErrors))
      return
    }
    onReported()
  }

  return (
    <DialogModal titleId="no-show-dialog-title" title={t('noShow.dialog.title')} onClose={onClose}>
      <p className="modal-subtitle">
        {t('noShow.dialog.intro', {
          code: booking.confirmation_code,
          hotel: booking.property_name,
          checkIn: formatDate(booking.check_in),
          checkOut: formatDate(booking.check_out),
        })}
      </p>
      <form onSubmit={submit}>
        {errorKey && <p className="alert alert-error" role="alert">{t(errorKey)}</p>}
        <div className="form-group">
          <label htmlFor="no-show-comment">{t('noShow.dialog.comment')}</label>
          <textarea
            id="no-show-comment"
            rows={4}
            maxLength={MAX_LENGTH}
            className="form-control"
            value={comment}
            aria-describedby="no-show-comment-hint"
            onChange={(e) => setComment(e.target.value)}
          />
          <small id="no-show-comment-hint" className="form-hint">
            {t('noShow.dialog.hint')} <span>{t('noShow.dialog.counter', { count: comment.length })}</span>
          </small>
        </div>
        <div className="modal-actions">
          <button type="submit" className="btn btn-primary" disabled={!canSend}>
            {sending ? t('noShow.dialog.sending') : t('noShow.dialog.send')}
          </button>
          <button type="button" className="btn btn-secondary" onClick={onClose} disabled={sending}>
            {t('common.cancel')}
          </button>
        </div>
      </form>
    </DialogModal>
  )
}
