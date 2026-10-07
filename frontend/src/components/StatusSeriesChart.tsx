import type { StatusGranularity, StatusSeriesRow } from '../adapters/statusAdapter'
import { formatCount, formatMoney, monthLabel } from '../utils/statusFormat'

interface StatusSeriesChartProps {
  series: StatusSeriesRow[]
  granularity: StatusGranularity
  /** 'revenue' needs `currency` */
  metric: 'stayed' | 'guests' | 'revenue'
  currency?: string
}

const METRIC_TITLE = { stayed: 'Stayed bookings', guests: 'Guests', revenue: 'Revenue' }
/** Above this many bars the value labels would overlap; the tooltip still has them */
const MAX_LABELLED_BARS = 14

/** "2026-10" -> "Oct", "2026-10-05" -> "10-05", "2026" -> "2026" */
function bucketLabel(period: string, granularity: StatusGranularity): string {
  if (granularity === 'month') return monthLabel(period)
  if (granularity === 'year') return period
  return period.slice(5)
}

/** Bar chart of one series metric (same approach as the statistics dashboard): one bar per bucket */
export function StatusSeriesChart({ series, granularity, metric, currency }: StatusSeriesChartProps) {
  const valueOf = (row: StatusSeriesRow) => metric === 'revenue'
    ? Number(row.revenue.find(item => item.currency === currency)?.amount ?? 0)
    : row[metric]
  const labelOf = (row: StatusSeriesRow) => metric === 'revenue'
    ? formatMoney({ currency: currency ?? '', amount: String(valueOf(row)) })
    : formatCount(valueOf(row))

  const max = Math.max(0, ...series.map(valueOf))
  const heading = metric === 'revenue' ? `${METRIC_TITLE.revenue} (${currency})` : METRIC_TITLE[metric]
  const title = `${heading} per ${granularity}`

  return (
    <div className="status-chart">
      <h3 className="status-chart-title">{title}</h3>
      <div className="chart-container">
        <div className="bar-chart" role="img" aria-label={title}>
          {series.map(row => {
            const value = valueOf(row)
            return (
              <div key={row.period} className="bar-chart-item">
                <div className="bar-container">
                  <div
                    className={`bar ${metric === 'revenue' ? 'status-bar--revenue' : ''}`}
                    style={{ height: `${max > 0 ? (value / max) * 100 : 0}%` }}
                    title={`${row.period}: ${labelOf(row)}`}
                  >
                    {value > 0 && series.length <= MAX_LABELLED_BARS && <span className="bar-label">{labelOf(row)}</span>}
                  </div>
                </div>
                <div className="bar-period">{bucketLabel(row.period, granularity)}</div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
