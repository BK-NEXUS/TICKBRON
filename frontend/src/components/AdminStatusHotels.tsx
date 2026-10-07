import { useId, useState } from 'react'
import { statusAdapter, AdminStatusHotel } from '../adapters/statusAdapter'
import { StatusRankedTable } from './StatusRankedTable'
import { StatusCsvButton } from './StatusCsvButton'
import { StatusStayedNote } from './StatusStayedNote'
import { formatCount, formatDate, formatMoneyList } from '../utils/statusFormat'
import type { DateRange } from '../utils/statusPeriod'

interface AdminStatusHotelsProps {
  period: string
  range?: DateRange | null
  onPeriodChange: (period: string) => void
  onRangeChange: (range: DateRange) => void
  onOpen: (hotel: AdminStatusHotel) => void
}

const TEXT = {
  title: 'Hotels',
  subtitle: 'Top 1,000 hotels. Counted = confirmed and completed bookings; stayed = completed. Revenue per currency.',
  sortBy: 'Sort by',
  order: 'Order',
  ascending: 'Ascending',
  descending: 'Descending',
  columns: {
    hotel: 'Hotel', location: 'Location', status: 'Status', rating: 'Rating', created: 'Created', counted: 'Counted',
    stayed: 'Stayed bookings', guests: 'Guests', nights: 'Nights', revenue: 'Revenue',
  },
}

const SORTS = [
  { value: 'revenue', label: 'Revenue (UZS)' },
  { value: 'bookings', label: 'Bookings' },
  { value: 'guests', label: 'Guests' },
  { value: 'nights', label: 'Nights' },
  { value: 'rating', label: 'Rating' },
  { value: 'created_at', label: 'Created date' },
]

/** Admin Status > Hotels: every hotel in one list, sorted and paginated by the backend, with CSV export */
export function AdminStatusHotels({ period, range, onPeriodChange, onRangeChange, onOpen }: AdminStatusHotelsProps) {
  const id = useId()
  const [sort, setSort] = useState('bookings')
  const [descending, setDescending] = useState(true)
  const ordering = `${descending ? '-' : ''}${sort}`

  const toolbar = (
    <div className="status-field">
      <label htmlFor={`${id}-sort`}>{TEXT.sortBy}</label>
      <select id={`${id}-sort`} value={sort} onChange={e => setSort(e.target.value)}>
        {SORTS.map(option => <option key={option.value} value={option.value}>{option.label}</option>)}
      </select>
      <label htmlFor={`${id}-order`} className="sr-only">{TEXT.order}</label>
      <select id={`${id}-order`} value={descending ? 'desc' : 'asc'} onChange={e => setDescending(e.target.value === 'desc')}>
        <option value="desc">{TEXT.descending}</option>
        <option value="asc">{TEXT.ascending}</option>
      </select>
    </div>
  )

  return (
    <>
      <StatusRankedTable<AdminStatusHotel>
        title={TEXT.title}
        subtitle={TEXT.subtitle}
        noun="hotels"
        period={period}
        onPeriodChange={onPeriodChange}
        range={range}
        onRangeChange={onRangeChange}
        toolbar={toolbar}
        reloadKey={ordering}
        renderActions={({ search }) => (
          <StatusCsvButton
            onExport={() => statusAdapter.exportAdminHotels({
              period, ...(period === 'custom' && range ? range : {}), search, ordering,
            })}
          />
        )}
        load={params => statusAdapter.getAdminHotels({ ...params, ordering })}
        rowKey={row => row.id}
        rowLabel={row => row.name}
        onOpen={onOpen}
        columns={[
          { header: TEXT.columns.hotel, render: row => row.name },
          { header: TEXT.columns.location, render: row => `${row.city}, ${row.region}, ${row.country_code}` },
          { header: TEXT.columns.status, render: row => row.status },
          { header: TEXT.columns.rating, numeric: true, render: row => row.rating ?? '—' },
          { header: TEXT.columns.created, render: row => formatDate(row.created_at) },
          { header: TEXT.columns.counted, numeric: true, render: row => formatCount(row.bookings) },
          { header: TEXT.columns.stayed, numeric: true, render: row => formatCount(row.stayed) },
          { header: TEXT.columns.guests, numeric: true, render: row => formatCount(row.guests) },
          { header: TEXT.columns.nights, numeric: true, render: row => formatCount(row.nights) },
          { header: TEXT.columns.revenue, numeric: true, render: row => formatMoneyList(row.revenue) },
        ]}
      />
      <StatusStayedNote />
    </>
  )
}
