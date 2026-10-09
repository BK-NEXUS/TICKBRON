import { textKeys, useTexts } from '../i18n/I18nContext'
import { useEffect, useState } from 'react'
import { statusAdapter, PartnerHotelStatus as HotelStatus } from '../adapters/statusAdapter'
import { useStatusPeriod } from '../hooks/useStatusPeriod'
import { StatusPeriodSelector } from './StatusPeriodSelector'
import { StatusReport } from './StatusReport'
import { PartnerArrivals } from './PartnerArrivals'

interface PartnerHotelStatusProps {
  hotelId: number
  onBack: () => void
}

const NOT_FOUND = 404

const TEXT_KEYS = textKeys({
  loading: 'status.loading2',
  back: 'status.back',
  notFoundTitle: 'status.notFoundTitle',
  notFoundText: 'status.notFoundText',

})

/** Partner panel > Status > one of the owner's own hotels. Another owner's hotel is a "not found" page. */
export function PartnerHotelStatus({ hotelId, onBack }: PartnerHotelStatusProps) {
  const TEXT = useTexts(TEXT_KEYS)
  const { params, period, range, granularity, setPeriod, setRange, setGranularity } = useStatusPeriod()
  const [data, setData] = useState<HotelStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [notFound, setNotFound] = useState(false)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)
    statusAdapter.getPartnerHotel(hotelId, params).then(response => {
      if (cancelled) return
      if (response.data) setData(response.data)
      setNotFound(response.status === NOT_FOUND)
      setError(response.error)
      setLoading(false)
    })
    return () => { cancelled = true }
  }, [hotelId, params])

  const backButton = <button type="button" className="btn btn-secondary" onClick={onBack}>{TEXT.back}</button>

  if (notFound) {
    return (
      <div className="empty-state">
        <h2 className="empty-state-title">{TEXT.notFoundTitle}</h2>
        <p className="empty-state-message">{TEXT.notFoundText}</p>
        {backButton}
      </div>
    )
  }
  if (!data && !error) return <div className="loading-state" role="status" aria-live="polite">{TEXT.loading}</div>

  return (
    <section className="status-hotel" aria-busy={loading}>
      {backButton}
      {data && (
        <div className="admin-view-header">
          <h2 className="admin-view-title">{data.hotel.name}</h2>
          <p className="admin-view-subtitle">{data.hotel.address}, {data.hotel.city}</p>
        </div>
      )}

      <div className="status-controls">
        <StatusPeriodSelector value={period} range={range} onChange={setPeriod} onRangeChange={setRange} />
      </div>

      {error ? (
        <div className="alert alert-error" role="alert">{error}</div>
      ) : data && (
        <>
          <StatusReport
            period={data.period} periodRange={data.period_range} totals={data.totals} series={data.series}
            granularity={granularity} onGranularityChange={setGranularity} reconciliation={data.reconciliation}
          />
          <PartnerArrivals propertyId={data.hotel.id} />
        </>
      )}
    </section>
  )
}
