import { useState } from 'react'
import { accountAdapter, CreateReviewRequest } from '../adapters/accountAdapter'
import { StarIcon } from './StarIcon'

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
            <StarIcon />
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

    // The backend ties every review to a completed stay (booking)
    if (!bookingId) {
      setError('You can review this property after a completed stay.')
      setIsLoading(false)
      return
    }

    const request: CreateReviewRequest = {
      property: propertyId,
      booking: bookingId,
      overall_rating: overallRating,
    }
    // Category ratings are optional; 0 means "not rated" and is not sent
    if (cleanlinessRating > 0) request.cleanliness_rating = cleanlinessRating
    if (locationRating > 0) request.location_rating = locationRating
    if (valueRating > 0) request.value_rating = valueRating
    if (amenitiesRating > 0) request.amenities_rating = amenitiesRating
    if (serviceRating > 0) request.service_rating = serviceRating
    if (title) request.title = title
    if (comment) request.comment = comment

    const response = await accountAdapter.createReview(request)

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
