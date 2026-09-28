import { describe, it, expect } from 'vitest'
import {
  EMPTY_FILTERS,
  FILTER_URL_KEYS,
  SORT_OPTIONS,
  filtersFromUrl,
  filtersToSearchParams,
  keepFilterParams,
  writeFiltersToUrl,
} from './searchFilters'

describe('searchFilters', () => {
  it('reads every filter and the sort from the URL', () => {
    const url = new URLSearchParams(
      'destination=Tashkent&property_type=2&min_price=20&max_price=80&features=wifi,parking&amenities=3,7&min_rating=4&sort=price_asc'
    )

    expect(filtersFromUrl(url)).toEqual({
      filters: {
        property_type: 2,
        min_price: 20,
        max_price: 80,
        features: ['wifi', 'parking'],
        amenities: [3, 7],
        min_rating: 4,
      },
      sort: 'price_asc',
    })
  })

  it('ignores missing, broken and unknown values', () => {
    const url = new URLSearchParams('property_type=hotel&min_price=abc&features=wifi,jacuzzi&amenities=x,5&sort=cheapest')

    expect(filtersFromUrl(url)).toEqual({
      filters: { ...EMPTY_FILTERS, features: ['wifi'], amenities: [5] },
      sort: 'relevance',
    })
  })

  it('writes filters to the URL and keeps the search params', () => {
    const current = new URLSearchParams('destination=Tashkent&check_in=2026-10-01&check_out=2026-10-03&guests=2&features=ac')
    const next = writeFiltersToUrl(current, { ...EMPTY_FILTERS, property_type: 2, features: ['wifi'], min_rating: 4.5 }, 'rating')

    expect(next.get('destination')).toBe('Tashkent')
    expect(next.get('check_in')).toBe('2026-10-01')
    expect(next.get('guests')).toBe('2')
    expect(next.get('property_type')).toBe('2')
    expect(next.get('features')).toBe('wifi')
    expect(next.get('min_rating')).toBe('4.5')
    expect(next.get('sort')).toBe('rating')
    // current is not changed
    expect(current.get('features')).toBe('ac')
  })

  it('drops empty filters and the default sort from the URL', () => {
    const current = new URLSearchParams('destination=Tashkent&property_type=2&features=wifi&sort=rating')
    const next = writeFiltersToUrl(current, EMPTY_FILTERS, 'relevance')

    expect(next.toString()).toBe('destination=Tashkent')
  })

  it('round-trips through the URL', () => {
    const filters = { property_type: 3, min_price: 10, max_price: 99, features: ['heating'], amenities: [4], min_rating: 3 }
    const url = writeFiltersToUrl(new URLSearchParams(), filters, 'reviews')

    expect(filtersFromUrl(url)).toEqual({ filters, sort: 'reviews' })
  })

  it('turns filters into backend search params', () => {
    expect(
      filtersToSearchParams({ property_type: 2, min_price: 20, features: ['wifi'], amenities: [3], min_rating: 4 }, 'price_desc')
    ).toEqual({
      property_type: 2,
      min_price: 20,
      max_price: undefined,
      features: ['wifi'],
      amenities: [3],
      min_rating: 4,
      sort: 'price_desc',
    })
    expect(filtersToSearchParams(EMPTY_FILTERS, 'relevance').sort).toBeUndefined()
  })

  it('keepFilterParams copies only the filter and sort params', () => {
    const from = new URLSearchParams('destination=Old&check_in=2026-10-01&features=wifi&sort=rating&min_rating=4')
    const to = new URLSearchParams('destination=New&guests=2')

    keepFilterParams(from, to)

    expect(to.get('destination')).toBe('New')
    expect(to.get('check_in')).toBeNull()
    expect(to.get('features')).toBe('wifi')
    expect(to.get('sort')).toBe('rating')
    expect(to.get('min_rating')).toBe('4')
  })

  it('sort option ids are the ones the backend accepts', () => {
    expect(SORT_OPTIONS.map(o => o.id)).toEqual(['relevance', 'price_asc', 'price_desc', 'rating', 'reviews'])
    expect(FILTER_URL_KEYS).toContain('sort')
  })
})
