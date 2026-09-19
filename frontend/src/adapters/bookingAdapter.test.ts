import { describe, it, expect, vi, beforeEach } from 'vitest'
import { BookingAdapter, bookingAdapter } from './bookingAdapter'

describe('BookingAdapter', () => {
  let adapter: BookingAdapter
  let mockFetch: vi.Mock

  beforeEach(() => {
    adapter = new BookingAdapter('http://test-api.com')
    mockFetch = vi.fn()
    global.fetch = mockFetch
  })

  describe('createBooking', () => {
    it('should create a booking with valid data', async () => {
      const mockBooking = {
        id: 1,
        guest: 1,
        guest_name: 'John Doe',
        property: 1,
        property_name: 'Test Property',
        status: 'pending',
        payment_status: 'pending',
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
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockBooking,
      })

      const request = {
        property_id: 1,
        room_type_id: 1,
        rate_plan_id: 1,
        check_in: '2025-01-20',
        check_out: '2025-01-25',
        guest_count: 2,
      }

      const result = await adapter.createBooking(request)

      expect(mockFetch).toHaveBeenCalledWith(
        'http://test-api.com/api/v1/bookings/',
        expect.objectContaining({
          method: 'POST',
          credentials: 'include',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(request),
        })
      )
      expect(result.data).toEqual(mockBooking)
      expect(result.error).toBeNull()
    })

    it('should handle booking creation with special requests', async () => {
      const mockBooking = {
        id: 1,
        guest: 1,
        guest_name: 'John Doe',
        property: 1,
        property_name: 'Test Property',
        status: 'pending',
        payment_status: 'pending',
        check_in: '2025-01-20',
        check_out: '2025-01-25',
        number_of_nights: 5,
        guest_count: 2,
        total_price: 500,
        currency: 'USD',
        special_requests: 'Early check-in requested',
        confirmation_code: 'ABC123',
        booking_items: [],
        created_at: '2025-01-15T10:00:00Z',
        updated_at: '2025-01-15T10:00:00Z',
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockBooking,
      })

      const request = {
        property_id: 1,
        room_type_id: 1,
        rate_plan_id: 1,
        check_in: '2025-01-20',
        check_out: '2025-01-25',
        guest_count: 2,
        special_requests: 'Early check-in requested',
      }

      const result = await adapter.createBooking(request)

      expect(result.data).toEqual(mockBooking)
      expect(result.error).toBeNull()
    })

    it('should handle booking creation errors', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: async () => ({ error: 'Invalid booking parameters', details: { check_in: ['Invalid date'] } }),
      })

      const request = {
        property_id: 1,
        room_type_id: 1,
        rate_plan_id: 1,
        check_in: 'invalid-date',
        check_out: '2025-01-25',
        guest_count: 2,
      }

      const result = await adapter.createBooking(request)

      expect(result.data).toBeNull()
      expect(result.error).toBe('Invalid booking parameters')
    })

    it('should handle network errors', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'))

      const request = {
        property_id: 1,
        room_type_id: 1,
        rate_plan_id: 1,
        check_in: '2025-01-20',
        check_out: '2025-01-25',
        guest_count: 2,
      }

      const result = await adapter.createBooking(request)

      expect(result.data).toBeNull()
      expect(result.error).toBe('Network error')
    })
  })

  describe('getBookings', () => {
    it('should get user bookings without filters', async () => {
      const mockResponse = {
        count: 2,
        next: null,
        previous: null,
        results: [
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
        ],
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      })

      const result = await adapter.getBookings()

      expect(mockFetch).toHaveBeenCalledWith(
        'http://test-api.com/api/v1/bookings/',
        expect.objectContaining({
          credentials: 'include',
        })
      )
      expect(result.data).toEqual(mockResponse)
      expect(result.error).toBeNull()
    })

    it('should get user bookings with status filter', async () => {
      const mockResponse = {
        count: 1,
        next: null,
        previous: null,
        results: [
          {
            id: 1,
            guest: 1,
            guest_name: 'John Doe',
            property: 1,
            property_name: 'Test Property',
            status: 'pending',
            payment_status: 'pending',
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
        ],
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      })

      const result = await adapter.getBookings({ status: 'pending' })

      expect(mockFetch).toHaveBeenCalledWith(
        'http://test-api.com/api/v1/bookings/?status=pending',
        expect.objectContaining({
          credentials: 'include',
        })
      )
      expect(result.data).toEqual(mockResponse)
      expect(result.error).toBeNull()
    })

    it('should handle unauthenticated access', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 403,
        json: async () => ({ detail: 'Authentication required' }),
      })

      const result = await adapter.getBookings()

      expect(result.data).toBeNull()
      expect(result.error).toBe('Authentication required')
    })
  })

  describe('getBookingById', () => {
    it('should get a specific booking by ID', async () => {
      const mockBooking = {
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
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockBooking,
      })

      const result = await adapter.getBookingById(1)

      expect(mockFetch).toHaveBeenCalledWith(
        'http://test-api.com/api/v1/bookings/1/',
        expect.objectContaining({
          credentials: 'include',
        })
      )
      expect(result.data).toEqual(mockBooking)
      expect(result.error).toBeNull()
    })

    it('should handle booking not found', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        json: async () => ({ detail: 'Booking not found' }),
      })

      const result = await adapter.getBookingById(999)

      expect(result.data).toBeNull()
      expect(result.error).toBe('Booking not found')
    })
  })

  describe('cancelBooking', () => {
    it('should cancel a booking with reason', async () => {
      const mockBooking = {
        id: 1,
        guest: 1,
        guest_name: 'John Doe',
        property: 1,
        property_name: 'Test Property',
        status: 'cancelled',
        payment_status: 'refunded',
        check_in: '2025-01-20',
        check_out: '2025-01-25',
        number_of_nights: 5,
        guest_count: 2,
        total_price: 500,
        currency: 'USD',
        confirmation_code: 'ABC123',
        cancelled_at: '2025-01-16T10:00:00Z',
        cancellation_reason: 'Change of plans',
        booking_items: [],
        created_at: '2025-01-15T10:00:00Z',
        updated_at: '2025-01-16T10:00:00Z',
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockBooking,
      })

      const result = await adapter.cancelBooking(1, { cancellation_reason: 'Change of plans' })

      expect(mockFetch).toHaveBeenCalledWith(
        'http://test-api.com/api/v1/bookings/1/cancel/',
        expect.objectContaining({
          method: 'POST',
          credentials: 'include',
          body: JSON.stringify({ cancellation_reason: 'Change of plans' }),
        })
      )
      expect(result.data).toEqual(mockBooking)
      expect(result.error).toBeNull()
    })

    it('should cancel a booking without reason', async () => {
      const mockBooking = {
        id: 1,
        guest: 1,
        guest_name: 'John Doe',
        property: 1,
        property_name: 'Test Property',
        status: 'cancelled',
        payment_status: 'refunded',
        check_in: '2025-01-20',
        check_out: '2025-01-25',
        number_of_nights: 5,
        guest_count: 2,
        total_price: 500,
        currency: 'USD',
        confirmation_code: 'ABC123',
        cancelled_at: '2025-01-16T10:00:00Z',
        booking_items: [],
        created_at: '2025-01-15T10:00:00Z',
        updated_at: '2025-01-16T10:00:00Z',
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockBooking,
      })

      const result = await adapter.cancelBooking(1)

      expect(result.data).toEqual(mockBooking)
      expect(result.error).toBeNull()
    })

    it('should handle cancellation errors', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: async () => ({ error: 'Cannot cancel confirmed booking' }),
      })

      const result = await adapter.cancelBooking(1)

      expect(result.data).toBeNull()
      expect(result.error).toBe('Cannot cancel confirmed booking')
    })
  })

  describe('singleton instance', () => {
    it('should export a singleton instance', () => {
      expect(bookingAdapter).toBeInstanceOf(BookingAdapter)
    })
  })
})
