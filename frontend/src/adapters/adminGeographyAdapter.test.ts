import { describe, it, expect, beforeEach, vi } from 'vitest'
import { AdminGeographyAdapter } from './adminGeographyAdapter'
import { setCsrfToken } from '../utils/api'

const fetchMock = vi.fn()
global.fetch = fetchMock

const ok = (body: unknown, status = 200) => ({ ok: true, status, json: async () => body, text: async () => '', clone() { return this } })
const fail = (status: number, body: unknown = {}) => ({ ok: false, status, json: async () => body, text: async () => '', clone() { return this } })

describe('AdminGeographyAdapter', () => {
  let adapter: AdminGeographyAdapter

  beforeEach(() => {
    fetchMock.mockReset()
    setCsrfToken('token')
    adapter = new AdminGeographyAdapter('http://test-api')
  })

  it('lists one kind with search and filters, hidden rows included', async () => {
    fetchMock.mockResolvedValue(ok({ count: 0, next: null, previous: null, results: [] }))
    await adapter.list('regions', { search: 'tash', country: 1 })
    const url = new URL(fetchMock.mock.calls[0][0])
    expect(url.pathname).toBe('/api/v1/admin-panel/geography/regions/')
    expect(url.searchParams.get('search')).toBe('tash')
    expect(url.searchParams.get('country')).toBe('1')
    expect(url.searchParams.get('page_size')).toBe('200')
  })

  it('skips blank filters', async () => {
    fetchMock.mockResolvedValue(ok({ count: 0, next: null, previous: null, results: [] }))
    await adapter.list('countries', { search: '' })
    expect(new URL(fetchMock.mock.calls[0][0]).searchParams.has('search')).toBe(false)
  })

  it('creates a row with POST and the CSRF header', async () => {
    fetchMock.mockResolvedValue(ok({ id: 5 }, 201))
    const body = { country: 1, name_uz: 'Toshkent', name_ru: 'Ташкент', name_en: 'Tashkent' }
    const result = await adapter.create('regions', body)
    const [url, init] = fetchMock.mock.calls[0]
    expect(url).toBe('http://test-api/api/v1/admin-panel/geography/regions/')
    expect(init.method).toBe('POST')
    expect(JSON.parse(init.body)).toEqual(body)
    expect(init.headers['X-CSRFToken']).toBe('token')
    expect(result.error).toBeNull()
  })

  it('edits and hides a row with PATCH', async () => {
    fetchMock.mockResolvedValue(ok({ id: 5, is_active: false }))
    await adapter.update('cities', 5, { is_active: false })
    const [url, init] = fetchMock.mock.calls[0]
    expect(url).toBe('http://test-api/api/v1/admin-panel/geography/cities/5/')
    expect(init.method).toBe('PATCH')
    expect(JSON.parse(init.body)).toEqual({ is_active: false })
  })

  it('deletes a row; 409 (in use) is reported as inUse so the screen can suggest hiding it', async () => {
    fetchMock.mockResolvedValueOnce(ok(null, 204))
    expect(await adapter.remove('cities', 5)).toEqual({ error: null, inUse: false })
    expect(fetchMock.mock.calls[0][1].method).toBe('DELETE')

    fetchMock.mockResolvedValueOnce(fail(409, { error: { message: 'In use' } }))
    const result = await adapter.remove('regions', 6)
    expect(result.inUse).toBe(true)
    expect(result.error).toBeTruthy()
  })

  it('reorders a kind by the list of ids', async () => {
    fetchMock.mockResolvedValue(ok({}))
    await adapter.reorder('countries', [3, 1, 2])
    const [url, init] = fetchMock.mock.calls[0]
    expect(url).toBe('http://test-api/api/v1/admin-panel/geography/countries/reorder/')
    expect(JSON.parse(init.body)).toEqual({ ids: [3, 1, 2] })
  })

  it('returns the first field error of a 400', async () => {
    fetchMock.mockResolvedValue(fail(400, { name_en: ['Already exists.'] }))
    const result = await adapter.create('regions', { country: 1, name_uz: 'a', name_ru: 'b', name_en: 'Tashkent' })
    expect(result.data).toBeNull()
    expect(result.error).toContain('Already exists')
  })

  it('reports a network failure', async () => {
    fetchMock.mockRejectedValue(new Error('offline'))
    expect((await adapter.list('countries', {})).error).toBe('offline')
  })
})
