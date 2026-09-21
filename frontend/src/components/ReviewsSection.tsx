import { useState, useEffect } from 'react'
import { accountAdapter, Review, PropertyScores, EligiblePropertiesResponse } from '../adapters/accountAdapter'
import { ReviewForm } from './ReviewForm'
import { ReviewCard } from './ReviewCard'
import { RatingBreakdown } from './RatingBreakdown'
import { useAuth } from '../contexts/AuthContext'

interface ReviewsSectionProps {
  propertyId: number
}

export function ReviewsSection({ propertyId }: ReviewsSectionProps) {
  const { isAuthenticated } = useAuth()
  const [propertyScores, setPropertyScores] = useState<PropertyScores | null>(null)
  const [reviews, setReviews] = useState<Review[]>([])
  const [eligibleProperties, setEligibleProperties] = useState<EligiblePropertiesResponse | null>(null)
  const [showReviewForm, setShowReviewForm] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const loadReviewsData = async () => {
      setLoading(true)
      setError(null)

      try {
        // Load property scores
        const scoresResponse = await accountAdapter.getPropertyScores(propertyId)
        if (scoresResponse.error) {
          setError(scoresResponse.error)
        } else if (scoresResponse.data) {
          setPropertyScores(scoresResponse.data)
        }

        // Load eligible properties if authenticated
        if (isAuthenticated) {
          const eligibleResponse = await accountAdapter.getEligibleProperties()
          if (eligibleResponse.data) {
            setEligibleProperties(eligibleResponse.data)
          }
        }

        // Load user's reviews
        if (isAuthenticated) {
          const reviewsResponse = await accountAdapter.getReviews()
          if (reviewsResponse.data) {
            // Filter reviews for this property
            const propertyReviews = reviewsResponse.data.filter(
              (review) => review.property === propertyId
            )
            setReviews(propertyReviews)
          }
        }

        setLoading(false)
      } catch (err) {
        setError('Failed to load reviews')
        setLoading(false)
      }
    }

    loadReviewsData()
  }, [propertyId, isAuthenticated])

  const handleReviewSubmit = () => {
    setShowReviewForm(false)
    // Reload reviews data
    const loadReviewsData = async () => {
      try {
        const scoresResponse = await accountAdapter.getPropertyScores(propertyId)
        if (scoresResponse.data) {
          setPropertyScores(scoresResponse.data)
        }

        if (isAuthenticated) {
          const reviewsResponse = await accountAdapter.getReviews()
          if (reviewsResponse.data) {
            const propertyReviews = reviewsResponse.data.filter(
              (review) => review.property === propertyId
            )
            setReviews(propertyReviews)
          }

          const eligibleResponse = await accountAdapter.getEligibleProperties()
          if (eligibleResponse.data) {
            setEligibleProperties(eligibleResponse.data)
          }
        }
      } catch (err) {
        setError('Failed to reload reviews')
      }
    }

    loadReviewsData()
  }

  const isEligibleForReview = eligibleProperties?.eligible_properties?.some(
    (eligible) => eligible.property_id === propertyId
  )

  if (loading) {
    return (
      <div className="reviews-section reviews-section--loading">
        <div className="loading-state" role="status" aria-live="polite">
          <div className="loading-spinner"></div>
          <p>Loading reviews...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="reviews-section reviews-section--error">
        <div className="error-state" role="alert" aria-live="assertive">
          <h2>Error Loading Reviews</h2>
          <p>{error}</p>
        </div>
      </div>
    )
  }

  return (
    <section className="reviews-section">
      <h2 className="reviews-section-title">Reviews</h2>

      {propertyScores && (
        <div className="reviews-section-breakdown">
          <RatingBreakdown propertyScores={propertyScores} />
        </div>
      )}

      {isAuthenticated && isEligibleForReview && !showReviewForm && (
        <div className="reviews-section-cta">
          <button
            className="btn btn-primary"
            onClick={() => setShowReviewForm(true)}
          >
            Write a Review
          </button>
        </div>
      )}

      {showReviewForm && isEligibleForReview && (
        <div className="reviews-section-form">
          <ReviewForm
            propertyId={propertyId}
            bookingId={eligibleProperties?.eligible_properties?.find(
              (eligible) => eligible.property_id === propertyId
            )?.booking_id}
            onSubmitSuccess={handleReviewSubmit}
            onCancel={() => setShowReviewForm(false)}
          />
        </div>
      )}

      {reviews.length > 0 && (
        <div className="reviews-section-list">
          <h3 className="reviews-section-list-title">Your Reviews</h3>
          <div className="reviews-section-cards">
            {reviews.map((review) => (
              <ReviewCard key={review.id} review={review} />
            ))}
          </div>
        </div>
      )}

      {!isAuthenticated && (
        <div className="reviews-section-auth-cta">
          <p className="reviews-section-auth-text">
            Log in to write a review for this property
          </p>
        </div>
      )}
    </section>
  )
}
