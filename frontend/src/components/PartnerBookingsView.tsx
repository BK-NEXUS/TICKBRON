import { useState, useEffect } from 'react'
import { partnerAdapter, PartnerBooking } from '../adapters/partnerAdapter'

export function PartnerBookingsView() {
  const [bookings, setBookings] = useState<PartnerBooking[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [paymentStatusFilter, setPaymentStatusFilter] = useState<string>('all')

  useEffect(() => {
    loadBookings()
  }, [statusFilter, paymentStatusFilter])

  const loadBookings = async () => {
    setLoading(true)
    setError(null)

    try {
      const statusParam = statusFilter === 'all' ? undefined : statusFilter
      const paymentStatusParam = paymentStatusFilter === 'all' ? undefined : paymentStatusFilter

      const response = await partnerAdapter.getPartnerBookings(statusParam, paymentStatusParam)
      
      if (response.error) {
        setError(response.error)
      } else if (response.data) {
        // Sort by check-in date (most recent first)
        const sortedBookings = [...response.data].sort((a, b) => 
          new Date(b.check_in).getTime() - new Date(a.check_in).getTime()
        )
        setBookings(sortedBookings)
      }
    } catch (err) {
      setError('Failed to load bookings. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const getStatusClass = (status: string) => {
    switch (status) {
      case 'confirmed':
        return 'booking-status--confirmed'
      case 'pending':
        return 'booking-status--pending'
      case 'completed':
        return 'booking-status--completed'
      case 'cancelled':
        return 'booking-status--cancelled'
      case 'no_show':
        return 'booking-status--no-show'
      default:
        return 'booking-status--unknown'
    }
  }

  const getPaymentStatusClass = (paymentStatus: string) => {
    switch (paymentStatus) {
      case 'paid':
        return 'payment-status--paid'
      case 'pending':
        return 'payment-status--pending'
      case 'failed':
        return 'payment-status--failed'
      case 'refunded':
        return 'payment-status--refunded'
      case 'partially_refunded':
        return 'payment-status--partially-refunded'
      default:
        return 'payment-status--unknown'
    }
  }

  const formatCurrency = (amount: number, currency: string) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency,
    }).format(amount)
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    })
  }

  return (
    <div className="partner-bookings-view">
      <div className="bookings-view-header">
        <h1 className="bookings-view-title">Partner Bookings</h1>
        <p className="bookings-view-subtitle">View and manage bookings for your properties</p>
      </div>

      <div className="bookings-filters">
        <div className="filter-group">
          <label htmlFor="status-filter">Booking Status:</label>
          <select
            id="status-filter"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="filter-select"
            aria-label="Filter by booking status"
          >
            <option value="all">All Statuses</option>
            <option value="pending">Pending</option>
            <option value="confirmed">Confirmed</option>
            <option value="completed">Completed</option>
            <option value="cancelled">Cancelled</option>
            <option value="no_show">No Show</option>
          </select>
        </div>

        <div className="filter-group">
          <label htmlFor="payment-status-filter">Payment Status:</label>
          <select
            id="payment-status-filter"
            value={paymentStatusFilter}
            onChange={(e) => setPaymentStatusFilter(e.target.value)}
            className="filter-select"
            aria-label="Filter by payment status"
          >
            <option value="all">All Payment Statuses</option>
            <option value="pending">Pending</option>
            <option value="paid">Paid</option>
            <option value="failed">Failed</option>
            <option value="refunded">Refunded</option>
            <option value="partially_refunded">Partially Refunded</option>
          </select>
        </div>
      </div>

      {error && (
        <div className="alert alert-error" role="alert" aria-live="polite">
          {error}
        </div>
      )}

      {loading ? (
        <div className="loading-state" role="status" aria-live="polite">
          Loading bookings...
        </div>
      ) : bookings.length === 0 ? (
        <div className="empty-state">
          <p>No bookings found matching your filters.</p>
          <p>Bookings will appear here once guests start booking your properties.</p>
        </div>
      ) : (
        <div className="bookings-list">
          {bookings.map(booking => (
            <div key={booking.id} className="booking-card">
              <div className="booking-card-header">
                <div className="booking-property-info">
                  <h3 className="booking-property-name">{booking.property_name}</h3>
                  <p className="booking-confirmation-code">Confirmation: {booking.confirmation_code}</p>
                </div>
                <div className="booking-status-badges">
                  <span className={`booking-status ${getStatusClass(booking.status)}`}>
                    {booking.status.replace('_', ' ').toUpperCase()}
                  </span>
                  <span className={`payment-status ${getPaymentStatusClass(booking.payment_status)}`}>
                    {booking.payment_status.replace('_', ' ').toUpperCase()}
                  </span>
                </div>
              </div>

              <div className="booking-card-body">
                <div className="booking-details-grid">
                  <div className="booking-detail">
                    <span className="detail-label">Guest:</span>
                    <span className="detail-value">{booking.guest_name}</span>
                  </div>
                  <div className="booking-detail">
                    <span className="detail-label">Check-in:</span>
                    <span className="detail-value">{formatDate(booking.check_in)}</span>
                  </div>
                  <div className="booking-detail">
                    <span className="detail-label">Check-out:</span>
                    <span className="detail-value">{formatDate(booking.check_out)}</span>
                  </div>
                  <div className="booking-detail">
                    <span className="detail-label">Nights:</span>
                    <span className="detail-value">{booking.number_of_nights}</span>
                  </div>
                  <div className="booking-detail">
                    <span className="detail-label">Guests:</span>
                    <span className="detail-value">{booking.guest_count}</span>
                  </div>
                  <div className="booking-detail">
                    <span className="detail-label">Total:</span>
                    <span className="detail-value">{formatCurrency(booking.total_price, booking.currency)}</span>
                  </div>
                </div>

                {booking.special_requests && (
                  <div className="booking-special-requests">
                    <span className="detail-label">Special Requests:</span>
                    <p className="detail-value">{booking.special_requests}</p>
                  </div>
                )}
              </div>

              <div className="booking-card-footer">
                <div className="booking-dates">
                  <small className="booking-created">
                    Booked on {formatDate(booking.created_at)}
                  </small>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
