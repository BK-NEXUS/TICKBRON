import { ReactNode, useState } from 'react'
import { formatDay, toLocalDate } from '../utils/dates'

export interface CalendarDayInfo {
  /** Can a stay start on this day? */
  selectable: boolean
  /** Extra modifier, e.g. "available" -> availability-calendar-day--available */
  status?: string
  /** Shown under the day number (e.g. the price) */
  content?: ReactNode
}

interface DateRangeCalendarProps {
  checkIn: string | null
  checkOut: string | null
  /** Called with (checkIn, null) after the first click and (checkIn, checkOut) after the second */
  onChange: (checkIn: string | null, checkOut: string | null) => void
  /** Per-day state; by default every day from minDate on can start a stay */
  describeDay?: (date: string) => CalendarDayInfo
  /** Reason the range [checkIn, checkOut) cannot be booked, or null */
  validateRange?: (checkIn: string, checkOut: string) => string | null
  /** YYYY-MM-DD; earlier days cannot be picked */
  minDate?: string
  /** YYYY-MM shown first; defaults to the check-in month, then the current month */
  initialMonth?: string
  className?: string
  children?: ReactNode
}

const WEEKDAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']

function monthStart(value?: string | null): Date {
  if (value) {
    const [year, month] = value.split('-').map(Number)
    return new Date(year, month - 1, 1)
  }
  const now = new Date()
  return new Date(now.getFullYear(), now.getMonth(), 1)
}

/**
 * Month calendar for choosing a stay: first click is the check-in, second click
 * the check-out, and the nights in between are highlighted. A day that cannot
 * start a stay can still be the check-out day, since no night is spent on it.
 */
export function DateRangeCalendar({
  checkIn,
  checkOut,
  onChange,
  describeDay,
  validateRange,
  minDate = toLocalDate(new Date()),
  initialMonth,
  className = '',
  children,
}: DateRangeCalendarProps) {
  const [month, setMonth] = useState(() => monthStart(initialMonth ?? checkIn))
  const [error, setError] = useState<string | null>(null)

  const pickingCheckOut = Boolean(checkIn && !checkOut)
  const info = (date: string): CalendarDayInfo => {
    const base = describeDay ? describeDay(date) : { selectable: true }
    return { ...base, selectable: base.selectable && date >= minDate }
  }
  const canPick = (date: string) => (pickingCheckOut && checkIn && date > checkIn) || info(date).selectable

  const pick = (date: string) => {
    if (!canPick(date)) return
    setError(null)
    if (!pickingCheckOut || !checkIn || date <= checkIn) {
      onChange(date, null)
      return
    }
    const problem = validateRange?.(checkIn, date) ?? null
    if (problem) {
      setError(problem)
      return
    }
    onChange(checkIn, date)
  }

  const year = month.getFullYear()
  const monthIndex = month.getMonth()
  const daysInMonth = new Date(year, monthIndex + 1, 0).getDate()
  const cells: Array<string | null> = [
    ...Array(new Date(year, monthIndex, 1).getDay()).fill(null),
    ...Array.from({ length: daysInMonth }, (_, i) => toLocalDate(new Date(year, monthIndex, i + 1))),
  ]
  const title = month.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })

  const rangeClass = (date: string) => {
    if (date === checkIn) return 'availability-calendar-day--range-start availability-calendar-day--selected'
    if (date === checkOut) return 'availability-calendar-day--range-end availability-calendar-day--selected'
    if (checkIn && checkOut && date > checkIn && date < checkOut) return 'availability-calendar-day--in-range'
    return ''
  }

  return (
    <div className={`availability-calendar ${className}`.trim()}>
      <div className="availability-calendar-header">
        <button
          type="button"
          className="availability-calendar-nav availability-calendar-nav--prev"
          onClick={() => setMonth(new Date(year, monthIndex - 1, 1))}
          aria-label="Previous month"
        >
          ‹
        </button>
        <h3 className="availability-calendar-title">{title}</h3>
        <button
          type="button"
          className="availability-calendar-nav availability-calendar-nav--next"
          onClick={() => setMonth(new Date(year, monthIndex + 1, 1))}
          aria-label="Next month"
        >
          ›
        </button>
      </div>

      <div className="availability-calendar-weekdays">
        {WEEKDAYS.map(day => (
          <div key={day} className="availability-calendar-weekday">{day}</div>
        ))}
      </div>

      <div className="availability-calendar-days">
        {cells.map((date, index) => {
          if (!date) {
            return <div key={`empty-${index}`} className="availability-calendar-day availability-calendar-day--empty" />
          }
          const day = info(date)
          const enabled = canPick(date)
          const selected = date === checkIn || date === checkOut
          return (
            <div
              key={date}
              data-date={date}
              className={[
                'availability-calendar-day',
                day.status ? `availability-calendar-day--${day.status}` : '',
                rangeClass(date),
              ].filter(Boolean).join(' ')}
              onClick={() => pick(date)}
              role="button"
              tabIndex={enabled ? 0 : -1}
              aria-label={formatDay(date)}
              aria-pressed={selected}
              aria-disabled={!enabled}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault()
                  pick(date)
                }
              }}
            >
              <div className="availability-calendar-day-number">{Number(date.slice(-2))}</div>
              {day.content}
            </div>
          )
        })}
      </div>

      {error && (
        <p className="availability-calendar-error" role="alert">{error}</p>
      )}

      {children}
    </div>
  )
}
