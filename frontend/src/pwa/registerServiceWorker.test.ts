import { describe, it, expect, vi } from 'vitest'
import { registerServiceWorker } from './registerServiceWorker'

const supported = (register = vi.fn().mockResolvedValue({})) => ({ serviceWorker: { register } })

describe('registerServiceWorker', () => {
  it('registers /sw.js on the whole site in the built site', async () => {
    const register = vi.fn().mockResolvedValue({})
    await registerServiceWorker(true, supported(register))
    expect(register).toHaveBeenCalledWith('/sw.js', { scope: '/' })
  })

  it('does nothing while developing (a worker would serve stale files to the dev server)', async () => {
    const register = vi.fn()
    await registerServiceWorker(false, supported(register))
    expect(register).not.toHaveBeenCalled()
  })

  it('does nothing in a browser without service workers', async () => {
    await expect(registerServiceWorker(true, {})).resolves.toBeUndefined()
  })

  it('never breaks the site when registering fails', async () => {
    const register = vi.fn().mockRejectedValue(new Error('blocked'))
    await expect(registerServiceWorker(true, supported(register))).resolves.toBeUndefined()
  })
})
