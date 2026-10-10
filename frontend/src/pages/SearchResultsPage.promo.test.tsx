import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { RouterProvider, createMemoryRouter } from 'react-router-dom'
import { SearchResultsPage } from './SearchResultsPage'
import * as propertyAdapter from '../adapters/propertyAdapter'
import { settle } from '../test/utils'

vi.mock('../adapters/propertyAdapter', () => ({
  propertyAdapter: {
    searchProperties: vi.fn(),
    getFilterOptions: vi.fn(),
  },
}))
vi.mock('../adapters/promotionAdapter', () => ({
  promotionAdapter: { trackClick: vi.fn() },
}))

function hotel(id: number, name: string, extra: Record<string, unknown> = {}) {
  return {
    id,
    owner_id: 1,
    property_type: { id: 1, name: 'Hotel', slug: 'hotel' },
    status: 'active',
    max_guests: 2,
    bedrooms: 1,
    bathrooms: 1,
    address_line1: '1 Street',
    city: 'Samarkand',
    country: 'Uzbekistan',
    base_price: 450000,
    currency: 'UZS',
    has_wifi: true,
    has_parking: false,
    has_ac: false,
    has_heating: false,
    has_elevator: false,
    translations: [{ language: 'en', name, description: '' }],
    policies: [],
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
    ...extra,
  }
}

function response(extra: Record<string, unknown> = {}) {
  return {
    data: {
      count: 2, next: null, previous: null,
      results: [hotel(1, 'Organic One'), hotel(2, 'Organic Two')],
      page: 1, page_size: 20, total_pages: 1,
      ...extra,
    },
    error: null,
  }
}

function renderPage() {
  const router = createMemoryRouter([{ path: '/search', element: <SearchResultsPage /> }], {
    initialEntries: ['/search?destination=Samarkand'],
  })
  render(<RouterProvider router={router} />)
}

describe('SearchResultsPage promoted banner and layout', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(propertyAdapter.propertyAdapter.getFilterOptions).mockResolvedValue({
      data: { property_types: [], features: [], amenities: [], price_range: { min: null, max: null }, sort_options: [] },
      error: null,
    })
  })

  it('shows the promoted banner above the filters and the list', async () => {
    vi.mocked(propertyAdapter.propertyAdapter.searchProperties).mockResolvedValue(
      response({ promoted: [{ ...hotel(9, 'Sponsored Palace'), promotion_id: 90 }] }) as never,
    )
    renderPage()
    await screen.findByText('Organic One')

    const carousel = screen.getByRole('region', { name: 'Featured hotels' })
    expect(carousel).toHaveTextContent('Sponsored Palace')
    expect(carousel).toHaveTextContent('Ad')
    const layout = document.querySelector('.search-results-layout') as HTMLElement
    expect(carousel.compareDocumentPosition(layout) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy()
    expect(layout.contains(carousel)).toBe(false)
  })

  it('shows no banner block when nothing is promoted', async () => {
    vi.mocked(propertyAdapter.propertyAdapter.searchProperties).mockResolvedValue(response({ promoted: [] }) as never)
    renderPage()
    await screen.findByText('Organic One')
    expect(screen.queryByRole('region', { name: 'Featured hotels' })).toBeNull()
    expect(document.querySelector('.promo-carousel')).toBeNull()
  })

  it('works when the backend sends no promoted key at all', async () => {
    vi.mocked(propertyAdapter.propertyAdapter.searchProperties).mockResolvedValue(response() as never)
    renderPage()
    await screen.findByText('Organic One')
    expect(document.querySelector('.promo-carousel')).toBeNull()
  })

  it('does not hold space for a banner while the first results load (a filter clicked meanwhile must not move)', async () => {
    vi.mocked(propertyAdapter.propertyAdapter.searchProperties).mockResolvedValue(response({ promoted: [] }) as never)
    renderPage()
    expect(screen.queryByRole('status', { name: 'Loading featured hotels' })).toBeNull()
    expect(document.querySelector('.promo-carousel')).toBeNull()
    await settle()
    expect(document.querySelector('.promo-carousel')).toBeNull()
  })

  it('hides the banner when the search fails', async () => {
    vi.mocked(propertyAdapter.propertyAdapter.searchProperties).mockResolvedValue({ data: null, error: 'boom' } as never)
    renderPage()
    await screen.findByRole('alert')
    expect(document.querySelector('.promo-carousel')).toBeNull()
  })

  it('keeps the banners while a new search is loading (no jump when filters change)', async () => {
    vi.mocked(propertyAdapter.propertyAdapter.searchProperties).mockResolvedValue(
      response({ promoted: [{ ...hotel(9, 'Sponsored Palace'), promotion_id: 90 }] }) as never,
    )
    renderPage()
    await screen.findByText('Organic One')
    vi.mocked(propertyAdapter.propertyAdapter.searchProperties).mockReturnValue(new Promise(() => {}))
    fireEvent.change(document.getElementById('sort-select') as HTMLElement, { target: { value: 'price_asc' } })
    await waitFor(() => expect(screen.getByText('Loading properties...')).toBeInTheDocument())
    expect(screen.getByRole('region', { name: 'Featured hotels' })).toBeInTheDocument()
  })

  it('lists the hotels in the two column grid', async () => {
    vi.mocked(propertyAdapter.propertyAdapter.searchProperties).mockResolvedValue(response() as never)
    renderPage()
    await screen.findByText('Organic One')
    const grid = document.querySelector('.search-results-grid') as HTMLElement
    expect(grid.querySelectorAll('.property-card')).toHaveLength(2)
    expect(grid).toHaveClass('search-results-grid')
  })

  describe('filters on a phone', () => {
    beforeEach(() => {
      vi.mocked(propertyAdapter.propertyAdapter.searchProperties).mockResolvedValue(response() as never)
    })

    it('has a show filters button that is collapsed by default', async () => {
      renderPage()
      await screen.findByText('Organic One')
      const button = screen.getByRole('button', { name: 'Show filters' })
      expect(button).toHaveAttribute('aria-expanded', 'false')
      expect(document.querySelector('.search-results-sidebar')).not.toHaveClass('search-results-sidebar--open')
    })

    it('opens and closes the filters panel', async () => {
      renderPage()
      await screen.findByText('Organic One')
      fireEvent.click(screen.getByRole('button', { name: 'Show filters' }))
      const hide = screen.getByRole('button', { name: 'Hide filters' })
      expect(hide).toHaveAttribute('aria-expanded', 'true')
      expect(document.querySelector('.search-results-sidebar')).toHaveClass('search-results-sidebar--open')
      fireEvent.click(hide)
      expect(screen.getByRole('button', { name: 'Show filters' })).toBeInTheDocument()
    })

    it('points the button at the filters panel', async () => {
      renderPage()
      await screen.findByText('Organic One')
      const button = screen.getByRole('button', { name: 'Show filters' })
      const panel = document.getElementById(button.getAttribute('aria-controls') as string)
      expect(panel).toBe(document.querySelector('.search-results-sidebar'))
    })
  })
})
