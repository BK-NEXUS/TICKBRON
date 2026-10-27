import { useCallback, useEffect, useState } from 'react'
import { notificationAdapter } from '../adapters/notificationAdapter'

const REFRESH_MS = 60000

/** The notifications page fires this when it marks notices read, so the badge updates at once */
export const NOTIFICATIONS_CHANGED = 'tickbron:notifications-changed'

/** The number behind the notices badge: unread notices of the logged-in account */
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
