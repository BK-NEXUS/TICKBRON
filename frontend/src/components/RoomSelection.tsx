import { useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  RoomType,
  RatePlan,
  DateInventory,
  AvailabilityDateInventory,
  propertyAdapter,
} from '../adapters/propertyAdapter'
import { RoomCard } from './RoomCard'
import { RatePlanCard } from './RatePlanCard'
import { AvailabilityCalendar } from './AvailabilityCalendar'

/** How far ahead the availability calendar loads, in days */
const AVAILABILITY_DAYS = 90

/** YYYY-MM-DD in local time (the calendar builds its dates the same way) */
const toLocalDate = (date: Date) =>
  `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`

/** Map a backend inventory row to the calendar's shape. A null price means the rate plan's base price applies. */
const toCalendarInventory = (row: AvailabilityDateInventory, ratePlan: RatePlan): DateInventory => {
  const bookable = row.is_available && row.remaining_rooms > 0
  return {
    id: row.id,
    rate_plan_id: ratePlan.id,
    date: row.date,
    status: bookable ? 'available' : 'fully_booked',
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
export function RoomSelection({ roomTypes, propertyId, currency = 'USD' }: RoomSelectionProps) {
  const navigate = useNavigate()
  const [selectedRoomId, setSelectedRoomId] = useState<number | null>(null)
  const [selectedRatePlanId, setSelectedRatePlanId] = useState<number | null>(null)
  const [selectedDate, setSelectedDate] = useState<string | null>(null)
  const [ratePlans, setRatePlans] = useState<RatePlan[]>([])
  const [dateInventory, setDateInventory] = useState<DateInventory[]>([])
  const [loading, setLoading] = useState(false)
  const [availabilityLoading, setAvailabilityLoading] = useState(false)
  const [availabilityError, setAvailabilityError] = useState<string | null>(null)
  // Ignore responses for a rate plan the user has already moved away from
  const availabilityRequestId = useRef(0)

  const selectedRoom = roomTypes.find(room => room.id === selectedRoomId)
  const selectedRatePlan = ratePlans.find(plan => plan.id === selectedRatePlanId)

  const handleRoomSelect = (roomId: number) => {
    availabilityRequestId.current += 1
    setSelectedRoomId(roomId)
    setSelectedRatePlanId(null)
    setSelectedDate(null)
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

    const today = new Date()
    const lastDay = new Date(today)
    lastDay.setDate(today.getDate() + AVAILABILITY_DAYS)
    const response = await propertyAdapter.getAvailability(propertyId, {
      check_in: toLocalDate(today),
      check_out: toLocalDate(lastDay),
    })
    if (requestId !== availabilityRequestId.current) return

    if (response.error || !response.data) {
      setAvailabilityError(response.error || 'Could not load availability. Please try again.')
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
    setSelectedDate(null)
    loadAvailability(ratePlanId)
  }

  const handleDateSelect = (date: string) => {
    setSelectedDate(date)
  }

  const handleProceedToBooking = () => {
    if (selectedRoom && selectedRatePlan && selectedDate) {
      const checkInDate = new Date(selectedDate)
      const nightsToBook = selectedRatePlan.min_nights || 1
      const checkOutDate = new Date(checkInDate.getTime() + nightsToBook * 24 * 60 * 60 * 1000)
      
      const bookingState = {
        propertyId,
        roomTypeId: selectedRoom.id,
        ratePlanId: selectedRatePlan.id,
        checkIn: selectedDate,
        checkOut: checkOutDate.toISOString().split('T')[0],
        guestCount: selectedRoom.base_occupancy,
        pricePerNight: selectedRatePlan.base_price,
        currency: selectedRatePlan.currency,
      }
      navigate('/booking', { state: bookingState })
    }
  }

  if (roomTypes.length === 0) {
    return (
      <div className="room-selection room-selection--empty">
        <p className="room-selection-empty">No rooms available for this property</p>
      </div>
    )
  }

  return (
    <div className="room-selection">
      <h2 className="room-selection-title">Select Your Room</h2>
      
      {/* Room Types */}
      <div className="room-selection-section">
        <h3 className="room-selection-section-title">Available Rooms</h3>
        <div className="room-selection-room-cards">
          {roomTypes.map(room => (
            <RoomCard
              key={room.id}
              room={room}
              currency={currency}
              onSelect={handleRoomSelect}
              isSelected={selectedRoomId === room.id}
            />
          ))}
        </div>
      </div>

      {/* Rate Plans */}
      {selectedRoom && ratePlans.length > 0 && (
        <div className="room-selection-section">
          <h3 className="room-selection-section-title">Rate Plans for {selectedRoom.name}</h3>
          {loading ? (
            <div className="room-selection-loading" role="status" aria-live="polite">
              <div className="loading-spinner"></div>
              <p>Loading rate plans...</p>
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
          <h3 className="room-selection-section-title">Availability Calendar</h3>
          {availabilityLoading ? (
            <div className="room-selection-loading" role="status" aria-live="polite">
              <div className="loading-spinner"></div>
              <p>Loading availability...</p>
            </div>
          ) : availabilityError ? (
            <div className="alert alert-error" role="alert">
              <p>{availabilityError}</p>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => loadAvailability(selectedRatePlan.id)}
              >
                Try again
              </button>
            </div>
          ) : dateInventory.length === 0 ? (
            <p className="room-selection-empty">No availability for the next {AVAILABILITY_DAYS} days.</p>
          ) : (
            <AvailabilityCalendar
              inventory={dateInventory}
              currency={selectedRatePlan.currency}
              onDateSelect={handleDateSelect}
              selectedDate={selectedDate || undefined}
            />
          )}
        </div>
      )}

      {/* Selection Summary */}
      {selectedRoom && selectedRatePlan && selectedDate && (
        <div className="room-selection-summary">
          <h3 className="room-selection-summary-title">Your Selection</h3>
          <div className="room-selection-summary-details">
            <div className="room-selection-summary-item">
              <span className="room-selection-summary-label">Room:</span>
              <span className="room-selection-summary-value">{selectedRoom.name}</span>
            </div>
            <div className="room-selection-summary-item">
              <span className="room-selection-summary-label">Rate Plan:</span>
              <span className="room-selection-summary-value">{selectedRatePlan.name}</span>
            </div>
            <div className="room-selection-summary-item">
              <span className="room-selection-summary-label">Check-in Date:</span>
              <span className="room-selection-summary-value">
                {new Date(selectedDate).toLocaleDateString('en-US', { 
                  weekday: 'long', 
                  year: 'numeric', 
                  month: 'long', 
                  day: 'numeric' 
                })}
              </span>
            </div>
            <div className="room-selection-summary-item">
              <span className="room-selection-summary-label">Price per Night:</span>
              <span className="room-selection-summary-value">
                {new Intl.NumberFormat('en-US', {
                  style: 'currency',
                  currency: selectedRatePlan.currency,
                  minimumFractionDigits: 0,
                  maximumFractionDigits: 0,
                }).format(selectedRatePlan.base_price)}
              </span>
            </div>
          </div>
          <button 
            className="btn btn-primary btn-large room-selection-cta"
            onClick={handleProceedToBooking}
            aria-label="Proceed to booking"
          >
            Proceed to Booking
          </button>
        </div>
      )}
    </div>
  )
}