import { useEffect, useState } from 'react'
import { statusAdapter, StatusPeriodParams, StatusUserDetail as UserDetail } from '../adapters/statusAdapter'
import { StatusPeriodSelector } from './StatusPeriodSelector'
import { StatusStatsCards } from './StatusStatsCards'
import { StatusStayedNote } from './StatusStayedNote'
import { StatusPagination } from './StatusPagination'
import { StatusCsvButton } from './StatusCsvButton'
import { formatCount, formatDate, formatMoney, formatMoneyList, periodLabel } from '../utils/statusFormat'
import type { DateRange } from '../utils/statusPeriod'

interface StatusUserDetailProps {
  userId: number
  period: string
  /** The applied range when period is "custom" */
  range?: DateRange | null
  onPeriodChange: (period: string) => void
  onRangeChange: (range: DateRange) => void
}

const TEXT = {
  loading: 'Loading user...',
  phone: 'Phone',
  email: 'Email',
  joined: 'Joined',
  hotelsVisited: 'Hotels visited',
  hotelsTitle: 'Hotels',
  noHotels: 'No hotels in this period.',
  historyTitle: 'Booking history',
  noHistory: 'No bookings in this period.',
  hotelHeaders: ['Hotel', 'Location', 'Bookings', 'Stayed', 'Nights', 'Guests', 'Spent'],
  historyHeaders: ['Reference', 'Hotel', 'Check-in', 'Check-out', 'Nights', 'Rooms', 'Guests', 'Status', 'Total', 'Paid', 'Refunded'],
  charged: 'charged',
}

const NUMERIC_HOTEL_COLUMNS = new Set([2, 3, 4, 5, 6])
const NUMERIC_HISTORY_COLUMNS = new Set([4, 5, 6, 8, 9, 10])

const statusText = (status: string) => status.replace(/_/g, ' ')

function periodParams(period: string, range: DateRange | null | undefined): StatusPeriodParams {
  return period === 'custom' && range ? { period, from: range.from, to: range.to } : { period }
}

/** Admin Status > Users > one guest: totals, hotels visited, per-hotel table and booking history */
export function StatusUserDetail({ userId, period, range, onPeriodChange, onRangeChange }: StatusUserDetailProps) {
  const [page, setPage] = useState({ key: `${period}|${range?.from}|${range?.to}`, value: 1 })
  const [data, setData] = useState<UserDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // A new period starts the history again from the first page
  const periodKey = `${period}|${range?.from}|${range?.to}`
  const historyPage = page.key === periodKey ? page.value : 1

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)
    statusAdapter.getUserDetail(userId, { ...periodParams(period, range), page: historyPage }).then(response => {
      if (cancelled) return
      if (response.data) setData(response.data)
      setError(response.error)
      setLoading(false)
    })
    return () => { cancelled = true }
  }, [userId, period, range, historyPage])

  if (!data && !error) return <div className="loading-state" role="status" aria-live="polite">{TEXT.loading}</div>

  return (
    <section className="status-user" aria-busy={loading}>
      {data && (
        <>
          <div className="admin-view-header">
            <h2 className="admin-view-title">{data.user.full_name || data.user.email}</h2>
          </div>
          <dl className="status-hotel-info">
            <div><dt>{TEXT.email}</dt><dd>{data.user.email}</dd></div>
            <div><dt>{TEXT.phone}</dt><dd>{data.user.phone || '—'}</dd></div>
            <div><dt>{TEXT.joined}</dt><dd>{formatDate(data.user.date_joined)}</dd></div>
          </dl>
        </>
      )}

      <div className="status-controls">
        <StatusPeriodSelector value={period} range={range} onChange={onPeriodChange} onRangeChange={onRangeChange} />
        <StatusCsvButton onExport={() => statusAdapter.exportUserHistory(userId, periodParams(period, range))} />
      </div>

      {error ? (
        <div className="alert alert-error" role="alert">{error}</div>
      ) : data && (
        <>
          <StatusStatsCards totals={data.totals} caption={periodLabel(data.period, data.period_range)} />
          <StatusStayedNote periodRange={data.period_range} />

          <dl className="status-hotel-info">
            <div><dt>{TEXT.hotelsVisited}</dt><dd>{formatCount(data.hotels_visited)}</dd></div>
          </dl>

          <h3 className="status-chart-title">{TEXT.hotelsTitle}</h3>
          {data.hotels.length === 0 ? (
            <div className="empty-state"><p>{TEXT.noHotels}</p></div>
          ) : (
            <div className="customers-table-container">
              <table className="customers-table status-table" aria-label={TEXT.hotelsTitle}>
                <thead>
                  <tr>
                    {TEXT.hotelHeaders.map((header, index) => (
                      <th key={header} scope="col" className={NUMERIC_HOTEL_COLUMNS.has(index) ? 'status-cell--numeric' : undefined}>
                        {header}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {data.hotels.map(hotel => (
                    <tr key={hotel.id}>
                      <td>{hotel.name}</td>
                      <td>{hotel.city}, {hotel.country}</td>
                      <td className="status-cell--numeric">{formatCount(hotel.bookings)}</td>
                      <td className="status-cell--numeric">{formatCount(hotel.stayed)}</td>
                      <td className="status-cell--numeric">{formatCount(hotel.nights)}</td>
                      <td className="status-cell--numeric">{formatCount(hotel.guests)}</td>
                      <td className="status-cell--numeric">{formatMoneyList(hotel.spent)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          <h3 className="status-chart-title">{TEXT.historyTitle}</h3>
          {data.history.results.length === 0 ? (
            <div className="empty-state"><p>{TEXT.noHistory}</p></div>
          ) : (
            <>
              <div className="customers-table-container">
                <table className="customers-table status-table" aria-label={TEXT.historyTitle}>
                  <thead>
                    <tr>
                      {TEXT.historyHeaders.map((header, index) => (
                        <th key={header} scope="col" className={NUMERIC_HISTORY_COLUMNS.has(index) ? 'status-cell--numeric' : undefined}>
                          {header}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {data.history.results.map(booking => (
                      <tr key={booking.id}>
                        <td>{booking.reference}</td>
                        <td>{booking.hotel.name}</td>
                        <td>{formatDate(booking.check_in)}</td>
                        <td>{formatDate(booking.check_out)}</td>
                        <td className="status-cell--numeric">{formatCount(booking.nights)}</td>
                        <td className="status-cell--numeric">{formatCount(booking.rooms)}</td>
                        <td className="status-cell--numeric">{formatCount(booking.guests)}</td>
                        <td>{statusText(booking.status)}</td>
                        <td className="status-cell--numeric">
                          {formatMoney({ currency: booking.currency, amount: booking.total_price })}
                          {booking.charge_amount && booking.charge_currency && booking.charge_currency !== booking.currency && (
                            <span className="status-card-caption">
                              {' '}{TEXT.charged} {formatMoney({ currency: booking.charge_currency, amount: booking.charge_amount })}
                            </span>
                          )}
                        </td>
                        <td className="status-cell--numeric">{formatMoneyList(booking.paid)}</td>
                        <td className="status-cell--numeric">{formatMoneyList(booking.refunded)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <StatusPagination
                page={historyPage} count={data.history.count} hasPrevious={Boolean(data.history.previous)}
                hasNext={Boolean(data.history.next)} onPage={value => setPage({ key: periodKey, value })}
              />
            </>
          )}
        </>
      )}
    </section>
  )
}
