// Hotel promotions (R10): the public banner endpoints and the super-admin management endpoints.
// Contract: .ai/API_CONTRACT.md, section "R10: hotel promotions".
import { apiFetch } from '../utils/api'
import { readApiError } from '../utils/errorHandler'
import type { Property } from './propertyAdapter'
import { translateNow } from '../i18n/translateNow'
import { API_BASE_URL } from '../utils/apiBase'

/** A search card plus the id the click counter needs and the pictures of the banner (at most 10; may be empty) */
export type PromotedProperty = Property & { promotion_id: number; promo_photos?: string[] }

export type PromotionStatus = 'scheduled' | 'active' | 'paused' | 'ended' | 'cancelled'
export type PromotionBlockedReason = 'hotel_not_active' | 'outside_scope' | null

export interface HotelSearchRow {
  id: number
  name: string
  city: string
  status: string
  has_running_promotion: boolean
}

/** One picture put on an ad */
export interface AdPhoto {
  id: number
  photo_url: string | null
  display_order: number
}

/** One region of the advertising panel: ads running and waiting in it, and the hotels running them */
export interface PromotionRegion {
  id: number
  country_code: string
  name_uz: string
  name_ru: string
  name_en: string
  running: number
  waiting: number
  hotels: { id: number; name: string }[]
}

export interface AdminPromotion {
  id: number
  property: { id: number; name: string; city: string; status: string }
  start_date: string
  end_date: string
  priority: number
  country_ref: number | null
  region_ref: number | null
  city_ref: number | null
  price_amount: string | null
  price_currency: string
  note: string
  paid: boolean
  paid_at: string | null
  status: PromotionStatus
  cancelled_reason: string
  is_shown_now: boolean
  blocked_reason: PromotionBlockedReason
  total_impressions: number
  total_clicks: number
  photos: AdPhoto[]
  photos_count: number
  created_at: string
}

export interface PromotionListParams {
  q?: string
  region?: number
  status?: string
  paid?: string
  from?: string
  to?: string
  ordering?: string
  page?: number
}

export interface PromotionList {
  count: number
  next: string | null
  previous: string | null
  results: AdminPromotion[]
}

export interface PromotionInput {
  property: number
  start_date: string
  end_date: string
  priority?: number
  price_amount?: string | null
  price_currency?: string
  note?: string
}

export type PromotionChanges = Partial<Omit<PromotionInput, 'property'>>

export interface PromotionStatsDay {
  date: string
  impressions: number
  clicks: number
  ctr: number | null
}

export interface PromotionStats {
  days: PromotionStatsDay[]
  totals: { impressions: number; clicks: number; ctr: number | null }
}

/** `code` is the backend's stable error name (e.g. `overlap`) so screens can translate it. */
export interface PromotionResult<T> {
  data: T | null
  error: string | null
  code: string | null
}

const ADMIN = '/api/v1/admin-panel'
// Getters: the text is chosen when an error happens, in the language the page is in then
const STATUS_MESSAGES = {
  get 401() { return translateNow('apiError.authRequired') },
  get 403() { return translateNow('apiError.adminRequired') },
  404: 'Promotion not found',
}

function withQuery(path: string, params: Record<string, string | number | undefined>): string {
  const query = new URLSearchParams()
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== '') query.append(key, String(value))
  }
  const text = query.toString()
  return text ? `${path}?${text}` : path
}

export class PromotionAdapter {
  private baseUrl: string

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<PromotionResult<T>> {
    try {
      const response = await apiFetch(`${this.baseUrl}${endpoint}`, {
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        ...options,
      })
      if (!response.ok) {
        const apiError = await readApiError(response, STATUS_MESSAGES)
        return { data: null, error: apiError.message, code: apiError.code ?? null }
      }
      if (response.status === 204) return { data: null, error: null, code: null }
      return { data: (await response.json()) as T, error: null, code: null }
    } catch (error) {
      return { data: null, error: error instanceof Error ? error.message : translateNow('apiError.networkOccurred'), code: null }
    }
  }

  private send<T>(endpoint: string, method: 'POST' | 'PATCH', body?: unknown): Promise<PromotionResult<T>> {
    return this.request<T>(endpoint, { method, body: body === undefined ? undefined : JSON.stringify(body) })
  }

  // Public

  /** Banners for the home page. Advertising must never break a page, so failures give an empty list. */
  async getHomePromotions(country?: number): Promise<PromotionResult<PromotedProperty[]>> {
    const result = await this.request<{ results?: PromotedProperty[] }>(
      withQuery('/api/v1/promotions/home/', { country }),
    )
    return { data: result.data?.results ?? [], error: result.error, code: result.code }
  }

  /** Counts a banner click. Fire and forget: a failure is never shown to the guest. */
  async trackClick(promotionId: number): Promise<void> {
    await this.send(`/api/v1/promotions/${promotionId}/click/`, 'POST')
  }

  // Super-admin

  async searchHotels(query: string): Promise<PromotionResult<HotelSearchRow[]>> {
    const result = await this.request<{ results: HotelSearchRow[] }>(
      withQuery(`${ADMIN}/promotion-hotels/`, { q: query }),
    )
    return { data: result.data?.results ?? null, error: result.error, code: result.code }
  }

  listPromotions(params: PromotionListParams = {}): Promise<PromotionResult<PromotionList>> {
    return this.request<PromotionList>(withQuery(`${ADMIN}/promotions/`, { ...params }))
  }

  createPromotion(input: PromotionInput): Promise<PromotionResult<AdminPromotion>> {
    return this.send(`${ADMIN}/promotions/`, 'POST', input)
  }

  updatePromotion(id: number, changes: PromotionChanges): Promise<PromotionResult<AdminPromotion>> {
    return this.send(`${ADMIN}/promotions/${id}/`, 'PATCH', changes)
  }

  pausePromotion(id: number): Promise<PromotionResult<AdminPromotion>> {
    return this.send(`${ADMIN}/promotions/${id}/pause/`, 'POST')
  }

  resumePromotion(id: number): Promise<PromotionResult<AdminPromotion>> {
    return this.send(`${ADMIN}/promotions/${id}/resume/`, 'POST')
  }

  markPromotionPaid(id: number): Promise<PromotionResult<AdminPromotion>> {
    return this.send(`${ADMIN}/promotions/${id}/mark-paid/`, 'POST')
  }

  cancelPromotion(id: number, reason: string): Promise<PromotionResult<AdminPromotion>> {
    return this.send(`${ADMIN}/promotions/${id}/cancel/`, 'POST', { reason })
  }

  /** Every region with the ads running and waiting in it (the advertising panel by region) */
  getRegionPanel(): Promise<PromotionResult<PromotionRegion[]>> {
    return this.request<PromotionRegion[]>(`${ADMIN}/promotions/regions/`)
  }

  getPromotionPhotos(id: number): Promise<PromotionResult<AdPhoto[]>> {
    return this.request<AdPhoto[]>(`${ADMIN}/promotions/${id}/photos/`)
  }

  /** Multipart upload of one picture; the server refuses an eleventh and anything that is not an image */
  async uploadPromotionPhoto(id: number, file: File): Promise<PromotionResult<AdPhoto>> {
    const body = new FormData()
    body.append('photo', file)
    try {
      const response = await apiFetch(`${this.baseUrl}${ADMIN}/promotions/${id}/photos/`, {
        method: 'POST', credentials: 'include', body,
      })
      if (!response.ok) {
        const apiError = await readApiError(response, STATUS_MESSAGES)
        return { data: null, error: apiError.message, code: apiError.code ?? null }
      }
      return { data: (await response.json()) as AdPhoto, error: null, code: null }
    } catch (error) {
      return { data: null, error: error instanceof Error ? error.message : translateNow('apiError.networkOccurred'), code: null }
    }
  }

  deletePromotionPhoto(id: number, photoId: number): Promise<PromotionResult<null>> {
    return this.request<null>(`${ADMIN}/promotions/${id}/photos/${photoId}/`, { method: 'DELETE' })
  }

  getPromotionStats(id: number, range: { from?: string; to?: string } = {}): Promise<PromotionResult<PromotionStats>> {
    return this.request<PromotionStats>(withQuery(`${ADMIN}/promotions/${id}/stats/`, range))
  }
}

export const promotionAdapter = new PromotionAdapter()
