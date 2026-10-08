import type { SearchParams } from '../adapters/propertyAdapter'

/**
 * Search sidebar filters and sorting, kept in the results page URL so a search
 * can be shared, refreshed and reached again with the back button.
 * Values match GET /api/v1/properties/search/ (see .ai/API_CONTRACT.md).
 */
export interface FilterState {
  property_type?: number
  min_price?: number
  max_price?: number
  /** Property flags: wifi, parking, ac, heating, elevator (the backend `features` param) */
  features: string[]
  /** Searchable amenity ids */
  amenities: number[]
  min_rating?: number
}

export const EMPTY_FILTERS: FilterState = {
  property_type: undefined,
  min_price: undefined,
  max_price: undefined,
  features: [],
  amenities: [],
  min_rating: undefined,
}

export const FEATURE_OPTIONS = [
  { id: 'wifi', label: 'WiFi' },
  { id: 'parking', label: 'Parking' },
  { id: 'ac', label: 'Air Conditioning' },
  { id: 'heating', label: 'Heating' },
  { id: 'elevator', label: 'Elevator' },
]

export const RATING_OPTIONS = [
  { value: 4.5, label: '4.5+' },
  { value: 4, label: '4+' },
  { value: 3, label: '3+' },
]

export const DEFAULT_SORT = 'relevance'

export const SORT_OPTIONS = [
  { id: 'relevance', label: 'Relevance' },
  { id: 'price_asc', label: 'Price: Low to High' },
  { id: 'price_desc', label: 'Price: High to Low' },
  { id: 'rating', label: 'Rating' },
  { id: 'reviews', label: 'Number of Reviews' },
]

/** URL params owned by the sidebar and the sort select (the search form owns the rest) */
export const FILTER_URL_KEYS = [
  'property_type', 'min_price', 'max_price', 'features', 'amenities', 'min_rating', 'sort',
] as const

const FEATURE_IDS = new Set(FEATURE_OPTIONS.map(f => f.id))
const SORT_IDS = new Set(SORT_OPTIONS.map(s => s.id))

function positiveNumber(value: string | null): number | undefined {
  if (value === null || value.trim() === '') return undefined
  const number = Number(value)
  return Number.isFinite(number) && number >= 0 ? number : undefined
}

function list(value: string | null): string[] {
  return value ? value.split(',').map(v => v.trim()).filter(Boolean) : []
}

export function filtersFromUrl(params: URLSearchParams): { filters: FilterState; sort: string } {
  const propertyType = positiveNumber(params.get('property_type'))
  const sort = params.get('sort')
  return {
    filters: {
      property_type: propertyType !== undefined && Number.isInteger(propertyType) && propertyType > 0 ? propertyType : undefined,
      min_price: positiveNumber(params.get('min_price')),
      max_price: positiveNumber(params.get('max_price')),
      features: list(params.get('features')).filter(f => FEATURE_IDS.has(f)),
      amenities: list(params.get('amenities')).map(Number).filter(id => Number.isInteger(id) && id > 0),
      min_rating: positiveNumber(params.get('min_rating')),
    },
    sort: sort && SORT_IDS.has(sort) ? sort : DEFAULT_SORT,
  }
}

/** A copy of `current` with the filter and sort params replaced (other params are kept) */
export function writeFiltersToUrl(current: URLSearchParams, filters: FilterState, sort: string): URLSearchParams {
  const next = new URLSearchParams(current)
  FILTER_URL_KEYS.forEach(key => next.delete(key))
  if (filters.property_type !== undefined) next.set('property_type', String(filters.property_type))
  if (filters.min_price !== undefined) next.set('min_price', String(filters.min_price))
  if (filters.max_price !== undefined) next.set('max_price', String(filters.max_price))
  if (filters.features.length > 0) next.set('features', filters.features.join(','))
  if (filters.amenities.length > 0) next.set('amenities', filters.amenities.join(','))
  if (filters.min_rating !== undefined) next.set('min_rating', String(filters.min_rating))
  if (sort && sort !== DEFAULT_SORT) next.set('sort', sort)
  return next
}

/** Copy the filter and sort params from one URL to another (a new search keeps the sidebar) */
export function keepFilterParams(from: URLSearchParams, to: URLSearchParams): URLSearchParams {
  FILTER_URL_KEYS.forEach(key => {
    const value = from.get(key)
    if (value !== null) to.set(key, value)
  })
  return to
}

export function filtersToSearchParams(filters: FilterState, sort: string): Partial<SearchParams> {
  return {
    property_type: filters.property_type,
    min_price: filters.min_price,
    max_price: filters.max_price,
    features: filters.features,
    amenities: filters.amenities,
    min_rating: filters.min_rating,
    sort: sort === DEFAULT_SORT ? undefined : sort,
  }
}

export function hasActiveFilters(filters: FilterState): boolean {
  return (
    filters.property_type !== undefined ||
    filters.min_price !== undefined ||
    filters.max_price !== undefined ||
    filters.features.length > 0 ||
    filters.amenities.length > 0 ||
    filters.min_rating !== undefined
  )
}

const LAST_SEARCH_KEY = 'tickbron:lastSearch'

/** Remember the results page query so breadcrumbs can lead back to it with its filters */
export function rememberSearch(queryString: string) {
  try {
    window.sessionStorage.setItem(LAST_SEARCH_KEY, queryString)
  } catch {
    // Storage blocked: breadcrumbs fall back to a plain city search
  }
}

/** The last search for this city (with its dates, guests, filters and sort), else a plain city search */
export function searchUrlForCity(city: string): string {
  try {
    const last = window.sessionStorage.getItem(LAST_SEARCH_KEY)
    if (last !== null) {
      const destination = new URLSearchParams(last).get('destination') ?? ''
      if (destination.trim().toLowerCase() === city.trim().toLowerCase()) return `/search?${last}`
    }
  } catch {
    // Storage blocked
  }
  return `/search?${new URLSearchParams({ destination: city }).toString()}`
}
