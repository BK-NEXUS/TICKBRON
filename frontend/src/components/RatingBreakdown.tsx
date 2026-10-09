import { PropertyScores } from '../adapters/accountAdapter'
import { StarIcon } from './StarIcon'

interface RatingBreakdownProps {
  propertyScores: PropertyScores
}

export function RatingBreakdown({ propertyScores }: RatingBreakdownProps) {
  const { average_rating, total_reviews, category_scores } = propertyScores

  if (!average_rating || total_reviews === 0) {
    return (
      <div className="rating-breakdown rating-breakdown--empty">
        <p className="rating-breakdown-empty-text">No reviews yet</p>
      </div>
    )
  }

  const renderProgressBar = (score: number) => {
    const percentage = (score / 5) * 100
    return (
      <div className="rating-breakdown-bar">
        <div 
          className="rating-breakdown-bar-fill" 
          style={{ width: `${percentage}%` }}
          aria-label={`Rating: ${score} out of 5`}
          data-testid="rating-breakdown-bar-fill"
        />
      </div>
    )
  }

  const categories = [
    { key: 'cleanliness_rating', label: 'Cleanliness' },
    { key: 'location_rating', label: 'Location' },
    { key: 'value_rating', label: 'Value' },
    { key: 'amenities_rating', label: 'Amenities' },
    { key: 'service_rating', label: 'Service' },
  ]

  return (
    <div className="rating-breakdown">
      <div className="rating-breakdown-header">
        <div className="rating-breakdown-overall">
          <span className="rating-breakdown-score">{average_rating.toFixed(1)}</span>
          <span className="rating-breakdown-stars">
            {[1, 2, 3, 4, 5].map((star) => (
              <span
                key={star}
                className={`rating-breakdown-star ${star <= Math.round(average_rating) ? 'rating-breakdown-star--active' : ''}`}
              >
                <StarIcon />
              </span>
            ))}
          </span>
        </div>
        <div className="rating-breakdown-reviews">
          {total_reviews} {total_reviews === 1 ? 'review' : 'reviews'}
        </div>
      </div>

      <div className="rating-breakdown-categories">
        {categories.map((category) => {
          const score = category_scores[category.key as keyof typeof category_scores]
          if (score === undefined) return null
          
          return (
            <div key={category.key} className="rating-breakdown-category">
              <div className="rating-breakdown-category-header">
                <span className="rating-breakdown-category-label">{category.label}</span>
                <span className="rating-breakdown-category-score">{score.toFixed(1)}</span>
              </div>
              {renderProgressBar(score)}
            </div>
          )
        })}
      </div>
    </div>
  )
}
