import { afterEach, describe, expect, it, vi } from 'vitest'

async function baseWith(value: string | undefined) {
  vi.resetModules()
  if (value === undefined) delete (import.meta.env as Record<string, unknown>).VITE_API_BASE_URL
  else vi.stubEnv('VITE_API_BASE_URL', value)
  return (await import('./apiBase')).API_BASE_URL
}

describe('API_BASE_URL', () => {
  afterEach(() => vi.unstubAllEnvs())

  it('is the local backend when nothing is set', async () => {
    expect(await baseWith(undefined)).toBe('http://localhost:8000')
  })

  it('is the address that was set, without a trailing slash', async () => {
    expect(await baseWith('https://tickbron.com/')).toBe('https://tickbron.com')
  })

  it('is empty when set empty, so requests go to the same address as the page (one ngrok tunnel)', async () => {
    expect(await baseWith('')).toBe('')
  })
})
