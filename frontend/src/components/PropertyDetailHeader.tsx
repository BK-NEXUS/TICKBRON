import { Property } from '../adapters/propertyAdapter'

interface PropertyDetailHeaderProps {
  property: Property
}

/**
 * PropertyDetailHeader component for displaying property header information
 * Shows property name, location, rating, and key details
 */
export function PropertyDetailHeader({ property }: PropertyDetailHeaderProps) {
  const translation = property.translations[0] || { name: 'Property', description: '' }
  const rating = property.rating || 0
  const reviewCount = property.review_count || 0

  const getLocationString = () => {
    const parts = [property.city, property.country]
    return parts.filter(Boolean).join(', ')
  }

  return (
    <header className="property-detail-header">
      <div className="container">
        <div className="property-detail-header-content">
          <div className="property-detail-header-main">
            <h1 className="property-detail-header-title">{translation.name}</h1>
            <p className="property-detail-header-location">{getLocationString()}</p>
            
            {property.rating && (
              <div className="property-detail-header-rating">
                <span className="property-detail-header-rating-value">★ {rating.toFixed(1)}</span>
                <span className="property-detail-header-reviews">({reviewCount} reviews)</span>
              </div>
            )}
          </div>

          <div className="property-detail-header-meta">
            <div className="property-detail-header-meta-item">
              <span className="property-detail-header-meta-label">Property Type</span>
              <span className="property-detail-header-meta-value">{property.property_type.name}</span>
            </div>
            <div className="property-detail-header-meta-item">
              <span className="property-detail-header-meta-label">Guests</span>
              <span className="property-detail-header-meta-value">{property.max_guests}</span>
            </div>
            <div className="property-detail-header-meta-item">
              <span className="property-detail-header-meta-label">Bedrooms</span>
              <span className="property-detail-header-meta-value">{property.bedrooms}</span>
            </div>
            <div className="property-detail-header-meta-item">
              <span className="property-detail-header-meta-label">Bathrooms</span>
              <span className="property-detail-header-meta-value">{property.bathrooms}</span>
            </div>
          </div>
        </div>
      </div>
    </header>
  )
}