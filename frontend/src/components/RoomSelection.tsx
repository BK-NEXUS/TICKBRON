import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router'
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

/** Bos orın kalendarı neshe kún aldınǵa júkleydi, kúnlerde */
const AVAILABILITY_DAYS = 90

/**
 * Backend inventory qatarın kalendar formasına sáykeslestiriw. null baha rate plan nıń tiykarǵı bahası qollanılatuǵının
 * bildiredi.
 */
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
    prices: row.prices,
    converted_currencies: Object.entries(ratePlan.prices ?? {}).filter(([, entry]) => entry.source === 'converted').map(([code]) => code),
    min_stay: row.minimum_stay ?? ratePlan.min_nights,
    max_stay: row.maximum_stay ?? ratePlan.max_nights,
    is_available: bookable,
  }
}

interface RoomSelectionProps {
  roomTypes: RoomType[]
  /** Qaralıp atırǵan mehmanxana id si; backend tiń room_types[] i onı alıp júrmeydi */
  propertyId: number
  currency?: string
}

/**
 * Xona/rate tańlaw UI ushın RoomSelection komponenti
 * Xona kartaların, rate plan kartaların hám bos orın kalendarın birlestiredi
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
  // Paydalanıwshı aldınan ketken rate plan ushın juwaplardı itibarǵa almaw
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
      // Mehmanxana tolıq maǵlıwmatına kirgen room_types ten rate plan lardı paydalanıw
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

  /** Backend turıwdı onı alatuǵın birdey kod penen bahalaydı */
  const loadQuote = async (start: string, end: string) => {
    if (selectedRoomId === null || selectedRatePlanId === null) return
    const requestId = ++quoteRequestId.current
    setQuoteLoading(true)
    const response = await propertyAdapter.getQuote(propertyId, {
      roomTypeId: selectedRoomId, ratePlanId: selectedRatePlanId, checkIn: start, checkOut: end, rooms: 1, currency,
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

  const { t, tp, formatMoney: formatAmount, formatDate, currency } = useI18n()

  // Mehmann aldınan bahalanǵan turıw menen valyutanı ózgertedi: jańa valyutada qaytadan bahalaw
  useEffect(() => {
    if (checkIn && checkOut) loadQuote(checkIn, checkOut)
  // Tek valyuta onı iske túsiredi; aralıq handler leri óz ózgerislerin ózleri bahalaydı
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currency])
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
      
      {/* Xona túrleri */}
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

      {/* Rate plan lar */}
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

      {/* Bos orın kalendarı */}
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

      {/* Tańlaw qısqasha mazmunı */}
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
                    ? t('rooms.nightsTotal', { nights: tp('rooms.nights', quote.number_of_nights), total: quote.price_source === 'converted' ? t('charge.approx', { amount: formatMoney(quote.total_price, quote.currency) }) : formatMoney(quote.total_price, quote.currency) })
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