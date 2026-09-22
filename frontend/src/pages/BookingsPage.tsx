import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { accountAdapter, Booking } from '../adapters/accountAdapter'
import { EmptyState } from '../components/EmptyState'
import { useAuth } from '../contexts/AuthContext'

interface BookingCardProps {
  booking: Booking
}

function BookingCard({ booking }: BookingCardProps) {
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
            <span className="booking-card-confirmation-label">Booking Reference:</span>
            <div className="booking-card-confirmation-code-wrapper">
              <span className="booking-card-confirmation-code">
                {booking.confirmation_code}
              </span>
              <button
                className="booking-card-copy-btn"
                onClick={handleCopyCode}
                aria-label="Copy booking reference code"
                title="Copy booking reference code"
              >
                {copied ? '✓' : '📋'}
              </button>
            </div>
          </div>
        </div>
        <div className={`booking-card-status booking-card-status--${booking.status}`}>
          {booking.status.charAt(0).toUpperCase() + booking.status.slice(1)}
        </div>
      </div>
      
      <div className="booking-card-details">
        <div className="booking-card-detail">
          <span className="booking-card-detail-label">Check-in:</span>
          <span className="booking-card-detail-value">{booking.check_in}</span>
        </div>
        <div className="booking-card-detail">
          <span className="booking-card-detail-label">Check-out:</span>
          <span className="booking-card-detail-value">{booking.check_out}</span>
        </div>
        <div className="booking-card-detail">
          <span className="booking-card-detail-label">Nights:</span>
          <span className="booking-card-detail-value">{booking.number_of_nights}</span>
        </div>
        <div className="booking-card-detail">
          <span className="booking-card-detail-label">Guests:</span>
          <span className="booking-card-detail-value">{booking.guest_count}</span>
        </div>
        <div className="booking-card-detail">
          <span className="booking-card-detail-label">Total:</span>
          <span className="booking-card-detail-value">
            ${booking.total_price} {booking.currency}
          </span>
        </div>
      </div>
      
      <div className="booking-card-footer">
        <div className={`booking-card-payment-status booking-card-payment-status--${booking.payment_status}`}>
          Payment: {booking.payment_status.charAt(0).toUpperCase() + booking.payment_status.slice(1)}
        </div>
        <Link 
          to={`/property/${booking.property}`}
          className="btn btn-secondary"
        >
          View Property
        </Link>
      </div>
    </div>
  )
}

type BookingFilter = 'all' | 'upcoming' | 'completed' | 'cancelled'

export function BookingsPage() {
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
            icon="🔒"
            title="Sign in required"
            message="Please sign in to view your booking history."
            ctaText="Sign In"
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
              <span className="sr-only">Loading...</span>
            </div>
            <p>Loading bookings...</p>
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
              Try Again
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
            icon="📅"
            title="No bookings yet"
            message="Start exploring amazing properties and book your first stay."
            ctaText="Search Properties"
            ctaLink="/"
          />
        </div>
      </div>
    )
  }

  return (
    <div className="bookings-page">
      <div className="container">
        <h1 className="bookings-page-title">My Bookings</h1>
        
        <div className="bookings-filters">
          <button
            className={`bookings-filter ${filter === 'all' ? 'bookings-filter--active' : ''}`}
            onClick={() => setFilter('all')}
            aria-label="Show all bookings"
          >
            All
          </button>
          <button
            className={`bookings-filter ${filter === 'upcoming' ? 'bookings-filter--active' : ''}`}
            onClick={() => setFilter('upcoming')}
            aria-label="Show upcoming bookings"
          >
            Upcoming
          </button>
          <button
            className={`bookings-filter ${filter === 'completed' ? 'bookings-filter--active' : ''}`}
            onClick={() => setFilter('completed')}
            aria-label="Show completed bookings"
          >
            Completed
          </button>
          <button
            className={`bookings-filter ${filter === 'cancelled' ? 'bookings-filter--active' : ''}`}
            onClick={() => setFilter('cancelled')}
            aria-label="Show cancelled bookings"
          >
            Cancelled
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
