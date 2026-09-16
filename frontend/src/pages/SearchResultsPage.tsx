import { useState, useEffect, useCallback } from 'react'
import { useSearchParams } from 'react-router-dom'
import { SearchAdapter, Property, SearchParams, PropertyType } from '../adapters/searchAdapter'
import { PropertyCard } from '../components/PropertyCard'
import { SearchFilters, FilterState } from '../components/SearchFilters'
import { SearchSort } from '../components/SearchSort'
import { ListViewMapView } from '../components/ListViewMapView'
import { SearchForm } from '../components/SearchForm'

type LoadingState = 'idle' | 'loading' | 'success' | 'error'

/**
 * SearchResultsPage component for displaying search results
 * Reads search parameters from URL and displays filtered/sorted property results
 */
export function SearchResultsPage() {
  const [searchParams] = useSearchParams()
  
  const [loadingState, setLoadingState] = useState<LoadingState>('idle')
  const [properties, setProperties] = useState<Property[]>([])
  const [propertyTypes, setPropertyTypes] = useState<PropertyType[]>([])
  const [error, setError] = useState<string | null>(null)
  const [view, setView] = useState<'list' | 'map'>('list')
  const [sortBy, setSortBy] = useState('relevance')
  
  const [filters, setFilters] = useState<FilterState>({
    property_type: undefined,
    min_price: undefined,
    max_price: undefined,
    amenities: [],
  })

  // Get search parameters from URL
  const getSearchParams = useCallback((): SearchParams => {
    return {
      destination: searchParams.get('destination') || undefined,
      check_in: searchParams.get('check_in') || undefined,
      check_out: searchParams.get('check_out') || undefined,
      guests: searchParams.get('guests') ? parseInt(searchParams.get('guests')!, 10) : undefined,
      adults: searchParams.get('adults') ? parseInt(searchParams.get('adults')!, 10) : undefined,
      children: searchParams.get('children') ? parseInt(searchParams.get('children')!, 10) : undefined,
      rooms: searchParams.get('rooms') ? parseInt(searchParams.get('rooms')!, 10) : undefined,
      property_type: filters.property_type,
      min_price: filters.min_price,
      max_price: filters.max_price,
      amenities: filters.amenities,
      sort_by: sortBy,
    }
  }, [searchParams, filters, sortBy])

  // Load property types on mount
  useEffect(() => {
    const loadPropertyTypes = async () => {
      try {
        const types = await SearchAdapter.getPropertyTypes()
        setPropertyTypes(types)
      } catch (err) {
        console.error('Failed to load property types:', err)
      }
    }
    
    loadPropertyTypes()
  }, [])

  // Load search results when search parameters or filters change
  useEffect(() => {
    const loadSearchResults = async () => {
      setLoadingState('loading')
      setError(null)
      
      try {
        const params = getSearchParams()
        const response = await SearchAdapter.searchProperties(params)
        setProperties(response.results)
        setLoadingState('success')
      } catch (err) {
        console.error('Failed to load search results:', err)
        setError('Failed to load search results. Please try again.')
        setLoadingState('error')
      }
    }

    loadSearchResults()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams, filters, sortBy])

  const handleFiltersChange = (newFilters: FilterState) => {
    setFilters(newFilters)
  }

  const handleClearFilters = () => {
    setFilters({
      property_type: undefined,
      min_price: undefined,
      max_price: undefined,
      amenities: [],
    })
  }

  const handleSortChange = (newSortBy: string) => {
    setSortBy(newSortBy)
  }

  const handleViewChange = (newView: 'list' | 'map') => {
    setView(newView)
  }

  const handlePropertyClick = (property: Property) => {
    // TODO: Navigate to property detail page in future checkpoint
    console.log('Property clicked:', property.id)
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
                  <span>{properties.length} properties found</span>
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
                propertyTypes={propertyTypes}
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
                    className="btn btn-primary"
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
                    className="btn btn-primary"
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
                        <PropertyCard
                          key={property.id}
                          property={property}
                          onClick={() => handlePropertyClick(property)}
                        />
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