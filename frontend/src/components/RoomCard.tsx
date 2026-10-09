import { Check } from 'lucide-react'
import { RoomType } from '../adapters/propertyAdapter'
import { useI18n } from '../i18n/I18nContext'

interface RoomCardProps {
  room: RoomType
  onSelect?: (roomId: number) => void
  isSelected?: boolean
}

/**
 * RoomCard component for displaying room information
 * Shows room details, occupancy, bed configuration, size, and pricing
 */
export function RoomCard({ room, onSelect, isSelected = false }: RoomCardProps) {
  const { t, formatMoney } = useI18n()
  const formatPrice = (price: number, currencyCode: string) => {
    return formatMoney(price, currencyCode, { minDecimals: 0, maxDecimals: 0 })
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
          <span className="room-card-price-period">{t('room.perNight')}</span>
        </div>
      </div>

      <p className="room-card-description">{room.description}</p>

      <div className="room-card-details">
        <div className="room-card-detail">
          <span className="room-card-detail-label">{t('room.occupancy')}</span>
          <span className="room-card-detail-value">
            {t('room.occupancyValue', { base: room.base_occupancy, max: room.max_occupancy })}
          </span>
        </div>

        <div className="room-card-detail">
          <span className="room-card-detail-label">{t('room.beds')}</span>
          <span className="room-card-detail-value">{room.bed_configuration}</span>
        </div>

        {room.room_size && (
          <div className="room-card-detail">
            <span className="room-card-detail-label">{t('room.size')}</span>
            <span className="room-card-detail-value">{room.room_size} m²</span>
          </div>
        )}

        <div className="room-card-detail">
          <span className="room-card-detail-label">{t('room.availableRooms')}</span>
          <span className="room-card-detail-value">{room.total_rooms}</span>
        </div>
      </div>

      {isSelected && (
        <div className="room-card-selected-indicator" aria-label={t('room.selectedLabel')}>
          <Check size={14} aria-hidden="true" /> {t('room.selected')}
        </div>
      )}
    </div>
  )
}