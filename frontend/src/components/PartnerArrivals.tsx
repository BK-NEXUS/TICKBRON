import { useI18n } from '../i18n/I18nContext'
import { textKeys, useTexts } from '../i18n/I18nContext'
import { useEffect, useState } from 'react'
import { SegmentedControl } from './SegmentedControl'
import { statusAdapter, ArrivalsDay, PartnerArrivalsPage } from '../adapters/statusAdapter'
import { partnerAdapter } from '../adapters/partnerAdapter'
import { ARRIVAL_GRACE_HOURS, formatArrivalTime } from '../utils/arrival'
import { StatusPagination } from './StatusPagination'
import { formatCount, formatDate } from '../utils/statusFormat'
import { phoneLink } from '../utils/contactLinks'

interface PartnerArrivalsProps {
  /** Limit to one of the owner's hotels */
  propertyId?: number
}

const ARRIVALS_PAGE_SIZE = 50

const TEXT_KEYS = textKeys({
  title: 'status.title2',
  today: 'status.today',
  tomorrow: 'status.tomorrow',
  loading: 'status.loading',
  emptyToday: 'status.noArrivalsToday',
  emptyTomorrow: 'status.noArrivalsTomorrow',
  headers: { reference: 'status.reference', guest: 'status.guest', hotel: 'status.hotel', rooms: 'status.rooms', roomCount: 'searchForm.rooms', nights: 'status.nights',
    guests: 'searchForm.guests', checkIn: 'searchForm.checkIn', checkOut: 'searchForm.checkOut', phone: 'profile.contact.phone', requests: 'status.requests',
    arrival: 'arrivals.arrivalTime', arrived: 'arrivals.arrivedHeader' },
  arrived: 'arrivals.arrived',

})

function PhoneCell({ phone }: { phone: string }) {
  const href = phoneLink(phone)
  return href ? <a href={href}>{phone}</a> : <>{phone}</>
}

/** Owner Status: confirmed bookings checking in today or tomorrow. The whole phone number, as a call link, so a late guest can be called. */
export function PartnerArrivals({ propertyId }: PartnerArrivalsProps) {
  const i18n = useI18n()
  const TEXT = useTexts(TEXT_KEYS)
  const days: { value: ArrivalsDay; label: string }[] = [
    { value: 'today', label: TEXT.today },
    { value: 'tomorrow', label: TEXT.tomorrow },
  ]
  const [day, setDay] = useState<ArrivalsDay>('today')
  const [pageState, setPageState] = useState({ day: 'today' as ArrivalsDay, page: 1 })
  const [data, setData] = useState<PartnerArrivalsPage | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  // Bookings the owner marked as arrived in this session (the list is not reloaded), and the one being sent
  const [markedIds, setMarkedIds] = useState<number[]>([])
  const [markingId, setMarkingId] = useState<number | null>(null)
  const [markError, setMarkError] = useState<string | null>(null)

  const markArrived = async (id: number) => {
    setMarkingId(id)
    setMarkError(null)
    const response = await partnerAdapter.markGuestArrived(id)
    setMarkingId(null)
    if (response.error) setMarkError(response.error)
    else setMarkedIds(prev => [...prev, id])
  }

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
        <SegmentedControl<ArrivalsDay> aria-label={TEXT.title} options={days} value={day} onChange={setDay} />
        {data && <span className="status-card-caption">{formatDate(data.date, i18n)}</span>}
      </div>
      <p className="status-card-caption">{i18n.t('arrivals.rule', { hours: ARRIVAL_GRACE_HOURS })}</p>
      {markError && <div className="alert alert-error" role="alert">{markError}</div>}

      {error ? (
        <div className="alert alert-error" role="alert">{error}</div>
      ) : !data ? (
        <div className="loading-state" role="status" aria-live="polite">{TEXT.loading}</div>
      ) : rows.length === 0 ? (
        <div className="empty-state"><p>{day === 'today' ? TEXT.emptyToday : TEXT.emptyTomorrow}</p></div>
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
                  <th scope="col">{TEXT.headers.arrival}</th>
                  <th scope="col">{TEXT.headers.arrived}</th>
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
                    <td>{formatDate(arrival.check_in, i18n)}</td>
                    <td>{formatDate(arrival.check_out, i18n)}</td>
                    <td><PhoneCell phone={arrival.phone} /></td>
                    <td>{arrival.expected_arrival_time ? formatArrivalTime(arrival.expected_arrival_time) : '—'}</td>
                    <td>
                      {arrival.arrived_at || markedIds.includes(arrival.id) ? (
                        <span className="status-badge status-badge--active">{TEXT.arrived}</span>
                      ) : day === 'today' ? (
                        <button
                          type="button"
                          className="btn btn-secondary"
                          disabled={markingId === arrival.id}
                          aria-label={i18n.t('arrivals.markArrivedFor', { reference: arrival.reference })}
                          onClick={() => void markArrived(arrival.id)}
                        >
                          {i18n.t('arrivals.markArrived')}
                        </button>
                      ) : '—'}
                    </td>
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
