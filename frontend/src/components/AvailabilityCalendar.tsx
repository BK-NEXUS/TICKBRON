import { DateInventory } from '../adapters/propertyAdapter'
import { DateRangeCalendar } from './DateRangeCalendar'
import { businessToday, nightsBetween } from '../utils/dates'
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
  const { t, tp, formatMoney, formatDay } = useI18n()
  const formatPrice = (price: number, code: string) =>
    formatMoney(price, code || currency, { minDecimals: 0, maxDecimals: 0 })

  const validateRange = (start: string, end: string): string | null => {
    const nights = nightsBetween(start, end)
    for (const night of nights) {
      const row = byDate.get(night)
      const status = statusOf(row)
      if (status === 'unavailable') return t('calendar.closedDay', { day: formatDay(night) })
      if (status === 'fully-booked') return t('calendar.soldOutDay', { day: formatDay(night) })
    }
    if (minNights && nights.length < minNights) return t('calendar.minStay', { nights: tp('rooms.nights', minNights) })
    if (maxNights && nights.length > maxNights) return t('calendar.maxStay', { nights: tp('rooms.nights', maxNights) })
    for (const night of nights) {
      const row = byDate.get(night)
      if (row?.min_stay && nights.length < row.min_stay) {
        return t('calendar.minStayDay', { day: formatDay(night), nights: tp('rooms.nights', row.min_stay) })
      }
      if (row?.max_stay && nights.length > row.max_stay) {
        return t('calendar.maxStayDay', { day: formatDay(night), nights: tp('rooms.nights', row.max_stay) })
      }
    }
    return null
  }

  if (inventory.length === 0) {
    return (
      <div className="availability-calendar availability-calendar--empty">
        <p className="availability-calendar-empty">{t('calendar.none')}</p>
      </div>
    )
  }

  const today = businessToday()
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
          <span>{t('calendar.available')}</span>
        </div>
        <div className="availability-calendar-legend-item">
          <div className="availability-calendar-legend-color" style={{ backgroundColor: STATUS_COLOR.limited }} />
          <span>{t('calendar.limited')}</span>
        </div>
        <div className="availability-calendar-legend-item">
          <div className="availability-calendar-legend-color" style={{ backgroundColor: STATUS_COLOR['fully-booked'] }} />
          <span>{t('calendar.fullyBooked')}</span>
        </div>
      </div>
    </DateRangeCalendar>
  )
}
