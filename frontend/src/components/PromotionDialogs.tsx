import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { DialogModal as Modal } from './DialogModal'
import { useI18n } from '../i18n/I18nContext'
import { promotionAdapter, type AdminPromotion, type PromotionStats } from '../adapters/promotionAdapter'
import { promotionErrorKey } from '../utils/promotionErrors'

interface HotelRef {
  id: number
  name: string
  status: string
}

interface CreatePromotionDialogProps {
  hotel: HotelRef
  onCreated: () => void
  onClose: () => void
}

/** Create a promotion for one hotel. Starts unpaid: it is shown only after "Mark as paid". */
export function CreatePromotionDialog({ hotel, onCreated, onClose }: CreatePromotionDialogProps) {
  const { t } = useI18n()
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [priority, setPriority] = useState('0')
  const [price, setPrice] = useState('')
  const [currency, setCurrency] = useState('UZS')
  const [note, setNote] = useState('')
  const [saving, setSaving] = useState(false)
  const [errorKey, setErrorKey] = useState<ReturnType<typeof promotionErrorKey> | null>(null)

  const submit = async (event: FormEvent) => {
    event.preventDefault()
    setSaving(true)
    setErrorKey(null)
    const result = await promotionAdapter.createPromotion({
      property: hotel.id,
      start_date: startDate,
      end_date: endDate,
      priority: Number(priority) || 0,
      price_amount: price.trim() === '' ? null : price.trim(),
      price_currency: currency.trim().toUpperCase(),
      note: note.trim(),
    })
    setSaving(false)
    if (result.error || !result.data) {
      setErrorKey(promotionErrorKey(result.code))
      return
    }
    onCreated()
  }

  return (
    <Modal titleId="promotion-create-title" title={t('promoAdmin.promoteHotel', { hotel: hotel.name })} onClose={onClose}>
      <form onSubmit={submit}>
        {hotel.status !== 'active' && <p className="alert alert-warning">{t('promoAdmin.hotelNotActive')}</p>}
        {errorKey && <p className="alert alert-error" role="alert">{t(errorKey)}</p>}
        <div className="form-group">
          <label htmlFor="promo-start">{t('promoAdmin.form.startDate')}</label>
          <input id="promo-start" type="date" className="form-control" value={startDate}
            onChange={(e) => setStartDate(e.target.value)} required />
        </div>
        <div className="form-group">
          <label htmlFor="promo-end">{t('promoAdmin.form.endDate')}</label>
          <input id="promo-end" type="date" className="form-control" value={endDate}
            min={startDate || undefined} onChange={(e) => setEndDate(e.target.value)} required />
        </div>
        <div className="form-group">
          <label htmlFor="promo-priority">{t('promoAdmin.form.priority')}</label>
          <input id="promo-priority" type="number" min={0} max={100} className="form-control" value={priority}
            aria-describedby="promo-priority-hint" onChange={(e) => setPriority(e.target.value)} />
          <small id="promo-priority-hint" className="form-hint">{t('promoAdmin.form.priorityHint')}</small>
        </div>
        <div className="form-group">
          <label htmlFor="promo-price">{t('promoAdmin.form.price')}</label>
          <input id="promo-price" type="number" min={0} step="any" className="form-control" value={price}
            onChange={(e) => setPrice(e.target.value)} />
        </div>
        <div className="form-group">
          <label htmlFor="promo-currency">{t('promoAdmin.form.currency')}</label>
          <input id="promo-currency" type="text" maxLength={3} className="form-control" value={currency}
            onChange={(e) => setCurrency(e.target.value)} />
        </div>
        <div className="form-group">
          <label htmlFor="promo-note">{t('promoAdmin.form.note')}</label>
          <textarea id="promo-note" rows={3} maxLength={500} className="form-control" value={note}
            aria-describedby="promo-note-hint" onChange={(e) => setNote(e.target.value)} />
          <small id="promo-note-hint" className="form-hint">{t('promoAdmin.form.noteHint')}</small>
        </div>
        <p className="form-hint">{t('promoAdmin.form.paymentHint')}</p>
        <div className="modal-actions">
          <button type="submit" className="btn btn-primary" disabled={saving || !startDate || !endDate}>
            {saving ? t('promoAdmin.form.saving') : t('promoAdmin.form.create')}
          </button>
          <button type="button" className="btn btn-secondary" onClick={onClose} disabled={saving}>
            {t('common.cancel')}
          </button>
        </div>
      </form>
    </Modal>
  )
}

interface CancelPromotionDialogProps {
  promotion: AdminPromotion
  onCancelled: () => void
  onClose: () => void
}

/** Cancelling needs a reason for the books; the money itself is settled outside the platform. */
export function CancelPromotionDialog({ promotion, onCancelled, onClose }: CancelPromotionDialogProps) {
  const { t } = useI18n()
  const [reason, setReason] = useState('')
  const [saving, setSaving] = useState(false)
  const [errorKey, setErrorKey] = useState<ReturnType<typeof promotionErrorKey> | null>(null)

  const confirm = async () => {
    setSaving(true)
    setErrorKey(null)
    const result = await promotionAdapter.cancelPromotion(promotion.id, reason.trim())
    setSaving(false)
    if (result.error) {
      setErrorKey(promotionErrorKey(result.code))
      return
    }
    onCancelled()
  }

  return (
    <Modal titleId="promotion-cancel-title" title={t('promoAdmin.cancelTitle')} onClose={onClose}>
      <p className="modal-subtitle">{promotion.property.name}</p>
      {errorKey && <p className="alert alert-error" role="alert">{t(errorKey)}</p>}
      <div className="form-group">
        <label htmlFor="promo-cancel-reason">{t('promoAdmin.cancelReason')}</label>
        <textarea id="promo-cancel-reason" rows={3} maxLength={255} className="form-control" value={reason}
          aria-describedby="promo-cancel-hint" onChange={(e) => setReason(e.target.value)} />
        <small id="promo-cancel-hint" className="form-hint">{t('promoAdmin.cancelReasonHint')}</small>
      </div>
      <div className="modal-actions">
        <button type="button" className="btn btn-danger" onClick={confirm} disabled={saving || !reason.trim()}>
          {t('promoAdmin.cancelConfirm')}
        </button>
        <button type="button" className="btn btn-secondary" onClick={onClose} disabled={saving}>
          {t('promoAdmin.keep')}
        </button>
      </div>
    </Modal>
  )
}

interface PromotionStatsDialogProps {
  promotion: AdminPromotion
  onClose: () => void
}

export function PromotionStatsDialog({ promotion, onClose }: PromotionStatsDialogProps) {
  const { t, formatDate } = useI18n()
  const [stats, setStats] = useState<PromotionStats | null>(null)
  const [failed, setFailed] = useState(false)

  useEffect(() => {
    let cancelled = false
    promotionAdapter.getPromotionStats(promotion.id).then(result => {
      if (cancelled) return
      if (result.data) setStats(result.data)
      else setFailed(true)
    })
    return () => { cancelled = true }
  }, [promotion.id])

  const rate = (ctr: number | null) => (ctr === null ? '-' : `${ctr}%`)

  return (
    <Modal titleId="promotion-stats-title" title={t('promoAdmin.statsTitle', { hotel: promotion.property.name })} onClose={onClose}>
      {failed && <p className="alert alert-error" role="alert">{t('promoAdmin.error.generic')}</p>}
      {!failed && !stats && <p className="loading-state">{t('promoAdmin.stats.loading')}</p>}
      {stats && stats.days.length === 0 && <p className="empty-state">{t('promoAdmin.stats.empty')}</p>}
      {stats && stats.days.length > 0 && (
        <div className="customers-table-container">
          <table className="customers-table">
            <thead>
              <tr>
                <th scope="col">{t('promoAdmin.stats.date')}</th>
                <th scope="col">{t('promoAdmin.stats.impressions')}</th>
                <th scope="col">{t('promoAdmin.stats.clicks')}</th>
                <th scope="col">{t('promoAdmin.stats.ctr')}</th>
              </tr>
            </thead>
            <tbody>
              {stats.days.map(day => (
                <tr key={day.date}>
                  <td>{formatDate(day.date)}</td>
                  <td>{day.impressions}</td>
                  <td>{day.clicks}</td>
                  <td>{rate(day.ctr)}</td>
                </tr>
              ))}
              <tr>
                <th scope="row">{t('promoAdmin.stats.total')}</th>
                <td>{stats.totals.impressions}</td>
                <td>{stats.totals.clicks}</td>
                <td>{rate(stats.totals.ctr)}</td>
              </tr>
            </tbody>
          </table>
        </div>
      )}
      <div className="modal-actions">
        <button type="button" className="btn btn-secondary" onClick={onClose}>{t('promoAdmin.close')}</button>
      </div>
    </Modal>
  )
}
