import { useId, useState } from 'react'
import type { StatusGranularity, StatusSeriesRow } from '../adapters/statusAdapter'
import { chartCurrencies } from '../utils/statusFormat'
import { StatusGranularitySelector } from './StatusGranularitySelector'
import { StatusSeriesChart } from './StatusSeriesChart'

interface StatusSeriesSectionProps {
  series: StatusSeriesRow[]
  granularity: StatusGranularity
  onGranularityChange: (granularity: StatusGranularity) => void
}

const TEXT = {
  currency: 'Chart currency',
  empty: 'No bookings in this period.',
  noRevenue: 'No revenue in this period.',
}

/** The period's series as charts (stayed, guests, revenue per currency) with the bucket size and currency choice */
export function StatusSeriesSection({ series, granularity, onGranularityChange }: StatusSeriesSectionProps) {
  const id = useId()
  const [currency, setCurrency] = useState<string | null>(null)
  const currencies = chartCurrencies(series)
  const chartCurrency = currency && currencies.includes(currency) ? currency : currencies[0]
  const hasData = series.some(row => row.bookings > 0)

  return (
    <section className="status-series">
      <div className="status-controls">
        <StatusGranularitySelector value={granularity} onChange={onGranularityChange} />
        {currencies.length > 1 && (
          <div className="status-field">
            <label htmlFor={`${id}-currency`}>{TEXT.currency}</label>
            <select id={`${id}-currency`} value={chartCurrency} onChange={e => setCurrency(e.target.value)}>
              {currencies.map(c => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>
        )}
      </div>
      {hasData ? (
        <div className="status-charts">
          <StatusSeriesChart series={series} granularity={granularity} metric="stayed" />
          <StatusSeriesChart series={series} granularity={granularity} metric="guests" />
          {chartCurrency ? (
            <StatusSeriesChart series={series} granularity={granularity} metric="revenue" currency={chartCurrency} />
          ) : (
            <div className="empty-state"><p>{TEXT.noRevenue}</p></div>
          )}
        </div>
      ) : (
        <div className="empty-state"><p>{TEXT.empty}</p></div>
      )}
    </section>
  )
}
