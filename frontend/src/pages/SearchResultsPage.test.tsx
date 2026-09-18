import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { RouterProvider, createMemoryRouter } from 'react-router-dom'
import { SearchResultsPage } from './SearchResultsPage'
import * as propertyAdapter from '../adapters/propertyAdapter'

// Mock the property adapter
vi.mock('../adapters/propertyAdapter', () => ({
  propertyAdapter: {
    searchProperties: vi.fn(),
  },
  Property: {},
  SearchParams: {},
  PropertyType: {},
}))

describe('SearchResultsPage', () => {
  const mockPropertyTypes = [
    { id: 1, name: 'Apartment', slug: 'apartment' },
    { id: 2, name: 'House', slug: 'house' },
  ]

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
      image_url: '🏰',
      created_at: '2024-01-15T10:00:00Z',
      updated_at: '2024-01-20T15:30:00Z',
    },
  ]

  beforeEach(() => {
    vi.clearAllMocks()
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

  it('displays loading state initially', () => {
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
    mapButton.click()

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
      expect(screen.getByText('1 properties found')).toBeInTheDocument()
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
})
