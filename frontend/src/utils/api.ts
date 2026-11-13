// Barlıq adapterler ushın ortaq fetch wrapper: session cookie ler hám CSRF qorǵawı.
//
// Backend Django session auth tı paydalanadı, ol kirgen session dıń POST/PUT/PATCH/DELETE sın
// X-CSRFToken header sız qabıllamaydı. csrftoken cookie HttpOnly,
// sol sebepli token GET /api/v1/auth/csrf/ tan keledi (qarań .ai/contracts/auth.md).
// Django token di kirgende hám shıqqanda aylandıradı, sol sebepli authAdapter sonda keshti tazalaydı.

import { readApiError } from './errorHandler'
import { getActiveLanguage } from '../i18n/languageChoice'
import { translateNow } from '../i18n/translateNow'
import { API_BASE_URL } from './apiBase'

const UNSAFE_METHODS = new Set(['POST', 'PUT', 'PATCH', 'DELETE'])

let csrfToken: string | null = null
let csrfRequest: Promise<string | null> | null = null
// Hár qayta ornatıwda arttırıladı, sonda kirisiw/shıǵıwdan aldın baslanǵan soraw eski token di keshlemeydi
let csrfGeneration = 0

async function fetchCsrfToken(): Promise<string | null> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/auth/csrf/`, {
      method: 'GET',
      credentials: 'include',
    })
    if (!response.ok) return null
    const data = await response.json()
    return typeof data?.csrf_token === 'string' ? data.csrf_token : null
  } catch {
    return null
  }
}

/** Házirgi CSRF token, bir márte alınadı hám birdey waqıttaǵı shaqırıwshılar ortaq paydalanadı. */
export async function getCsrfToken(): Promise<string | null> {
  if (csrfToken) return csrfToken
  if (!csrfRequest) {
    const generation = csrfGeneration
    csrfRequest = fetchCsrfToken().then((token) => {
      if (generation === csrfGeneration) {
        csrfToken = token
        csrfRequest = null
      }
      return token
    })
  }
  return csrfRequest
}

/** Keshlengen token di tikkeley belgilew (testler, yamasa basqa juwaptan alınǵan token). */
export function setCsrfToken(token: string | null): void {
  csrfGeneration += 1
  csrfToken = token
  csrfRequest = null
}

/** Keshlengen token di umıtıw; keyingi qáwipsiz emes soraw jańasın aladı. Kirgennen/shıqqannan keyin shaqırıń. */
export function clearCsrfToken(): void {
  setCsrfToken(null)
}

function headersToObject(headers: HeadersInit | undefined): Record<string, string> {
  if (!headers) return {}
  if (headers instanceof Headers) return Object.fromEntries(headers.entries())
  if (Array.isArray(headers)) return Object.fromEntries(headers)
  return { ...headers }
}

function withCsrfHeader(init: RequestInit, token: string | null): RequestInit {
  if (!token) return init
  return { ...init, headers: { ...headersToObject(init.headers), 'X-CSRFToken': token } }
}

/** API óz biykar etiwlerin bet tilinde jazadı; header joq bolsa inglizsha jiberedi */
function withLanguageHeader(init: RequestInit): RequestInit {
  const language = getActiveLanguage()
  const headers = headersToObject(init.headers)
  if (language === 'en' || Object.keys(headers).some((name) => name.toLowerCase() === 'accept-language')) return init
  return { ...init, headers: { ...headers, 'Accept-Language': language } }
}

async function isCsrfFailure(response: Response): Promise<boolean> {
  if (response.status !== 403 || typeof response.clone !== 'function') return false
  const body = await response.clone().text().catch(() => '')
  return body.includes('CSRF Failed')
}

/**
 * Credentials hám, qáwipsiz emes metodlar ushın, X-CSRFToken header i menen fetch().
 * CSRF 403 (eski token, mısalı basqa tabtan kirgennen keyin) jańa token menen bir márte qayta uriladı;
 * Django bulardı view islewden aldın biykar etedi, sol sebepli qayta urınıw jazıwdı eki ret islemeydi.
 */
export async function apiFetch(url: string, init: RequestInit = {}): Promise<Response> {
  const options: RequestInit = withLanguageHeader({ credentials: 'include', ...init })
  const method = (options.method || 'GET').toUpperCase()
  if (!UNSAFE_METHODS.has(method)) {
    return fetch(url, options)
  }

  const response = await fetch(url, withCsrfHeader(options, await getCsrfToken()))
  if (!(await isCsrfFailure(response))) {
    return response
  }

  clearCsrfToken()
  return fetch(url, withCsrfHeader(options, await getCsrfToken()))
}

/** DRF PageNumberPagination konverti (backend te PAGE_SIZE 20). */
export interface Paginated<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

/** fetchAllPages alatuǵın betlerdiń eń kóp sanı (20 element hár bet -> 1000 element). */
export const DEFAULT_MAX_PAGES = 50

export interface FetchAllPagesOptions {
  /** Usı sandaǵı betten keyin toqtaw hám truncated: true xabarlaw */
  maxPages?: number
  /** readApiError ke berilgen hár status ushın xabarlar */
  errorMessages?: Record<number, string>
  /** Tarmaq qátelikleri ushın xabar; ádetde taslanǵan qátelik teksti */
  networkErrorMessage?: string
}

export interface FetchAllPagesResult<T> {
  data: T[] | null
  error: string | null
  /** Alınǵannan kóp bet bar bolsa true (maxPages, yamasa basqa origin ge next silteme) */
  truncated: boolean
}

function isPaginated<T>(body: unknown): body is Paginated<T> {
  return typeof body === 'object' && body !== null && Array.isArray((body as Paginated<T>).results)
}

/**
 * Dizim endpoint ine GET hám hár elementti qaytarıw, DRF `next` siltemelerin izlep.
 * Ápiwayı massiv juwapları (betlenbegen endpoint ler) sol qalpında qaytadı.
 * Tek bir origin degi `next` siltemeler izlenedi.
 */
export async function fetchAllPages<T>(url: string, options: FetchAllPagesOptions = {}): Promise<FetchAllPagesResult<T>> {
  const { maxPages = DEFAULT_MAX_PAGES, errorMessages = {}, networkErrorMessage } = options
  // Salıstırmalı mánzil (bos API_BASE_URL) betke qarata oqıladı, sol sebepli origin tekseriwi ele isleydi
  const origin = new URL(url, window.location.href).origin
  const items: T[] = []
  let nextUrl: string | null = url
  let pages = 0

  try {
    while (nextUrl && pages < maxPages) {
      const response = await apiFetch(nextUrl, {
        method: 'GET',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
      })
      if (!response.ok) {
        const apiError = await readApiError(response, errorMessages)
        return { data: null, error: apiError.message, truncated: false }
      }
      const body: unknown = await response.json()
      pages += 1
      if (!isPaginated<T>(body)) {
        return { data: Array.isArray(body) ? (body as T[]) : [], error: null, truncated: false }
      }
      items.push(...body.results)
      nextUrl = body.next
      if (nextUrl && new URL(nextUrl, new URL(url, window.location.href)).origin !== origin) {
        return { data: items, error: null, truncated: true }
      }
    }
  } catch (error) {
    const message = networkErrorMessage ?? (error instanceof Error ? error.message : translateNow('apiError.networkOccurred'))
    return { data: null, error: message, truncated: false }
  }

  return { data: items, error: null, truncated: nextUrl !== null }
}
