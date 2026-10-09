import { textKeys, useI18n, useTexts } from '../i18n/I18nContext'
import { useEffect, useId, useState } from 'react'
import {
  statusAdapter, StatusDetailParams, StatusGranularity, StatusHotelDetail as HotelDetail,
} from '../adapters/statusAdapter'
import { StatusPeriodSelector } from './StatusPeriodSelector'
import { StatusMonthlyChart } from './StatusMonthlyChart'
import { StatusReport } from './StatusReport'
import { chartCurrencies, formatDate } from '../utils/statusFormat'
import type { DateRange } from '../utils/statusPeriod'

interface StatusHotelDetailProps {
  hotelId: number
  period: string
  /** The applied range when period is "custom" */
  range?: DateRange | null
  onPeriodChange: (period: string) => void
  onRangeChange: (range: DateRange) => void
}

const TEXT_KEYS = textKeys({
  loading: 'status.loading2',
  location: 'property.location',
  status: 'partner.status',
  registered: 'status.registered',
  owner: 'status.owner',
  ownerPhone: 'status.ownerPhone',
  ownerEmail: 'status.ownerEmail',
  chartYear: 'status.chartYear',
  chartCurrency: 'status.chartCurrency',
  yearTitle: 'status.yearTitle',

})

function requestOf(
  period: string, range: DateRange | null | undefined, granularity: StatusGranularity | undefined, year: number | undefined,
): StatusDetailParams {
  const params: StatusDetailParams = { period }
  if (period === 'custom' && range) Object.assign(params, { from: range.from, to: range.to })
  if (granularity) params.granularity = granularity
  if (year !== undefined) params.year = year
  return params
}

/** Admin Status > one hotel: info, owner contact, R12a totals, series, reconciliation and the monthly year chart */
export function StatusHotelDetail({ hotelId, period, range, onPeriodChange, onRangeChange }: StatusHotelDetailProps) {
  const TEXT = useTexts(TEXT_KEYS)
  const i18n = useI18n()
  const { t } = i18n
  const id = useId()
  const [year, setYear] = useState<number | undefined>(undefined)
  const [granularity, setGranularity] = useState<StatusGranularity | undefined>(undefined)
  const [data, setData] = useState<HotelDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [currency, setCurrency] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)
    statusAdapter.getHotelDetail(hotelId, requestOf(period, range, granularity, year)).then(response => {
      if (cancelled) return
      if (response.data) setData(response.data)
      setError(response.error)
      setLoading(false)
    })
    return () => { cancelled = true }
  }, [hotelId, period, range, granularity, year])

  if (!data && !error) return <div className="loading-state" role="status" aria-live="polite">{TEXT.loading}</div>

  const hotel = data?.hotel
  const years = data ? (data.available_years.includes(data.year) ? data.available_years : [...data.available_years, data.year].sort()) : []
  const currencies = data ? chartCurrencies(data.monthly) : []
  const chartCurrency = currency && currencies.includes(currency) ? currency : currencies[0]

  return (
    <section className="status-hotel" aria-busy={loading}>
      {hotel && (
        <>
          <div className="admin-view-header">
            <h2 className="admin-view-title">{hotel.name}</h2>
            <p className="admin-view-subtitle">{hotel.address}</p>
          </div>

          <dl className="status-hotel-info">
            <div><dt>{TEXT.location}</dt><dd>{hotel.city}, {hotel.region}, {hotel.country}</dd></div>
            <div><dt>{TEXT.status}</dt><dd>{hotel.status}</dd></div>
            <div><dt>{TEXT.registered}</dt><dd>{formatDate(hotel.registered_at, i18n)}</dd></div>
            <div><dt>{TEXT.owner}</dt><dd>{hotel.owner.name}</dd></div>
            <div><dt>{TEXT.ownerPhone}</dt><dd>{hotel.owner.phone || '—'}</dd></div>
            <div><dt>{TEXT.ownerEmail}</dt><dd>{hotel.owner.email}</dd></div>
          </dl>
        </>
      )}

      <div className="status-controls">
        <StatusPeriodSelector value={period} range={range} onChange={onPeriodChange} onRangeChange={onRangeChange} />
      </div>

      {error ? (
        <div className="alert alert-error" role="alert">{error}</div>
      ) : data && (
        <>
          <StatusReport
            period={data.period} periodRange={data.period_range} totals={data.totals} series={data.series}
            granularity={granularity ?? data.granularity} onGranularityChange={setGranularity}
            reconciliation={data.reconciliation}
          />

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
              <div className="empty-state"><p>{t('status.noRevenueIn', { year: data.year })}</p></div>
            )}
            <StatusMonthlyChart months={data.monthly} year={data.year} metric="guests" />
          </div>
        </>
      )}
    </section>
  )
}
