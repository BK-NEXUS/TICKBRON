import { useState } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { adminAdapter, SupportLookupBooking } from '../adapters/adminAdapter'
import { EmptyState } from '../components/EmptyState'

export function SupportLookupPage() {
  const { user, isAuthenticated } = useAuth()
  const [referenceCode, setReferenceCode] = useState('')
  const [booking, setBooking] = useState<SupportLookupBooking | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [searched, setSearched] = useState(false)

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!referenceCode.trim()) {
      setError('Please enter a reference code')
      return
    }

    setLoading(true)
    setError(null)
    setSearched(true)

    try {
      const response = await adminAdapter.lookupBookingByReferenceCode({ reference_code: referenceCode.trim() })
      
      if (response.error) {
        setError(response.error)
        setBooking(null)
      } else if (response.data) {
        setBooking(response.data)
        setError(null)
      }
    } catch (err) {
      setError('Failed to look up booking. Please try again.')
      setBooking(null)
    } finally {
      setLoading(false)
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    })
  }

  const formatCurrency = (amount: number, currency: string) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency,
    }).format(amount)
  }

  const getStatusClass = (status: string) => {
    switch (status.toLowerCase()) {
      case 'confirmed':
        return 'status-badge--confirmed'
      case 'pending':
        return 'status-badge--pending'
      case 'cancelled':
        return 'status-badge--cancelled'
      case 'completed':
        return 'status-badge--completed'
      default:
        return 'status-badge--unknown'
    }
  }

  if (!isAuthenticated || !user) {
    return (
      <div className="support-lookup-page">
        <div className="container">
          <EmptyState
            icon="🔒"
            title="Authentication required"
            message="Please sign in to access the support lookup tool."
            ctaText="Sign In"
            ctaLink="/login"
          />
        </div>
      </div>
    )
  }

  if (!user.is_staff && !user.is_superuser) {
    return (
      <div className="support-lookup-page">
        <div className="container">
          <EmptyState
            icon="🚫"
            title="Access Denied"
            message="You do not have permission to access the support lookup tool."
            ctaText="Go to Home"
            ctaLink="/"
          />
        </div>
      </div>
    )
  }

  return (
    <div className="support-lookup-page">
      <div className="container">
        <div className="admin-view-header">
          <h1 className="admin-view-title">Support Lookup</h1>
          <p className="admin-view-subtitle">Look up booking details by reference code</p>
        </div>

        <form onSubmit={handleSearch} className="support-search-form">
          <div className="search-input-group">
            <label htmlFor="reference-code">Reference Code</label>
            <input
              id="reference-code"
              type="text"
              value={referenceCode}
              onChange={(e) => setReferenceCode(e.target.value.toUpperCase())}
              placeholder="Enter 6-character reference code (e.g., ABC123)"
              maxLength={6}
              className="search-input"
              aria-describedby="reference-code-help"
            />
            <p id="reference-code-help" className="input-help">
              Enter the 6-character reference code provided by the guest
            </p>
          </div>
          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? 'Searching...' : 'Look Up Booking'}
          </button>
        </form>

        {error && (
          <div className="alert alert-error" role="alert" aria-live="polite">
            {error}
          </div>
        )}

        {searched && !loading && !error && !booking && (
          <div className="empty-state">
            <p>No booking found with reference code "{referenceCode}"</p>
            <p>Please verify the code and try again.</p>
          </div>
        )}

        {booking && (
          <div className="booking-details">
            <div className="booking-details-header">
              <h2>Booking Details</h2>
              <span className={`status-badge ${getStatusClass(booking.status)}`}>
                {booking.status}
              </span>
            </div>

            <div className="booking-details-grid">
              <div className="booking-detail-section">
                <h3>Reference Information</h3>
                <dl className="detail-list">
                  <div className="detail-item">
                    <dt>Reference Code</dt>
                    <dd className="reference-code">{booking.reference_code}</dd>
                  </div>
                  <div className="detail-item">
                    <dt>Booking ID</dt>
                    <dd>{booking.id}</dd>
                  </div>
                  <div className="detail-item">
                    <dt>Status</dt>
                    <dd>{booking.status}</dd>
                  </div>
                  <div className="detail-item">
                    <dt>Payment Status</dt>
                    <dd>{booking.payment_status}</dd>
                  </div>
                </dl>
              </div>

              <div className="booking-detail-section">
                <h3>Customer Information</h3>
                <dl className="detail-list">
                  <div className="detail-item">
                    <dt>Name</dt>
                    <dd>{booking.customer.full_name}</dd>
                  </div>
                  <div className="detail-item">
                    <dt>Email</dt>
                    <dd>
                      <a href={`mailto:${booking.customer.email}`} className="contact-link">
                        {booking.customer.email}
                      </a>
                    </dd>
                  </div>
                  <div className="detail-item">
                    <dt>Phone</dt>
                    <dd>
                      <a href={`tel:${booking.customer.phone_number}`} className="contact-link">
                        {booking.customer.phone_number}
                      </a>
                    </dd>
                  </div>
                  {booking.customer.whatsapp && (
                    <div className="detail-item">
                      <dt>WhatsApp</dt>
                      <dd>
                        <a href={`https://wa.me/${booking.customer.whatsapp}`} className="contact-link" target="_blank" rel="noopener noreferrer">
                          {booking.customer.whatsapp}
                        </a>
                      </dd>
                    </div>
                  )}
                  {booking.customer.telegram && (
                    <div className="detail-item">
                      <dt>Telegram</dt>
                      <dd>
                        <a href={`https://t.me/${booking.customer.telegram}`} className="contact-link" target="_blank" rel="noopener noreferrer">
                          {booking.customer.telegram}
                        </a>
                      </dd>
                    </div>
                  )}
                  <div className="detail-item">
                    <dt>Preferred Contact</dt>
                    <dd>{booking.customer.preferred_contact_method}</dd>
                  </div>
                </dl>
              </div>

              <div className="booking-detail-section">
                <h3>Property Information</h3>
                <dl className="detail-list">
                  <div className="detail-item">
                    <dt>Property Name</dt>
                    <dd>{booking.property.name}</dd>
                  </div>
                  <div className="detail-item">
                    <dt>Location</dt>
                    <dd>{booking.property.city}, {booking.property.country}</dd>
                  </div>
                  <div className="detail-item">
                    <dt>Address</dt>
                    <dd>{booking.property.address_line1}</dd>
                  </div>
                  <div className="detail-item">
                    <dt>Room</dt>
                    <dd>{booking.room.name} ({booking.room.room_type})</dd>
                  </div>
                </dl>
              </div>

              <div className="booking-detail-section">
                <h3>Booking Details</h3>
                <dl className="detail-list">
                  <div className="detail-item">
                    <dt>Check-in</dt>
                    <dd>{formatDate(booking.check_in)}</dd>
                  </div>
                  <div className="detail-item">
                    <dt>Check-out</dt>
                    <dd>{formatDate(booking.check_out)}</dd>
                  </div>
                  <div className="detail-item">
                    <dt>Number of Nights</dt>
                    <dd>{booking.number_of_nights}</dd>
                  </div>
                  <div className="detail-item">
                    <dt>Total Price</dt>
                    <dd>{formatCurrency(booking.total_price, booking.currency)}</dd>
                  </div>
                  <div className="detail-item">
                    <dt>Booked On</dt>
                    <dd>{formatDate(booking.created_at)}</dd>
                  </div>
                </dl>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default SupportLookupPage
