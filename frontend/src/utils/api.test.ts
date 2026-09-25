import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { apiFetch, clearCsrfToken, getCsrfToken, setCsrfToken, fetchAllPages } from './api'
import { AuthAdapter } from '../adapters/authAdapter'

const CSRF_URL = 'http://localhost:8000/api/v1/auth/csrf/'

function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })
}

const csrfFailure = () =>
  jsonResponse({ error: { code: 'error', message: 'CSRF Failed: CSRF token incorrect.', details: {} } }, 403)

describe('apiFetch', () => {
  let mockFetch: ReturnType<typeof vi.fn>

  beforeEach(() => {
    clearCsrfToken()
    mockFetch = vi.fn()
    vi.stubGlobal('fetch', mockFetch)
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  const headersOf = (callIndex: number) => mockFetch.mock.calls[callIndex][1].headers as Record<string, string>

  it('fetches the token from /auth/csrf/ and sends it on POST', async () => {
    mockFetch
      .mockResolvedValueOnce(jsonResponse({ csrf_token: 'tok-1' }))
      .mockResolvedValueOnce(jsonResponse({ id: 1 }, 201))

    const response = await apiFetch('http://api/x/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: '{}',
    })

    expect(response.status).toBe(201)
    expect(mockFetch.mock.calls[0][0]).toBe(CSRF_URL)
    expect(mockFetch.mock.calls[0][1]).toMatchObject({ method: 'GET', credentials: 'include' })
    expect(headersOf(1)).toEqual({ 'Content-Type': 'application/json', 'X-CSRFToken': 'tok-1' })
    expect(mockFetch.mock.calls[1][1].credentials).toBe('include')
  })

  it.each(['PUT', 'PATCH', 'DELETE'])('sends the token on %s', async (method) => {
    setCsrfToken('cached')
    mockFetch.mockResolvedValueOnce(new Response(null, { status: 204 }))

    await apiFetch('http://api/x/', { method })

    expect(mockFetch).toHaveBeenCalledTimes(1)
    expect(headersOf(0)['X-CSRFToken']).toBe('cached')
  })

  it('does not fetch or send a token for GET', async () => {
    mockFetch.mockResolvedValueOnce(jsonResponse([]))

    await apiFetch('http://api/x/', { headers: { 'Content-Type': 'application/json' } })

    expect(mockFetch).toHaveBeenCalledTimes(1)
    expect(headersOf(0)).toEqual({ 'Content-Type': 'application/json' })
    expect(mockFetch.mock.calls[0][1].credentials).toBe('include')
  })

  it('reuses the cached token and shares one lookup between concurrent requests', async () => {
    mockFetch.mockImplementation(async (url: string) =>
      url === CSRF_URL ? jsonResponse({ csrf_token: 'shared' }) : jsonResponse({})
    )

    await Promise.all([
      apiFetch('http://api/a/', { method: 'POST' }),
      apiFetch('http://api/b/', { method: 'POST' }),
    ])
    await apiFetch('http://api/c/', { method: 'DELETE' })

    const csrfCalls = mockFetch.mock.calls.filter(([url]) => url === CSRF_URL)
    expect(csrfCalls).toHaveLength(1)
    expect(headersOf(mockFetch.mock.calls.length - 1)['X-CSRFToken']).toBe('shared')
  })

  it('keeps FormData bodies without adding a Content-Type', async () => {
    setCsrfToken('cached')
    mockFetch.mockResolvedValueOnce(jsonResponse({}, 201))
    const body = new FormData()

    await apiFetch('http://api/photos/', { method: 'POST', body })

    expect(headersOf(0)).toEqual({ 'X-CSRFToken': 'cached' })
    expect(mockFetch.mock.calls[0][1].body).toBe(body)
  })

  it('retries once with a fresh token after a CSRF 403', async () => {
    setCsrfToken('stale')
    mockFetch
      .mockResolvedValueOnce(csrfFailure())
      .mockResolvedValueOnce(jsonResponse({ csrf_token: 'fresh' }))
      .mockResolvedValueOnce(jsonResponse({ ok: true }))

    const response = await apiFetch('http://api/x/', { method: 'POST' })

    expect(response.status).toBe(200)
    expect(headersOf(0)['X-CSRFToken']).toBe('stale')
    expect(mockFetch.mock.calls[1][0]).toBe(CSRF_URL)
    expect(headersOf(2)['X-CSRFToken']).toBe('fresh')
  })

  it('does not retry a permission 403 or loop on repeated CSRF failures', async () => {
    setCsrfToken('tok')
    mockFetch.mockResolvedValueOnce(
      jsonResponse({ error: { code: 'permission_denied', message: 'Hotel-owner role required', details: {} } }, 403)
    )

    const denied = await apiFetch('http://api/x/', { method: 'POST' })
    expect(denied.status).toBe(403)
    expect(mockFetch).toHaveBeenCalledTimes(1)

    mockFetch.mockReset()
    mockFetch
      .mockResolvedValueOnce(csrfFailure())
      .mockResolvedValueOnce(jsonResponse({ csrf_token: 'fresh' }))
      .mockResolvedValueOnce(csrfFailure())

    const failed = await apiFetch('http://api/x/', { method: 'POST' })
    expect(failed.status).toBe(403)
    expect(mockFetch).toHaveBeenCalledTimes(3)
  })

  it('sends the request without a token if /auth/csrf/ is unreachable', async () => {
    mockFetch.mockRejectedValueOnce(new TypeError('Failed to fetch')).mockResolvedValueOnce(jsonResponse({}))

    await apiFetch('http://api/x/', { method: 'POST', headers: { 'Content-Type': 'application/json' } })

    expect(headersOf(1)).toEqual({ 'Content-Type': 'application/json' })
  })
})

describe('CSRF token and session changes', () => {
  let mockFetch: ReturnType<typeof vi.fn>

  beforeEach(() => {
    mockFetch = vi.fn()
    vi.stubGlobal('fetch', mockFetch)
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it.each([
    ['login', (a: AuthAdapter) => a.login({ email: 'a@b.c', password: 'x' })],
    ['verifyOTP', (a: AuthAdapter) => a.verifyOTP({ phone_number: '+998901234567', otp_code: '123456' })],
    ['logout', (a: AuthAdapter) => a.logout()],
    ['register', (a: AuthAdapter) =>
      a.register({ email: 'a@b.c', full_name: 'A B', phone_number: '+998901234567', password: 'x', password_confirm: 'x' })],
  ])('drops the cached token after %s, since Django rotates it', async (_name, call) => {
    setCsrfToken('before')
    mockFetch.mockResolvedValue(jsonResponse({ id: 1 }))

    await call(new AuthAdapter('http://localhost:8000'))

    mockFetch.mockReset()
    mockFetch.mockResolvedValueOnce(jsonResponse({ csrf_token: 'after' }))
    expect(await getCsrfToken()).toBe('after')
  })

  it('does not let a lookup started before logout cache the old token', async () => {
    clearCsrfToken()
    let resolveOld: (r: Response) => void = () => {}
    mockFetch.mockReturnValueOnce(new Promise<Response>((resolve) => { resolveOld = resolve }))
    const oldLookup = getCsrfToken()

    clearCsrfToken()
    resolveOld(jsonResponse({ csrf_token: 'old' }))
    await oldLookup

    mockFetch.mockResolvedValueOnce(jsonResponse({ csrf_token: 'new' }))
    expect(await getCsrfToken()).toBe('new')
  })
})

describe('fetchAllPages', () => {
  let mockFetch: ReturnType<typeof vi.fn>

  beforeEach(() => {
    mockFetch = vi.fn()
    vi.stubGlobal('fetch', mockFetch)
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  const page = (results: unknown[], next: string | null) => jsonResponse({ count: 99, next, previous: null, results })

  it('follows next links and concatenates results', async () => {
    mockFetch
      .mockResolvedValueOnce(page([1, 2], 'http://api/items/?page=2'))
      .mockResolvedValueOnce(page([3], 'http://api/items/?page=3'))
      .mockResolvedValueOnce(page([4], null))

    const result = await fetchAllPages<number>('http://api/items/')

    expect(result).toEqual({ data: [1, 2, 3, 4], error: null, truncated: false })
    expect(mockFetch.mock.calls.map(call => call[0])).toEqual([
      'http://api/items/', 'http://api/items/?page=2', 'http://api/items/?page=3',
    ])
    expect(mockFetch.mock.calls[0][1]).toEqual(expect.objectContaining({ method: 'GET', credentials: 'include' }))
  })

  it('accepts a plain array (non-paginated endpoint)', async () => {
    mockFetch.mockResolvedValueOnce(jsonResponse([1, 2]))

    const result = await fetchAllPages<number>('http://api/items/')

    expect(result).toEqual({ data: [1, 2], error: null, truncated: false })
    expect(mockFetch).toHaveBeenCalledTimes(1)
  })

  it('stops at maxPages and reports truncation', async () => {
    mockFetch
      .mockResolvedValueOnce(page([1], 'http://api/items/?page=2'))
      .mockResolvedValueOnce(page([2], 'http://api/items/?page=3'))
      .mockResolvedValueOnce(page([3], null))

    const result = await fetchAllPages<number>('http://api/items/', { maxPages: 2 })

    expect(result).toEqual({ data: [1, 2], error: null, truncated: true })
    expect(mockFetch).toHaveBeenCalledTimes(2)
  })

  it('does not follow a next link to another origin', async () => {
    mockFetch.mockResolvedValueOnce(page([1], 'http://evil.example/steal/?page=2'))

    const result = await fetchAllPages<number>('http://api/items/')

    expect(result).toEqual({ data: [1], error: null, truncated: true })
    expect(mockFetch).toHaveBeenCalledTimes(1)
  })

  it('returns the parsed error of a failed page', async () => {
    mockFetch.mockResolvedValueOnce(jsonResponse({ error: { code: 'error', message: 'Nope', details: {} } }, 400))

    const result = await fetchAllPages<number>('http://api/items/', { errorMessages: { 401: 'Authentication required' } })

    expect(result.data).toBeNull()
    expect(result.error).toBe('Nope')
  })

  it('uses the status override message', async () => {
    mockFetch.mockResolvedValueOnce(jsonResponse({}, 401))

    const result = await fetchAllPages<number>('http://api/items/', { errorMessages: { 401: 'Authentication required' } })

    expect(result).toEqual({ data: null, error: 'Authentication required', truncated: false })
  })

  it('reports network errors with the given message, or the error text by default', async () => {
    mockFetch.mockRejectedValueOnce(new Error('offline'))
    expect((await fetchAllPages('http://api/items/', { networkErrorMessage: 'Network error occurred' })).error)
      .toBe('Network error occurred')

    mockFetch.mockRejectedValueOnce(new Error('offline'))
    expect((await fetchAllPages('http://api/items/')).error).toBe('offline')
  })
})
