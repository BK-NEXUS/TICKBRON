import { useId, useState } from 'react'
import { useI18n } from '../i18n/I18nContext'
import { bookingAdapter, type Booking } from '../adapters/bookingAdapter'
import { DialogModal } from './DialogModal'

interface CancelBookingDialogProps {
  bookingId: number
  onClose: () => void
  /** The cancelled booking */
  onCancelled: (booking: Booking) => void
}

/** The guest cancels a booking. Cancelling is free (cash at the hotel); nothing happens until they confirm. */
export function CancelBookingDialog({ bookingId, onClose, onCancelled }: CancelBookingDialogProps) {
  const { t } = useI18n()
  const titleId = useId()
  const [cancelling, setCancelling] = useState(false)
  const [cancelError, setCancelError] = useState<string | null>(null)

  const confirm = async () => {
    setCancelling(true)
    setCancelError(null)
    const result = await bookingAdapter.cancelBooking(bookingId)
    setCancelling(false)
    if (result.data) onCancelled(result.data)
    else setCancelError(result.error || t('cancel.failed'))
  }

  return (
    <DialogModal titleId={titleId} title={t('cancel.title')} onClose={onClose}>
      <p className="cancel-dialog-consequence">{t('cancel.freeNote')}</p>
      {cancelError && <p role="alert" className="alert alert-error">{cancelError}</p>}
      <div className="modal-actions">
        <button type="button" className="btn btn-secondary" onClick={onClose}>{t('cancel.keep')}</button>
        <button type="button" className="btn btn-danger" disabled={cancelling} onClick={() => void confirm()}>
          {cancelling ? t('cancel.cancelling') : t('cancel.confirm')}
        </button>
      </div>
    </DialogModal>
  )
}
