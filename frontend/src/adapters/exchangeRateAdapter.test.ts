import { describe, it, expect, beforeEach, vi } from 'vitest'
import { ExchangeRateAdapter } from './exchangeRateAdapter'
import { setCsrfToken } from '../utils/api'

const fetchMock = vi.fn()
global.fetch = fetchMock

const ok = (body: unknown, status = 200) => ({ ok: true, status, json: async () => body, text: async () => '', clone() { return this } })
const fail = (status: number, body: unknown = {}) => ({ ok: false, status, json: async () => body, text: async () => '', clone() { return this } })

describe('ExchangeRateAdapter', () => {
  let adapter: ExchangeRateAdapter

  beforeEach(() => {
    fetchMock.mockReset()
    setCsrfToken('token')
    adapter = new ExchangeRateAdapter('http://test-api')
  })

  it('loads one page of the rate history, newest first (the backend orders it)', async () => {
    fetchMock.mockResolvedValue(ok({ count: 0, next: null, previous: null, results: [] }))
    await adapter.list({ page: 2 })
    const url = new URL(fetchMock.mock.calls[0][0])
    expect(url.pathname).toBe('/api/v1/admin-panel/exchange-rates/')
    expect(url.searchParams.get('page')).toBe('2')
    expect(url.searchParams.get('page_size')).toBe('20')
  })

  it('loads the status of the rates (super-admin)', async () => {
    fetchMock.mockResolvedValue(ok({ currencies: [] }))
    const result = await adapter.status()
    expect(fetchMock.mock.calls[0][0]).toBe('http://test-api/api/v1/admin-panel/exchange-rates/status/')
    expect(result.data).toEqual({ currencies: [] })
  })

  it('accepts a rejected rate with POST and the CSRF header', async () => {
    fetchMock.mockResolvedValue(ok({ id: 9, status: 'accepted' }, 201))
    const result = await adapter.accept(7)
    const [url, init] = fetchMock.mock.calls[0]
    expect(url).toBe('http://test-api/api/v1/admin-panel/exchange-rates/7/accept/')
    expect(init.method).toBe('POST')
    expect(init.headers['X-CSRFToken']).toBe('token')
    expect(result.error).toBeNull()
  })

  it('returns the status code with the error (400 not rejected, 404 unknown, 409 already accepted)', async () => {
    fetchMock.mockResolvedValue(fail(409, { error: 'A rate for that date is already accepted' }))
    const result = await adapter.accept(7)
    expect(result.data).toBeNull()
    expect(result.status).toBe(409)
    expect(result.error).toContain('already accepted')
  })

  it('reports a network failure', async () => {
    fetchMock.mockRejectedValue(new Error('offline'))
    expect((await adapter.status()).error).toBe('offline')
  })
})
