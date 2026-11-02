import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { act, renderHook } from '@testing-library/react'
import { useOnlineStatus } from './useOnlineStatus'

const setNavigatorOnline = (value: boolean) => vi.spyOn(window.navigator, 'onLine', 'get').mockReturnValue(value)

describe('useOnlineStatus', () => {
  beforeEach(() => { setNavigatorOnline(true) })
  afterEach(() => { vi.restoreAllMocks(); vi.unstubAllGlobals() })

  it('starts with what the browser says', () => {
    setNavigatorOnline(false)
    expect(renderHook(() => useOnlineStatus()).result.current.online).toBe(false)
    setNavigatorOnline(true)
    expect(renderHook(() => useOnlineStatus()).result.current.online).toBe(true)
  })

  it('follows the offline and online events of the window', () => {
    const { result } = renderHook(() => useOnlineStatus())
    act(() => { window.dispatchEvent(new Event('offline')) })
    expect(result.current.online).toBe(false)
    act(() => { window.dispatchEvent(new Event('online')) })
    expect(result.current.online).toBe(true)
  })

  it('recheck: a reachable server means online again, even when the browser is unsure', async () => {
    setNavigatorOnline(false)
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(null)))
    const { result } = renderHook(() => useOnlineStatus())
    let reached = false
    await act(async () => { reached = await result.current.recheck() })
    expect(reached).toBe(true)
    expect(result.current.online).toBe(true)
  })

  it('recheck: no answer from the server keeps it offline and says so', async () => {
    setNavigatorOnline(false)
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('Failed to fetch')))
    const { result } = renderHook(() => useOnlineStatus())
    let reached = true
    await act(async () => { reached = await result.current.recheck() })
    expect(reached).toBe(false)
    expect(result.current.online).toBe(false)
  })
})
