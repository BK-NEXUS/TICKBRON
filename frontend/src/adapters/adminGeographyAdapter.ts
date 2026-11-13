// Super-admin geografiya basqarıwı: Country > Region > City.
// Contract: .ai/API_CONTRACT.md, "Geography: Country > Region > City" bólimi (tek super-admin).
import { apiFetch, type Paginated } from '../utils/api'
import { readApiError } from '../utils/errorHandler'
import type { GeographyNames } from './geographyAdapter'
import { translateNow } from '../i18n/translateNow'
import { API_BASE_URL } from '../utils/apiBase'

export type GeographyKind = 'countries' | 'regions'

interface RowBase extends GeographyNames {
  id: number
  is_active: boolean
  sort_order: number
  hotel_count: number
}

export interface AdminCountry extends RowBase {
  code: string
  currency: string
  region_count: number
  image_url: string | null
}

export interface AdminRegion extends RowBase {
  country: number
  slug: string
  image_url: string | null
}

export type AdminGeographyRow = AdminCountry | AdminRegion

export interface GeographyListParams {
  search?: string
  /** Usı mámleket id sine tiyisli regionlar */
  country?: number
}

/** Jaratıw yamasa ózgertiw maydanları; bar qatardıń ata-anası hám kodın ózgertip bolmaydı. */
export interface GeographyWrite extends Partial<GeographyNames> {
  code?: string
  currency?: string
  country?: number
  is_active?: boolean
  /** Qosqanda májbúriy, ózgertkende ıqtıyarıy */
  image?: File
}

/** JSON, yamasa súwret qosılǵanda multipart (brauzer boundary header in ózi belgileydi) */
function writeInit(method: string, body: GeographyWrite): RequestInit {
  if (!body.image) return { method, body: JSON.stringify(body) }
  const form = new FormData()
  for (const [key, value] of Object.entries(body)) {
    if (value !== undefined) form.append(key, value instanceof File ? value : String(value))
  }
  return { method, body: form }
}

type Result<T> = { data: T | null; error: string | null }

export class AdminGeographyAdapter {
  constructor(private baseUrl: string = API_BASE_URL) {}

  private url(kind: GeographyKind, suffix = '') {
    return `${this.baseUrl}/api/v1/admin-panel/geography/${kind}/${suffix}`
  }

  private async send<T>(url: string, init: RequestInit = {}): Promise<Result<T>> {
    try {
      const json = typeof init.body === 'string'
      const response = await apiFetch(url, json ? { ...init, headers: { 'Content-Type': 'application/json' } } : init)
      if (!response.ok) return { data: null, error: (await readApiError(response)).message }
      return { data: response.status === 204 ? null : await response.json(), error: null }
    } catch (error) {
      return { data: null, error: error instanceof Error ? error.message : translateNow('apiError.networkOccurred') }
    }
  }

  list<K extends GeographyKind>(kind: K, params: GeographyListParams) {
    const query = new URLSearchParams({ page_size: '200' })
    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined && value !== '') query.set(key, String(value))
    }
    return this.send<Paginated<K extends 'countries' ? AdminCountry : AdminRegion>>(
      this.url(kind, `?${query}`))
  }

  create(kind: GeographyKind, body: GeographyWrite) {
    return this.send<AdminGeographyRow>(this.url(kind), writeInit('POST', body))
  }

  update(kind: GeographyKind, id: number, body: GeographyWrite) {
    return this.send<AdminGeographyRow>(this.url(kind, `${id}/`), writeInit('PATCH', body))
  }

  /** 409 qatar paydalanılıp atırǵanın bildiredi (balalar yamasa mehmanxanalar): ekran sonda onı jasırıwdı usınadı. */
  async remove(kind: GeographyKind, id: number): Promise<{ error: string | null; inUse: boolean }> {
    try {
      const response = await apiFetch(this.url(kind, `${id}/`), { method: 'DELETE' })
      if (response.ok) return { error: null, inUse: false }
      return { error: (await readApiError(response)).message, inUse: response.status === 409 }
    } catch (error) {
      return { error: error instanceof Error ? error.message : translateNow('apiError.networkOccurred'), inUse: false }
    }
  }

  reorder(kind: GeographyKind, ids: number[]) {
    return this.send<unknown>(this.url(kind, 'reorder/'), { method: 'POST', body: JSON.stringify({ ids }) })
  }
}

export const adminGeographyAdapter = new AdminGeographyAdapter()
