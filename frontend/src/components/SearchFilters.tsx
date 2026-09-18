import { useState } from 'react'
import { CoachMark } from './CoachMark'

export interface FilterState {
  property_type?: string
  min_price?: number
  max_price?: number
  amenities: string[]
}

interface SearchFiltersProps {
  filters: FilterState
  onFiltersChange: (filters: FilterState) => void
  onClearFilters: () => void
  propertyTypes: Array<{ id: number; name: string; slug: string }>
}

const AMENITY_OPTIONS = [
  { id: 'wifi', label: 'WiFi', icon: '📶' },
  { id: 'parking', label: 'Parking', icon: '🅿️' },
  { id: 'ac', label: 'Air Conditioning', icon: '❄️' },
  { id: 'heating', label: 'Heating', icon: '🔥' },
  { id: 'elevator', label: 'Elevator', icon: '🛗' },
]

/**
 * SearchFilters component for filtering search results
 * Supports property type, price range, and amenities filtering
 */
export function SearchFilters({ filters, onFiltersChange, onClearFilters, propertyTypes }: SearchFiltersProps) {
  const [isExpanded, setIsExpanded] = useState(false)

  const handlePropertyTypeChange = (propertyType: string) => {
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

  const handleAmenityToggle = (amenity: string) => {
    const updatedAmenities = filters.amenities.includes(amenity)
      ? filters.amenities.filter(a => a !== amenity)
      : [...filters.amenities, amenity]
    
    onFiltersChange({ ...filters, amenities: updatedAmenities })
  }

  const handleClearFilters = () => {
    onClearFilters()
  }

  const hasActiveFilters = 
    filters.property_type || 
    filters.min_price !== undefined || 
    filters.max_price !== undefined || 
    filters.amenities.length > 0

  return (
    <aside className="search-filters">
      <div className="search-filters-header">
        <h2 className="search-filters-title">Filters</h2>
        <div className="search-filters-header-button" style={{ position: 'relative' }}>
          {hasActiveFilters && (
            <>
              <button 
                className="search-filters-clear"
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
                  value={type.slug}
                  checked={filters.property_type === type.slug}
                  onChange={() => handlePropertyTypeChange(type.slug)}
                  className="search-filter-input"
                />
                <span className="search-filter-label">{type.name}</span>
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

        {/* Amenities Filter */}
        <div className="search-filter-section">
          <h3 className="search-filter-section-title">Amenities</h3>
          <div className="search-filter-amenities">
            {AMENITY_OPTIONS.map(amenity => (
              <label key={amenity.id} className="search-filter-amenity">
                <input
                  type="checkbox"
                  checked={filters.amenities.includes(amenity.id)}
                  onChange={() => handleAmenityToggle(amenity.id)}
                  className="search-filter-checkbox"
                  aria-label={amenity.label}
                />
                <span className="search-filter-amenity-icon">{amenity.icon}</span>
                <span className="search-filter-amenity-label">{amenity.label}</span>
              </label>
            ))}
          </div>
        </div>
      </div>

      {/* Mobile Expand/Collapse Button */}
      <button 
        className="search-filters-toggle"
        onClick={() => setIsExpanded(!isExpanded)}
        aria-expanded={isExpanded}
        aria-controls="search-filters-content"
      >
        {isExpanded ? 'Show Less' : 'Show More'}
      </button>
    </aside>
  )
}