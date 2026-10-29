import { useCallback, useEffect, useState } from 'react'
import { useI18n } from '../i18n/I18nContext'
import {
  promotionAdapter, type AdRenewalRow, type PromotionResult, type RenewalList, type RenewalStatus,
} from '../adapters/promotionAdapter'
import { promotionErrorKey } from '../utils/promotionErrors'
import { StatusPagination } from './StatusPagination'

const PAGE_SIZE = 20
const STATUSES: RenewalStatus[] = ['pending', 'renewed', 'declined', 'expired']
const BADGE: Record<RenewalStatus, string> = {
  pending: 'pending', renewed: 'active', declined: 'cancelled', expired: 'cancelled',
}

interface AdminPromotionRenewalsProps {
  /** Only a super-admin may answer; staff can look. The backend enforces it too. */
  isSuperAdmin: boolean
  /** Called after an answer, so the ads list and the region panel read their numbers again */
  onChanged: () => void
}

function mapLink(row: AdRenewalRow): string | null {
  if (row.latitude === null || row.longitude === null) return null
  return `https://www.openstreetmap.org/?mlat=${row.latitude}&mlon=${row.longitude}#map=16/${row.latitude}/${row.longitude}`
}

/** The ads whose month ended: did the hotel pay for the next one? (.ai/PLAN_AD_RENEWAL.md) */
export function AdminPromotionRenewals({ isSuperAdmin, onChanged }: AdminPromotionRenewalsProps) {
  const { t, formatDate, formatMoney } = useI18n()
  const [status, setStatus] = useState<RenewalStatus>('pending')
  const [page, setPage] = useState(1)
  const [data, setData] = useState<RenewalList | null>(null)
  const [loading, setLoading] = useState(true)
  const [loadFailed, setLoadFailed] = useState(false)
  const [actionError, setActionError] = useState<ReturnType<typeof promotionErrorKey> | null>(null)
  const [busyId, setBusyId] = useState<number | null>(null)
  const [askingId, setAskingId] = useState<number | null>(null)

  // Doubles as the Try Again button
  const load = useCallback(async () => {
    setLoading(true)
    setLoadFailed(false)
    const result = await promotionAdapter.listRenewals({ status, page })
    if (result.data) setData(result.data)
    else setLoadFailed(true)
    setLoading(false)
  }, [status, page])

  useEffect(() => {
    void load()
  }, [load])

  const answer = async (id: number, action: () => Promise<PromotionResult<AdRenewalRow>>) => {
    setBusyId(id)
    setActionError(null)
    setAskingId(null)
    const result = await action()
    setBusyId(null)
    if (result.error) setActionError(promotionErrorKey(result.code))
    else onChanged()
    await load()
  }

  const rows = data?.results ?? []

  return (
    <section className="admin-promotion-renewals" aria-labelledby="promo-renewals-title">
      <h3 id="promo-renewals-title" className="admin-section-title">{t('promoRenewals.title')}</h3>
      <p className="admin-view-subtitle">{t('promoRenewals.subtitle')}</p>

      <div className="customers-controls">
        <div className="search-bar">
          <label htmlFor="renewal-status-filter" className="search-label">{t('promoRenewals.statusLabel')}</label>
          <select id="renewal-status-filter" className="search-input" value={status}
            onChange={(e) => { setStatus(e.target.value as RenewalStatus); setPage(1) }}>
            {STATUSES.map(value => <option key={value} value={value}>{t(`promoRenewals.status.${value}`)}</option>)}
          </select>
        </div>
      </div>

      {actionError && <p className="alert alert-error" role="alert">{t(actionError)}</p>}
      {loadFailed && (
        <div className="alert alert-error" role="alert">
          <p>{t('promoRenewals.loadError')}</p>
          <button type="button" className="btn btn-secondary btn-sm" onClick={() => void load()}>{t('common.tryAgain')}</button>
        </div>
      )}
      {loading && !data && !loadFailed && <p className="loading-state">{t('promoRenewals.loading')}</p>}
      {!loading && !loadFailed && rows.length === 0 && <p className="empty-state">{t('promoRenewals.empty')}</p>}

      {rows.length > 0 && (
        <ul className="renewal-list">
          {rows.map(row => {
            const busy = busyId === row.id
            const link = mapLink(row)
            return (
              <li key={row.id} className="renewal-card">
                <div className="renewal-card-head">
                  <div>
                    <strong>{row.hotel_name}</strong>
                    <div className="promotion-city">{row.city}, {row.address}</div>
                  </div>
                  <span className={`status-badge status-badge--${BADGE[row.status]}`}>
                    {t(`promoRenewals.status.${row.status}`)}
                  </span>
                </div>
                <div className="promotion-city">
                  {row.owner_name && <span>{row.owner_name} </span>}
                  {row.owner_phone && <span>{row.owner_phone} </span>}
                  <span>{row.owner_email}</span>
                </div>
                {link && (
                  <a href={link} target="_blank" rel="noopener noreferrer"
                    aria-label={`${t('promoRenewals.openMap')}: ${row.hotel_name}`}>
                    {t('promoRenewals.openMap')}
                  </a>
                )}
                <dl className="renewal-facts">
                  <div>
                    <dt>{t('promoRenewals.col.period')}</dt>
                    <dd>{formatDate(row.start_date)} - {formatDate(row.end_date)}</dd>
                  </div>
                  <div>
                    <dt>{t('promoRenewals.col.price')}</dt>
                    <dd>
                      {row.price_amount
                        ? formatMoney(row.price_amount, row.price_currency, { minDecimals: 0, maxDecimals: 0 })
                        : '-'}
                    </dd>
                  </div>
                  <div>
                    <dt>{t('promoRenewals.col.deadline')}</dt>
                    <dd>
                      {formatDate(row.deadline)}
                      {row.status === 'pending' && (
                        <div className="promotion-city">
                          {row.days_left >= 0 ? t('promoRenewals.daysLeft', { count: row.days_left }) : t('promoRenewals.overdue')}
                        </div>
                      )}
                    </dd>
                  </div>
                </dl>
                {row.decided_via && <div className="promotion-city">{t(`promoRenewals.via.${row.decided_via}`)}</div>}
                {isSuperAdmin && row.status === 'pending' && askingId !== row.id && (
                  <div className="promotion-actions">
                    <button type="button" className="btn btn-primary btn-sm" disabled={busy}
                      aria-label={`${t('promoRenewals.confirm')}: ${row.hotel_name}`}
                      onClick={() => void answer(row.id, () => promotionAdapter.confirmRenewal(row.id))}>
                      {t('promoRenewals.confirm')}
                    </button>
                    <button type="button" className="btn btn-danger btn-sm" disabled={busy}
                      aria-label={`${t('promoRenewals.decline')}: ${row.hotel_name}`}
                      onClick={() => setAskingId(row.id)}>
                      {t('promoRenewals.decline')}
                    </button>
                  </div>
                )}
                {isSuperAdmin && row.status === 'pending' && askingId === row.id && (
                  <div className="promotion-actions" role="group" aria-label={t('promoRenewals.declineQuestion')}>
                    <span>{t('promoRenewals.declineQuestion')}</span>
                    <button type="button" className="btn btn-danger btn-sm" disabled={busy}
                      onClick={() => void answer(row.id, () => promotionAdapter.declineRenewal(row.id))}>
                      {t('promoRenewals.declineYes')}
                    </button>
                    <button type="button" className="btn btn-secondary btn-sm" onClick={() => setAskingId(null)}>
                      {t('promoRenewals.declineNo')}
                    </button>
                  </div>
                )}
              </li>
            )
          })}
        </ul>
      )}

      {data && data.count > PAGE_SIZE && (
        <StatusPagination page={page} count={data.count} pageSize={PAGE_SIZE}
          hasPrevious={page > 1} hasNext={Boolean(data.next)} onPage={setPage} />
      )}
    </section>
  )
}
