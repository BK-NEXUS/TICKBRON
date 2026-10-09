import { textKeys, useTexts } from '../i18n/I18nContext'
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

const TEXT_KEYS = textKeys({
  // TODO: show stayed_guests (persons) when the API provides it
  stayed: 'status.stayed',
  stayedHint: 'status.stayedHint',
  counted: 'status.counted',
  countedHint: 'status.countedHint',
  upcoming: 'bookings.filterUpcoming',
  upcomingHint: 'status.upcomingHint',
  guests: 'searchForm.guests',
  guestsHint: 'status.guestsHint',
  unique: 'status.unique',
  uniqueHint: 'status.uniqueHint',
  nights: 'status.nights',
  roomNights: 'status.roomNights',
  revenue: 'status.revenue',
  revenueHint: 'status.revenueHint',
  value: 'status.value',
  valueHint: 'status.valueHint',
  fullyRefunded: 'status.fullyRefunded',
  fullyRefundedHint: 'status.fullyRefundedHint',
  noShow: 'status.booking.no_show',
  noShowHint: 'status.noShowHint',
  noShowReported: 'status.noShowReported',
  noShowReportedHint: 'status.noShowReportedHint',

})

interface Card {
  label: string
  value: string
  hint: string
  headline?: boolean
}

type Text = { [K in keyof typeof TEXT_KEYS]: string }

function cardsOf(totals: StatusFullTotals, guestsLabel: string, TEXT: Text): Card[] {
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
export function StatusStatsCards({ totals, caption, lead, guestsLabel: guestsLabelProp }: StatusStatsCardsProps) {
  const TEXT = useTexts(TEXT_KEYS)
  const guestsLabel = guestsLabelProp ?? TEXT.guests
  return (
    <div className="status-cards">
      {lead && (
        <div className="status-card">
          <span className="status-card-label">{lead.label}</span>
          <span className="status-card-value">{lead.value}</span>
        </div>
      )}
      {cardsOf(totals, guestsLabel, TEXT).map(card => (
        <div key={card.label} className={`status-card${card.headline ? ' status-card--headline' : ''}`}>
          <span className="status-card-label">{card.label}</span>
          <span className="status-card-value">{card.value}</span>
          <span className="status-card-caption">{card.label === TEXT.upcoming ? card.hint : `${caption}, ${card.hint}`}</span>
        </div>
      ))}
    </div>
  )
}
