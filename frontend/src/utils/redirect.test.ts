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

  it('accepts only a path on this site (a leading // or a backslash would leave it)', () => {
    for (const pathname of ['//evil.example', '///evil.example', 'https://evil.example', '/\\evil.example', 'bookings', '/a\nb']) {
      expect(redirectPathFrom({ from: { pathname } })).toBe('/')
    }
    expect(redirectPathFrom({ from: { pathname: '/search/x' } })).toBe('/search/x')
  })
})
