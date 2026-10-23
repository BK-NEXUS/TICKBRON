import { FormEvent, useCallback, useEffect, useMemo, useState } from 'react'
import { chatAdapter, type InboxRow } from '../adapters/chatAdapter'
import { ChatThread } from './ChatThread'
import { useI18n } from '../i18n/I18nContext'

interface AdminSupportChatProps {
  /** Told when the team's unread number may have changed */
  onSeen?: () => void
}

const INBOX_REFRESH_MS = 15000

export function AdminSupportChat({ onSeen }: AdminSupportChatProps) {
  const { t, formatDate } = useI18n()
  const [rows, setRows] = useState<InboxRow[]>([])
  const [hasNext, setHasNext] = useState(false)
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [query, setQuery] = useState('')
  const [onlyUnread, setOnlyUnread] = useState(false)
  const [loading, setLoading] = useState(true)
  const [failed, setFailed] = useState(false)
  const [openId, setOpenId] = useState<number | null>(null)

  const load = useCallback(async () => {
    const result = await chatAdapter.inbox({ q: query, unread: onlyUnread, page })
    setLoading(false)
    if (!result.data) {
      setFailed(true)
      return
    }
    setFailed(false)
    setRows(result.data.results)
    setHasNext(Boolean(result.data.next))
  }, [query, onlyUnread, page])

  useEffect(() => {
    void load()
    const timer = setInterval(() => {
      if (document.visibilityState === 'visible') void load()
    }, INBOX_REFRESH_MS)
    return () => clearInterval(timer)
  }, [load])

  const open = rows.find(row => row.id === openId) ?? null
  const api = useMemo(() => (openId === null ? null : chatAdapter.thread(openId)), [openId])

  const afterSeen = useCallback(() => {
    void load()
    onSeen?.()
  }, [load, onSeen])

  const submitSearch = (event: FormEvent) => {
    event.preventDefault()
    setPage(1)
    setQuery(search.trim())
  }

  return (
    <section className="admin-chat">
      <h2>{t('chat.admin.title')}</h2>
      <div className="admin-chat__layout">
        <div className="admin-chat__inbox">
          <form className="admin-chat__filters" onSubmit={submitSearch} role="search">
            <label className="sr-only" htmlFor="admin-chat-search">{t('chat.admin.search')}</label>
            <input
              id="admin-chat-search"
              type="search"
              value={search}
              placeholder={t('chat.admin.search')}
              onChange={event => setSearch(event.target.value)}
            />
            <label className="admin-chat__check">
              <input
                type="checkbox"
                checked={onlyUnread}
                onChange={event => { setPage(1); setOnlyUnread(event.target.checked) }}
              />
              {t('chat.admin.onlyUnread')}
            </label>
          </form>
          {loading && <p className="chat-thread__note">{t('chat.loading')}</p>}
          {failed && <p className="chat-thread__error" role="alert">{t('chat.error.load')}</p>}
          {!loading && !failed && rows.length === 0 && <p className="chat-thread__note">{t('chat.admin.none')}</p>}
          <ul className="admin-chat__rows">
            {rows.map(row => (
              <li key={row.id}>
                <button
                  type="button"
                  className={`admin-chat__row ${row.id === openId ? 'admin-chat__row--open' : ''}`}
                  aria-current={row.id === openId ? 'true' : undefined}
                  onClick={() => setOpenId(row.id)}
                >
                  <span className="admin-chat__who">
                    <strong>{row.user.name || row.user.email}</strong>
                    <span className="admin-chat__role">{t(row.user.role === 'hotel-owner' ? 'chat.admin.owner' : 'chat.admin.guest')}</span>
                  </span>
                  <span className="admin-chat__preview">{row.last_message?.text}</span>
                  <span className="admin-chat__meta">
                    {formatDate(row.last_message_at, { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })}
                    {row.unread > 0 && <span className="chat-badge" aria-label={t('chat.admin.unreadCount', { count: row.unread })}>{row.unread}</span>}
                  </span>
                </button>
              </li>
            ))}
          </ul>
          {(page > 1 || hasNext) && (
            <div className="admin-chat__pager">
              <button type="button" className="btn btn-secondary" disabled={page === 1} onClick={() => setPage(page - 1)}>{t('chat.admin.prev')}</button>
              <button type="button" className="btn btn-secondary" disabled={!hasNext} onClick={() => setPage(page + 1)}>{t('chat.admin.next')}</button>
            </div>
          )}
        </div>
        <div className="admin-chat__thread">
          {open && api ? (
            <>
              <h3>{open.user.name || open.user.email}</h3>
              <p className="admin-chat__email">{open.user.email}</p>
              <ChatThread key={open.id} api={api} side="team" onSeen={afterSeen} emptyText={t('chat.empty')} />
            </>
          ) : (
            <p className="chat-thread__note">{t('chat.admin.pick')}</p>
          )}
        </div>
      </div>
    </section>
  )
}
