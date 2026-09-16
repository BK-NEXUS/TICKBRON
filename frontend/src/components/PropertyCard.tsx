import { Property } from '../adapters/searchAdapter'

interface PropertyCardProps {
  property: Property
  onClick?: () => void
}

/**
 * PropertyCard component for displaying property search results
 * Shows property image, name, location, rating, price, and key amenities
 */
export function PropertyCard({ property, onClick }: PropertyCardProps) {
  const translation = property.translations[0] || { name: 'Unknown Property', description: '' }
  const rating = property.rating || 0
  const reviewCount = property.review_count || 0

  const formatPrice = (price: number, currency: string) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency,
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(price)
  }

  const getLocationString = () => {
    const parts = [property.city, property.country]
    return parts.filter(Boolean).join(', ')
  }

  return (
    <article 
      className="property-card"
      onClick={onClick}
      role="button"
      tabIndex={0}
      aria-label={`${translation.name} in ${getLocationString()}`}
    >
      <div className="property-card-image">
        <div className="property-card-image-placeholder">
          {property.image_url || '🏠'}
        </div>
        {property.rating && (
          <div className="property-card-rating">
            <span className="property-card-rating-value">★ {rating.toFixed(1)}</span>
            <span className="property-card-reviews">({reviewCount})</span>
          </div>
        )}
      </div>

      <div className="property-card-content">
        <h3 className="property-card-name">{translation.name}</h3>
        <p className="property-card-location">{getLocationString()}</p>
        
        <div className="property-card-details">
          <span className="property-card-detail">
            {property.max_guests} guests
          </span>
          <span className="property-card-detail">
            {property.bedrooms} bedrooms
          </span>
          <span className="property-card-detail">
            {property.bathrooms} bathrooms
          </span>
        </div>

        <div className="property-card-amenities">
          {property.has_wifi && (
            <span className="property-card-amenity" title="WiFi">📶</span>
          )}
          {property.has_parking && (
            <span className="property-card-amenity" title="Parking">🅿️</span>
          )}
          {property.has_ac && (
            <span className="property-card-amenity" title="Air Conditioning">❄️</span>
          )}
          {property.has_heating && (
            <span className="property-card-amenity" title="Heating">🔥</span>
          )}
          {property.has_elevator && (
            <span className="property-card-amenity" title="Elevator">🛗</span>
          )}
        </div>

        <div className="property-card-footer">
          <div className="property-card-price">
            <span className="property-card-price-value">
              {formatPrice(property.base_price, property.currency)}
            </span>
            <span className="property-card-price-period">per night</span>
          </div>
          <button className="btn btn-primary btn-small property-card-cta">
            View Details
          </button>
        </div>
      </div>
    </article>
  )
}