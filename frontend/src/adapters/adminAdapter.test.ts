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

  describe('Customers Directory Methods (Checkpoint 24)', () => {
    it('should get customers successfully', async () => {
      const mockCustomersResponse = {
        count: 2,
        next: null,
        previous: null,
        results: [
          {
            id: 1,
            registration_date: '2024-01-01T00:00:00Z',
            full_name: 'John Doe',
            phone: '+998901234567',
            email: 'john@example.com',
            whatsapp: '+998901234567',
            telegram: '@johndoe',
            preferred_contact_method: 'email',
            total_booking_count: 5,
            last_booking_date: '2024-09-01T00:00:00Z',
            total_amount_paid: 1500,
            customer_status: 'active',
          },
          {
            id: 2,
            registration_date: '2024-02-01T00:00:00Z',
            full_name: 'Jane Smith',
            phone: '+998907654321',
            email: 'jane@example.com',
            whatsapp: null,
            telegram: null,
            preferred_contact_method: 'phone',
            total_booking_count: 2,
            last_booking_date: '2024-08-15T00:00:00Z',
            total_amount_paid: 800,
            customer_status: 'active',
          },
        ],
      }

      ;(global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockCustomersResponse,
      })

      const result = await adapter.getCustomers()

      expect(result.data).toEqual(mockCustomersResponse)
      expect(result.error).toBeNull()
      expect(global.fetch).toHaveBeenCalledWith(
        'http://test-api/api/v1/admin-panel/customers/',
        expect.objectContaining({
          credentials: 'include',
          headers: { 'Content-Type': 'application/json' },
        })
      )
    })

    it('should get customers with search parameter', async () => {
      const mockCustomersResponse = {
        count: 1,
        next: null,
        previous: null,
        results: [
          {
            id: 1,
            registration_date: '2024-01-01T00:00:00Z',
            full_name: 'John Doe',
            phone: '+998901234567',
            email: 'john@example.com',
            whatsapp: '+998901234567',
            telegram: '@johndoe',
            preferred_contact_method: 'email',
            total_booking_count: 5,
            last_booking_date: '2024-09-01T00:00:00Z',
            total_amount_paid: 1500,
            customer_status: 'active',
          },
        ],
      }

      ;(global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockCustomersResponse,
      })

      const result = await adapter.getCustomers({ search: 'John' })

      expect(result.data).toEqual(mockCustomersResponse)
      expect(result.error).toBeNull()
      expect(global.fetch).toHaveBeenCalledWith(
        'http://test-api/api/v1/admin-panel/customers/?search=John',
        expect.objectContaining({
          credentials: 'include',
          headers: { 'Content-Type': 'application/json' },
        })
      )
    })

    it('should get customers with pagination parameters', async () => {
      const mockCustomersResponse = {
        count: 50,
        next: 'http://test-api/api/v1/admin-panel/customers/?page=2',
        previous: null,
        results: [
          {
            id: 1,
            registration_date: '2024-01-01T00:00:00Z',
            full_name: 'John Doe',
            phone: '+998901234567',
            email: 'john@example.com',
            whatsapp: '+998901234567',
            telegram: '@johndoe',
            preferred_contact_method: 'email',
            total_booking_count: 5,
            last_booking_date: '2024-09-01T00:00:00Z',
            total_amount_paid: 1500,
            customer_status: 'active',
          },
        ],
      }

      ;(global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockCustomersResponse,
      })

      const result = await adapter.getCustomers({ page: 1, page_size: 20 })

      expect(result.data).toEqual(mockCustomersResponse)
      expect(result.error).toBeNull()
      expect(global.fetch).toHaveBeenCalledWith(
        'http://test-api/api/v1/admin-panel/customers/?page=1&page_size=20',
        expect.objectContaining({
          credentials: 'include',
          headers: { 'Content-Type': 'application/json' },
        })
      )
    })

    it('should get customers with sorting parameters', async () => {
      const mockCustomersResponse = {
        count: 2,
        next: null,
        previous: null,
        results: [
          {
            id: 1,
            registration_date: '2024-01-01T00:00:00Z',
            full_name: 'John Doe',
            phone: '+998901234567',
            email: 'john@example.com',
            whatsapp: '+998901234567',
            telegram: '@johndoe',
            preferred_contact_method: 'email',
            total_booking_count: 5,
            last_booking_date: '2024-09-01T00:00:00Z',
            total_amount_paid: 1500,
            customer_status: 'active',
          },
        ],
      }

      ;(global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockCustomersResponse,
      })

      const result = await adapter.getCustomers({ sort_by: 'total_booking_count', sort_order: 'desc' })

      expect(result.data).toEqual(mockCustomersResponse)
      expect(result.error).toBeNull()
      expect(global.fetch).toHaveBeenCalledWith(
        'http://test-api/api/v1/admin-panel/customers/?sort_by=total_booking_count&sort_order=desc',
        expect.objectContaining({
          credentials: 'include',
          headers: { 'Content-Type': 'application/json' },
        })
      )
    })

    it('should get customers with all parameters combined', async () => {
      const mockCustomersResponse = {
        count: 1,
        next: null,
        previous: null,
        results: [
          {
            id: 1,
            registration_date: '2024-01-01T00:00:00Z',
            full_name: 'John Doe',
            phone: '+998901234567',
            email: 'john@example.com',
            whatsapp: '+998901234567',
            telegram: '@johndoe',
            preferred_contact_method: 'email',
            total_booking_count: 5,
            last_booking_date: '2024-09-01T00:00:00Z',
            total_amount_paid: 1500,
            customer_status: 'active',
          },
        ],
      }

      ;(global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockCustomersResponse,
      })

      const result = await adapter.getCustomers({
        search: 'John',
        page: 1,
        page_size: 50,
        sort_by: 'total_amount_paid',
        sort_order: 'desc',
      })

      expect(result.data).toEqual(mockCustomersResponse)
      expect(result.error).toBeNull()
      expect(global.fetch).toHaveBeenCalledWith(
        'http://test-api/api/v1/admin-panel/customers/?search=John&page=1&page_size=50&sort_by=total_amount_paid&sort_order=desc',
        expect.objectContaining({
          credentials: 'include',
          headers: { 'Content-Type': 'application/json' },
        })
      )
    })

    it('should handle 403 error for non-staff users when getting customers', async () => {
      ;(global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 403,
        json: async () => ({ detail: 'Admin or staff role required' }),
      })

      const result = await adapter.getCustomers()

      expect(result.data).toBeNull()
      expect(result.error).toBe('Admin or staff role required')
    })

    it('should handle 404 error when customers endpoint not found', async () => {
      ;(global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 404,
        json: async () => ({ detail: 'Not found' }),
      })

      const result = await adapter.getCustomers()

      expect(result.data).toBeNull()
      expect(result.error).toBe('Resource not found')
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

  describe('Admin Customer Profile Methods (Checkpoint 25)', () => {
    it('should get customer profile successfully', async () => {
      const mockCustomerProfile = {
        customer: {
          id: 1,
          email: 'john@example.com',
          first_name: 'John',
          last_name: 'Doe',
          full_name: 'John Doe',
          phone_number: '+998901234567',
          whatsapp: '+998901234567',
          telegram: '@johndoe',
          preferred_contact_method: 'email',
          date_joined: '2024-01-01T00:00:00Z',
          last_login: '2024-09-15T10:30:00Z',
          is_active: true,
          email_verified: true,
          phone_verified: true,
        },
        bookings: [
          {
            id: 1,
            reference_code: 'ABC123',
            status: 'confirmed',
            payment_status: 'paid',
            check_in: '2024-10-01T00:00:00Z',
            check_out: '2024-10-03T00:00:00Z',
            number_of_nights: 2,
            total_price: 200,
            currency: 'USD',
            property_name: 'Tashkent Hotel',
            property_city: 'Tashkent',
            created_at: '2024-09-01T00:00:00Z',
          },
        ],
        payments: [
          {
            id: 1,
            booking_id: 1,
            provider: 'payme',
            amount: 200,
            currency: 'USD',
            status: 'paid',
            created_at: '2024-09-01T00:00:00Z',
          },
        ],
        internal_notes: [
          {
            id: 1,
            customer: 1,
            author: 10,
            author_name: 'Admin User',
            author_email: 'admin@example.com',
            note: 'VIP customer',
            created_at: '2024-09-10T10:00:00Z',
            updated_at: '2024-09-10T10:00:00Z',
          },
        ],
        last_activity: '2024-09-15T10:30:00Z',
      }

      ;(global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockCustomerProfile,
      })

      const result = await adapter.getCustomerProfile(1)

      expect(result.data).toEqual(mockCustomerProfile)
      expect(result.error).toBeNull()
      expect(global.fetch).toHaveBeenCalledWith(
        'http://test-api/api/v1/admin-panel/customers/1/',
        expect.objectContaining({
          credentials: 'include',
          headers: { 'Content-Type': 'application/json' },
        })
      )
    })

    it('should get customer profile with booking filter', async () => {
      const mockCustomerProfile = {
        customer: {
          id: 1,
          email: 'john@example.com',
          first_name: 'John',
          last_name: 'Doe',
          full_name: 'John Doe',
          phone_number: '+998901234567',
          whatsapp: '+998901234567',
          telegram: '@johndoe',
          preferred_contact_method: 'email',
          date_joined: '2024-01-01T00:00:00Z',
          last_login: '2024-09-15T10:30:00Z',
          is_active: true,
          email_verified: true,
          phone_verified: true,
        },
        bookings: [],
        payments: [],
        internal_notes: [],
      }

      ;(global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockCustomerProfile,
      })

      const result = await adapter.getCustomerProfile(1, { booking_filter: 'upcoming' })

      expect(result.data).toEqual(mockCustomerProfile)
      expect(result.error).toBeNull()
      expect(global.fetch).toHaveBeenCalledWith(
        'http://test-api/api/v1/admin-panel/customers/1/?booking_filter=upcoming',
        expect.objectContaining({
          credentials: 'include',
          headers: { 'Content-Type': 'application/json' },
        })
      )
    })

    it('should create internal note successfully', async () => {
      const mockNote = {
        id: 1,
        customer: 1,
        author: 10,
        author_name: 'Admin User',
        author_email: 'admin@example.com',
        note: 'VIP customer',
        created_at: '2024-09-10T10:00:00Z',
        updated_at: '2024-09-10T10:00:00Z',
      }

      ;(global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockNote,
      })

      const noteData = { note: 'VIP customer' }
      const result = await adapter.createInternalNote(1, noteData)

      expect(result.data).toEqual(mockNote)
      expect(result.error).toBeNull()
      expect(global.fetch).toHaveBeenCalledWith(
        'http://test-api/api/v1/admin-panel/customers/1/notes/',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(noteData),
        })
      )
    })

    it('should update internal note successfully', async () => {
      const mockNote = {
        id: 1,
        customer: 1,
        author: 10,
        author_name: 'Admin User',
        author_email: 'admin@example.com',
        note: 'Updated note',
        created_at: '2024-09-10T10:00:00Z',
        updated_at: '2024-09-16T10:00:00Z',
      }

      ;(global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockNote,
      })

      const noteData = { note: 'Updated note' }
      const result = await adapter.updateInternalNote(1, 1, noteData)

      expect(result.data).toEqual(mockNote)
      expect(result.error).toBeNull()
      expect(global.fetch).toHaveBeenCalledWith(
        'http://test-api/api/v1/admin-panel/customers/1/notes/1/',
        expect.objectContaining({
          method: 'PUT',
          body: JSON.stringify(noteData),
        })
      )
    })

    it('should delete internal note successfully', async () => {
      ;(global.fetch as any).mockResolvedValueOnce({
        ok: true,
        status: 204,
      })

      const result = await adapter.deleteInternalNote(1, 1)

      expect(result.data).toBeNull()
      expect(result.error).toBeNull()
      expect(global.fetch).toHaveBeenCalledWith(
        'http://test-api/api/v1/admin-panel/customers/1/notes/1/',
        expect.objectContaining({
          method: 'DELETE',
        })
      )
    })

    it('should handle 403 error for non-staff users when getting customer profile', async () => {
      ;(global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 403,
        json: async () => ({ detail: 'Admin or staff role required' }),
      })

      const result = await adapter.getCustomerProfile(1)

      expect(result.data).toBeNull()
      expect(result.error).toBe('Admin or staff role required')
    })

    it('should handle 404 error when customer not found', async () => {
      ;(global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 404,
        json: async () => ({ detail: 'Not found' }),
      })

      const result = await adapter.getCustomerProfile(999)

      expect(result.data).toBeNull()
      expect(result.error).toBe('Resource not found')
    })
  })

  describe('Statistics Methods (Checkpoint 26)', () => {
    it('should get registration statistics successfully', async () => {
      const mockStatistics = {
        type: 'rolling_12_months',
        data: [
          { period: '2024-01', count: 15 },
          { period: '2024-02', count: 23 },
          { period: '2024-03', count: 18 },
        ],
      }

      ;(global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockStatistics,
      })

      const result = await adapter.getRegistrationStatistics()

      expect(result.data).toEqual(mockStatistics)
      expect(result.error).toBeNull()
      expect(global.fetch).toHaveBeenCalledWith(
        'http://test-api/api/v1/admin-panel/statistics/registrations/',
        expect.objectContaining({
          credentials: 'include',
          headers: { 'Content-Type': 'application/json' },
        })
      )
    })

    it('should get registration statistics with type parameter', async () => {
      const mockStatistics = {
        type: 'calendar_year',
        data: [
          { period: '2023', count: 150 },
          { period: '2024', count: 200 },
        ],
      }

      ;(global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockStatistics,
      })

      const result = await adapter.getRegistrationStatistics({ type: 'calendar_year' })

      expect(result.data).toEqual(mockStatistics)
      expect(result.error).toBeNull()
      expect(global.fetch).toHaveBeenCalledWith(
        'http://test-api/api/v1/admin-panel/statistics/registrations/?type=calendar_year',
        expect.objectContaining({
          credentials: 'include',
          headers: { 'Content-Type': 'application/json' },
        })
      )
    })

    it('should get top bookers leaderboard successfully', async () => {
      const mockTopBookers = [
        {
          rank: 1,
          customer_id: 1,
          customer_name: 'John Doe',
          completed_booking_count: 15,
        },
        {
          rank: 2,
          customer_id: 2,
          customer_name: 'Jane Smith',
          completed_booking_count: 12,
        },
      ]

      ;(global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockTopBookers,
      })

      const result = await adapter.getTopBookers()

      expect(result.data).toEqual(mockTopBookers)
      expect(result.error).toBeNull()
      expect(global.fetch).toHaveBeenCalledWith(
        'http://test-api/api/v1/admin-panel/statistics/top-bookers/',
        expect.objectContaining({
          credentials: 'include',
          headers: { 'Content-Type': 'application/json' },
        })
      )
    })

    it('should get top bookers leaderboard with period parameter', async () => {
      const mockTopBookers = [
        {
          rank: 1,
          customer_id: 1,
          customer_name: 'John Doe',
          completed_booking_count: 5,
        },
      ]

      ;(global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockTopBookers,
      })

      const result = await adapter.getTopBookers({ period: 'this_month' })

      expect(result.data).toEqual(mockTopBookers)
      expect(result.error).toBeNull()
      expect(global.fetch).toHaveBeenCalledWith(
        'http://test-api/api/v1/admin-panel/statistics/top-bookers/?period=this_month',
        expect.objectContaining({
          credentials: 'include',
          headers: { 'Content-Type': 'application/json' },
        })
      )
    })

    it('should get top bookers leaderboard with limit parameter', async () => {
      const mockTopBookers = [
        {
          rank: 1,
          customer_id: 1,
          customer_name: 'John Doe',
          completed_booking_count: 15,
        },
      ]

      ;(global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockTopBookers,
      })

      const result = await adapter.getTopBookers({ limit: 5 })

      expect(result.data).toEqual(mockTopBookers)
      expect(result.error).toBeNull()
      expect(global.fetch).toHaveBeenCalledWith(
        'http://test-api/api/v1/admin-panel/statistics/top-bookers/?limit=5',
        expect.objectContaining({
          credentials: 'include',
          headers: { 'Content-Type': 'application/json' },
        })
      )
    })

    it('should get top bookers leaderboard with all parameters', async () => {
      const mockTopBookers = [
        {
          rank: 1,
          customer_id: 1,
          customer_name: 'John Doe',
          completed_booking_count: 3,
        },
      ]

      ;(global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockTopBookers,
      })

      const result = await adapter.getTopBookers({ period: 'this_year', limit: 20 })

      expect(result.data).toEqual(mockTopBookers)
      expect(result.error).toBeNull()
      expect(global.fetch).toHaveBeenCalledWith(
        'http://test-api/api/v1/admin-panel/statistics/top-bookers/?period=this_year&limit=20',
        expect.objectContaining({
          credentials: 'include',
          headers: { 'Content-Type': 'application/json' },
        })
      )
    })

    it('should handle 403 error for non-staff users when getting statistics', async () => {
      ;(global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 403,
        json: async () => ({ detail: 'Admin or staff role required' }),
      })

      const result = await adapter.getRegistrationStatistics()

      expect(result.data).toBeNull()
      expect(result.error).toBe('Admin or staff role required')
    })
  })

  describe('Support Lookup Methods (Checkpoint 23)', () => {
    it('should look up booking by reference code successfully', async () => {
      const mockBooking = {
        id: 1,
        reference_code: 'ABC123',
        status: 'confirmed',
        payment_status: 'paid',
        check_in: '2024-10-01T00:00:00Z',
        check_out: '2024-10-03T00:00:00Z',
        number_of_nights: 2,
        total_price: 200,
        currency: 'USD',
        property: {
          id: 1,
          name: 'Tashkent Hotel',
          city: 'Tashkent',
          country: 'Uzbekistan',
          address_line1: '123 Main St',
        },
        room: {
          id: 1,
          name: 'Deluxe Room',
          room_type: 'deluxe',
        },
        customer: {
          id: 1,
          full_name: 'John Doe',
          email: 'john@example.com',
          phone_number: '+998901234567',
          whatsapp: '+998901234567',
          telegram: '@johndoe',
          preferred_contact_method: 'email',
        },
        created_at: '2024-09-01T00:00:00Z',
        updated_at: '2024-09-01T00:00:00Z',
      }

      ;(global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockBooking,
      })

      const result = await adapter.lookupBookingByReferenceCode({ reference_code: 'ABC123' })

      expect(result.data).toEqual(mockBooking)
      expect(result.error).toBeNull()
      expect(global.fetch).toHaveBeenCalledWith(
        'http://test-api/api/v1/admin-panel/bookings/lookup/?reference_code=ABC123',
        expect.objectContaining({
          credentials: 'include',
          headers: { 'Content-Type': 'application/json' },
        })
      )
    })

    it('should handle 404 error when booking not found', async () => {
      ;(global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 404,
        json: async () => ({ detail: 'Booking not found' }),
      })

      const result = await adapter.lookupBookingByReferenceCode({ reference_code: 'INVALID' })

      expect(result.data).toBeNull()
      expect(result.error).toBe('Resource not found')
    })

    it('should handle 403 error for non-staff users when looking up booking', async () => {
      ;(global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 403,
        json: async () => ({ detail: 'Admin or staff role required' }),
      })

      const result = await adapter.lookupBookingByReferenceCode({ reference_code: 'ABC123' })

      expect(result.data).toBeNull()
      expect(result.error).toBe('Admin or staff role required')
    })
  })

  describe('Singleton Instance', () => {
    it('should export singleton instance', () => {
      expect(adminAdapter).toBeInstanceOf(AdminAdapter)
    })
  })
})

// Total tests: 48 (previous: 37, added 11 statistics + support lookup tests)
