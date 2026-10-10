import { useState } from 'react'
import type { FormEvent } from 'react'
import { useI18n } from '../i18n/I18nContext'
import { noShowAdapter, type StaffNoShowReport } from '../adapters/noShowAdapter'
import { noShowErrorKey } from '../utils/noShowErrors'
import { DialogModal } from './DialogModal'

const MIN_LENGTH = 10
const MAX_LENGTH = 500

export type NoShowDecision = 'approve' | 'reject' | 'reverse'

const TITLE = { approve: 'noShowAdmin.approveTitle', reject: 'noShowAdmin.rejectTitle', reverse: 'noShowAdmin.reverseTitle' } as const
const CONFIRM = { approve: 'noShowAdmin.approveAndRefund', reject: 'noShowAdmin.rejectTitle', reverse: 'noShowAdmin.reverseTitle' } as const

interface NoShowDecisionDialogProps {
  report: StaffNoShowReport
  decision: NoShowDecision
  onDone: () => void
  onClose: () => void
}

/** Staff decide a report. A comment is required: the hotel reads it. */
export function NoShowDecisionDialog({ report, decision, onDone, onClose }: NoShowDecisionDialogProps) {
  const { t, formatMoney } = useI18n()
  const [comment, setComment] = useState('')
  const [sending, setSending] = useState(false)
  const [errorKey, setErrorKey] = useState<ReturnType<typeof noShowErrorKey> | null>(null)

  const trimmed = comment.trim()
  const canSend = trimmed.length >= MIN_LENGTH && !sending
  const preview = report.refund_preview

  const submit = async (event: FormEvent) => {
    event.preventDefault()
    if (!canSend) return
    setSending(true)
    setErrorKey(null)
    const send = { approve: noShowAdapter.approveReport, reject: noShowAdapter.rejectReport, reverse: noShowAdapter.reverseReport }[decision]
    const result = await send.call(noShowAdapter, report.id, trimmed)
    setSending(false)
    if (result.error || !result.data) {
      setErrorKey(noShowErrorKey(result.code, result.fieldErrors))
      return
    }
    onDone()
  }

  return (
    <DialogModal titleId="no-show-decision-title" title={t(TITLE[decision])} onClose={onClose}>
      <p className="modal-subtitle">{report.booking_reference} - {report.property_name}</p>
      {decision === 'approve' && (
        <>
          <p>{t('noShowAdmin.approveHint')}</p>
          {preview && (
            <p className="no-show-refund-preview">
              {t('noShowAdmin.ifApproved', {
                percent: preview.percent,
                paid: formatMoney(preview.paid, preview.currency, { minDecimals: 0, maxDecimals: 0 }),
                amount: formatMoney(preview.amount, preview.currency, { minDecimals: 0, maxDecimals: 0 }),
              })}
            </p>
          )}
        </>
      )}
      {decision === 'reverse' && <p>{t('noShowAdmin.reverseHint')}</p>}
      <form onSubmit={submit}>
        {errorKey && <p className="alert alert-error" role="alert">{t(errorKey)}</p>}
        <div className="form-group">
          <label htmlFor="no-show-decision-comment">{t('noShowAdmin.comment')}</label>
          <textarea
            id="no-show-decision-comment"
            rows={4}
            maxLength={MAX_LENGTH}
            className="form-control"
            value={comment}
            aria-describedby="no-show-decision-hint"
            onChange={(e) => setComment(e.target.value)}
          />
          <small id="no-show-decision-hint" className="form-hint">
            {t('noShowAdmin.commentHint')} <span>{t('noShow.dialog.counter', { count: comment.length })}</span>
          </small>
        </div>
        <div className="modal-actions">
          <button type="submit" className={`btn ${decision === 'reject' ? 'btn-danger' : 'btn-primary'}`} disabled={!canSend}>
            {sending ? t('noShowAdmin.sending') : t(CONFIRM[decision])}
          </button>
          <button type="button" className="btn btn-secondary" onClick={onClose} disabled={sending}>
            {t('common.cancel')}
          </button>
        </div>
      </form>
    </DialogModal>
  )
}
