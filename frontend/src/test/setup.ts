import '@testing-library/jest-dom'
import { cleanup } from '@testing-library/react'
import { afterEach, beforeEach } from 'vitest'
import { setCsrfToken } from '../utils/api'

// Adapter tests mock fetch call by call; a cached token keeps the CSRF lookup out of those sequences
beforeEach(() => {
  setCsrfToken('test-csrf-token')
})

afterEach(() => {
  cleanup()
})
