import { useI18n } from '../i18n/I18nContext'
import { ReactNode, useEffect, useRef, useState } from 'react'
import { businessToday, toLocalDate } from '../utils/dates'

export interface CalendarDayInfo {
  /** Turıw usı kúnnen baslana ala ma? */
  selectable: boolean
  /** Qosımsha modifikator, mısalı "available" -> availability-calendar-day--available */
  status?: string
  /** Kún nomeri astında kórsetiledi (mısalı baha) */
  content?: ReactNode
}

interface DateRangeCalendarProps {
  checkIn: string | null
  checkOut: string | null
  /** Birinshi klikten keyin (checkIn, null) menen, ekinshisinen keyin (checkIn, checkOut) penen shaqırıladı */
  onChange: (checkIn: string | null, checkOut: string | null) => void
  /** Kún boyınsha jaǵday; ádetde minDate nan baslap hár kún turıwdı baslay aladı */
  describeDay?: (date: string) => CalendarDayInfo
  /** [checkIn, checkOut) aralıǵın bronlap bolmaytuǵın sebep, yamasa null */
  validateRange?: (checkIn: string, checkOut: string) => string | null
  /** YYYY-MM-DD; aldınǵı kúnlerdi tańlap bolmaydı */
  minDate?: string
  /** Aldın kórsetiletuǵın YYYY-MM; ádetde check-in ayı, keyin házirgi ay */
  initialMonth?: string
  /** Kalendar aydı birinshi ret kórsetkende hám ay ózgergen hár waqıtta 'YYYY-MM' penen shaqırıladı */
  onMonthChange?: (month: string) => void
  className?: string
  children?: ReactNode
}

function monthStart(value?: string | null): Date {
  if (value) {
    const [year, month] = value.split('-').map(Number)
    return new Date(year, month - 1, 1)
  }
  const [year, month] = businessToday().split('-').map(Number)
  return new Date(year, month - 1, 1)
}

/**
 * Turıwdı tańlaw ushın ay kalendarı: birinshi klik check-in, ekinshisi
 * check-out, hám aradaǵı túnler ajıratıladı. Turıwdı baslay almaytuǵın kún
 * ele check-out kúni bola aladı, sebebi onda tún ótkizilmeydi.
 */
export function DateRangeCalendar({
  checkIn,
  checkOut,
  onChange,
  describeDay,
  validateRange,
  minDate = businessToday(),
  initialMonth,
  onMonthChange,
  className = '',
  children,
}: DateRangeCalendarProps) {
  const { t, formatDate, formatDay } = useI18n()
  const [month, setMonth] = useState(() => monthStart(initialMonth ?? checkIn))
  const [error, setError] = useState<string | null>(null)

  const year = month.getFullYear()
  const monthIndex = month.getMonth()
  const onMonthChangeRef = useRef(onMonthChange)
  onMonthChangeRef.current = onMonthChange
  useEffect(() => {
    onMonthChangeRef.current?.(`${year}-${String(monthIndex + 1).padStart(2, '0')}`)
  }, [year, monthIndex])

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

  const daysInMonth = new Date(year, monthIndex + 1, 0).getDate()
  const cells: Array<string | null> = [
    ...Array(new Date(year, monthIndex, 1).getDay()).fill(null),
    ...Array.from({ length: daysInMonth }, (_, i) => toLocalDate(new Date(year, monthIndex, i + 1))),
  ]
  const title = formatDate(month, { month: 'long', year: 'numeric' })
  // 2024-01-07 jekshembi: bet tilindegi jeti qısqa hápte kúni atı, jekshembi birinshi
  const weekdays = Array.from({ length: 7 }, (_, i) => formatDate(new Date(2024, 0, 7 + i), { weekday: 'short' }))

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
          aria-label={t('calendar.previousMonth')}
        >
          ‹
        </button>
        <h3 className="availability-calendar-title">{title}</h3>
        <button
          type="button"
          className="availability-calendar-nav availability-calendar-nav--next"
          onClick={() => setMonth(new Date(year, monthIndex + 1, 1))}
          aria-label={t('calendar.nextMonth')}
        >
          ›
        </button>
      </div>

      <div className="availability-calendar-weekdays">
        {weekdays.map(day => (
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
