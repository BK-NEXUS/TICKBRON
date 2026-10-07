import { useEffect, useId, useState } from 'react'
import { statusAdapter, PartnerStatus } from '../adapters/statusAdapter'
import { useStatusPeriod } from '../hooks/useStatusPeriod'
import { StatusPeriodSelector } from './StatusPeriodSelector'
import { StatusMonthlyChart } from './StatusMonthlyChart'
import { StatusReport } from './StatusReport'
import { StatusCsvButton } from './StatusCsvButton'
import { PartnerArrivals } from './PartnerArrivals'
import { PartnerHotelStatus } from './PartnerHotelStatus'
import { chartCurrencies, formatCount, formatDate, formatMoneyList } from '../utils/statusFormat'

const TEXT = {
  title: 'Status',
  subtitle: 'Your numbers on TICKBRON. Stayed guests lead; counted bookings (confirmed and completed) are shown separately. By check-in date.',
  loading: 'Loading your numbers...',
  since: 'On TICKBRON since',
  guestsLabel: 'Guests via TICKBRON',
  properties: 'Your properties',
  noProperties: 'No properties yet. Numbers appear here once guests book them.',
  headers: { property: 'Property', location: 'Location', counted: 'Counted', stayed: 'Stayed', guests: 'Guests', revenue: 'Revenue' },
  yearTitle: 'Year overview',
  chartYear: 'Chart year',
  chartCurrency: 'Chart currency',
  noRevenue: (year: number) => `No revenue in ${year}.`,
}

/**
 * Partner panel > Status: the owner's own numbers (summary, series, reconciliation, arrivals, CSV)
 * and a page per own hotel. Revenue is one amount per currency.
 */
export function PartnerStatusTab() {
  const id = useId()
  const { params, period, range, granularity, setPeriod, setRange, setGranularity } = useStatusPeriod()
  const [year, setYear] = useState<number | undefined>(undefined)
  const [currency, setCurrency] = useState<string | null>(null)
  const [hotelId, setHotelId] = useState<number | null>(null)
  const [data, setData] = useState<PartnerStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)
    statusAdapter.getPartnerStatus(year === undefined ? params : { ...params, year }).then(response => {
      if (cancelled) return
      if (response.data) setData(response.data)
      setError(response.error)
      setLoading(false)
    })
    return () => { cancelled = true }
  }, [params, year])

  if (hotelId !== null) return <PartnerHotelStatus hotelId={hotelId} onBack={() => setHotelId(null)} />

  const header = (
    <div className="admin-view-header">
      <h1 className="admin-view-title">{TEXT.title}</h1>
      <p className="admin-view-subtitle">{TEXT.subtitle}</p>
    </div>
  )

  if (!data && !error) {
    return (
      <div className="partner-status">
        {header}
        <div className="loading-state" role="status" aria-live="polite">{TEXT.loading}</div>
      </div>
    )
  }

  const years = data ? (data.available_years.includes(data.year) ? data.available_years : [...data.available_years, data.year].sort()) : []
  const currencies = data ? chartCurrencies(data.monthly) : []
  const chartCurrency = currency && currencies.includes(currency) ? currency : currencies[0]

  return (
    <div className="partner-status" aria-busy={loading}>
      {header}

      <div className="status-controls">
        <StatusPeriodSelector value={period} range={range} onChange={setPeriod} onRangeChange={setRange} />
        <StatusCsvButton onExport={() => statusAdapter.exportPartnerReconciliation(params)} />
      </div>

      {error ? (
        <div className="alert alert-error" role="alert">{error}</div>
      ) : data && (
        <>
          <StatusReport
            period={data.period} periodRange={data.period_range} totals={data.totals} series={data.series}
            granularity={granularity} onGranularityChange={setGranularity} reconciliation={data.reconciliation}
            lead={{ label: TEXT.since, value: formatDate(data.since) }} guestsLabel={TEXT.guestsLabel}
          />

          {data.properties.length === 0 ? (
            <div className="empty-state"><p>{TEXT.noProperties}</p></div>
          ) : (
            <div className="customers-table-container">
              <table className="customers-table status-table" aria-label={TEXT.properties}>
                <thead>
                  <tr>
                    <th scope="col">{TEXT.headers.property}</th>
                    <th scope="col">{TEXT.headers.location}</th>
                    <th scope="col" className="status-cell--numeric">{TEXT.headers.counted}</th>
                    <th scope="col" className="status-cell--numeric">{TEXT.headers.stayed}</th>
                    <th scope="col" className="status-cell--numeric">{TEXT.headers.guests}</th>
                    <th scope="col" className="status-cell--numeric">{TEXT.headers.revenue}</th>
                  </tr>
                </thead>
                <tbody>
                  {data.properties.map(property => (
                    <tr key={property.id}>
                      <td>
                        <button type="button" className="status-row-link" onClick={() => setHotelId(property.id)}>
                          {property.name}
                        </button>
                      </td>
                      <td>{property.city}, {property.region}, {property.country}</td>
                      <td className="status-cell--numeric">{formatCount(property.bookings)}</td>
                      <td className="status-cell--numeric">{formatCount(property.stayed)}</td>
                      <td className="status-cell--numeric">{formatCount(property.guests)}</td>
                      <td className="status-cell--numeric">{formatMoneyList(property.revenue)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          <PartnerArrivals />

          <h3 className="status-chart-title">{TEXT.yearTitle}</h3>
          <div className="status-controls">
            <div className="status-field">
              <label htmlFor={`${id}-year`}>{TEXT.chartYear}</label>
              <select id={`${id}-year`} value={data.year} onChange={e => setYear(Number(e.target.value))}>
                {years.map(y => <option key={y} value={y}>{y}</option>)}
              </select>
            </div>
            {currencies.length > 1 && (
              <div className="status-field">
                <label htmlFor={`${id}-currency`}>{TEXT.chartCurrency}</label>
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
              <div className="empty-state"><p>{TEXT.noRevenue(data.year)}</p></div>
            )}
            <StatusMonthlyChart months={data.monthly} year={data.year} metric="guests" />
          </div>
        </>
      )}
    </div>
  )
}
