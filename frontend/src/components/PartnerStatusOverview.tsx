import { useId, useState } from 'react'
import { useI18n } from '../i18n/I18nContext'
import type { MonthComparison, PartnerStatus } from '../adapters/statusAdapter'
import { monthChange } from '../utils/statusChange'
import { chartCurrencies, formatCount, formatMoneyList, monthLabel, periodLabel } from '../utils/statusFormat'
import { StatusMonthlyChart } from './StatusMonthlyChart'

interface PartnerStatusOverviewProps {
  data: PartnerStatus
  onYearChange: (year: number) => void
  onOpenHotel: (hotelId: number) => void
}

interface CardProps {
  label: string
  value: string
  caption: string
  tone?: 'up' | 'down' | 'same' | 'none'
}

function Card({ label, value, caption, tone }: CardProps) {
  return (
    <div className="status-card">
      <span className="status-card-label">{label}</span>
      <span className="status-card-value">{value}</span>
      <span className={`status-card-caption${tone ? ` status-change--${tone}` : ''}`}>{caption}</span>
    </div>
  )
}

const DASH = '—'
const percent = (value: string | null) => (value === null ? DASH : `${value}%`)

/** This month against last month, the next 7 days, a few key numbers of the chosen period, the yearly charts and the hotels. */
export function PartnerStatusOverview({ data, onYearChange, onOpenHotel }: PartnerStatusOverviewProps) {
  const i18n = useI18n()
  const { t } = i18n
  const id = useId()
  const [currency, setCurrency] = useState<string | null>(null)
  const { months, totals, insights } = data
  const revenueChange = (months: MonthComparison) => months.change_pct.revenue[0]?.pct ?? null
  const revenue = monthChange(revenueChange(months), t)
  const guests = monthChange(months.change_pct.guests, t)
  const bookings = monthChange(months.change_pct.bookings, t)

  const years = data.available_years.includes(data.year) ? data.available_years : [...data.available_years, data.year].sort()
  const currencies = chartCurrencies(data.monthly)
  const chartCurrency = currency && currencies.includes(currency) ? currency : currencies[0]
  const caption = periodLabel(data.period, data.period_range, i18n)

  return (
    <>
      <section aria-labelledby={`${id}-month`}>
        <h3 id={`${id}-month`} className="status-chart-title">
          {t('ownerStatus.thisMonth', { month: monthLabel(months.current.month, i18n) })}
        </h3>
        <div className="status-cards">
          <Card label={t('status.revenue')} value={formatMoneyList(months.current.revenue)} caption={revenue.text} tone={revenue.tone} />
          <Card label={t('status.guestsLabel')} value={formatCount(months.current.guests)} caption={guests.text} tone={guests.tone} />
          <Card label={t('status.bookings')} value={formatCount(months.current.bookings)} caption={bookings.text} tone={bookings.tone} />
          <Card
            label={t('ownerStatus.next7')}
            value={formatCount(months.next_7_days.guests)}
            caption={t('ownerStatus.next7Hint', { bookings: months.next_7_days.bookings })}
          />
        </div>
      </section>

      <section aria-labelledby={`${id}-key`}>
        <h3 id={`${id}-key`} className="status-chart-title">{t('ownerStatus.keyNumbers', { period: caption })}</h3>
        <div className="status-cards">
          <Card label={t('status.stayed')} value={formatCount(totals.stayed)} caption={t('status.stayedHint')} />
          <Card label={t('status.revenue')} value={formatMoneyList(totals.revenue)} caption={t('status.revenueHint')} />
          <Card label={t('status.insights.occupancy')} value={percent(insights.occupancy_rate)} caption={t('status.insights.occupancyHint')} />
          <Card label={t('status.insights.cancellationRate')} value={percent(insights.cancellation_rate)} caption={t('status.insights.cancellationRateHint')} />
          <Card
            label={t('ownerStatus.leadDays')}
            value={insights.average_lead_days === null ? DASH : t('ownerStatus.leadDaysValue', { value: insights.average_lead_days })}
            caption={t('ownerStatus.leadDaysHint')}
          />
          <Card label={t('ownerStatus.repeatGuests')} value={percent(insights.repeat_guest_pct)} caption={t('ownerStatus.repeatGuestsHint')} />
        </div>
      </section>

      <section aria-labelledby={`${id}-year`}>
        <h3 id={`${id}-year`} className="status-chart-title">{t('status.yearTitle')}</h3>
        <div className="status-controls">
          <div className="status-field">
            <label htmlFor={`${id}-year-select`}>{t('status.chartYear')}</label>
            <select id={`${id}-year-select`} value={data.year} onChange={e => onYearChange(Number(e.target.value))}>
              {years.map(y => <option key={y} value={y}>{y}</option>)}
            </select>
          </div>
          {currencies.length > 1 && (
            <div className="status-field">
              <label htmlFor={`${id}-currency`}>{t('status.chartCurrency')}</label>
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
      </section>

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
