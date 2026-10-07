import type { StatusFullTotals } from '../adapters/statusAdapter'
import { formatCount, formatMoneyList } from '../utils/statusFormat'

interface StatusStatsCardsProps {
  totals: StatusFullTotals
  /** e.g. "All time" or "April 2026" */
  caption: string
  /** Extra first card, e.g. the partner's "since" date */
  lead?: { label: string; value: string }
  /** Label of the guests card (partner: "Guests via TICKBRON") */
  guestsLabel?: string
}

const TEXT = {
  // TODO: show stayed_guests (persons) when the API provides it
  stayed: 'Stayed bookings',
  stayedHint: 'completed bookings',
  counted: 'Counted',
  countedHint: 'confirmed and completed bookings',
  upcoming: 'Upcoming',
  upcomingHint: 'confirmed, check-in after today (not limited by the period)',
  guests: 'Guests',
  guestsHint: 'persons in counted bookings',
  unique: 'Unique customers',
  uniqueHint: 'distinct accounts',
  nights: 'Nights',
  roomNights: 'room nights',
  revenue: 'Revenue',
  revenueHint: 'paid minus refunded, per currency',
  value: 'Booking value',
  valueHint: 'total price of counted bookings, per currency',
  fullyRefunded: 'Fully refunded',
  fullyRefundedHint: 'left out of every other number',
  noShow: 'No-show',
  noShowHint: 'guest did not arrive',
  noShowReported: 'No-show reported',
  noShowReportedHint: 'waiting for a decision',
}

interface Card {
  label: string
  value: string
  hint: string
  headline?: boolean
}

function cardsOf(totals: StatusFullTotals, guestsLabel: string): Card[] {
  const cards: Card[] = [
    { label: TEXT.stayed, value: formatCount(totals.stayed), hint: TEXT.stayedHint, headline: true },
    { label: TEXT.counted, value: formatCount(totals.counted), hint: TEXT.countedHint },
    { label: TEXT.upcoming, value: formatCount(totals.upcoming), hint: TEXT.upcomingHint },
    { label: guestsLabel, value: formatCount(totals.guests), hint: TEXT.guestsHint },
    { label: TEXT.unique, value: formatCount(totals.unique_customers), hint: TEXT.uniqueHint },
    { label: TEXT.nights, value: formatCount(totals.nights), hint: `${formatCount(totals.room_nights)} ${TEXT.roomNights}` },
    { label: TEXT.revenue, value: formatMoneyList(totals.revenue), hint: TEXT.revenueHint },
    { label: TEXT.value, value: formatMoneyList(totals.booking_value), hint: TEXT.valueHint },
  ]
  if (totals.fully_refunded > 0) {
    cards.push({ label: TEXT.fullyRefunded, value: formatCount(totals.fully_refunded), hint: TEXT.fullyRefundedHint })
  }
  if (totals.no_show > 0) cards.push({ label: TEXT.noShow, value: formatCount(totals.no_show), hint: TEXT.noShowHint })
  if (totals.no_show_reported > 0) {
    cards.push({ label: TEXT.noShowReported, value: formatCount(totals.no_show_reported), hint: TEXT.noShowReportedHint })
  }
  return cards
}

/** R12a summary cards: "stayed" is the headline; counted and upcoming are separate; money is per currency */
export function StatusStatsCards({ totals, caption, lead, guestsLabel = TEXT.guests }: StatusStatsCardsProps) {
  return (
    <div className="status-cards">
      {lead && (
        <div className="status-card">
          <span className="status-card-label">{lead.label}</span>
          <span className="status-card-value">{lead.value}</span>
        </div>
      )}
      {cardsOf(totals, guestsLabel).map(card => (
        <div key={card.label} className={`status-card${card.headline ? ' status-card--headline' : ''}`}>
          <span className="status-card-label">{card.label}</span>
          <span className="status-card-value">{card.value}</span>
          <span className="status-card-caption">{card.label === TEXT.upcoming ? card.hint : `${caption}, ${card.hint}`}</span>
        </div>
      ))}
    </div>
  )
}
