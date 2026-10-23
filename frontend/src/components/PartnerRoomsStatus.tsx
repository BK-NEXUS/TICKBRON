import { useEffect, useId, useState } from 'react'
import { useI18n } from '../i18n/I18nContext'
import { statusAdapter } from '../adapters/statusAdapter'
import type { PartnerRoomsStatus, StatusPeriodParams } from '../adapters/statusAdapter'
import { formatCount, formatMoneyList } from '../utils/statusFormat'

interface PartnerRoomsStatusProps {
  params: StatusPeriodParams
  /** The owner's hotels, for the hotel filter */
  hotels: { id: number; name: string }[]
}

const DASH = '—'
const percent = (value: string | null) => (value === null ? DASH : `${value}%`)

/** Which room types are booked most: counted bookings, share, room nights, occupancy and revenue per room type. */
export function PartnerRoomsStatus({ params, hotels }: PartnerRoomsStatusProps) {
  const { t } = useI18n()
  const id = useId()
  const [hotelId, setHotelId] = useState<number | undefined>(undefined)
  const [data, setData] = useState<PartnerRoomsStatus | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [attempt, setAttempt] = useState(0)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    statusAdapter.getPartnerRooms({ ...params, property: hotelId }).then(response => {
      if (cancelled) return
      if (response.data) setData(response.data)
      setError(response.error)
      setLoading(false)
    })
    return () => { cancelled = true }
  }, [params, hotelId, attempt])

  const rows = data?.rows ?? []
  const busiest = rows.length > 0 && rows[0].bookings > 0 ? rows[0].room_type_id : null

  return (
    <div className="partner-rooms-status" aria-busy={loading}>
      <p className="status-note">{t('ownerStatus.rooms.subtitle')}</p>
      {hotels.length > 1 && (
        <div className="status-controls">
          <div className="status-field">
            <label htmlFor={`${id}-hotel`}>{t('ownerStatus.rooms.hotel')}</label>
            <select id={`${id}-hotel`} value={hotelId ?? ''} onChange={e => setHotelId(e.target.value ? Number(e.target.value) : undefined)}>
              <option value="">{t('ownerStatus.rooms.allHotels')}</option>
              {hotels.map(hotel => <option key={hotel.id} value={hotel.id}>{hotel.name}</option>)}
            </select>
          </div>
        </div>
      )}

      {error ? (
        <div className="alert alert-error" role="alert">
          <p>{error}</p>
          <button type="button" className="btn btn-secondary btn-sm" onClick={() => setAttempt(n => n + 1)}>{t('common.tryAgain')}</button>
        </div>
      ) : !data ? (
        <div className="loading-state" role="status" aria-live="polite">{t('status.loading3')}</div>
      ) : rows.length === 0 ? (
        <div className="empty-state"><p>{t('ownerStatus.rooms.empty')}</p></div>
      ) : (
        <div className="customers-table-container">
          <table className="customers-table status-table" aria-label={t('ownerStatus.rooms.title')}>
            <thead>
              <tr>
                <th scope="col">{t('ownerStatus.rooms.roomType')}</th>
                <th scope="col">{t('crumb.property')}</th>
                <th scope="col" className="status-cell--numeric">{t('status.bookings')}</th>
                <th scope="col">{t('ownerStatus.rooms.share')}</th>
                <th scope="col" className="status-cell--numeric">{t('status.roomNights')}</th>
                <th scope="col" className="status-cell--numeric">{t('status.insights.occupancy')}</th>
                <th scope="col" className="status-cell--numeric">{t('status.revenue')}</th>
              </tr>
            </thead>
            <tbody>
              {rows.map(row => (
                <tr key={row.room_type_id}>
                  <td>
                    {row.name}
                    <span className="status-hint"> · {t('ownerStatus.rooms.roomCount', { count: row.total_rooms })}</span>
                    {row.room_type_id === busiest && <span className="status-badge">{t('ownerStatus.rooms.busiest')}</span>}
                  </td>
                  <td>{row.property.name}</td>
                  <td className="status-cell--numeric">{formatCount(row.bookings)}</td>
                  <td>
                    <span className="status-share" role="img" aria-label={percent(row.share_pct)}>
                      <span className="status-share-bar" style={{ width: `${Number(row.share_pct ?? 0)}%` }} />
                    </span>
                    <span className="status-share-text">{percent(row.share_pct)}</span>
                  </td>
                  <td className="status-cell--numeric">{formatCount(row.room_nights)}</td>
                  <td className="status-cell--numeric">{percent(row.occupancy_rate)}</td>
                  <td className="status-cell--numeric">{formatMoneyList(row.revenue)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
