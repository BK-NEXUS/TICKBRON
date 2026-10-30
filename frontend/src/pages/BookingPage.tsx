import { cleanField, isPhoneValid } from '../utils/inputFilters'
import { ARRIVAL_GRACE_HOURS, DEFAULT_ARRIVAL_TIME, formatArrivalTime, isArrivalPassed } from '../utils/arrival'
import { ChargeMain, ChargeNotes } from '../components/ChargeAmount'
import type { MessageKey } from '../i18n/messages/en'
import { useState, useEffect, useRef } from 'react'
import { Check, Clock } from 'lucide-react'
import { useNavigate, useLocation } from 'react-router'
import { bookingAdapter, BookingCreateRequest, Booking } from '../adapters/bookingAdapter'
import { propertyAdapter, Property, RoomType, RatePlan, StayQuote } from '../adapters/propertyAdapter'
import { useAuth } from '../contexts/AuthContext'
import { usePageTrail } from '../components/Breadcrumbs'
import { searchUrlForCity } from '../utils/searchFilters'
import { overlapsOwnStay, type StayDates } from '../utils/stays'
import type { Refusal } from '../utils/refusal'
import { propertyDisplayName } from '../utils/propertyName'
import { useI18n } from '../i18n/I18nContext'
import { VipBadge } from '../components/VipBadge'

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
  phone_number: string
  arrival_time: string
  number_of_rooms: number
  children: number[]
  special_requests?: string
}

/**
 * BookingPage component for the booking flow
 * Includes guest details form, price summary, validation, and confirmation states
 */
/** A backend message (text) or one of ours (key): ours are translated when shown, also when set inside an effect */
type Message = { text: string } | { key: MessageKey; params?: Record<string, string | number> }
// Refusals the backend names with a code: shown in the page language instead of the server's English text
const REFUSAL_KEYS: Partial<Record<string, MessageKey>> = {
  exchange_rate_unavailable: 'booking.rateUnavailable', // 503: a hotel priced in dollars and no rate yet; nothing was reserved
  too_many_upcoming_bookings: 'booking.tooManyUpcoming',
  overlapping_booking: 'booking.overlapping',
}
// Why a stay cannot be booked (the quote answers with a code and the values), said in the page language
const AVAILABILITY_KEYS: Partial<Record<string, MessageKey>> = {
  night_unavailable: 'booking.nightUnavailable',
  night_min_stay: 'booking.nightMinStay',
  night_max_stay: 'booking.nightMaxStay',
  no_rooms_left: 'booking.noRoomsLeft',
  few_rooms_left: 'booking.fewRoomsLeft',
  plan_min_stay: 'booking.planMinStay',
  plan_max_stay: 'booking.planMaxStay',
}
const refusalMessage = (reason: Refusal | undefined): Message | undefined => {
  const key = reason ? AVAILABILITY_KEYS[reason.code] : undefined
  return key && reason ? { key, params: reason.params } : undefined
}
const failure = (text: string | null | undefined, key: MessageKey): Message => (text ? { text } : { key })

export function BookingPage() {
  const { t, tp, formatMoney: formatAmount, formatDate, currency: chosenCurrency } = useI18n()
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
    arrival_time: DEFAULT_ARRIVAL_TIME,
    number_of_rooms: 1,
    children: [],
    special_requests: '',
  })
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({})
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  // The guest's own upcoming stays, to say before sending that the dates overlap one (the server decides)
  const [ownStays, setOwnStays] = useState<StayDates[]>([])
  const [booking, setBooking] = useState<Booking | null>(null)

  // Home › City › Hotel › Booking
  usePageTrail(property ? [
    { label: property.city, to: searchUrlForCity(property.city) },
    { label: propertyDisplayName(property), to: `/property/${property.id}` },
    { label: t('booking.crumb') },
  ] : null)
  const [error, setError] = useState<Message | null>(null)
  const [step, setStep] = useState<'details' | 'success'>('details')

  // GET /properties/{id}/quote/: priced by the same backend code that charges the booking,
  // so the total shown here is the amount paid. There is no local fallback price.
  const [quote, setQuote] = useState<StayQuote | null>(null)
  const [quoteError, setQuoteError] = useState<Message | null>(null)
  const quoteRequestId = useRef(0)
  const roomsForQuote = Math.max(1, guestDetails.number_of_rooms || 1)

  useEffect(() => {
    if (!isAuthenticated) return
    let current = true
    void bookingAdapter.getBookings({ status: 'confirmed' }).then(({ data }) => {
      if (current && data) setOwnStays(data.results)
    })
    return () => { current = false }
  }, [isAuthenticated])

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
      setError({ key: 'booking.errorMissing' })
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
          currency: chosenCurrency,
        })
      } catch {
        response = undefined
      }
      if (requestId !== quoteRequestId.current) return
      if (response?.data) {
        setQuote(response.data)
      } else {
        setQuoteError(refusalMessage(response?.reason) ?? failure(response?.error, 'booking.errorQuote'))
      }
    }
    loadQuote()
  }, [bookingState, roomsForQuote, chosenCurrency])

  // Load property, room type, and rate plan data
  useEffect(() => {
    const loadData = async () => {
      if (!bookingState) return

      try {
        setLoading(true)
        
        // Load property details
        const propertyResponse = await propertyAdapter.getPropertyById(bookingState.propertyId)
        if (propertyResponse.error || !propertyResponse.data) {
          setError(failure(propertyResponse.error, 'booking.errorProperty'))
          setLoading(false)
          return
        }
        setProperty(propertyResponse.data)

        // Find room type and rate plan from property data
        const foundRoomType = propertyResponse.data.room_types?.find(rt => rt.id === bookingState.roomTypeId)
        const foundRatePlan = foundRoomType?.rate_plans?.find(rp => rp.id === bookingState.ratePlanId)
        
        if (!foundRoomType || !foundRatePlan) {
          setError({ key: 'booking.errorRoom' })
          setLoading(false)
          return
        }
        
        setRoomType(foundRoomType)
        setRatePlan(foundRatePlan)
        setLoading(false)
      } catch {
        setError({ key: 'booking.errorLoad' })
        setLoading(false)
      }
    }

    loadData()
  }, [bookingState])

  // The booking's own total once it exists (the amount charged), else the backend quote;
  // null while neither is known or when the stay cannot be booked
  const totalPrice = booking ? Number(booking.total_price) : quote ? Number(quote.total_price) : null
  const currency = booking?.currency || quote?.currency || bookingState?.currency || 'USD'
  const formatMoney = (value: number) => formatAmount(value, currency, { minDecimals: 0, maxDecimals: 2 })
  // A price the owner did not enter (a conversion at the CBU rate) is shown with ≈
  const approximate = !booking && quote?.price_source === 'converted'
  const showMoney = (value: number) => (approximate ? t('charge.approx', { amount: formatMoney(value) }) : formatMoney(value))

  /** "$60 × 2 nights" when every night costs the same, otherwise "2 nights"; "× N rooms" when more than one */
  const priceBreakdownLabel = (): string => {
    const nights = quote?.number_of_nights ?? calculateNumberOfNights()
    const prices = (quote?.nights ?? []).map(night => Number(night.price))
    const uniform = prices.length > 0 && prices.every(price => price === prices[0])
    const format = (value: number) => formatAmount(value, currency, { minDecimals: 0, maxDecimals: 0 })
    const nightsLabel = tp('rooms.nights', nights)
    const nightsText = uniform ? t('booking.breakdown', { price: format(prices[0]), nights: nightsLabel }) : nightsLabel
    return roomsForQuote > 1 ? t('booking.times', { text: nightsText, rooms: tp('booking.roomsCount', roomsForQuote) }) : nightsText
  }

  // A date among the values (YYYY-MM-DD) is written out in the page language when the message is shown
  const messageValues = (params: Record<string, string | number> | undefined) => params && {
    ...params,
    ...(typeof params.date === 'string' ? { date: formatDate(params.date) } : {}),
  }
  const messageText = (message: Message | null) => (
    message ? ('text' in message ? message.text : t(message.key, messageValues(message.params))) : null)
  const errorText = messageText(error)
  const overlapsOwn = bookingState !== undefined && bookingState !== null
    && overlapsOwnStay(ownStays, bookingState.checkIn, bookingState.checkOut)
  const quoteErrorText = messageText(quoteError)

  // Redirect if not authenticated
  useEffect(() => {
    if (!isAuthenticated && !loading) {
      navigate('/login', { state: { from: location.pathname, state: location.state } })
    }
  }, [isAuthenticated, loading, navigate, location])

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target
    setField(name, cleanField(name, value))
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

  // Children are part of the guest count and one guest is always an adult
  const maxChildren = Math.max(0, (bookingState?.guestCount ?? 1) - 1)

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
      errors.first_name = t('booking.firstNameRequired')
    } else if (guestDetails.first_name.trim().length < 2) {
      errors.first_name = t('booking.firstNameShort')
    }

    if (!guestDetails.last_name.trim()) {
      errors.last_name = t('booking.lastNameRequired')
    } else if (guestDetails.last_name.trim().length < 2) {
      errors.last_name = t('booking.lastNameShort')
    }

    if (!guestDetails.email.trim()) {
      errors.email = t('booking.emailRequired')
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(guestDetails.email)) {
      errors.email = t('booking.emailInvalid')
    }

    if (!isPhoneValid(guestDetails.phone_number)) {
      errors.phone_number = t('auth.errPhone')
    }

    if (!guestDetails.arrival_time) {
      errors.arrival_time = t('booking.arrivalRequired')
    } else if (bookingState && isArrivalPassed(bookingState.checkIn, guestDetails.arrival_time)) {
      errors.arrival_time = t('booking.arrivalPassed')
    }

    if (guestDetails.number_of_rooms < 1) {
      errors.number_of_rooms = t('booking.roomsMin')
    }

    if (guestDetails.children.some(age => age < 0 || age > 17)) {
      errors.children = t('booking.childrenRange')
    } else if (guestDetails.children.length > maxChildren) {
      errors.children = t('booking.childrenIncluded')
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
      setError({ key: 'booking.errorInfo' })
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
        guest_email: guestDetails.email,
        guest_phone: guestDetails.phone_number,
        expected_arrival_time: guestDetails.arrival_time,
        number_of_rooms: guestDetails.number_of_rooms,
        children: guestDetails.children.length > 0 ? guestDetails.children : undefined,
        special_requests: guestDetails.special_requests || undefined,
      }

      const response = await bookingAdapter.createBooking(bookingRequest)
      
      if (response.error || !response.data) {
        const refusal = response.code ? REFUSAL_KEYS[response.code] : undefined
        setError(refusal ? { key: refusal } : refusalMessage(response.reason) ?? failure(response.error, 'booking.errorCreate'))
        setSubmitting(false)
        return
      }

      // Cash at the hotel: the booking is confirmed at once, there is no payment step
      setBooking(response.data)
      setStep('success')
      setSubmitting(false)
    } catch {
      setError({ key: 'booking.errorCreateRetry' })
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
            <p>{t('booking.loading')}</p>
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
            <h1>{t('booking.errorTitle')}</h1>
            <p>{errorText}</p>
            <button 
              className="btn btn-primary"
              onClick={handleBackToProperty}
              aria-label={t(property ? 'booking.backToPropertyLabel' : 'booking.backToSearchLabel')}
            >
              {t(property ? 'booking.backToProperty' : 'booking.backToSearch')}
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
            <h1>{t('booking.confirmedTitle')}</h1>
            <p>{t('booking.confirmedText')}</p>
            
            <div className="booking-confirmation-details">
              <div className="booking-confirmation-item">
                <span className="booking-confirmation-label">{t('booking.confirmationCode')}</span>
                <span className="booking-confirmation-value">{booking.confirmation_code}</span>
              </div>
              <div className="booking-confirmation-item">
                <span className="booking-confirmation-label">{t('booking.property')}</span>
                <span className="booking-confirmation-value">{booking.property_name}</span>
              </div>
              <div className="booking-confirmation-item">
                <span className="booking-confirmation-label">{t('booking.checkIn')}</span>
                <span className="booking-confirmation-value">
                  {formatDate(booking.check_in, { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
                </span>
              </div>
              <div className="booking-confirmation-item">
                <span className="booking-confirmation-label">{t('booking.checkOut')}</span>
                <span className="booking-confirmation-value">
                  {formatDate(booking.check_out, { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
                </span>
              </div>
              <div className="booking-confirmation-item">
                <span className="booking-confirmation-label">{t('booking.totalPrice')}</span>
                <span className="booking-confirmation-value"><ChargeMain booking={booking} /><ChargeNotes booking={booking} /></span>
              </div>
              {booking.expected_arrival_time && (
                <div className="booking-confirmation-item">
                  <span className="booking-confirmation-label">{t('booking.arrivalTime')}</span>
                  <span className="booking-confirmation-value">{formatArrivalTime(booking.expected_arrival_time)}</span>
                </div>
              )}
            </div>

            {booking.expected_arrival_time && (
              <p className="booking-arrival-notice" role="note">
                {t('booking.arrivalNotice', { time: formatArrivalTime(booking.expected_arrival_time), hours: ARRIVAL_GRACE_HOURS })}
              </p>
            )}

            <div className="booking-confirmation-actions">
              <button 
                className="btn btn-primary"
                onClick={() => navigate('/bookings')}
                aria-label={t('booking.viewBookingsLabel')}
              >
                {t('booking.viewBookings')}
              </button>
              <button 
                className="btn btn-secondary"
                onClick={handleBackToProperty}
                aria-label={t('booking.backToPropertyLabel')}
              >
                {t('booking.backToProperty')}
              </button>
            </div>
          </div>
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
              aria-label={t('booking.backArrowProperty')}
            >
              ← {t('booking.backToProperty')}
            </button>
            <h1>{t('booking.complete')}</h1>
          </div>

          {step === 'details' && (
            <form onSubmit={handleSubmit} className="booking-form" noValidate>
              <div className="booking-form-section">
                <h2 className="booking-form-section-title">{t('booking.guestDetails')}</h2>
                
                <div className="booking-form-row">
                  <div className="booking-form-field">
                    <label htmlFor="first_name" className="booking-form-label">
                      {t('booking.firstName')} <span className="required">*</span>
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
                      {t('booking.lastName')} <span className="required">*</span>
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
                    {t('booking.email')} <span className="required">*</span>
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
                    {t('auth.phone')} <span className="required">*</span>
                  </label>
                  <input
                    type="tel"
                    inputMode="tel"
                    id="phone_number"
                    name="phone_number"
                    value={guestDetails.phone_number}
                    onChange={handleInputChange}
                    className={`booking-form-input ${validationErrors.phone_number ? 'booking-form-input--error' : ''}`}
                    aria-invalid={!!validationErrors.phone_number}
                    aria-describedby={validationErrors.phone_number ? 'phone_number-error' : 'phone_number-hint'}
                    autoComplete="tel"
                    placeholder="+998 90 123 45 67"
                    required
                  />
                  <span id="phone_number-hint" className="booking-form-hint">{t('auth.phoneHint')}</span>
                  {validationErrors.phone_number && (
                    <span id="phone_number-error" className="booking-form-error" role="alert">
                      {validationErrors.phone_number}
                    </span>
                  )}
                </div>

                <div className="booking-form-field">
                  <label htmlFor="arrival_time" className="booking-form-label">
                    {t('booking.arrivalTime')} <span className="required">*</span>
                  </label>
                  <input
                    type="time"
                    id="arrival_time"
                    name="arrival_time"
                    value={guestDetails.arrival_time}
                    onChange={handleInputChange}
                    className={`booking-form-input ${validationErrors.arrival_time ? 'booking-form-input--error' : ''}`}
                    aria-invalid={!!validationErrors.arrival_time}
                    aria-describedby={validationErrors.arrival_time ? 'arrival_time-error' : 'arrival_time-hint'}
                    required
                  />
                  {guestDetails.arrival_time && (
                    <span id="arrival_time-hint" className="booking-form-hint">
                      {t('booking.arrivalNotice', { time: guestDetails.arrival_time, hours: ARRIVAL_GRACE_HOURS })}
                    </span>
                  )}
                  {validationErrors.arrival_time && (
                    <span id="arrival_time-error" className="booking-form-error" role="alert">
                      {validationErrors.arrival_time}
                    </span>
                  )}
                </div>

                <div className="booking-form-field">
                  <label htmlFor="number_of_rooms" className="booking-form-label">
                    {t('booking.numberOfRooms')} <span className="required">*</span>
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
                  <label className="booking-form-label">{t('booking.childrenAges')}</label>
                  <div className="booking-form-children">
                    {guestDetails.children.map((age, index) => (
                      <div key={index} className="booking-form-child-item">
                        <label htmlFor={`child_age_${index}`} className="booking-form-child-label">
                          {t('booking.child', { number: index + 1 })}
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
                          aria-label={t('booking.removeChildLabel', { number: index + 1 })}
                        >
                          {t('booking.remove')}
                        </button>
                      </div>
                    ))}
                    <button
                      type="button"
                      className="btn btn-secondary booking-form-child-add"
                      onClick={addChild}
                      disabled={guestDetails.children.length >= maxChildren}
                      aria-describedby="children-hint"
                    >
                      + {t('booking.addChild')}
                    </button>
                  </div>
                  <span id="children-hint" className="booking-form-hint">{t('booking.childrenIncluded')}</span>
                  {validationErrors.children && (
                    <span className="booking-form-error" role="alert">
                      {validationErrors.children}
                    </span>
                  )}
                </div>

                <div className="booking-form-field">
                  <label htmlFor="special_requests" className="booking-form-label">
                    {t('booking.requests')}
                  </label>
                  <textarea
                    id="special_requests"
                    name="special_requests"
                    value={guestDetails.special_requests}
                    onChange={handleInputChange}
                    className="booking-form-textarea"
                    rows={4}
                    placeholder={t('booking.requestsPlaceholder')}
                  />
                </div>
              </div>

              {error && (
                <div className="booking-form-error" role="alert" aria-live="assertive">
                  {errorText}
                </div>
              )}

              {overlapsOwn && (
                <div className="booking-form-error" role="alert">
                  {t('booking.overlapping')}
                </div>
              )}

              <button 
                type="submit" 
                className="btn btn-primary btn-large booking-form-submit"
                disabled={submitting || !quote || overlapsOwn}
                aria-busy={submitting}
              >
                {submitting ? t('booking.processing') : t('booking.continue')}
              </button>
            </form>
          )}
        </div>

        <aside className="booking-page-sidebar">
          <div className="booking-summary-card">
            <h3 className="booking-summary-title">{t('booking.summary')}</h3>
            
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
                  <div className="booking-summary-room-name">{roomType.name} {roomType.is_vip && <VipBadge />}</div>
                  <div className="booking-summary-rate-plan">{ratePlan.name}</div>
                </div>

                {totalPrice === null ? (
                  quoteError ? (
                    <div className="booking-summary-error" role="alert">{quoteErrorText}</div>
                  ) : (
                    <div className="booking-summary-loading" role="status">{t('booking.calculating')}</div>
                  )
                ) : (
                  <>
                    <div className="booking-summary-breakdown">
                      <div className="booking-summary-item">
                        <span className="booking-summary-label">{priceBreakdownLabel()}</span>
                        <span className="booking-summary-value">{showMoney(totalPrice)}</span>
                      </div>
                    </div>

                    <div className="booking-summary-total">
                      <span className="booking-summary-total-label">{t('booking.total')}</span>
                      <span className="booking-summary-total-value">{showMoney(totalPrice)}</span>
                    </div>
                    {quote?.uzs_total && (
                      <p className="charge-notes">
                        <span className="charge-approx">
                          {t(quote.exchange_rate === null && quote.currency !== 'UZS' ? 'charge.youPay' : 'charge.inSom',
                            { amount: formatAmount(quote.uzs_total, 'UZS', { minDecimals: 0, maxDecimals: 0 }) })}
                        </span>
                      </p>
                    )}
                  </>
                )}
              </>
            )}

            {booking && booking.expires_at && (
              <div className="booking-summary-expiry">
                <div className="booking-summary-expiry-icon"><Clock size={20} aria-hidden="true" /></div>
                <div className="booking-summary-expiry-text">
                  <strong>{t('booking.expires')}</strong>
                  <div>{t('booking.expiresBefore', { time: new Date(booking.expires_at).toLocaleTimeString() })}</div>
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
