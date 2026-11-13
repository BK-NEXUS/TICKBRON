// TICKBRON komandası menen chat: akkauntıń óz thread i hám komandanıń kiriwshi qutısı.
// Contract: .ai/API_CONTRACT.md, "Support chat" bólimi.
import { apiFetch } from '../utils/api'
import { readApiError } from '../utils/errorHandler'
import { translateNow } from '../i18n/translateNow'
import { API_BASE_URL } from '../utils/apiBase'

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

/**
 * Thread tiń bir juwabı: jańa xabarlar (birinshi oqıwda sońǵı 100), oqılmaǵan sanı (paydalanıwshı tárepi) yamasa paydalanıwshı
 * (komanda tárepi)
 */
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

/** `code` backend tiń turaqlı qátelik atı (empty, too_long, bad_text), sol sebepli ekranlar onı awdara aladı. */
export interface ChatResult<T> {
  data: T | null
  error: string | null
  code: string | null
}

/** Chat oynası ne talap etedi, qaysı tárep bolsa da: jańa xabarlardı oqıw, birin jazıw, thread kórilgenin aytıw */
export interface ChatApi {
  load: (after: number) => Promise<ChatResult<ThreadPage>>
  send: (text: string) => Promise<ChatResult<ChatMessage>>
  markRead: () => Promise<unknown>
}

const MY = '/api/v1/chat'
const ADMIN = '/api/v1/admin-panel/chat'
// Getter: tekst qátelik bolǵanda, bet sol waqıtta qaysı tilde bolsa sol tilde tańlanadı
const STATUS_MESSAGES = {
  get 401() { return translateNow('apiError.authRequired') },
  403: 'Not allowed',
  404: 'Not found',
  429: 'Too many requests',
}

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
      return { data: null, error: error instanceof Error ? error.message : translateNow('apiError.networkOccurred'), code: null }
    }
  }

  private post<T>(endpoint: string, body?: unknown): Promise<ChatResult<T>> {
    return this.request<T>(endpoint, { method: 'POST', body: body === undefined ? undefined : JSON.stringify(body) })
  }

  // Akkauntıń óz thread i

  /** Kirgen akkauntıń chat oynası */
  mine(): ChatApi {
    return {
      load: after => this.request<ThreadPage>(`${MY}/messages/${after ? `?after=${after}` : ''}`),
      send: text => this.post<ChatMessage>(`${MY}/messages/`, { text }),
      markRead: () => this.post(`${MY}/read/`),
    }
  }

  /** Komandadan kelgen neshe xabardı akkaunt oqımaǵan (belgi) */
  async myUnread(): Promise<ChatResult<{ unread: number }>> {
    return this.request<{ unread: number }>(`${MY}/unread/`)
  }

  // Komandanıń tárepi

  async inbox(params: { q?: string; unread?: boolean; page?: number } = {}): Promise<ChatResult<Inbox>> {
    const query = new URLSearchParams()
    if (params.q) query.set('q', params.q)
    if (params.unread) query.set('unread', 'true')
    if (params.page && params.page > 1) query.set('page', String(params.page))
    const text = query.toString()
    return this.request<Inbox>(`${ADMIN}/conversations/${text ? `?${text}` : ''}`)
  }

  /** Bir thread tiń chat oynası, komanda ushın */
  thread(conversationId: number): ChatApi {
    return {
      load: after => this.request<ThreadPage>(`${ADMIN}/conversations/${conversationId}/${after ? `?after=${after}` : ''}`),
      send: text => this.post<ChatMessage>(`${ADMIN}/conversations/${conversationId}/`, { text }),
      markRead: () => this.post(`${ADMIN}/conversations/${conversationId}/read/`),
    }
  }

  /** Neshe thread te komanda oqımaǵan xabar bar (admin tabındaǵı belgi) */
  async staffUnread(): Promise<ChatResult<{ unread_threads: number }>> {
    return this.request<{ unread_threads: number }>(`${ADMIN}/unread/`)
  }
}

export const chatAdapter = new ChatAdapter()
