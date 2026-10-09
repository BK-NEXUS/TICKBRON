import { describe, it, expect, afterEach, vi } from 'vitest'
import { isCardTestMode } from './paymentTestMode'

describe('isCardTestMode', () => {
  afterEach(() => vi.unstubAllEnvs())

  it('is off unless VITE_PAYMENT_TEST_MODE is "true"', () => {
    vi.stubEnv('VITE_PAYMENT_TEST_MODE', '')
    expect(isCardTestMode()).toBe(false)
    vi.stubEnv('VITE_PAYMENT_TEST_MODE', 'yes')
    expect(isCardTestMode()).toBe(false)
  })

  it('is on in a development or test build when the flag is "true"', () => {
    vi.stubEnv('VITE_PAYMENT_TEST_MODE', 'true')
    expect(isCardTestMode()).toBe(true)
  })

  it('is never on in a production build, whatever the flag says', () => {
    vi.stubEnv('VITE_PAYMENT_TEST_MODE', 'true')
    vi.stubEnv('PROD', true)
    expect(isCardTestMode()).toBe(false)
  })
})
