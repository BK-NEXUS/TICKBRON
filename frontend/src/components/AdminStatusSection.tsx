import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { statusAdapter, StatusCountry, StatusHotel, StatusRegion, StatusUser } from '../adapters/statusAdapter'
import { Crumb, usePageTrail } from './Breadcrumbs'
import { StatusRankedTable, StatusColumn } from './StatusRankedTable'
import { StatusHotelDetail } from './StatusHotelDetail'
import { AdminStatusHotels } from './AdminStatusHotels'
import { StatusUserDetail } from './StatusUserDetail'
import { useStatusPeriod } from '../hooks/useStatusPeriod'
import { formatCount, formatDate, formatMoneyList } from '../utils/statusFormat'

type Level =
  | { kind: 'home' }
  | { kind: 'countries' }
  | { kind: 'regions'; country: string }
  | { kind: 'hotels'; country: string; region: string }
  | { kind: 'hotel'; country: string; region: string; hotelId: number; hotelName: string }
  | { kind: 'users' }
  | { kind: 'allHotels' }
  | { kind: 'allHotel'; hotelId: number; hotelName: string }
  | { kind: 'user'; userId: number; name: string }

interface AdminStatusSectionProps {
  /** Leave the Status section (the "Admin Dashboard" breadcrumb, or Back from the tiles) */
  onExit: () => void
}

type Metrics = { bookings: number; guests: number; revenue: { currency: string; amount: string }[] }

function metricColumns<T extends Metrics>(): StatusColumn<T>[] {
  return [
    { header: 'Bookings', numeric: true, render: row => formatCount(row.bookings) },
    { header: 'Guests', numeric: true, render: row => formatCount(row.guests) },
    { header: 'Revenue', numeric: true, render: row => formatMoneyList(row.revenue) },
  ]
}

/**
 * Admin panel > Status: Countries > Regions > Hotels > Hotel detail, and Users (guests ranking).
 * Numbers count confirmed and completed bookings, by check-in date; revenue per currency.
 */
export function AdminStatusSection({ onExit }: AdminStatusSectionProps) {
  const [level, setLevel] = useState<Level>({ kind: 'home' })
  const { period, range, setPeriod, setRange } = useStatusPeriod()
  const navigate = useNavigate()
  // Every list and detail takes the period and the custom range together
  const periodProps = { period, range, onPeriodChange: setPeriod, onRangeChange: setRange }

  const goHome = () => setLevel({ kind: 'home' })
  const goCountries = () => setLevel({ kind: 'countries' })
  const goRegions = (country: string) => setLevel({ kind: 'regions', country })
  const goHotels = (country: string, region: string) => setLevel({ kind: 'hotels', country, region })

  // Home › Admin Dashboard › Status › Countries › Uzbekistan › Tashkent › Hotel (each level clickable, Back steps up)
  const trail: Crumb[] = [{ label: 'Admin Dashboard', onClick: onExit }]
  trail.push(level.kind === 'home' ? { label: 'Status' } : { label: 'Status', onClick: goHome })
  const goUsers = () => setLevel({ kind: 'users' })
  const goAllHotels = () => setLevel({ kind: 'allHotels' })
  if (level.kind === 'users') trail.push({ label: 'Users' })
  if (level.kind === 'user') trail.push({ label: 'Users', onClick: goUsers }, { label: level.name })
  if (level.kind === 'allHotels') trail.push({ label: 'Hotels' })
  if (level.kind === 'allHotel') trail.push({ label: 'Hotels', onClick: goAllHotels }, { label: level.hotelName })
  if (level.kind === 'countries' || level.kind === 'regions' || level.kind === 'hotels' || level.kind === 'hotel') {
    trail.push(level.kind === 'countries' ? { label: 'Countries' } : { label: 'Countries', onClick: goCountries })
  }
  if (level.kind === 'regions' || level.kind === 'hotels' || level.kind === 'hotel') {
    const { country } = level
    trail.push(level.kind === 'regions' ? { label: country } : { label: country, onClick: () => goRegions(country) })
  }
  if (level.kind === 'hotels' || level.kind === 'hotel') {
    const { country, region } = level
    trail.push(level.kind === 'hotels' ? { label: region } : { label: region, onClick: () => goHotels(country, region) })
  }
  if (level.kind === 'hotel') trail.push({ label: level.hotelName })
  usePageTrail(trail)

  if (level.kind === 'home') {
    return (
      <div className="admin-status">
        <div className="admin-view-header">
          <h1 className="admin-view-title">Status</h1>
          <p className="admin-view-subtitle">
            Bookings, guests and revenue. Only confirmed and completed bookings count, by check-in date.
          </p>
        </div>
        <div className="status-tiles">
          <button type="button" className="status-tile" onClick={goCountries}>
            <span className="status-tile-title">Countries</span>
            <span className="status-tile-text">By country, region and hotel</span>
          </button>
          <button type="button" className="status-tile" onClick={goAllHotels}>
            <span className="status-tile-title">Hotels</span>
            <span className="status-tile-text">All hotels, sorted by revenue, bookings, guests and more</span>
          </button>
          <button type="button" className="status-tile" onClick={goUsers}>
            <span className="status-tile-title">Users</span>
            <span className="status-tile-text">Guests ranked by bookings</span>
          </button>
        </div>
      </div>
    )
  }

  if (level.kind === 'users') {
    return (
      <StatusRankedTable<StatusUser>
        key="users"
        title="Users"
        subtitle="Top 1,000 guests by bookings. Search by name, phone, email or ID; open a row for the customer profile."
        noun="users"
        {...periodProps}
        load={params => statusAdapter.getUsers(params)}
        rowKey={row => row.id}
        rowLabel={row => row.full_name || row.email}
        onOpen={row => navigate(`/admin/customers/${row.id}`)}
        columns={[
          { header: 'Name', render: row => row.full_name },
          { header: 'Phone', render: row => row.phone || '—' },
          { header: 'Email', render: row => row.email },
          { header: 'Bookings', numeric: true, render: row => formatCount(row.bookings) },
          { header: 'Total spent', numeric: true, render: row => formatMoneyList(row.total_spent) },
          { header: 'Last booking', render: row => formatDate(row.last_booking_date) },
          {
            header: 'Statistics',
            render: row => (
              <button
                type="button"
                className="btn btn-secondary"
                aria-label={`Statistics of ${row.full_name || row.email}`}
                onClick={event => { event.stopPropagation(); setLevel({ kind: 'user', userId: row.id, name: row.full_name || row.email }) }}
              >
                Statistics
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
        title="Countries"
        subtitle="Top 100 countries by bookings"
        noun="countries"
        {...periodProps}
        load={params => statusAdapter.getCountries(params)}
        rowKey={row => row.country}
        rowLabel={row => row.country}
        onOpen={row => goRegions(row.country)}
        columns={[
          { header: 'Country', render: row => row.country },
          { header: 'Hotels', numeric: true, render: row => formatCount(row.hotels) },
          ...metricColumns<StatusCountry>(),
        ]}
      />
    )
  }

  if (level.kind === 'regions') {
    const { country } = level
    return (
      <StatusRankedTable<StatusRegion>
        key={`regions:${country}`}
        title={country}
        subtitle="Top 100 regions by bookings"
        noun="regions"
        {...periodProps}
        load={params => statusAdapter.getRegions(country, params)}
        rowKey={row => row.region}
        rowLabel={row => row.region}
        onOpen={row => goHotels(country, row.region)}
        columns={[
          { header: 'Region', render: row => row.region },
          { header: 'Hotels', numeric: true, render: row => formatCount(row.hotels) },
          ...metricColumns<StatusRegion>(),
        ]}
      />
    )
  }

  if (level.kind === 'hotels') {
    const { country, region } = level
    return (
      <StatusRankedTable<StatusHotel>
        key={`hotels:${country}:${region}`}
        title={`${region}, ${country}`}
        subtitle="Top 1,000 hotels by bookings"
        noun="hotels"
        {...periodProps}
        load={params => statusAdapter.getHotels(country, region, params)}
        rowKey={row => row.id}
        rowLabel={row => row.name}
        onOpen={row => setLevel({ kind: 'hotel', country, region, hotelId: row.id, hotelName: row.name })}
        columns={[
          { header: 'Hotel', render: row => row.name },
          { header: 'City', render: row => row.city },
          ...metricColumns<StatusHotel>(),
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
