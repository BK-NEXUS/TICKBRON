import { ChargeMain, ChargeNotes } from '../components/ChargeAmount'
import { NoShowRefundNote } from '../components/NoShowRefundNote'
import { useI18n } from '../i18n/I18nContext'
import { statusText } from '../utils/statusText'
import { useState, useEffect } from 'react'
import { Check, Copy } from 'lucide-react'
import { Lock, Calendar } from 'lucide-react'
import { Link } from 'react-router-dom'
import { accountAdapter, Booking } from '../adapters/accountAdapter'
import { EmptyState } from '../components/EmptyState'
import { useAuth } from '../contexts/AuthContext'

interface BookingCardProps {
  booking: Booking
}

function BookingCard({ booking }: BookingCardProps) {
  const { t, formatDate } = useI18n()
  const [copied, setCopied] = useState(false)

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
      
      <NoShowRefundNote info={booking} />

      <div className="booking-card-footer">
        <div className={`booking-card-payment-status booking-card-payment-status--${booking.payment_status}`}>
          {t('bookings.payment', { status: statusText('status.payment', booking.payment_status, t) })}
        </div>
        <Link 
          to={`/property/${booking.property}`}
          className="btn btn-secondary"
        >
          {t('bookings.viewProperty')}
        </Link>
      </div>
    </div>
  )
}

type BookingFilter = 'all' | 'upcoming' | 'completed' | 'cancelled'

export function BookingsPage() {
  const { t } = useI18n()
  const { isAuthenticated } = useAuth()
  const [bookings, setBookings] = useState<Booking[]>([])
  const [filter, setFilter] = useState<BookingFilter>('all')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!isAuthenticated) {
      setLoading(false)
      return
    }

    const loadBookings = async () => {
      setLoading(true)
      setError(null)
      
      let statusFilter: string | undefined
      if (filter === 'upcoming') {
        statusFilter = 'confirmed'
      } else if (filter === 'completed') {
        statusFilter = 'completed'
      } else if (filter === 'cancelled') {
        statusFilter = 'cancelled'
      }
      
      const result = await accountAdapter.getBookings(statusFilter)
      
      if (result.error) {
        setError(result.error)
      } else {
        setBookings(result.data || [])
      }
      setLoading(false)
    }

    loadBookings()
  }, [isAuthenticated, filter])

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

  if (filteredBookings.length === 0) {
    return (
      <div className="bookings-page">
        <div className="container">
          <EmptyState
            icon={<Calendar size={40} />}
            title={t('bookings.emptyTitle')}
            message={t('bookings.emptyText')}
            ctaText={t('bookings.emptyCta')}
            ctaLink="/"
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
        
        <div className="bookings-list">
          {filteredBookings.map((booking) => (
            <BookingCard key={booking.id} booking={booking} />
          ))}
        </div>
      </div>
    </div>
  )
}

export default BookingsPage
