import { act, renderHook } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { useIsMobile } from './useIsMobile'
import { useReducedMotion } from './useReducedMotion'

type Listener = () => void

function mockMatchMedia(matches: boolean) {
  const listeners = new Set<Listener>()
  const mql = {
    matches,
    addEventListener: (_: string, l: Listener) => listeners.add(l),
    removeEventListener: (_: string, l: Listener) => listeners.delete(l),
  }
  vi.stubGlobal('matchMedia', vi.fn(() => mql))
  return {
    set(next: boolean) {
      mql.matches = next
      listeners.forEach((l) => l())
    },
  }
}

afterEach(() => vi.unstubAllGlobals())

describe('useReducedMotion', () => {
  it('reflects the media query and reacts to changes', () => {
    const media = mockMatchMedia(true)
    const { result } = renderHook(() => useReducedMotion())
    expect(result.current).toBe(true)
    act(() => media.set(false))
    expect(result.current).toBe(false)
  })
})

describe('useIsMobile', () => {
  it('reflects the media query and reacts to changes', () => {
    const media = mockMatchMedia(false)
    const { result } = renderHook(() => useIsMobile())
    expect(result.current).toBe(false)
    act(() => media.set(true))
    expect(result.current).toBe(true)
  })
})
