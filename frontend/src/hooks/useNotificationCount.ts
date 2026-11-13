import { useCallback, useEffect, useState } from 'react'
import { notificationAdapter } from '../adapters/notificationAdapter'

const REFRESH_MS = 60000

/** Xabarlandırıwlar beti olardı oqılǵan dep belgilegende bunı iske túsiredi, sonda belgi birden jańalanadı */
export const NOTIFICATIONS_CHANGED = 'tickbron:notifications-changed'

/** Xabarlandırıw belgisi artındaǵı san: kirgen akkauntıń oqılmaǵan xabarlandırıwları */
export function useNotificationCount(enabled: boolean) {
  const [count, setCount] = useState(0)

  const refresh = useCallback(async () => {
    if (!enabled || document.visibilityState !== 'visible') return
    const result = await notificationAdapter.unreadCount()
    if (result.data) setCount(result.data.unread)
  }, [enabled])

  useEffect(() => {
    void refresh()
    if (!enabled) return undefined
    const timer = setInterval(() => void refresh(), REFRESH_MS)
    const onChanged = () => void refresh()
    window.addEventListener(NOTIFICATIONS_CHANGED, onChanged)
    return () => {
      clearInterval(timer)
      window.removeEventListener(NOTIFICATIONS_CHANGED, onChanged)
    }
  }, [enabled, refresh])

  return { count: enabled ? count : 0, refresh }
}
