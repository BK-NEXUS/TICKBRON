import { textKeys, useTexts } from '../i18n/I18nContext'
import type { BookingStatusCounts } from '../adapters/statusAdapter'
import { formatCount } from '../utils/statusFormat'

interface StatusBookingStatusCountsProps {
  counts: BookingStatusCounts
}

const TEXT_KEYS = textKeys({
  title: 'status.title3',
  labels: {
    pending: 'pay.statusName.pending',
    confirmed: 'status.booking.confirmed',
    completed: 'pay.statusName.completed',
    cancelled: 'status.booking.cancelled',
    expired: 'status.expired',
    no_show: 'status.booking.no_show',
    no_show_reported: 'status.noShowReported',
  },
})

const ALWAYS: (keyof BookingStatusCounts)[] = ['pending', 'confirmed', 'completed', 'cancelled', 'expired']
const WHEN_NON_ZERO: (keyof BookingStatusCounts)[] = ['no_show', 'no_show_reported']

/** Raw booking counts per status in the period; no-show counts appear only when non-zero */
export function StatusBookingStatusCounts({ counts }: StatusBookingStatusCountsProps) {
  const TEXT = useTexts(TEXT_KEYS)
  const shown = [...ALWAYS, ...WHEN_NON_ZERO.filter(key => counts[key] > 0)]
  return (
    <section className="status-booking-status">
      <h3 className="status-chart-title" id="status-booking-status-title">{TEXT.title}</h3>
      <ul className="status-booking-status-list" aria-labelledby="status-booking-status-title" role="list">
        {shown.map(key => (
          <li key={key}>
            <span>{TEXT.labels[key]}</span>
            <strong>{formatCount(counts[key])}</strong>
          </li>
        ))}
      </ul>
    </section>
  )
}
