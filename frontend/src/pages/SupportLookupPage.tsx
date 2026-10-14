import { useState } from 'react'
import { Lock, Ban } from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'
import { adminAdapter, SupportLookupBooking } from '../adapters/adminAdapter'
import { EmptyState } from '../components/EmptyState'
import { useI18n } from '../i18n/I18nContext'
import { ContactLink } from '../components/ContactLink'
import { telegramLink, whatsappLink } from '../utils/contactLinks'

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
      setError(t('admin.pleaseEnterAReference'))
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
      setError(t('admin.failedToLookUp'))
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

  const { t, formatMoney } = useI18n()

  const formatCurrency = (amount: number, currency: string) => {
    return formatMoney(amount, currency)
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
            headingLevel={1}
            icon={<Lock size={40} />}
            title={t('partner.authenticationRequired')}
            message={t('admin.pleaseSignInTo2')}
            ctaText={t('auth.signIn')}
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
            headingLevel={1}
            icon={<Ban size={40} />}
            title={t('denied.title')}
            message={t('admin.youDoNotHave2')}
            ctaText={t('admin.goToHome')}
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
          <h1 className="admin-view-title">{t('crumb.supportLookup')}</h1>
          <p className="admin-view-subtitle">{t('admin.lookUpBookingDetails')}</p>
        </div>

        <form onSubmit={handleSearch} className="support-search-form">
          <div className="search-input-group">
            <label htmlFor="reference-code">{t('admin.referenceCode')}</label>
            <input
              id="reference-code"
              type="text"
              value={referenceCode}
              onChange={(e) => setReferenceCode(e.target.value.toUpperCase())}
              placeholder={t('admin.enter6CharacterReference')}
              maxLength={6}
              className="search-input"
              aria-describedby="reference-code-help"
            />
            <p id="reference-code-help" className="input-help">
              {t('admin.enterThe6Character')}
            </p>
          </div>
          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? t('admin.searching') : t('admin.lookUpBooking')}
          </button>
        </form>

        {error && (
          <div className="alert alert-error" role="alert" aria-live="polite">
            {error}
          </div>
        )}

        {searched && !loading && !error && !booking && (
          <div className="empty-state">
            <p>{t('admin.noBookingFound', { code: referenceCode })}</p>
            <p>{t('admin.pleaseVerifyTheCode')}</p>
          </div>
        )}

        {booking && (
          <div className="booking-details">
            <div className="booking-details-header">
              <h2>{t('pay.bookingTitle')}</h2>
              <span className={`status-badge ${getStatusClass(booking.status)}`}>
                {booking.status}
              </span>
            </div>

            <div className="booking-details-grid">
              <div className="booking-detail-section">
                <h3>{t('admin.referenceInformation')}</h3>
                <dl className="detail-list">
                  <div className="detail-item">
                    <dt>{t('admin.referenceCode')}</dt>
                    <dd className="reference-code">{booking.reference_code}</dd>
                  </div>
                  <div className="detail-item">
                    <dt>{t('admin.bookingId')}</dt>
                    <dd>{booking.id}</dd>
                  </div>
                  <div className="detail-item">
                    <dt>{t('partner.status')}</dt>
                    <dd>{booking.status}</dd>
                  </div>
                  <div className="detail-item">
                    <dt>{t('admin.paymentStatus')}</dt>
                    <dd>{booking.payment_status}</dd>
                  </div>
                </dl>
              </div>

              <div className="booking-detail-section">
                <h3>{t('admin.customerInformation')}</h3>
                <dl className="detail-list">
                  <div className="detail-item">
                    <dt>{t('admin.name')}</dt>
                    <dd>{booking.customer.full_name}</dd>
                  </div>
                  <div className="detail-item">
                    <dt>{t('auth.email')}</dt>
                    <dd>
                      <a href={`mailto:${booking.customer.email}`} className="contact-link">
                        {booking.customer.email}
                      </a>
                    </dd>
                  </div>
                  <div className="detail-item">
                    <dt>{t('profile.contact.phone')}</dt>
                    <dd>
                      <a href={`tel:${booking.customer.phone_number}`} className="contact-link">
                        {booking.customer.phone_number}
                      </a>
                    </dd>
                  </div>
                  {booking.customer.whatsapp && (
                    <div className="detail-item">
                      <dt>{t('profile.whatsapp')}</dt>
                      <dd>
                        <ContactLink href={whatsappLink(booking.customer.whatsapp)} className="contact-link" fallback={booking.customer.whatsapp}>
                          {booking.customer.whatsapp}
                        </ContactLink>
                      </dd>
                    </div>
                  )}
                  {booking.customer.telegram && (
                    <div className="detail-item">
                      <dt>{t('profile.telegram')}</dt>
                      <dd>
                        <ContactLink href={telegramLink(booking.customer.telegram)} className="contact-link" fallback={booking.customer.telegram}>
                          {booking.customer.telegram}
                        </ContactLink>
                      </dd>
                    </div>
                  )}
                  <div className="detail-item">
                    <dt>{t('admin.preferredContact')}</dt>
                    <dd>{booking.customer.preferred_contact_method}</dd>
                  </div>
                </dl>
              </div>

              <div className="booking-detail-section">
                <h3>{t('admin.propertyInformation')}</h3>
                <dl className="detail-list">
                  <div className="detail-item">
                    <dt>{t('admin.propertyName')}</dt>
                    <dd>{booking.property.name}</dd>
                  </div>
                  <div className="detail-item">
                    <dt>{t('property.location')}</dt>
                    <dd>{booking.property.city}, {booking.property.country}</dd>
                  </div>
                  <div className="detail-item">
                    <dt>{t('admin.address')}</dt>
                    <dd>{booking.property.address_line1}</dd>
                  </div>
                  <div className="detail-item">
                    <dt>{t('admin.room')}</dt>
                    <dd>{booking.room ? `${booking.room.name} (${booking.room.rate_plan})` : 'N/A'}</dd>
                  </div>
                </dl>
              </div>

              <div className="booking-detail-section">
                <h3>{t('pay.bookingTitle')}</h3>
                <dl className="detail-list">
                  <div className="detail-item">
                    <dt>{t('searchForm.checkIn')}</dt>
                    <dd>{formatDate(booking.check_in)}</dd>
                  </div>
                  <div className="detail-item">
                    <dt>{t('searchForm.checkOut')}</dt>
                    <dd>{formatDate(booking.check_out)}</dd>
                  </div>
                  <div className="detail-item">
                    <dt>{t('admin.numberOfNights')}</dt>
                    <dd>{booking.number_of_nights}</dd>
                  </div>
                  <div className="detail-item">
                    <dt>{t('admin.totalPrice')}</dt>
                    <dd>{formatCurrency(booking.total_price, booking.currency)}</dd>
                  </div>
                  <div className="detail-item">
                    <dt>{t('admin.bookedOn')}</dt>
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
