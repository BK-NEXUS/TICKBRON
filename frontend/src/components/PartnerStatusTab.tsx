import { useEffect, useId, useState } from 'react'
import { statusAdapter, PartnerStatus } from '../adapters/statusAdapter'
import { StatusPeriodSelector } from './StatusPeriodSelector'
import { StatusMonthlyChart } from './StatusMonthlyChart'
import { StatusTotalsCards } from './StatusTotalsCards'
import { chartCurrencies, formatCount, formatDate, formatMoneyList, periodLabel } from '../utils/statusFormat'

/**
 * Partner panel > Status: the owner's own numbers. Confirmed and completed bookings
 * count, by check-in date; revenue one amount per currency.
 */
export function PartnerStatusTab() {
  const id = useId()
  const [period, setPeriod] = useState('all')
  const [year, setYear] = useState<number | undefined>(undefined)
  const [currency, setCurrency] = useState<string | null>(null)
  const [data, setData] = useState<PartnerStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)
    statusAdapter.getPartnerStatus(year === undefined ? { period } : { period, year }).then(response => {
      if (cancelled) return
      setData(response.data)
      setError(response.error)
      setLoading(false)
    })
    return () => { cancelled = true }
  }, [period, year])

  const header = (
    <div className="admin-view-header">
      <h1 className="admin-view-title">Status</h1>
      <p className="admin-view-subtitle">
        Your numbers on TICKBRON. Confirmed and completed bookings count, by check-in date.
      </p>
    </div>
  )

  if (error) {
    return (
      <div className="partner-status">
        {header}
        <div className="alert alert-error" role="alert">{error}</div>
      </div>
    )
  }
  if (!data) {
    return (
      <div className="partner-status">
        {header}
        <div className="loading-state" role="status" aria-live="polite">Loading your numbers...</div>
      </div>
    )
  }

  const years = data.available_years.includes(data.year)
    ? data.available_years
    : [...data.available_years, data.year].sort()
  const currencies = chartCurrencies(data.monthly)
  const chartCurrency = currency && currencies.includes(currency) ? currency : currencies[0]

  return (
    <div className="partner-status" aria-busy={loading}>
      {header}

      <div className="status-controls">
        <StatusPeriodSelector value={period} onChange={setPeriod} />
      </div>
      <StatusTotalsCards
        totals={data.totals}
        caption={periodLabel(data.period)}
        lead={{ label: 'On TICKBRON since', value: formatDate(data.since) }}
        guestsLabel="Guests via TICKBRON"
      />

      {data.properties.length === 0 ? (
        <div className="empty-state"><p>No properties yet. Numbers appear here once guests book them.</p></div>
      ) : (
        <div className="customers-table-container">
          <table className="customers-table status-table" aria-label="Your properties">
            <thead>
              <tr>
                <th scope="col">Property</th>
                <th scope="col">Location</th>
                <th scope="col" className="status-cell--numeric">Bookings</th>
                <th scope="col" className="status-cell--numeric">Guests</th>
                <th scope="col" className="status-cell--numeric">Revenue</th>
              </tr>
            </thead>
            <tbody>
              {data.properties.map(property => (
                <tr key={property.id}>
                  <td>{property.name}</td>
                  <td>{property.city}, {property.region}, {property.country}</td>
                  <td className="status-cell--numeric">{formatCount(property.bookings)}</td>
                  <td className="status-cell--numeric">{formatCount(property.guests)}</td>
                  <td className="status-cell--numeric">{formatMoneyList(property.revenue)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="status-controls">
        <div className="status-field">
          <label htmlFor={`${id}-year`}>Chart year</label>
          <select id={`${id}-year`} value={data.year} onChange={e => setYear(Number(e.target.value))}>
            {years.map(y => <option key={y} value={y}>{y}</option>)}
          </select>
        </div>
        {currencies.length > 1 && (
          <div className="status-field">
            <label htmlFor={`${id}-currency`}>Chart currency</label>
            <select id={`${id}-currency`} value={chartCurrency} onChange={e => setCurrency(e.target.value)}>
              {currencies.map(c => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>
        )}
      </div>
      <div className="status-charts">
        {chartCurrency ? (
          <StatusMonthlyChart months={data.monthly} year={data.year} metric="revenue" currency={chartCurrency} />
        ) : (
          <div className="empty-state"><p>No revenue in {data.year}.</p></div>
        )}
        <StatusMonthlyChart months={data.monthly} year={data.year} metric="guests" />
      </div>
    </div>
  )
}
