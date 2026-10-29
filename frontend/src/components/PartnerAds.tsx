import { useCallback, useEffect, useState } from 'react'
import { partnerAdapter, type OwnerPromotion } from '../adapters/partnerAdapter'
import { useI18n } from '../i18n/I18nContext'

const STATUSES: OwnerPromotion['status'][] = ['scheduled', 'active', 'paused', 'ended', 'cancelled']
const BADGE: Record<OwnerPromotion['status'], string> = {
  active: 'active', scheduled: 'pending', paused: 'pending', ended: 'completed', cancelled: 'cancelled',
}

/** The ads of the owner's hotels in the banner: whether they are shown now, views, clicks, and the open renewal question. */
export function PartnerAds() {
  const { t, formatDate } = useI18n()
  const [status, setStatus] = useState<OwnerPromotion['status'] | ''>('')
  const [ads, setAds] = useState<OwnerPromotion[]>([])
  const [page, setPage] = useState(0)
  const [hasMore, setHasMore] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async (wanted: OwnerPromotion['status'] | '', pageNumber: number) => {
    setLoading(true)
    const result = await partnerAdapter.getPromotions({ status: wanted || undefined, page: pageNumber })
    if (result.data) {
      const { results, hasMore: more } = result.data
      setAds(previous => (pageNumber === 1 ? results : [...previous, ...results]))
      setPage(pageNumber)
      setHasMore(more)
      setError(null)
    } else {
      setError(result.error ?? t('ownerAds.loadError'))
    }
    setLoading(false)
  }, [t])

  useEffect(() => {
    void load(status, 1)
  }, [status, load])

  const visibility = (ad: OwnerPromotion): string | null => {
    if (ad.is_shown_now) return t('ownerAds.shownNow')
    if (ad.blocked_reason) return t(`ownerAds.notShown.${ad.blocked_reason}`)
    if (!ad.paid) return t('ownerAds.notShown.unpaid')
    return null
  }

  return (
    <div className="partner-ads">
      <div className="admin-view-header">
        <h2 className="admin-view-title">{t('ownerAds.title')}</h2>
        <p className="admin-view-subtitle">{t('ownerAds.subtitle')}</p>
      </div>

      <div className="customers-controls">
        <div className="search-bar">
          <label htmlFor="owner-ads-status" className="search-label">{t('ownerAds.statusLabel')}</label>
          <select id="owner-ads-status" className="search-input" value={status}
            onChange={(e) => setStatus(e.target.value as OwnerPromotion['status'] | '')}>
            <option value="">{t('ownerAds.all')}</option>
            {STATUSES.map(value => <option key={value} value={value}>{t(`ownerAds.status.${value}`)}</option>)}
          </select>
        </div>
      </div>

      {error && (
        <div className="alert alert-error" role="alert">
          <p>{error}</p>
          <button type="button" className="btn btn-secondary btn-sm" onClick={() => void load(status, 1)}>{t('common.tryAgain')}</button>
        </div>
      )}
      {loading && ads.length === 0 && !error && <p className="loading-state">{t('ownerAds.loading')}</p>}
      {!loading && !error && ads.length === 0 && <p className="empty-state">{t('ownerAds.empty')}</p>}

      {ads.length > 0 && (
        <ul className="renewal-list">
          {ads.map(ad => {
            const line = visibility(ad)
            return (
              <li key={ad.id} className="renewal-card">
                <div className="renewal-card-head">
                  <div>
                    <strong>{ad.property.name}</strong>
                    <div className="promotion-city">{formatDate(ad.start_date)} - {formatDate(ad.end_date)}</div>
                  </div>
                  <span className={`status-badge status-badge--${BADGE[ad.status]}`}>{t(`ownerAds.status.${ad.status}`)}</span>
                </div>
                {line && <div className="promotion-city">{line}</div>}
                <dl className="renewal-facts renewal-facts--stats">
                  <div><dt>{t('ownerAds.views')}</dt><dd>{ad.impressions}</dd></div>
                  <div><dt>{t('ownerAds.clicks')}</dt><dd>{ad.clicks}</dd></div>
                  <div><dt>{t('ownerAds.clickRate')}</dt><dd>{ad.click_rate === null ? '-' : `${ad.click_rate}%`}</dd></div>
                </dl>
                {ad.renewal && (
                  <p className="alert alert-info">
                    {t('ownerAds.renewal', { date: formatDate(ad.renewal.deadline), count: ad.renewal.days_left })}
                  </p>
                )}
              </li>
            )
          })}
        </ul>
      )}

      {hasMore && (
        <button type="button" className="btn btn-secondary" disabled={loading} onClick={() => void load(status, page + 1)}>
          {t('ownerAds.showMore')}
        </button>
      )}
    </div>
  )
}
