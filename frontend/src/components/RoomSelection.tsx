import { useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  RoomType,
  RatePlan,
  DateInventory,
  AvailabilityDateInventory,
  StayQuote,
  propertyAdapter,
} from '../adapters/propertyAdapter'
import { RoomCard } from './RoomCard'
import { RatePlanCard } from './RatePlanCard'
import { AvailabilityCalendar } from './AvailabilityCalendar'
import { useI18n } from '../i18n/I18nContext'
import { addDays, businessToday } from '../utils/dates'

/** How far ahead the availability calendar loads, in days */
const AVAILABILITY_DAYS = 90

/** Map a backend inventory row to the calendar's shape. A null price means the rate plan's base price applies. */
const toCalendarInventory = (row: AvailabilityDateInventory, ratePlan: RatePlan): DateInventory => {
  const bookable = row.is_available && row.remaining_rooms > 0
  return {
    id: row.id,
    rate_plan_id: ratePlan.id,
    date: row.date,
    status: !row.is_available ? 'closed' : bookable ? 'available' : 'fully_booked',
    available_rooms: row.available_rooms,
    booked_rooms: row.booked_rooms,
    price: Number(row.price ?? ratePlan.base_price),
    currency: row.currency || ratePlan.currency,
    min_stay: row.minimum_stay ?? ratePlan.min_nights,
    max_stay: row.maximum_stay ?? ratePlan.max_nights,
    is_available: bookable,
  }
}

interface RoomSelectionProps {
  roomTypes: RoomType[]
  /** Id of the property being viewed; the backend's room_types[] do not carry it */
  propertyId: number
  currency?: string
}

/**
 * RoomSelection component for room/rate selection UI
 * Combines room cards, rate plan cards, and availability calendar
 */
export function RoomSelection({ roomTypes, propertyId }: RoomSelectionProps) {
  const navigate = useNavigate()
  const [selectedRoomId, setSelectedRoomId] = useState<number | null>(null)
  const [selectedRatePlanId, setSelectedRatePlanId] = useState<number | null>(null)
  const [checkIn, setCheckIn] = useState<string | null>(null)
  const [checkOut, setCheckOut] = useState<string | null>(null)
  const [quote, setQuote] = useState<StayQuote | null>(null)
  const [quoteError, setQuoteError] = useState<string | null>(null)
  const [quoteLoading, setQuoteLoading] = useState(false)
  const quoteRequestId = useRef(0)
  const [ratePlans, setRatePlans] = useState<RatePlan[]>([])
  const [dateInventory, setDateInventory] = useState<DateInventory[]>([])
  const [loading, setLoading] = useState(false)
  const [availabilityLoading, setAvailabilityLoading] = useState(false)
  const [availabilityError, setAvailabilityError] = useState<string | null>(null)
  // Ignore responses for a rate plan the user has already moved away from
  const availabilityRequestId = useRef(0)

  const selectedRoom = roomTypes.find(room => room.id === selectedRoomId)
  const selectedRatePlan = ratePlans.find(plan => plan.id === selectedRatePlanId)

  const clearRange = () => {
    quoteRequestId.current += 1
    setCheckIn(null)
    setCheckOut(null)
    setQuote(null)
    setQuoteError(null)
    setQuoteLoading(false)
  }

  const handleRoomSelect = (roomId: number) => {
    availabilityRequestId.current += 1
    setSelectedRoomId(roomId)
    setSelectedRatePlanId(null)
    clearRange()
    setRatePlans([])
    setDateInventory([])
    setAvailabilityLoading(false)
    setAvailabilityError(null)
    
    setLoading(true)
    try {
      // Use rate plans from room_types included in property detail
      const room = roomTypes.find(r => r.id === roomId)
      if (room) {
        setRatePlans(room.rate_plans || [])
      }
    } catch (error) {
      console.error('Failed to load rate plans:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadAvailability = async (ratePlanId: number) => {
    const ratePlan = ratePlans.find(plan => plan.id === ratePlanId)
    if (!ratePlan || selectedRoomId === null) return

    const requestId = ++availabilityRequestId.current
    setAvailabilityLoading(true)
    setAvailabilityError(null)
    setDateInventory([])

    const today = businessToday()
    const response = await propertyAdapter.getAvailability(propertyId, {
      check_in: today,
      check_out: addDays(today, AVAILABILITY_DAYS),
    })
    if (requestId !== availabilityRequestId.current) return

    if (response.error || !response.data) {
      setAvailabilityError(response.error || t('rooms.errorAvailability'))
    } else {
      const rows = response.data.room_types
        .find(room => room.id === selectedRoomId)
        ?.rate_plans.find(plan => plan.id === ratePlanId)
        ?.date_inventory ?? []
      setDateInventory(rows.map(row => toCalendarInventory(row, ratePlan)))
    }
    setAvailabilityLoading(false)
  }

  const handleRatePlanSelect = (ratePlanId: number) => {
    setSelectedRatePlanId(ratePlanId)
    clearRange()
    loadAvailability(ratePlanId)
  }

  /** The backend prices the stay, with the same code that charges for it */
  const loadQuote = async (start: string, end: string) => {
    if (selectedRoomId === null || selectedRatePlanId === null) return
    const requestId = ++quoteRequestId.current
    setQuoteLoading(true)
    const response = await propertyAdapter.getQuote(propertyId, {
      roomTypeId: selectedRoomId, ratePlanId: selectedRatePlanId, checkIn: start, checkOut: end, rooms: 1,
    })
    if (requestId !== quoteRequestId.current) return
    setQuote(response?.data ?? null)
    setQuoteError(response?.data ? null : response?.error || t('rooms.errorQuote'))
    setQuoteLoading(false)
  }

  const handleRangeChange = (start: string | null, end: string | null) => {
    clearRange()
    setCheckIn(start)
    setCheckOut(end)
    if (start && end) loadQuote(start, end)
  }

  const handleProceedToBooking = () => {
    if (selectedRoom && selectedRatePlan && checkIn && checkOut && quote) {
      const bookingState = {
        propertyId,
        roomTypeId: selectedRoom.id,
        ratePlanId: selectedRatePlan.id,
        checkIn,
        checkOut,
        guestCount: selectedRoom.base_occupancy,
        pricePerNight: selectedRatePlan.base_price,
        currency: selectedRatePlan.currency,
      }
      navigate('/booking', { state: bookingState })
    }
  }

  const { t, tp, formatMoney: formatAmount, formatDate } = useI18n()
  const formatMoney = (amount: string | number, code: string) =>
    formatAmount(Number(amount), code, { minDecimals: 0, maxDecimals: 2 })

  const formatLongDate = (date: string) => {
    const [year, month, day] = date.split('-').map(Number)
    return formatDate(new Date(year, month - 1, day), {
      weekday: 'long', year: 'numeric', month: 'long', day: 'numeric',
    })
  }

  if (roomTypes.length === 0) {
    return (
      <div className="room-selection room-selection--empty" tabIndex={-1}>
        <p className="room-selection-empty">{t('rooms.none')}</p>
      </div>
    )
  }

  return (
    <div className="room-selection" tabIndex={-1}>
      <h2 className="room-selection-title">{t('rooms.select')}</h2>
      
      {/* Room Types */}
      <div className="room-selection-section">
        <h3 className="room-selection-section-title">{t('rooms.available')}</h3>
        <div className="room-selection-room-cards">
          {roomTypes.map(room => (
            <RoomCard
              key={room.id}
              room={room}
              onSelect={handleRoomSelect}
              isSelected={selectedRoomId === room.id}
            />
          ))}
        </div>
      </div>

      {/* Rate Plans */}
      {selectedRoom && ratePlans.length > 0 && (
        <div className="room-selection-section">
          <h3 className="room-selection-section-title">{t('rooms.ratePlansFor', { room: selectedRoom.name })}</h3>
          {loading ? (
            <div className="room-selection-loading" role="status" aria-live="polite">
              <div className="loading-spinner"></div>
              <p>{t('rooms.loadingRates')}</p>
            </div>
          ) : (
            <div className="room-selection-rate-plans">
              {ratePlans.map(ratePlan => (
                <RatePlanCard
                  key={ratePlan.id}
                  ratePlan={ratePlan}
                  onSelect={handleRatePlanSelect}
                  isSelected={selectedRatePlanId === ratePlan.id}
                />
              ))}
            </div>
          )}
        </div>
      )}

      {/* Availability Calendar */}
      {selectedRatePlan && (
        <div className="room-selection-section">
          <h3 className="room-selection-section-title">{t('rooms.calendar')}</h3>
          {availabilityLoading ? (
            <div className="room-selection-loading" role="status" aria-live="polite">
              <div className="loading-spinner"></div>
              <p>{t('rooms.loadingAvailability')}</p>
            </div>
          ) : availabilityError ? (
            <div className="alert alert-error" role="alert">
              <p>{availabilityError}</p>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => loadAvailability(selectedRatePlan.id)}
              >
                {t('rooms.tryAgain')}
              </button>
            </div>
          ) : dateInventory.length === 0 ? (
            <p className="room-selection-empty">{tp('rooms.noAvailability', AVAILABILITY_DAYS)}</p>
          ) : (
            <>
              <p className="room-selection-hint" aria-live="polite">
                {!checkIn
                  ? t('rooms.hintCheckIn')
                  : !checkOut
                    ? t('rooms.hintCheckOut')
                    : null}
              </p>
              <AvailabilityCalendar
                inventory={dateInventory}
                currency={selectedRatePlan.currency}
                checkIn={checkIn}
                checkOut={checkOut}
                onRangeChange={handleRangeChange}
                minNights={selectedRatePlan.min_nights}
                maxNights={selectedRatePlan.max_nights}
              />
            </>
          )}
        </div>
      )}

      {/* Selection Summary */}
      {selectedRoom && selectedRatePlan && checkIn && checkOut && (
        <div className="room-selection-summary">
          <h3 className="room-selection-summary-title">{t('rooms.selection')}</h3>
          <div className="room-selection-summary-details">
            <div className="room-selection-summary-item">
              <span className="room-selection-summary-label">{t('rooms.room')}</span>
              <span className="room-selection-summary-value">{selectedRoom.name}</span>
            </div>
            <div className="room-selection-summary-item">
              <span className="room-selection-summary-label">{t('rooms.ratePlan')}</span>
              <span className="room-selection-summary-value">{selectedRatePlan.name}</span>
            </div>
            <div className="room-selection-summary-item">
              <span className="room-selection-summary-label">{t('rooms.checkIn')}</span>
              <span className="room-selection-summary-value">{formatLongDate(checkIn)}</span>
            </div>
            <div className="room-selection-summary-item">
              <span className="room-selection-summary-label">{t('rooms.checkOut')}</span>
              <span className="room-selection-summary-value">{formatLongDate(checkOut)}</span>
            </div>
            <div className="room-selection-summary-item room-selection-summary-total">
              <span className="room-selection-summary-label">{t('rooms.total')}</span>
              <span className="room-selection-summary-value">
                {quoteLoading
                  ? t('rooms.calculating')
                  : quote
                    ? t('rooms.nightsTotal', { nights: tp('rooms.nights', quote.number_of_nights), total: formatMoney(quote.total_price, quote.currency) })
                    : '—'}
              </span>
            </div>
          </div>
          {quoteError && (
            <div className="alert alert-error" role="alert">
              <p>{quoteError}</p>
            </div>
          )}
          {quote && (
            <button
              className="btn btn-primary btn-large room-selection-cta"
              onClick={handleProceedToBooking}
              aria-label={t('rooms.proceedLabel')}
            >
              {t('rooms.proceed')}
            </button>
          )}
        </div>
      )}
    </div>
  )
}