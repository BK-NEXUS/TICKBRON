import { useState, useEffect } from 'react'
import { SegmentedControl } from './SegmentedControl'
import { useParams, useNavigate } from 'react-router-dom'
import { adminAdapter } from '../adapters/adminAdapter'
import type { AdminCustomerProfile as AdminCustomerProfileData, InternalNote, CreateNoteRequest, UpdateNoteRequest } from '../adapters/adminAdapter'
import { useI18n } from '../i18n/I18nContext'
import { ContactLink } from './ContactLink'
import { telegramLink, whatsappLink } from '../utils/contactLinks'

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
  // Reloads when these inputs change; the loader is also the Retry action, so it stays a plain function
  // eslint-disable-next-line react-hooks/exhaustive-deps
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
      setError(t('admin.failedToLoadCustomer'))
    } finally {
      setLoading(false)
    }
  }

  const handleAddNote = async () => {
    if (!customerId || !noteText.trim()) {
      setNoteError(t('admin.noteEmpty'))
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
      setNoteError(t('admin.noteAddFailed'))
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
      setNoteError(t('admin.noteEmpty'))
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
      setNoteError(t('admin.noteUpdateFailed'))
    } finally {
      setNoteSaving(false)
    }
  }

  const handleDeleteNote = async (noteId: number) => {
    if (!customerId) return

    if (!confirm(t('admin.areYouSureYou'))) {
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
      setNoteError(t('admin.noteDeleteFailed'))
    } finally {
      setNoteSaving(false)
    }
  }

  const formatDate = (dateString: string) =>
    dateString ? formatLocalDate(dateString, { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : t('admin.na')

  const { t, formatMoney, formatDate: formatLocalDate } = useI18n()

  const formatCurrency = (amount: number, currency: string = 'USD') => {
    return formatMoney(amount, currency)
  }

  const formatPhoneNumber = (phone: string) => {
    // Remove any non-digit characters for tel: links
    return phone.replace(/[^0-9+]/g, '')
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
          {t('admin.loadingCustomerProfile')}
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
            <p>{t('admin.customerNotFound')}</p>
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
        className="btn btn-ghost btn-sm"
        onClick={() => navigate('/admin')}
        aria-label={t('admin.backToAdminDashboard')}
      >
        ← {t('admin.backArrow')}
      </button>

      {/* Customer Header */}
      <div className="customer-profile-header">
        <div className="customer-info">
          <h1 className="customer-name">{customer.full_name}</h1>
          <div className="customer-meta">
            <span className="customer-id">{t('admin.idValue', { id: customer.id })}</span>
            <span className="customer-joined">{t('admin.joinedOn', { date: formatDate(customer.date_joined) })}</span>
            {customer.last_login && (
              <span className="customer-last-login">{t('admin.lastLoginOn', { date: formatDate(customer.last_login) })}</span>
            )}
          </div>
        </div>

        {/* Contact Info */}
        <div className="customer-contact-info">
          <div className="contact-item">
            <span className="contact-label">{t('admin.email')}</span>
            <span className="contact-value">{customer.email}</span>
            <a
              href={`mailto:${customer.email}`}
              className="contact-link contact-link--email"
              aria-label={t('admin.sendEmailTo', { value: customer.email })}
            >
              {t('auth.email')}
            </a>
          </div>

          <div className="contact-item">
            <span className="contact-label">{t('admin.phone')}</span>
            <span className="contact-value">{customer.phone_number}</span>
            <a
              href={`tel:${formatPhoneNumber(customer.phone_number)}`}
              className="contact-link contact-link--phone"
              aria-label={t('admin.callNumber', { value: customer.phone_number })}
            >
              {t('admin.call')}
            </a>
          </div>

          {customer.whatsapp && (
            <div className="contact-item">
              <span className="contact-label">{t('admin.whatsapp')}</span>
              <span className="contact-value">{customer.whatsapp}</span>
              <ContactLink
                href={whatsappLink(customer.whatsapp)}
                className="contact-link contact-link--whatsapp"
                ariaLabel={t('admin.openWhatsApp', { value: customer.whatsapp })}
              >
                {t('profile.whatsapp')}
              </ContactLink>
            </div>
          )}

          {customer.telegram && (
            <div className="contact-item">
              <span className="contact-label">{t('admin.telegram')}</span>
              <span className="contact-value">{customer.telegram}</span>
              <ContactLink
                href={telegramLink(customer.telegram)}
                className="contact-link contact-link--telegram"
                ariaLabel={t('admin.openTelegram', { value: customer.telegram })}
              >
                {t('profile.telegram')}
              </ContactLink>
            </div>
          )}

          <div className="contact-item">
            <span className="contact-label">{t('admin.preferredContact2')}</span>
            <span className="contact-value contact-value--preferred">
              {customer.preferred_contact_method}
            </span>
          </div>
        </div>

        {/* Account Status */}
        <div className="customer-status">
          <div className="status-item">
            <span className="status-label">{t('admin.accountStatus')}</span>
            <span className={`status-badge ${customer.is_active ? 'status-badge--active' : 'status-badge--inactive'}`}>
              {customer.is_active ? t('profile.active') : t('profile.inactive')}
            </span>
          </div>
          <div className="status-item">
            <span className="status-label">{t('admin.emailVerified')}</span>
            <span className={`status-badge ${customer.email_verified ? 'status-badge--verified' : 'status-badge--unverified'}`}>
              {customer.email_verified ? t('profile.verified') : t('admin.unverified')}
            </span>
          </div>
          <div className="status-item">
            <span className="status-label">{t('admin.phoneVerified')}</span>
            <span className={`status-badge ${customer.phone_verified ? 'status-badge--verified' : 'status-badge--unverified'}`}>
              {customer.phone_verified ? t('profile.verified') : t('admin.unverified')}
            </span>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <SegmentedControl<TabType>
        mode="tabs"
        aria-label={t('admin.customerSections')}
        value={activeTab}
        onChange={setActiveTab}
        options={[
          { value: 'bookings', label: t('admin.tabBookings', { count: profile.bookings.length }), controls: 'bookings-panel' },
          { value: 'payments', label: t('admin.tabPayments', { count: profile.payments.length }), controls: 'payments-panel' },
          { value: 'notes', label: t('admin.tabNotes', { count: profile.internal_notes.length }), controls: 'notes-panel' },
        ]}
      />

      {/* Tab Content */}
      <div className="customer-tab-content">
        {activeTab === 'bookings' && (
          <div className="tab-panel" id="bookings-panel" role="tabpanel">
            <div className="bookings-filter">
              <label htmlFor="booking-filter" className="filter-label">
                {t('admin.filterBookings')}
              </label>
              <select
                id="booking-filter"
                className="filter-select"
                value={bookingFilter}
                onChange={(e) => setBookingFilter(e.target.value as BookingFilterType)}
                aria-label={t('admin.filterBookingsByStatus')}
              >
                <option value="all">{t('admin.allBookings')}</option>
                <option value="upcoming">{t('bookings.filterUpcoming')}</option>
                <option value="completed">{t('pay.statusName.completed')}</option>
                <option value="cancelled">{t('status.booking.cancelled')}</option>
              </select>
            </div>

            {profile.bookings.length === 0 ? (
              <div className="empty-state">
                <p>{t('admin.noBookingsFoundFor')}</p>
              </div>
            ) : (
              <table className="bookings-table" role="table" aria-label={t('admin.customerBookings')}>
                <thead>
                  <tr>
                    <th scope="col">{t('status.reference')}</th>
                    <th scope="col">{t('crumb.property')}</th>
                    <th scope="col">{t('admin.city')}</th>
                    <th scope="col">{t('searchForm.checkIn')}</th>
                    <th scope="col">{t('searchForm.checkOut')}</th>
                    <th scope="col">{t('status.nights')}</th>
                    <th scope="col">{t('booking.total')}</th>
                    <th scope="col">{t('partner.status')}</th>
                    <th scope="col">{t('admin.payment')}</th>
                    <th scope="col">{t('status.created')}</th>
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
                <p>{t('admin.noPaymentsFoundFor')}</p>
              </div>
            ) : (
              <table className="payments-table" role="table" aria-label={t('admin.customerPayments')}>
                <thead>
                  <tr>
                    <th scope="col">{t('admin.id')}</th>
                    <th scope="col">{t('admin.bookingId')}</th>
                    <th scope="col">{t('admin.provider')}</th>
                    <th scope="col">{t('admin.amount')}</th>
                    <th scope="col">{t('partner.status')}</th>
                    <th scope="col">{t('status.created')}</th>
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
                {t('admin.addInternalNote')}
              </label>
              <textarea
                id="new-note"
                className="note-textarea"
                value={noteText}
                onChange={(e) => setNoteText(e.target.value)}
                placeholder={t('admin.enterInternalNoteFor')}
                rows={3}
                aria-label={t('admin.newInternalNote')}
              />
              <div className="note-actions">
                <button
                  className="btn btn-primary btn-sm"
                  onClick={handleAddNote}
                  disabled={noteSaving || !noteText.trim()}
                  aria-label={t('admin.addNote')}
                >
                  {noteSaving ? t('admin.adding') : t('admin.addNote2')}
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
                <p>{t('admin.noInternalNotesFor')}</p>
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
                        <span className="note-created">{t('admin.noteCreated', { date: formatDate(note.created_at) })}</span>
                        {note.updated_at !== note.created_at && (
                          <span className="note-updated">{t('admin.noteUpdated', { date: formatDate(note.updated_at) })}</span>
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
                          aria-label={t('admin.editNoteFrom', { author: note.author_name })}
                        />
                        <div className="note-edit-actions">
                          <button
                            className="btn btn-primary btn-sm"
                            onClick={() => handleUpdateNote(note.id)}
                            disabled={noteSaving || !editingNoteText.trim()}
                            aria-label={t('admin.saveNote')}
                          >
                            {noteSaving ? t('profile.saving') : t('partner.save')}
                          </button>
                          <button
                            className="btn btn-secondary btn-sm"
                            onClick={handleCancelEditNote}
                            aria-label={t('admin.cancelEdit')}
                          >
                            {t('common.cancel')}
                          </button>
                        </div>
                      </div>
                    ) : (
                      <div className="note-content">
                        <p className="note-text">{note.note}</p>
                        <div className="note-actions">
                          <button
                            className="btn btn-secondary btn-sm"
                            onClick={() => handleEditNote(note)}
                            aria-label={t('admin.editNoteFrom', { author: note.author_name })}
                          >
                            {t('partner.edit')}
                          </button>
                          <button
                            className="btn btn-danger btn-sm"
                            onClick={() => handleDeleteNote(note.id)}
                            aria-label={t('admin.deleteNoteFrom', { author: note.author_name })}
                          >
                            {t('partner.delete')}
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
