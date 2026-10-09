import { useI18n } from '../i18n/I18nContext'
import type { MessageKey } from '../i18n/messages/en'
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
  const { t } = useI18n()
  const { isAuthenticated } = useAuth()
  const [propertyScores, setPropertyScores] = useState<PropertyScores | null>(null)
  const [reviews, setReviews] = useState<Review[]>([])
  const [eligibleProperties, setEligibleProperties] = useState<EligiblePropertiesResponse | null>(null)
  const [showReviewForm, setShowReviewForm] = useState(false)
  const [loading, setLoading] = useState(true)
  // A backend message (text) or one of ours (key), so ours follow the page language
  const [error, setError] = useState<{ text: string } | { key: MessageKey } | null>(null)

  useEffect(() => {
    const loadReviewsData = async () => {
      setLoading(true)
      setError(null)

      try {
        // Load property scores
        const scoresResponse = await accountAdapter.getPropertyScores(propertyId)
        if (scoresResponse.error) {
          setError({ text: scoresResponse.error })
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
        setError({ key: 'reviews.errorLoad' })
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
        setError({ key: 'reviews.errorReload' })
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
          <p>{t('reviews.loading')}</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="reviews-section reviews-section--error">
        <div className="error-state" role="alert" aria-live="assertive">
          <h2>{t('reviews.errorTitle')}</h2>
          <p>{'text' in error ? error.text : t(error.key)}</p>
        </div>
      </div>
    )
  }

  return (
    <section className="reviews-section">
      <h2 className="reviews-section-title">{t('reviews.title')}</h2>

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
            {t('reviews.write')}
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
          <h3 className="reviews-section-list-title">{t('reviews.yours')}</h3>
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
            {t('reviews.loginToWrite')}
          </p>
        </div>
      )}
    </section>
  )
}
