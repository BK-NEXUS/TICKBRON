import { RoomType } from '../adapters/searchAdapter'

interface RoomCardProps {
  room: RoomType
  currency?: string
  onSelect?: (roomId: number) => void
  isSelected?: boolean
}

/**
 * RoomCard component for displaying room information
 * Shows room details, occupancy, bed configuration, size, and pricing
 */
export function RoomCard({ room, currency = 'USD', onSelect, isSelected = false }: RoomCardProps) {
  const formatPrice = (price: number, currencyCode: string) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currencyCode,
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(price)
  }

  return (
    <div 
      className={`room-card ${isSelected ? 'room-card--selected' : ''}`}
      onClick={() => onSelect?.(room.id)}
      role="button"
      tabIndex={0}
      aria-pressed={isSelected}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault()
          onSelect?.(room.id)
        }
      }}
    >
      <div className="room-card-header">
        <h3 className="room-card-name">{room.name}</h3>
        <div className="room-card-price">
          <span className="room-card-price-value">
            {formatPrice(room.base_price, room.currency)}
          </span>
          <span className="room-card-price-period">per night</span>
        </div>
      </div>

      <p className="room-card-description">{room.description}</p>

      <div className="room-card-details">
        <div className="room-card-detail">
          <span className="room-card-detail-label">Occupancy</span>
          <span className="room-card-detail-value">
            {room.base_occupancy} - {room.max_occupancy} guests
          </span>
        </div>

        <div className="room-card-detail">
          <span className="room-card-detail-label">Bed Configuration</span>
          <span className="room-card-detail-value">{room.bed_configuration}</span>
        </div>

        {room.room_size && (
          <div className="room-card-detail">
            <span className="room-card-detail-label">Room Size</span>
            <span className="room-card-detail-value">{room.room_size} m²</span>
          </div>
        )}

        <div className="room-card-detail">
          <span className="room-card-detail-label">Available Rooms</span>
          <span className="room-card-detail-value">{room.total_rooms}</span>
        </div>
      </div>

      {isSelected && (
        <div className="room-card-selected-indicator" aria-label="Selected room">
          ✓ Selected
        </div>
      )}
    </div>
  )
}