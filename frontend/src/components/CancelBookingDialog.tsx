import { useCallback, useEffect, useId, useState } from 'react'
import { useI18n } from '../i18n/I18nContext'
import { bookingAdapter, type Booking, type CancelPreview, type CancelRefund } from '../adapters/bookingAdapter'
import { DialogModal } from './DialogModal'

interface CancelBookingDialogProps {
  bookingId: number
  onClose: () => void
  /** The cancelled booking and what was refunded */
  onCancelled: (booking: Booking & { refund: CancelRefund }) => void
}

/**
 * The guest cancels a booking. The refund is shown FIRST, exactly as the backend computes it
 * (`cancel-preview`); nothing is calculated here and nothing is cancelled until the guest confirms.
 */
export function CancelBookingDialog({ bookingId, onClose, onCancelled }: CancelBookingDialogProps) {
  const { t, formatMoney } = useI18n()
  const titleId = useId()
  const [preview, setPreview] = useState<CancelPreview | null>(null)
  const [previewError, setPreviewError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [cancelling, setCancelling] = useState(false)
  const [cancelError, setCancelError] = useState<string | null>(null)

  // Doubles as the Try Again button
  const loadPreview = useCallback(async () => {
    setLoading(true)
    setPreviewError(null)
    const result = await bookingAdapter.getCancelPreview(bookingId)
    if (result.data) setPreview(result.data)
    else setPreviewError(result.error || '')
    setLoading(false)
  }, [bookingId])

  useEffect(() => {
    void loadPreview()
  }, [loadPreview])

  const confirm = async () => {
    setCancelling(true)
    setCancelError(null)
    const result = await bookingAdapter.cancelBooking(bookingId)
    setCancelling(false)
    if (result.data) onCancelled(result.data)
    else setCancelError(result.error || t('cancel.failed'))
  }

  const consequence = () => {
    if (!preview) return null
    const amount = Number(preview.refund_amount)
    if (amount > 0) {
      return t('cancel.willRefund', {
        amount: formatMoney(preview.refund_amount, preview.refund_currency, { minDecimals: 0, maxDecimals: 0 }),
        percent: preview.refund_percent ?? 0,
      })
    }
    if (preview.refund_percent === null) return t('cancel.noPromise')
    return t(preview.refund_percent === 0 ? 'cancel.noRefund' : 'cancel.nothingPaid')
  }

  return (
    <DialogModal titleId={titleId} title={t('cancel.title')} onClose={onClose}>
      {loading && <p role="status">{t('cancel.loadingPreview')}</p>}
      {previewError !== null && (
        <div role="alert" className="alert alert-error">
          <p>{previewError || t('cancel.previewError')}</p>
          <button type="button" className="btn btn-secondary btn-sm" onClick={() => void loadPreview()}>{t('common.tryAgain')}</button>
        </div>
      )}
      {preview && <p className="cancel-dialog-consequence">{consequence()}</p>}
      {cancelError && <p role="alert" className="alert alert-error">{cancelError}</p>}
      <div className="modal-actions">
        <button type="button" className="btn btn-secondary" onClick={onClose}>{t('cancel.keep')}</button>
        <button type="button" className="btn btn-danger" disabled={!preview || cancelling} onClick={() => void confirm()}>
          {cancelling ? t('cancel.cancelling') : t('cancel.confirm')}
        </button>
      </div>
    </DialogModal>
  )
}
