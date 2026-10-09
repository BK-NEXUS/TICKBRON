import { useI18n } from '../i18n/I18nContext'
import type { StatusMonth } from '../adapters/statusAdapter'
import { formatCount, formatMoney, monthLabel } from '../utils/statusFormat'

interface StatusMonthlyChartProps {
  months: StatusMonth[]
  year: number
  /** 'guests' or 'revenue' (revenue needs `currency`) */
  metric: 'guests' | 'revenue'
  currency?: string
}

/** Simple bar chart (same approach as the statistics dashboard): one bar per month */
export function StatusMonthlyChart({ months, year, metric, currency }: StatusMonthlyChartProps) {
  const i18n = useI18n()
  const { t } = i18n
  const valueOf = (month: StatusMonth) => metric === 'guests'
    ? month.guests
    : Number(month.revenue.find(item => item.currency === currency)?.amount ?? 0)
  const labelOf = (month: StatusMonth) => metric === 'guests'
    ? formatCount(month.guests)
    : formatMoney({ currency: currency ?? '', amount: String(valueOf(month)) })

  const max = Math.max(0, ...months.map(valueOf))
  const title = metric === 'guests'
    ? t('status.guestsPerMonth', { year })
    : t('status.revenuePerMonth', { currency: currency ?? '', year })

  return (
    <div className="status-chart">
      <h3 className="status-chart-title">{title}</h3>
      <div className="chart-container">
        <div className="bar-chart" role="img" aria-label={title}>
          {months.map(month => {
            const value = valueOf(month)
            return (
              <div key={month.month} className="bar-chart-item">
                <div className="bar-container">
                  <div
                    className={`bar ${metric === 'revenue' ? 'status-bar--revenue' : ''}`}
                    style={{ height: `${max > 0 ? (value / max) * 100 : 0}%` }}
                    title={labelOf(month)}
                  >
                    {value > 0 && <span className="bar-label">{labelOf(month)}</span>}
                  </div>
                </div>
                <div className="bar-period">{monthLabel(month.month, i18n)}</div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
