import type { MessageKey } from '../i18n/messages/en'
import { useI18n } from '../i18n/I18nContext'
import { useState } from 'react'
import { useNavigate } from 'react-router'
import { statusAdapter, StatusCountry, StatusHotel, StatusRegion, StatusUser } from '../adapters/statusAdapter'
import { Crumb, usePageTrail } from './Breadcrumbs'
import { StatusRankedTable, StatusColumn } from './StatusRankedTable'
import { StatusHotelDetail } from './StatusHotelDetail'
import { AdminStatusHotels } from './AdminStatusHotels'
import { StatusUserDetail } from './StatusUserDetail'
import { AdminStatusOverview } from './AdminStatusOverview'
import { StatusPeriodSelector } from './StatusPeriodSelector'
import { useStatusPeriod } from '../hooks/useStatusPeriod'
import { formatCount, formatDate, formatMoneyList } from '../utils/statusFormat'
import { countryPlace, placeLabel, regionPlace, type StatusPlace } from '../utils/statusPlaces'

type Level =
  | { kind: 'home' }
  | { kind: 'countries' }
  | { kind: 'regions'; country: StatusPlace }
  | { kind: 'hotels'; country: StatusPlace; region: StatusPlace }
  | { kind: 'hotel'; country: StatusPlace; region: StatusPlace; hotelId: number; hotelName: string }
  | { kind: 'users' }
  | { kind: 'allHotels' }
  | { kind: 'allHotel'; hotelId: number; hotelName: string }
  | { kind: 'user'; userId: number; name: string }

interface AdminStatusSectionProps {
  /** Leave the Status section (the "Admin Dashboard" breadcrumb, or Back from the tiles) */
  onExit: () => void
}

type Metrics = { bookings: number; guests: number; revenue: { currency: string; amount: string }[] }

function metricColumns<T extends Metrics>(t: (key: MessageKey) => string): StatusColumn<T>[] {
  return [
    { header: t('status.bookings'), numeric: true, render: row => formatCount(row.bookings) },
    { header: t('status.guests'), numeric: true, render: row => formatCount(row.guests) },
    { header: t('status.revenue'), numeric: true, render: row => formatMoneyList(row.revenue) },
  ]
}

/**
 * Admin panel > Status: Countries > Regions > Hotels > Hotel detail, and Users (guests ranking).
 * Numbers count confirmed and completed bookings, by check-in date; revenue per currency.
 */
export function AdminStatusSection({ onExit }: AdminStatusSectionProps) {
  const i18n = useI18n()
  const { t, language } = i18n
  const label = (place: StatusPlace) => placeLabel(place, language, t('status.unspecified'))
  const [level, setLevel] = useState<Level>({ kind: 'home' })
  const { params, period, range, setPeriod, setRange } = useStatusPeriod()
  const navigate = useNavigate()
  // Every list and detail takes the period and the custom range together
  const periodProps = { period, range, onPeriodChange: setPeriod, onRangeChange: setRange }

  const goHome = () => setLevel({ kind: 'home' })
  const goCountries = () => setLevel({ kind: 'countries' })
  const goRegions = (country: StatusPlace) => setLevel({ kind: 'regions', country })
  const goHotels = (country: StatusPlace, region: StatusPlace) => setLevel({ kind: 'hotels', country, region })

  // Home › Admin Dashboard › Status › Countries › Uzbekistan › Tashkent › Hotel (each level clickable, Back steps up)
  const trail: Crumb[] = [{ label: t('header.adminDashboard'), onClick: onExit }]
  trail.push(level.kind === 'home' ? { label: t('partner.status') } : { label: t('partner.status'), onClick: goHome })
  const goUsers = () => setLevel({ kind: 'users' })
  const goAllHotels = () => setLevel({ kind: 'allHotels' })
  if (level.kind === 'users') trail.push({ label: t('status.users') })
  if (level.kind === 'user') trail.push({ label: t('status.users'), onClick: goUsers }, { label: level.name })
  if (level.kind === 'allHotels') trail.push({ label: t('status.title') })
  if (level.kind === 'allHotel') trail.push({ label: t('status.title'), onClick: goAllHotels }, { label: level.hotelName })
  if (level.kind === 'countries' || level.kind === 'regions' || level.kind === 'hotels' || level.kind === 'hotel') {
    trail.push(level.kind === 'countries' ? { label: t('home.stat.countries') } : { label: t('home.stat.countries'), onClick: goCountries })
  }
  if (level.kind === 'regions' || level.kind === 'hotels' || level.kind === 'hotel') {
    const { country } = level
    trail.push(level.kind === 'regions' ? { label: label(country) } : { label: label(country), onClick: () => goRegions(country) })
  }
  if (level.kind === 'hotels' || level.kind === 'hotel') {
    const { country, region } = level
    trail.push(level.kind === 'hotels' ? { label: label(region) } : { label: label(region), onClick: () => goHotels(country, region) })
  }
  if (level.kind === 'hotel') trail.push({ label: level.hotelName })
  usePageTrail(trail)

  if (level.kind === 'home') {
    return (
      <div className="admin-status">
        <div className="admin-view-header">
          <h2 className="admin-view-title">{t('partner.status')}</h2>
          <p className="admin-view-subtitle">
            {t('status.bookingsGuestsAndRevenue')}
          </p>
        </div>
        <div className="status-controls">
          <StatusPeriodSelector value={period} range={range} onChange={setPeriod} onRangeChange={setRange} />
        </div>
        <AdminStatusOverview params={params} />
        <h3 className="status-chart-title">{t('adminStatus.browse')}</h3>
        <div className="status-tiles">
          <button type="button" className="status-tile" onClick={goCountries}>
            <span className="status-tile-title">{t('home.stat.countries')}</span>
            <span className="status-tile-text">{t('status.byCountryRegionAnd')}</span>
          </button>
          <button type="button" className="status-tile" onClick={goAllHotels}>
            <span className="status-tile-title">{t('status.title')}</span>
            <span className="status-tile-text">{t('status.allHotelsSortedBy')}</span>
          </button>
          <button type="button" className="status-tile" onClick={goUsers}>
            <span className="status-tile-title">{t('status.users')}</span>
            <span className="status-tile-text">{t('status.guestsRankedByBookings')}</span>
          </button>
        </div>
      </div>
    )
  }

  if (level.kind === 'users') {
    return (
      <StatusRankedTable<StatusUser>
        key="users"
        title={t('status.users')}
        subtitle={t('status.subtitleUsers')}
        noun="status.nounUsers"
        {...periodProps}
        load={params => statusAdapter.getUsers(params)}
        rowKey={row => row.id}
        rowLabel={row => row.full_name || row.email}
        onOpen={row => navigate(`/admin/customers/${row.id}`)}
        columns={[
          { header: t('admin.name'), render: row => row.full_name },
          { header: t('profile.contact.phone'), render: row => row.phone || '—' },
          { header: t('auth.email'), render: row => row.email },
          { header: t('status.bookings'), numeric: true, render: row => formatCount(row.bookings) },
          { header: t('status.totalSpent'), numeric: true, render: row => formatMoneyList(row.total_spent) },
          { header: t('status.lastBooking'), render: row => formatDate(row.last_booking_date, i18n) },
          {
            header: t('status.statistics'),
            render: row => (
              <button
                type="button"
                className="btn btn-secondary"
                aria-label={t('status.statisticsOf', { name: row.full_name || row.email })}
                onClick={event => { event.stopPropagation(); setLevel({ kind: 'user', userId: row.id, name: row.full_name || row.email }) }}
              >
                {t('status.statistics')}
              </button>
            ),
          },
        ]}
      />
    )
  }

  if (level.kind === 'countries') {
    return (
      <StatusRankedTable<StatusCountry>
        key="countries"
        title={t('home.stat.countries')}
        subtitle={t('status.subtitleCountries')}
        noun="status.nounCountries"
        {...periodProps}
        load={params => statusAdapter.getCountries(params)}
        rowKey={row => countryPlace(row).key}
        rowLabel={row => label(countryPlace(row))}
        onOpen={row => goRegions(countryPlace(row))}
        columns={[
          { header: t('status.country'), render: row => label(countryPlace(row)) },
          { header: t('status.title'), numeric: true, render: row => formatCount(row.hotels) },
          ...metricColumns<StatusCountry>(t),
        ]}
      />
    )
  }

  if (level.kind === 'regions') {
    const { country } = level
    return (
      <StatusRankedTable<StatusRegion>
        key={`regions:${country.key}`}
        title={label(country)}
        subtitle={t('status.subtitleRegions')}
        noun="status.nounRegions"
        {...periodProps}
        load={params => statusAdapter.getRegions(country.key, params)}
        rowKey={row => regionPlace(row).key}
        rowLabel={row => label(regionPlace(row))}
        onOpen={row => goHotels(country, regionPlace(row))}
        columns={[
          { header: t('status.region'), render: row => label(regionPlace(row)) },
          { header: t('status.title'), numeric: true, render: row => formatCount(row.hotels) },
          ...metricColumns<StatusRegion>(t),
        ]}
      />
    )
  }

  if (level.kind === 'hotels') {
    const { country, region } = level
    return (
      <StatusRankedTable<StatusHotel>
        key={`hotels:${country.key}:${region.key}`}
        title={`${label(region)}, ${label(country)}`}
        subtitle={t('status.subtitleHotels')}
        noun="status.nounHotels"
        {...periodProps}
        load={params => statusAdapter.getHotels(country.key, region.key, params)}
        rowKey={row => row.id}
        rowLabel={row => row.name}
        onOpen={row => setLevel({ kind: 'hotel', country, region, hotelId: row.id, hotelName: row.name })}
        columns={[
          { header: t('status.hotel'), render: row => row.name },
          { header: t('admin.city'), render: row => row.city },
          ...metricColumns<StatusHotel>(t),
        ]}
      />
    )
  }

  if (level.kind === 'allHotels') {
    return (
      <AdminStatusHotels
        {...periodProps}
        onOpen={row => setLevel({ kind: 'allHotel', hotelId: row.id, hotelName: row.name })}
      />
    )
  }

  if (level.kind === 'user') {
    return <StatusUserDetail key={level.userId} userId={level.userId} {...periodProps} />
  }

  return <StatusHotelDetail key={level.hotelId} hotelId={level.hotelId} {...periodProps} />
}
