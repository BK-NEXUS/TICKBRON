// The in-app notices of the logged-in account. Contract: .ai/API_CONTRACT.md, "Notifications API".
import { apiFetch } from '../utils/api'
import { readApiError } from '../utils/errorHandler'
import { translateNow } from '../i18n/translateNow'
import { API_BASE_URL } from '../utils/apiBase'

/** `title` and `message` are the English fallback; screens write their own text from `code` + `params` */
export interface AppNotification {
  id: number
  code: string | null
  params: Record<string, string | number> | null
  title: string
  message: string
  is_read: boolean
  booking: number | null
  created_at: string
}

export interface NotificationResult<T> {
  data: T | null
  error: string | null
}

const BASE = '/api/v1/me/notifications/'
// A getter: the text is chosen when an error happens, in the language the page is in then
const STATUS_MESSAGES = {
  get 401() { return translateNow('apiError.authRequired') },
}

async function request<T>(path: string, options: RequestInit = {}): Promise<NotificationResult<T>> {
  try {
    const response = await apiFetch(`${API_BASE_URL}${BASE}${path}`, {
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      ...options,
    })
    if (!response.ok) {
      const apiError = await readApiError(response, STATUS_MESSAGES)
      return { data: null, error: apiError.message }
    }
    return { data: (await response.json()) as T, error: null }
  } catch {
    return { data: null, error: translateNow('apiError.networkOccurred') }
  }
}

export const notificationAdapter = {
  /** One page of the notices, newest first; `hasMore` is true while the server has a next page */
  async list(page = 1): Promise<NotificationResult<{ items: AppNotification[]; hasMore: boolean }>> {
    const result = await request<{ results: AppNotification[]; next: string | null }>(`?page=${page}`)
    if (!result.data) return { data: null, error: result.error }
    return { data: { items: result.data.results, hasMore: result.data.next !== null }, error: null }
  },

  async unreadCount(): Promise<NotificationResult<{ unread: number }>> {
    return request<{ unread: number }>('count/')
  },

  async markRead(id: number): Promise<NotificationResult<AppNotification>> {
    return request<AppNotification>(`${id}/`, { method: 'PATCH', body: JSON.stringify({ is_read: true }) })
  },

  async markAllRead(): Promise<NotificationResult<{ marked_as_read: number }>> {
    return request<{ marked_as_read: number }>('mark_all_read/', { method: 'POST' })
  },
}
