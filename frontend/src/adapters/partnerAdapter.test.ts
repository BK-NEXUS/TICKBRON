import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { PartnerAdapter, partnerAdapter } from './partnerAdapter'

// Mock fetch
global.fetch = vi.fn()

describe('PartnerAdapter', () => {
  let adapter: PartnerAdapter
  const mockBaseUrl = 'http://test-api.com'

  beforeEach(() => {
    adapter = new PartnerAdapter(mockBaseUrl)
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.resetAllMocks()
  })

  describe('Property Management', () => {
    it('should create a property successfully', async () => {
      const mockProperty = {
        id: 1,
        owner: 1,
        property_type: 1,
        status: 'pending',
        max_guests: 4,
        bedrooms: 2,
        bathrooms: 1,
        address_line1: '123 Test St',
        city: 'Tashkent',
        country: 'Uzbekistan',
        base_price: 100,
        currency: 'USD',
        has_elevator: false,
        has_parking: true,
        has_wifi: true,
        has_ac: false,
        has_heating: false,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      }

      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => mockProperty,
      } as Response)

      const propertyData = {
        property_type: 1,
        max_guests: 4,
        bedrooms: 2,
        bathrooms: 1,
        address_line1: '123 Test St',
        city: 'Tashkent',
        country: 'Uzbekistan',
        base_price: 100,
        currency: 'USD',
        has_elevator: false,
        has_parking: true,
        has_wifi: true,
        has_ac: false,
        has_heating: false,
      }

      const result = await adapter.createProperty(propertyData)

      expect(result.error).toBeNull()
      expect(result.data).toEqual(mockProperty)
      expect(fetch).toHaveBeenCalledWith(
        `${mockBaseUrl}/api/v1/partner/properties/`,
        expect.objectContaining({
          method: 'POST',
          credentials: 'include',
          body: JSON.stringify(propertyData),
        })
      )
    })

    it('should handle 403 error for non-hotel-owner users', async () => {
      vi.mocked(fetch).mockResolvedValueOnce({
        ok: false,
        status: 403,
        json: async () => ({ detail: 'Hotel-owner role required' }),
      } as Response)

      const result = await adapter.createProperty({
        property_type: 1,
        max_guests: 4,
        bedrooms: 2,
        bathrooms: 1,
        address_line1: '123 Test St',
        city: 'Tashkent',
        country: 'Uzbekistan',
        base_price: 100,
        currency: 'USD',
        has_elevator: false,
        has_parking: true,
        has_wifi: true,
        has_ac: false,
        has_heating: false,
      })

      expect(result.error).toBe('Hotel-owner role required')
      expect(result.data).toBeNull()
    })

    it('should get properties successfully', async () => {
      const mockProperties = [
        {
          id: 1,
          owner: 1,
          property_type: 1,
          status: 'active',
          max_guests: 4,
          bedrooms: 2,
          bathrooms: 1,
          address_line1: '123 Test St',
          city: 'Tashkent',
          country: 'Uzbekistan',
          base_price: 100,
          currency: 'USD',
          has_elevator: false,
          has_parking: true,
          has_wifi: true,
          has_ac: false,
          has_heating: false,
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
        },
      ]

      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => mockProperties,
      } as Response)

      const result = await adapter.getProperties()

      expect(result.error).toBeNull()
      expect(result.data).toEqual(mockProperties)
      expect(fetch).toHaveBeenCalledWith(
        `${mockBaseUrl}/api/v1/partner/properties/`,
        expect.objectContaining({
          method: 'GET',
          credentials: 'include',
        })
      )
    })

    it('should update a property successfully', async () => {
      const mockProperty = {
        id: 1,
        owner: 1,
        property_type: 1,
        status: 'active',
        max_guests: 6,
        bedrooms: 3,
        bathrooms: 2,
        address_line1: '123 Test St',
        city: 'Tashkent',
        country: 'Uzbekistan',
        base_price: 150,
        currency: 'USD',
        has_elevator: false,
        has_parking: true,
        has_wifi: true,
        has_ac: false,
        has_heating: false,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-02T00:00:00Z',
      }

      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => mockProperty,
      } as Response)

      const updateData = {
        max_guests: 6,
        bedrooms: 3,
        bathrooms: 2,
        base_price: 150,
      }

      const result = await adapter.updateProperty(1, updateData)

      expect(result.error).toBeNull()
      expect(result.data).toEqual(mockProperty)
      expect(fetch).toHaveBeenCalledWith(
        `${mockBaseUrl}/api/v1/partner/properties/1/`,
        expect.objectContaining({
          method: 'PATCH',
          credentials: 'include',
          body: JSON.stringify(updateData),
        })
      )
    })

    it('should delete a property successfully', async () => {
      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        status: 204,
      } as Response)

      const result = await adapter.deleteProperty(1)

      expect(result.error).toBeNull()
      expect(result.data).toBeNull()
      expect(fetch).toHaveBeenCalledWith(
        `${mockBaseUrl}/api/v1/partner/properties/1/`,
        expect.objectContaining({
          method: 'DELETE',
          credentials: 'include',
        })
      )
    })
  })

  describe('Room Type Management', () => {
    it('should create a room type successfully', async () => {
      const mockRoomType = {
        id: 1,
        property: 1,
        name: 'Deluxe Room',
        slug: 'deluxe-room',
        description: 'A luxurious room',
        base_occupancy: 2,
        max_occupancy: 4,
        base_price: 150,
        currency: 'USD',
        total_rooms: 5,
        bed_configuration: '1 King Bed',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      }

      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => mockRoomType,
      } as Response)

      const roomTypeData = {
        property: 1,
        name: 'Deluxe Room',
        slug: 'deluxe-room',
        description: 'A luxurious room',
        base_occupancy: 2,
        max_occupancy: 4,
        base_price: 150,
        currency: 'USD',
        total_rooms: 5,
        bed_configuration: '1 King Bed',
      }

      const result = await adapter.createRoomType(roomTypeData)

      expect(result.error).toBeNull()
      expect(result.data).toEqual(mockRoomType)
    })

    it('should get room types successfully', async () => {
      const mockRoomTypes = [
        {
          id: 1,
          property: 1,
          name: 'Deluxe Room',
          slug: 'deluxe-room',
          description: 'A luxurious room',
          base_occupancy: 2,
          max_occupancy: 4,
          base_price: 150,
          currency: 'USD',
          total_rooms: 5,
          bed_configuration: '1 King Bed',
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
        },
      ]

      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => mockRoomTypes,
      } as Response)

      const result = await adapter.getRoomTypes()

      expect(result.error).toBeNull()
      expect(result.data).toEqual(mockRoomTypes)
    })

    it('should update a room type successfully', async () => {
      const mockRoomType = {
        id: 1,
        property: 1,
        name: 'Deluxe Suite',
        slug: 'deluxe-suite',
        description: 'A luxurious suite',
        base_occupancy: 2,
        max_occupancy: 4,
        base_price: 200,
        currency: 'USD',
        total_rooms: 5,
        bed_configuration: '1 King Bed',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-02T00:00:00Z',
      }

      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => mockRoomType,
      } as Response)

      const updateData = {
        name: 'Deluxe Suite',
        slug: 'deluxe-suite',
        base_price: 200,
      }

      const result = await adapter.updateRoomType(1, updateData)

      expect(result.error).toBeNull()
      expect(result.data).toEqual(mockRoomType)
    })

    it('should delete a room type successfully', async () => {
      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        status: 204,
      } as Response)

      const result = await adapter.deleteRoomType(1)

      expect(result.error).toBeNull()
      expect(result.data).toBeNull()
    })
  })

  describe('Rate Plan Management', () => {
    it('should create a rate plan successfully', async () => {
      const mockRatePlan = {
        id: 1,
        room_type: 1,
        name: 'Standard Rate',
        slug: 'standard-rate',
        rate_type: 'standard',
        description: 'Standard pricing',
        base_price: 150,
        currency: 'USD',
        min_nights: 1,
        max_nights: 30,
        is_active: true,
        cancellation_policy: 'flexible',
        deposit_required: false,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      }

      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => mockRatePlan,
      } as Response)

      const ratePlanData = {
        room_type: 1,
        name: 'Standard Rate',
        slug: 'standard-rate',
        rate_type: 'standard',
        description: 'Standard pricing',
        base_price: 150,
        currency: 'USD',
        min_nights: 1,
        max_nights: 30,
        is_active: true,
        cancellation_policy: 'flexible',
        deposit_required: false,
      }

      const result = await adapter.createRatePlan(ratePlanData)

      expect(result.error).toBeNull()
      expect(result.data).toEqual(mockRatePlan)
    })

    it('should get rate plans successfully', async () => {
      const mockRatePlans = [
        {
          id: 1,
          room_type: 1,
          name: 'Standard Rate',
          slug: 'standard-rate',
          rate_type: 'standard',
          description: 'Standard pricing',
          base_price: 150,
          currency: 'USD',
          min_nights: 1,
          max_nights: 30,
          is_active: true,
          cancellation_policy: 'flexible',
          deposit_required: false,
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
        },
      ]

      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => mockRatePlans,
      } as Response)

      const result = await adapter.getRatePlans()

      expect(result.error).toBeNull()
      expect(result.data).toEqual(mockRatePlans)
    })

    it('should update a rate plan successfully', async () => {
      const mockRatePlan = {
        id: 1,
        room_type: 1,
        name: 'Premium Rate',
        slug: 'premium-rate',
        rate_type: 'standard',
        description: 'Premium pricing',
        base_price: 200,
        currency: 'USD',
        min_nights: 1,
        max_nights: 30,
        is_active: true,
        cancellation_policy: 'flexible',
        deposit_required: false,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-02T00:00:00Z',
      }

      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => mockRatePlan,
      } as Response)

      const updateData = {
        name: 'Premium Rate',
        slug: 'premium-rate',
        base_price: 200,
      }

      const result = await adapter.updateRatePlan(1, updateData)

      expect(result.error).toBeNull()
      expect(result.data).toEqual(mockRatePlan)
    })

    it('should delete a rate plan successfully', async () => {
      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        status: 204,
      } as Response)

      const result = await adapter.deleteRatePlan(1)

      expect(result.error).toBeNull()
      expect(result.data).toBeNull()
    })
  })

  describe('Date Inventory Management', () => {
    it('should create date inventory successfully', async () => {
      const mockInventory = {
        id: 1,
        rate_plan: 1,
        date: '2024-01-01',
        available_rooms: 5,
        booked_rooms: 0,
        price: 150,
        currency: 'USD',
        is_available: true,
        minimum_stay: 1,
        maximum_stay: 30,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      }

      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => mockInventory,
      } as Response)

      const inventoryData = {
        rate_plan: 1,
        date: '2024-01-01',
        available_rooms: 5,
        price: 150,
        currency: 'USD',
        is_available: true,
        minimum_stay: 1,
        maximum_stay: 30,
      }

      const result = await adapter.createDateInventory(inventoryData)

      expect(result.error).toBeNull()
      expect(result.data).toEqual(mockInventory)
    })

    it('should get date inventory successfully', async () => {
      const mockInventory = [
        {
          id: 1,
          rate_plan: 1,
          date: '2024-01-01',
          available_rooms: 5,
          booked_rooms: 0,
          price: 150,
          currency: 'USD',
          is_available: true,
          minimum_stay: 1,
          maximum_stay: 30,
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
        },
      ]

      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => mockInventory,
      } as Response)

      const result = await adapter.getDateInventory()

      expect(result.error).toBeNull()
      expect(result.data).toEqual(mockInventory)
    })

    it('should update date inventory successfully', async () => {
      const mockInventory = {
        id: 1,
        rate_plan: 1,
        date: '2024-01-01',
        available_rooms: 4,
        booked_rooms: 1,
        price: 160,
        currency: 'USD',
        is_available: true,
        minimum_stay: 1,
        maximum_stay: 30,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-02T00:00:00Z',
      }

      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => mockInventory,
      } as Response)

      const updateData = {
        available_rooms: 4,
        price: 160,
      }

      const result = await adapter.updateDateInventory(1, updateData)

      expect(result.error).toBeNull()
      expect(result.data).toEqual(mockInventory)
    })

    it('should delete date inventory successfully', async () => {
      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        status: 204,
      } as Response)

      const result = await adapter.deleteDateInventory(1)

      expect(result.error).toBeNull()
      expect(result.data).toBeNull()
    })
  })

  describe('Partner Bookings', () => {
    it('should get partner bookings successfully', async () => {
      const mockBookings = [
        {
          id: 1,
          guest: 1,
          guest_name: 'John Doe',
          property: 1,
          property_name: 'Test Property',
          status: 'confirmed',
          payment_status: 'paid',
          check_in: '2024-01-01',
          check_out: '2024-01-05',
          number_of_nights: 4,
          guest_count: 2,
          total_price: 600,
          currency: 'USD',
          confirmation_code: 'ABC123',
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
        },
      ]

      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => mockBookings,
      } as Response)

      const result = await adapter.getPartnerBookings()

      expect(result.error).toBeNull()
      expect(result.data).toEqual(mockBookings)
    })

    it('should get partner bookings with status filter', async () => {
      const mockBookings = [
        {
          id: 1,
          guest: 1,
          guest_name: 'John Doe',
          property: 1,
          property_name: 'Test Property',
          status: 'confirmed',
          payment_status: 'paid',
          check_in: '2024-01-01',
          check_out: '2024-01-05',
          number_of_nights: 4,
          guest_count: 2,
          total_price: 600,
          currency: 'USD',
          confirmation_code: 'ABC123',
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
        },
      ]

      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => mockBookings,
      } as Response)

      const result = await adapter.getPartnerBookings('confirmed', 'paid')

      expect(result.error).toBeNull()
      expect(result.data).toEqual(mockBookings)
      expect(fetch).toHaveBeenCalledWith(
        `${mockBaseUrl}/api/v1/partner/bookings/?status=confirmed&payment_status=paid`,
        expect.objectContaining({
          credentials: 'include',
        })
      )
    })
  })

  describe('Error Handling', () => {
    it('should handle network errors', async () => {
      vi.mocked(fetch).mockRejectedValueOnce(new Error('Network error'))

      const result = await adapter.getProperties()

      expect(result.error).toBe('Network error')
      expect(result.data).toBeNull()
    })

    it('should handle 401 authentication errors', async () => {
      vi.mocked(fetch).mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: async () => ({ detail: 'Authentication required' }),
      } as Response)

      const result = await adapter.getProperties()

      expect(result.error).toBe('Authentication required')
      expect(result.data).toBeNull()
    })

    it('should handle 404 not found errors', async () => {
      vi.mocked(fetch).mockResolvedValueOnce({
        ok: false,
        status: 404,
        json: async () => ({ detail: 'Resource not found' }),
      } as Response)

      const result = await adapter.updateProperty(999, {})

      expect(result.error).toBe('Resource not found')
      expect(result.data).toBeNull()
    })
  })

  describe('Room Inventory Management (audit #31)', () => {
    const mockRow = {
      id: 1, room_type: 7, date: '2026-10-01', available_rooms: 5, booked_rooms: 2,
      remaining_rooms: 3, is_available: true,
    }

    it('should create room inventory', async () => {
      vi.mocked(fetch).mockResolvedValueOnce({ ok: true, json: async () => mockRow } as Response)

      const result = await adapter.createRoomInventory({ room_type: 7, date: '2026-10-01', available_rooms: 5 })

      expect(result.error).toBeNull()
      expect(result.data).toEqual(mockRow)
      expect(fetch).toHaveBeenCalledWith(
        `${mockBaseUrl}/api/v1/partner/room-inventory/`,
        expect.objectContaining({ method: 'POST' }),
      )
    })

    it('should list room inventory with room_type/date filters in the query string', async () => {
      vi.mocked(fetch).mockResolvedValueOnce({ ok: true, json: async () => [mockRow] } as Response)

      const result = await adapter.getRoomInventory({ room_type: 7, date_from: '2026-10-01', date_to: '2026-10-31' })

      expect(result.error).toBeNull()
      expect(result.data).toEqual([mockRow])
      expect(fetch).toHaveBeenCalledWith(
        `${mockBaseUrl}/api/v1/partner/room-inventory/?room_type=7&date_from=2026-10-01&date_to=2026-10-31`,
        expect.anything(),
      )
    })

    it('should update room inventory', async () => {
      vi.mocked(fetch).mockResolvedValueOnce({ ok: true, json: async () => mockRow } as Response)

      const result = await adapter.updateRoomInventory(1, { available_rooms: 4 })

      expect(result.error).toBeNull()
      expect(fetch).toHaveBeenCalledWith(
        `${mockBaseUrl}/api/v1/partner/room-inventory/1/`,
        expect.objectContaining({ method: 'PATCH', body: JSON.stringify({ available_rooms: 4 }) }),
      )
    })

    it('should bulk-set room inventory over a date range', async () => {
      vi.mocked(fetch).mockResolvedValueOnce({ ok: true, json: async () => [mockRow] } as Response)

      const result = await adapter.bulkSetRoomInventory({
        room_type: 7, date_from: '2026-10-01', date_to: '2026-10-05', available_rooms: 3,
      })

      expect(result.error).toBeNull()
      expect(result.data).toEqual([mockRow])
      expect(fetch).toHaveBeenCalledWith(
        `${mockBaseUrl}/api/v1/partner/room-inventory/bulk/`,
        expect.objectContaining({ method: 'POST' }),
      )
    })

    it('should surface the date named in a bulk error', async () => {
      vi.mocked(fetch).mockResolvedValueOnce({
        ok: false, status: 400,
        json: async () => ({ error: { details: { available_rooms: ['Cannot set 2026-10-02 below the 3 room(s) already booked on TICKBRON.'] } } }),
      } as Response)

      const result = await adapter.bulkSetRoomInventory({
        room_type: 7, date_from: '2026-10-01', date_to: '2026-10-05', available_rooms: 1,
      })

      expect(result.data).toBeNull()
      expect(result.error).toContain('2026-10-02')
    })
  })

  describe('External Booking Blocks (RoomBlock, 3.5)', () => {
    const mockBlock = {
      id: 9, room_type: 7, date_from: '2026-10-01', date_to: '2026-10-03', rooms: 2,
      note: 'Booking.com', created_by: 3, created_at: '2026-09-29T00:00:00Z',
    }

    it('should create a block', async () => {
      vi.mocked(fetch).mockResolvedValueOnce({ ok: true, json: async () => mockBlock } as Response)

      const result = await adapter.createBlock({
        room_type: 7, date_from: '2026-10-01', date_to: '2026-10-03', rooms: 2, note: 'Booking.com',
      })

      expect(result.error).toBeNull()
      expect(result.data).toEqual(mockBlock)
      expect(fetch).toHaveBeenCalledWith(
        `${mockBaseUrl}/api/v1/partner/blocks/`,
        expect.objectContaining({ method: 'POST' }),
      )
    })

    it('should list blocks filtered by room_type', async () => {
      vi.mocked(fetch).mockResolvedValueOnce({ ok: true, json: async () => [mockBlock] } as Response)

      const result = await adapter.getBlocks({ room_type: 7 })

      expect(result.error).toBeNull()
      expect(result.data).toEqual([mockBlock])
      expect(fetch).toHaveBeenCalledWith(
        `${mockBaseUrl}/api/v1/partner/blocks/?room_type=7`,
        expect.anything(),
      )
    })

    it('should delete (undo) a block', async () => {
      vi.mocked(fetch).mockResolvedValueOnce({ ok: true, status: 204, json: async () => ({}) } as Response)

      const result = await adapter.deleteBlock(9)

      expect(result.error).toBeNull()
      expect(fetch).toHaveBeenCalledWith(
        `${mockBaseUrl}/api/v1/partner/blocks/9/`,
        expect.objectContaining({ method: 'DELETE' }),
      )
    })
  })

  describe('Bulk Price Edit (3.7)', () => {
    it('should bulk-set price over a date range for one rate plan', async () => {
      const mockRow = {
        id: 4, rate_plan: 11, date: '2026-10-01', available_rooms: 5, booked_rooms: 0,
        price: 120, currency: 'USD', is_available: true, minimum_stay: 1, maximum_stay: 30,
      }
      vi.mocked(fetch).mockResolvedValueOnce({ ok: true, json: async () => [mockRow] } as Response)

      const result = await adapter.bulkSetPrice({
        rate_plan: 11, date_from: '2026-10-01', date_to: '2026-10-05', price: 120,
      })

      expect(result.error).toBeNull()
      expect(result.data).toEqual([mockRow])
      expect(fetch).toHaveBeenCalledWith(
        `${mockBaseUrl}/api/v1/partner/inventory/bulk-price/`,
        expect.objectContaining({ method: 'POST' }),
      )
    })
  })
})

describe('partnerAdapter singleton', () => {
  it('should export a singleton instance', () => {
    expect(partnerAdapter).toBeInstanceOf(PartnerAdapter)
  })
})
