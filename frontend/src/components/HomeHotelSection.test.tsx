import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { HomeHotelSection } from './HomeHotelSection'
import { I18nProvider } from '../i18n/I18nContext'
import { propertyAdapter } from '../adapters/propertyAdapter'
import { settle } from '../test/utils'

vi.mock('../adapters/propertyAdapter', () => ({
  propertyAdapter: { searchProperties: vi.fn() },
}))

const search = vi.mocked(propertyAdapter.searchProperties)

function hotel(id: number, name: string) {
  return {
    id, owner_id: 1, property_type: { id: 1, name: 'Hotel', slug: 'hotel' }, status: 'active', max_guests: 2,
    bedrooms: 1, bathrooms: 1, address_line1: '1 St', city: 'Samarkand', country: 'Uzbekistan', base_price: 450000,
    currency: 'UZS', has_wifi: true, has_parking: false, has_ac: false, has_heating: false, has_elevator: false,
    translations: [{ language: 'en', name, description: '' }], policies: [], average_rating: 9.1, review_count: 12,
    created_at: '2026-01-01T00:00:00Z', updated_at: '2026-01-01T00:00:00Z',
  }
}

function answer(results: ReturnType<typeof hotel>[]) {
  return { data: { count: results.length, next: null, previous: null, results, page: 1, page_size: 8, total_pages: 1 }, error: null }
}

function renderSection() {
  return render(
    <I18nProvider>
      <MemoryRouter>
        <HomeHotelSection title="Top rated hotels" seeAllTo="/search?sort=rating" search={{ sort: 'rating', page_size: 8 }} />
      </MemoryRouter>
    </I18nProvider>,
  )
}

describe('HomeHotelSection', () => {
  beforeEach(() => {
    vi.resetAllMocks()
  })

  it('asks the backend for the hotels of its list', async () => {
    search.mockResolvedValue(answer([hotel(1, 'Alpha')]) as never)
    renderSection()
    await settle()
    expect(search).toHaveBeenCalledWith({ sort: 'rating', page_size: 8 })
    expect(search).toHaveBeenCalledTimes(1)
  })

  it('shows a headed list of hotel cards and a See all link to the search page', async () => {
    search.mockResolvedValue(answer([hotel(1, 'Alpha'), hotel(2, 'Beta')]) as never)
    renderSection()
    const section = await screen.findByRole('region', { name: 'Top rated hotels' })
    expect(section).toHaveTextContent('Alpha')
    expect(section).toHaveTextContent('Beta')
    expect(section.querySelectorAll('.property-card')).toHaveLength(2)
    expect(screen.getByRole('link', { name: 'See all' })).toHaveAttribute('href', '/search?sort=rating')
  })

  it('puts the cards in the home grid', async () => {
    search.mockResolvedValue(answer([hotel(1, 'Alpha')]) as never)
    renderSection()
    await screen.findByText('Alpha')
    expect(document.querySelector('.home-hotel-grid .property-card')).not.toBeNull()
  })

  it('shows a skeleton of cards while loading', async () => {
    search.mockReturnValue(new Promise(() => {}))
    renderSection()
    expect(screen.getByRole('status', { name: 'Loading hotels' })).toBeInTheDocument()
    expect(document.querySelectorAll('.skeleton-card').length).toBeGreaterThan(0)
  })

  it('removes the skeleton when the hotels arrive', async () => {
    search.mockResolvedValue(answer([hotel(1, 'Alpha')]) as never)
    renderSection()
    await screen.findByText('Alpha')
    expect(screen.queryByRole('status', { name: 'Loading hotels' })).toBeNull()
  })

  it('shows nothing at all when there are no hotels', async () => {
    search.mockResolvedValue(answer([]) as never)
    const { container } = renderSection()
    await waitFor(() => expect(screen.queryByRole('status', { name: 'Loading hotels' })).toBeNull())
    expect(container).toBeEmptyDOMElement()
  })

  it('shows nothing when the request fails, so the page stays clean', async () => {
    search.mockResolvedValue({ data: null, error: 'boom' } as never)
    const { container } = renderSection()
    await waitFor(() => expect(screen.queryByRole('status', { name: 'Loading hotels' })).toBeNull())
    expect(container).toBeEmptyDOMElement()
  })

  it('shows nothing when the request is rejected', async () => {
    search.mockRejectedValue(new Error('offline'))
    const { container } = renderSection()
    await waitFor(() => expect(screen.queryByRole('status', { name: 'Loading hotels' })).toBeNull())
    expect(container).toBeEmptyDOMElement()
  })

  it('does not update after the page was left', async () => {
    let resolve: (value: ReturnType<typeof answer>) => void = () => {}
    search.mockReturnValue(new Promise(r => { resolve = r }) as never)
    const view = renderSection()
    view.unmount()
    resolve(answer([hotel(1, 'Late')]))
    await settle()
    expect(screen.queryByText('Late')).toBeNull()
  })
})
