import { useState, useEffect, useMemo } from 'react'
import { useSearchParams } from 'react-router-dom'
import { propertyAdapter, Property, SearchParams, FilterOptions } from '../adapters/propertyAdapter'
import { PropertyCard } from '../components/PropertyCard'
import { SearchFilters } from '../components/SearchFilters'
import { SearchSort } from '../components/SearchSort'
import { ListViewMapView } from '../components/ListViewMapView'
import { SearchForm } from '../components/SearchForm'
import {
  EMPTY_FILTERS, FilterState, filtersFromUrl, filtersToSearchParams, writeFiltersToUrl,
} from '../utils/searchFilters'

type LoadingState = 'idle' | 'loading' | 'success' | 'error'

/**
 * SearchResultsPage component for displaying search results
 * The search (destination, dates, guests), sidebar filters and sort all live in the URL,
 * so results can be shared, refreshed and reached again with the back button.
 */
export function SearchResultsPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  
  const [loadingState, setLoadingState] = useState<LoadingState>('idle')
  const [properties, setProperties] = useState<Property[]>([])
  const [filterOptions, setFilterOptions] = useState<FilterOptions | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [view, setView] = useState<'list' | 'map'>('list')
  const [totalCount, setTotalCount] = useState(0)

  const queryString = searchParams.toString()
  const { filters, sort: sortBy } = useMemo(
    () => filtersFromUrl(new URLSearchParams(queryString)),
    [queryString]
  )

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
          setLoadingState('error')
        } else if (response.data) {
          setProperties(response.data.results)
          setTotalCount(response.data.count)
          setLoadingState('success')
        }
      } catch (err) {
        if (cancelled) return
        console.error('Failed to load search results:', err)
        setError('Failed to load search results. Please try again.')
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
  const destination = searchParams.get('destination') || 'All destinations'
  const checkIn = searchParams.get('check_in')
  const checkOut = searchParams.get('check_out')
  const guests = searchParams.get('guests')

  const formatDate = (dateString: string) => {
    if (!dateString) return ''
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
  }

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
              Properties in {destination}
            </h1>
            <div className="search-results-meta">
              {(checkIn || checkOut || guests) && (
                <div className="search-results-dates">
                  {checkIn && <span>{formatDate(checkIn)}</span>}
                  {checkIn && checkOut && <span> → </span>}
                  {checkOut && <span>{formatDate(checkOut)}</span>}
                  {guests && <span> • {guests} guest{guests !== '1' ? 's' : ''}</span>}
                </div>
              )}
              <div className="search-results-count">
                {loadingState === 'success' && (
                  <span>{totalCount} properties found</span>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="search-results-main">
        <div className="container">
          <div className="search-results-layout">
            {/* Filters Sidebar */}
            <aside className="search-results-sidebar">
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
                <SearchSort sortBy={sortBy} onSortChange={handleSortChange} />
                <ListViewMapView view={view} onViewChange={handleViewChange} />
              </div>

              {/* Loading State */}
              {loadingState === 'loading' && (
                <div className="search-results-loading" role="status" aria-live="polite">
                  <div className="search-results-loading-spinner" aria-hidden="true"></div>
                  <p>Loading properties...</p>
                </div>
              )}

              {/* Error State */}
              {loadingState === 'error' && (
                <div className="search-results-error" role="alert">
                  <h2>Unable to load properties</h2>
                  <p>{error}</p>
                  <button 
                    className="btn btn-secondary"
                    onClick={() => window.location.reload()}
                  >
                    Try Again
                  </button>
                </div>
              )}

              {/* Empty State */}
              {loadingState === 'success' && properties.length === 0 && (
                <div className="search-results-empty" role="status">
                  <h2>No properties found</h2>
                  <p>Try adjusting your search criteria or filters to find more properties.</p>
                  <button 
                    className="btn btn-secondary"
                    onClick={handleClearFilters}
                  >
                    Clear Filters
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
                          <span className="search-results-map-placeholder-icon">🗺️</span>
                          <h2>Map View</h2>
                          <p>Map integration will be implemented in a future checkpoint.</p>
                          <p>Current view: {properties.length} properties on map</p>
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
