import { describe, it, expect } from 'vitest'
import { redirectPathFrom } from './redirect'

describe('redirectPathFrom', () => {
  it('returns the page the visitor came from', () => {
    expect(redirectPathFrom({ from: { pathname: '/bookings' } })).toBe('/bookings')
  })

  it('falls back to the home page for anything else', () => {
    expect(redirectPathFrom(null)).toBe('/')
    expect(redirectPathFrom(undefined)).toBe('/')
    expect(redirectPathFrom({})).toBe('/')
    expect(redirectPathFrom({ from: { pathname: 42 } })).toBe('/')
    expect(redirectPathFrom({ from: { pathname: '' } })).toBe('/')
    expect(redirectPathFrom('/x')).toBe('/')
  })
})
