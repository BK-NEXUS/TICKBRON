import { useState, useEffect, useMemo } from 'react'
import { Map as MapIcon, SlidersHorizontal } from 'lucide-react'
import { useSearchParams } from 'react-router-dom'
import { propertyAdapter, Property, SearchParams, FilterOptions } from '../adapters/propertyAdapter'
import type { PromotedProperty } from '../adapters/promotionAdapter'
import { PromoCarousel } from '../components/PromoCarousel'
import { PropertyCard } from '../components/PropertyCard'
import { SearchFilters } from '../components/SearchFilters'
import { SearchSort } from '../components/SearchSort'
import { ListViewMapView } from '../components/ListViewMapView'
import { SearchForm } from '../components/SearchForm'
import { useI18n } from '../i18n/I18nContext'
import {
  EMPTY_FILTERS, FilterState, filtersFromUrl, filtersToSearchParams, rememberSearch, writeFiltersToUrl,
} from '../utils/searchFilters'

type LoadingState = 'idle' | 'loading' | 'success' | 'error'

/**
 * SearchResultsPage component for displaying search results
 * The search (destination, dates, guests), sidebar filters and sort all live in the URL,
 * so results can be shared, refreshed and reached again with the back button.
 */
export function SearchResultsPage() {
  const { t, tp, formatDate } = useI18n()
  const [searchParams, setSearchParams] = useSearchParams()
  
  const [loadingState, setLoadingState] = useState<LoadingState>('idle')
  const [properties, setProperties] = useState<Property[]>([])
  // null until the first response; the banner appears only when there is one, and stays while filters change
  const [promoted, setPromoted] = useState<PromotedProperty[] | null>(null)
  // Phones only: the filters panel is collapsed behind a button
  const [filtersOpen, setFiltersOpen] = useState(false)
  const [filterOptions, setFilterOptions] = useState<FilterOptions | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [view, setView] = useState<'list' | 'map'>('list')
  const [totalCount, setTotalCount] = useState(0)

  const queryString = searchParams.toString()
  const { filters, sort: sortBy } = useMemo(
    () => filtersFromUrl(new URLSearchParams(queryString)),
    [queryString]
  )

  // The property page's breadcrumb leads back to this exact search (dates, guests, filters, sort)
  useEffect(() => {
    rememberSearch(queryString)
  }, [queryString])

  // Property types, feature counts and amenities come from the backend
  useEffect(() => {
    let cancelled = false
    propertyAdapter.getFilterOptions().then(response => {
      if (!cancelled && response.data) setFilterOptions(response.data)
    }).catch(err => console.error('Failed to load filter options:', err))
    return () => { cancelled = true }
  }, [])

  // Load search results whenever the URL changes
  useEffect(() => {
    let cancelled = false
    const params = new URLSearchParams(queryString)
    const guests = params.get('guests') ? parseInt(params.get('guests')!, 10) : undefined
    const searchRequest: SearchParams = {
      q: params.get('destination') || undefined,
      location: params.get('destination') || undefined,
      check_in: params.get('check_in') || undefined,
      check_out: params.get('check_out') || undefined,
      min_guests: guests && !isNaN(guests) ? guests : undefined,
      ...filtersToSearchParams(filters, sortBy),
      page: 1,
      page_size: 20,
    }

    const loadSearchResults = async () => {
      setLoadingState('loading')
      setError(null)
      
      try {
        const response = await propertyAdapter.searchProperties(searchRequest)
        if (cancelled) return
        
        if (response.error) {
          setError(response.error)
          setPromoted([])
          setLoadingState('error')
        } else if (response.data) {
          setProperties(response.data.results)
          setPromoted(response.data.promoted ?? [])
          setTotalCount(response.data.count)
          setLoadingState('success')
        }
      } catch (err) {
        if (cancelled) return
        console.error('Failed to load search results:', err)
        setError(null)
        setPromoted([])
        setLoadingState('error')
      }
    }

    loadSearchResults()
    return () => { cancelled = true }
  }, [queryString, filters, sortBy])

  const updateUrl = (newFilters: FilterState, newSort: string, replace = false) => {
    setSearchParams(writeFiltersToUrl(new URLSearchParams(queryString), newFilters, newSort), { replace })
  }

  const handleFiltersChange = (newFilters: FilterState) => {
    // Typing a price should not add a history entry per keystroke
    const onlyPriceChanged =
      newFilters.property_type === filters.property_type &&
      newFilters.min_rating === filters.min_rating &&
      newFilters.features.join() === filters.features.join() &&
      newFilters.amenities.join() === filters.amenities.join()
    updateUrl(newFilters, sortBy, onlyPriceChanged)
  }

  const handleClearFilters = () => {
    updateUrl(EMPTY_FILTERS, sortBy)
  }

  const handleSortChange = (newSortBy: string) => {
    updateUrl(filters, newSortBy)
  }

  const handleViewChange = (newView: 'list' | 'map') => {
    setView(newView)
  }

  // Get search context for display
  const destination = searchParams.get('destination') || t('search.allDestinations')
  const checkIn = searchParams.get('check_in')
  const checkOut = searchParams.get('check_out')
  const guests = searchParams.get('guests')

  return (
    <div className="search-results-page">
      {/* Search Form Header */}
      <div className="search-results-header">
        <div className="container">
          <div className="search-results-search-form">
            <SearchForm />
          </div>
          
          <div className="search-results-context">
            <h1 className="search-results-title">
              {t('search.title', { destination })}
            </h1>
            <div className="search-results-meta">
              {(checkIn || checkOut || guests) && (
                <div className="search-results-dates">
                  {checkIn && <span>{formatDate(checkIn)}</span>}
                  {checkIn && checkOut && <span> → </span>}
                  {checkOut && <span>{formatDate(checkOut)}</span>}
                  {guests && <span> • {tp('search.guests', Number(guests))}</span>}
                </div>
              )}
              <div className="search-results-count">
                {loadingState === 'success' && (
                  <span>{tp('search.found', totalCount)}</span>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="search-results-main">
        <div className="container">
          {/* Paid banners: above the filters and the list, only hotels that match this search */}
          <div className="search-results-promo">
            <PromoCarousel items={promoted ?? []} />
          </div>
          <div className="search-results-layout">
            {/* Filters Sidebar */}
            <aside
              id="search-results-filters"
              className={`search-results-sidebar${filtersOpen ? ' search-results-sidebar--open' : ''}`}
            >
              <SearchFilters
                filters={filters}
                onFiltersChange={handleFiltersChange}
                onClearFilters={handleClearFilters}
                propertyTypes={filterOptions?.property_types ?? []}
                featureCounts={filterOptions ? Object.fromEntries(filterOptions.features.map(f => [f.id, f.count])) : undefined}
                amenities={filterOptions?.amenities ?? []}
              />
            </aside>

            {/* Results Area */}
            <main className="search-results-content">
              {/* Toolbar */}
              <div className="search-results-toolbar">
                <button
                  type="button"
                  className="btn btn-secondary btn-sm search-results-filters-toggle"
                  aria-expanded={filtersOpen}
                  aria-controls="search-results-filters"
                  onClick={() => setFiltersOpen(open => !open)}
                >
                  <SlidersHorizontal size={16} aria-hidden="true" /> {filtersOpen ? t('search.hideFilters') : t('search.showFilters')}
                </button>
                <SearchSort sortBy={sortBy} onSortChange={handleSortChange} />
                <ListViewMapView view={view} onViewChange={handleViewChange} />
              </div>

              {/* Loading State */}
              {loadingState === 'loading' && (
                <div className="search-results-loading" role="status" aria-live="polite">
                  <div className="search-results-loading-spinner" aria-hidden="true"></div>
                  <p>{t('search.loading')}</p>
                  <div className="search-results-grid search-results-skeletons" aria-hidden="true">
                    {Array.from({ length: 6 }).map((_, index) => (
                      <div key={index} className="property-card skeleton-card">
                        <div className="skeleton skeleton-image"></div>
                        <div className="skeleton-card-content">
                          <div className="skeleton skeleton-text"></div>
                          <div className="skeleton skeleton-text"></div>
                          <div className="skeleton skeleton-text"></div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Error State */}
              {loadingState === 'error' && (
                <div className="search-results-error" role="alert">
                  <h2>{t('search.errorTitle')}</h2>
                  <p>{error ?? t('search.errorLoad')}</p>
                  <button 
                    className="btn btn-secondary"
                    onClick={() => window.location.reload()}
                  >
                    {t('search.tryAgain')}
                  </button>
                </div>
              )}

              {/* Empty State */}
              {loadingState === 'success' && properties.length === 0 && (
                <div className="search-results-empty" role="status">
                  <h2>{t('search.emptyTitle')}</h2>
                  <p>{t('search.emptyText')}</p>
                  <button 
                    className="btn btn-secondary"
                    onClick={handleClearFilters}
                  >
                    {t('search.clearFilters')}
                  </button>
                </div>
              )}

              {/* Results Grid */}
              {loadingState === 'success' && properties.length > 0 && (
                <>
                  {view === 'list' ? (
                    <div className="search-results-grid">
                      {properties.map(property => (
                        <PropertyCard key={property.id} property={property} />
                      ))}
                    </div>
                  ) : (
                    <div className="search-results-map">
                      <div className="search-results-map-placeholder">
                        <div className="search-results-map-placeholder-content">
                          <span className="search-results-map-placeholder-icon"><MapIcon size={48} /></span>
                          <h2>{t('search.mapTitle')}</h2>
                          <p>{t('search.mapSoon')}</p>
                          <p>{tp('search.mapCount', properties.length)}</p>
                        </div>
                      </div>
                    </div>
                  )}
                </>
              )}
            </main>
          </div>
        </div>
      </div>
    </div>
  )
}
export default SearchResultsPage
