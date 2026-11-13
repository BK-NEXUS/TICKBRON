import { useI18n } from '../i18n/I18nContext'
import { useState } from 'react'
import { AmenityIcon } from './AmenityIcon'
import { CoachMark } from './CoachMark'
import { FEATURE_OPTIONS, FilterState, RATING_OPTIONS, hasActiveFilters } from '../utils/searchFilters'
import { StarIcon } from './StarIcon'

export type { FilterState } from '../utils/searchFilters'

interface SearchFiltersProps {
  filters: FilterState
  onFiltersChange: (filters: FilterState) => void
  onClearFilters: () => void
  /** GET /properties/filter-options/ ten */
  propertyTypes: Array<{ id: number; name: string; slug: string; count?: number }>
  /** filter-options ten hár feature ushın mehmanxana sanları (ıqtıyarıy) */
  featureCounts?: Record<string, number>
  /** filter-options ten izlenetuǵın amenity ler (ıqtıyarıy) */
  amenities?: Array<{ id: number; name: string; slug?: string; icon?: string | null; count?: number }>
}

/**
 * Izlew nátiyjelerin filterlew ushın SearchFilters komponenti
 * Mehmanxana túri, baha aralıǵı, amenity ler (feature lar), qolaylıqlar hám mehmanlar reytingin qollaydı
 */
export function SearchFilters({
  filters, onFiltersChange, onClearFilters, propertyTypes, featureCounts, amenities = [],
}: SearchFiltersProps) {
  const { t } = useI18n()
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
        <h2 className="search-filters-title">{t('filters.title')}</h2>
        <div className="search-filters-header-button" style={{ position: 'relative' }}>
          {hasActiveFilters(filters) && (
            <>
              <button
                className="btn btn-ghost btn-sm"
                onClick={handleClearFilters}
                aria-label={t('filters.clearAllLabel')}
              >
                {t('filters.clearAll')}
              </button>
              <CoachMark
                featureId="search-filters-clear"
                title={t('filters.coachTitle')}
                message={t('filters.coachText')}
                position="bottom"
              />
            </>
          )}
        </div>
      </div>

      <div className={`search-filters-content ${isExpanded ? 'search-filters-content-expanded' : ''}`}>
        {/* Mehmanxana túri filteri */}
        <div className="search-filter-section">
          <h3 className="search-filter-section-title">{t('filters.propertyType')}</h3>
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
                    // Belgilengen túrge ekinshi klik onı tazalaydı (sonda onChange iske túspeydi)
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

        {/* Baha aralıǵı filteri */}
        <div className="search-filter-section">
          <h3 className="search-filter-section-title">{t('filters.priceRange')}</h3>
          <div className="search-filter-price-range">
            <div className="search-filter-price-input">
              <label htmlFor="min_price" className="search-filter-price-label">
                {t('filters.minPrice')}
              </label>
              <input
                id="min_price"
                type="number"
                min="0"
                placeholder={t('filters.noMin')}
                value={filters.min_price !== undefined ? filters.min_price : ''}
                onChange={(e) => handleMinPriceChange(e.target.value)}
                className="search-filter-input-field"
                aria-label={t('filters.minPriceLabel')}
              />
            </div>
            <div className="search-filter-price-input">
              <label htmlFor="max_price" className="search-filter-price-label">
                {t('filters.maxPrice')}
              </label>
              <input
                id="max_price"
                type="number"
                min="0"
                placeholder={t('filters.noMax')}
                value={filters.max_price !== undefined ? filters.max_price : ''}
                onChange={(e) => handleMaxPriceChange(e.target.value)}
                className="search-filter-input-field"
                aria-label={t('filters.maxPriceLabel')}
              />
            </div>
          </div>
        </div>

        {/* Mehmanlar reytingi filteri */}
        <div className="search-filter-section">
          <h3 className="search-filter-section-title">{t('filters.guestRating')}</h3>
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
                  aria-label={t('filters.ratingLabel', { value: option.label })}
                />
                <span className="search-filter-label"><StarIcon /> {option.label}</span>
              </label>
            ))}
          </div>
        </div>

        {/* Amenity ler filteri (mehmanxana feature ları) */}
        <div className="search-filter-section">
          <h3 className="search-filter-section-title">{t('filters.amenities')}</h3>
          <div className="search-filter-amenities">
            {FEATURE_OPTIONS.map(feature => (
              <label key={feature.id} className="search-filter-amenity">
                <input
                  type="checkbox"
                  checked={filters.features.includes(feature.id)}
                  onChange={() => handleFeatureToggle(feature.id)}
                  className="search-filter-checkbox"
                  aria-label={t(feature.labelKey)}
                />
                <span className="search-filter-amenity-icon"><AmenityIcon slug={feature.id} /></span>
                <span className="search-filter-amenity-label">{t(feature.labelKey)}</span>
                {featureCounts?.[feature.id] !== undefined && (
                  <span className="search-filter-count">{featureCounts[feature.id]}</span>
                )}
              </label>
            ))}
          </div>
        </div>

        {/* Qolaylıqlar filteri (backend ten izlenetuǵın amenity ler) */}
        {amenities.length > 0 && (
          <div className="search-filter-section">
            <h3 className="search-filter-section-title">{t('filters.facilities')}</h3>
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
                  <span className="search-filter-amenity-icon"><AmenityIcon slug={amenity.slug ?? ""} /></span>
                  <span className="search-filter-amenity-label">{amenity.name}</span>
                  {amenity.count !== undefined && <span className="search-filter-count">{amenity.count}</span>}
                </label>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Mobil keńeytiw/jıyıw túymesi */}
      <button
        className="btn btn-secondary btn-full"
        onClick={() => setIsExpanded(!isExpanded)}
        aria-expanded={isExpanded}
        aria-controls="search-filters-content"
      >
        {isExpanded ? t('filters.showLess') : t('filters.showMore')}
      </button>
    </aside>
  )
}
