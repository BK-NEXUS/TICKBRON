import { useCallback, useEffect, useState } from 'react'
import { partnerAdapter, type OwnerReview } from '../adapters/partnerAdapter'
import { useI18n } from '../i18n/I18nContext'

interface PartnerReviewsProps {
  properties: Array<{ id: number; name: string }>
}

/** The approved reviews of the owner's hotels, each with a public answer the owner can write, change or remove. */
export function PartnerReviews({ properties }: PartnerReviewsProps) {
  const { t, formatDate } = useI18n()
  const [propertyId, setPropertyId] = useState<number | undefined>(undefined)
  const [reviews, setReviews] = useState<OwnerReview[]>([])
  const [page, setPage] = useState(0)
  const [hasMore, setHasMore] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  // The text being typed per review, kept until the answer is accepted
  const [drafts, setDrafts] = useState<Record<number, string>>({})
  const [busyId, setBusyId] = useState<number | null>(null)

  const load = useCallback(async (hotel: number | undefined, pageNumber: number) => {
    setLoading(true)
    const result = await partnerAdapter.getReviews({ propertyId: hotel, page: pageNumber })
    if (result.data) {
      const { results, hasMore: more } = result.data
      setReviews(previous => (pageNumber === 1 ? results : [...previous, ...results]))
      setPage(pageNumber)
      setHasMore(more)
      setError(null)
    } else {
      setError(result.error ?? t('ownerReviews.loadError'))
    }
    setLoading(false)
  }, [t])

  useEffect(() => {
    void load(propertyId, 1)
  }, [propertyId, load])

  const replace = (updated: OwnerReview) =>
    setReviews(previous => previous.map(row => (row.id === updated.id ? updated : row)))

  const send = async (review: OwnerReview) => {
    const text = (drafts[review.id] ?? review.owner_reply).trim()
    if (!text) {
      setError(t('ownerReviews.answerFirst'))
      return
    }
    setBusyId(review.id)
    const result = await partnerAdapter.replyToReview(review.id, text)
    setBusyId(null)
    if (result.data) {
      replace(result.data)
      setDrafts(previous => Object.fromEntries(Object.entries(previous).filter(([id]) => Number(id) !== review.id)))
      setError(null)
    } else {
      setError(result.error)
    }
  }

  const remove = async (review: OwnerReview) => {
    setBusyId(review.id)
    const result = await partnerAdapter.deleteReviewReply(review.id)
    setBusyId(null)
    if (result.error) {
      setError(result.error)
      return
    }
    replace({ ...review, owner_reply: '', replied_at: null })
    setError(null)
  }

  return (
    <div className="partner-reviews">
      <div className="admin-view-header">
        <h2 className="admin-view-title">{t('ownerReviews.title')}</h2>
        <p className="admin-view-subtitle">{t('ownerReviews.subtitle')}</p>
      </div>

      {properties.length > 1 && (
        <div className="form-group">
          <label htmlFor="partner-reviews-hotel">{t('ownerReviews.hotel')}</label>
          <select
            id="partner-reviews-hotel"
            className="form-input"
            value={propertyId ?? ''}
            onChange={event => setPropertyId(event.target.value ? Number(event.target.value) : undefined)}
          >
            <option value="">{t('ownerReviews.allHotels')}</option>
            {properties.map(property => <option key={property.id} value={property.id}>{property.name}</option>)}
          </select>
        </div>
      )}

      {error && <div className="alert alert-error" role="alert">{error}</div>}

      {!loading && !error && reviews.length === 0 && <p className="admin-review-empty">{t('ownerReviews.empty')}</p>}

      <ul className="admin-review-list">
        {reviews.map(review => {
          const answered = Boolean(review.owner_reply)
          const draft = drafts[review.id] ?? review.owner_reply
          return (
            <li key={review.id} className="admin-review-row">
              <h3 className="admin-review-hotel">{review.property_name}</h3>
              <p className="admin-review-who">
                {review.reviewer}
                {review.stay_month && ` · ${t('reviews.stayed', { month: formatDate(`${review.stay_month}-01`, { year: 'numeric', month: 'long' }) })}`}
                {` · ${formatDate(review.created_at)}`}
              </p>
              <p className="admin-review-rating">{t('reviewAdmin.rating', { rating: review.overall_rating })}</p>
              {review.title && <p className="admin-review-title">{review.title}</p>}
              {review.comment && <p className="admin-review-comment">{review.comment}</p>}

              <label htmlFor={`reply-${review.id}`}>{t('ownerReviews.answerLabel')}</label>
              <textarea
                id={`reply-${review.id}`}
                className="form-input"
                rows={3}
                maxLength={1000}
                value={draft}
                onChange={event => setDrafts(previous => ({ ...previous, [review.id]: event.target.value }))}
              />
              <div className="admin-review-actions">
                <button type="button" className="btn btn-primary" disabled={busyId === review.id} onClick={() => void send(review)}>
                  {t(answered ? 'ownerReviews.edit' : 'ownerReviews.send')}
                </button>
                {answered && (
                  <button type="button" className="btn btn-secondary" disabled={busyId === review.id} onClick={() => void remove(review)}>
                    {t('ownerReviews.remove')}
                  </button>
                )}
              </div>
            </li>
          )
        })}
      </ul>

      {hasMore && (
        <button type="button" className="btn btn-secondary" disabled={loading} onClick={() => void load(propertyId, page + 1)}>
          {t('ownerReviews.showMore')}
        </button>
      )}
    </div>
  )
}
