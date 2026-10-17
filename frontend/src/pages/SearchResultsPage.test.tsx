import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { render, screen, waitFor, fireEvent, act, within } from '@testing-library/react'
import { RouterProvider, createMemoryRouter, MemoryRouter, Routes, Route, useLocation, useNavigate } from 'react-router-dom'
import { SearchResultsPage } from './SearchResultsPage'
import * as propertyAdapter from '../adapters/propertyAdapter'
import { settle } from '../test/utils'

// Mock the property adapter
vi.mock('../adapters/propertyAdapter', () => ({
  propertyAdapter: {
    searchProperties: vi.fn(),
    getFilterOptions: vi.fn(),
  },
  Property: {},
  SearchParams: {},
  PropertyType: {},
}))

describe('SearchResultsPage', () => {
  const mockProperties = [
    {
      id: 1,
      owner_id: 1,
      property_type: { id: 1, name: 'Apartment', slug: 'apartment' },
      status: 'active',
      max_guests: 4,
      bedrooms: 2,
      bathrooms: 1,
      address_line1: '123 Rue de Paris',
      city: 'Paris',
      country: 'France',
      base_price: 150,
      currency: 'EUR',
      has_wifi: true,
      has_parking: false,
      has_ac: true,
      has_heating: true,
      has_elevator: true,
      translations: [
        {
          language: 'en',
          name: 'Charming Paris Apartment',
          description: 'Beautiful apartment',
        },
      ],
      policies: [],
      rating: 4.8,
      review_count: 127,
      image_url: 'castle.jpg',
      created_at: '2024-01-15T10:00:00Z',
      updated_at: '2024-01-20T15:30:00Z',
    },
  ]

  const mockFilterOptions = {
    property_types: [
      { id: 7, name: 'Guesthouse', slug: 'guesthouse', count: 3 },
      { id: 9, name: 'Hotel', slug: 'hotel', count: 12 },
    ],
    features: [
      { id: 'wifi', label: 'WiFi', count: 10 },
      { id: 'parking', label: 'Parking', count: 4 },
      { id: 'ac', label: 'Air Conditioning', count: 8 },
      { id: 'heating', label: 'Heating', count: 2 },
      { id: 'elevator', label: 'Elevator', count: 1 },
    ],
    amenities: [],
    price_range: { min: 15, max: 120 },
    sort_options: [],
  }

  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(propertyAdapter.propertyAdapter.getFilterOptions).mockResolvedValue({
      data: mockFilterOptions,
      error: null,
    })
    vi.mocked(propertyAdapter.propertyAdapter.searchProperties).mockResolvedValue({
      data: {
        count: 1,
        next: null,
        previous: null,
        results: mockProperties,
        page: 1,
        page_size: 20,
        total_pages: 1,
      },
      error: null,
    })
  })

  it('renders search results page', async () => {
    const router = createMemoryRouter(
      [
        {
          path: '/search',
          element: <SearchResultsPage />,
        },
      ],
      {
        initialEntries: ['/search?destination=Paris&check_in=2024-01-15&check_out=2024-01-20&guests=2&adults=2&children=0&rooms=1'],
      }
    )

    render(<RouterProvider router={router} />)

    await waitFor(() => {
      expect(screen.getByText('Properties in Paris')).toBeInTheDocument()
    })
  })

  it('displays loading state initially', async () => {
    const router = createMemoryRouter(
      [
        {
          path: '/search',
          element: <SearchResultsPage />,
        },
      ],
      {
        initialEntries: ['/search?destination=Paris'],
      }
    )

    render(<RouterProvider router={router} />)

    expect(screen.getByText('Loading properties...')).toBeInTheDocument()
    // Let the page finish loading inside the test
    await settle()
  })

  it('displays search results after loading', async () => {
    const router = createMemoryRouter(
      [
        {
          path: '/search',
          element: <SearchResultsPage />,
        },
      ],
      {
        initialEntries: ['/search?destination=Paris'],
      }
    )

    render(<RouterProvider router={router} />)

    await waitFor(() => {
      expect(screen.getByText('Charming Paris Apartment')).toBeInTheDocument()
    })
  })

  it('displays empty state when no results found', async () => {
    vi.mocked(propertyAdapter.propertyAdapter.searchProperties).mockResolvedValue({
      data: {
        count: 0,
        next: null,
        previous: null,
        results: [],
        page: 1,
        page_size: 20,
        total_pages: 0,
      },
      error: null,
    })

    const router = createMemoryRouter(
      [
        {
          path: '/search',
          element: <SearchResultsPage />,
        },
      ],
      {
        initialEntries: ['/search?destination=Nowhere'],
      }
    )

    render(<RouterProvider router={router} />)

    await waitFor(() => {
      expect(screen.getByText('No properties found')).toBeInTheDocument()
    })
  })

  it('displays error state when search fails', async () => {
    vi.mocked(propertyAdapter.propertyAdapter.searchProperties).mockResolvedValue({
      data: null,
      error: 'Search failed',
    })

    const router = createMemoryRouter(
      [
        {
          path: '/search',
          element: <SearchResultsPage />,
        },
      ],
      {
        initialEntries: ['/search?destination=Paris'],
      }
    )

    render(<RouterProvider router={router} />)

    await waitFor(() => {
      expect(screen.getByText('Unable to load properties')).toBeInTheDocument()
    })
  })

  it('displays search context information', async () => {
    const router = createMemoryRouter(
      [
        {
          path: '/search',
          element: <SearchResultsPage />,
        },
      ],
      {
        initialEntries: ['/search?destination=Paris&check_in=2024-01-15&check_out=2024-01-20&guests=2'],
      }
    )

    render(<RouterProvider router={router} />)

    await waitFor(() => {
      expect(screen.getByText('Properties in Paris')).toBeInTheDocument()
      expect(screen.getByText(/Jan 15/)).toBeInTheDocument()
      expect(screen.getByText(/Jan 20/)).toBeInTheDocument()
      expect(screen.getByText(/2 guests/)).toBeInTheDocument()
    })
  })

  it('renders filter sidebar', async () => {
    const router = createMemoryRouter(
      [
        {
          path: '/search',
          element: <SearchResultsPage />,
        },
      ],
      {
        initialEntries: ['/search?destination=Paris'],
      }
    )

    render(<RouterProvider router={router} />)

    await waitFor(() => {
      expect(screen.getByText('Filters')).toBeInTheDocument()
    })
  })

  it('renders sort options', async () => {
    const router = createMemoryRouter(
      [
        {
          path: '/search',
          element: <SearchResultsPage />,
        },
      ],
      {
        initialEntries: ['/search?destination=Paris'],
      }
    )

    render(<RouterProvider router={router} />)

    await waitFor(() => {
      expect(screen.getByText('Sort by:')).toBeInTheDocument()
    })
  })

  it('renders list/map view toggle', async () => {
    const router = createMemoryRouter(
      [
        {
          path: '/search',
          element: <SearchResultsPage />,
        },
      ],
      {
        initialEntries: ['/search?destination=Paris'],
      }
    )

    render(<RouterProvider router={router} />)

    await waitFor(() => {
      expect(screen.getByLabelText('List view')).toBeInTheDocument()
      expect(screen.getByLabelText('Map view')).toBeInTheDocument()
    })
  })

  it('displays map placeholder when map view is selected', async () => {
    const router = createMemoryRouter(
      [
        {
          path: '/search',
          element: <SearchResultsPage />,
        },
      ],
      {
        initialEntries: ['/search?destination=Paris'],
      }
    )

    render(<RouterProvider router={router} />)

    await waitFor(() => {
      expect(screen.getByLabelText('List view')).toBeInTheDocument()
    })

    const mapButton = screen.getByLabelText('Map view')
    fireEvent.click(mapButton)

    await waitFor(() => {
      expect(screen.getByText('Map View')).toBeInTheDocument()
    })
  })

  describe('map', () => {
    const located = [{ ...mockProperties[0], latitude: '48.856614', longitude: '2.352222' }]

    // jsdom has no layout: give the map a size, so the pins are placed as in a browser
    beforeEach(() => {
      Object.defineProperty(HTMLElement.prototype, 'clientWidth', { configurable: true, get: () => 800 })
      Object.defineProperty(HTMLElement.prototype, 'clientHeight', { configurable: true, get: () => 500 })
    })

    afterEach(() => {
      delete (HTMLElement.prototype as unknown as Record<string, unknown>).clientWidth
      delete (HTMLElement.prototype as unknown as Record<string, unknown>).clientHeight
    })

    const renderSearch = async () => {
      vi.mocked(propertyAdapter.propertyAdapter.searchProperties).mockResolvedValue({
        data: { count: 1, next: null, previous: null, results: located, page: 1, page_size: 20, total_pages: 1 },
        error: null,
      })
      const router = createMemoryRouter([{ path: '/search', element: <SearchResultsPage /> }], { initialEntries: ['/search?destination=Paris'] })
      render(<RouterProvider router={router} />)
      await screen.findByLabelText('List view')
    }

    it('the map view puts the results on the map as price pins', async () => {
      await renderSearch()
      fireEvent.click(screen.getByLabelText('Map view'))
      expect(await screen.findByRole('region', { name: 'Map of properties' })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /Charming Paris Apartment, €150/ })).toBeInTheDocument()
    })

    it('a card above the filters opens the map view', async () => {
      await renderSearch()
      const filters = document.getElementById('search-results-filters') as HTMLElement
      fireEvent.click(within(filters).getByRole('button', { name: 'Show on map' }))
      expect(await screen.findByRole('region', { name: 'Map of properties' })).toBeInTheDocument()
    })

    it('a search around a point sends the centre and radius, and not the destination text', async () => {
      vi.mocked(propertyAdapter.propertyAdapter.searchProperties).mockResolvedValue({
        data: { count: 1, next: null, previous: null, results: located, page: 1, page_size: 20, total_pages: 1 },
        error: null,
      })
      const router = createMemoryRouter([{ path: '/search', element: <SearchResultsPage /> }], {
        initialEntries: ['/search?lat=41.3&lng=69.2&radius=12'],
      })
      render(<RouterProvider router={router} />)
      await screen.findByText('Properties in the map area')
      const request = vi.mocked(propertyAdapter.propertyAdapter.searchProperties).mock.calls.at(-1)![0]
      expect(request).toMatchObject({ lat: 41.3, lng: 69.2, radius: 12 })
      expect(request.location).toBeUndefined()
      expect(request.q).toBeUndefined()
    })

    it('ignores a point in the URL that is not a number or is out of range', async () => {
      const router = createMemoryRouter([{ path: '/search', element: <SearchResultsPage /> }], {
        initialEntries: ['/search?destination=Paris&lat=abc&lng=500&radius=0'],
      })
      render(<RouterProvider router={router} />)
      await screen.findByLabelText('List view')
      const request = vi.mocked(propertyAdapter.propertyAdapter.searchProperties).mock.calls.at(-1)![0]
      expect(request.lat).toBeUndefined()
      expect(request.lng).toBeUndefined()
      expect(request.radius).toBeUndefined()
      expect(request.location).toBe('Paris')
    })

    it('asks for more results on the map (up to 100) than in the list (20)', async () => {
      await renderSearch()
      const lastPageSize = () => vi.mocked(propertyAdapter.propertyAdapter.searchProperties).mock.calls.at(-1)![0].page_size
      expect(lastPageSize()).toBe(20)
      fireEvent.click(screen.getByLabelText('Map view'))
      await waitFor(() => expect(lastPageSize()).toBe(100))
    })

    it('Search this area searches the visible part of the map instead of the destination', async () => {
      await renderSearch()
      fireEvent.click(screen.getByLabelText('Map view'))
      await screen.findByRole('region', { name: 'Map of properties' })
      fireEvent.click(document.querySelector('.leaflet-control-zoom-in') as HTMLElement)
      fireEvent.click(await screen.findByRole('button', { name: 'Search this area' }))
      await screen.findByText('Properties in the map area')
      const request = vi.mocked(propertyAdapter.propertyAdapter.searchProperties).mock.calls.at(-1)![0]
      expect(request.lat).toBeCloseTo(48.86, 0)
      expect(request.lng).toBeCloseTo(2.35, 0)
      expect(request.radius).toBeGreaterThanOrEqual(1)
      expect(request.location).toBeUndefined()
    })

    it('back to the list view brings the cards back', async () => {
      await renderSearch()
      fireEvent.click(screen.getByLabelText('Map view'))
      await screen.findByRole('region', { name: 'Map of properties' })
      fireEvent.click(screen.getByLabelText('List view'))
      expect(await screen.findByText('Charming Paris Apartment')).toBeInTheDocument()
      expect(screen.queryByRole('region', { name: 'Map of properties' })).toBeNull()
    })
  })

  it('shows property count when results are loaded', async () => {
    const router = createMemoryRouter(
      [
        {
          path: '/search',
          element: <SearchResultsPage />,
        },
      ],
      {
        initialEntries: ['/search?destination=Paris'],
      }
    )

    render(<RouterProvider router={router} />)

    await waitFor(() => {
      expect(screen.getByText('1 property found')).toBeInTheDocument()
    })
  })

  it('calls search adapter with correct parameters', async () => {
    const router = createMemoryRouter(
      [
        {
          path: '/search',
          element: <SearchResultsPage />,
        },
      ],
      {
        initialEntries: ['/search?destination=Paris&guests=2'],
      }
    )

    render(<RouterProvider router={router} />)

    await waitFor(() => {
      expect(propertyAdapter.propertyAdapter.searchProperties).toHaveBeenCalledWith(
        expect.objectContaining({
          q: 'Paris',
          location: 'Paris',
          min_guests: 2,
        })
      )
    })
  })

  describe('filters and sort live in the URL', () => {
    // MemoryRouter + a probe: a data router navigation builds a Request whose AbortSignal jsdom rejects
    const router = { state: { location: { search: '' } }, navigate: async (delta: number) => { void delta } }
    const Probe = () => {
      const location = useLocation()
      const navigate = useNavigate()
      router.state.location.search = location.search
      router.navigate = async (delta: number) => { navigate(delta) }
      return null
    }
    const renderAt = (url: string) => {
      render(
        <MemoryRouter initialEntries={[url]}>
          <Routes>
            <Route path="/search" element={<><SearchResultsPage /><Probe /></>} />
          </Routes>
        </MemoryRouter>
      )
      return router
    }
    const lastSearch = () => {
      const calls = vi.mocked(propertyAdapter.propertyAdapter.searchProperties).mock.calls
      return calls[calls.length - 1][0]
    }

    it('reads filters and sort from the URL and searches with them', async () => {
      renderAt('/search?destination=Tashkent&property_type=9&features=wifi&min_rating=4&min_price=20&sort=price_asc')

      await waitFor(() => {
        expect(propertyAdapter.propertyAdapter.searchProperties).toHaveBeenCalledWith(
          expect.objectContaining({
            location: 'Tashkent',
            property_type: 9,
            features: ['wifi'],
            min_rating: 4,
            min_price: 20,
            sort: 'price_asc',
          })
        )
      })
      expect((screen.getByLabelText('Sort search results') as HTMLSelectElement).value).toBe('price_asc')
      expect(await screen.findByLabelText('Hotel')).toBeChecked()
      expect(screen.getByLabelText('WiFi')).toBeChecked()
      expect(screen.getByLabelText('Minimum price')).toHaveValue(20)
    })

    it('writes a changed filter to the URL and searches again', async () => {
      const router = renderAt('/search?destination=Tashkent&guests=2')
      await screen.findByText('Charming Paris Apartment')

      fireEvent.click(screen.getByLabelText('Parking'))

      await waitFor(() => {
        expect(new URLSearchParams(router.state.location.search).get('features')).toBe('parking')
      })
      const params = new URLSearchParams(router.state.location.search)
      expect(params.get('destination')).toBe('Tashkent')
      expect(params.get('guests')).toBe('2')
      await waitFor(() => expect(lastSearch()).toEqual(expect.objectContaining({ features: ['parking'] })))
    })

    it('writes the sort to the URL', async () => {
      const router = renderAt('/search?destination=Tashkent')
      await screen.findByText('Charming Paris Apartment')

      fireEvent.change(screen.getByLabelText('Sort search results'), { target: { value: 'rating' } })

      await waitFor(() => {
        expect(new URLSearchParams(router.state.location.search).get('sort')).toBe('rating')
      })
      await waitFor(() => expect(lastSearch()).toEqual(expect.objectContaining({ sort: 'rating' })))
    })

    it('clearing filters removes them from the URL but keeps the search and sort', async () => {
      const router = renderAt('/search?destination=Tashkent&features=wifi&property_type=9&sort=rating')
      await screen.findByText('Charming Paris Apartment')

      fireEvent.click(screen.getByRole('button', { name: 'Clear all filters' }))

      await waitFor(() => {
        expect(router.state.location.search).toBe('?destination=Tashkent&sort=rating')
      })
    })

    it('shows property types from the backend, not a fixed list', async () => {
      renderAt('/search?destination=Tashkent')

      expect(await screen.findByLabelText('Guesthouse')).toBeInTheDocument()
      expect(screen.getByLabelText('Hotel')).toBeInTheDocument()
      expect(screen.queryByLabelText('Villa')).not.toBeInTheDocument()
      expect(screen.queryByLabelText('Condo')).not.toBeInTheDocument()
      expect(propertyAdapter.propertyAdapter.getFilterOptions).toHaveBeenCalledTimes(1)
    })

    it('restores filters when going back in history', async () => {
      const router = renderAt('/search?destination=Tashkent')
      await screen.findByText('Charming Paris Apartment')

      fireEvent.click(screen.getByLabelText('WiFi'))
      await waitFor(() => expect(screen.getByLabelText('WiFi')).toBeChecked())

      await act(async () => { await router.navigate(-1) })

      await waitFor(() => expect(screen.getByLabelText('WiFi')).not.toBeChecked())
      expect(router.state.location.search).toBe('?destination=Tashkent')
    })
  })
})
