import { useEffect, useId, useState } from 'react'
import { statusAdapter, StatusHotelDetail as HotelDetail } from '../adapters/statusAdapter'
import { StatusPeriodSelector } from './StatusPeriodSelector'
import { StatusMonthlyChart } from './StatusMonthlyChart'
import { StatusTotalsCards } from './StatusTotalsCards'
import { chartCurrencies, formatDate, periodLabel } from '../utils/statusFormat'

interface StatusHotelDetailProps {
  hotelId: number
  period: string
  onPeriodChange: (period: string) => void
}

/** Admin Status > ... > one hotel: info, owner contact, totals and a monthly chart */
export function StatusHotelDetail({ hotelId, period, onPeriodChange }: StatusHotelDetailProps) {
  const id = useId()
  const [year, setYear] = useState<number | undefined>(undefined)
  const [data, setData] = useState<HotelDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [currency, setCurrency] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)
    statusAdapter.getHotelDetail(hotelId, year === undefined ? { period } : { period, year }).then(response => {
      if (cancelled) return
      setData(response.data)
      setError(response.error)
      setLoading(false)
    })
    return () => { cancelled = true }
  }, [hotelId, period, year])

  if (error) return <div className="alert alert-error" role="alert">{error}</div>
  if (!data) return <div className="loading-state" role="status" aria-live="polite">Loading hotel...</div>

  const { hotel, totals, monthly } = data
  const years = data.available_years.includes(data.year) ? data.available_years : [...data.available_years, data.year].sort()
  const currencies = chartCurrencies(monthly)
  const chartCurrency = currency && currencies.includes(currency) ? currency : currencies[0]

  return (
    <section className="status-hotel" aria-busy={loading}>
      <div className="admin-view-header">
        <h2 className="admin-view-title">{hotel.name}</h2>
        <p className="admin-view-subtitle">{hotel.address}</p>
      </div>

      <dl className="status-hotel-info">
        <div><dt>Location</dt><dd>{hotel.city}, {hotel.region}, {hotel.country}</dd></div>
        <div><dt>Status</dt><dd>{hotel.status}</dd></div>
        <div><dt>Registered</dt><dd>{formatDate(hotel.registered_at)}</dd></div>
        <div><dt>Owner</dt><dd>{hotel.owner.name}</dd></div>
        <div><dt>Owner phone</dt><dd>{hotel.owner.phone || '—'}</dd></div>
        <div><dt>Owner email</dt><dd>{hotel.owner.email}</dd></div>
      </dl>

      <div className="status-controls">
        <StatusPeriodSelector value={period} onChange={onPeriodChange} />
      </div>
      <StatusTotalsCards totals={totals} caption={periodLabel(data.period)} />

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
          <StatusMonthlyChart months={monthly} year={data.year} metric="revenue" currency={chartCurrency} />
        ) : (
          <div className="empty-state"><p>No revenue in {data.year}.</p></div>
        )}
        <StatusMonthlyChart months={monthly} year={data.year} metric="guests" />
      </div>
    </section>
  )
}
