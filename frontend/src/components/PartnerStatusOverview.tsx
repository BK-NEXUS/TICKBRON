import { useId } from 'react'
import { useI18n } from '../i18n/I18nContext'
import type { MonthComparison, PartnerStatus } from '../adapters/statusAdapter'
import { monthChange } from '../utils/statusChange'
import { formatCount, formatMoneyList, monthLabel, periodLabel } from '../utils/statusFormat'
import { StatusMetricCard } from './StatusMetricCard'
import { StatusYearCharts } from './StatusYearCharts'

interface PartnerStatusOverviewProps {
  data: PartnerStatus
  onYearChange: (year: number) => void
  onOpenHotel: (hotelId: number) => void
}

const DASH = '—'
const percent = (value: string | null) => (value === null ? DASH : `${value}%`)

/** This month against last month, the next 7 days, a few key numbers of the chosen period, the yearly charts and the hotels. */
export function PartnerStatusOverview({ data, onYearChange, onOpenHotel }: PartnerStatusOverviewProps) {
  const i18n = useI18n()
  const { t } = i18n
  const id = useId()
  const { months, totals, insights } = data
  const revenueChange = (months: MonthComparison) => months.change_pct.revenue[0]?.pct ?? null
  const revenue = monthChange(revenueChange(months), t)
  const guests = monthChange(months.change_pct.guests, t)
  const bookings = monthChange(months.change_pct.bookings, t)

  const caption = periodLabel(data.period, data.period_range, i18n)

  return (
    <>
      <section aria-labelledby={`${id}-month`}>
        <h3 id={`${id}-month`} className="status-chart-title">
          {t('ownerStatus.thisMonth', { month: monthLabel(months.current.month, i18n) })}
        </h3>
        <div className="status-cards">
          <StatusMetricCard label={t('status.revenue')} value={formatMoneyList(months.current.revenue)} caption={revenue.text} tone={revenue.tone} />
          <StatusMetricCard label={t('status.guestsLabel')} value={formatCount(months.current.guests)} caption={guests.text} tone={guests.tone} />
          <StatusMetricCard label={t('status.bookings')} value={formatCount(months.current.bookings)} caption={bookings.text} tone={bookings.tone} />
          <StatusMetricCard
            label={t('ownerStatus.next7')}
            value={formatCount(months.next_7_days.guests)}
            caption={t('ownerStatus.next7Hint', { bookings: months.next_7_days.bookings })}
          />
        </div>
      </section>

      <section aria-labelledby={`${id}-key`}>
        <h3 id={`${id}-key`} className="status-chart-title">{t('ownerStatus.keyNumbers', { period: caption })}</h3>
        <div className="status-cards">
          <StatusMetricCard label={t('status.stayed')} value={formatCount(totals.stayed)} caption={t('status.stayedHint')} />
          <StatusMetricCard label={t('status.revenue')} value={formatMoneyList(totals.revenue)} caption={t('status.revenueHint')} />
          <StatusMetricCard label={t('status.insights.occupancy')} value={percent(insights.occupancy_rate)} caption={t('status.insights.occupancyHint')} />
          <StatusMetricCard label={t('status.insights.cancellationRate')} value={percent(insights.cancellation_rate)} caption={t('status.insights.cancellationRateHint')} />
          <StatusMetricCard
            label={t('ownerStatus.leadDays')}
            value={insights.average_lead_days === null ? DASH : t('ownerStatus.leadDaysValue', { value: insights.average_lead_days })}
            caption={t('ownerStatus.leadDaysHint')}
          />
          <StatusMetricCard label={t('ownerStatus.repeatGuests')} value={percent(insights.repeat_guest_pct)} caption={t('ownerStatus.repeatGuestsHint')} />
        </div>
      </section>

      <StatusYearCharts months={data.monthly} year={data.year} availableYears={data.available_years} onYearChange={onYearChange} />

      <section aria-labelledby={`${id}-hotels`}>
        <h3 id={`${id}-hotels`} className="status-chart-title">{t('status.properties')}</h3>
        {data.properties.length === 0 ? (
          <div className="empty-state"><p>{t('status.noProperties')}</p></div>
        ) : (
          <div className="customers-table-container">
            <table className="customers-table status-table" aria-label={t('status.properties')}>
              <thead>
                <tr>
                  <th scope="col">{t('crumb.property')}</th>
                  <th scope="col">{t('property.location')}</th>
                  <th scope="col" className="status-cell--numeric">{t('status.counted')}</th>
                  <th scope="col" className="status-cell--numeric">{t('status.stayed')}</th>
                  <th scope="col" className="status-cell--numeric">{t('searchForm.guests')}</th>
                  <th scope="col" className="status-cell--numeric">{t('status.revenue')}</th>
                </tr>
              </thead>
              <tbody>
                {data.properties.map(property => (
                  <tr key={property.id}>
                    <td>
                      <button type="button" className="status-row-link" onClick={() => onOpenHotel(property.id)}>{property.name}</button>
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
      </section>
    </>
  )
}
