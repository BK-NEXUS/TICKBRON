import { ChargeMain, ChargeNotes } from '../components/ChargeAmount'
import { useI18n } from '../i18n/I18nContext'
import { statusText } from '../utils/statusText'
import { useState, useEffect, useRef } from 'react'
import { Check, Copy } from 'lucide-react'
import { Lock, Calendar } from 'lucide-react'
import { Link } from 'react-router'
import { accountAdapter, Booking } from '../adapters/accountAdapter'
import { EmptyState } from '../components/EmptyState'
import { useAuth } from '../contexts/AuthContext'
import { CancelBookingDialog } from '../components/CancelBookingDialog'
import type { Booking as CancelledBooking } from '../adapters/bookingAdapter'
import { businessToday } from '../utils/dates'
import { canUsePartnerPanel } from '../utils/roles'
import { ARRIVAL_GRACE_HOURS, formatArrivalTime } from '../utils/arrival'

interface BookingCardProps {
  booking: Booking
  onCancelled: (booking: CancelledBooking) => void
}

/** The guest may ask to cancel an upcoming booking that is still open; the backend has the last word. */
const canCancel = (booking: Booking) =>
  (booking.status === 'pending' || booking.status === 'confirmed') && booking.check_in > businessToday()

function BookingCard({ booking, onCancelled }: BookingCardProps) {
  const { t, formatDate } = useI18n()
  const [copied, setCopied] = useState(false)
  const [cancelling, setCancelling] = useState(false)

  const handleCopyCode = async () => {
    try {
      await navigator.clipboard.writeText(booking.confirmation_code)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (error) {
      console.error('Failed to copy code:', error)
    }
  }

  return (
    <div className="booking-card">
      <div className="booking-card-header">
        <div className="booking-card-title">
          <h3>
            <Link to={`/property/${booking.property}`}>
              {booking.property_name}
            </Link>
          </h3>
          <div className="booking-card-confirmation-container">
            <span className="booking-card-confirmation-label">{t('bookings.reference')}</span>
            <div className="booking-card-confirmation-code-wrapper">
              <span className="booking-card-confirmation-code">
                {booking.confirmation_code}
              </span>
              <button
                className="booking-card-copy-btn"
                onClick={handleCopyCode}
                aria-label={t('bookings.copyLabel')}
                title={t('bookings.copyLabel')}
              >
                {copied ? <Check size={16} aria-hidden="true" /> : <Copy size={16} aria-hidden="true" />}
              </button>
            </div>
          </div>
        </div>
        <div className={`booking-card-status booking-card-status--${booking.status}`}>
          {statusText('status.booking', booking.status, t)}
        </div>
      </div>
      
      <div className="booking-card-details">
        <div className="booking-card-detail">
          <span className="booking-card-detail-label">{t('bookings.checkIn')}</span>
          <span className="booking-card-detail-value">{formatDate(booking.check_in)}</span>
        </div>
        <div className="booking-card-detail">
          <span className="booking-card-detail-label">{t('bookings.checkOut')}</span>
          <span className="booking-card-detail-value">{formatDate(booking.check_out)}</span>
        </div>
        {booking.expected_arrival_time && (
          <div className="booking-card-detail">
            <span className="booking-card-detail-label">{t('booking.arrivalTime')}</span>
            <span className="booking-card-detail-value">{formatArrivalTime(booking.expected_arrival_time)}</span>
          </div>
        )}
        <div className="booking-card-detail">
          <span className="booking-card-detail-label">{t('bookings.nights')}</span>
          <span className="booking-card-detail-value">{booking.number_of_nights}</span>
        </div>
        <div className="booking-card-detail">
          <span className="booking-card-detail-label">{t('bookings.guests')}</span>
          <span className="booking-card-detail-value">{booking.guest_count}</span>
        </div>
        <div className="booking-card-detail">
          <span className="booking-card-detail-label">{t('bookings.total')}</span>
          <span className="booking-card-detail-value">
            <ChargeMain booking={booking} />
          </span>
          <ChargeNotes booking={booking} />
        </div>
      </div>
      
      {booking.status === 'confirmed' && booking.expected_arrival_time && !booking.arrived_at && (
        <p className="booking-arrival-notice" role="note">
          {t('booking.arrivalNotice', { time: formatArrivalTime(booking.expected_arrival_time), hours: ARRIVAL_GRACE_HOURS })}
        </p>
      )}
      {booking.arrived_at && <p className="booking-arrival-notice">{t('bookings.arrived')}</p>}
      {booking.status === 'cancelled' && booking.cancellation_reason === 'no_arrival' && (
        <p className="booking-arrival-notice">{t('bookings.cancelledNoArrival')}</p>
      )}

      <div className="booking-card-footer">
        <div className={`booking-card-payment-status booking-card-payment-status--${booking.payment_status}`}>
          {t('bookings.payment', { status: statusText('status.payment', booking.payment_status, t) })}
        </div>
        <div className="booking-card-actions">
          {canCancel(booking) && (
            <button type="button" className="btn btn-secondary" onClick={() => setCancelling(true)}>
              {t('cancel.button')}
            </button>
          )}
          <Link
            to={`/property/${booking.property}`}
            className="btn btn-secondary"
          >
            {t('bookings.viewProperty')}
          </Link>
        </div>
      </div>
      {cancelling && (
        <CancelBookingDialog
          bookingId={booking.id}
          onClose={() => setCancelling(false)}
          onCancelled={cancelled => { setCancelling(false); onCancelled(cancelled) }}
        />
      )}
    </div>
  )
}

type BookingFilter = 'all' | 'upcoming' | 'completed' | 'cancelled'

const statusOfFilter = (filter: BookingFilter): string | undefined =>
  ({ all: undefined, upcoming: 'confirmed', completed: 'completed', cancelled: 'cancelled' })[filter]

export function BookingsPage() {
  const { t } = useI18n()
  const { isAuthenticated, user } = useAuth()
  const [bookings, setBookings] = useState<Booking[]>([])
  const [total, setTotal] = useState(0)
  const [nextPage, setNextPage] = useState<number | null>(null)
  const [loadingMore, setLoadingMore] = useState(false)
  const [loadMoreError, setLoadMoreError] = useState(false)
  // The filter the list on screen was loaded for: a page that arrives for another filter is dropped
  const shownFilter = useRef<BookingFilter>('all')
  const [filter, setFilter] = useState<BookingFilter>('all')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)

  useEffect(() => {
    if (!isAuthenticated) {
      setLoading(false)
      return
    }

    const loadBookings = async () => {
      setLoading(true)
      setError(null)
      shownFilter.current = filter
      setLoadingMore(false)
      
      const result = await accountAdapter.getBookings(statusOfFilter(filter))
      
      if (result.error) {
        setError(result.error)
      } else {
        setBookings(result.data?.results ?? [])
        setTotal(result.data?.count ?? 0)
        setNextPage(result.data?.next ? 2 : null)
        setLoadMoreError(false)
      }
      setLoading(false)
    }

    loadBookings()
  }, [isAuthenticated, filter])

  const handleLoadMore = async () => {
    if (nextPage === null) return
    setLoadingMore(true)
    setLoadMoreError(false)
    const result = await accountAdapter.getBookings(statusOfFilter(filter), undefined, nextPage)
    if (shownFilter.current !== filter) return
    if (result.error || !result.data) {
      setLoadMoreError(true)
    } else {
      const more = result.data
      // A booking can move between pages while the guest reads; the id keeps each one once
      setBookings(current => [...current, ...more.results.filter(row => !current.some(seen => seen.id === row.id))])
      setTotal(more.count)
      setNextPage(more.next ? nextPage + 1 : null)
    }
    setLoadingMore(false)
  }

  const handleCancelled = (cancelled: CancelledBooking) => {
    setBookings(current => current.map(booking => (booking.id === cancelled.id ? { ...booking, status: 'cancelled' } : booking)))
    setNotice(t('cancel.done'))
  }

  const filteredBookings = bookings.filter(booking => {
    if (filter === 'all') return true
    if (filter === 'upcoming') {
      return booking.status === 'confirmed'
    }
    if (filter === 'completed') {
      return booking.status === 'completed'
    }
    if (filter === 'cancelled') {
      return booking.status === 'cancelled'
    }
    return true
  })

  if (!isAuthenticated) {
    return (
      <div className="bookings-page">
        <div className="container">
          <EmptyState
            headingLevel={1}
            icon={<Lock size={40} />}
            title={t('common.signInRequired')}
            message={t('bookings.signInText')}
            ctaText={t('auth.signIn')}
            ctaLink="/login"
          />
        </div>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="bookings-page">
        <div className="container">
          <div className="loading-state">
            <div className="spinner" role="status" aria-live="polite">
              <span className="sr-only">{t('common.loading')}</span>
            </div>
            <p>{t('bookings.loading')}</p>
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bookings-page">
        <div className="container">
          <div className="error-state" role="alert" aria-live="assertive">
            <p>{error}</p>
            <button 
              onClick={() => window.location.reload()}
              className="btn btn-primary"
            >
              {t('common.tryAgain')}
            </button>
          </div>
        </div>
      </div>
    )
  }

  // Only a guest with no bookings at all gets the bare empty screen; an empty filter keeps the buttons to switch back
  if (filteredBookings.length === 0 && filter === 'all') {
    return (
      <div className="bookings-page">
        <div className="container">
          <EmptyState
            icon={<Calendar size={40} />}
            title={t('bookings.emptyTitle')}
            message={t(canUsePartnerPanel(user) ? 'bookings.emptyTextOwner' : 'bookings.emptyText')}
            ctaText={t('bookings.emptyCta')}
            ctaLink="/"
            headingLevel={1}
          />
        </div>
      </div>
    )
  }

  return (
    <div className="bookings-page">
      <div className="container">
        <h1 className="bookings-page-title">{t('bookings.title')}</h1>
        
        <div className="bookings-filters">
          <button
            className={`bookings-filter ${filter === 'all' ? 'bookings-filter--active' : ''}`}
            onClick={() => setFilter('all')}
            aria-label={t('bookings.showAll')}
          >
            {t('bookings.filterAll')}
          </button>
          <button
            className={`bookings-filter ${filter === 'upcoming' ? 'bookings-filter--active' : ''}`}
            onClick={() => setFilter('upcoming')}
            aria-label={t('bookings.showUpcoming')}
          >
            {t('bookings.filterUpcoming')}
          </button>
          <button
            className={`bookings-filter ${filter === 'completed' ? 'bookings-filter--active' : ''}`}
            onClick={() => setFilter('completed')}
            aria-label={t('bookings.showCompleted')}
          >
            {t('bookings.filterCompleted')}
          </button>
          <button
            className={`bookings-filter ${filter === 'cancelled' ? 'bookings-filter--active' : ''}`}
            onClick={() => setFilter('cancelled')}
            aria-label={t('bookings.showCancelled')}
          >
            {t('bookings.filterCancelled')}
          </button>
        </div>
        
        {notice && <p role="status" className="alert alert-success bookings-notice">{notice}</p>}

        {filteredBookings.length === 0 ? (
          <EmptyState
            icon={<Calendar size={40} />}
            title={t('bookings.emptyTitle')}
            message={t('bookings.emptyText')}
            ctaText={t('bookings.emptyCta')}
            ctaLink="/"
          />
        ) : (
          <>
            <div className="bookings-list">
              {filteredBookings.map((booking) => (
                <BookingCard key={booking.id} booking={booking} onCancelled={handleCancelled} />
              ))}
            </div>

            <div className="bookings-more">
              <p className="bookings-shown">{t('bookings.shown', { shown: bookings.length, total })}</p>
              {loadMoreError && <p role="alert" className="alert alert-error">{t('bookings.loadMoreFailed')}</p>}
              {nextPage !== null && (
                <button type="button" className="btn btn-secondary" onClick={handleLoadMore} disabled={loadingMore}>
                  {loadingMore ? t('bookings.loadingMore') : t('bookings.loadMore')}
                </button>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  )
}

export default BookingsPage
