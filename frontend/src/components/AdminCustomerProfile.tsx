import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { adminAdapter } from '../adapters/adminAdapter'
import type { AdminCustomerProfile as AdminCustomerProfileData, InternalNote, CreateNoteRequest, UpdateNoteRequest } from '../adapters/adminAdapter'

type TabType = 'bookings' | 'payments' | 'notes'
type BookingFilterType = 'all' | 'upcoming' | 'completed' | 'cancelled'

export function AdminCustomerProfile() {
  const { customerId } = useParams<{ customerId: string }>()
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState<TabType>('bookings')
  const [bookingFilter, setBookingFilter] = useState<BookingFilterType>('all')
  
  const [profile, setProfile] = useState<AdminCustomerProfileData | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  // Internal notes state
  const [noteText, setNoteText] = useState('')
  const [editingNoteId, setEditingNoteId] = useState<number | null>(null)
  const [editingNoteText, setEditingNoteText] = useState('')
  const [noteError, setNoteError] = useState<string | null>(null)
  const [noteSaving, setNoteSaving] = useState(false)

  useEffect(() => {
    if (customerId) {
      loadProfile()
    }
  }, [customerId, bookingFilter])

  const loadProfile = async () => {
    if (!customerId) return

    setLoading(true)
    setError(null)

    try {
      const response = await adminAdapter.getCustomerProfile(Number(customerId), { booking_filter: bookingFilter })
      
      if (response.error) {
        setError(response.error)
      } else if (response.data) {
        setProfile(response.data)
      }
    } catch (err) {
      setError('Failed to load customer profile. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleAddNote = async () => {
    if (!customerId || !noteText.trim()) {
      setNoteError('Please enter a note')
      return
    }

    setNoteSaving(true)
    setNoteError(null)

    try {
      const noteData: CreateNoteRequest = { note: noteText.trim() }
      const response = await adminAdapter.createInternalNote(Number(customerId), noteData)
      
      if (response.error) {
        setNoteError(response.error)
      } else if (response.data) {
        setNoteText('')
        // Reload profile to get updated notes
        await loadProfile()
      }
    } catch (err) {
      setNoteError('Failed to add note. Please try again.')
    } finally {
      setNoteSaving(false)
    }
  }

  const handleEditNote = (note: InternalNote) => {
    setEditingNoteId(note.id)
    setEditingNoteText(note.note)
  }

  const handleCancelEditNote = () => {
    setEditingNoteId(null)
    setEditingNoteText('')
  }

  const handleUpdateNote = async (noteId: number) => {
    if (!customerId || !editingNoteText.trim()) {
      setNoteError('Please enter a note')
      return
    }

    setNoteSaving(true)
    setNoteError(null)

    try {
      const noteData: UpdateNoteRequest = { note: editingNoteText.trim() }
      const response = await adminAdapter.updateInternalNote(Number(customerId), noteId, noteData)
      
      if (response.error) {
        setNoteError(response.error)
      } else if (response.data) {
        setEditingNoteId(null)
        setEditingNoteText('')
        // Reload profile to get updated notes
        await loadProfile()
      }
    } catch (err) {
      setNoteError('Failed to update note. Please try again.')
    } finally {
      setNoteSaving(false)
    }
  }

  const handleDeleteNote = async (noteId: number) => {
    if (!customerId) return

    if (!confirm('Are you sure you want to delete this note?')) {
      return
    }

    setNoteSaving(true)
    setNoteError(null)

    try {
      const response = await adminAdapter.deleteInternalNote(Number(customerId), noteId)
      
      if (response.error) {
        setNoteError(response.error)
      } else {
        // Reload profile to get updated notes
        await loadProfile()
      }
    } catch (err) {
      setNoteError('Failed to delete note. Please try again.')
    } finally {
      setNoteSaving(false)
    }
  }

  const formatDate = (dateString: string) => {
    if (!dateString) return 'N/A'
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  const formatCurrency = (amount: number, currency: string = 'USD') => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency,
    }).format(amount)
  }

  const formatPhoneNumber = (phone: string) => {
    // Remove any non-digit characters for tel: links
    return phone.replace(/[^0-9+]/g, '')
  }

  const getWhatsAppLink = (phone: string) => {
    const cleanedPhone = phone.replace(/[^0-9]/g, '')
    return `https://wa.me/${cleanedPhone}`
  }

  const getTelegramLink = (telegram: string) => {
    // Remove @ if present
    const cleanedUsername = telegram.startsWith('@') ? telegram.slice(1) : telegram
    return `https://t.me/${cleanedUsername}`
  }

  const getBookingStatusClass = (status: string) => {
    const statusMap: Record<string, string> = {
      pending: 'status-badge--pending',
      confirmed: 'status-badge--confirmed',
      completed: 'status-badge--completed',
      cancelled: 'status-badge--cancelled',
      no_show: 'status-badge--no-show',
    }
    return statusMap[status] || 'status-badge--default'
  }

  const getPaymentStatusClass = (status: string) => {
    const statusMap: Record<string, string> = {
      pending: 'status-badge--pending',
      paid: 'status-badge--paid',
      failed: 'status-badge--failed',
      refunded: 'status-badge--refunded',
      partially_refunded: 'status-badge--partially-refunded',
    }
    return statusMap[status] || 'status-badge--default'
  }

  if (loading) {
    return (
      <div className="admin-customer-profile">
        <div className="loading-state" role="status" aria-live="polite">
          Loading customer profile...
        </div>
      </div>
    )
  }

  if (error || !profile) {
    return (
      <div className="admin-customer-profile">
        {error && (
          <div className="alert alert-error" role="alert" aria-live="polite">
            {error}
          </div>
        )}
        {!profile && !error && (
          <div className="empty-state">
            <p>Customer not found.</p>
          </div>
        )}
      </div>
    )
  }

  const customer = profile.customer

  return (
    <div className="admin-customer-profile">
      {/* Back button */}
      <button
        className="back-button"
        onClick={() => navigate('/admin')}
        aria-label="Back to admin dashboard"
      >
        ← Back to Admin Dashboard
      </button>

      {/* Customer Header */}
      <div className="customer-profile-header">
        <div className="customer-info">
          <h1 className="customer-name">{customer.full_name}</h1>
          <div className="customer-meta">
            <span className="customer-id">ID: {customer.id}</span>
            <span className="customer-joined">Joined: {formatDate(customer.date_joined)}</span>
            {customer.last_login && (
              <span className="customer-last-login">Last login: {formatDate(customer.last_login)}</span>
            )}
          </div>
        </div>

        {/* Contact Info */}
        <div className="customer-contact-info">
          <div className="contact-item">
            <span className="contact-label">Email:</span>
            <span className="contact-value">{customer.email}</span>
            <a
              href={`mailto:${customer.email}`}
              className="contact-link contact-link--email"
              aria-label={`Send email to ${customer.email}`}
            >
              Email
            </a>
          </div>

          <div className="contact-item">
            <span className="contact-label">Phone:</span>
            <span className="contact-value">{customer.phone_number}</span>
            <a
              href={`tel:${formatPhoneNumber(customer.phone_number)}`}
              className="contact-link contact-link--phone"
              aria-label={`Call ${customer.phone_number}`}
            >
              Call
            </a>
          </div>

          {customer.whatsapp && (
            <div className="contact-item">
              <span className="contact-label">WhatsApp:</span>
              <span className="contact-value">{customer.whatsapp}</span>
              <a
                href={getWhatsAppLink(customer.whatsapp)}
                target="_blank"
                rel="noopener noreferrer"
                className="contact-link contact-link--whatsapp"
                aria-label={`Open WhatsApp chat with ${customer.whatsapp}`}
              >
                WhatsApp
              </a>
            </div>
          )}

          {customer.telegram && (
            <div className="contact-item">
              <span className="contact-label">Telegram:</span>
              <span className="contact-value">{customer.telegram}</span>
              <a
                href={getTelegramLink(customer.telegram)}
                target="_blank"
                rel="noopener noreferrer"
                className="contact-link contact-link--telegram"
                aria-label={`Open Telegram chat with ${customer.telegram}`}
              >
                Telegram
              </a>
            </div>
          )}

          <div className="contact-item">
            <span className="contact-label">Preferred Contact:</span>
            <span className="contact-value contact-value--preferred">
              {customer.preferred_contact_method}
            </span>
          </div>
        </div>

        {/* Account Status */}
        <div className="customer-status">
          <div className="status-item">
            <span className="status-label">Account Status:</span>
            <span className={`status-badge ${customer.is_active ? 'status-badge--active' : 'status-badge--inactive'}`}>
              {customer.is_active ? 'Active' : 'Inactive'}
            </span>
          </div>
          <div className="status-item">
            <span className="status-label">Email Verified:</span>
            <span className={`status-badge ${customer.email_verified ? 'status-badge--verified' : 'status-badge--unverified'}`}>
              {customer.email_verified ? 'Verified' : 'Unverified'}
            </span>
          </div>
          <div className="status-item">
            <span className="status-label">Phone Verified:</span>
            <span className={`status-badge ${customer.phone_verified ? 'status-badge--verified' : 'status-badge--unverified'}`}>
              {customer.phone_verified ? 'Verified' : 'Unverified'}
            </span>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="customer-tabs" role="tablist">
        <button
          className={`tab-button ${activeTab === 'bookings' ? 'tab-button--active' : ''}`}
          onClick={() => setActiveTab('bookings')}
          role="tab"
          aria-selected={activeTab === 'bookings'}
          aria-controls="bookings-panel"
        >
          Bookings ({profile.bookings.length})
        </button>
        <button
          className={`tab-button ${activeTab === 'payments' ? 'tab-button--active' : ''}`}
          onClick={() => setActiveTab('payments')}
          role="tab"
          aria-selected={activeTab === 'payments'}
          aria-controls="payments-panel"
        >
          Payments ({profile.payments.length})
        </button>
        <button
          className={`tab-button ${activeTab === 'notes' ? 'tab-button--active' : ''}`}
          onClick={() => setActiveTab('notes')}
          role="tab"
          aria-selected={activeTab === 'notes'}
          aria-controls="notes-panel"
        >
          Internal Notes ({profile.internal_notes.length})
        </button>
      </div>

      {/* Tab Content */}
      <div className="customer-tab-content">
        {activeTab === 'bookings' && (
          <div className="tab-panel" id="bookings-panel" role="tabpanel">
            <div className="bookings-filter">
              <label htmlFor="booking-filter" className="filter-label">
                Filter bookings:
              </label>
              <select
                id="booking-filter"
                className="filter-select"
                value={bookingFilter}
                onChange={(e) => setBookingFilter(e.target.value as BookingFilterType)}
                aria-label="Filter bookings by status"
              >
                <option value="all">All Bookings</option>
                <option value="upcoming">Upcoming</option>
                <option value="completed">Completed</option>
                <option value="cancelled">Cancelled</option>
              </select>
            </div>

            {profile.bookings.length === 0 ? (
              <div className="empty-state">
                <p>No bookings found for this customer.</p>
              </div>
            ) : (
              <table className="bookings-table" role="table" aria-label="Customer bookings">
                <thead>
                  <tr>
                    <th scope="col">Reference</th>
                    <th scope="col">Property</th>
                    <th scope="col">City</th>
                    <th scope="col">Check-in</th>
                    <th scope="col">Check-out</th>
                    <th scope="col">Nights</th>
                    <th scope="col">Total</th>
                    <th scope="col">Status</th>
                    <th scope="col">Payment</th>
                    <th scope="col">Created</th>
                  </tr>
                </thead>
                <tbody>
                  {profile.bookings.map(booking => (
                    <tr key={booking.id}>
                      <td className="booking-reference">{booking.reference_code}</td>
                      <td className="booking-property">{booking.property_name}</td>
                      <td className="booking-city">{booking.property_city}</td>
                      <td className="booking-check-in">{formatDate(booking.check_in)}</td>
                      <td className="booking-check-out">{formatDate(booking.check_out)}</td>
                      <td className="booking-nights">{booking.number_of_nights}</td>
                      <td className="booking-total">{formatCurrency(booking.total_price, booking.currency)}</td>
                      <td className="booking-status">
                        <span className={`status-badge ${getBookingStatusClass(booking.status)}`}>
                          {booking.status}
                        </span>
                      </td>
                      <td className="booking-payment-status">
                        <span className={`status-badge ${getPaymentStatusClass(booking.payment_status)}`}>
                          {booking.payment_status}
                        </span>
                      </td>
                      <td className="booking-created">{formatDate(booking.created_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}

        {activeTab === 'payments' && (
          <div className="tab-panel" id="payments-panel" role="tabpanel">
            {profile.payments.length === 0 ? (
              <div className="empty-state">
                <p>No payments found for this customer.</p>
              </div>
            ) : (
              <table className="payments-table" role="table" aria-label="Customer payments">
                <thead>
                  <tr>
                    <th scope="col">ID</th>
                    <th scope="col">Booking ID</th>
                    <th scope="col">Provider</th>
                    <th scope="col">Amount</th>
                    <th scope="col">Status</th>
                    <th scope="col">Created</th>
                  </tr>
                </thead>
                <tbody>
                  {profile.payments.map(payment => (
                    <tr key={payment.id}>
                      <td className="payment-id">{payment.id}</td>
                      <td className="payment-booking-id">{payment.booking_id}</td>
                      <td className="payment-provider">{payment.provider}</td>
                      <td className="payment-amount">{formatCurrency(payment.amount, payment.currency)}</td>
                      <td className="payment-status">
                        <span className={`status-badge ${getPaymentStatusClass(payment.status)}`}>
                          {payment.status}
                        </span>
                      </td>
                      <td className="payment-created">{formatDate(payment.created_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}

        {activeTab === 'notes' && (
          <div className="tab-panel" id="notes-panel" role="tabpanel">
            {/* Add Note Form */}
            <div className="add-note-form">
              <label htmlFor="new-note" className="note-label">
                Add Internal Note:
              </label>
              <textarea
                id="new-note"
                className="note-textarea"
                value={noteText}
                onChange={(e) => setNoteText(e.target.value)}
                placeholder="Enter internal note for staff reference..."
                rows={3}
                aria-label="New internal note"
              />
              <div className="note-actions">
                <button
                  className="note-button note-button--primary"
                  onClick={handleAddNote}
                  disabled={noteSaving || !noteText.trim()}
                  aria-label="Add note"
                >
                  {noteSaving ? 'Adding...' : 'Add Note'}
                </button>
              </div>
            </div>

            {noteError && (
              <div className="alert alert-error" role="alert" aria-live="polite">
                {noteError}
              </div>
            )}

            {/* Notes List */}
            {profile.internal_notes.length === 0 ? (
              <div className="empty-state">
                <p>No internal notes for this customer.</p>
              </div>
            ) : (
              <div className="notes-list">
                {profile.internal_notes.map(note => (
                  <div key={note.id} className="note-item">
                    <div className="note-header">
                      <div className="note-author">
                        <span className="note-author-name">{note.author_name}</span>
                        <span className="note-author-email">{note.author_email}</span>
                      </div>
                      <div className="note-dates">
                        <span className="note-created">Created: {formatDate(note.created_at)}</span>
                        {note.updated_at !== note.created_at && (
                          <span className="note-updated">Updated: {formatDate(note.updated_at)}</span>
                        )}
                      </div>
                    </div>

                    {editingNoteId === note.id ? (
                      <div className="note-edit-form">
                        <textarea
                          className="note-textarea note-textarea--edit"
                          value={editingNoteText}
                          onChange={(e) => setEditingNoteText(e.target.value)}
                          rows={3}
                          aria-label={`Edit note from ${note.author_name}`}
                        />
                        <div className="note-edit-actions">
                          <button
                            className="note-button note-button--primary"
                            onClick={() => handleUpdateNote(note.id)}
                            disabled={noteSaving || !editingNoteText.trim()}
                            aria-label="Save note"
                          >
                            {noteSaving ? 'Saving...' : 'Save'}
                          </button>
                          <button
                            className="note-button note-button--secondary"
                            onClick={handleCancelEditNote}
                            aria-label="Cancel edit"
                          >
                            Cancel
                          </button>
                        </div>
                      </div>
                    ) : (
                      <div className="note-content">
                        <p className="note-text">{note.note}</p>
                        <div className="note-actions">
                          <button
                            className="note-action-button"
                            onClick={() => handleEditNote(note)}
                            aria-label={`Edit note from ${note.author_name}`}
                          >
                            Edit
                          </button>
                          <button
                            className="note-action-button note-action-button--danger"
                            onClick={() => handleDeleteNote(note.id)}
                            aria-label={`Delete note from ${note.author_name}`}
                          >
                            Delete
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export default AdminCustomerProfile
