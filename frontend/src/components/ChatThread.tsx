import { FormEvent, useCallback, useEffect, useRef, useState } from 'react'
import { Send } from 'lucide-react'
import type { ChatApi, ChatMessage } from '../adapters/chatAdapter'
import { useI18n } from '../i18n/I18nContext'
import type { MessageKey } from '../i18n/messages/en'

const POLL_MS = 4000
const MAX_POLL_MS = 30000
export const MAX_CHAT_TEXT = 2000

type Side = 'guest' | 'team'

interface ChatThreadProps {
  api: ChatApi
  /** Which side is typing: decides whose messages sit on the right */
  side: Side
  /** Told after every read, so a badge elsewhere can follow */
  onSeen?: () => void
  emptyText: string
  /** Fills the box when the chat opens from a shortcut such as "request advertising" */
  initialText?: string
}

const ERROR_KEYS: Record<string, MessageKey> = {
  empty: 'chat.error.empty',
  too_long: 'chat.error.tooLong',
  bad_text: 'chat.error.badText',
}

export function ChatThread({ api, side, onSeen, emptyText, initialText = '' }: ChatThreadProps) {
  const { t, formatDate } = useI18n()
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [loading, setLoading] = useState(true)
  const [loadFailed, setLoadFailed] = useState(false)
  const [text, setText] = useState(initialText)
  const [sending, setSending] = useState(false)
  const [sendError, setSendError] = useState<string | null>(null)
  const lastId = useRef(0)
  const delay = useRef(POLL_MS)
  const listRef = useRef<HTMLDivElement>(null)

  const isMine = useCallback((message: ChatMessage) => message.from_staff === (side === 'team'), [side])

  const append = useCallback((incoming: ChatMessage[]) => {
    if (incoming.length === 0) return
    setMessages(current => {
      const known = new Set(current.map(message => message.id))
      return [...current, ...incoming.filter(message => !known.has(message.id))]
    })
    lastId.current = Math.max(lastId.current, ...incoming.map(message => message.id))
  }, [])

  const poll = useCallback(async () => {
    const result = await api.load(lastId.current)
    if (!result.data) {
      setLoadFailed(true)
      delay.current = Math.min(delay.current * 2, MAX_POLL_MS)
      setLoading(false)
      return
    }
    setLoadFailed(false)
    delay.current = POLL_MS
    append(result.data.messages)
    setLoading(false)
    if (result.data.messages.some(message => !isMine(message))) {
      await api.markRead()
      onSeen?.()
    }
  }, [api, append, isMine, onSeen])

  useEffect(() => {
    let stopped = false
    let timer: ReturnType<typeof setTimeout> | undefined
    const tick = async () => {
      if (document.visibilityState === 'visible') await poll()
      if (!stopped) timer = setTimeout(tick, delay.current)
    }
    const onVisible = () => {
      if (document.visibilityState !== 'visible') return
      clearTimeout(timer)
      delay.current = POLL_MS
      void tick()
    }
    document.addEventListener('visibilitychange', onVisible)
    void tick()
    return () => {
      stopped = true
      clearTimeout(timer)
      document.removeEventListener('visibilitychange', onVisible)
    }
  }, [poll])

  useEffect(() => {
    const list = listRef.current
    if (list) list.scrollTop = list.scrollHeight
  }, [messages])

  const submit = async (event: FormEvent) => {
    event.preventDefault()
    const body = text.trim()
    if (!body || sending) return
    setSending(true)
    setSendError(null)
    const result = await api.send(body)
    setSending(false)
    if (result.data) {
      append([result.data])
      setText('')
    } else {
      const key = result.code ? ERROR_KEYS[result.code] : undefined
      setSendError(key ? t(key) : t('chat.error.send'))
    }
  }

  return (
    <div className="chat-thread">
      <div className="chat-thread__list" ref={listRef} role="log" aria-live="polite" aria-label={t('chat.messages')}>
        {loading && <p className="chat-thread__note">{t('chat.loading')}</p>}
        {!loading && messages.length === 0 && !loadFailed && <p className="chat-thread__note">{emptyText}</p>}
        {messages.map(message => (
          <div key={message.id} className={`chat-bubble ${isMine(message) ? 'chat-bubble--mine' : 'chat-bubble--theirs'}`}>
            <p className="chat-bubble__text">{message.text}</p>
            <time className="chat-bubble__time" dateTime={message.created_at}>
              {formatDate(message.created_at, { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })}
            </time>
          </div>
        ))}
      </div>
      {loadFailed && <p className="chat-thread__error" role="alert">{t('chat.error.load')}</p>}
      <form className="chat-thread__form" onSubmit={submit}>
        <label className="sr-only" htmlFor="chat-input">{t('chat.inputLabel')}</label>
        <textarea
          id="chat-input"
          className="chat-thread__input"
          rows={2}
          value={text}
          maxLength={MAX_CHAT_TEXT}
          placeholder={t('chat.placeholder')}
          onChange={event => setText(event.target.value)}
          onKeyDown={event => {
            if (event.key === 'Enter' && !event.shiftKey) {
              event.preventDefault()
              event.currentTarget.form?.requestSubmit()
            }
          }}
        />
        <button type="submit" className="btn btn-primary chat-thread__send" disabled={sending || !text.trim()}>
          <Send size={16} aria-hidden="true" /> {t('chat.send')}
        </button>
      </form>
      {sendError && <p className="chat-thread__error" role="alert">{sendError}</p>}
    </div>
  )
}
