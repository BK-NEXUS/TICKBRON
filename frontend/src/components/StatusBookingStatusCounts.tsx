import type { BookingStatusCounts } from '../adapters/statusAdapter'
import { formatCount } from '../utils/statusFormat'

interface StatusBookingStatusCountsProps {
  counts: BookingStatusCounts
}

const TEXT = {
  title: 'Bookings by status',
  labels: {
    pending: 'Pending',
    confirmed: 'Confirmed',
    completed: 'Completed',
    cancelled: 'Cancelled',
    expired: 'Expired',
    no_show: 'No-show',
    no_show_reported: 'No-show reported',
  } as Record<keyof BookingStatusCounts, string>,
}

const ALWAYS: (keyof BookingStatusCounts)[] = ['pending', 'confirmed', 'completed', 'cancelled', 'expired']
const WHEN_NON_ZERO: (keyof BookingStatusCounts)[] = ['no_show', 'no_show_reported']

/** Raw booking counts per status in the period; no-show counts appear only when non-zero */
export function StatusBookingStatusCounts({ counts }: StatusBookingStatusCountsProps) {
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
