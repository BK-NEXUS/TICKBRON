// The in-app notices of the logged-in account. Contract: .ai/API_CONTRACT.md, "Notifications API".
import { apiFetch } from '../utils/api'
import { readApiError } from '../utils/errorHandler'
import { translateNow } from '../i18n/translateNow'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

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
  /** The newest notices (the first page, newest first) */
  async list(): Promise<NotificationResult<AppNotification[]>> {
    const result = await request<{ results: AppNotification[] }>('')
    return { data: result.data ? result.data.results : null, error: result.error }
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
