import { describe, it, expect, beforeEach, vi } from 'vitest'
import { statusAdapter } from './statusAdapter'
import { setCsrfToken } from '../utils/api'

const okJson = (body: unknown) =>
  ({ ok: true, status: 200, json: async () => body, clone() { return this } }) as unknown as Response

const csvResponse = (disposition: string | null) =>
  ({
    ok: true,
    status: 200,
    blob: async () => new Blob(['﻿hotel_id,hotel\n1,Hotel A'], { type: 'text/csv' }),
    headers: new Headers(disposition ? { 'Content-Disposition': disposition } : {}),
    clone() { return this },
  }) as unknown as Response

const errorResponse = (status: number, body: unknown) =>
  ({ ok: false, status, json: async () => body, text: async () => '', clone() { return this } }) as unknown as Response

const money = [{ currency: 'UZS', amount: '1500000.00' }, { currency: 'USD', amount: '70.00' }]

const totals = {
  bookings: 12, stayed: 9, counted: 12, guests: 31, unique_customers: 10, nights: 40, room_nights: 52,
  no_show: 1, no_show_reported: 0, fully_refunded: 2, upcoming: 3, revenue: money, booking_value: money,
  booking_status: { pending: 1, confirmed: 3, completed: 9, cancelled: 2, expired: 1, no_show: 1, no_show_reported: 0 },
}

const window = { from: '2026-10-07', to: '2026-10-07', counted: { bookings: 1, guests: 2 }, stayed: { bookings: 0, guests: 0 } }
const reconciliation = {
  today: window, this_week: window, this_month: window, this_year: window,
  all_time: { ...window, from: null, to: null },
}

const hotelDetail = {
  hotel: { id: 7, name: 'Hotel A', status: 'active' },
  period: 'last_7_days',
  period_range: { from: '2026-10-01', to: '2026-10-07' },
  totals,
  granularity: 'day',
  series: [{ period: '2026-10-01', start: '2026-10-01', bookings: 1, guests: 2, nights: 3, stayed: 1, revenue: money }],
  reconciliation,
  year: 2026,
  available_years: [2026],
  monthly: [],
}

describe('statusAdapter R12a', () => {
  const fetchMock = vi.fn()

  beforeEach(() => {
    fetchMock.mockReset()
    fetchMock.mockResolvedValue(okJson({}))
    vi.stubGlobal('fetch', fetchMock)
    setCsrfToken('test-token')
  })

  const calledUrl = (index = 0) => new URL(fetchMock.mock.calls[index][0] as string)

  it('lists admin hotels with period, filters, ordering and paging', async () => {
    const body = { count: 1, next: null, previous: null, results: [], period: 'this_year', period_range: { from: '2026-01-01', to: '2026-12-31' }, ordering: '-revenue' }
    fetchMock.mockResolvedValue(okJson(body))

    const result = await statusAdapter.getAdminHotels({
      period: 'this_year', search: 'hilton', ordering: '-revenue', page: 2, pageSize: 50,
    })

    const url = calledUrl()
    expect(url.pathname).toBe('/api/v1/admin-panel/status/hotels/')
    expect(Object.fromEntries(url.searchParams)).toEqual({
      period: 'this_year', search: 'hilton', ordering: '-revenue', page: '2', page_size: '50',
    })
    expect(result).toEqual({ data: body, error: null })
  })

  it('sends from and to only for the custom period', async () => {
    await statusAdapter.getAdminHotels({ period: 'custom', from: '2026-01-01', to: '2026-03-01' })
    await statusAdapter.getAdminHotels({ period: 'last_7_days', from: '2026-01-01', to: '2026-03-01' })

    expect(calledUrl(0).searchParams.get('from')).toBe('2026-01-01')
    expect(calledUrl(0).searchParams.get('to')).toBe('2026-03-01')
    expect(calledUrl(1).searchParams.has('from')).toBe(false)
    expect(calledUrl(1).searchParams.has('to')).toBe(false)
  })

  it('loads a hotel detail with granularity and keeps the reconciliation block', async () => {
    fetchMock.mockResolvedValue(okJson(hotelDetail))

    const result = await statusAdapter.getHotelDetail(7, { period: 'last_7_days', granularity: 'day' })

    expect(calledUrl().searchParams.get('granularity')).toBe('day')
    expect(result.data?.reconciliation.all_time.from).toBeNull()
    expect(result.data?.series[0].stayed).toBe(1)
  })

  it('loads a user detail with period and history page', async () => {
    await statusAdapter.getUserDetail(5, { period: 'custom', from: '2026-01-01', to: '2026-02-01', page: 3 })

    const url = calledUrl()
    expect(url.pathname).toBe('/api/v1/admin-panel/status/users/5/')
    expect(Object.fromEntries(url.searchParams)).toEqual({ period: 'custom', from: '2026-01-01', to: '2026-02-01', page: '3' })
  })

  it('shows the backend message for an invalid custom range', async () => {
    fetchMock.mockResolvedValue(errorResponse(400, { period: ['"to" must not be before "from".'] }))

    const result = await statusAdapter.getAdminHotels({ period: 'custom', from: '2026-03-01', to: '2026-01-01' })

    expect(result.data).toBeNull()
    expect(result.error).toContain('must not be before')
  })

  it('maps 404 of an unknown user to a clear message', async () => {
    fetchMock.mockResolvedValue(errorResponse(404, {}))
    const result = await statusAdapter.getUserDetail(999, { period: 'all' })
    expect(result).toEqual({ data: null, error: 'Not found' })
  })

  it('loads the owner summary with series and reconciliation', async () => {
    await statusAdapter.getPartnerStatus({ period: 'last_30_days', granularity: 'week' })

    const url = calledUrl()
    expect(url.pathname).toBe('/api/v1/partner/status/')
    expect(url.searchParams.get('granularity')).toBe('week')
  })

  it('loads an owner hotel and shows "not found" for another owner hotel', async () => {
    fetchMock.mockResolvedValueOnce(okJson(hotelDetail))
    await statusAdapter.getPartnerHotel(7, { period: 'all', granularity: 'year' })
    expect(calledUrl().pathname).toBe('/api/v1/partner/status/hotels/7/')

    fetchMock.mockResolvedValueOnce(errorResponse(404, {}))
    const other = await statusAdapter.getPartnerHotel(8, { period: 'all' })
    expect(other).toEqual({ data: null, error: 'Not found' })
  })

  it('loads owner arrivals for a day, a hotel and a page', async () => {
    const body = {
      count: 1, next: null, previous: null, day: 'tomorrow', date: '2026-10-08',
      results: [{
        id: 1, reference: 'TB-1', property: { id: 7, name: 'Hotel A' }, guest_name: 'Aziz K.', room_types: ['Double'],
        rooms: 1, nights: 2, guests: 2, check_in: '2026-10-08', check_out: '2026-10-10', special_requests: '', phone_last4: '1234',
      }],
    }
    fetchMock.mockResolvedValue(okJson(body))

    const result = await statusAdapter.getPartnerArrivals({ day: 'tomorrow', property: 7, page: 2 })

    const url = calledUrl()
    expect(url.pathname).toBe('/api/v1/partner/status/arrivals/')
    expect(Object.fromEntries(url.searchParams)).toEqual({ day: 'tomorrow', property: '7', page: '2' })
    expect(result.data?.results[0].phone_last4).toBe('1234')
  })

  describe('CSV export', () => {
    it('downloads the hotels CSV as a blob through apiFetch, not a link', async () => {
      fetchMock.mockResolvedValue(csvResponse('attachment; filename="status_hotels.csv"'))

      const result = await statusAdapter.exportAdminHotels({ period: 'this_year', ordering: '-guests', search: 'a' })

      const [url, init] = fetchMock.mock.calls[0]
      const parsed = new URL(url as string)
      expect(parsed.pathname).toBe('/api/v1/admin-panel/status/hotels/')
      expect(parsed.searchParams.get('export')).toBe('csv')
      expect(parsed.searchParams.get('ordering')).toBe('-guests')
      expect(parsed.searchParams.has('page')).toBe(false)
      expect(init).toMatchObject({ credentials: 'include' })
      expect(result.error).toBeNull()
      expect(result.data?.filename).toBe('status_hotels.csv')
      expect(result.data?.blob).toBeInstanceOf(Blob)
    })

    it('falls back to a default file name without Content-Disposition', async () => {
      fetchMock.mockResolvedValue(csvResponse(null))
      const result = await statusAdapter.exportUsers({ period: 'all' })
      expect(calledUrl().pathname).toBe('/api/v1/admin-panel/status/users/')
      expect(result.data?.filename).toBe('status_users.csv')
    })

    it('exports a user history and the owner reconciliation', async () => {
      fetchMock.mockResolvedValue(csvResponse(null))

      await statusAdapter.exportUserHistory(5, { period: '2026-04' })
      await statusAdapter.exportPartnerReconciliation({ period: 'all' })

      expect(calledUrl(0).pathname).toBe('/api/v1/admin-panel/status/users/5/')
      expect(calledUrl(0).searchParams.get('export')).toBe('csv')
      expect(calledUrl(1).pathname).toBe('/api/v1/partner/status/')
      expect(calledUrl(1).searchParams.get('export')).toBe('csv')
    })

    it('reports a failed export with the server message', async () => {
      fetchMock.mockResolvedValue(errorResponse(403, {}))
      const result = await statusAdapter.exportAdminHotels({ period: 'all' })
      expect(result.data).toBeNull()
      expect(result.error).toBe('Admin or staff role required')
    })

    it('reports a network failure', async () => {
      fetchMock.mockRejectedValue(new Error('offline'))
      const result = await statusAdapter.exportUsers({ period: 'all' })
      expect(result).toEqual({ data: null, error: 'offline' })
    })
  })
})
