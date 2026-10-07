import { useEffect, useState } from 'react'
import { statusAdapter, ArrivalsDay, PartnerArrivalsPage } from '../adapters/statusAdapter'
import { StatusPagination } from './StatusPagination'
import { formatCount, formatDate } from '../utils/statusFormat'

interface PartnerArrivalsProps {
  /** Limit to one of the owner's hotels */
  propertyId?: number
}

const ARRIVALS_PAGE_SIZE = 50

const TEXT = {
  title: 'Arrivals',
  today: 'Today',
  tomorrow: 'Tomorrow',
  loading: 'Loading arrivals...',
  empty: (day: ArrivalsDay) => `No arrivals ${day}.`,
  headers: { reference: 'Reference', guest: 'Guest', hotel: 'Hotel', rooms: 'Room types', roomCount: 'Rooms', nights: 'Nights',
    guests: 'Guests', checkIn: 'Check-in', checkOut: 'Check-out', phone: 'Phone', requests: 'Special requests' },
}

const DAYS: { value: ArrivalsDay; label: string }[] = [
  { value: 'today', label: TEXT.today },
  { value: 'tomorrow', label: TEXT.tomorrow },
]

/** Owner Status: confirmed bookings checking in today or tomorrow. The phone is only its last 4 digits. */
export function PartnerArrivals({ propertyId }: PartnerArrivalsProps) {
  const [day, setDay] = useState<ArrivalsDay>('today')
  const [pageState, setPageState] = useState({ day: 'today' as ArrivalsDay, page: 1 })
  const [data, setData] = useState<PartnerArrivalsPage | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Another day starts from its first page
  const page = pageState.day === day ? pageState.page : 1

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)
    statusAdapter.getPartnerArrivals({ day, ...(propertyId === undefined ? {} : { property: propertyId }), page }).then(response => {
      if (cancelled) return
      setData(response.data)
      setError(response.error)
      setLoading(false)
    })
    return () => { cancelled = true }
  }, [day, propertyId, page])

  const rows = data?.results ?? []

  return (
    <section className="partner-arrivals" aria-busy={loading}>
      <h3 className="status-chart-title">{TEXT.title}</h3>
      <div className="status-controls">
        <div className="status-field" role="group" aria-label={TEXT.title}>
          {DAYS.map(option => (
            <button
              key={option.value}
              type="button"
              className={`btn ${day === option.value ? 'btn-primary' : 'btn-secondary'}`}
              aria-pressed={day === option.value}
              onClick={() => setDay(option.value)}
            >
              {option.label}
            </button>
          ))}
        </div>
        {data && <span className="status-card-caption">{formatDate(data.date)}</span>}
      </div>

      {error ? (
        <div className="alert alert-error" role="alert">{error}</div>
      ) : !data ? (
        <div className="loading-state" role="status" aria-live="polite">{TEXT.loading}</div>
      ) : rows.length === 0 ? (
        <div className="empty-state"><p>{TEXT.empty(day)}</p></div>
      ) : (
        <>
          <div className="customers-table-container">
            <table className="customers-table status-table" aria-label={TEXT.title}>
              <thead>
                <tr>
                  <th scope="col">{TEXT.headers.reference}</th>
                  <th scope="col">{TEXT.headers.guest}</th>
                  {propertyId === undefined && <th scope="col">{TEXT.headers.hotel}</th>}
                  <th scope="col">{TEXT.headers.rooms}</th>
                  <th scope="col" className="status-cell--numeric">{TEXT.headers.roomCount}</th>
                  <th scope="col" className="status-cell--numeric">{TEXT.headers.nights}</th>
                  <th scope="col" className="status-cell--numeric">{TEXT.headers.guests}</th>
                  <th scope="col">{TEXT.headers.checkIn}</th>
                  <th scope="col">{TEXT.headers.checkOut}</th>
                  <th scope="col">{TEXT.headers.phone}</th>
                  <th scope="col">{TEXT.headers.requests}</th>
                </tr>
              </thead>
              <tbody>
                {rows.map(arrival => (
                  <tr key={arrival.id}>
                    <td>{arrival.reference}</td>
                    <td>{arrival.guest_name}</td>
                    {propertyId === undefined && <td>{arrival.property.name}</td>}
                    <td>{arrival.room_types.join(', ')}</td>
                    <td className="status-cell--numeric">{formatCount(arrival.rooms)}</td>
                    <td className="status-cell--numeric">{formatCount(arrival.nights)}</td>
                    <td className="status-cell--numeric">{formatCount(arrival.guests)}</td>
                    <td>{formatDate(arrival.check_in)}</td>
                    <td>{formatDate(arrival.check_out)}</td>
                    <td>{`•••• ${arrival.phone_last4}`}</td>
                    <td>{arrival.special_requests || '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <StatusPagination
            page={page} count={data.count} pageSize={ARRIVALS_PAGE_SIZE} hasPrevious={Boolean(data.previous)}
            hasNext={Boolean(data.next)} onPage={value => setPageState({ day, page: value })}
          />
        </>
      )}
    </section>
  )
}
