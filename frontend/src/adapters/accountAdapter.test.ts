import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { accountAdapter } from './accountAdapter'

// Mock fetch
const mockFetch = vi.fn()
global.fetch = mockFetch

describe('accountAdapter', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('getFavorites', () => {
    it('should fetch favorites successfully', async () => {
      const mockFavorites = [
        {
          id: 1,
          user: 1,
          property: 1,
          property_name: 'Test Property',
          city: 'Tashkent',
          country: 'Uzbekistan',
          base_price: 100,
          currency: 'USD',
          primary_photo: 'http://example.com/photo.jpg',
          created_at: '2025-01-15T10:00:00Z',
          updated_at: '2025-01-15T10:00:00Z',
        },
      ]

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockFavorites,
      })

      const result = await accountAdapter.getFavorites()

      expect(result.data).toEqual(mockFavorites)
      expect(result.error).toBeNull()
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/me/favorites/'),
        expect.objectContaining({
          method: 'GET',
          credentials: 'include',
        })
      )
    })

    it('should handle 401 unauthorized error', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: async () => ({ detail: 'Authentication credentials were not provided.' }),
      })

      const result = await accountAdapter.getFavorites()

      expect(result.data).toBeNull()
      expect(result.error).toBe('Authentication required')
    })

    it('should handle network errors', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'))

      const result = await accountAdapter.getFavorites()

      expect(result.data).toBeNull()
      expect(result.error).toBe('Network error occurred')
    })
  })

  describe('addFavorite', () => {
    it('should add favorite successfully', async () => {
      const mockFavorite = {
        id: 1,
        user: 1,
        property: 1,
        property_name: 'Test Property',
        city: 'Tashkent',
        country: 'Uzbekistan',
        base_price: 100,
        currency: 'USD',
        created_at: '2025-01-15T10:00:00Z',
        updated_at: '2025-01-15T10:00:00Z',
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockFavorite,
      })

      const result = await accountAdapter.addFavorite(1, 'Great property!')

      expect(result.data).toEqual(mockFavorite)
      expect(result.error).toBeNull()
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/me/favorites/'),
        expect.objectContaining({
          method: 'POST',
          credentials: 'include',
          body: JSON.stringify({ property: 1, notes: 'Great property!' }),
        })
      )
    })

    it('should add favorite without notes', async () => {
      const mockFavorite = {
        id: 1,
        user: 1,
        property: 1,
        property_name: 'Test Property',
        city: 'Tashkent',
        country: 'Uzbekistan',
        base_price: 100,
        currency: 'USD',
        created_at: '2025-01-15T10:00:00Z',
        updated_at: '2025-01-15T10:00:00Z',
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockFavorite,
      })

      const result = await accountAdapter.addFavorite(1)

      expect(result.data).toEqual(mockFavorite)
      expect(result.error).toBeNull()
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/me/favorites/'),
        expect.objectContaining({
          method: 'POST',
          credentials: 'include',
          body: JSON.stringify({ property: 1 }),
        })
      )
    })

    it('should handle 404 property not found error', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        json: async () => ({ detail: 'Property not found' }),
      })

      const result = await accountAdapter.addFavorite(999)

      expect(result.data).toBeNull()
      expect(result.error).toBe('Property not found')
    })

    it('should handle 401 unauthorized error', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: async () => ({ detail: 'Authentication credentials were not provided.' }),
      })

      const result = await accountAdapter.addFavorite(1)

      expect(result.data).toBeNull()
      expect(result.error).toBe('Authentication required')
    })
  })

  describe('removeFavorite', () => {
    it('should remove favorite successfully', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 204,
      })

      const result = await accountAdapter.removeFavorite(1)

      expect(result.data).toBeNull()
      expect(result.error).toBeNull()
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/me/favorites/1/'),
        expect.objectContaining({
          method: 'DELETE',
          credentials: 'include',
        })
      )
    })

    it('should handle 404 favorite not found error', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        json: async () => ({ detail: 'Favorite not found' }),
      })

      const result = await accountAdapter.removeFavorite(999)

      expect(result.data).toBeNull()
      expect(result.error).toBe('Favorite not found')
    })

    it('should handle 401 unauthorized error', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: async () => ({ detail: 'Authentication credentials were not provided.' }),
      })

      const result = await accountAdapter.removeFavorite(1)

      expect(result.data).toBeNull()
      expect(result.error).toBe('Authentication required')
    })
  })

  describe('getFavoriteCount', () => {
    it('should fetch favorite count successfully', async () => {
      const mockCount = { count: 5 }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockCount,
      })

      const result = await accountAdapter.getFavoriteCount()

      expect(result.data).toEqual(mockCount)
      expect(result.error).toBeNull()
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/me/favorites/count/'),
        expect.objectContaining({
          method: 'GET',
          credentials: 'include',
        })
      )
    })

    it('should handle 401 unauthorized error', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: async () => ({ detail: 'Authentication credentials were not provided.' }),
      })

      const result = await accountAdapter.getFavoriteCount()

      expect(result.data).toBeNull()
      expect(result.error).toBe('Authentication required')
    })
  })

  describe('getAccountHistory', () => {
    it('should fetch account history successfully', async () => {
      const mockHistory = [
        {
          id: 1,
          user: 1,
          action: 'favorite_added',
          description: 'Added property to favorites',
          created_at: '2025-01-15T10:00:00Z',
        },
      ]

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockHistory,
      })

      const result = await accountAdapter.getAccountHistory()

      expect(result.data).toEqual(mockHistory)
      expect(result.error).toBeNull()
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/me/history/'),
        expect.objectContaining({
          method: 'GET',
          credentials: 'include',
        })
      )
    })

    it('should handle 401 unauthorized error', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: async () => ({ detail: 'Authentication credentials were not provided.' }),
      })

      const result = await accountAdapter.getAccountHistory()

      expect(result.data).toBeNull()
      expect(result.error).toBe('Authentication required')
    })
  })

  describe('getRecentHistory', () => {
    it('should fetch recent history successfully', async () => {
      const mockHistory = [
        {
          id: 1,
          user: 1,
          action: 'favorite_added',
          description: 'Added property to favorites',
          created_at: '2025-01-15T10:00:00Z',
        },
      ]

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockHistory,
      })

      const result = await accountAdapter.getRecentHistory(10)

      expect(result.data).toEqual(mockHistory)
      expect(result.error).toBeNull()
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/me/history/recent/?limit=10'),
        expect.objectContaining({
          method: 'GET',
          credentials: 'include',
        })
      )
    })

    it('should handle 400 invalid limit error', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: async () => ({}),
      })

      const result = await accountAdapter.getRecentHistory(999)

      expect(result.data).toBeNull()
      expect(result.error).toBe('Invalid limit parameter')
    })

    it('should handle 401 unauthorized error', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: async () => ({ detail: 'Authentication credentials were not provided.' }),
      })

      const result = await accountAdapter.getRecentHistory(10)

      expect(result.data).toBeNull()
      expect(result.error).toBe('Authentication required')
    })
  })

  describe('getAccountHistoryStats', () => {
    it('should fetch account history stats successfully', async () => {
      const mockStats = {
        total_entries: 100,
        action_counts: {
          favorite_added: 50,
          favorite_removed: 30,
          booking_created: 20,
        },
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockStats,
      })

      const result = await accountAdapter.getAccountHistoryStats()

      expect(result.data).toEqual(mockStats)
      expect(result.error).toBeNull()
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/me/history/stats/'),
        expect.objectContaining({
          method: 'GET',
          credentials: 'include',
        })
      )
    })

    it('should handle 401 unauthorized error', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: async () => ({ detail: 'Authentication credentials were not provided.' }),
      })

      const result = await accountAdapter.getAccountHistoryStats()

      expect(result.data).toBeNull()
      expect(result.error).toBe('Authentication required')
    })
  })

  describe('getBookings', () => {
    it('should fetch bookings successfully', async () => {
      const mockBookings = [
        {
          id: 1,
          guest: 1,
          guest_name: 'John Doe',
          property: 1,
          property_name: 'Test Property',
          status: 'confirmed',
          payment_status: 'paid',
          check_in: '2025-01-20',
          check_out: '2025-01-25',
          number_of_nights: 5,
          guest_count: 2,
          total_price: 500,
          currency: 'USD',
          confirmation_code: 'ABC123',
          booking_items: [],
          created_at: '2025-01-15T10:00:00Z',
          updated_at: '2025-01-15T10:00:00Z',
        },
      ]

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockBookings,
      })

      const result = await accountAdapter.getBookings()

      expect(result.data).toEqual(mockBookings)
      expect(result.error).toBeNull()
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/bookings/'),
        expect.objectContaining({
          method: 'GET',
          credentials: 'include',
        })
      )
    })

    it('should fetch bookings with status filter', async () => {
      const mockBookings = [
        {
          id: 1,
          guest: 1,
          guest_name: 'John Doe',
          property: 1,
          property_name: 'Test Property',
          status: 'confirmed',
          payment_status: 'paid',
          check_in: '2025-01-20',
          check_out: '2025-01-25',
          number_of_nights: 5,
          guest_count: 2,
          total_price: 500,
          currency: 'USD',
          confirmation_code: 'ABC123',
          booking_items: [],
          created_at: '2025-01-15T10:00:00Z',
          updated_at: '2025-01-15T10:00:00Z',
        },
      ]

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockBookings,
      })

      const result = await accountAdapter.getBookings('confirmed')

      expect(result.data).toEqual(mockBookings)
      expect(result.error).toBeNull()
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/bookings/?status=confirmed'),
        expect.objectContaining({
          method: 'GET',
          credentials: 'include',
        })
      )
    })

    it('should fetch bookings with payment status filter', async () => {
      const mockBookings = [
        {
          id: 1,
          guest: 1,
          guest_name: 'John Doe',
          property: 1,
          property_name: 'Test Property',
          status: 'confirmed',
          payment_status: 'paid',
          check_in: '2025-01-20',
          check_out: '2025-01-25',
          number_of_nights: 5,
          guest_count: 2,
          total_price: 500,
          currency: 'USD',
          confirmation_code: 'ABC123',
          booking_items: [],
          created_at: '2025-01-15T10:00:00Z',
          updated_at: '2025-01-15T10:00:00Z',
        },
      ]

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockBookings,
      })

      const result = await accountAdapter.getBookings(undefined, 'paid')

      expect(result.data).toEqual(mockBookings)
      expect(result.error).toBeNull()
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/bookings/?payment_status=paid'),
        expect.objectContaining({
          method: 'GET',
          credentials: 'include',
        })
      )
    })

    it('should fetch bookings with both filters', async () => {
      const mockBookings = [
        {
          id: 1,
          guest: 1,
          guest_name: 'John Doe',
          property: 1,
          property_name: 'Test Property',
          status: 'confirmed',
          payment_status: 'paid',
          check_in: '2025-01-20',
          check_out: '2025-01-25',
          number_of_nights: 5,
          guest_count: 2,
          total_price: 500,
          currency: 'USD',
          confirmation_code: 'ABC123',
          booking_items: [],
          created_at: '2025-01-15T10:00:00Z',
          updated_at: '2025-01-15T10:00:00Z',
        },
      ]

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockBookings,
      })

      const result = await accountAdapter.getBookings('confirmed', 'paid')

      expect(result.data).toEqual(mockBookings)
      expect(result.error).toBeNull()
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/bookings/?status=confirmed&payment_status=paid'),
        expect.objectContaining({
          method: 'GET',
          credentials: 'include',
        })
      )
    })

    it('should handle 401 unauthorized error', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: async () => ({ detail: 'Authentication credentials were not provided.' }),
      })

      const result = await accountAdapter.getBookings()

      expect(result.data).toBeNull()
      expect(result.error).toBe('Authentication required')
    })

    it('should handle 403 unauthorized access error', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 403,
        json: async () => ({ detail: 'You do not have permission to perform this action.' }),
      })

      const result = await accountAdapter.getBookings()

      expect(result.data).toBeNull()
      expect(result.error).toBe('Unauthorized access')
    })
  })

  describe('getReviews', () => {
    it('should fetch reviews successfully', async () => {
      const mockReviews = [
        {
          id: 1,
          user: 1,
          property: 1,
          overall_rating: 5,
          cleanliness_rating: 5,
          location_rating: 5,
          value_rating: 5,
          amenities_rating: 5,
          service_rating: 5,
          title: 'Great stay!',
          comment: 'Amazing property',
          status: 'approved',
          created_at: '2025-01-15T10:00:00Z',
          updated_at: '2025-01-15T10:00:00Z',
        },
      ]

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockReviews,
      })

      const result = await accountAdapter.getReviews()

      expect(result.data).toEqual(mockReviews)
      expect(result.error).toBeNull()
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/me/reviews/'),
        expect.objectContaining({
          method: 'GET',
          credentials: 'include',
        })
      )
    })

    it('should handle 401 unauthorized error', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: async () => ({ detail: 'Authentication credentials were not provided.' }),
      })

      const result = await accountAdapter.getReviews()

      expect(result.data).toBeNull()
      expect(result.error).toBe('Authentication required')
    })
  })

  describe('createReview', () => {
    it('should create review successfully', async () => {
      const mockReview = {
        id: 1,
        user: 1,
        property: 1,
        overall_rating: 5,
        cleanliness_rating: 5,
        location_rating: 5,
        value_rating: 5,
        amenities_rating: 5,
        service_rating: 5,
        title: 'Great stay!',
        comment: 'Amazing property',
        status: 'pending',
        created_at: '2025-01-15T10:00:00Z',
        updated_at: '2025-01-15T10:00:00Z',
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockReview,
      })

      const reviewData = {
        property: 1,
        booking: 7,
        overall_rating: 5,
        cleanliness_rating: 5,
        location_rating: 5,
        value_rating: 5,
        amenities_rating: 5,
        service_rating: 5,
        title: 'Great stay!',
        comment: 'Amazing property',
      }

      const result = await accountAdapter.createReview(reviewData)

      expect(result.data).toEqual(mockReview)
      expect(result.error).toBeNull()
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/me/reviews/'),
        expect.objectContaining({
          method: 'POST',
          credentials: 'include',
          body: JSON.stringify(reviewData),
        })
      )
    })

    it('should create review with minimal data', async () => {
      const mockReview = {
        id: 1,
        user: 1,
        property: 1,
        overall_rating: 4,
        status: 'pending',
        created_at: '2025-01-15T10:00:00Z',
        updated_at: '2025-01-15T10:00:00Z',
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockReview,
      })

      const reviewData = {
        property: 1,
        booking: 7,
        overall_rating: 4,
      }

      const result = await accountAdapter.createReview(reviewData)

      expect(result.data).toEqual(mockReview)
      expect(result.error).toBeNull()
    })

    it('should handle 401 unauthorized error', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: async () => ({ detail: 'Authentication credentials were not provided.' }),
      })

      const result = await accountAdapter.createReview({
        property: 1,
        booking: 7,
        overall_rating: 5,
      })

      expect(result.data).toBeNull()
      expect(result.error).toBe('Authentication required')
    })

    it('should handle 400 validation error', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: async () => ({}),
      })

      const result = await accountAdapter.createReview({
        property: 1,
        booking: 7,
        overall_rating: 6, // Invalid rating
      })

      expect(result.data).toBeNull()
      expect(result.error).toBe('Invalid review data')
    })

    it('shows the field errors the backend returns', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: async () => ({
          error: {
            code: 'error',
            message: "{'booking': [ErrorDetail(string='You can only review completed bookings.', code='invalid')]}",
            details: { booking: ['You can only review completed bookings.'] },
          },
        }),
      })

      const result = await accountAdapter.createReview({ property: 1, booking: 7, overall_rating: 5 })

      expect(result.error).toBe('Booking: You can only review completed bookings.')
    })

    it('should handle 404 property not found error', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        json: async () => ({ detail: 'No Property matches the given query.' }),
      })

      const result = await accountAdapter.createReview({
        property: 999,
        booking: 7,
        overall_rating: 5,
      })

      expect(result.data).toBeNull()
      expect(result.error).toBe('Property or booking not found')
    })
  })

  describe('getEligibleProperties', () => {
    it('should fetch eligible properties successfully', async () => {
      const mockEligible = {
        eligible_properties: [
          {
            property_id: 1,
            property_city: 'Tashkent',
            property_country: 'Uzbekistan',
            booking_id: 1,
            confirmation_code: 'ABC123',
            check_in: '2025-01-20',
            check_out: '2025-01-25',
          },
        ],
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockEligible,
      })

      const result = await accountAdapter.getEligibleProperties()

      expect(result.data).toEqual(mockEligible)
      expect(result.error).toBeNull()
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/me/reviews/eligible_properties/'),
        expect.objectContaining({
          method: 'GET',
          credentials: 'include',
        })
      )
    })

    it('should handle 401 unauthorized error', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: async () => ({ detail: 'Authentication credentials were not provided.' }),
      })

      const result = await accountAdapter.getEligibleProperties()

      expect(result.data).toBeNull()
      expect(result.error).toBe('Authentication required')
    })
  })

  describe('getPropertyScores', () => {
    it('should fetch property scores successfully', async () => {
      const mockScores = {
        property_id: 1,
        total_reviews: 10,
        average_rating: 4.5,
        category_scores: {
          cleanliness_rating: 4.8,
          location_rating: 4.6,
          value_rating: 4.4,
          amenities_rating: 4.5,
          service_rating: 4.7,
        },
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockScores,
      })

      const result = await accountAdapter.getPropertyScores(1)

      expect(result.data).toEqual(mockScores)
      expect(result.error).toBeNull()
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/me/reviews/property_scores/?property_id=1'),
        expect.objectContaining({
          method: 'GET',
          credentials: 'include',
        })
      )
    })

    it('should handle property with no reviews', async () => {
      const mockScores = {
        property_id: 1,
        total_reviews: 0,
        average_rating: null,
        category_scores: {},
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockScores,
      })

      const result = await accountAdapter.getPropertyScores(1)

      expect(result.data).toEqual(mockScores)
      expect(result.error).toBeNull()
    })

    it('should handle 401 unauthorized error', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: async () => ({ detail: 'Authentication credentials were not provided.' }),
      })

      const result = await accountAdapter.getPropertyScores(1)

      expect(result.data).toBeNull()
      expect(result.error).toBe('Authentication required')
    })

    it('should handle 400 missing property_id error', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: async () => ({ detail: 'Property ID is required' }),
      })

      const result = await accountAdapter.getPropertyScores(0)

      expect(result.data).toBeNull()
      expect(result.error).toBe('Property ID is required')
    })
  })
})
