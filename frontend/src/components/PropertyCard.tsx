import { Property } from '../adapters/propertyAdapter'
import { House, MapPin, Wifi, Car, Snowflake, Flame, ArrowUpDown } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { FavoriteButton } from './FavoriteButton'

interface PropertyCardProps {
  property: Property
  onClick?: () => void
}

/**
 * PropertyCard component for displaying property search results
 * Shows property image, name, location, rating, price, and key amenities
 */
export function PropertyCard({ property, onClick }: PropertyCardProps) {
  const navigate = useNavigate()
  const translation = property.translations[0] || { name: 'Unknown Property', description: '' }
  const rating = property.rating || property.average_rating || 0
  const reviewCount = property.review_count || 0

  const handleClick = () => {
    if (onClick) {
      onClick()
    }
    navigate(`/property/${property.id}`)
  }

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
      onClick={handleClick}
      role="button"
      tabIndex={0}
      aria-label={`${translation.name} in ${getLocationString()}`}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault()
          handleClick()
        }
      }}
    >
      <div className="property-card-image">
        {property.primary_photo?.photo ? (
          <img
            className="property-card-photo"
            src={property.primary_photo.photo}
            alt={property.primary_photo.alt_text || translation.name}
            loading="lazy"
          />
        ) : (
          <div className="property-card-image-placeholder" data-testid="property-image-placeholder">
            <House size={56} />
          </div>
        )}
        <FavoriteButton propertyId={property.id} propertyName={translation.name} />
        {rating > 0 && (
          <div className="property-card-rating">
            <span className="property-card-rating-value">★ {rating.toFixed(1)}</span>
            <span className="property-card-reviews">({reviewCount})</span>
          </div>
        )}
      </div>

      <div className="property-card-content">
        <h3 className="property-card-name">{translation.name}</h3>
        <p className="property-card-location">
          <MapPin size={15} /> {getLocationString()}
        </p>
        
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
            <span className="property-card-amenity" title="WiFi">
              <Wifi size={16} />
            </span>
          )}
          {property.has_parking && (
            <span className="property-card-amenity" title="Parking">
              <Car size={16} />
            </span>
          )}
          {property.has_ac && (
            <span className="property-card-amenity" title="Air Conditioning">
              <Snowflake size={16} />
            </span>
          )}
          {property.has_heating && (
            <span className="property-card-amenity" title="Heating">
              <Flame size={16} />
            </span>
          )}
          {property.has_elevator && (
            <span className="property-card-amenity" title="Elevator">
              <ArrowUpDown size={16} />
            </span>
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