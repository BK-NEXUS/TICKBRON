import { useState } from 'react'
import { CoachMark } from './CoachMark'
import { FEATURE_OPTIONS, FilterState, RATING_OPTIONS, hasActiveFilters } from '../utils/searchFilters'

export type { FilterState } from '../utils/searchFilters'

interface SearchFiltersProps {
  filters: FilterState
  onFiltersChange: (filters: FilterState) => void
  onClearFilters: () => void
  /** From GET /properties/filter-options/ */
  propertyTypes: Array<{ id: number; name: string; slug: string; count?: number }>
  /** Property counts per feature, from filter-options (optional) */
  featureCounts?: Record<string, number>
  /** Searchable amenities, from filter-options (optional) */
  amenities?: Array<{ id: number; name: string; icon?: string | null; count?: number }>
}

/**
 * SearchFilters component for filtering search results
 * Supports property type, price range, amenities (features), facilities and guest rating
 */
export function SearchFilters({
  filters, onFiltersChange, onClearFilters, propertyTypes, featureCounts, amenities = [],
}: SearchFiltersProps) {
  const [isExpanded, setIsExpanded] = useState(false)

  const handlePropertyTypeChange = (propertyType: number) => {
    onFiltersChange({
      ...filters,
      property_type: filters.property_type === propertyType ? undefined : propertyType,
    })
  }

  const handleMinPriceChange = (value: string) => {
    const minPrice = value ? parseInt(value, 10) : undefined
    onFiltersChange({ ...filters, min_price: minPrice })
  }

  const handleMaxPriceChange = (value: string) => {
    const maxPrice = value ? parseInt(value, 10) : undefined
    onFiltersChange({ ...filters, max_price: maxPrice })
  }

  const handleFeatureToggle = (feature: string) => {
    const updatedFeatures = filters.features.includes(feature)
      ? filters.features.filter(f => f !== feature)
      : [...filters.features, feature]

    onFiltersChange({ ...filters, features: updatedFeatures })
  }

  const handleAmenityToggle = (amenityId: number) => {
    const updatedAmenities = filters.amenities.includes(amenityId)
      ? filters.amenities.filter(a => a !== amenityId)
      : [...filters.amenities, amenityId]

    onFiltersChange({ ...filters, amenities: updatedAmenities })
  }

  const handleRatingChange = (rating: number) => {
    onFiltersChange({
      ...filters,
      min_rating: filters.min_rating === rating ? undefined : rating,
    })
  }

  const handleClearFilters = () => {
    onClearFilters()
  }

  return (
    <aside className="search-filters">
      <div className="search-filters-header">
        <h2 className="search-filters-title">Filters</h2>
        <div className="search-filters-header-button" style={{ position: 'relative' }}>
          {hasActiveFilters(filters) && (
            <>
              <button
                className="btn btn-ghost btn-sm"
                onClick={handleClearFilters}
                aria-label="Clear all filters"
              >
                Clear All
              </button>
              <CoachMark
                featureId="search-filters-clear"
                title="Clear Filters"
                message="Quickly remove all applied filters to see more results."
                position="bottom"
              />
            </>
          )}
        </div>
      </div>

      <div className={`search-filters-content ${isExpanded ? 'search-filters-content-expanded' : ''}`}>
        {/* Property Type Filter */}
        <div className="search-filter-section">
          <h3 className="search-filter-section-title">Property Type</h3>
          <div className="search-filter-options">
            {propertyTypes.map(type => (
              <label key={type.id} className="search-filter-option">
                <input
                  type="radio"
                  name="property_type"
                  value={type.id}
                  checked={filters.property_type === type.id}
                  onChange={() => handlePropertyTypeChange(type.id)}
                  onClick={() => {
                    // A second click on the checked type clears it (onChange does not fire then)
                    if (filters.property_type === type.id) handlePropertyTypeChange(type.id)
                  }}
                  className="search-filter-input"
                  aria-label={type.name}
                />
                <span className="search-filter-label">{type.name}</span>
                {type.count !== undefined && <span className="search-filter-count">{type.count}</span>}
              </label>
            ))}
          </div>
        </div>

        {/* Price Range Filter */}
        <div className="search-filter-section">
          <h3 className="search-filter-section-title">Price Range</h3>
          <div className="search-filter-price-range">
            <div className="search-filter-price-input">
              <label htmlFor="min_price" className="search-filter-price-label">
                Min Price
              </label>
              <input
                id="min_price"
                type="number"
                min="0"
                placeholder="No minimum"
                value={filters.min_price !== undefined ? filters.min_price : ''}
                onChange={(e) => handleMinPriceChange(e.target.value)}
                className="search-filter-input-field"
                aria-label="Minimum price"
              />
            </div>
            <div className="search-filter-price-input">
              <label htmlFor="max_price" className="search-filter-price-label">
                Max Price
              </label>
              <input
                id="max_price"
                type="number"
                min="0"
                placeholder="No maximum"
                value={filters.max_price !== undefined ? filters.max_price : ''}
                onChange={(e) => handleMaxPriceChange(e.target.value)}
                className="search-filter-input-field"
                aria-label="Maximum price"
              />
            </div>
          </div>
        </div>

        {/* Guest Rating Filter */}
        <div className="search-filter-section">
          <h3 className="search-filter-section-title">Guest Rating</h3>
          <div className="search-filter-options">
            {RATING_OPTIONS.map(option => (
              <label key={option.value} className="search-filter-option">
                <input
                  type="radio"
                  name="min_rating"
                  value={option.value}
                  checked={filters.min_rating === option.value}
                  onChange={() => handleRatingChange(option.value)}
                  onClick={() => {
                    if (filters.min_rating === option.value) handleRatingChange(option.value)
                  }}
                  className="search-filter-input"
                  aria-label={`Rating ${option.label}`}
                />
                <span className="search-filter-label">★ {option.label}</span>
              </label>
            ))}
          </div>
        </div>

        {/* Amenities Filter (property features) */}
        <div className="search-filter-section">
          <h3 className="search-filter-section-title">Amenities</h3>
          <div className="search-filter-amenities">
            {FEATURE_OPTIONS.map(feature => (
              <label key={feature.id} className="search-filter-amenity">
                <input
                  type="checkbox"
                  checked={filters.features.includes(feature.id)}
                  onChange={() => handleFeatureToggle(feature.id)}
                  className="search-filter-checkbox"
                  aria-label={feature.label}
                />
                <span className="search-filter-amenity-icon">{feature.icon}</span>
                <span className="search-filter-amenity-label">{feature.label}</span>
                {featureCounts?.[feature.id] !== undefined && (
                  <span className="search-filter-count">{featureCounts[feature.id]}</span>
                )}
              </label>
            ))}
          </div>
        </div>

        {/* Facilities Filter (searchable amenities from the backend) */}
        {amenities.length > 0 && (
          <div className="search-filter-section">
            <h3 className="search-filter-section-title">Facilities</h3>
            <div className="search-filter-amenities">
              {amenities.map(amenity => (
                <label key={amenity.id} className="search-filter-amenity">
                  <input
                    type="checkbox"
                    checked={filters.amenities.includes(amenity.id)}
                    onChange={() => handleAmenityToggle(amenity.id)}
                    className="search-filter-checkbox"
                    aria-label={amenity.name}
                  />
                  {amenity.icon && <span className="search-filter-amenity-icon">{amenity.icon}</span>}
                  <span className="search-filter-amenity-label">{amenity.name}</span>
                  {amenity.count !== undefined && <span className="search-filter-count">{amenity.count}</span>}
                </label>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Mobile Expand/Collapse Button */}
      <button
        className="btn btn-secondary btn-full"
        onClick={() => setIsExpanded(!isExpanded)}
        aria-expanded={isExpanded}
        aria-controls="search-filters-content"
      >
        {isExpanded ? 'Show Less' : 'Show More'}
      </button>
    </aside>
  )
}
