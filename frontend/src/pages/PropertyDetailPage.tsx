import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { SearchAdapter, Property } from '../adapters/searchAdapter'
import { PropertyGallery } from '../components/PropertyGallery'
import { PropertyDetailHeader } from '../components/PropertyDetailHeader'
import { PropertyAmenitiesDetail } from '../components/PropertyAmenitiesDetail'
import { PropertyPoliciesDetail } from '../components/PropertyPoliciesDetail'
import { NearbyPlaces } from '../components/NearbyPlaces'
import { DiningRestaurants } from '../components/DiningRestaurants'

/**
 * PropertyDetailPage component for displaying detailed property information
 * Includes gallery, header, and responsive interaction patterns
 */
export function PropertyDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [property, setProperty] = useState<Property | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const loadProperty = async () => {
      if (!id) {
        setError('Property ID is required')
        setLoading(false)
        return
      }

      try {
        const propertyId = parseInt(id, 10)
        if (isNaN(propertyId)) {
          setError('Invalid property ID')
          setLoading(false)
          return
        }

        const data = await SearchAdapter.getPropertyById(propertyId)
        if (!data) {
          setError('Property not found')
          setLoading(false)
          return
        }

        setProperty(data)
        setLoading(false)
      } catch (err) {
        setError('Failed to load property details')
        setLoading(false)
      }
    }

    loadProperty()
  }, [id])

  // SEO metadata
  useEffect(() => {
    if (property) {
      const translation = property.translations[0] || { name: 'Property', description: '' }
      document.title = `${translation.name} | TICKBRON`
      
      // Update meta description
      const metaDescription = document.querySelector('meta[name="description"]')
      if (metaDescription) {
        metaDescription.setAttribute('content', translation.description)
      } else {
        const newMeta = document.createElement('meta')
        newMeta.setAttribute('name', 'description')
        newMeta.setAttribute('content', translation.description)
        document.head.appendChild(newMeta)
      }
    }
  }, [property])

  if (loading) {
    return (
      <div className="property-detail-page property-detail-page--loading">
        <div className="container">
          <div className="loading-state" role="status" aria-live="polite">
            <div className="loading-spinner"></div>
            <p>Loading property details...</p>
          </div>
        </div>
      </div>
    )
  }

  if (error || !property) {
    return (
      <div className="property-detail-page property-detail-page--error">
        <div className="container">
          <div className="error-state" role="alert" aria-live="assertive">
            <h2>Property Not Found</h2>
            <p>{error || 'The property you are looking for does not exist.'}</p>
            <button 
              className="btn btn-primary"
              onClick={() => navigate('/search')}
              aria-label="Return to search results"
            >
              Back to Search
            </button>
          </div>
        </div>
      </div>
    )
  }

  const translation = property.translations[0] || { name: 'Property', description: '' }

  return (
    <div className="property-detail-page">
      <PropertyDetailHeader property={property} />
      <PropertyGallery property={property} />
      
      <div className="container property-detail-content">
        <div className="property-detail-main">
          <section className="property-detail-section">
            <h2 className="property-detail-section-title">About this property</h2>
            <p className="property-detail-description">{translation.description}</p>
          </section>

          <section className="property-detail-section">
            <h2 className="property-detail-section-title">Property details</h2>
            <div className="property-detail-info">
              <div className="property-detail-info-item">
                <span className="property-detail-info-label">Guests</span>
                <span className="property-detail-info-value">{property.max_guests}</span>
              </div>
              <div className="property-detail-info-item">
                <span className="property-detail-info-label">Bedrooms</span>
                <span className="property-detail-info-value">{property.bedrooms}</span>
              </div>
              <div className="property-detail-info-item">
                <span className="property-detail-info-label">Bathrooms</span>
                <span className="property-detail-info-value">{property.bathrooms}</span>
              </div>
              {property.total_area && (
                <div className="property-detail-info-item">
                  <span className="property-detail-info-label">Total Area</span>
                  <span className="property-detail-info-value">{property.total_area} m²</span>
                </div>
              )}
            </div>
          </section>

          <section className="property-detail-section">
            <h2 className="property-detail-section-title">Location</h2>
            <address className="property-detail-address">
              {property.address_line1 && <p>{property.address_line1}</p>}
              {property.address_line2 && <p>{property.address_line2}</p>}
              <p>
                {[property.city, property.state, property.postal_code, property.country]
                  .filter(Boolean)
                  .join(', ')}
              </p>
            </address>
          </section>

          <section className="property-detail-section">
            <PropertyAmenitiesDetail amenities={property.amenities} />
          </section>

          <section className="property-detail-section">
            <PropertyPoliciesDetail policies={property.policies} />
          </section>

          <section className="property-detail-section">
            <NearbyPlaces places={property.nearby_places} />
          </section>

          <section className="property-detail-section">
            <DiningRestaurants restaurants={property.restaurants} />
          </section>
        </div>

        <aside className="property-detail-sidebar">
          <div className="property-detail-booking-card">
            <div className="property-detail-price">
              <span className="property-detail-price-value">
                {new Intl.NumberFormat('en-US', {
                  style: 'currency',
                  currency: property.currency,
                  minimumFractionDigits: 0,
                  maximumFractionDigits: 0,
                }).format(property.base_price)}
              </span>
              <span className="property-detail-price-period">per night</span>
            </div>
            
            {property.rating && (
              <div className="property-detail-rating">
                <span className="property-detail-rating-value">★ {property.rating.toFixed(1)}</span>
                <span className="property-detail-reviews">({property.review_count} reviews)</span>
              </div>
            )}

            <button className="btn btn-primary btn-large property-detail-cta">
              Book Now
            </button>
          </div>
        </aside>
      </div>
    </div>
  )
}