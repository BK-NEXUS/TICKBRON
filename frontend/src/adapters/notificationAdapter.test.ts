import { describe, it, expect, beforeEach, vi } from 'vitest'
import { notificationAdapter } from './notificationAdapter'

global.fetch = vi.fn()

const respond = (body: unknown) =>
  vi.mocked(fetch).mockResolvedValueOnce({ ok: true, status: 200, json: async () => body } as Response)

describe('notificationAdapter.list', () => {
  beforeEach(() => vi.mocked(fetch).mockReset())

  it('asks for the first page and says there is another one when the server has a next link', async () => {
    respond({ count: 30, next: 'http://x/?page=2', previous: null, results: [{ id: 1 }] })

    const result = await notificationAdapter.list()

    expect(String(vi.mocked(fetch).mock.calls[0][0])).toMatch(/\/api\/v1\/me\/notifications\/\?page=1$/)
    expect(result.data).toEqual({ items: [{ id: 1 }], hasMore: true })
  })

  it('asks for the requested page and sees the end of the list', async () => {
    respond({ count: 30, next: null, previous: 'http://x/?page=1', results: [{ id: 21 }] })

    const result = await notificationAdapter.list(2)

    expect(String(vi.mocked(fetch).mock.calls[0][0])).toMatch(/\?page=2$/)
    expect(result.data).toEqual({ items: [{ id: 21 }], hasMore: false })
  })
})
