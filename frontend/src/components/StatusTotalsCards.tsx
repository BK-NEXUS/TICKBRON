import type { StatusTotals } from '../adapters/statusAdapter'
import { formatCount, formatMoneyList } from '../utils/statusFormat'

interface StatusTotalsCardsProps {
  totals: StatusTotals
  /** e.g. "All time" or "April 2026" */
  caption: string
  /** Extra first card, e.g. the partner's "since" date */
  lead?: { label: string; value: string }
  /** Label of the guests card (partner: "Guests via TICKBRON") */
  guestsLabel?: string
}

/** Summary cards: bookings, guests and revenue (one line per currency) */
export function StatusTotalsCards({ totals, caption, lead, guestsLabel = 'Guests' }: StatusTotalsCardsProps) {
  return (
    <div className="status-cards">
      {lead && (
        <div className="status-card">
          <span className="status-card-label">{lead.label}</span>
          <span className="status-card-value">{lead.value}</span>
        </div>
      )}
      <div className="status-card">
        <span className="status-card-label">Bookings</span>
        <span className="status-card-value">{formatCount(totals.bookings)}</span>
        <span className="status-card-caption">{caption}</span>
      </div>
      <div className="status-card">
        <span className="status-card-label">{guestsLabel}</span>
        <span className="status-card-value">{formatCount(totals.guests)}</span>
        <span className="status-card-caption">{caption}</span>
      </div>
      <div className="status-card">
        <span className="status-card-label">Revenue</span>
        <span className="status-card-value">{formatMoneyList(totals.revenue)}</span>
        <span className="status-card-caption">{caption}, confirmed and completed bookings</span>
      </div>
    </div>
  )
}

