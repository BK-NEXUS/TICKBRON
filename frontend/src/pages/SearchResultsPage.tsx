import { useState, useEffect, useMemo } from 'react'
import { SearchX, SlidersHorizontal } from 'lucide-react'
import { useSearchParams } from 'react-router'
import { propertyAdapter, Property, SearchParams, FilterOptions } from '../adapters/propertyAdapter'
import type { PromotedProperty } from '../adapters/promotionAdapter'
import { PromoCarousel } from '../components/PromoCarousel'
import { PropertyCard } from '../components/PropertyCard'
import { SearchFilters } from '../components/SearchFilters'
import { SearchSort } from '../components/SearchSort'
import { ListViewMapView } from '../components/ListViewMapView'
import { PropertiesMapView } from '../components/PropertiesMapView'
import type { MapArea } from '../components/PropertiesMap'
import { areaFromUrl, areaToUrl } from '../utils/searchArea'
import { ShowOnMapCard } from '../components/ShowOnMapCard'
import { SearchForm } from '../components/SearchForm'
import { useI18n } from '../i18n/I18nContext'
import { ErrorState } from '../components/ErrorState'
import { EmptyState } from '../components/EmptyState'
import {
  EMPTY_FILTERS, FilterState, filtersFromUrl, filtersToSearchParams, rememberSearch, writeFiltersToUrl,
} from '../utils/searchFilters'

type LoadingState = 'idle' | 'loading' | 'success' | 'error'

/**
 * Izlew nátiyjelerin kórsetiw ushın SearchResultsPage komponenti
 * Izlew (barar orın, sanalar, mehmanlar), jan panel filterleri hám tártiplew URL de turadı,
 * sol sebepli nátiyjelerdi bólisiw, jańalaw hám artqa túymesi menen qayta ashıw múmkin.
 */
export function SearchResultsPage() {
  const { t, tp, formatDate } = useI18n()
  const [searchParams, setSearchParams] = useSearchParams()
  
  const [loadingState, setLoadingState] = useState<LoadingState>('idle')
  const [properties, setProperties] = useState<Property[]>([])
  // Birinshi juwapqa shekem null; banner tek bar bolǵanda payda boladı hám filterler ózgergende qaladı
  const [promoted, setPromoted] = useState<PromotedProperty[] | null>(null)
  // Tek telefonlarda: filterler paneli túyme artında jıyılǵan
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

  // Mehmanxana betiniń breadcrumb ı dál usı izlewge (sanalar, mehmanlar, filterler, tártip) qaytaradı
  useEffect(() => {
    rememberSearch(queryString)
  }, [queryString])

  // Mehmanxana túrleri, feature sanları hám amenity ler backend ten keledi
  useEffect(() => {
    let cancelled = false
    propertyAdapter.getFilterOptions().then(response => {
      if (!cancelled && response.data) setFilterOptions(response.data)
    }).catch(err => console.error('Failed to load filter options:', err))
    return () => { cancelled = true }
  }, [])

  // URL ózgergen hár waqıtta izlew nátiyjelerin júklew
  useEffect(() => {
    let cancelled = false
    const params = new URLSearchParams(queryString)
    const guests = params.get('guests') ? parseInt(params.get('guests')!, 10) : undefined
    const area = areaFromUrl(params)
    const searchRequest: SearchParams = {
      // Karta aymaǵı átirapındaǵı izlew barar orın tekstin almastıradı
      q: area ? undefined : params.get('destination') || undefined,
      location: area ? undefined : params.get('destination') || undefined,
      ...(area ? { lat: area.lat, lng: area.lng, radius: area.radius } : {}),
      check_in: params.get('check_in') || undefined,
      check_out: params.get('check_out') || undefined,
      min_guests: guests && !isNaN(guests) ? guests : undefined,
      ...filtersToSearchParams(filters, sortBy),
      page: 1,
      // Karta ol kórsete alatuǵın hár mehmanxananı kórsetedi; dizim bir bette qaladı
      page_size: view === 'map' ? 100 : 20,
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
  }, [queryString, filters, sortBy, view])

  const updateUrl = (newFilters: FilterState, newSort: string, replace = false) => {
    setSearchParams(writeFiltersToUrl(new URLSearchParams(queryString), newFilters, newSort), { replace })
  }

  const handleFiltersChange = (newFilters: FilterState) => {
    // Bahanı teriw hár basıwǵa tariyx jazbasın qospawı kerek
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

  const handleSearchArea = (area: MapArea) => {
    setSearchParams(areaToUrl(new URLSearchParams(queryString), area))
  }

  // Kórsetiw ushın izlew konteksin alıw
  const inMapArea = areaFromUrl(searchParams) !== null
  const destination = searchParams.get('destination') || t('search.allDestinations')
  const checkIn = searchParams.get('check_in')
  const checkOut = searchParams.get('check_out')
  const guests = searchParams.get('guests')

  return (
    <div className="search-results-page">
      {/* Izlew forması header i */}
      <div className="search-results-header">
        <div className="container">
          <div className="search-results-search-form">
            <SearchForm />
          </div>
          
          <div className="search-results-context">
            <h1 className="search-results-title">
              {inMapArea ? t('search.mapAreaTitle') : t('search.title', { destination })}
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

      {/* Tiykarǵı mazmun */}
      <div className="search-results-main">
        <div className="container">
          {/* Tólengen banner ler: filterler hám dizim ústinde, tek usı izlewge sáykes mehmanxanalar */}
          <div className="search-results-promo">
            <PromoCarousel items={promoted ?? []} placeName={searchParams.get('destination') || undefined} />
          </div>
          <div className="search-results-layout">
            {/* Filterler jan paneli */}
            <aside
              id="search-results-filters"
              className={`search-results-sidebar${filtersOpen ? ' search-results-sidebar--open' : ''}`}
            >
              <ShowOnMapCard onShow={() => handleViewChange('map')} />
              <SearchFilters
                filters={filters}
                onFiltersChange={handleFiltersChange}
                onClearFilters={handleClearFilters}
                propertyTypes={filterOptions?.property_types ?? []}
                featureCounts={filterOptions ? Object.fromEntries(filterOptions.features.map(f => [f.id, f.count])) : undefined}
                amenities={filterOptions?.amenities ?? []}
              />
            </aside>

            {/* Nátiyjeler aymaǵı */}
            <main className="search-results-content">
              {/* Qural paneli */}
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

              {/* Júklew jaǵdayı */}
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

              {/* Qátelik jaǵdayı */}
              {loadingState === 'error' && (
                <ErrorState
                  title={t('search.errorTitle')}
                  message={error ?? t('search.errorLoad')}
                  onRetry={() => window.location.reload()}
                />
              )}

              {/* Bos jaǵday */}
              {loadingState === 'success' && properties.length === 0 && (
                <EmptyState
                  icon={<SearchX size={40} />}
                  title={t('search.emptyTitle')}
                  message={t('search.emptyText')}
                  ctaText={t('search.clearFilters')}
                  onClick={handleClearFilters}
                />
              )}

              {/* Nátiyjeler toru */}
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
                      <h2 className="search-results-map-title">{t('search.mapTitle')}</h2>
                      <p>{tp('search.mapCount', properties.length)}</p>
                      <PropertiesMapView properties={properties} onSearchArea={handleSearchArea} />
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
