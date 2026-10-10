import { useCallback, useEffect, useState } from 'react'
import { useI18n } from '../i18n/I18nContext'
import {
  promotionAdapter, type AdminPromotion, type HotelSearchRow, type PromotionList, type PromotionResult,
} from '../adapters/promotionAdapter'
import { promotionErrorKey } from '../utils/promotionErrors'
import { CancelPromotionDialog, CreatePromotionDialog, PromotionStatsDialog } from './PromotionDialogs'
import { PromotionHotelFinder } from './PromotionHotelFinder'
import { StatusPagination } from './StatusPagination'

const PAGE_SIZE = 20
const NAME_FILTER_DELAY_MS = 300
const STATUSES = ['scheduled', 'active', 'paused', 'ended', 'cancelled'] as const
const BADGE: Record<AdminPromotion['status'], string> = {
  active: 'active', scheduled: 'pending', paused: 'pending', ended: 'completed', cancelled: 'cancelled',
}

interface AdminPromotionsProps {
  /** Only a super-admin may change promotions; staff can look. The backend enforces it too. */
  isSuperAdmin: boolean
}

export function AdminPromotions({ isSuperAdmin }: AdminPromotionsProps) {
  const { t, formatDate, formatMoney } = useI18n()
  const [nameInput, setNameInput] = useState('')
  const [name, setName] = useState('')
  const [status, setStatus] = useState('')
  const [paid, setPaid] = useState('')
  const [page, setPage] = useState(1)
  const [data, setData] = useState<PromotionList | null>(null)
  const [loading, setLoading] = useState(true)
  const [loadFailed, setLoadFailed] = useState(false)
  const [actionError, setActionError] = useState<ReturnType<typeof promotionErrorKey> | null>(null)
  const [busyId, setBusyId] = useState<number | null>(null)
  const [hotelToPromote, setHotelToPromote] = useState<HotelSearchRow | null>(null)
  const [toCancel, setToCancel] = useState<AdminPromotion | null>(null)
  const [statsFor, setStatsFor] = useState<AdminPromotion | null>(null)

  // The hotel name filter waits for a pause in typing; the other filters apply at once
  useEffect(() => {
    const timer = setTimeout(() => {
      setName(nameInput.trim())
      setPage(1)
    }, NAME_FILTER_DELAY_MS)
    return () => clearTimeout(timer)
  }, [nameInput])

  // Doubles as the Try Again button
  const load = useCallback(async () => {
    setLoading(true)
    setLoadFailed(false)
    const result = await promotionAdapter.listPromotions({ q: name, status, paid, page })
    if (result.data) setData(result.data)
    else setLoadFailed(true)
    setLoading(false)
  }, [name, status, paid, page])

  useEffect(() => {
    void load()
  }, [load])

  const runAction = async (id: number, action: () => Promise<PromotionResult<AdminPromotion>>) => {
    setBusyId(id)
    setActionError(null)
    const result = await action()
    setBusyId(null)
    if (result.error) {
      setActionError(promotionErrorKey(result.code))
      return
    }
    await load()
  }

  const closeAndReload = () => {
    setHotelToPromote(null)
    setToCancel(null)
    void load()
  }

  const visibility = (promotion: AdminPromotion) => {
    if (promotion.is_shown_now) return t('promoAdmin.shown')
    if (promotion.blocked_reason) return t(`promoAdmin.blocked.${promotion.blocked_reason}`)
    return t('promoAdmin.notShown')
  }

  const rows = data?.results ?? []

  return (
    <div className="admin-promotions">
      <div className="admin-view-header">
        <h2 className="admin-view-title">{t('promoAdmin.title')}</h2>
        <p className="admin-view-subtitle">{t('promoAdmin.subtitle')}</p>
      </div>

      {isSuperAdmin ? (
        <PromotionHotelFinder onPromote={setHotelToPromote} />
      ) : (
        <p className="admin-view-subtitle">{t('promoAdmin.readOnly')}</p>
      )}

      <h3 className="admin-section-title">{t('promoAdmin.listTitle')}</h3>
      <div className="customers-controls">
        <div className="search-bar">
          <label htmlFor="promotion-name-filter" className="search-label">{t('promoAdmin.searchLabel')}</label>
          <input id="promotion-name-filter" type="search" className="search-input" value={nameInput}
            onChange={(e) => setNameInput(e.target.value)} />
        </div>
        <div className="search-bar">
          <label htmlFor="promotion-status-filter" className="search-label">{t('promoAdmin.statusLabel')}</label>
          <select id="promotion-status-filter" className="search-input" value={status}
            onChange={(e) => { setStatus(e.target.value); setPage(1) }}>
            <option value="">{t('promoAdmin.all')}</option>
            {STATUSES.map(value => <option key={value} value={value}>{t(`promoAdmin.status.${value}`)}</option>)}
          </select>
        </div>
        <div className="search-bar">
          <label htmlFor="promotion-paid-filter" className="search-label">{t('promoAdmin.paidLabel')}</label>
          <select id="promotion-paid-filter" className="search-input" value={paid}
            onChange={(e) => { setPaid(e.target.value); setPage(1) }}>
            <option value="">{t('promoAdmin.all')}</option>
            <option value="true">{t('promoAdmin.paid')}</option>
            <option value="false">{t('promoAdmin.unpaid')}</option>
          </select>
        </div>
      </div>

      {actionError && <p className="alert alert-error" role="alert">{t(actionError)}</p>}

      {loadFailed && (
        <div className="alert alert-error" role="alert">
          <p>{t('promoAdmin.loadError')}</p>
          <button type="button" className="btn btn-secondary btn-sm" onClick={() => void load()}>{t('common.tryAgain')}</button>
        </div>
      )}
      {loading && !data && !loadFailed && <p className="loading-state">{t('promoAdmin.loading')}</p>}
      {!loading && !loadFailed && rows.length === 0 && <p className="empty-state">{t('promoAdmin.empty')}</p>}

      {rows.length > 0 && (
        <div className="customers-table-container">
          <table className="customers-table">
            <thead>
              <tr>
                <th scope="col">{t('promoAdmin.col.hotel')}</th>
                <th scope="col">{t('promoAdmin.col.period')}</th>
                <th scope="col">{t('promoAdmin.statusLabel')}</th>
                <th scope="col">{t('promoAdmin.col.priority')}</th>
                <th scope="col">{t('promoAdmin.col.price')}</th>
                <th scope="col">{t('promoAdmin.col.payment')}</th>
                <th scope="col">{t('promoAdmin.col.shown')}</th>
                <th scope="col">{t('promoAdmin.col.views')}</th>
                <th scope="col">{t('promoAdmin.col.clicks')}</th>
                <th scope="col">{t('promoAdmin.col.actions')}</th>
              </tr>
            </thead>
            <tbody>
              {rows.map(promotion => {
                const busy = busyId === promotion.id
                const open = ['scheduled', 'active', 'paused'].includes(promotion.status)
                return (
                  <tr key={promotion.id}>
                    <td>
                      <strong>{promotion.property.name}</strong>
                      <div className="promotion-city">{promotion.property.city}</div>
                    </td>
                    <td>{formatDate(promotion.start_date)} - {formatDate(promotion.end_date)}</td>
                    <td>
                      <span className={`status-badge status-badge--${BADGE[promotion.status]}`}>
                        {t(`promoAdmin.status.${promotion.status}`)}
                      </span>
                    </td>
                    <td>{promotion.priority}</td>
                    <td>
                      {promotion.price_amount
                        ? formatMoney(promotion.price_amount, promotion.price_currency, { minDecimals: 0, maxDecimals: 0 })
                        : '-'}
                    </td>
                    <td>{promotion.paid ? t('promoAdmin.paid') : t('promoAdmin.unpaid')}</td>
                    <td>{visibility(promotion)}</td>
                    <td>{promotion.total_impressions}</td>
                    <td>{promotion.total_clicks}</td>
                    <td>
                      <div className="promotion-actions">
                        <button type="button" className="btn btn-secondary btn-sm" disabled={busy}
                          onClick={() => setStatsFor(promotion)}>{t('promoAdmin.stats')}</button>
                        {isSuperAdmin && open && !promotion.paid && (
                          <button type="button" className="btn btn-primary btn-sm" disabled={busy}
                            onClick={() => runAction(promotion.id, () => promotionAdapter.markPromotionPaid(promotion.id))}>
                            {t('promoAdmin.markPaid')}
                          </button>
                        )}
                        {isSuperAdmin && (promotion.status === 'scheduled' || promotion.status === 'active') && (
                          <button type="button" className="btn btn-secondary btn-sm" disabled={busy}
                            onClick={() => runAction(promotion.id, () => promotionAdapter.pausePromotion(promotion.id))}>
                            {t('promoAdmin.pause')}
                          </button>
                        )}
                        {isSuperAdmin && promotion.status === 'paused' && (
                          <button type="button" className="btn btn-secondary btn-sm" disabled={busy}
                            onClick={() => runAction(promotion.id, () => promotionAdapter.resumePromotion(promotion.id))}>
                            {t('promoAdmin.resume')}
                          </button>
                        )}
                        {isSuperAdmin && open && (
                          <button type="button" className="btn btn-danger btn-sm" disabled={busy}
                            onClick={() => setToCancel(promotion)}>
                            {t('promoAdmin.cancel')}
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}

      {data && data.count > PAGE_SIZE && (
        <StatusPagination page={page} count={data.count} pageSize={PAGE_SIZE}
          hasPrevious={page > 1} hasNext={Boolean(data.next)} onPage={setPage} />
      )}

      {hotelToPromote && (
        <CreatePromotionDialog hotel={hotelToPromote} onCreated={closeAndReload} onClose={() => setHotelToPromote(null)} />
      )}
      {toCancel && (
        <CancelPromotionDialog promotion={toCancel} onCancelled={closeAndReload} onClose={() => setToCancel(null)} />
      )}
      {statsFor && <PromotionStatsDialog promotion={statsFor} onClose={() => setStatsFor(null)} />}
    </div>
  )
}
