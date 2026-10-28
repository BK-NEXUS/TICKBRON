import { useI18n } from '../i18n/I18nContext'
import { PublicReview, Review } from '../adapters/accountAdapter'
import { StarIcon } from './StarIcon'

interface ReviewCardProps {
  /** The visitor's own review (with its status) or a guest review of the hotel page (with the reviewer's name) */
  review: Review | PublicReview
}

export function ReviewCard({ review }: ReviewCardProps) {
  const { t, formatDate } = useI18n()
  const renderStars = (rating: number) => {
    return (
      <div className="review-card-stars" aria-label={t('reviews.starsOf5', { rating })}>
        {[1, 2, 3, 4, 5].map((star) => (
          <span
            key={star}
            className={`review-card-star ${star <= rating ? 'review-card-star--active' : ''}`}
          >
            <StarIcon />
          </span>
        ))}
      </div>
    )
  }

  const formatReviewDate = (dateString: string) =>
    formatDate(dateString, { year: 'numeric', month: 'long', day: 'numeric' })

  // Only the visitor's own reviews carry a status; a guest review of the hotel page is always approved
  const status = 'status' in review ? review.status : 'approved'
  const reviewer = 'reviewer' in review ? review.reviewer : ''
  const stayMonth = 'stay_month' in review ? review.stay_month : null

  return (
    <article className="review-card">
      {(reviewer || stayMonth) && (
        <p className="review-card-reviewer">
          {reviewer && <strong>{reviewer}</strong>}
          {stayMonth && (
            <span className="review-card-stay">
              {reviewer ? ' · ' : ''}{t('reviews.stayed', { month: formatDate(`${stayMonth}-01`, { year: 'numeric', month: 'long' }) })}
            </span>
          )}
        </p>
      )}
      <div className="review-card-header">
        <div className="review-card-rating">
          {renderStars(review.overall_rating)}
        </div>
        <div className="review-card-date">
          {formatReviewDate(review.created_at)}
        </div>
      </div>

      {review.title && (
        <h4 className="review-card-title">{review.title}</h4>
      )}

      {review.comment && (
        <p className="review-card-comment">{review.comment}</p>
      )}

      {(review.cleanliness_rating || review.location_rating || review.value_rating || 
        review.amenities_rating || review.service_rating) && (
        <div className="review-card-category-ratings">
          <h5 className="review-card-category-title">{t('reviews.categoryTitle')}</h5>
          <div className="review-card-category-grid">
            {review.cleanliness_rating && (
              <div className="review-card-category-item">
                <span className="review-card-category-label">{t('reviews.cleanliness')}</span>
                <span className="review-card-category-value">{review.cleanliness_rating}/5</span>
              </div>
            )}
            {review.location_rating && (
              <div className="review-card-category-item">
                <span className="review-card-category-label">{t('reviews.location')}</span>
                <span className="review-card-category-value">{review.location_rating}/5</span>
              </div>
            )}
            {review.value_rating && (
              <div className="review-card-category-item">
                <span className="review-card-category-label">{t('reviews.value')}</span>
                <span className="review-card-category-value">{review.value_rating}/5</span>
              </div>
            )}
            {review.amenities_rating && (
              <div className="review-card-category-item">
                <span className="review-card-category-label">{t('reviews.amenities')}</span>
                <span className="review-card-category-value">{review.amenities_rating}/5</span>
              </div>
            )}
            {review.service_rating && (
              <div className="review-card-category-item">
                <span className="review-card-category-label">{t('reviews.service')}</span>
                <span className="review-card-category-value">{review.service_rating}/5</span>
              </div>
            )}
          </div>
        </div>
      )}

      {status === 'pending' && (
        <div className="review-card-status review-card-status--pending">
          {t('reviews.pending')}
        </div>
      )}
      {status === 'rejected' && (
        <div className="review-card-status review-card-status--rejected">
          {t('reviews.statusRejected')}
        </div>
      )}
    </article>
  )
}
