import { useCallback, useEffect, useState } from 'react'
import { API_BASE_URL } from '../utils/apiBase'

const CHECK_TIMEOUT_MS = 6000

/**
 * Qurılma onlayn ba: brauzer ne dese sol, online hám offline waqıyaları arqalı tikkeley izlenedi.
 * Brauzer qátelesiwi múmkin (internetsiz Wi-Fi "online" dep oqıladı; turaqsız signal "offline"), sol sebepli `recheck`
 * serverden ózi soraydı hám sheshedi.
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

  /** Server juwap bergen bolsa true. `no-cors`: tek oǵan jetiw áhmiyetli, juwaptı oqıw emes. */
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
