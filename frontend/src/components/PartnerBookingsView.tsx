import { useState, useEffect } from 'react'
import { partnerAdapter, PartnerBooking } from '../adapters/partnerAdapter'
import { useI18n } from '../i18n/I18nContext'
import { NoShowReportDialog } from './NoShowReportDialog'

export function PartnerBookingsView() {
  const [bookings, setBookings] = useState<PartnerBooking[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [paymentStatusFilter, setPaymentStatusFilter] = useState<string>('all')
  const [reportableOnly, setReportableOnly] = useState(false)
  const [reportTarget, setReportTarget] = useState<PartnerBooking | null>(null)
  const [reportSent, setReportSent] = useState(false)

  useEffect(() => {
    loadBookings()
  // Reloads when these inputs change; the loader is also the Retry action, so it stays a plain function
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [statusFilter, paymentStatusFilter, reportableOnly])

  const loadBookings = async () => {
    setLoading(true)
    setError(null)

    try {
      const statusParam = statusFilter === 'all' ? undefined : statusFilter
      const paymentStatusParam = paymentStatusFilter === 'all' ? undefined : paymentStatusFilter

      const response = await partnerAdapter.getPartnerBookings(statusParam, paymentStatusParam, reportableOnly)
      
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
      setError(t('partner.failedToLoadBookings'))
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

  const { t, formatMoney, formatDate: formatLocalDate } = useI18n()

  const formatCurrency = (amount: number, currency: string) => {
    return formatMoney(amount, currency)
  }

  const formatDate = (dateString: string) => formatLocalDate(dateString)

  return (
    <div className="partner-bookings-view">
      <div className="bookings-view-header">
        <h1 className="bookings-view-title">{t('partner.partnerBookings')}</h1>
        <p className="bookings-view-subtitle">{t('partner.viewAndManageBookings')}</p>
      </div>

      <div className="bookings-filters">
        <div className="filter-group">
          <label htmlFor="status-filter">{t('partner.bookingStatus')}</label>
          <select
            id="status-filter"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="filter-select"
            aria-label={t('partner.filterByBookingStatus')}
          >
            <option value="all">{t('partner.allStatuses')}</option>
            <option value="pending">{t('pay.statusName.pending')}</option>
            <option value="confirmed">{t('status.booking.confirmed')}</option>
            <option value="completed">{t('pay.statusName.completed')}</option>
            <option value="cancelled">{t('status.booking.cancelled')}</option>
            <option value="no_show">{t('partner.noShow')}</option>
          </select>
        </div>

        <div className="filter-group">
          <label htmlFor="payment-status-filter">{t('partner.paymentStatus')}</label>
          <select
            id="payment-status-filter"
            value={paymentStatusFilter}
            onChange={(e) => setPaymentStatusFilter(e.target.value)}
            className="filter-select"
            aria-label={t('partner.filterByPaymentStatus')}
          >
            <option value="all">{t('partner.allPaymentStatuses')}</option>
            <option value="pending">{t('pay.statusName.pending')}</option>
            <option value="paid">{t('status.payment.paid')}</option>
            <option value="failed">{t('pay.statusName.failed')}</option>
            <option value="refunded">{t('pay.statusName.refunded')}</option>
            <option value="partially_refunded">{t('partner.partiallyRefunded')}</option>
          </select>
        </div>

        <div className="filter-group">
          <label className="filter-checkbox">
            <input
              type="checkbox"
              checked={reportableOnly}
              onChange={(e) => setReportableOnly(e.target.checked)}
            />
            {t('noShow.onlyReportable')}
          </label>
        </div>
      </div>

      {reportSent && (
        <p className="alert alert-success" role="status" aria-label={t('noShow.sent')}>{t('noShow.sentText')}</p>
      )}

      {error && (
        <div className="alert alert-error" role="alert" aria-live="polite">
          {error}
        </div>
      )}

      {loading ? (
        <div className="loading-state" role="status" aria-live="polite">
          {t('bookings.loading')}
        </div>
      ) : bookings.length === 0 ? (
        <div className="empty-state">
          <p>{t('partner.noBookingsFoundMatching')}</p>
          <p>{t('partner.bookingsWillAppearHere')}</p>
        </div>
      ) : (
        <div className="bookings-list">
          {bookings.map(booking => (
            <div key={booking.id} className="booking-card">
              <div className="booking-card-header">
                <div className="booking-property-info">
                  <h3 className="booking-property-name">{booking.property_name}</h3>
                  <p className="booking-confirmation-code">{t('partner.confirmationLine', { code: booking.confirmation_code })}</p>
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
                    <span className="detail-label">{t('partner.guest')}</span>
                    <span className="detail-value">{booking.guest_name}</span>
                  </div>
                  <div className="booking-detail">
                    <span className="detail-label">{t('rooms.checkIn')}</span>
                    <span className="detail-value">{formatDate(booking.check_in)}</span>
                  </div>
                  <div className="booking-detail">
                    <span className="detail-label">{t('rooms.checkOut')}</span>
                    <span className="detail-value">{formatDate(booking.check_out)}</span>
                  </div>
                  <div className="booking-detail">
                    <span className="detail-label">{t('bookings.nights')}</span>
                    <span className="detail-value">{booking.number_of_nights}</span>
                  </div>
                  <div className="booking-detail">
                    <span className="detail-label">{t('booking.guests')}</span>
                    <span className="detail-value">{booking.guest_count}</span>
                  </div>
                  <div className="booking-detail">
                    <span className="detail-label">{t('rooms.total')}</span>
                    <span className="detail-value">{formatCurrency(booking.total_price, booking.currency)}</span>
                  </div>
                </div>

                {booking.special_requests && (
                  <div className="booking-special-requests">
                    <span className="detail-label">{t('booking.specialRequests')}</span>
                    <p className="detail-value">{booking.special_requests}</p>
                  </div>
                )}
              </div>

              <div className="booking-card-footer">
                <div className="booking-dates">
                  <small className="booking-created">
                    {t('partner.bookedOn', { date: formatDate(booking.created_at) })}
                  </small>
                </div>
                {booking.can_report_no_show && (
                  <div className="booking-no-show">
                    {booking.report_deadline && (
                      <small>{t('noShow.reportUntil', { date: formatDate(booking.report_deadline) })}</small>
                    )}
                    <button type="button" className="btn btn-secondary btn-sm" onClick={() => setReportTarget(booking)}>
                      {t('noShow.reportButton')}
                    </button>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {reportTarget && (
        <NoShowReportDialog
          booking={reportTarget}
          onClose={() => setReportTarget(null)}
          onReported={() => {
            setReportTarget(null)
            setReportSent(true)
            void loadBookings()
          }}
        />
      )}
    </div>
  )
}
