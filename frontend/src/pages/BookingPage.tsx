import { useState, useEffect, useRef } from 'react'
import { Check, Clock } from 'lucide-react'
import { useNavigate, useLocation } from 'react-router-dom'
import { bookingAdapter, BookingCreateRequest, Booking } from '../adapters/bookingAdapter'
import { propertyAdapter, Property, RoomType, RatePlan, StayQuote } from '../adapters/propertyAdapter'
import { paymentAdapter, PaymentProvider, PaymentTransaction, PaymentStatus } from '../adapters/paymentAdapter'
import { useAuth } from '../contexts/AuthContext'
import { PaymentMethodSelector } from '../components/PaymentMethodSelector'
import { PaymentProcessing } from '../components/PaymentProcessing'
import { PaymentConfirmation } from '../components/PaymentConfirmation'
import { PaymentFailure } from '../components/PaymentFailure'
import { PhoneInput } from '../components/PhoneInput'
import { isValidPhone, phoneErrorMessage } from '../utils/phone'
import { usePageTrail } from '../components/Breadcrumbs'
import { searchUrlForCity } from '../utils/searchFilters'
import { propertyDisplayName } from '../utils/propertyName'

interface BookingState {
  propertyId: number
  roomTypeId: number
  ratePlanId: number
  checkIn: string
  checkOut: string
  guestCount: number
  pricePerNight: number
  currency: string
}

interface GuestDetails {
  first_name: string
  last_name: string
  email: string
  phone_number?: string
  number_of_rooms: number
  children: number[]
  special_requests?: string
}

/**
 * BookingPage component for the booking flow
 * Includes guest details form, price summary, validation, and confirmation states
 */
export function BookingPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const { user, isAuthenticated } = useAuth()
  
  const [property, setProperty] = useState<Property | null>(null)
  const [roomType, setRoomType] = useState<RoomType | null>(null)
  const [ratePlan, setRatePlan] = useState<RatePlan | null>(null)
  const [bookingState, setBookingState] = useState<BookingState | null>(null)
  const [guestDetails, setGuestDetails] = useState<GuestDetails>({
    first_name: '',
    last_name: '',
    email: '',
    phone_number: '',
    number_of_rooms: 1,
    children: [],
    special_requests: '',
  })
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({})
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [booking, setBooking] = useState<Booking | null>(null)

  // Home › City › Hotel › Booking
  usePageTrail(property ? [
    { label: property.city, to: searchUrlForCity(property.city) },
    { label: propertyDisplayName(property), to: `/property/${property.id}` },
    { label: 'Booking' },
  ] : null)
  const [error, setError] = useState<string | null>(null)
  const [step, setStep] = useState<'details' | 'payment' | 'processing' | 'confirmation' | 'success' | 'failure'>('details')
  const [selectedProvider, setSelectedProvider] = useState<PaymentProvider | null>(null)
  const [paymentTransaction, setPaymentTransaction] = useState<PaymentTransaction | null>(null)
  const [paymentStatus, setPaymentStatus] = useState<PaymentStatus>('pending')
  const [paymentError, setPaymentError] = useState<string | null>(null)

  // GET /properties/{id}/quote/: priced by the same backend code that charges the booking,
  // so the total shown here is the amount paid. There is no local fallback price.
  const [quote, setQuote] = useState<StayQuote | null>(null)
  const [quoteError, setQuoteError] = useState<string | null>(null)
  const quoteRequestId = useRef(0)
  const roomsForQuote = Math.max(1, guestDetails.number_of_rooms || 1)

  const calculateNumberOfNights = (): number => {
    if (!bookingState) return 0

    const checkIn = new Date(bookingState.checkIn)
    const checkOut = new Date(bookingState.checkOut)
    return Math.ceil((checkOut.getTime() - checkIn.getTime()) / (1000 * 60 * 60 * 24))
  }

  // Parse booking state from location state
  useEffect(() => {
    const state = location.state as BookingState
    if (!state) {
      setError('Missing booking information. Please select a room and try again.')
      setLoading(false)
      return
    }
    setBookingState(state)
    
    // Pre-fill guest details from user if authenticated
    if (user) {
      // Since checkpoint 21 most profiles only have full_name: first word = first name, rest = last name
      const [nameFromFull = '', ...restOfName] = (user.full_name || '').trim().split(/\s+/)
      setGuestDetails(prev => ({
        ...prev,
        first_name: user.first_name || nameFromFull,
        last_name: user.last_name || restOfName.join(' '),
        email: user.email || '',
        phone_number: user.phone_number || '',
      }))
    }
  }, [location.state, user])

  // Price the stay (again when the number of rooms changes)
  useEffect(() => {
    if (!bookingState) return
    const requestId = ++quoteRequestId.current
    setQuote(null)
    setQuoteError(null)
    const loadQuote = async () => {
      let response: Awaited<ReturnType<typeof propertyAdapter.getQuote>> | undefined
      try {
        response = await propertyAdapter.getQuote(bookingState.propertyId, {
          roomTypeId: bookingState.roomTypeId,
          ratePlanId: bookingState.ratePlanId,
          checkIn: bookingState.checkIn,
          checkOut: bookingState.checkOut,
          rooms: roomsForQuote,
        })
      } catch {
        response = undefined
      }
      if (requestId !== quoteRequestId.current) return
      if (response?.data) {
        setQuote(response.data)
      } else {
        setQuoteError(response?.error || 'Could not price this stay. Please go back and choose other dates.')
      }
    }
    loadQuote()
  }, [bookingState, roomsForQuote])

  // Load property, room type, and rate plan data
  useEffect(() => {
    const loadData = async () => {
      if (!bookingState) return

      try {
        setLoading(true)
        
        // Load property details
        const propertyResponse = await propertyAdapter.getPropertyById(bookingState.propertyId)
        if (propertyResponse.error || !propertyResponse.data) {
          setError(propertyResponse.error || 'Failed to load property details')
          setLoading(false)
          return
        }
        setProperty(propertyResponse.data)

        // Find room type and rate plan from property data
        const foundRoomType = propertyResponse.data.room_types?.find(rt => rt.id === bookingState.roomTypeId)
        const foundRatePlan = foundRoomType?.rate_plans?.find(rp => rp.id === bookingState.ratePlanId)
        
        if (!foundRoomType || !foundRatePlan) {
          setError('Room or rate plan not found')
          setLoading(false)
          return
        }
        
        setRoomType(foundRoomType)
        setRatePlan(foundRatePlan)
        setLoading(false)
      } catch (err) {
        setError('Failed to load booking information')
        setLoading(false)
      }
    }

    loadData()
  }, [bookingState])

  // The booking's own total once it exists (the amount charged), else the backend quote;
  // null while neither is known or when the stay cannot be booked
  const totalPrice = booking ? Number(booking.total_price) : quote ? Number(quote.total_price) : null
  const currency = booking?.currency || quote?.currency || bookingState?.currency || 'USD'
  const formatMoney = (value: number) => new Intl.NumberFormat('en-US', {
    style: 'currency', currency, minimumFractionDigits: 0, maximumFractionDigits: 2,
  }).format(value)

  /** "$60 × 2 nights" when every night costs the same, otherwise "2 nights"; "× N rooms" when more than one */
  const priceBreakdownLabel = (): string => {
    const nights = quote?.number_of_nights ?? calculateNumberOfNights()
    const prices = (quote?.nights ?? []).map(night => Number(night.price))
    const uniform = prices.length > 0 && prices.every(price => price === prices[0])
    const format = (value: number) => new Intl.NumberFormat('en-US', {
      style: 'currency', currency, minimumFractionDigits: 0, maximumFractionDigits: 0,
    }).format(value)
    const nightWord = nights === 1 ? 'night' : 'nights'
    const nightsText = uniform ? `${format(prices[0])} × ${nights} ${nightWord}` : `${nights} ${nightWord}`
    return roomsForQuote > 1 ? `${nightsText} × ${roomsForQuote} rooms` : nightsText
  }

  // Redirect if not authenticated
  useEffect(() => {
    if (!isAuthenticated && !loading) {
      navigate('/login', { state: { from: location.pathname, state: location.state } })
    }
  }, [isAuthenticated, loading, navigate, location])

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target
    setField(name, value)
  }

  const setField = (name: string, value: string) => {
    setGuestDetails(prev => ({ ...prev, [name]: value }))
    // Clear validation error for this field
    if (validationErrors[name]) {
      setValidationErrors(prev => {
        const newErrors = { ...prev }
        delete newErrors[name]
        return newErrors
      })
    }
  }

  const handleChildrenChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { value } = e.target
    const ages = value.split(',').map(age => parseInt(age.trim())).filter(age => !isNaN(age) && age >= 0)
    setGuestDetails(prev => ({ ...prev, children: ages }))
  }

  const addChild = () => {
    setGuestDetails(prev => ({ ...prev, children: [...prev.children, 0] }))
  }

  const removeChild = (index: number) => {
    setGuestDetails(prev => ({
      ...prev,
      children: prev.children.filter((_, i) => i !== index)
    }))
  }

  const updateChildAge = (index: number, age: number) => {
    setGuestDetails(prev => ({
      ...prev,
      children: prev.children.map((a, i) => i === index ? age : a)
    }))
  }

  const validateGuestDetails = (): boolean => {
    const errors: Record<string, string> = {}

    if (!guestDetails.first_name.trim()) {
      errors.first_name = 'First name is required'
    } else if (guestDetails.first_name.trim().length < 2) {
      errors.first_name = 'First name must be at least 2 characters'
    }

    if (!guestDetails.last_name.trim()) {
      errors.last_name = 'Last name is required'
    } else if (guestDetails.last_name.trim().length < 2) {
      errors.last_name = 'Last name must be at least 2 characters'
    }

    if (!guestDetails.email.trim()) {
      errors.email = 'Email is required'
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(guestDetails.email)) {
      errors.email = 'Please enter a valid email address'
    }

    if (guestDetails.phone_number && !isValidPhone(guestDetails.phone_number)) {
      errors.phone_number = phoneErrorMessage()
    }

    if (guestDetails.number_of_rooms < 1) {
      errors.number_of_rooms = 'Number of rooms must be at least 1'
    }

    if (guestDetails.children.some(age => age < 0 || age > 17)) {
      errors.children = 'Children ages must be between 0 and 17'
    }

    setValidationErrors(errors)
    return Object.keys(errors).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!validateGuestDetails()) {
      return
    }

    if (!bookingState || !property) {
      setError('Missing booking information')
      return
    }

    setSubmitting(true)
    setError(null)

    try {
      const bookingRequest: BookingCreateRequest = {
        property_id: bookingState.propertyId,
        room_type_id: bookingState.roomTypeId,
        rate_plan_id: bookingState.ratePlanId,
        check_in: bookingState.checkIn,
        check_out: bookingState.checkOut,
        guest_count: bookingState.guestCount,
        guest_full_name: `${guestDetails.first_name} ${guestDetails.last_name}`,
        guest_phone: guestDetails.phone_number || undefined,
        guest_email: guestDetails.email,
        number_of_rooms: guestDetails.number_of_rooms,
        children: guestDetails.children.length > 0 ? guestDetails.children : undefined,
        special_requests: guestDetails.special_requests || undefined,
      }

      const response = await bookingAdapter.createBooking(bookingRequest)
      
      if (response.error || !response.data) {
        setError(response.error || 'Failed to create booking')
        setSubmitting(false)
        return
      }

      setBooking(response.data)
      setStep('payment')
      setSubmitting(false)
    } catch (err) {
      setError('Failed to create booking. Please try again.')
      setSubmitting(false)
    }
  }

  const handleConfirmBooking = async () => {
    if (!booking || !selectedProvider) {
      setError('Missing booking or payment method')
      return
    }

    setSubmitting(true)
    setError(null)
    setPaymentError(null)
    setStep('processing')
    setPaymentStatus('pending')

    try {
      // Generate idempotency key for payment
      const idempotencyKey = paymentAdapter.generateIdempotencyKey()
      
      // Get client IP and user agent for audit trail
      const clientIp = await paymentAdapter.getClientIp()
      const userAgent = paymentAdapter.getUserAgent()

      // Create payment transaction
      const paymentRequest = {
        idempotency_key: idempotencyKey,
        booking: booking.id,
        provider: selectedProvider,
        amount: booking.total_price,
        currency: booking.currency,
        client_ip: clientIp || undefined,
        user_agent: userAgent,
      }

      setPaymentStatus('processing')
      const paymentResponse = await paymentAdapter.createPayment(paymentRequest)

      if (paymentResponse.error || !paymentResponse.data) {
        setPaymentError(paymentResponse.error || 'Failed to initiate payment')
        setPaymentStatus('failed')
        setStep('failure')
        setSubmitting(false)
        return
      }

      setPaymentTransaction(paymentResponse.data)
      setPaymentStatus('processing')

      // Confirm payment
      const confirmResponse = await paymentAdapter.confirmPayment(paymentResponse.data.id)

      if (confirmResponse.error || !confirmResponse.data) {
        setPaymentError(confirmResponse.error || 'Failed to confirm payment')
        setPaymentStatus('failed')
        setStep('failure')
        setSubmitting(false)
        return
      }

      setPaymentTransaction(confirmResponse.data)
      setPaymentStatus('completed')
      setStep('confirmation')
      setSubmitting(false)
    } catch (err) {
      setPaymentError('Payment processing failed. Please try again.')
      setPaymentStatus('failed')
      setStep('failure')
      setSubmitting(false)
    }
  }

  const handleRetryPayment = () => {
    setPaymentError(null)
    setPaymentTransaction(null)
    setPaymentStatus('pending')
    setStep('payment')
  }

  const handleTryDifferentMethod = () => {
    setPaymentError(null)
    setPaymentTransaction(null)
    setPaymentStatus('pending')
    setSelectedProvider(null)
    setStep('payment')
  }

  const handleCancelBooking = () => {
    navigate('/search')
  }

  const handleBackToProperty = () => {
    if (property) {
      navigate(`/property/${property.id}`)
    } else {
      navigate('/search')
    }
  }

  if (loading) {
    return (
      <div className="booking-page booking-page--loading">
        <div className="container">
          <div className="loading-state" role="status" aria-live="polite">
            <div className="loading-spinner"></div>
            <p>Loading booking information...</p>
          </div>
        </div>
      </div>
    )
  }

  if (error && !booking) {
    return (
      <div className="booking-page booking-page--error">
        <div className="container">
          <div className="error-state" role="alert" aria-live="assertive">
            <h2>Booking Error</h2>
            <p>{error}</p>
            <button 
              className="btn btn-primary"
              onClick={handleBackToProperty}
              aria-label="Return to property page"
            >
              Back to Property
            </button>
          </div>
        </div>
      </div>
    )
  }

  if (step === 'success' && booking) {
    return (
      <div className="booking-page booking-page--success">
        <div className="container">
          <div className="success-state" role="status" aria-live="polite">
            <div className="success-icon">
              <Check size={36} />
            </div>
            <h1>Booking Confirmed!</h1>
            <p>Your booking has been successfully created.</p>
            
            <div className="booking-confirmation-details">
              <div className="booking-confirmation-item">
                <span className="booking-confirmation-label">Confirmation Code:</span>
                <span className="booking-confirmation-value">{booking.confirmation_code}</span>
              </div>
              <div className="booking-confirmation-item">
                <span className="booking-confirmation-label">Property:</span>
                <span className="booking-confirmation-value">{booking.property_name}</span>
              </div>
              <div className="booking-confirmation-item">
                <span className="booking-confirmation-label">Check-in:</span>
                <span className="booking-confirmation-value">
                  {new Date(booking.check_in).toLocaleDateString('en-US', { 
                    weekday: 'long', 
                    year: 'numeric', 
                    month: 'long', 
                    day: 'numeric' 
                  })}
                </span>
              </div>
              <div className="booking-confirmation-item">
                <span className="booking-confirmation-label">Check-out:</span>
                <span className="booking-confirmation-value">
                  {new Date(booking.check_out).toLocaleDateString('en-US', { 
                    weekday: 'long', 
                    year: 'numeric', 
                    month: 'long', 
                    day: 'numeric' 
                  })}
                </span>
              </div>
              <div className="booking-confirmation-item">
                <span className="booking-confirmation-label">Total Price:</span>
                <span className="booking-confirmation-value">{formatMoney(Number(booking.total_price))}</span>
              </div>
            </div>

            <div className="booking-confirmation-actions">
              <button 
                className="btn btn-primary"
                onClick={() => navigate('/bookings')}
                aria-label="View my bookings"
              >
                View My Bookings
              </button>
              <button 
                className="btn btn-secondary"
                onClick={handleBackToProperty}
                aria-label="Return to property page"
              >
                Back to Property
              </button>
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (step === 'payment' && booking) {
    return (
      <div className="booking-page booking-page--payment">
        <div className="container booking-page-container">
          <div className="booking-page-main">
            <div className="booking-page-header">
              <button 
                className="btn btn-link booking-page-back"
                onClick={() => setStep('details')}
                aria-label="Back to guest details"
              >
                ← Back to Details
              </button>
              <h1>Payment Method</h1>
            </div>

            <PaymentMethodSelector
              selectedProvider={selectedProvider}
              onProviderSelect={setSelectedProvider}
              disabled={submitting}
            />

            {selectedProvider && (
              <div className="payment-method-actions">
                {error && (
                  <div className="booking-form-error" role="alert" aria-live="assertive">
                    {error}
                  </div>
                )}
                <button 
                  className="btn btn-primary btn-large"
                  onClick={handleConfirmBooking}
                  disabled={submitting}
                  aria-busy={submitting}
                >
                  {submitting ? 'Processing...' : `Pay with ${selectedProvider.charAt(0).toUpperCase() + selectedProvider.slice(1)}`}
                </button>
              </div>
            )}
          </div>

          <aside className="booking-page-sidebar">
            <div className="booking-summary-card">
              <h3 className="booking-summary-title">Price Summary</h3>
              
              {property && (
                <div className="booking-summary-property">
                  <div className="booking-summary-property-name">{property.translations[0]?.name || property.name}</div>
                  <div className="booking-summary-property-location">
                    {property.city}, {property.country}
                  </div>
                </div>
              )}

              {roomType && ratePlan && (
                <>
                  <div className="booking-summary-room">
                    <div className="booking-summary-room-name">{roomType.name}</div>
                    <div className="booking-summary-rate-plan">{ratePlan.name}</div>
                  </div>

                  {totalPrice !== null && (
                    <>
                      <div className="booking-summary-breakdown">
                        <div className="booking-summary-item">
                          <span className="booking-summary-label">{priceBreakdownLabel()}</span>
                          <span className="booking-summary-value">{formatMoney(totalPrice)}</span>
                        </div>
                      </div>

                      <div className="booking-summary-total">
                        <span className="booking-summary-total-label">Total</span>
                        <span className="booking-summary-total-value">{formatMoney(totalPrice)}</span>
                      </div>
                    </>
                  )}
                </>
              )}

              {booking && booking.expires_at && (
                <div className="booking-summary-expiry">
                  <div className="booking-summary-expiry-icon">
                    <Clock size={20} />
                  </div>
                  <div className="booking-summary-expiry-text">
                    <strong>Booking expires in 15 minutes</strong>
                    <div>Please complete your booking before {new Date(booking.expires_at).toLocaleTimeString()}</div>
                  </div>
                </div>
              )}
            </div>
          </aside>
        </div>
      </div>
    )
  }

  if (step === 'processing' && booking && selectedProvider) {
    return (
      <div className="booking-page booking-page--processing">
        <div className="container">
          <PaymentProcessing
            provider={selectedProvider}
            amount={booking.total_price}
            currency={booking.currency}
            status={paymentStatus}
          />
        </div>
      </div>
    )
  }

  if (step === 'confirmation' && paymentTransaction && booking) {
    return (
      <div className="booking-page booking-page--confirmation">
        <div className="container">
          <PaymentConfirmation
            payment={paymentTransaction}
            bookingDetails={{
              property_name: booking.property_name,
              check_in: booking.check_in,
              check_out: booking.check_out,
              confirmation_code: booking.confirmation_code,
            }}
            onViewBookings={() => navigate('/bookings')}
            onBackToProperty={handleBackToProperty}
          />
        </div>
      </div>
    )
  }

  if (step === 'failure' && booking && selectedProvider) {
    return (
      <div className="booking-page booking-page--failure">
        <div className="container">
          <PaymentFailure
            provider={selectedProvider}
            amount={booking.total_price}
            currency={booking.currency}
            error={paymentError || undefined}
            onRetry={handleRetryPayment}
            onTryDifferentMethod={handleTryDifferentMethod}
            onCancel={handleCancelBooking}
          />
        </div>
      </div>
    )
  }

  return (
    <div className="booking-page">
      <div className="container booking-page-container">
        <div className="booking-page-main">
          <div className="booking-page-header">
            <button 
              className="btn btn-link booking-page-back"
              onClick={handleBackToProperty}
              aria-label="Back to property"
            >
              ← Back to Property
            </button>
            <h1>Complete Your Booking</h1>
          </div>

          {step === 'details' && (
            <form onSubmit={handleSubmit} className="booking-form">
              <div className="booking-form-section">
                <h2 className="booking-form-section-title">Guest Details</h2>
                
                <div className="booking-form-row">
                  <div className="booking-form-field">
                    <label htmlFor="first_name" className="booking-form-label">
                      First Name <span className="required">*</span>
                    </label>
                    <input
                      type="text"
                      id="first_name"
                      name="first_name"
                      value={guestDetails.first_name}
                      onChange={handleInputChange}
                      className={`booking-form-input ${validationErrors.first_name ? 'booking-form-input--error' : ''}`}
                      aria-invalid={!!validationErrors.first_name}
                      aria-describedby={validationErrors.first_name ? 'first_name-error' : undefined}
                      autoComplete="given-name"
                      required
                    />
                    {validationErrors.first_name && (
                      <span id="first_name-error" className="booking-form-error" role="alert">
                        {validationErrors.first_name}
                      </span>
                    )}
                  </div>

                  <div className="booking-form-field">
                    <label htmlFor="last_name" className="booking-form-label">
                      Last Name <span className="required">*</span>
                    </label>
                    <input
                      type="text"
                      id="last_name"
                      name="last_name"
                      value={guestDetails.last_name}
                      onChange={handleInputChange}
                      className={`booking-form-input ${validationErrors.last_name ? 'booking-form-input--error' : ''}`}
                      aria-invalid={!!validationErrors.last_name}
                      aria-describedby={validationErrors.last_name ? 'last_name-error' : undefined}
                      autoComplete="family-name"
                      required
                    />
                    {validationErrors.last_name && (
                      <span id="last_name-error" className="booking-form-error" role="alert">
                        {validationErrors.last_name}
                      </span>
                    )}
                  </div>
                </div>

                <div className="booking-form-field">
                  <label htmlFor="email" className="booking-form-label">
                    Email <span className="required">*</span>
                  </label>
                  <input
                    type="email"
                    id="email"
                    name="email"
                    value={guestDetails.email}
                    onChange={handleInputChange}
                    className={`booking-form-input ${validationErrors.email ? 'booking-form-input--error' : ''}`}
                    aria-invalid={!!validationErrors.email}
                    aria-describedby={validationErrors.email ? 'email-error' : undefined}
                    autoComplete="email"
                    required
                  />
                  {validationErrors.email && (
                    <span id="email-error" className="booking-form-error" role="alert">
                      {validationErrors.email}
                    </span>
                  )}
                </div>

                <div className="booking-form-field">
                  <label htmlFor="phone_number" className="booking-form-label">
                    Phone Number
                  </label>
                  <PhoneInput
                    id="phone_number"
                    name="phone_number"
                    value={guestDetails.phone_number ?? ''}
                    onChange={(value) => setField('phone_number', value)}
                    className={`booking-form-input ${validationErrors.phone_number ? 'booking-form-input--error' : ''}`}
                    aria-invalid={!!validationErrors.phone_number}
                    aria-describedby={validationErrors.phone_number ? 'phone_number-error' : undefined}
                  />
                  {validationErrors.phone_number && (
                    <span id="phone_number-error" className="booking-form-error" role="alert">
                      {validationErrors.phone_number}
                    </span>
                  )}
                </div>

                <div className="booking-form-field">
                  <label htmlFor="number_of_rooms" className="booking-form-label">
                    Number of Rooms <span className="required">*</span>
                  </label>
                  <input
                    type="number"
                    id="number_of_rooms"
                    name="number_of_rooms"
                    value={guestDetails.number_of_rooms}
                    onChange={handleInputChange}
                    min="1"
                    className={`booking-form-input ${validationErrors.number_of_rooms ? 'booking-form-input--error' : ''}`}
                    aria-invalid={!!validationErrors.number_of_rooms}
                    aria-describedby={validationErrors.number_of_rooms ? 'number_of_rooms-error' : undefined}
                    required
                  />
                  {validationErrors.number_of_rooms && (
                    <span id="number_of_rooms-error" className="booking-form-error" role="alert">
                      {validationErrors.number_of_rooms}
                    </span>
                  )}
                </div>

                <div className="booking-form-field">
                  <label className="booking-form-label">Children (Ages 0-17)</label>
                  <div className="booking-form-children">
                    {guestDetails.children.map((age, index) => (
                      <div key={index} className="booking-form-child-item">
                        <label htmlFor={`child_age_${index}`} className="booking-form-child-label">
                          Child {index + 1}
                        </label>
                        <input
                          type="number"
                          id={`child_age_${index}`}
                          value={age}
                          onChange={(e) => updateChildAge(index, parseInt(e.target.value) || 0)}
                          min="0"
                          max="17"
                          className="booking-form-input booking-form-child-input"
                        />
                        <button
                          type="button"
                          className="btn btn-link booking-form-child-remove"
                          onClick={() => removeChild(index)}
                          aria-label={`Remove child ${index + 1}`}
                        >
                          Remove
                        </button>
                      </div>
                    ))}
                    <button
                      type="button"
                      className="btn btn-secondary booking-form-child-add"
                      onClick={addChild}
                    >
                      + Add Child
                    </button>
                  </div>
                  {validationErrors.children && (
                    <span className="booking-form-error" role="alert">
                      {validationErrors.children}
                    </span>
                  )}
                </div>

                <div className="booking-form-field">
                  <label htmlFor="special_requests" className="booking-form-label">
                    Special Requests
                  </label>
                  <textarea
                    id="special_requests"
                    name="special_requests"
                    value={guestDetails.special_requests}
                    onChange={handleInputChange}
                    className="booking-form-textarea"
                    rows={4}
                    placeholder="Any special requests for your stay..."
                  />
                </div>
              </div>

              {error && (
                <div className="booking-form-error" role="alert" aria-live="assertive">
                  {error}
                </div>
              )}

              <button 
                type="submit" 
                className="btn btn-primary btn-large booking-form-submit"
                disabled={submitting || !quote}
                aria-busy={submitting}
              >
                {submitting ? 'Processing...' : 'Continue to Payment'}
              </button>
            </form>
          )}

          {step === 'confirmation' && booking && (
            <div className="booking-confirmation">
              <h2 className="booking-confirmation-title">Review Your Booking</h2>
              
              <div className="booking-confirmation-summary">
                <div className="booking-confirmation-item">
                  <span className="booking-confirmation-label">Property:</span>
                  <span className="booking-confirmation-value">{booking.property_name}</span>
                </div>
                <div className="booking-confirmation-item">
                  <span className="booking-confirmation-label">Room:</span>
                  <span className="booking-confirmation-value">{roomType?.name}</span>
                </div>
                <div className="booking-confirmation-item">
                  <span className="booking-confirmation-label">Rate Plan:</span>
                  <span className="booking-confirmation-value">{ratePlan?.name}</span>
                </div>
                <div className="booking-confirmation-item">
                  <span className="booking-confirmation-label">Check-in:</span>
                  <span className="booking-confirmation-value">
                    {new Date(booking.check_in).toLocaleDateString('en-US', { 
                      weekday: 'long', 
                      year: 'numeric', 
                      month: 'long', 
                      day: 'numeric' 
                    })}
                  </span>
                </div>
                <div className="booking-confirmation-item">
                  <span className="booking-confirmation-label">Check-out:</span>
                  <span className="booking-confirmation-value">
                    {new Date(booking.check_out).toLocaleDateString('en-US', { 
                      weekday: 'long', 
                      year: 'numeric', 
                      month: 'long', 
                      day: 'numeric' 
                    })}
                  </span>
                </div>
                <div className="booking-confirmation-item">
                  <span className="booking-confirmation-label">Guests:</span>
                  <span className="booking-confirmation-value">{booking.guest_count}</span>
                </div>
                <div className="booking-confirmation-item">
                  <span className="booking-confirmation-label">Total Price:</span>
                  <span className="booking-confirmation-value">{formatMoney(Number(booking.total_price))}</span>
                </div>
                {booking.special_requests && (
                  <div className="booking-confirmation-item">
                    <span className="booking-confirmation-label">Special Requests:</span>
                    <span className="booking-confirmation-value">{booking.special_requests}</span>
                  </div>
                )}
              </div>

              {error && (
                <div className="booking-confirmation-error" role="alert" aria-live="assertive">
                  {error}
                </div>
              )}

              <div className="booking-confirmation-actions">
                <button 
                  className="btn btn-primary btn-large"
                  onClick={handleConfirmBooking}
                  disabled={submitting}
                  aria-busy={submitting}
                >
                  {submitting ? 'Confirming...' : 'Confirm Booking'}
                </button>
                <button 
                  className="btn btn-secondary"
                  onClick={() => setStep('details')}
                  disabled={submitting}
                >
                  Back to Details
                </button>
              </div>
            </div>
          )}
        </div>

        <aside className="booking-page-sidebar">
          <div className="booking-summary-card">
            <h3 className="booking-summary-title">Price Summary</h3>
            
            {property && (
              <div className="booking-summary-property">
                <div className="booking-summary-property-name">{property.translations[0]?.name || property.name}</div>
                <div className="booking-summary-property-location">
                  {property.city}, {property.country}
                </div>
              </div>
            )}

            {roomType && ratePlan && (
              <>
                <div className="booking-summary-room">
                  <div className="booking-summary-room-name">{roomType.name}</div>
                  <div className="booking-summary-rate-plan">{ratePlan.name}</div>
                </div>

                {totalPrice === null ? (
                  quoteError ? (
                    <div className="booking-summary-error" role="alert">{quoteError}</div>
                  ) : (
                    <div className="booking-summary-loading" role="status">Calculating price...</div>
                  )
                ) : (
                  <>
                    <div className="booking-summary-breakdown">
                      <div className="booking-summary-item">
                        <span className="booking-summary-label">{priceBreakdownLabel()}</span>
                        <span className="booking-summary-value">{formatMoney(totalPrice)}</span>
                      </div>

                      {ratePlan.deposit_required && ratePlan.deposit_percentage && (
                        <div className="booking-summary-item">
                          <span className="booking-summary-label">Deposit ({ratePlan.deposit_percentage}%)</span>
                          <span className="booking-summary-value">
                            {formatMoney(totalPrice * (ratePlan.deposit_percentage / 100))}
                          </span>
                        </div>
                      )}
                    </div>

                    <div className="booking-summary-total">
                      <span className="booking-summary-total-label">Total</span>
                      <span className="booking-summary-total-value">{formatMoney(totalPrice)}</span>
                    </div>
                  </>
                )}
              </>
            )}

            {booking && booking.expires_at && (
              <div className="booking-summary-expiry">
                <div className="booking-summary-expiry-icon"><Clock size={20} aria-hidden="true" /></div>
                <div className="booking-summary-expiry-text">
                  <strong>Booking expires in 15 minutes</strong>
                  <div>Please complete your booking before {new Date(booking.expires_at).toLocaleTimeString()}</div>
                </div>
              </div>
            )}
          </div>
        </aside>
      </div>
    </div>
  )
}

export default BookingPage
