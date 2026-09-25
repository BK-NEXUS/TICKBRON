// F20: DRF PageNumberPagination (PAGE_SIZE 20) wraps these list endpoints in
// { count, next, previous, results }. The adapters must return every item as a plain array.
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { accountAdapter } from './accountAdapter'
import { AdminAdapter } from './adminAdapter'
import { PartnerAdapter } from './partnerAdapter'

const ACCOUNT_BASE = 'http://localhost:8000'
const ADMIN_BASE = 'http://test-admin'
const PARTNER_BASE = 'http://test-partner'

function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })
}

const admin = new AdminAdapter(ADMIN_BASE)
const partner = new PartnerAdapter(PARTNER_BASE)

const LIST_METHODS: Array<{ name: string; url: string; call: () => Promise<{ data: unknown; error: string | null }> }> = [
  { name: 'accountAdapter.getFavorites', url: `${ACCOUNT_BASE}/api/v1/me/favorites/`, call: () => accountAdapter.getFavorites() },
  { name: 'accountAdapter.getAccountHistory', url: `${ACCOUNT_BASE}/api/v1/me/history/`, call: () => accountAdapter.getAccountHistory() },
  { name: 'accountAdapter.getReviews', url: `${ACCOUNT_BASE}/api/v1/me/reviews/`, call: () => accountAdapter.getReviews() },
  { name: 'adminAdapter.getProperties', url: `${ADMIN_BASE}/api/v1/admin-panel/properties/`, call: () => admin.getProperties() },
  { name: 'adminAdapter.getAmenities', url: `${ADMIN_BASE}/api/v1/admin-panel/amenities/`, call: () => admin.getAmenities() },
  { name: 'adminAdapter.getAmenityCategories', url: `${ADMIN_BASE}/api/v1/admin-panel/amenities/categories/`, call: () => admin.getAmenityCategories() },
  { name: 'partnerAdapter.getProperties', url: `${PARTNER_BASE}/api/v1/partner/properties/`, call: () => partner.getProperties() },
  { name: 'partnerAdapter.getRoomTypes', url: `${PARTNER_BASE}/api/v1/partner/rooms/`, call: () => partner.getRoomTypes() },
  { name: 'partnerAdapter.getRatePlans', url: `${PARTNER_BASE}/api/v1/partner/rates/`, call: () => partner.getRatePlans() },
  { name: 'partnerAdapter.getDateInventory', url: `${PARTNER_BASE}/api/v1/partner/inventory/`, call: () => partner.getDateInventory() },
]

describe('paginated list endpoints (F20)', () => {
  let mockFetch: ReturnType<typeof vi.fn>

  beforeEach(() => {
    mockFetch = vi.fn()
    vi.stubGlobal('fetch', mockFetch)
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it.each(LIST_METHODS)('$name returns the items of every page as one array', async ({ url, call }) => {
    mockFetch
      .mockResolvedValueOnce(jsonResponse({ count: 3, next: `${url}?page=2`, previous: null, results: [{ id: 1 }, { id: 2 }] }))
      .mockResolvedValueOnce(jsonResponse({ count: 3, next: null, previous: url, results: [{ id: 3 }] }))

    const result = await call()

    expect(result.error).toBeNull()
    expect(result.data).toEqual([{ id: 1 }, { id: 2 }, { id: 3 }])
    expect(mockFetch).toHaveBeenCalledTimes(2)
    expect(mockFetch.mock.calls[0][0]).toBe(url)
    expect(mockFetch.mock.calls[1][0]).toBe(`${url}?page=2`)
  })

  it.each(LIST_METHODS)('$name returns the error of a failed page', async ({ url, call }) => {
    mockFetch
      .mockResolvedValueOnce(jsonResponse({ count: 3, next: `${url}?page=2`, previous: null, results: [{ id: 1 }] }))
      .mockResolvedValueOnce(jsonResponse({ error: { code: 'error', message: 'Server exploded', details: {} } }, 500))

    const result = await call()

    expect(result.data).toBeNull()
    expect(result.error).toBeTruthy()
  })
})
