import { describe, it, expect, beforeEach, vi } from 'vitest'
import { NoShowAdapter } from './noShowAdapter'
import { noShowErrorKey } from '../utils/noShowErrors'

const mockFetch = vi.fn()
global.fetch = mockFetch

function reply(status: number, body?: unknown) {
  mockFetch.mockResolvedValueOnce({ ok: status >= 200 && status < 300, status, json: async () => body })
}

function lastCall() {
  const [url, init] = mockFetch.mock.calls.at(-1) as [string, RequestInit]
  return { url, init }
}

const BASE = 'http://test-api'

describe('NoShowAdapter', () => {
  let adapter: NoShowAdapter

  beforeEach(() => {
    adapter = new NoShowAdapter(BASE)
    mockFetch.mockReset()
    // Unsafe calls first ask for a CSRF token
    mockFetch.mockImplementation(async (url: string) =>
      String(url).includes('/auth/csrf/')
        ? { ok: true, status: 200, json: async () => ({ csrf_token: 'tok' }) }
        : { ok: false, status: 500, json: async () => ({}) },
    )
  })

  describe('owner', () => {
    it('files a report with the comment', async () => {
      reply(201, { id: 5, status: 'pending', comment: 'Guest never came' })
      const result = await adapter.reportNoShow(12, 'Guest never came')
      expect(result.data?.id).toBe(5)
      const { url, init } = lastCall()
      expect(url).toBe(`${BASE}/api/v1/partner/bookings/12/no-show-report/`)
      expect(init.method).toBe('POST')
      expect(JSON.parse(init.body as string)).toEqual({ comment: 'Guest never came' })
    })

    it('returns the server code for a business error', async () => {
      reply(400, { error: 'The report window is closed', code: 'window_closed' })
      const result = await adapter.reportNoShow(12, 'Guest never came')
      expect(result.data).toBeNull()
      expect(result.code).toBe('window_closed')
    })

    it('returns field errors for a bad comment', async () => {
      reply(400, { comment: ['Ensure this field has at least 10 characters.'] })
      const result = await adapter.reportNoShow(12, 'short')
      expect(result.data).toBeNull()
      expect(result.fieldErrors?.comment).toHaveLength(1)
    })

    it('lists own reports with filters and pagination', async () => {
      mockFetch.mockReset()
      reply(200, { count: 1, next: null, previous: null, results: [{ id: 1 }] })
      const result = await adapter.listMyReports({ status: 'pending', property: 3, page: 2 })
      expect(result.data?.count).toBe(1)
      const { url } = lastCall()
      expect(url).toContain('/api/v1/partner/no-show-reports/?')
      for (const part of ['status=pending', 'property=3', 'page=2']) expect(url).toContain(part)
    })

    it('omits empty filters', async () => {
      mockFetch.mockReset()
      reply(200, { count: 0, next: null, previous: null, results: [] })
      await adapter.listMyReports({ status: '' })
      expect(lastCall().url).toBe(`${BASE}/api/v1/partner/no-show-reports/`)
    })

    it('withdraws a report with POST and no body', async () => {
      reply(200, { id: 5, status: 'withdrawn' })
      const result = await adapter.withdrawReport(5)
      expect(result.data?.status).toBe('withdrawn')
      const { url, init } = lastCall()
      expect(url).toBe(`${BASE}/api/v1/partner/no-show-reports/5/withdraw/`)
      expect(init.method).toBe('POST')
      expect(init.body).toBeUndefined()
    })
  })

  describe('staff', () => {
    it('lists the queue with filters', async () => {
      mockFetch.mockReset()
      reply(200, { count: 1, next: null, previous: null, results: [{ id: 9, refund_preview: null }] })
      const result = await adapter.listReports({ status: 'pending', from: '2026-10-01', to: '2026-10-09', page: 1 })
      expect(result.data?.results[0].id).toBe(9)
      const { url } = lastCall()
      expect(url).toContain('/api/v1/admin-panel/no-show-reports/?')
      for (const part of ['status=pending', 'from=2026-10-01', 'to=2026-10-09']) expect(url).toContain(part)
    })

    it.each([
      ['approve', 'approveReport'],
      ['reject', 'rejectReport'],
      ['reverse', 'reverseReport'],
    ] as const)('POSTs a decision comment to %s', async (path, method) => {
      reply(200, { id: 9 })
      await adapter[method](9, 'Checked with the hotel')
      const { url, init } = lastCall()
      expect(url).toBe(`${BASE}/api/v1/admin-panel/no-show-reports/9/${path}/`)
      expect(init.method).toBe('POST')
      expect(JSON.parse(init.body as string)).toEqual({ decision_comment: 'Checked with the hotel' })
    })

    it('returns the code when approval cannot run', async () => {
      reply(400, { error: 'Nights are no longer free', code: 'inventory_unavailable' })
      const result = await adapter.approveReport(9, 'Checked with the hotel')
      expect(result.code).toBe('inventory_unavailable')
    })

    it('maps a missing report to not_found', async () => {
      reply(404, { error: 'Report not found', code: 'not_found' })
      expect((await adapter.rejectReport(9, 'x'.repeat(12))).code).toBe('not_found')
    })

    it('reports a network failure as an error without a code', async () => {
      mockFetch.mockReset()
      mockFetch.mockRejectedValueOnce(new Error('offline'))
      const result = await adapter.listReports()
      expect(result.error).toBe('offline')
      expect(result.code).toBeNull()
    })
  })
})

describe('noShowErrorKey', () => {
  it.each([
    'not_reportable_status', 'too_early', 'window_closed', 'report_exists', 'not_found', 'not_pending',
    'not_decided', 'booking_not_reportable', 'inventory_unavailable', 'refund_refused',
  ])('has a message for %s', (code) => {
    expect(noShowErrorKey(code)).toBe(`noShow.error.${code}`)
  })

  it('uses the comment message for field errors on a comment', () => {
    expect(noShowErrorKey(null, { comment: ['too short'] })).toBe('noShow.error.commentInvalid')
    expect(noShowErrorKey(null, { decision_comment: ['too short'] })).toBe('noShow.error.commentInvalid')
  })

  it('falls back to the generic message', () => {
    expect(noShowErrorKey(null)).toBe('noShow.error.generic')
    expect(noShowErrorKey('something_new')).toBe('noShow.error.generic')
  })
})
