import { useState, useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { bookingAdapter, BookingCreateRequest, Booking } from '../adapters/bookingAdapter'
import { propertyAdapter, Property, RoomType, RatePlan } from '../adapters/propertyAdapter'
import { useAuth } from '../contexts/AuthContext'

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
    special_requests: '',
  })
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({})
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [booking, setBooking] = useState<Booking | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [step, setStep] = useState<'details' | 'confirmation' | 'success'>('details')

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
      setGuestDetails(prev => ({
        ...prev,
        first_name: user.first_name || '',
        last_name: user.last_name || '',
        email: user.email || '',
      }))
    }
  }, [location.state, user])

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

  // Redirect if not authenticated
  useEffect(() => {
    if (!isAuthenticated && !loading) {
      navigate('/login', { state: { from: location.pathname, state: location.state } })
    }
  }, [isAuthenticated, loading, navigate, location])

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target
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

    if (guestDetails.phone_number && guestDetails.phone_number.trim().length < 10) {
      errors.phone_number = 'Phone number must be at least 10 characters'
    }

    setValidationErrors(errors)
    return Object.keys(errors).length === 0
  }

  const calculateTotalPrice = (): number => {
    if (!bookingState) return 0
    
    const checkIn = new Date(bookingState.checkIn)
    const checkOut = new Date(bookingState.checkOut)
    const numberOfNights = Math.ceil((checkOut.getTime() - checkIn.getTime()) / (1000 * 60 * 60 * 24))
    
    return numberOfNights * bookingState.pricePerNight
  }

  const calculateNumberOfNights = (): number => {
    if (!bookingState) return 0
    
    const checkIn = new Date(bookingState.checkIn)
    const checkOut = new Date(bookingState.checkOut)
    return Math.ceil((checkOut.getTime() - checkIn.getTime()) / (1000 * 60 * 60 * 24))
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
        special_requests: guestDetails.special_requests || undefined,
      }

      const response = await bookingAdapter.createBooking(bookingRequest)
      
      if (response.error || !response.data) {
        setError(response.error || 'Failed to create booking')
        setSubmitting(false)
        return
      }

      setBooking(response.data)
      setStep('confirmation')
    } catch (err) {
      setError('Failed to create booking. Please try again.')
      setSubmitting(false)
    }
  }

  const handleConfirmBooking = async () => {
    if (!booking) return

    setSubmitting(true)
    setError(null)

    try {
      // In a real implementation, this would integrate with payment
      // For now, we'll simulate confirmation
      setStep('success')
      setSubmitting(false)
    } catch (err) {
      setError('Failed to confirm booking. Please try again.')
      setSubmitting(false)
    }
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
            <div className="success-icon">✓</div>
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
                <span className="booking-confirmation-value">
                  {new Intl.NumberFormat('en-US', {
                    style: 'currency',
                    currency: booking.currency,
                    minimumFractionDigits: 0,
                    maximumFractionDigits: 0,
                  }).format(booking.total_price)}
                </span>
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

  const totalPrice = calculateTotalPrice()
  const numberOfNights = calculateNumberOfNights()
  const currency = bookingState?.currency || 'USD'

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
                  <input
                    type="tel"
                    id="phone_number"
                    name="phone_number"
                    value={guestDetails.phone_number}
                    onChange={handleInputChange}
                    className={`booking-form-input ${validationErrors.phone_number ? 'booking-form-input--error' : ''}`}
                    aria-invalid={!!validationErrors.phone_number}
                    aria-describedby={validationErrors.phone_number ? 'phone_number-error' : undefined}
                    autoComplete="tel"
                  />
                  {validationErrors.phone_number && (
                    <span id="phone_number-error" className="booking-form-error" role="alert">
                      {validationErrors.phone_number}
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
                disabled={submitting}
                aria-busy={submitting}
              >
                {submitting ? 'Processing...' : 'Continue to Confirmation'}
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
                  <span className="booking-confirmation-value">
                    {new Intl.NumberFormat('en-US', {
                      style: 'currency',
                      currency: booking.currency,
                      minimumFractionDigits: 0,
                      maximumFractionDigits: 0,
                    }).format(booking.total_price)}
                  </span>
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

                <div className="booking-summary-breakdown">
                  <div className="booking-summary-item">
                    <span className="booking-summary-label">
                      {new Intl.NumberFormat('en-US', {
                        style: 'currency',
                        currency,
                        minimumFractionDigits: 0,
                        maximumFractionDigits: 0,
                      }).format(ratePlan.base_price)} × {numberOfNights} nights
                    </span>
                    <span className="booking-summary-value">
                      {new Intl.NumberFormat('en-US', {
                        style: 'currency',
                        currency,
                        minimumFractionDigits: 0,
                        maximumFractionDigits: 0,
                      }).format(totalPrice)}
                    </span>
                  </div>
                  
                  {ratePlan.deposit_required && ratePlan.deposit_percentage && (
                    <div className="booking-summary-item">
                      <span className="booking-summary-label">Deposit ({ratePlan.deposit_percentage}%)</span>
                      <span className="booking-summary-value">
                        {new Intl.NumberFormat('en-US', {
                          style: 'currency',
                          currency,
                          minimumFractionDigits: 0,
                          maximumFractionDigits: 0,
                        }).format(totalPrice * (ratePlan.deposit_percentage / 100))}
                      </span>
                    </div>
                  )}
                </div>

                <div className="booking-summary-total">
                  <span className="booking-summary-total-label">Total</span>
                  <span className="booking-summary-total-value">
                    {new Intl.NumberFormat('en-US', {
                      style: 'currency',
                      currency,
                      minimumFractionDigits: 0,
                      maximumFractionDigits: 0,
                    }).format(totalPrice)}
                  </span>
                </div>
              </>
            )}

            {booking && booking.expires_at && (
              <div className="booking-summary-expiry">
                <div className="booking-summary-expiry-icon">⏰</div>
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
