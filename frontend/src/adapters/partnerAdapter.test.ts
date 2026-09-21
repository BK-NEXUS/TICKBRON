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
})

describe('partnerAdapter singleton', () => {
  it('should export a singleton instance', () => {
    expect(partnerAdapter).toBeInstanceOf(PartnerAdapter)
  })
})
