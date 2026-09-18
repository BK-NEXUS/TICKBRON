// Tests for Property API adapter
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { PropertyAdapter, propertyAdapter } from './propertyAdapter'

// Mock fetch
const mockFetch = vi.fn()
global.fetch = mockFetch

describe('PropertyAdapter', () => {
  let adapter: PropertyAdapter

  beforeEach(() => {
    adapter = new PropertyAdapter('http://test-api')
    mockFetch.mockClear()
  })

  afterEach(() => {
    mockFetch.mockReset()
  })

  describe('searchProperties', () => {
    it('should search properties with basic parameters', async () => {
      const mockResponse = {
        count: 10,
        next: null,
        previous: null,
        results: [
          {
            id: 1,
            name: 'Test Property',
            base_price: 100,
            city: 'Test City',
          },
        ],
        page: 1,
        page_size: 20,
        total_pages: 1,
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      })

      const result = await adapter.searchProperties({ q: 'test' })

      expect(result.error).toBeNull()
      expect(result.data).toEqual(mockResponse)
      expect(mockFetch).toHaveBeenCalledWith(
        'http://test-api/api/v1/properties/search/?q=test',
        expect.objectContaining({
          credentials: 'include',
          headers: { 'Content-Type': 'application/json' },
        })
      )
    })

    it('should handle search with all parameters', async () => {
      const mockResponse = {
        count: 5,
        next: null,
        previous: null,
        results: [],
        page: 1,
        page_size: 10,
        total_pages: 1,
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      })

      const params = {
        q: 'test',
        location: 'Paris',
        lat: 48.8566,
        lng: 2.3522,
        radius: 10,
        min_price: 50,
        max_price: 500,
        min_guests: 1,
        max_guests: 10,
        amenities: [1, 2, 3],
        property_type: 1,
        check_in: '2024-01-01',
        check_out: '2024-01-07',
        sort: 'price_asc',
        page: 1,
        page_size: 10,
      }

      const result = await adapter.searchProperties(params)

      expect(result.error).toBeNull()
      expect(result.data).toEqual(mockResponse)
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('api/v1/properties/search/'),
        expect.any(Object)
      )
    })

    it('should handle API errors', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: async () => ({ error: 'Invalid parameters', details: 'Location too long' }),
      })

      const result = await adapter.searchProperties({ location: 'a'.repeat(300) })

      expect(result.data).toBeNull()
      expect(result.error).toContain('Invalid parameters')
    })

    it('should handle network errors', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'))

      const result = await adapter.searchProperties({ q: 'test' })

      expect(result.data).toBeNull()
      expect(result.error).toBe('Network error')
    })

    it('should handle empty search results', async () => {
      const mockResponse = {
        count: 0,
        next: null,
        previous: null,
        results: [],
        page: 1,
        page_size: 20,
        total_pages: 0,
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      })

      const result = await adapter.searchProperties({ q: 'nonexistent' })

      expect(result.error).toBeNull()
      expect(result.data?.results).toEqual([])
      expect(result.data?.count).toBe(0)
    })
  })

  describe('getSearchSuggestions', () => {
    it('should get search suggestions', async () => {
      const mockResponse = {
        suggestions: ['Paris', 'Paris, France', 'Paris, Texas'],
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      })

      const result = await adapter.getSearchSuggestions('Paris', 5)

      expect(result.error).toBeNull()
      expect(result.data).toEqual(mockResponse)
      expect(mockFetch).toHaveBeenCalledWith(
        'http://test-api/api/v1/properties/search/suggestions/?q=Paris&limit=5',
        expect.objectContaining({
          credentials: 'include',
        })
      )
    })

    it('should handle API errors for suggestions', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => ({ error: 'Server error' }),
      })

      const result = await adapter.getSearchSuggestions('test')

      expect(result.data).toBeNull()
      expect(result.error).toBeTruthy()
    })
  })

  describe('getPropertyById', () => {
    it('should get property details by ID', async () => {
      const mockResponse = {
        id: 1,
        name: 'Test Property',
        base_price: 100,
        city: 'Test City',
        gallery: {
          exterior: [{ id: 1, photo: 'url1.jpg', photo_type: 'exterior', is_primary: true, display_order: 1 }],
        },
        room_types: [],
        amenities: [],
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      })

      const result = await adapter.getPropertyById(1)

      expect(result.error).toBeNull()
      expect(result.data).toEqual(mockResponse)
      expect(mockFetch).toHaveBeenCalledWith(
        'http://test-api/api/v1/properties/1/',
        expect.objectContaining({
          credentials: 'include',
        })
      )
    })

    it('should handle property not found', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        json: async () => ({ error: 'Property not found', details: 'Property with ID 999 does not exist' }),
      })

      const result = await adapter.getPropertyById(999)

      expect(result.data).toBeNull()
      expect(result.error).toContain('Property not found')
    })

    it('should handle network errors', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'))

      const result = await adapter.getPropertyById(1)

      expect(result.data).toBeNull()
      expect(result.error).toBe('Network error')
    })
  })

  describe('singleton instance', () => {
    it('should export singleton instance', () => {
      expect(propertyAdapter).toBeInstanceOf(PropertyAdapter)
    })
  })
})
