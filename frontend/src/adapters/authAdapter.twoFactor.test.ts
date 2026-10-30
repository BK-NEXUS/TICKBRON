import { describe, it, expect, beforeEach, vi } from 'vitest'
import { AuthAdapter } from './authAdapter'

const USER = { id: 1, email: 'admin@example.com', two_factor_enabled: true }

describe('AuthAdapter two-step sign-in', () => {
  let adapter: AuthAdapter
  let mockFetch: ReturnType<typeof vi.fn>

  const answer = (body: unknown, ok = true, status = 200) =>
    mockFetch.mockResolvedValueOnce({ ok, status, json: async () => body, headers: new Headers() })
  const sentBody = (call = 0) => JSON.parse(mockFetch.mock.calls[call][1].body)

  beforeEach(() => {
    adapter = new AuthAdapter('http://test-api')
    mockFetch = vi.fn()
    global.fetch = mockFetch
  })

  it('tells the page that the password was right but a code is needed', async () => {
    answer({ two_factor_required: true })

    const result = await adapter.login({ email: 'admin@example.com', password: 'x' })

    expect(result).toEqual({ success: true, twoFactorRequired: true })
  })

  it('sends the app code to the second step and returns the user', async () => {
    answer(USER)

    const result = await adapter.loginTwoFactor({ code: '123456' })

    expect(mockFetch.mock.calls[0][0]).toBe('http://test-api/api/v1/auth/login/2fa/')
    expect(sentBody()).toEqual({ code: '123456' })
    expect(result.success).toBe(true)
    expect(result.user?.email).toBe('admin@example.com')
  })

  it('sends a backup code under its own name', async () => {
    answer(USER)

    await adapter.loginTwoFactor({ backupCode: 'ab12c-34d56' })

    expect(sentBody()).toEqual({ backup_code: 'ab12c-34d56' })
  })

  it('shows why the second step failed', async () => {
    answer({ detail: 'Invalid credentials.' }, false, 401)

    const result = await adapter.loginTwoFactor({ code: '000000' })

    expect(result.success).toBe(false)
    expect(result.error).toBeTruthy()
  })

  it('asks for a new secret and returns the link for the QR code', async () => {
    answer({ otpauth_uri: 'otpauth://totp/TICKBRON:a?secret=ABC', secret: 'ABC' })

    const result = await adapter.startTwoFactorSetup()

    expect(mockFetch.mock.calls[0][0]).toBe('http://test-api/api/v1/auth/2fa/setup/')
    expect(result).toEqual({ success: true, otpauthUri: 'otpauth://totp/TICKBRON:a?secret=ABC', secret: 'ABC' })
  })

  it('confirms the first code and returns the backup codes', async () => {
    answer({ backup_codes: ['ab12c-34d56'] })

    const result = await adapter.confirmTwoFactorSetup('123456')

    expect(mockFetch.mock.calls[0][0]).toBe('http://test-api/api/v1/auth/2fa/confirm/')
    expect(sentBody()).toEqual({ code: '123456' })
    expect(result).toEqual({ success: true, backupCodes: ['ab12c-34d56'] })
  })

  it('returns the server message when the confirm code is wrong', async () => {
    answer({ detail: 'The code is not right.' }, false, 400)

    const result = await adapter.confirmTwoFactorSetup('000000')

    expect(result.success).toBe(false)
    expect(result.backupCodes).toBeUndefined()
    expect(result.error).toBe('The code is not right.')
  })

  it('reports a network failure instead of throwing', async () => {
    mockFetch.mockRejectedValueOnce(new Error('offline'))

    const result = await adapter.startTwoFactorSetup()

    expect(result).toEqual({ success: false, error: 'offline' })
  })
})
