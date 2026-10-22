// Super-admin geography management: Country > Region > City.
// Contract: .ai/API_CONTRACT.md, section "Geography: Country > Region > City" (Super-admin only).
import { apiFetch, type Paginated } from '../utils/api'
import { readApiError } from '../utils/errorHandler'
import type { GeographyNames } from './geographyAdapter'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export type GeographyKind = 'countries' | 'regions' | 'cities'

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
  city_count: number
  image_url: string | null
}

export interface AdminCity extends RowBase {
  region: number
  slug: string
}

export type AdminGeographyRow = AdminCountry | AdminRegion | AdminCity

export interface GeographyListParams {
  search?: string
  /** Regions of this country id */
  country?: number
  /** Cities of this region id */
  region?: number
}

/** Fields of a create or edit; the parent and the code of an existing row cannot change. */
export interface GeographyWrite extends Partial<GeographyNames> {
  code?: string
  currency?: string
  country?: number
  region?: number
  is_active?: boolean
  /** Countries and regions only: required when adding, optional when editing */
  image?: File
}

/** JSON, or multipart when a picture is attached (the browser sets the boundary header) */
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
      return { data: null, error: error instanceof Error ? error.message : 'Network error occurred' }
    }
  }

  list<K extends GeographyKind>(kind: K, params: GeographyListParams) {
    const query = new URLSearchParams({ page_size: '200' })
    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined && value !== '') query.set(key, String(value))
    }
    return this.send<Paginated<K extends 'countries' ? AdminCountry : K extends 'regions' ? AdminRegion : AdminCity>>(
      this.url(kind, `?${query}`))
  }

  create(kind: GeographyKind, body: GeographyWrite) {
    return this.send<AdminGeographyRow>(this.url(kind), writeInit('POST', body))
  }

  update(kind: GeographyKind, id: number, body: GeographyWrite) {
    return this.send<AdminGeographyRow>(this.url(kind, `${id}/`), writeInit('PATCH', body))
  }

  /** 409 means the row is in use (children or hotels): the screen then suggests hiding it. */
  async remove(kind: GeographyKind, id: number): Promise<{ error: string | null; inUse: boolean }> {
    try {
      const response = await apiFetch(this.url(kind, `${id}/`), { method: 'DELETE' })
      if (response.ok) return { error: null, inUse: false }
      return { error: (await readApiError(response)).message, inUse: response.status === 409 }
    } catch (error) {
      return { error: error instanceof Error ? error.message : 'Network error occurred', inUse: false }
    }
  }

  reorder(kind: GeographyKind, ids: number[]) {
    return this.send<unknown>(this.url(kind, 'reorder/'), { method: 'POST', body: JSON.stringify({ ids }) })
  }
}

export const adminGeographyAdapter = new AdminGeographyAdapter()
