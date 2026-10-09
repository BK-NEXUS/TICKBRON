import { DateInventory } from '../adapters/propertyAdapter'
import { DateRangeCalendar } from './DateRangeCalendar'
import { formatDay, nightsBetween, toLocalDate } from '../utils/dates'
import { useI18n } from '../i18n/I18nContext'

interface AvailabilityCalendarProps {
  inventory: DateInventory[]
  currency?: string
  checkIn: string | null
  checkOut: string | null
  onRangeChange: (checkIn: string | null, checkOut: string | null) => void
  /** Rate plan stay rules */
  minNights?: number | null
  maxNights?: number | null
}

type Status = 'available' | 'limited' | 'fully-booked' | 'unavailable'

function statusOf(row?: DateInventory): Status {
  if (!row || row.status === 'closed') return 'unavailable'
  if (!row.is_available || row.available_rooms <= row.booked_rooms) return 'fully-booked'
  if (row.available_rooms - row.booked_rooms <= 1) return 'limited'
  return 'available'
}

const STATUS_COLOR: Record<Status, string> = {
  available: 'var(--color-success)',
  limited: 'var(--color-warning)',
  'fully-booked': 'var(--color-error)',
  unavailable: 'var(--color-error)',
}

/**
 * Availability and price per night for one rate plan, with check-in/check-out
 * selection. A range is refused, naming the date, when a night is closed or
 * sold out or the stay breaks a minimum/maximum stay rule. The total itself
 * comes from the backend quote, not from here.
 */
export function AvailabilityCalendar({
  inventory,
  currency = 'USD',
  checkIn,
  checkOut,
  onRangeChange,
  minNights,
  maxNights,
}: AvailabilityCalendarProps) {
  const byDate = new Map(inventory.map(row => [row.date, row]))
  const { formatMoney } = useI18n()
  const formatPrice = (price: number, code: string) =>
    formatMoney(price, code || currency, { minDecimals: 0, maxDecimals: 0 })

  const validateRange = (start: string, end: string): string | null => {
    const nights = nightsBetween(start, end)
    for (const night of nights) {
      const row = byDate.get(night)
      const status = statusOf(row)
      if (status === 'unavailable') return `${formatDay(night)} is not available. Choose other dates.`
      if (status === 'fully-booked') return `${formatDay(night)} is sold out. Choose other dates.`
    }
    if (minNights && nights.length < minNights) return `Minimum stay is ${minNights} nights.`
    if (maxNights && nights.length > maxNights) return `Maximum stay is ${maxNights} nights.`
    for (const night of nights) {
      const row = byDate.get(night)
      if (row?.min_stay && nights.length < row.min_stay) {
        return `A stay including ${formatDay(night)} must be at least ${row.min_stay} nights.`
      }
      if (row?.max_stay && nights.length > row.max_stay) {
        return `A stay including ${formatDay(night)} can be at most ${row.max_stay} nights.`
      }
    }
    return null
  }

  if (inventory.length === 0) {
    return (
      <div className="availability-calendar availability-calendar--empty">
        <p className="availability-calendar-empty">No availability data available</p>
      </div>
    )
  }

  const today = toLocalDate(new Date())
  const firstOpen = inventory
    .filter(row => row.date >= today && statusOf(row) !== 'unavailable' && statusOf(row) !== 'fully-booked')
    .map(row => row.date)
    .sort()[0]

  return (
    <DateRangeCalendar
      checkIn={checkIn}
      checkOut={checkOut}
      onChange={onRangeChange}
      validateRange={validateRange}
      initialMonth={(checkIn ?? firstOpen ?? inventory[0].date).slice(0, 7)}
      describeDay={(date) => {
        const row = byDate.get(date)
        const status = statusOf(row)
        return {
          selectable: status === 'available' || status === 'limited',
          status,
          content: row && (
            <>
              <div className="availability-calendar-day-price">{formatPrice(row.price, row.currency)}</div>
              <div
                className="availability-calendar-day-indicator"
                style={{ backgroundColor: STATUS_COLOR[status] }}
                aria-hidden="true"
              />
            </>
          ),
        }
      }}
    >
      <div className="availability-calendar-legend">
        <div className="availability-calendar-legend-item">
          <div className="availability-calendar-legend-color" style={{ backgroundColor: STATUS_COLOR.available }} />
          <span>Available</span>
        </div>
        <div className="availability-calendar-legend-item">
          <div className="availability-calendar-legend-color" style={{ backgroundColor: STATUS_COLOR.limited }} />
          <span>Limited</span>
        </div>
        <div className="availability-calendar-legend-item">
          <div className="availability-calendar-legend-color" style={{ backgroundColor: STATUS_COLOR['fully-booked'] }} />
          <span>Fully Booked</span>
        </div>
      </div>
    </DateRangeCalendar>
  )
}
