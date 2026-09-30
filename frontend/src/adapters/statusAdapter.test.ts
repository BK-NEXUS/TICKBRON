import { describe, it, expect, beforeEach, vi } from 'vitest'
import { statusAdapter } from './statusAdapter'
import { setCsrfToken } from '../utils/api'

const okJson = (body: unknown) =>
  ({ ok: true, status: 200, json: async () => body, clone() { return this } }) as unknown as Response

const page = { count: 0, next: null, previous: null, results: [], period: 'all' }

describe('statusAdapter', () => {
  const fetchMock = vi.fn()

  beforeEach(() => {
    fetchMock.mockReset()
    fetchMock.mockResolvedValue(okJson(page))
    vi.stubGlobal('fetch', fetchMock)
    setCsrfToken('test-token')
  })

  const calledUrl = (index = 0) => new URL(fetchMock.mock.calls[index][0] as string)

  it('lists countries with period, search and page', async () => {
    const result = await statusAdapter.getCountries({ period: '2026-04', search: 'uz', page: 2 })

    const url = calledUrl()
    expect(url.pathname).toBe('/api/v1/admin-panel/status/countries/')
    expect(url.searchParams.get('period')).toBe('2026-04')
    expect(url.searchParams.get('search')).toBe('uz')
    expect(url.searchParams.get('page')).toBe('2')
    expect(result).toEqual({ data: page, error: null })
    expect(fetchMock.mock.calls[0][1]).toMatchObject({ credentials: 'include' })
  })

  it('leaves out empty filters', async () => {
    await statusAdapter.getCountries({ period: 'all', search: '' })
    expect(calledUrl().search).toBe('?period=all')
  })

  it('encodes the country and region in the path', async () => {
    await statusAdapter.getRegions('Côte d’Ivoire / North', { period: 'all' })
    await statusAdapter.getHotels('Uzbekistan', 'Tashkent Region', { period: '2026' })

    expect(fetchMock.mock.calls[0][0]).toContain(
      `/status/countries/${encodeURIComponent('Côte d’Ivoire / North')}/regions/`)
    expect(calledUrl(1).pathname).toBe('/api/v1/admin-panel/status/countries/Uzbekistan/regions/Tashkent%20Region/hotels/')
  })

  it('loads a hotel with period and year', async () => {
    await statusAdapter.getHotelDetail(7, { period: 'all', year: 2025 })

    const url = calledUrl()
    expect(url.pathname).toBe('/api/v1/admin-panel/status/hotels/7/')
    expect(url.searchParams.get('year')).toBe('2025')
  })

  it('lists users', async () => {
    await statusAdapter.getUsers({ period: '2026', search: 'naz' })
    expect(calledUrl().pathname).toBe('/api/v1/admin-panel/status/users/')
    expect(calledUrl().searchParams.get('search')).toBe('naz')
  })

  it('returns the server error message', async () => {
    fetchMock.mockResolvedValue({
      ok: false, status: 400, json: async () => ({ period: ['period must be "all", a year (YYYY) or a month (YYYY-MM).'] }),
      text: async () => '', clone() { return this },
    } as unknown as Response)

    const result = await statusAdapter.getCountries({ period: 'bad' })

    expect(result.data).toBeNull()
    expect(result.error).toContain('period must be')
  })

  it('returns a message when the network fails', async () => {
    fetchMock.mockRejectedValue(new Error('offline'))
    const result = await statusAdapter.getUsers({ period: 'all' })
    expect(result).toEqual({ data: null, error: 'offline' })
  })

  it('sets a property region with PATCH and the CSRF header', async () => {
    fetchMock.mockResolvedValue(okJson({ id: 3, state: 'Tashkent' }))

    const result = await statusAdapter.setPropertyRegion(3, 'Tashkent')

    const [url, init] = fetchMock.mock.calls[0]
    expect(url).toContain('/api/v1/admin-panel/properties/3/region/')
    expect(init.method).toBe('PATCH')
    expect(JSON.parse(init.body)).toEqual({ state: 'Tashkent' })
    expect(init.headers['X-CSRFToken']).toBe('test-token')
    expect(result.error).toBeNull()
  })

  it('loads the partner Status with period and year', async () => {
    await statusAdapter.getPartnerStatus({ period: '2026-04', year: 2025 })

    const url = calledUrl()
    expect(url.pathname).toBe('/api/v1/partner/status/')
    expect(url.searchParams.get('period')).toBe('2026-04')
    expect(url.searchParams.get('year')).toBe('2025')
  })

  it('partner Status: the year is optional', async () => {
    await statusAdapter.getPartnerStatus({ period: 'all' })
    expect(calledUrl().search).toBe('?period=all')
  })
})
