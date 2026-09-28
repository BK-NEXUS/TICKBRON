import '@testing-library/jest-dom'
import { act, cleanup } from '@testing-library/react'
import { format } from 'node:util'
import { afterEach, beforeEach } from 'vitest'
import { setCsrfToken } from '../utils/api'

// React's "An update to X inside a test was not wrapped in act(...)" means a state update landed
// while nothing was waiting for it: the test asserted before the component finished loading, or
// ended with a request still pending. Those are the tests that pass alone and fail under load, so a
// test that causes one fails (tests that silence console.error themselves are not checked).
const ACT_WARNING = 'not wrapped in act('
let actWarnings: string[] = []
const originalConsoleError = console.error

// Adapter tests mock fetch call by call; a cached token keeps the CSRF lookup out of those sequences
beforeEach(() => {
  setCsrfToken('test-csrf-token')
  actWarnings = []
  console.error = (...args: unknown[]) => {
    // React passes a format string ("An update to %s inside a test...") and its values
    const message = format(...args)
    if (message.includes(ACT_WARNING)) {
      const component = message.match(/An update to (\w+)/)?.[1] ?? 'a component'
      actWarnings.push(component)
    }
    originalConsoleError(...args)
  }
})

afterEach(async () => {
  // Let requests the test started (mocked, so already resolved) finish inside act before unmounting
  await act(async () => {})
  cleanup()
  console.error = originalConsoleError
  if (actWarnings.length > 0) {
    const components = [...new Set(actWarnings)].join(', ')
    actWarnings = []
    throw new Error(
      `State update outside act() in ${components}: await what the test triggers ` +
      '(findBy*/waitFor on the result) before asserting or ending the test.'
    )
  }
})
