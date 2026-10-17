import { describe, it, expect, beforeEach, vi } from 'vitest'
import { GeographyAdapter, geographyName } from './geographyAdapter'

const mockFetch = vi.fn()
global.fetch = mockFetch

const tashkent = { id: 3, name_uz: 'Toshkent', name_ru: 'Ташкент', name_en: 'Tashkent' }

describe('geographyName', () => {
  it('picks the name of the page language', () => {
    expect(geographyName(tashkent, 'uz')).toBe('Toshkent')
    expect(geographyName(tashkent, 'ru')).toBe('Ташкент')
    expect(geographyName(tashkent, 'en')).toBe('Tashkent')
  })

  it('falls back to English when the chosen name is blank', () => {
    expect(geographyName({ ...tashkent, name_ru: '' }, 'ru')).toBe('Tashkent')
  })
})

describe('GeographyAdapter', () => {
  let adapter: GeographyAdapter

  beforeEach(() => {
    adapter = new GeographyAdapter('http://test-api')
    mockFetch.mockReset()
  })

  it('loads the countries', async () => {
    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => [{ id: 1, code: 'UZ', currency: 'UZS', ...tashkent, hotel_count: 4 }] })
    const result = await adapter.getCountries()
    expect(mockFetch).toHaveBeenCalledWith('http://test-api/api/v1/geography/countries/', expect.objectContaining({ credentials: 'include' }))
    expect(result.error).toBeNull()
    expect(result.data?.[0].code).toBe('UZ')
  })

  it('loads the regions of a country by its code', async () => {
    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => [] })
    await adapter.getRegions('UZ')
    expect(mockFetch.mock.calls[0][0]).toBe('http://test-api/api/v1/geography/countries/UZ/regions/')
  })

  it('loads the cities of a region by its id', async () => {
    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => [] })
    await adapter.getCities(7)
    expect(mockFetch.mock.calls[0][0]).toBe('http://test-api/api/v1/geography/regions/7/cities/')
  })

  it('returns the API error message', async () => {
    mockFetch.mockResolvedValueOnce({ ok: false, status: 404, json: async () => ({ error: { message: 'Not found' } }), clone() { return this } })
    const result = await adapter.getRegions('XX')
    expect(result.data).toBeNull()
    expect(result.error).toBeTruthy()
  })

  it('reports a network failure as an error', async () => {
    mockFetch.mockRejectedValueOnce(new Error('offline'))
    const result = await adapter.getCountries()
    expect(result.data).toBeNull()
    expect(result.error).toBe('offline')
  })
})
