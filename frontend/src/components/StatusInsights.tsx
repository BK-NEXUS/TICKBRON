import { useI18n } from '../i18n/I18nContext'
import type { StatusInsights as Insights, StatusRank } from '../adapters/statusAdapter'
import { formatMoneyList } from '../utils/statusFormat'

interface StatusInsightsProps {
  insights: Insights
  /** The owner's place in the region; null or missing hides the card */
  rank?: StatusRank | null
}

const DASH = '—'
const MINUS = '−'

const percent = (value: string | null) => (value === null ? DASH : `${value}%`)

interface Card {
  label: string
  value: string
  hint: string
}

interface Change {
  label: string
  description: string
  text: string
}

/** R12 additions: rates, averages, the rank and the change against the previous period */
export function StatusInsights({ insights, rank }: StatusInsightsProps) {
  const { t } = useI18n()

  const describe = (pct: string | null): { description: string; text: string } => {
    if (pct === null) return { description: t('status.insights.noBase'), text: DASH }
    const value = Number(pct)
    if (value === 0) return { description: t('status.insights.same'), text: `${pct}%` }
    const size = Math.abs(value).toFixed(1)
    return value > 0
      ? { description: t('status.insights.up', { value: size }), text: `+${size}%` }
      : { description: t('status.insights.down', { value: size }), text: `${MINUS}${size}%` }
  }

  const cards: Card[] = [
    { label: t('status.insights.cancellationRate'), value: percent(insights.cancellation_rate), hint: t('status.insights.cancellationRateHint') },
    { label: t('status.insights.occupancy'), value: percent(insights.occupancy_rate), hint: t('status.insights.occupancyHint') },
    { label: t('status.insights.averageValue'), value: formatMoneyList(insights.average_booking_value), hint: t('status.insights.averageValueHint') },
    {
      label: t('status.insights.averageStay'),
      value: insights.average_stay_nights === null ? DASH : t('status.insights.averageStayValue', { value: insights.average_stay_nights }),
      hint: t('status.insights.averageStayHint'),
    },
  ]
  if (rank) {
    cards.push({
      label: t('status.insights.rank'),
      value: t('status.insights.rankValue', { position: rank.position, of: rank.of }),
      hint: t('status.insights.rankHint'),
    })
  }

  const changes: Change[] = insights.change_pct ? [
    { label: t('status.bookings'), pct: insights.change_pct.bookings },
    { label: t('searchForm.guests'), pct: insights.change_pct.guests },
    { label: t('status.nights'), pct: insights.change_pct.nights },
    { label: t('status.stayed'), pct: insights.change_pct.stayed },
    ...insights.change_pct.revenue.map(row => ({ label: `${t('status.revenue')} ${row.currency}`, pct: row.pct })),
  ].map(({ label, pct }) => ({ label, ...describe(pct) })) : []

  return (
    <>
      <div className="status-cards">
        {cards.map(card => (
          <div key={card.label} className="status-card">
            <span className="status-card-label">{card.label}</span>
            <span className="status-card-value">{card.value}</span>
            <span className="status-card-caption">{card.hint}</span>
          </div>
        ))}
      </div>
      {insights.previous_period && changes.length > 0 && (
        <div className="status-changes">
          <p className="status-changes-title">
            {t('status.insights.compared', { from: insights.previous_period.range.from, to: insights.previous_period.range.to })}
          </p>
          <ul className="status-changes-list">
            {changes.map(change => (
              <li key={change.label} className="status-change" aria-label={`${change.label}: ${change.description}`}>
                <span className="status-change-label" aria-hidden="true">{change.label}</span>
                <span className="status-change-value" aria-hidden="true">{change.text}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </>
  )
}
