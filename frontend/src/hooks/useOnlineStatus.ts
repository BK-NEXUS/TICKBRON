import { useCallback, useEffect, useState } from 'react'
import { API_BASE_URL } from '../utils/apiBase'

const CHECK_TIMEOUT_MS = 6000

/**
 * Whether the device is online: what the browser says, followed live through its online and offline events.
 * The browser can be wrong (a Wi-Fi without internet reads "online"; a flaky signal "offline"), so `recheck`
 * asks the server itself and settles it.
 */
export function useOnlineStatus() {
  const [online, setOnline] = useState(() => navigator.onLine)

  useEffect(() => {
    const goOnline = () => setOnline(true)
    const goOffline = () => setOnline(false)
    window.addEventListener('online', goOnline)
    window.addEventListener('offline', goOffline)
    return () => {
      window.removeEventListener('online', goOnline)
      window.removeEventListener('offline', goOffline)
    }
  }, [])

  /** True when the server answered. `no-cors`: only reaching it matters, not reading the answer. */
  const recheck = useCallback(async () => {
    const controller = new AbortController()
    const timer = window.setTimeout(() => controller.abort(), CHECK_TIMEOUT_MS)
    try {
      await fetch(`${API_BASE_URL}/healthz/`, { mode: 'no-cors', cache: 'no-store', signal: controller.signal })
      setOnline(true)
      return true
    } catch {
      setOnline(false)
      return false
    } finally {
      window.clearTimeout(timer)
    }
  }, [])

  return { online, recheck }
}
