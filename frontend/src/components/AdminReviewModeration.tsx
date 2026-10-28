import { useCallback, useEffect, useState } from 'react'
import { adminAdapter, type AdminReview, type ReviewStatus } from '../adapters/adminAdapter'
import { useI18n } from '../i18n/I18nContext'

const TABS: ReviewStatus[] = ['pending', 'approved', 'rejected']
const TAB_LABEL = { pending: 'reviewAdmin.waiting', approved: 'reviewAdmin.approved', rejected: 'reviewAdmin.rejected' } as const

/** Guest reviews become public only when the staff approves them: waiting, approved and rejected lists. */
export function AdminReviewModeration() {
  const { t, formatDate } = useI18n()
  const [status, setStatus] = useState<ReviewStatus>('pending')
  const [reviews, setReviews] = useState<AdminReview[]>([])
  const [page, setPage] = useState(0)
  const [hasMore, setHasMore] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [busyId, setBusyId] = useState<number | null>(null)

  const load = useCallback(async (wanted: ReviewStatus, pageNumber: number) => {
    setLoading(true)
    const result = await adminAdapter.getReviews(wanted, pageNumber)
    if (result.data) {
      const { results, hasMore: more } = result.data
      setReviews(previous => (pageNumber === 1 ? results : [...previous, ...results]))
      setPage(pageNumber)
      setHasMore(more)
      setError(null)
    } else {
      setError(result.error ?? t('reviewAdmin.loadError'))
    }
    setLoading(false)
  }, [t])

  useEffect(() => {
    void load(status, 1)
  }, [status, load])

  const decide = async (review: AdminReview, decision: 'approve' | 'reject') => {
    setBusyId(review.id)
    const result = await adminAdapter.decideReview(review.id, decision)
    setBusyId(null)
    if (result.error) {
      setError(result.error)
      return
    }
    setError(null)
    setReviews(previous => previous.filter(row => row.id !== review.id))
  }

  return (
    <div className="admin-review-moderation">
      <div className="admin-view-header">
        <h2 className="admin-view-title">{t('reviewAdmin.title')}</h2>
        <p className="admin-view-subtitle">{t('reviewAdmin.subtitle')}</p>
      </div>

      <div role="tablist" aria-label={t('reviewAdmin.title')} className="admin-review-tabs">
        {TABS.map(tab => (
          <button
            key={tab}
            role="tab"
            type="button"
            aria-selected={status === tab}
            className={`btn ${status === tab ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setStatus(tab)}
          >
            {t(TAB_LABEL[tab])}
          </button>
        ))}
      </div>

      {error && <div className="alert alert-error" role="alert">{error}</div>}

      {!loading && !error && reviews.length === 0 && <p className="admin-review-empty">{t('reviewAdmin.empty')}</p>}

      <ul className="admin-review-list">
        {reviews.map(review => (
          <li key={review.id} className="admin-review-row">
            <h3 className="admin-review-hotel">{review.property_name}</h3>
            <p className="admin-review-who">
              {review.reviewer} ({review.reviewer_email})
              {review.stay_month && ` · ${t('reviews.stayed', { month: formatDate(`${review.stay_month}-01`, { year: 'numeric', month: 'long' }) })}`}
              {` · ${formatDate(review.created_at)}`}
            </p>
            <p className="admin-review-rating">{t('reviewAdmin.rating', { rating: review.overall_rating })}</p>
            {review.title && <p className="admin-review-title">{review.title}</p>}
            {review.comment && <p className="admin-review-comment">{review.comment}</p>}
            <div className="admin-review-actions">
              {review.status !== 'approved' && (
                <button type="button" className="btn btn-primary" disabled={busyId === review.id}
                  onClick={() => void decide(review, 'approve')}>
                  {t('reviewAdmin.approve')}
                </button>
              )}
              {review.status !== 'rejected' && (
                <button type="button" className="btn btn-secondary" disabled={busyId === review.id}
                  onClick={() => void decide(review, 'reject')}>
                  {t('reviewAdmin.reject')}
                </button>
              )}
            </div>
          </li>
        ))}
      </ul>

      {hasMore && (
        <button type="button" className="btn btn-secondary" disabled={loading} onClick={() => void load(status, page + 1)}>
          {t('reviewAdmin.showMore')}
        </button>
      )}
    </div>
  )
}
