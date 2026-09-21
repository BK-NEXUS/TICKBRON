import { Review } from '../adapters/accountAdapter'

interface ReviewCardProps {
  review: Review
}

export function ReviewCard({ review }: ReviewCardProps) {
  const renderStars = (rating: number) => {
    return (
      <div className="review-card-stars" aria-label={`Rating: ${rating} out of 5 stars`}>
        {[1, 2, 3, 4, 5].map((star) => (
          <span
            key={star}
            className={`review-card-star ${star <= rating ? 'review-card-star--active' : ''}`}
          >
            ★
          </span>
        ))}
      </div>
    )
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    })
  }

  return (
    <article className="review-card">
      <div className="review-card-header">
        <div className="review-card-rating">
          {renderStars(review.overall_rating)}
        </div>
        <div className="review-card-date">
          {formatDate(review.created_at)}
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
          <h5 className="review-card-category-title">Category Ratings</h5>
          <div className="review-card-category-grid">
            {review.cleanliness_rating && (
              <div className="review-card-category-item">
                <span className="review-card-category-label">Cleanliness</span>
                <span className="review-card-category-value">{review.cleanliness_rating}/5</span>
              </div>
            )}
            {review.location_rating && (
              <div className="review-card-category-item">
                <span className="review-card-category-label">Location</span>
                <span className="review-card-category-value">{review.location_rating}/5</span>
              </div>
            )}
            {review.value_rating && (
              <div className="review-card-category-item">
                <span className="review-card-category-label">Value</span>
                <span className="review-card-category-value">{review.value_rating}/5</span>
              </div>
            )}
            {review.amenities_rating && (
              <div className="review-card-category-item">
                <span className="review-card-category-label">Amenities</span>
                <span className="review-card-category-value">{review.amenities_rating}/5</span>
              </div>
            )}
            {review.service_rating && (
              <div className="review-card-category-item">
                <span className="review-card-category-label">Service</span>
                <span className="review-card-category-value">{review.service_rating}/5</span>
              </div>
            )}
          </div>
        </div>
      )}

      {review.status === 'pending' && (
        <div className="review-card-status review-card-status--pending">
          Pending Approval
        </div>
      )}
    </article>
  )
}
