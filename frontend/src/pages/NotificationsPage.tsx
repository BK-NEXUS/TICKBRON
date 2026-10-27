import { useCallback, useEffect, useState } from 'react'
import { Bell, Lock } from 'lucide-react'
import { useI18n } from '../i18n/I18nContext'
import { useAuth } from '../contexts/AuthContext'
import { EmptyState } from '../components/EmptyState'
import { notificationAdapter, type AppNotification } from '../adapters/notificationAdapter'
import { notificationText } from '../utils/notificationText'
import { NOTIFICATIONS_CHANGED } from '../hooks/useNotificationCount'

export function NotificationsPage() {
  const { t, formatDate } = useI18n()
  const { isAuthenticated, isLoading: sessionLoading } = useAuth()
  const [notices, setNotices] = useState<AppNotification[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    const result = await notificationAdapter.list()
    if (result.error) setError(result.error)
    else setNotices(result.data ?? [])
    setLoading(false)
  }, [])

  useEffect(() => {
    if (!isAuthenticated) {
      setLoading(false)
      return
    }
    void load()
  }, [isAuthenticated, load])

  const changed = () => window.dispatchEvent(new Event(NOTIFICATIONS_CHANGED))

  const open = async (notice: AppNotification) => {
    if (notice.is_read) return
    const result = await notificationAdapter.markRead(notice.id)
    if (result.error) return setError(result.error)
    setNotices(current => current.map(row => (row.id === notice.id ? { ...row, is_read: true } : row)))
    changed()
  }

  const markAll = async () => {
    const result = await notificationAdapter.markAllRead()
    if (result.error) return setError(result.error)
    setNotices(current => current.map(row => ({ ...row, is_read: true })))
    changed()
  }

  if (!isAuthenticated && !sessionLoading) {
    return (
      <div className="notifications-page">
        <div className="container">
          <EmptyState
            headingLevel={1}
            icon={<Lock size={40} />}
            title={t('common.signInRequired')}
            message={t('notifications.signInText')}
            ctaText={t('auth.signIn')}
            ctaLink="/login"
          />
        </div>
      </div>
    )
  }

  if (loading || sessionLoading) {
    return (
      <div className="notifications-page">
        <div className="container">
          <div className="loading-state">
            <div className="spinner" role="status" aria-live="polite">
              <span className="sr-only">{t('common.loading')}</span>
            </div>
            <p>{t('notifications.loading')}</p>
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="notifications-page">
        <div className="container">
          <div className="error-state" role="alert" aria-live="assertive">
            <p>{error}</p>
            <button onClick={() => void load()} className="btn btn-primary">{t('common.tryAgain')}</button>
          </div>
        </div>
      </div>
    )
  }

  if (notices.length === 0) {
    return (
      <div className="notifications-page">
        <div className="container">
          <EmptyState
            headingLevel={1}
            icon={<Bell size={40} />}
            title={t('notifications.emptyTitle')}
            message={t('notifications.emptyText')}
            ctaText={t('favorites.emptyCta')}
            ctaLink="/search"
          />
        </div>
      </div>
    )
  }

  const anyUnread = notices.some(notice => !notice.is_read)

  return (
    <div className="notifications-page">
      <div className="container">
        <div className="notifications-head">
          <h1 className="notifications-title">{t('notifications.title')}</h1>
          {anyUnread && (
            <button type="button" onClick={() => void markAll()} className="btn btn-secondary">
              {t('notifications.markAll')}
            </button>
          )}
        </div>
        <ul className="notifications-list">
          {notices.map(notice => {
            const text = notificationText(notice, t)
            return (
              <li key={notice.id}>
                <button
                  type="button"
                  onClick={() => void open(notice)}
                  className={`notification-row ${notice.is_read ? '' : 'notification-row--unread'}`}
                >
                  <span className="notification-row-title">
                    {!notice.is_read && <span className="notification-dot" role="img" aria-label={t('notifications.unread')} />}
                    {text.title}
                  </span>
                  <span className="notification-row-message">{text.message}</span>
                  <time className="notification-row-time" dateTime={notice.created_at}>{formatDate(notice.created_at)}</time>
                </button>
              </li>
            )
          })}
        </ul>
      </div>
    </div>
  )
}

export default NotificationsPage
