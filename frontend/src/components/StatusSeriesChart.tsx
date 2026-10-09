import type { StatusGranularity, StatusSeriesRow } from '../adapters/statusAdapter'
import { useI18n, type I18nValue } from '../i18n/I18nContext'
import type { MessageKey } from '../i18n/messages/en'
import { formatCount, formatMoney, monthLabel } from '../utils/statusFormat'

interface StatusSeriesChartProps {
  series: StatusSeriesRow[]
  granularity: StatusGranularity
  /** 'revenue' needs `currency` */
  metric: 'stayed' | 'guests' | 'revenue'
  currency?: string
}

const METRIC_TITLE: Record<'stayed' | 'guests' | 'revenue', MessageKey> = {
  stayed: 'status.stayed', guests: 'status.guests', revenue: 'status.revenue',
}
const PER: Record<StatusGranularity, MessageKey> = {
  day: 'status.perDay', week: 'status.perWeek', month: 'status.perMonth', year: 'status.perYear',
}
/** Above this many bars the value labels would overlap; the tooltip still has them */
const MAX_LABELLED_BARS = 14

/** "2026-10" -> "Oct", "2026-10-05" -> "10-05", "2026" -> "2026" */
function bucketLabel(period: string, granularity: StatusGranularity, i18n: I18nValue): string {
  if (granularity === 'month') return monthLabel(period, i18n)
  if (granularity === 'year') return period
  return period.slice(5)
}

/** Bar chart of one series metric (same approach as the statistics dashboard): one bar per bucket */
export function StatusSeriesChart({ series, granularity, metric, currency }: StatusSeriesChartProps) {
  const i18n = useI18n()
  const { t } = i18n
  const valueOf = (row: StatusSeriesRow) => metric === 'revenue'
    ? Number(row.revenue.find(item => item.currency === currency)?.amount ?? 0)
    : row[metric]
  const labelOf = (row: StatusSeriesRow) => metric === 'revenue'
    ? formatMoney({ currency: currency ?? '', amount: String(valueOf(row)) })
    : formatCount(valueOf(row))

  const max = Math.max(0, ...series.map(valueOf))
  const heading = metric === 'revenue' ? t('status.revenueCurrency', { currency: currency ?? '' }) : t(METRIC_TITLE[metric])
  const title = t('status.chartTitle', { metric: heading, per: t(PER[granularity]) })

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
                <div className="bar-period">{bucketLabel(row.period, granularity, i18n)}</div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
