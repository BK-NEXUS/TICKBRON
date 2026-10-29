import { useI18n } from '../i18n/I18nContext'
import type { PropertyScores } from '../adapters/accountAdapter'
import type { ReviewSummary } from '../adapters/statusAdapter'
import { RatingBreakdown } from './RatingBreakdown'
import { StarIcon } from './StarIcon'

interface OwnerHotelRatingProps {
  hotelId: number
  reviews: ReviewSummary
}

const CATEGORY_KEYS = {
  cleanliness: 'cleanliness_rating', location: 'location_rating', value: 'value_rating',
  amenities: 'amenities_rating', service: 'service_rating',
} as const

/** What the guest-facing rating block shows, built from the owner's numbers (text with one decimal -> numbers) */
function toScores(hotelId: number, reviews: ReviewSummary): PropertyScores {
  const category_scores: PropertyScores['category_scores'] = {}
  for (const [name, key] of Object.entries(CATEGORY_KEYS) as Array<[keyof typeof CATEGORY_KEYS, string]>) {
    const value = reviews.categories[name]
    if (value !== null) category_scores[key as keyof PropertyScores['category_scores']] = Number(value)
  }
  return {
    property_id: hotelId, total_reviews: reviews.count,
    average_rating: reviews.average === null ? null : Number(reviews.average), category_scores,
  }
}

/** Owner Status > one hotel: how guests rate it (the same block guests see), plus how many gave 5, 4, 3, 2 and 1 stars. */
export function OwnerHotelRating({ hotelId, reviews }: OwnerHotelRatingProps) {
  const { t } = useI18n()
  const stars = [5, 4, 3, 2, 1]

  return (
    <section className="owner-hotel-rating" aria-labelledby="owner-hotel-rating-title">
      <h3 id="owner-hotel-rating-title" className="status-chart-title">{t('ownerRating.title')}</h3>
      <p className="status-hint">{t('ownerRating.hint')}</p>
      <RatingBreakdown propertyScores={toScores(hotelId, reviews)} />
      {reviews.count > 0 && (
        <ul className="owner-rating-split">
          {stars.map(star => {
            const count = reviews.distribution[star - 1] ?? 0
            return (
              <li key={star} className="owner-rating-split-row">
                <span className="owner-rating-split-label">{star}<StarIcon /></span>
                <div className="rating-breakdown-bar">
                  <div
                    className="rating-breakdown-bar-fill"
                    role="img"
                    aria-label={t('ownerRating.starRow', { count, total: reviews.count, stars: star })}
                    style={{ width: `${(count / reviews.count) * 100}%` }}
                  />
                </div>
                <span className="owner-rating-split-count">{count}</span>
              </li>
            )
          })}
        </ul>
      )}
    </section>
  )
}
