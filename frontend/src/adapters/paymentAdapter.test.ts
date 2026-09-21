import { describe, it, expect, beforeEach, vi } from 'vitest'
import { PaymentAdapter, PaymentProvider, PaymentStatus } from './paymentAdapter'

describe('PaymentAdapter', () => {
  let adapter: PaymentAdapter
  let mockFetch: ReturnType<typeof vi.fn>

  beforeEach(() => {
    adapter = new PaymentAdapter('http://test-api.com')
    mockFetch = vi.fn()
    global.fetch = mockFetch
  })

  describe('createPayment', () => {
    it('should create a payment transaction successfully', async () => {
      const mockResponse = {
        id: 1,
        idempotency_key: 'test_key_123',
        booking: 100,
        provider: 'payme' as PaymentProvider,
        provider_transaction_id: 'txn_123',
        amount: 100.00,
        currency: 'USD',
        status: 'processing' as PaymentStatus,
        payment_method_token: null,
        provider_response: { success: true },
        error_code: null,
        error_message: null,
        client_ip: '127.0.0.1',
        user_agent: 'test-agent',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      })

      const request = {
        idempotency_key: 'test_key_123',
        booking: 100,
        provider: 'payme' as PaymentProvider,
        amount: 100.00,
        currency: 'USD',
      }

      const result = await adapter.createPayment(request)

      expect(mockFetch).toHaveBeenCalledWith(
        'http://test-api.com/api/v1/payments/transactions/',
        expect.objectContaining({
          method: 'POST',
          credentials: 'include',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
          body: JSON.stringify(request),
        })
      )

      expect(result.data).toEqual(mockResponse)
      expect(result.error).toBeNull()
    })

    it('should handle payment creation error', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: async () => ({ error: 'Invalid payment request' }),
      })

      const request = {
        idempotency_key: 'test_key_123',
        booking: 100,
        provider: 'payme' as PaymentProvider,
        amount: 100.00,
        currency: 'USD',
      }

      const result = await adapter.createPayment(request)

      expect(result.data).toBeNull()
      expect(result.error).toBe('Invalid payment request')
    })

    it('should handle network errors', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'))

      const request = {
        idempotency_key: 'test_key_123',
        booking: 100,
        provider: 'payme' as PaymentProvider,
        amount: 100.00,
        currency: 'USD',
      }

      const result = await adapter.createPayment(request)

      expect(result.data).toBeNull()
      expect(result.error).toBe('Network error')
    })
  })

  describe('confirmPayment', () => {
    it('should confirm a payment transaction successfully', async () => {
      const mockResponse = {
        id: 1,
        idempotency_key: 'test_key_123',
        booking: 100,
        provider: 'payme' as PaymentProvider,
        provider_transaction_id: 'txn_123',
        amount: 100.00,
        currency: 'USD',
        status: 'completed' as PaymentStatus,
        payment_method_token: null,
        provider_response: { success: true },
        error_code: null,
        error_message: null,
        client_ip: '127.0.0.1',
        user_agent: 'test-agent',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      })

      const result = await adapter.confirmPayment(1)

      expect(mockFetch).toHaveBeenCalledWith(
        'http://test-api.com/api/v1/payments/transactions/1/confirm/',
        expect.objectContaining({
          method: 'POST',
          credentials: 'include',
        })
      )

      expect(result.data).toEqual(mockResponse)
      expect(result.error).toBeNull()
    })

    it('should handle payment confirmation error', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: async () => ({ error: 'Payment already confirmed' }),
      })

      const result = await adapter.confirmPayment(1)

      expect(result.data).toBeNull()
      expect(result.error).toBe('Payment already confirmed')
    })
  })

  describe('refundPayment', () => {
    it('should refund a payment transaction successfully', async () => {
      const mockResponse = {
        id: 1,
        idempotency_key: 'test_key_123',
        booking: 100,
        provider: 'payme' as PaymentProvider,
        provider_transaction_id: 'txn_123',
        amount: 100.00,
        currency: 'USD',
        status: 'refunded' as PaymentStatus,
        payment_method_token: null,
        provider_response: { success: true },
        error_code: null,
        error_message: null,
        client_ip: '127.0.0.1',
        user_agent: 'test-agent',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      })

      const result = await adapter.refundPayment(1, { amount: 50.00 })

      expect(mockFetch).toHaveBeenCalledWith(
        'http://test-api.com/api/v1/payments/transactions/1/refund/',
        expect.objectContaining({
          method: 'POST',
          credentials: 'include',
          body: JSON.stringify({ amount: 50.00 }),
        })
      )

      expect(result.data).toEqual(mockResponse)
      expect(result.error).toBeNull()
    })

    it('should handle refund without amount (full refund)', async () => {
      const mockResponse = {
        id: 1,
        idempotency_key: 'test_key_123',
        booking: 100,
        provider: 'payme' as PaymentProvider,
        provider_transaction_id: 'txn_123',
        amount: 100.00,
        currency: 'USD',
        status: 'refunded' as PaymentStatus,
        payment_method_token: null,
        provider_response: { success: true },
        error_code: null,
        error_message: null,
        client_ip: '127.0.0.1',
        user_agent: 'test-agent',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      })

      const result = await adapter.refundPayment(1)

      expect(mockFetch).toHaveBeenCalledWith(
        'http://test-api.com/api/v1/payments/transactions/1/refund/',
        expect.objectContaining({
          method: 'POST',
          credentials: 'include',
          body: JSON.stringify({}),
        })
      )

      expect(result.data).toEqual(mockResponse)
      expect(result.error).toBeNull()
    })
  })

  describe('getPaymentById', () => {
    it('should get a payment transaction by ID successfully', async () => {
      const mockResponse = {
        id: 1,
        idempotency_key: 'test_key_123',
        booking: 100,
        provider: 'payme' as PaymentProvider,
        provider_transaction_id: 'txn_123',
        amount: 100.00,
        currency: 'USD',
        status: 'completed' as PaymentStatus,
        payment_method_token: null,
        provider_response: { success: true },
        error_code: null,
        error_message: null,
        client_ip: '127.0.0.1',
        user_agent: 'test-agent',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      })

      const result = await adapter.getPaymentById(1)

      expect(mockFetch).toHaveBeenCalledWith(
        'http://test-api.com/api/v1/payments/transactions/1/',
        expect.objectContaining({
          credentials: 'include',
        })
      )

      expect(result.data).toEqual(mockResponse)
      expect(result.error).toBeNull()
    })

    it('should handle payment not found error', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        json: async () => ({ error: 'Payment not found' }),
      })

      const result = await adapter.getPaymentById(999)

      expect(result.data).toBeNull()
      expect(result.error).toBe('Payment not found')
    })
  })

  describe('generateIdempotencyKey', () => {
    it('should generate unique idempotency keys', () => {
      const key1 = adapter.generateIdempotencyKey()
      const key2 = adapter.generateIdempotencyKey()

      expect(key1).not.toBe(key2)
      expect(key1).toMatch(/^payment_\d+_[a-z0-9]+$/)
      expect(key2).toMatch(/^payment_\d+_[a-z0-9]+$/)
    })
  })

  describe('getUserAgent', () => {
    it('should return user agent string', () => {
      const userAgent = adapter.getUserAgent()

      expect(typeof userAgent).toBe('string')
      expect(userAgent.length).toBeGreaterThan(0)
    })
  })

  describe('getClientIp', () => {
    it('should fetch client IP address successfully', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ ip: '192.168.1.1' }),
      })

      const ip = await adapter.getClientIp()

      expect(ip).toBe('192.168.1.1')
    })

    it('should handle IP fetch failure gracefully', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'))

      const ip = await adapter.getClientIp()

      expect(ip).toBeNull()
    })
  })
})
