import { useEffect, useId, useState } from 'react'
import { useI18n } from '../i18n/I18nContext'
import { statusAdapter } from '../adapters/statusAdapter'
import type { AdminOverview, StatusPeriodParams } from '../adapters/statusAdapter'
import { monthChange } from '../utils/statusChange'
import { formatCount, formatMoneyList, monthLabel, periodLabel } from '../utils/statusFormat'
import { regionPlace, placeLabel } from '../utils/statusPlaces'
import { StatusMetricCard } from './StatusMetricCard'
import { StatusYearCharts } from './StatusYearCharts'

interface AdminStatusOverviewProps {
  /** Period params of the page's period selector */
  params: StatusPeriodParams
}

const DASH = '—'
const percent = (value: string | null) => (value === null ? DASH : `${value}%`)

/** The whole platform at a glance: this month, key numbers of the period, busiest regions and room types, yearly charts. */
export function AdminStatusOverview({ params }: AdminStatusOverviewProps) {
  const i18n = useI18n()
  const { t, language } = i18n
  const id = useId()
  const [year, setYear] = useState<number | undefined>(undefined)
  const [data, setData] = useState<AdminOverview | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [attempt, setAttempt] = useState(0)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    statusAdapter.getAdminOverview({ ...params, year }).then(response => {
      if (cancelled) return
      if (response.data) setData(response.data)
      setError(response.error)
      setLoading(false)
    })
    return () => { cancelled = true }
  }, [params, year, attempt])

  if (error) {
    return (
      <div className="alert alert-error" role="alert">
        <p>{error}</p>
        <button type="button" className="btn btn-secondary btn-sm" onClick={() => setAttempt(n => n + 1)}>{t('common.tryAgain')}</button>
      </div>
    )
  }
  if (!data) return <div className="loading-state" role="status" aria-live="polite">{t('status.loading3')}</div>

  const { months, totals, insights } = data
  const revenue = monthChange(months.change_pct.revenue[0]?.pct ?? null, t)
  const guests = monthChange(months.change_pct.guests, t)
  const bookings = monthChange(months.change_pct.bookings, t)

  return (
    <div className="admin-status-overview" aria-busy={loading}>
      <section aria-labelledby={`${id}-month`}>
        <h3 id={`${id}-month`} className="status-chart-title">
          {t('ownerStatus.thisMonth', { month: monthLabel(months.current.month, i18n) })}
        </h3>
        <div className="status-cards">
          <StatusMetricCard label={t('status.revenue')} value={formatMoneyList(months.current.revenue)} caption={revenue.text} tone={revenue.tone} />
          <StatusMetricCard label={t('status.guests')} value={formatCount(months.current.guests)} caption={guests.text} tone={guests.tone} />
          <StatusMetricCard label={t('status.bookings')} value={formatCount(months.current.bookings)} caption={bookings.text} tone={bookings.tone} />
          <StatusMetricCard
            label={t('ownerStatus.next7')} value={formatCount(months.next_7_days.guests)}
            caption={t('ownerStatus.next7Hint', { bookings: months.next_7_days.bookings })}
          />
          <StatusMetricCard
            label={t('adminStatus.newGuests')} value={formatCount(data.new_users.current_month)}
            caption={t('adminStatus.newGuestsHint', { count: data.new_users.previous_month })}
          />
        </div>
      </section>

      <section aria-labelledby={`${id}-key`}>
        <h3 id={`${id}-key`} className="status-chart-title">
          {t('ownerStatus.keyNumbers', { period: periodLabel(data.period, data.period_range, i18n) })}
        </h3>
        <div className="status-cards">
          <StatusMetricCard label={t('status.stayed')} value={formatCount(totals.stayed)} caption={t('status.stayedHint')} />
          <StatusMetricCard label={t('status.revenue')} value={formatMoneyList(totals.revenue)} caption={t('status.revenueHint')} />
          <StatusMetricCard
            label={t('adminStatus.hotels')} value={formatCount(data.hotels.active)}
            caption={t('adminStatus.hotelsHint', { total: data.hotels.total })}
          />
          <StatusMetricCard label={t('status.insights.occupancy')} value={percent(insights.occupancy_rate)} caption={t('status.insights.occupancyHint')} />
          <StatusMetricCard
            label={t('status.insights.cancellationRate')} value={percent(insights.cancellation_rate)}
            caption={t('status.insights.cancellationRateHint')}
          />
          <StatusMetricCard label={t('adminStatus.noShowRate')} value={percent(data.no_show_rate)} caption={t('adminStatus.noShowRateHint')} />
          <StatusMetricCard
            label={t('ownerStatus.leadDays')}
            value={insights.average_lead_days === null ? DASH : t('ownerStatus.leadDaysValue', { value: insights.average_lead_days })}
            caption={t('ownerStatus.leadDaysHint')}
          />
          <StatusMetricCard label={t('ownerStatus.repeatGuests')} value={percent(insights.repeat_guest_pct)} caption={t('ownerStatus.repeatGuestsHint')} />
        </div>
      </section>

      <section aria-labelledby={`${id}-regions`}>
        <h3 id={`${id}-regions`} className="status-chart-title">{t('adminStatus.busiestRegions')}</h3>
        {data.top_regions.length === 0 ? (
          <div className="empty-state"><p>{t('adminStatus.empty')}</p></div>
        ) : (
          <div className="customers-table-container">
            <table className="customers-table status-table" aria-label={t('adminStatus.busiestRegions')}>
              <thead>
                <tr>
                  <th scope="col">{t('status.region')}</th>
                  <th scope="col" className="status-cell--numeric">{t('status.title')}</th>
                  <th scope="col" className="status-cell--numeric">{t('status.bookings')}</th>
                  <th scope="col" className="status-cell--numeric">{t('status.guests')}</th>
                </tr>
              </thead>
              <tbody>
                {data.top_regions.map(region => {
                  const place = regionPlace(region)
                  return (
                    <tr key={place.key}>
                      <td>{placeLabel(place, language, t('status.unspecified'))}</td>
                      <td className="status-cell--numeric">{formatCount(region.hotels)}</td>
                      <td className="status-cell--numeric">{formatCount(region.bookings)}</td>
                      <td className="status-cell--numeric">{formatCount(region.guests)}</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section aria-labelledby={`${id}-rooms`}>
        <h3 id={`${id}-rooms`} className="status-chart-title">{t('adminStatus.busiestRooms')}</h3>
        {data.top_room_types.length === 0 ? (
          <div className="empty-state"><p>{t('adminStatus.empty')}</p></div>
        ) : (
          <div className="customers-table-container">
            <table className="customers-table status-table" aria-label={t('adminStatus.busiestRooms')}>
              <thead>
                <tr>
                  <th scope="col">{t('ownerStatus.rooms.roomType')}</th>
                  <th scope="col">{t('crumb.property')}</th>
                  <th scope="col" className="status-cell--numeric">{t('status.bookings')}</th>
                  <th scope="col" className="status-cell--numeric">{t('status.revenue')}</th>
                </tr>
              </thead>
              <tbody>
                {data.top_room_types.map(row => (
                  <tr key={row.room_type_id}>
                    <td>{row.name}</td>
                    <td>{row.property.name}</td>
                    <td className="status-cell--numeric">{formatCount(row.bookings)}</td>
                    <td className="status-cell--numeric">{formatMoneyList(row.revenue)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <StatusYearCharts months={data.monthly} year={data.year} availableYears={data.available_years} onYearChange={setYear} />
    </div>
  )
}
