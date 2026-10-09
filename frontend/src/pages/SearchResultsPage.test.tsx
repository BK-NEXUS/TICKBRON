import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, waitFor, fireEvent, act } from '@testing-library/react'
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
