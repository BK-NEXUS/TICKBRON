import { useCallback, useEffect, useState } from 'react'
import { chatAdapter } from '../adapters/chatAdapter'

const REFRESH_MS = 30000

/** Chat belgisi artındaǵı san; `staff` komandanı kútip turǵan thread lerdi sanaydı, bolmasa akkaunt ushın oqılmaǵan xabarlar. */
export function useChatUnread(enabled: boolean, staff = false) {
  const [count, setCount] = useState(0)

  const refresh = useCallback(async () => {
    if (!enabled || document.visibilityState !== 'visible') return
    if (staff) {
      const result = await chatAdapter.staffUnread()
      if (result.data) setCount(result.data.unread_threads)
    } else {
      const result = await chatAdapter.myUnread()
      if (result.data) setCount(result.data.unread)
    }
  }, [enabled, staff])

  useEffect(() => {
    void refresh()
    if (!enabled) return undefined
    const timer = setInterval(() => void refresh(), REFRESH_MS)
    return () => clearInterval(timer)
  }, [enabled, refresh])

  return { count: enabled ? count : 0, refresh }
}
