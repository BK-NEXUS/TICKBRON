// Chat with the TICKBRON team: the account's own thread and the team's inbox.
// Contract: .ai/API_CONTRACT.md, section "Support chat".
import { apiFetch } from '../utils/api'
import { readApiError } from '../utils/errorHandler'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export interface ChatMessage {
  id: number
  text: string
  from_staff: boolean
  created_at: string
}

export interface ChatUser {
  id: number
  name: string
  email: string
  role: 'customer' | 'hotel-owner'
}

/** One answer of the thread: the new messages (the last 100 on the first read), the unread count (user side) or the user (team side) */
export interface ThreadPage {
  messages: ChatMessage[]
  unread?: number
  user?: ChatUser
}

export interface InboxRow {
  id: number
  user: ChatUser
  last_message: { text: string; from_staff: boolean; created_at: string } | null
  unread: number
  last_message_at: string
}

export interface Inbox {
  count: number
  next: string | null
  previous: string | null
  results: InboxRow[]
}

/** `code` is the backend's stable error name (empty, too_long, bad_text) so screens can translate it. */
export interface ChatResult<T> {
  data: T | null
  error: string | null
  code: string | null
}

/** What a chat window needs, whichever side it is: read new messages, write one, tell that the thread was seen */
export interface ChatApi {
  load: (after: number) => Promise<ChatResult<ThreadPage>>
  send: (text: string) => Promise<ChatResult<ChatMessage>>
  markRead: () => Promise<unknown>
}

const MY = '/api/v1/chat'
const ADMIN = '/api/v1/admin-panel/chat'
const STATUS_MESSAGES = { 401: 'Authentication required', 403: 'Not allowed', 404: 'Not found', 429: 'Too many requests' }

export class ChatAdapter {
  constructor(private baseUrl: string = API_BASE_URL) {}

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<ChatResult<T>> {
    try {
      const response = await apiFetch(`${this.baseUrl}${endpoint}`, {
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        ...options,
      })
      if (!response.ok) {
        const apiError = await readApiError(response, STATUS_MESSAGES)
        return { data: null, error: apiError.message, code: apiError.code ?? null }
      }
      if (response.status === 204) return { data: null, error: null, code: null }
      return { data: (await response.json()) as T, error: null, code: null }
    } catch (error) {
      return { data: null, error: error instanceof Error ? error.message : 'Network error occurred', code: null }
    }
  }

  private post<T>(endpoint: string, body?: unknown): Promise<ChatResult<T>> {
    return this.request<T>(endpoint, { method: 'POST', body: body === undefined ? undefined : JSON.stringify(body) })
  }

  // The account's own thread

  /** The chat window of the logged-in account */
  mine(): ChatApi {
    return {
      load: after => this.request<ThreadPage>(`${MY}/messages/${after ? `?after=${after}` : ''}`),
      send: text => this.post<ChatMessage>(`${MY}/messages/`, { text }),
      markRead: () => this.post(`${MY}/read/`),
    }
  }

  /** How many messages from the team the account has not read (the badge) */
  async myUnread(): Promise<ChatResult<{ unread: number }>> {
    return this.request<{ unread: number }>(`${MY}/unread/`)
  }

  // The team's side

  async inbox(params: { q?: string; unread?: boolean; page?: number } = {}): Promise<ChatResult<Inbox>> {
    const query = new URLSearchParams()
    if (params.q) query.set('q', params.q)
    if (params.unread) query.set('unread', 'true')
    if (params.page && params.page > 1) query.set('page', String(params.page))
    const text = query.toString()
    return this.request<Inbox>(`${ADMIN}/conversations/${text ? `?${text}` : ''}`)
  }

  /** The chat window of one thread, for the team */
  thread(conversationId: number): ChatApi {
    return {
      load: after => this.request<ThreadPage>(`${ADMIN}/conversations/${conversationId}/${after ? `?after=${after}` : ''}`),
      send: text => this.post<ChatMessage>(`${ADMIN}/conversations/${conversationId}/`, { text }),
      markRead: () => this.post(`${ADMIN}/conversations/${conversationId}/read/`),
    }
  }

  /** How many threads have messages the team has not read (the badge on the admin tab) */
  async staffUnread(): Promise<ChatResult<{ unread_threads: number }>> {
    return this.request<{ unread_threads: number }>(`${ADMIN}/unread/`)
  }
}

export const chatAdapter = new ChatAdapter()
