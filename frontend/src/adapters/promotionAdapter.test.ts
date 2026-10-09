import { describe, it, expect, beforeEach, vi } from 'vitest'
import { PromotionAdapter } from './promotionAdapter'

const mockFetch = vi.fn()
global.fetch = mockFetch

function reply(status: number, body?: unknown) {
  mockFetch.mockResolvedValueOnce({
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
  })
}

function lastCall() {
  const [url, init] = mockFetch.mock.calls.at(-1) as [string, RequestInit]
  return { url, init }
}

describe('PromotionAdapter', () => {
  let adapter: PromotionAdapter

  beforeEach(() => {
    adapter = new PromotionAdapter('http://test-api')
    mockFetch.mockReset()
    // Unsafe calls first ask for a CSRF token
    mockFetch.mockImplementation(async (url: string) =>
      String(url).includes('/auth/csrf/')
        ? { ok: true, status: 200, json: async () => ({ csrf_token: 'tok' }) }
        : { ok: false, status: 500, json: async () => ({}) },
    )
  })

  describe('public', () => {
    it('loads the home banners', async () => {
      mockFetch.mockReset()
      reply(200, { results: [{ id: 5, promotion_id: 9 }] })
      const result = await adapter.getHomePromotions()
      expect(result.data).toEqual([{ id: 5, promotion_id: 9 }])
      expect(result.error).toBeNull()
      expect(lastCall().url).toBe('http://test-api/api/v1/promotions/home/')
    })

    it('passes the country filter', async () => {
      mockFetch.mockReset()
      reply(200, { results: [] })
      await adapter.getHomePromotions(3)
      expect(lastCall().url).toBe('http://test-api/api/v1/promotions/home/?country=3')
    })

    it('returns an empty list and an error message on failure, never throws', async () => {
      mockFetch.mockReset()
      mockFetch.mockRejectedValueOnce(new Error('offline'))
      const result = await adapter.getHomePromotions()
      expect(result.data).toEqual([])
      expect(result.error).toBe('offline')
    })

    it('treats a missing results key as an empty list', async () => {
      mockFetch.mockReset()
      reply(200, {})
      expect((await adapter.getHomePromotions()).data).toEqual([])
    })

    it('trackClick posts to the click endpoint and never throws', async () => {
      mockFetch.mockReset()
      mockFetch.mockImplementation(async (url: string) =>
        String(url).includes('/auth/csrf/')
          ? { ok: true, status: 200, json: async () => ({ csrf_token: 'tok' }) }
          : { ok: true, status: 204, json: async () => undefined },
      )
      await expect(adapter.trackClick(12)).resolves.toBeUndefined()
      expect(lastCall().url).toBe('http://test-api/api/v1/promotions/12/click/')
      expect(lastCall().init.method).toBe('POST')
    })

    it('trackClick swallows network errors', async () => {
      mockFetch.mockReset()
      mockFetch.mockRejectedValue(new Error('offline'))
      await expect(adapter.trackClick(12)).resolves.toBeUndefined()
    })
  })

  describe('admin', () => {
    it('searches hotels by name', async () => {
      mockFetch.mockReset()
      reply(200, { results: [{ id: 1, name: 'Alpha', city: 'Samarkand', status: 'active', has_running_promotion: false }] })
      const result = await adapter.searchHotels('alp ha')
      expect(result.data?.[0].name).toBe('Alpha')
      expect(lastCall().url).toBe('http://test-api/api/v1/admin-panel/promotion-hotels/?q=alp+ha')
    })

    it('lists promotions with filters and pagination', async () => {
      mockFetch.mockReset()
      reply(200, { count: 1, next: null, previous: null, results: [{ id: 4 }] })
      const result = await adapter.listPromotions({ q: 'alpha', status: 'active', paid: 'false', page: 2, ordering: '-clicks' })
      expect(result.data?.count).toBe(1)
      const { url } = lastCall()
      expect(url).toContain('/api/v1/admin-panel/promotions/?')
      for (const part of ['q=alpha', 'status=active', 'paid=false', 'page=2', 'ordering=-clicks']) {
        expect(url).toContain(part)
      }
    })

    it('omits empty filters', async () => {
      mockFetch.mockReset()
      reply(200, { count: 0, next: null, previous: null, results: [] })
      await adapter.listPromotions({ q: '', status: '' })
      expect(lastCall().url).toBe('http://test-api/api/v1/admin-panel/promotions/')
    })

    it('creates a promotion with a JSON body', async () => {
      reply(201, { id: 7, status: 'scheduled' })
      const result = await adapter.createPromotion({
        property: 3, start_date: '2026-10-10', end_date: '2026-10-16', priority: 10,
        price_amount: '2500000', price_currency: 'UZS', note: 'Invoice 7',
      })
      expect(result.data?.id).toBe(7)
      const { url, init } = lastCall()
      expect(url).toBe('http://test-api/api/v1/admin-panel/promotions/')
      expect(init.method).toBe('POST')
      expect(JSON.parse(init.body as string)).toMatchObject({ property: 3, priority: 10 })
    })

    it('returns the server error code so the screen can translate it', async () => {
      reply(400, { error: 'This hotel already has a promotion in these dates', code: 'overlap' })
      const result = await adapter.createPromotion({ property: 3, start_date: '2026-10-10', end_date: '2026-10-16' })
      expect(result.data).toBeNull()
      expect(result.code).toBe('overlap')
      expect(result.error).toContain('already has a promotion')
    })

    it('updates with PATCH', async () => {
      reply(200, { id: 7, priority: 50 })
      await adapter.updatePromotion(7, { priority: 50 })
      const { url, init } = lastCall()
      expect(url).toBe('http://test-api/api/v1/admin-panel/promotions/7/')
      expect(init.method).toBe('PATCH')
    })

    it.each([
      ['pause', 'pausePromotion'],
      ['resume', 'resumePromotion'],
      ['mark-paid', 'markPromotionPaid'],
    ] as const)('POSTs to %s', async (path, method) => {
      reply(200, { id: 7 })
      await adapter[method](7)
      const { url, init } = lastCall()
      expect(url).toBe(`http://test-api/api/v1/admin-panel/promotions/7/${path}/`)
      expect(init.method).toBe('POST')
    })

    it('cancels with a reason', async () => {
      reply(200, { id: 7, status: 'cancelled' })
      await adapter.cancelPromotion(7, 'Client withdrew')
      const { url, init } = lastCall()
      expect(url).toBe('http://test-api/api/v1/admin-panel/promotions/7/cancel/')
      expect(JSON.parse(init.body as string)).toEqual({ reason: 'Client withdrew' })
    })

    it('reads the statistics with a date range', async () => {
      mockFetch.mockReset()
      reply(200, { days: [], totals: { impressions: 0, clicks: 0, ctr: null } })
      const result = await adapter.getPromotionStats(7, { from: '2026-10-01', to: '2026-10-09' })
      expect(result.data?.totals.ctr).toBeNull()
      expect(lastCall().url).toBe('http://test-api/api/v1/admin-panel/promotions/7/stats/?from=2026-10-01&to=2026-10-09')
    })

    it('maps 403 to a friendly message', async () => {
      mockFetch.mockReset()
      reply(403, { detail: 'You do not have permission to perform this action.' })
      const result = await adapter.listPromotions()
      expect(result.data).toBeNull()
      expect(result.error).toBeTruthy()
    })

    it('reports a network failure as an error', async () => {
      mockFetch.mockReset()
      mockFetch.mockRejectedValueOnce(new Error('offline'))
      const result = await adapter.listPromotions()
      expect(result.error).toBe('offline')
      expect(result.code).toBeNull()
    })
  })
})
