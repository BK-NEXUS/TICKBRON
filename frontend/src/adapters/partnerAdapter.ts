// Mehmanxana iyesi mehmanxanalardı basqarıwı ushın Partner API adapteri
// Checkpoint 18 degi backend partner endpoint leri menen birlesedi

import { readApiError } from '../utils/errorHandler'
import { apiFetch, fetchAllPages } from '../utils/api'
import { translateNow } from '../i18n/translateNow'
import { API_BASE_URL } from '../utils/apiBase'
import type { CommissionStatement } from './commissionTypes'

// Backend contract tan Property túrleri
/** Hár tildegi (uz, ru, en) mehmanxana atı hám táripleme */
export type PropertyTexts = Partial<Record<'uz' | 'ru' | 'en', { name: string; description: string }>>

export interface PartnerProperty {
  id: number
  /** Mehmanxana atı (inglizsha awdarma, bolmasa qálegen, bolmasa mánzil); tek oqıw */
  name?: string
  translations?: PropertyTexts
  owner: number
  property_type: number
  status: string
  max_guests: number
  bedrooms: number
  bathrooms: number
  address_line1: string
  address_line2?: string
  city: string
  state?: string
  postal_code?: string
  country: string
  latitude?: number
  longitude?: number
  base_price: number
  currency: string
  total_area?: number
  floor_number?: number
  has_elevator: boolean
  has_parking: boolean
  has_wifi: boolean
  has_ac: boolean
  has_heating: boolean
  approved_by?: number
  approved_at?: string
  created_at: string
  updated_at: string
}

export interface CreatePropertyRequest {
  /** Eń keminde atı bar bir til */
  translations: PropertyTexts
  property_type: number
  max_guests: number
  bedrooms: number
  bathrooms: number
  address_line1: string
  address_line2?: string
  /** Geografiya id leri (eski tekst maydanlar country/state/city tek oqıw nusqaları) */
  country_ref: number
  region_ref: number
  postal_code?: string
  latitude?: number
  longitude?: number
  base_price: number
  currency: string
  total_area?: number
  floor_number?: number
  has_elevator: boolean
  has_parking: boolean
  has_wifi: boolean
  has_ac: boolean
  has_heating: boolean
}

export interface UpdatePropertyRequest {
  /** Jiberilgen tiller almastırıladı, qalǵanları qaladı */
  translations?: PropertyTexts
  property_type?: number
  max_guests?: number
  bedrooms?: number
  bathrooms?: number
  address_line1?: string
  address_line2?: string
  country_ref?: number
  region_ref?: number
  postal_code?: string
  latitude?: number
  longitude?: number
  base_price?: number
  currency?: string
  total_area?: number
  floor_number?: number
  has_elevator?: boolean
  has_parking?: boolean
  has_wifi?: boolean
  has_ac?: boolean
  has_heating?: boolean
}

// Backend contract tan Room Type túrleri
export interface PartnerRoomType {
  id: number
  property: number
  name: string
  slug: string
  description: string
  base_occupancy: number
  max_occupancy: number
  base_price: number
  currency: string
  total_rooms: number
  bed_configuration: string
  room_size?: number
  is_vip: boolean
  /** Xona túriniń aktiv súwretleri hám muqabanıń mánzili (súwret joq bolsa null) */
  photos_count: number
  cover_url: string | null
  created_at: string
  updated_at: string
}

export interface CreateRoomTypeRequest {
  property: number
  name: string
  /** Formalar taslap ketedi: server onı attan jasaydı */
  slug?: string
  description: string
  base_occupancy: number
  max_occupancy: number
  base_price: number
  currency: string
  total_rooms: number
  bed_configuration: string
  room_size?: number
  is_vip: boolean
}

export interface UpdateRoomTypeRequest {
  name?: string
  slug?: string
  description?: string
  base_occupancy?: number
  max_occupancy?: number
  base_price?: number
  currency?: string
  total_rooms?: number
  bed_configuration?: string
  room_size?: number
  is_vip?: boolean
}

// Backend contract tan Rate Plan túrleri
export interface PartnerRatePlan {
  id: number
  room_type: number
  name: string
  slug: string
  rate_type: string
  description: string
  base_price: number
  currency: string
  /** R16: iye hár valyutada kirgizgen baha (kod -> summa qatarı); tiykarǵısı `currency` */
  prices?: Record<string, string>
  min_nights: number
  max_nights: number
  is_active: boolean
  cancellation_policy: string
  deposit_required: boolean
  deposit_percentage?: number
  advance_booking_days?: number
  created_at: string
  updated_at: string
}

export interface CreateRatePlanRequest {
  room_type: number
  name: string
  /** Formalar taslap ketedi: server onı attan jasaydı */
  slug?: string
  rate_type: string
  description: string
  /** R16: hár valyutadaǵı baha; backend tiykarǵı bahanı (mehmanxana valyutası) sonnan aladı */
  prices: Record<string, string>
  min_nights: number
  max_nights: number
  is_active: boolean
  cancellation_policy: string
  deposit_required: boolean
  deposit_percentage?: number
  advance_booking_days?: number
}

export interface UpdateRatePlanRequest {
  name?: string
  slug?: string
  rate_type?: string
  description?: string
  /** R16: hár valyutadaǵı baha (backend tiykarǵı bahanı sonnan belgileydi) */
  prices?: Record<string, string>
  min_nights?: number
  max_nights?: number
  is_active?: boolean
  cancellation_policy?: string
  deposit_required?: boolean
  deposit_percentage?: number
  advance_booking_days?: number
}

// Backend contract tan Date Inventory túrleri
export interface PartnerDateInventory {
  id: number
  rate_plan: number
  date: string
  available_rooms: number
  booked_rooms: number
  price: number
  currency: string
  is_available: boolean
  minimum_stay: number | null // null: usı sana ushın shek belgilenbegen
  maximum_stay: number | null
  notes?: string
  created_at: string
  updated_at: string
}

export interface CreateDateInventoryRequest {
  rate_plan: number
  date: string
  available_rooms: number
  price: number
  currency: string
  is_available: boolean
  minimum_stay: number
  maximum_stay: number
  notes?: string
}

export interface UpdateDateInventoryRequest {
  available_rooms?: number
  price?: number
  currency?: string
  is_available?: boolean
  minimum_stay?: number
  maximum_stay?: number
  notes?: string
}

// Backend contract tan Room Inventory túrleri (RoomInventory, audit #31): xona
// túriniń haqıyqıy, ortaq fizikalıq xona sanı. DateInventory (joqarıda) ele bahanı
// hám hár rate plan nıń óz qaǵıydaların saqlaydı.
export interface PartnerRoomInventory {
  id: number
  room_type: number
  date: string
  available_rooms: number
  booked_rooms: number
  remaining_rooms: number
  is_available: boolean
}

export interface CreateRoomInventoryRequest {
  room_type: number
  date: string
  available_rooms: number
  is_available?: boolean
}

export interface UpdateRoomInventoryRequest {
  available_rooms?: number
  is_available?: boolean
}

/** Bir rate plan nıń kúnlik bahaları; eki sana da kiredi */
export interface GetDateInventoryParams {
  rate_plan?: number
  date_from?: string
  date_to?: string
}

export interface GetRoomInventoryParams {
  room_type?: number
  date_from?: string
  date_to?: string
}

/** date_to kirmeydi, bronnıń check_in/check_out ı sıyaqlı kelisim. */
export interface BulkRoomInventoryRequest {
  room_type: number
  date_from: string
  date_to: string
  available_rooms?: number
  is_available?: boolean
}

/** date_to kirmeydi, bronnıń check_in/check_out ı sıyaqlı kelisim. */
export interface BulkPriceRequest {
  rate_plan: number
  date_from: string
  date_to: string
  price: number
}

// Backend contract tan sırtqı bron blok túrleri (RoomBlock, 3.5): TICKBRON broni joq
// sana aralıǵında satıwdan alınǵan xonalar.
export interface PartnerBlock {
  id: number
  room_type: number
  date_from: string
  date_to: string
  rooms: number
  note: string
  created_by: number
  created_at: string
}

/** date_to kirmeydi, bronnıń check_in/check_out ı sıyaqlı kelisim. */
export interface CreateBlockRequest {
  room_type: number
  date_from: string
  date_to: string
  rooms: number
  note: string
}

// Backend contract tan Photo Upload túrleri
export interface PropertyPhoto {
  id: number
  photo: string
  photo_url: string | null
  photo_type: string
  caption: string | null
  is_primary: boolean
  display_order: number
  alt_text: string | null
}

export interface UpdatePhotoRequest {
  caption?: string
  alt_text?: string
  photo_type?: string
  is_primary?: true
}

/** Súwret basqarıwshısına bir mehmanxana yamasa bir xona túri ushın kerek shaqırıwlar */
export interface PhotoApi {
  list(): Promise<ApiResponse<PropertyPhoto[]>>
  upload(data: UploadPhotoRequest): Promise<ApiResponse<PropertyPhoto>>
  update(photoId: number, data: UpdatePhotoRequest): Promise<ApiResponse<PropertyPhoto>>
  remove(photoId: number): Promise<ApiResponse<null>>
}

export interface PartnerPropertyType {
  id: number
  name: string
  slug: string
}

/**
 * Iyeniń mehmanxanalarınıń biriniń ashıq sharhı (GET /api/v1/partner/reviews/): sharh jazıwshı "Aziz K.", hesh qashan mánzil
 * emes
 */
export interface OwnerReview {
  id: number
  property: number
  property_name: string
  reviewer: string
  stay_month: string | null
  overall_rating: number
  title: string
  comment: string
  created_at: string
  owner_reply: string
  replied_at: string | null
}

export interface OwnerReviewsPage {
  count: number
  hasMore: boolean
  results: OwnerReview[]
}

/**
 * Iyeniń mehmanxanasınıń bannerdegi bir reklaması: qalay isleydi hám adamlar qalay juwap berdi. Baha joq: ol staff ta qaladı.
 */
export interface OwnerPromotion {
  id: number
  property: { id: number; name: string }
  start_date: string
  end_date: string
  status: 'scheduled' | 'active' | 'paused' | 'ended' | 'cancelled'
  paid: boolean
  is_shown_now: boolean
  blocked_reason: 'hotel_not_active' | 'outside_scope' | null
  impressions: number
  clicks: number
  click_rate: string | null
  /** Ashıq soraw "mehmanxana keyingi ay ushın tóledi me?": reklama `deadline` ǵa shekem kórinip turadı */
  renewal: { ends_on: string; deadline: string; days_left: number } | null
}

export interface OwnerPromotionsPage {
  count: number
  hasMore: boolean
  results: OwnerPromotion[]
}

export interface AssignedPlace {
  country_ref: number | null
  region_ref: number | null
}

export interface UploadPhotoRequest {
  photo: File
  photo_type: string
  caption?: string
  is_primary?: boolean
  display_order?: number
  alt_text?: string
}

// Backend contract tan Partner Booking túrleri
export interface PartnerBooking {
  id: number
  guest: number
  guest_name: string
  property: number
  property_name: string
  status: string
  payment_status: string
  check_in: string
  check_out: string
  number_of_nights: number
  guest_count: number
  total_price: number
  currency: string
  special_requests?: string
  confirmation_code: string
  created_at: string
  updated_at: string
  /** R12b: iye mehmann kelmegeni haqqında ele xabarlay alatuǵın waqıt true */
  can_report_no_show?: boolean
  /** Esabat berile alatuǵın sońǵı kún (YYYY-MM-DD); esabat berip bolmaytuǵın bolsa null */
  report_deadline?: string | null
}

// API Response túrleri
export interface ApiResponse<T> {
  data: T | null
  error: string | null
}

class PartnerAdapter {
  private baseUrl: string

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl
  }

  /** Betlerge bólingen dizim endpoint ine GET hám hár bettiń elementlerin qaytarıw */
  private async requestAll<T>(endpoint: string): Promise<ApiResponse<T[]>> {
    const { data, error } = await fetchAllPages<T>(`${this.baseUrl}${endpoint}`, {
      errorMessages: { 401: translateNow('apiError.authRequired'), 403: 'Hotel-owner role required', 404: translateNow('apiError.notFound') },
    })
    return { data, error }
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<{ data: T | null; error: string | null }> {
    const url = `${this.baseUrl}${endpoint}`
    
    const defaultOptions: RequestInit = {
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
      },
      ...options,
    }

    try {
      const response = await apiFetch(url, defaultOptions)
      
      if (!response.ok) {
        const apiError = await readApiError(response, { 401: translateNow('apiError.authRequired'), 403: 'Hotel-owner role required', 404: translateNow('apiError.notFound') })
        return { data: null, error: apiError.message }
      }

      // 204 No Content di islew (DELETE ámelleri)
      if (response.status === 204) {
        return { data: null as T, error: null }
      }

      const data = await response.json()
      return { data, error: null }
    } catch (error) {
      return {
        data: null,
        error: error instanceof Error ? error.message : translateNow('apiError.networkOccurred'),
      }
    }
  }

  // Mehmanxanalardı basqarıw metodları

  /**
   * Jańa mehmanxana jaratıw
   * POST /api/v1/partner/properties/ endpoint i menen birlesedi
   */
  async createProperty(propertyData: CreatePropertyRequest): Promise<ApiResponse<PartnerProperty>> {
    return this.request<PartnerProperty>('/api/v1/partner/properties/', {
      method: 'POST',
      body: JSON.stringify(propertyData),
    })
  }

  /**
   * Mehmanxana iyesiniń mehmanxanaların dizimlew
   * GET /api/v1/partner/properties/ endpoint i menen birlesedi
   */
  async getProperties(): Promise<ApiResponse<PartnerProperty[]>> {
    return this.requestAll<PartnerProperty>('/api/v1/partner/properties/')
  }

  /**
   * Mehmanxanani jańalaw
   * PATCH /api/v1/partner/properties/{id}/ endpoint i menen birlesedi
   */
  async updateProperty(id: number, propertyData: UpdatePropertyRequest): Promise<ApiResponse<PartnerProperty>> {
    return this.request<PartnerProperty>(`/api/v1/partner/properties/${id}/`, {
      method: 'PATCH',
      body: JSON.stringify(propertyData),
    })
  }

  /**
   * Mehmanxananı óshiriw (soft delete)
   * DELETE /api/v1/partner/properties/{id}/ endpoint i menen birlesedi
   */
  async deleteProperty(id: number): Promise<ApiResponse<null>> {
    return this.request<null>(`/api/v1/partner/properties/${id}/`, {
      method: 'DELETE',
    })
  }

  // Xona túrin basqarıw metodları

  /**
   * Jańa xona túri jaratıw
   * POST /api/v1/partner/rooms/ endpoint i menen birlesedi
   */
  async createRoomType(roomTypeData: CreateRoomTypeRequest): Promise<ApiResponse<PartnerRoomType>> {
    return this.request<PartnerRoomType>('/api/v1/partner/rooms/', {
      method: 'POST',
      body: JSON.stringify(roomTypeData),
    })
  }

  /**
   * Mehmanxana iyesiniń xona túrlerin dizimlew
   * GET /api/v1/partner/rooms/ endpoint i menen birlesedi
   */
  async getRoomTypes(): Promise<ApiResponse<PartnerRoomType[]>> {
    return this.requestAll<PartnerRoomType>('/api/v1/partner/rooms/')
  }

  /**
   * Xona túrin jańalaw
   * PATCH /api/v1/partner/rooms/{id}/ endpoint i menen birlesedi
   */
  async updateRoomType(id: number, roomTypeData: UpdateRoomTypeRequest): Promise<ApiResponse<PartnerRoomType>> {
    return this.request<PartnerRoomType>(`/api/v1/partner/rooms/${id}/`, {
      method: 'PATCH',
      body: JSON.stringify(roomTypeData),
    })
  }

  /**
   * Xona túrin óshiriw (soft delete)
   * DELETE /api/v1/partner/rooms/{id}/ endpoint i menen birlesedi
   */
  async deleteRoomType(id: number): Promise<ApiResponse<null>> {
    return this.request<null>(`/api/v1/partner/rooms/${id}/`, {
      method: 'DELETE',
    })
  }

  // Rate plan di basqarıw metodları

  /**
   * Jańa rate plan jaratıw
   * POST /api/v1/partner/rates/ endpoint i menen birlesedi
   */
  async createRatePlan(ratePlanData: CreateRatePlanRequest): Promise<ApiResponse<PartnerRatePlan>> {
    return this.request<PartnerRatePlan>('/api/v1/partner/rates/', {
      method: 'POST',
      body: JSON.stringify(ratePlanData),
    })
  }

  /**
   * Mehmanxana iyesiniń rate planların dizimlew
   * GET /api/v1/partner/rates/ endpoint i menen birlesedi
   */
  async getRatePlans(): Promise<ApiResponse<PartnerRatePlan[]>> {
    return this.requestAll<PartnerRatePlan>('/api/v1/partner/rates/')
  }

  /**
   * Rate plan dı jańalaw
   * PATCH /api/v1/partner/rates/{id}/ endpoint i menen birlesedi
   */
  async updateRatePlan(id: number, ratePlanData: UpdateRatePlanRequest): Promise<ApiResponse<PartnerRatePlan>> {
    return this.request<PartnerRatePlan>(`/api/v1/partner/rates/${id}/`, {
      method: 'PATCH',
      body: JSON.stringify(ratePlanData),
    })
  }

  /**
   * Rate plan dı óshiriw (soft delete)
   * DELETE /api/v1/partner/rates/{id}/ endpoint i menen birlesedi
   */
  async deleteRatePlan(id: number): Promise<ApiResponse<null>> {
    return this.request<null>(`/api/v1/partner/rates/${id}/`, {
      method: 'DELETE',
    })
  }

  // Date inventory di basqarıw metodları

  /**
   * Date inventory jaratıw
   * POST /api/v1/partner/inventory/ endpoint i menen birlesedi
   */
  async createDateInventory(inventoryData: CreateDateInventoryRequest): Promise<ApiResponse<PartnerDateInventory>> {
    return this.request<PartnerDateInventory>('/api/v1/partner/inventory/', {
      method: 'POST',
      body: JSON.stringify(inventoryData),
    })
  }

  /**
   * Mehmanxana iyesiniń date inventory sın dizimlew
   * GET /api/v1/partner/inventory/ endpoint i menen birlesedi
   */
  async getDateInventory(params: GetDateInventoryParams = {}): Promise<ApiResponse<PartnerDateInventory[]>> {
    const search = new URLSearchParams()
    if (params.rate_plan !== undefined) search.append('rate_plan', String(params.rate_plan))
    if (params.date_from) search.append('date_from', params.date_from)
    if (params.date_to) search.append('date_to', params.date_to)
    const query = search.toString()
    return this.requestAll<PartnerDateInventory>(`/api/v1/partner/inventory/${query ? `?${query}` : ''}`)
  }

  /**
   * Date inventory di jańalaw
   * PATCH /api/v1/partner/inventory/{id}/ endpoint i menen birlesedi
   */
  async updateDateInventory(id: number, inventoryData: UpdateDateInventoryRequest): Promise<ApiResponse<PartnerDateInventory>> {
    return this.request<PartnerDateInventory>(`/api/v1/partner/inventory/${id}/`, {
      method: 'PATCH',
      body: JSON.stringify(inventoryData),
    })
  }

  /**
   * Date inventory di óshiriw (soft delete)
   * DELETE /api/v1/partner/inventory/{id}/ endpoint i menen birlesedi
   */
  async deleteDateInventory(id: number): Promise<ApiResponse<null>> {
    return this.request<null>(`/api/v1/partner/inventory/${id}/`, {
      method: 'DELETE',
    })
  }

  /**
   * Bir rate plan nıń túngi bahasın sana aralıǵı boyınsha belgilew (3.7 kóp bahanı ózgertiw)
   * POST /api/v1/partner/inventory/bulk-price/ endpoint i menen birlesedi
   */
  async bulkSetPrice(data: BulkPriceRequest): Promise<ApiResponse<PartnerDateInventory[]>> {
    return this.request<PartnerDateInventory[]>('/api/v1/partner/inventory/bulk-price/', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  // Xona inventory sın basqarıw metodları (RoomInventory, audit #31)

  /**
   * Xona inventory sın jaratıw
   * POST /api/v1/partner/room-inventory/ endpoint i menen birlesedi
   */
  async createRoomInventory(data: CreateRoomInventoryRequest): Promise<ApiResponse<PartnerRoomInventory>> {
    return this.request<PartnerRoomInventory>('/api/v1/partner/room-inventory/', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  /**
   * Mehmanxana iyesiniń xona inventory sın dizimlew, ıqtıyarıy room_type/date_from/date_to boyınsha filterlengen
   * GET /api/v1/partner/room-inventory/ endpoint i menen birlesedi
   */
  async getRoomInventory(params: GetRoomInventoryParams = {}): Promise<ApiResponse<PartnerRoomInventory[]>> {
    const search = new URLSearchParams()
    if (params.room_type !== undefined) search.append('room_type', String(params.room_type))
    if (params.date_from) search.append('date_from', params.date_from)
    if (params.date_to) search.append('date_to', params.date_to)
    const query = search.toString()
    return this.requestAll<PartnerRoomInventory>(`/api/v1/partner/room-inventory/${query ? `?${query}` : ''}`)
  }

  /**
   * Xona inventory sın jańalaw
   * PATCH /api/v1/partner/room-inventory/{id}/ endpoint i menen birlesedi
   */
  async updateRoomInventory(id: number, data: UpdateRoomInventoryRequest): Promise<ApiResponse<PartnerRoomInventory>> {
    return this.request<PartnerRoomInventory>(`/api/v1/partner/room-inventory/${id}/`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    })
  }

  /**
   * Xona túri ushın available_rooms hám/yamasa is_available di sana aralıǵı boyınsha belgilew (3.6 kalendar)
   * POST /api/v1/partner/room-inventory/bulk/ endpoint i menen birlesedi
   */
  async bulkSetRoomInventory(data: BulkRoomInventoryRequest): Promise<ApiResponse<PartnerRoomInventory[]>> {
    return this.request<PartnerRoomInventory[]>('/api/v1/partner/room-inventory/bulk/', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  // Sırtqı bron bloklarınıń metodları (RoomBlock, 3.5)

  /**
   * Sırtqı bron blokın jaratıw
   * POST /api/v1/partner/blocks/ endpoint i menen birlesedi
   */
  async createBlock(data: CreateBlockRequest): Promise<ApiResponse<PartnerBlock>> {
    return this.request<PartnerBlock>('/api/v1/partner/blocks/', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  /**
   * Mehmanxana iyesiniń blokların dizimlew, ıqtıyarıy room_type boyınsha filterlengen
   * GET /api/v1/partner/blocks/ endpoint i menen birlesedi
   */
  async getBlocks(params: { room_type?: number } = {}): Promise<ApiResponse<PartnerBlock[]>> {
    const search = new URLSearchParams()
    if (params.room_type !== undefined) search.append('room_type', String(params.room_type))
    const query = search.toString()
    return this.requestAll<PartnerBlock>(`/api/v1/partner/blocks/${query ? `?${query}` : ''}`)
  }

  /**
   * Blokti óshiriw (biykar etiw): bloklanǵan xonalardı qaytaradı
   * DELETE /api/v1/partner/blocks/{id}/ endpoint i menen birlesedi
   */
  async deleteBlock(id: number): Promise<ApiResponse<null>> {
    return this.request<null>(`/api/v1/partner/blocks/${id}/`, {
      method: 'DELETE',
    })
  }

  /**
   * Mehmanxana óz bronlarınıń birindegi mehmannıń kelgenin aytadı (mehmanxanada naqd).
   * POST /api/v1/partner/bookings/{id}/arrived/ endpoint i menen birlesedi
   */
  async markGuestArrived(bookingId: number): Promise<ApiResponse<{ id: number; arrived_at: string }>> {
    return this.request<{ id: number; arrived_at: string }>(`/api/v1/partner/bookings/${bookingId}/arrived/`, {
      method: 'POST',
    })
  }

  // Súwret júklew metodları

  /** Eki túrdegi súwret paydalanatuǵın multipart POST */
  private async postPhoto(url: string, photoData: UploadPhotoRequest, notFound: string): Promise<ApiResponse<PropertyPhoto>> {
    const formData = new FormData()
    formData.append('photo', photoData.photo)
    formData.append('photo_type', photoData.photo_type)
    if (photoData.caption) formData.append('caption', photoData.caption)
    if (photoData.is_primary !== undefined) formData.append('is_primary', photoData.is_primary.toString())
    if (photoData.display_order !== undefined) formData.append('display_order', photoData.display_order.toString())
    if (photoData.alt_text) formData.append('alt_text', photoData.alt_text)

    try {
      const response = await apiFetch(`${this.baseUrl}${url}`, {
        method: 'POST',
        credentials: 'include',
        body: formData,
      })

      if (!response.ok) {
        const apiError = await readApiError(response, { 401: translateNow('apiError.authRequired'), 403: 'Hotel-owner role required', 404: notFound })
        return { data: null, error: apiError.message }
      }

      const data = await response.json()
      return { data, error: null }
    } catch (error) {
      return {
        data: null,
        error: error instanceof Error ? error.message : translateNow('apiError.networkOccurred'),
      }
    }
  }

  /**
   * Mehmanxana súwretin júklew
   * POST /api/v1/partner/properties/{id}/photos/ endpoint i menen birlesedi
   */
  async uploadPropertyPhoto(propertyId: number, photoData: UploadPhotoRequest): Promise<ApiResponse<PropertyPhoto>> {
    return this.postPhoto(`/api/v1/partner/properties/${propertyId}/photos/`, photoData, 'Property not found')
  }

  /** GET /api/v1/partner/property-types/: hár mehmanxana túri, ele hesh bir mehmanxana paydalanbaǵanları da */
  async getPropertyTypes(): Promise<ApiResponse<PartnerPropertyType[]>> {
    return this.request<PartnerPropertyType[]>('/api/v1/partner/property-types/')
  }

  /**
   * Iyeniń mehmanxanalarınıń tastıyıqlanǵan sharhlarınıń bir beti (barlıǵı, yamasa `propertyId` penen biri), eń jańası
   * birinshi
   */
  async getReviews({ propertyId, page = 1 }: { propertyId?: number; page?: number } = {}): Promise<ApiResponse<OwnerReviewsPage>> {
    const params = new URLSearchParams({ page: String(page) })
    if (propertyId) params.set('property', String(propertyId))
    const { data, error } = await this.request<{ count: number; next: string | null; results: OwnerReview[] }>(
      `/api/v1/partner/reviews/?${params.toString()}`)
    return data
      ? { data: { count: data.count, hasMore: Boolean(data.next), results: data.results }, error: null }
      : { data: null, error }
  }

  /** GET /api/v1/partner/commission/: iyeniń procenti, aylar hám (bir jıllıq akkaunt ushın) jıllıq jıynaqlar */
  async getCommission(): Promise<ApiResponse<CommissionStatement>> {
    return this.request<CommissionStatement>('/api/v1/partner/commission/')
  }

  /** Iyeniń mehmanxanaları reklamalarınıń bir beti, eń jańası birinshi (ıqtıyarıy tek bir status) */
  async getPromotions({ status, page = 1 }: { status?: OwnerPromotion['status']; page?: number } = {}): Promise<ApiResponse<OwnerPromotionsPage>> {
    const params = new URLSearchParams({ page: String(page) })
    if (status) params.set('status', status)
    const { data, error } = await this.request<{ count: number; next: string | null; results: OwnerPromotion[] }>(
      `/api/v1/partner/promotions/?${params.toString()}`)
    return data
      ? { data: { count: data.count, hasMore: Boolean(data.next), results: data.results }, error: null }
      : { data: null, error }
  }

  /** POST /api/v1/partner/reviews/{id}/reply/: sharhqa ashıq juwaptı jazıw yamasa almastırıw */
  async replyToReview(id: number, text: string): Promise<ApiResponse<OwnerReview>> {
    return this.request<OwnerReview>(`/api/v1/partner/reviews/${id}/reply/`, { method: 'POST', body: JSON.stringify({ text }) })
  }

  /** DELETE /api/v1/partner/reviews/{id}/reply/: juwaptı qaytarıp alıw */
  async deleteReviewReply(id: number): Promise<ApiResponse<null>> {
    return this.request<null>(`/api/v1/partner/reviews/${id}/reply/`, { method: 'DELETE' })
  }

  /** GET /api/v1/partner/assigned-place/: super admin usı akkauntqa bergen orın (joq bolsa hámmesi null) */
  async getAssignedPlace(): Promise<ApiResponse<AssignedPlace>> {
    return this.request<AssignedPlace>('/api/v1/partner/assigned-place/')
  }

  /** GET /api/v1/partner/properties/{id}/photos/ (ápiwayı dizim, muqaba hám tártip saqlanǵanday) */
  async getPropertyPhotos(propertyId: number): Promise<ApiResponse<PropertyPhoto[]>> {
    return this.request<PropertyPhoto[]>(`/api/v1/partner/properties/${propertyId}/photos/`)
  }

  /** PATCH /api/v1/partner/properties/{id}/photos/{photoId}/ (is_primary tek true ǵa qoyılıwı múmkin) */
  async updatePropertyPhoto(propertyId: number, photoId: number, data: UpdatePhotoRequest): Promise<ApiResponse<PropertyPhoto>> {
    return this.request<PropertyPhoto>(`/api/v1/partner/properties/${propertyId}/photos/${photoId}/`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    })
  }

  /** DELETE /api/v1/partner/properties/{id}/photos/{photoId}/ */
  async deletePropertyPhoto(propertyId: number, photoId: number): Promise<ApiResponse<null>> {
    return this.request<null>(`/api/v1/partner/properties/${propertyId}/photos/${photoId}/`, {
      method: 'DELETE',
    })
  }

  /** GET /api/v1/partner/rooms/{id}/photos/ (ápiwayı dizim, muqaba hám tártip saqlanǵanday) */
  async getRoomPhotos(roomTypeId: number): Promise<ApiResponse<PropertyPhoto[]>> {
    return this.request<PropertyPhoto[]>(`/api/v1/partner/rooms/${roomTypeId}/photos/`)
  }

  /** POST /api/v1/partner/rooms/{id}/photos/ (multipart; birinshi súwret muqaba boladı) */
  async uploadRoomPhoto(roomTypeId: number, photoData: UploadPhotoRequest): Promise<ApiResponse<PropertyPhoto>> {
    return this.postPhoto(`/api/v1/partner/rooms/${roomTypeId}/photos/`, photoData, 'Room type not found')
  }

  /** PATCH /api/v1/partner/rooms/{id}/photos/{photoId}/ (is_primary tek true ǵa qoyılıwı múmkin) */
  async updateRoomPhoto(roomTypeId: number, photoId: number, data: UpdatePhotoRequest): Promise<ApiResponse<PropertyPhoto>> {
    return this.request<PropertyPhoto>(`/api/v1/partner/rooms/${roomTypeId}/photos/${photoId}/`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    })
  }

  /** DELETE /api/v1/partner/rooms/{id}/photos/{photoId}/ */
  async deleteRoomPhoto(roomTypeId: number, photoId: number): Promise<ApiResponse<null>> {
    return this.request<null>(`/api/v1/partner/rooms/${roomTypeId}/photos/${photoId}/`, { method: 'DELETE' })
  }

  // Partner bronları metodları

  /**
   * Mehmanxana iyesiniń mehmanxanaları bronların dizimlew
   * GET /api/v1/partner/bookings/ endpoint i menen birlesedi
   */
  async getPartnerBookings(status?: string, paymentStatus?: string, reportableOnly = false): Promise<ApiResponse<PartnerBooking[]>> {
    const params = new URLSearchParams()
    if (status) params.append('status', status)
    if (paymentStatus) params.append('payment_status', paymentStatus)
    if (reportableOnly) params.append('reportable', 'true')

    const endpoint = `/api/v1/partner/bookings/${params.toString() ? `?${params.toString()}` : ''}`
    return this.request<PartnerBooking[]>(endpoint)
  }
}

// Singleton nusqasın eksport etiw
export const partnerAdapter = new PartnerAdapter()

// Testlew ushın klasstı eksport etiw
export { PartnerAdapter }
