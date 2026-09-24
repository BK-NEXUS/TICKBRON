// Shared fetch wrapper for all adapters: session cookies plus CSRF protection.
//
// The backend uses Django session auth, which rejects POST/PUT/PATCH/DELETE from a
// logged-in session without an X-CSRFToken header. The csrftoken cookie is HttpOnly,
// so the token comes from GET /api/v1/auth/csrf/ (see .ai/contracts/auth.md).
// Django rotates the token on login and logout, so authAdapter clears the cache then.

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const UNSAFE_METHODS = new Set(['POST', 'PUT', 'PATCH', 'DELETE'])

let csrfToken: string | null = null
let csrfRequest: Promise<string | null> | null = null
// Bumped on every reset so a request started before login/logout cannot cache the old token
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

/** Current CSRF token, fetched once and shared by concurrent callers. */
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

/** Set the cached token directly (tests, or a token from another response). */
export function setCsrfToken(token: string | null): void {
  csrfGeneration += 1
  csrfToken = token
  csrfRequest = null
}

/** Forget the cached token; the next unsafe request fetches a fresh one. Call after login/logout. */
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

async function isCsrfFailure(response: Response): Promise<boolean> {
  if (response.status !== 403 || typeof response.clone !== 'function') return false
  const body = await response.clone().text().catch(() => '')
  return body.includes('CSRF Failed')
}

/**
 * fetch() with credentials and, for unsafe methods, the X-CSRFToken header.
 * A CSRF 403 (stale token, e.g. after logging in from another tab) is retried once with a fresh token;
 * Django rejects those before the view runs, so the retry cannot duplicate a write.
 */
export async function apiFetch(url: string, init: RequestInit = {}): Promise<Response> {
  const options: RequestInit = { credentials: 'include', ...init }
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
