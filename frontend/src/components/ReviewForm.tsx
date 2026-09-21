import { useState } from 'react'
import { accountAdapter } from '../adapters/accountAdapter'

interface ReviewFormProps {
  propertyId: number
  bookingId?: number
  onSubmitSuccess?: () => void
  onCancel?: () => void
}

export function ReviewForm({ propertyId, bookingId, onSubmitSuccess, onCancel }: ReviewFormProps) {
  const [overallRating, setOverallRating] = useState(0)
  const [cleanlinessRating, setCleanlinessRating] = useState(0)
  const [locationRating, setLocationRating] = useState(0)
  const [valueRating, setValueRating] = useState(0)
  const [amenitiesRating, setAmenitiesRating] = useState(0)
  const [serviceRating, setServiceRating] = useState(0)
  const [title, setTitle] = useState('')
  const [comment, setComment] = useState('')
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  const RatingInput = ({ label, value, onChange }: { label: string; value: number; onChange: (rating: number) => void }) => (
    <div className="review-form-rating">
      <label className="review-form-rating-label">{label}</label>
      <div className="review-form-stars" role="radiogroup" aria-label={`${label} rating`}>
        {[1, 2, 3, 4, 5].map((star) => (
          <button
            key={star}
            type="button"
            className={`review-form-star ${star <= value ? 'review-form-star--active' : ''}`}
            onClick={() => onChange(star)}
            aria-label={`${label} ${star} stars`}
            aria-pressed={star <= value}
          >
            ★
          </button>
        ))}
      </div>
    </div>
  )

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setIsLoading(true)

    if (overallRating < 1 || overallRating > 5) {
      setError('Overall rating is required')
      setIsLoading(false)
      return
    }

    const category_ratings: Record<string, number> = {}
    if (cleanlinessRating > 0) category_ratings.cleanliness_rating = cleanlinessRating
    if (locationRating > 0) category_ratings.location_rating = locationRating
    if (valueRating > 0) category_ratings.value_rating = valueRating
    if (amenitiesRating > 0) category_ratings.amenities_rating = amenitiesRating
    if (serviceRating > 0) category_ratings.service_rating = serviceRating

    const response = await accountAdapter.createReview({
      property_id: propertyId,
      booking_id: bookingId,
      overall_rating: overallRating,
      category_ratings: Object.keys(category_ratings).length > 0 ? category_ratings : undefined,
      title: title || undefined,
      comment: comment || undefined,
    })

    setIsLoading(false)

    if (response.error) {
      setError(response.error)
    } else {
      if (onSubmitSuccess) {
        onSubmitSuccess()
      }
    }
  }

  return (
    <form className="review-form" onSubmit={handleSubmit}>
      <h3 className="review-form-title">Write a Review</h3>

      {error && (
        <div className="review-form-error" role="alert" aria-live="assertive">
          {error}
        </div>
      )}

      <RatingInput
        label="Overall Rating"
        value={overallRating}
        onChange={setOverallRating}
      />

      <div className="review-form-category-ratings">
        <h4 className="review-form-category-title">Category Ratings (Optional)</h4>
        <RatingInput
          label="Cleanliness"
          value={cleanlinessRating}
          onChange={setCleanlinessRating}
        />
        <RatingInput
          label="Location"
          value={locationRating}
          onChange={setLocationRating}
        />
        <RatingInput
          label="Value"
          value={valueRating}
          onChange={setValueRating}
        />
        <RatingInput
          label="Amenities"
          value={amenitiesRating}
          onChange={setAmenitiesRating}
        />
        <RatingInput
          label="Service"
          value={serviceRating}
          onChange={setServiceRating}
        />
      </div>

      <div className="review-form-field">
        <label htmlFor="review-title" className="review-form-label">
          Title (Optional)
        </label>
        <input
          id="review-title"
          type="text"
          className="review-form-input"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          maxLength={200}
          disabled={isLoading}
        />
      </div>

      <div className="review-form-field">
        <label htmlFor="review-comment" className="review-form-label">
          Comment (Optional)
        </label>
        <textarea
          id="review-comment"
          className="review-form-textarea"
          value={comment}
          onChange={(e) => setComment(e.target.value)}
          rows={4}
          disabled={isLoading}
        />
      </div>

      <div className="review-form-actions">
        <button
          type="submit"
          className="btn btn-primary"
          disabled={isLoading}
        >
          {isLoading ? 'Submitting...' : 'Submit Review'}
        </button>
        {onCancel && (
          <button
            type="button"
            className="btn btn-secondary"
            onClick={onCancel}
            disabled={isLoading}
          >
            Cancel
          </button>
        )}
      </div>
    </form>
  )
}
