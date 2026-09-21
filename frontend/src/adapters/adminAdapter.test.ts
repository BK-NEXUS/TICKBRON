import { describe, it, expect, beforeEach, vi } from 'vitest'
import { AdminAdapter, adminAdapter } from './adminAdapter'

// Mock fetch globally
global.fetch = vi.fn()

describe('AdminAdapter', () => {
  let adapter: AdminAdapter

  beforeEach(() => {
    adapter = new AdminAdapter('http://test-api')
    vi.clearAllMocks()
  })

  describe('Property Moderation Methods', () => {
    it('should get properties successfully', async () => {
      const mockProperties = [
        {
          id: 1,
          owner: 1,
          status: 'pending',
          city: 'Tashkent',
          country: 'Uzbekistan',
          address_line1: '123 Main St',
          base_price: 100,
          currency: 'USD',
          created_at: '2024-01-01T00:00:00Z',
        },
      ]

      ;(global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockProperties,
      })

      const result = await adapter.getProperties()

      expect(result.data).toEqual(mockProperties)
      expect(result.error).toBeNull()
      expect(global.fetch).toHaveBeenCalledWith(
        'http://test-api/api/v1/admin-panel/properties/',
        expect.objectContaining({
          credentials: 'include',
          headers: { 'Content-Type': 'application/json' },
        })
      )
    })

    it('should handle 403 error for non-admin users when getting properties', async () => {
      ;(global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 403,
        json: async () => ({ detail: 'Admin or staff role required' }),
      })

      const result = await adapter.getProperties()

      expect(result.data).toBeNull()
      expect(result.error).toBe('Admin or staff role required')
    })

    it('should approve property successfully', async () => {
      const mockProperty = {
        id: 1,
        status: 'active',
        approved_by: 1,
        approved_at: '2024-01-01T00:00:00Z',
      }

      ;(global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockProperty,
      })

      const result = await adapter.approveProperty(1, {})

      expect(result.data).toEqual(mockProperty)
      expect(result.error).toBeNull()
      expect(global.fetch).toHaveBeenCalledWith(
        'http://test-api/api/v1/admin-panel/properties/1/approve/',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({}),
        })
      )
    })

    it('should reject property with reason', async () => {
      const mockProperty = {
        id: 1,
        status: 'rejected',
        rejection_reason: 'Invalid information',
      }

      ;(global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockProperty,
      })

      const result = await adapter.approveProperty(1, { rejection_reason: 'Invalid information' })

      expect(result.data).toEqual(mockProperty)
      expect(result.error).toBeNull()
      expect(global.fetch).toHaveBeenCalledWith(
        'http://test-api/api/v1/admin-panel/properties/1/approve/',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ rejection_reason: 'Invalid information' }),
        })
      )
    })

    it('should suspend property successfully', async () => {
      const mockProperty = {
        id: 1,
        status: 'suspended',
      }

      ;(global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockProperty,
      })

      const result = await adapter.suspendProperty(1)

      expect(result.data).toEqual(mockProperty)
      expect(result.error).toBeNull()
      expect(global.fetch).toHaveBeenCalledWith(
        'http://test-api/api/v1/admin-panel/properties/1/suspend/',
        expect.objectContaining({
          method: 'POST',
        })
      )
    })
  })

  describe('User Management Methods', () => {
    it('should get users successfully', async () => {
      const mockUsers = [
        {
          id: 1,
          email: 'admin@example.com',
          first_name: 'Admin',
          last_name: 'User',
          full_name: 'Admin User',
          is_staff: true,
          is_superuser: true,
          role: 'super-admin',
          is_active: true,
          date_joined: '2024-01-01T00:00:00Z',
        },
      ]

      ;(global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockUsers,
      })

      const result = await adapter.getUsers()

      expect(result.data).toEqual(mockUsers)
      expect(result.error).toBeNull()
      expect(global.fetch).toHaveBeenCalledWith(
        'http://test-api/api/v1/admin-panel/users/',
        expect.objectContaining({
          method: 'GET',
        })
      )
    })

    it('should create hotel owner account successfully', async () => {
      const mockOwner = {
        id: 2,
        email: 'owner@example.com',
        first_name: 'Hotel',
        last_name: 'Owner',
        full_name: 'Hotel Owner',
        role: 'hotel-owner',
        is_active: true,
        date_joined: '2024-01-01T00:00:00Z',
      }

      const ownerData = {
        email: 'owner@example.com',
        first_name: 'Hotel',
        last_name: 'Owner',
        password: 'SecurePassword123!',
        password_confirm: 'SecurePassword123!',
      }

      ;(global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockOwner,
      })

      const result = await adapter.createHotelOwner(ownerData)

      expect(result.data).toEqual(mockOwner)
      expect(result.error).toBeNull()
      expect(global.fetch).toHaveBeenCalledWith(
        'http://test-api/api/v1/admin-panel/users/create-hotel-owner/',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(ownerData),
        })
      )
    })

    it('should handle 403 error for non-super-admin when creating hotel owner', async () => {
      const ownerData = {
        email: 'owner@example.com',
        first_name: 'Hotel',
        last_name: 'Owner',
        password: 'SecurePassword123!',
        password_confirm: 'SecurePassword123!',
      }

      ;(global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 403,
        json: async () => ({ detail: 'Super-admin required' }),
      })

      const result = await adapter.createHotelOwner(ownerData)

      expect(result.data).toBeNull()
      expect(result.error).toBe('Admin or staff role required')
    })
  })

  describe('Amenity Management Methods', () => {
    it('should get amenities successfully', async () => {
      const mockAmenities = [
        {
          id: 1,
          category: 1,
          category_name: 'Kitchen',
          name: 'WiFi',
          slug: 'wifi',
          description: 'Wireless internet',
          icon: 'wifi',
          is_searchable: true,
          sort_order: 1,
          created_at: '2024-01-01T00:00:00Z',
        },
      ]

      ;(global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockAmenities,
      })

      const result = await adapter.getAmenities()

      expect(result.data).toEqual(mockAmenities)
      expect(result.error).toBeNull()
      expect(global.fetch).toHaveBeenCalledWith(
        'http://test-api/api/v1/admin-panel/amenities/',
        expect.objectContaining({
          method: 'GET',
        })
      )
    })

    it('should create amenity successfully', async () => {
      const mockAmenity = {
        id: 2,
        category: 1,
        name: 'Pool',
        slug: 'pool',
        description: 'Swimming pool',
        icon: 'pool',
        is_searchable: true,
        sort_order: 2,
        created_at: '2024-01-01T00:00:00Z',
      }

      const amenityData = {
        category: 1,
        name: 'Pool',
        slug: 'pool',
        description: 'Swimming pool',
        icon: 'pool',
        is_searchable: true,
        sort_order: 2,
      }

      ;(global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockAmenity,
      })

      const result = await adapter.createAmenity(amenityData)

      expect(result.data).toEqual(mockAmenity)
      expect(result.error).toBeNull()
      expect(global.fetch).toHaveBeenCalledWith(
        'http://test-api/api/v1/admin-panel/amenities/',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(amenityData),
        })
      )
    })

    it('should update amenity successfully', async () => {
      const mockAmenity = {
        id: 1,
        name: 'WiFi Updated',
        slug: 'wifi',
        description: 'Updated description',
      }

      const updateData = {
        name: 'WiFi Updated',
        description: 'Updated description',
      }

      ;(global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockAmenity,
      })

      const result = await adapter.updateAmenity(1, updateData)

      expect(result.data).toEqual(mockAmenity)
      expect(result.error).toBeNull()
      expect(global.fetch).toHaveBeenCalledWith(
        'http://test-api/api/v1/admin-panel/amenities/1/',
        expect.objectContaining({
          method: 'PATCH',
          body: JSON.stringify(updateData),
        })
      )
    })

    it('should delete amenity successfully', async () => {
      ;(global.fetch as any).mockResolvedValueOnce({
        ok: true,
        status: 204,
      })

      const result = await adapter.deleteAmenity(1)

      expect(result.data).toBeNull()
      expect(result.error).toBeNull()
      expect(global.fetch).toHaveBeenCalledWith(
        'http://test-api/api/v1/admin-panel/amenities/1/',
        expect.objectContaining({
          method: 'DELETE',
        })
      )
    })

    it('should get amenity categories successfully', async () => {
      const mockCategories = [
        {
          id: 1,
          name: 'Kitchen',
          slug: 'kitchen',
          description: 'Kitchen amenities',
          icon: 'kitchen',
          sort_order: 1,
          created_at: '2024-01-01T00:00:00Z',
        },
      ]

      ;(global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockCategories,
      })

      const result = await adapter.getAmenityCategories()

      expect(result.data).toEqual(mockCategories)
      expect(result.error).toBeNull()
      expect(global.fetch).toHaveBeenCalledWith(
        'http://test-api/api/v1/admin-panel/amenities/categories/',
        expect.objectContaining({
          method: 'GET',
        })
      )
    })

    it('should create amenity category successfully', async () => {
      const mockCategory = {
        id: 2,
        name: 'Bathroom',
        slug: 'bathroom',
        description: 'Bathroom amenities',
        icon: 'bathroom',
        sort_order: 2,
        created_at: '2024-01-01T00:00:00Z',
      }

      const categoryData = {
        name: 'Bathroom',
        slug: 'bathroom',
        description: 'Bathroom amenities',
        icon: 'bathroom',
        sort_order: 2,
      }

      ;(global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockCategory,
      })

      const result = await adapter.createAmenityCategory(categoryData)

      expect(result.data).toEqual(mockCategory)
      expect(result.error).toBeNull()
      expect(global.fetch).toHaveBeenCalledWith(
        'http://test-api/api/v1/admin-panel/amenities/categories/',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(categoryData),
        })
      )
    })

    it('should update amenity category successfully', async () => {
      const mockCategory = {
        id: 1,
        name: 'Kitchen Updated',
        slug: 'kitchen',
      }

      const updateData = {
        name: 'Kitchen Updated',
      }

      ;(global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockCategory,
      })

      const result = await adapter.updateAmenityCategory(1, updateData)

      expect(result.data).toEqual(mockCategory)
      expect(result.error).toBeNull()
      expect(global.fetch).toHaveBeenCalledWith(
        'http://test-api/api/v1/admin-panel/amenities/categories/1/',
        expect.objectContaining({
          method: 'PATCH',
          body: JSON.stringify(updateData),
        })
      )
    })

    it('should delete amenity category successfully', async () => {
      ;(global.fetch as any).mockResolvedValueOnce({
        ok: true,
        status: 204,
      })

      const result = await adapter.deleteAmenityCategory(1)

      expect(result.data).toBeNull()
      expect(result.error).toBeNull()
      expect(global.fetch).toHaveBeenCalledWith(
        'http://test-api/api/v1/admin-panel/amenities/categories/1/',
        expect.objectContaining({
          method: 'DELETE',
        })
      )
    })
  })

  describe('Payment Monitoring Methods', () => {
    it('should get payment transactions successfully', async () => {
      const mockTransactions = [
        {
          id: 1,
          booking: 1,
          provider: 'payme',
          amount: 100,
          currency: 'USD',
          status: 'completed',
          created_at: '2024-01-01T00:00:00Z',
        },
      ]

      ;(global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockTransactions,
      })

      const result = await adapter.getPaymentTransactions()

      expect(result.data).toEqual(mockTransactions)
      expect(result.error).toBeNull()
      expect(global.fetch).toHaveBeenCalledWith(
        'http://test-api/api/v1/admin-panel/payments/transactions/',
        expect.objectContaining({
          credentials: 'include',
          headers: { 'Content-Type': 'application/json' },
        })
      )
    })

    it('should get payment transactions with filters', async () => {
      const mockTransactions = [
        {
          id: 1,
          booking: 1,
          provider: 'payme',
          amount: 100,
          currency: 'USD',
          status: 'completed',
          created_at: '2024-01-01T00:00:00Z',
        },
      ]

      ;(global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockTransactions,
      })

      const result = await adapter.getPaymentTransactions('completed', 'payme')

      expect(result.data).toEqual(mockTransactions)
      expect(result.error).toBeNull()
      expect(global.fetch).toHaveBeenCalledWith(
        'http://test-api/api/v1/admin-panel/payments/transactions/?status=completed&provider=payme',
        expect.objectContaining({
          credentials: 'include',
          headers: { 'Content-Type': 'application/json' },
        })
      )
    })
  })

  describe('Error Handling', () => {
    it('should handle network errors', async () => {
      ;(global.fetch as any).mockRejectedValueOnce(new Error('Network error'))

      const result = await adapter.getProperties()

      expect(result.data).toBeNull()
      expect(result.error).toBe('Network error')
    })

    it('should handle 404 errors', async () => {
      ;(global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 404,
        json: async () => ({ detail: 'Not found' }),
      })

      const result = await adapter.getProperties()

      expect(result.data).toBeNull()
      expect(result.error).toBe('Resource not found')
    })

    it('should handle 401 authentication errors', async () => {
      ;(global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: async () => ({ detail: 'Authentication required' }),
      })

      const result = await adapter.getProperties()

      expect(result.data).toBeNull()
      expect(result.error).toBe('Authentication required')
    })

    it('should handle generic HTTP errors', async () => {
      ;(global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => ({ detail: 'Internal server error' }),
      })

      const result = await adapter.getProperties()

      expect(result.data).toBeNull()
      expect(result.error).toBe('Internal server error')
    })
  })

  describe('Singleton Instance', () => {
    it('should export singleton instance', () => {
      expect(adminAdapter).toBeInstanceOf(AdminAdapter)
    })
  })
})
