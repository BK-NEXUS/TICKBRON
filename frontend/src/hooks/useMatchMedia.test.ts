import { describe, it, expect, afterEach, vi } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useMatchMedia } from './useMatchMedia'

type Listener = (event: { matches: boolean }) => void

function stubMatchMedia(initial: boolean) {
  const listeners = new Set<Listener>()
  const query = {
    matches: initial,
    addEventListener: (_: string, listener: Listener) => listeners.add(listener),
    removeEventListener: (_: string, listener: Listener) => listeners.delete(listener),
  }
  window.matchMedia = vi.fn().mockReturnValue(query) as unknown as typeof window.matchMedia
  return {
    listeners,
    change(matches: boolean) {
      query.matches = matches
      listeners.forEach(listener => listener({ matches }))
    },
  }
}

describe('useMatchMedia', () => {
  const original = window.matchMedia
  afterEach(() => { window.matchMedia = original })

  it('starts with the current answer of the query', () => {
    stubMatchMedia(true)
    expect(renderHook(() => useMatchMedia('(min-width: 1024px)')).result.current).toBe(true)
  })

  it('follows the screen when it changes', () => {
    const media = stubMatchMedia(false)
    const { result } = renderHook(() => useMatchMedia('(min-width: 1024px)'))
    expect(result.current).toBe(false)
    act(() => media.change(true))
    expect(result.current).toBe(true)
  })

  it('stops listening when the component goes away', () => {
    const media = stubMatchMedia(false)
    const { unmount } = renderHook(() => useMatchMedia('(min-width: 1024px)'))
    expect(media.listeners.size).toBe(1)
    unmount()
    expect(media.listeners.size).toBe(0)
  })

  it('says false where matchMedia does not exist', () => {
    // @ts-expect-error simulating an environment without matchMedia
    window.matchMedia = undefined
    expect(renderHook(() => useMatchMedia('(min-width: 1024px)')).result.current).toBe(false)
  })
})
