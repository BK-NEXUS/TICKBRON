import { useState } from 'react'
import { RoomType, RatePlan, DateInventory } from '../adapters/propertyAdapter'
import { propertyAdapter } from '../adapters/propertyAdapter'
import { RoomCard } from './RoomCard'
import { RatePlanCard } from './RatePlanCard'
import { AvailabilityCalendar } from './AvailabilityCalendar'

interface RoomSelectionProps {
  roomTypes: RoomType[]
  currency?: string
}

/**
 * RoomSelection component for room/rate selection UI
 * Combines room cards, rate plan cards, and availability calendar
 */
export function RoomSelection({ roomTypes, currency = 'USD' }: RoomSelectionProps) {
  const [selectedRoomId, setSelectedRoomId] = useState<number | null>(null)
  const [selectedRatePlanId, setSelectedRatePlanId] = useState<number | null>(null)
  const [selectedDate, setSelectedDate] = useState<string | null>(null)
  const [ratePlans, setRatePlans] = useState<RatePlan[]>([])
  const [dateInventory, setDateInventory] = useState<DateInventory[]>([])
  const [loading, setLoading] = useState(false)

  const selectedRoom = roomTypes.find(room => room.id === selectedRoomId)
  const selectedRatePlan = ratePlans.find(plan => plan.id === selectedRatePlanId)

  const handleRoomSelect = (roomId: number) => {
    setSelectedRoomId(roomId)
    setSelectedRatePlanId(null)
    setSelectedDate(null)
    setRatePlans([])
    setDateInventory([])
    
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

  const handleRatePlanSelect = (ratePlanId: number) => {
    setSelectedRatePlanId(ratePlanId)
    setSelectedDate(null)
    setDateInventory([])
    
    setLoading(true)
    try {
      // Generate mock inventory data
      const today = new Date()
      const inventory: DateInventory[] = []
      for (let i = 0; i < 30; i++) {
        const date = new Date(today)
        date.setDate(today.getDate() + i)
        const dateStr = date.toISOString().split('T')[0]
        const availableRooms = Math.floor(Math.random() * 3) + 1
        const bookedRooms = Math.floor(Math.random() * availableRooms)
        const ratePlan = ratePlans.find(rp => rp.id === ratePlanId)
        inventory.push({
          id: inventory.length + 1,
          rate_plan_id: ratePlanId,
          date: dateStr,
          available_rooms: availableRooms,
          booked_rooms: bookedRooms,
          price: ratePlan?.base_price || 100,
          currency: ratePlan?.currency || 'USD',
          is_available: availableRooms > bookedRooms,
          minimum_stay: ratePlan?.min_nights || 1,
          maximum_stay: ratePlan?.max_nights || 30,
        })
      }
      setDateInventory(inventory)
    } catch (error) {
      console.error('Failed to load date inventory:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleDateSelect = (date: string) => {
    setSelectedDate(date)
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
      {selectedRatePlan && dateInventory.length > 0 && (
        <div className="room-selection-section">
          <h3 className="room-selection-section-title">Availability Calendar</h3>
          {loading ? (
            <div className="room-selection-loading" role="status" aria-live="polite">
              <div className="loading-spinner"></div>
              <p>Loading availability...</p>
            </div>
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
          <button className="btn btn-primary btn-large room-selection-cta">
            Proceed to Booking
          </button>
        </div>
      )}
    </div>
  )
}