import { useI18n } from '../i18n/I18nContext'
import { textKeys, useTexts } from '../i18n/I18nContext'
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

const TEXT_KEYS = textKeys({
  title: 'status.title',
  subtitle: 'status.subtitle',
  sortBy: 'status.sortBy',
  order: 'status.order',
  ascending: 'status.ascending',
  descending: 'status.descending',
  columns: {
    hotel: 'status.hotel', location: 'property.location', status: 'partner.status', rating: 'sort.rating', created: 'status.created', counted: 'status.counted',
    stayed: 'status.stayed', guests: 'searchForm.guests', nights: 'status.nights', revenue: 'status.revenue',
  },

})

const SORTS = [
  { value: 'revenue', labelKey: 'status.sortRevenueUzs' },
  { value: 'bookings', labelKey: 'status.bookings' },
  { value: 'guests', labelKey: 'status.guests' },
  { value: 'nights', labelKey: 'status.nights' },
  { value: 'rating', labelKey: 'sort.rating' },
  { value: 'created_at', labelKey: 'status.createdDate' },
] as const

/** Admin Status > Hotels: every hotel in one list, sorted and paginated by the backend, with CSV export */
export function AdminStatusHotels({ period, range, onPeriodChange, onRangeChange, onOpen }: AdminStatusHotelsProps) {
  const i18n = useI18n()
  const TEXT = useTexts(TEXT_KEYS)
  const id = useId()
  const [sort, setSort] = useState('bookings')
  const [descending, setDescending] = useState(true)
  const ordering = `${descending ? '-' : ''}${sort}`

  const toolbar = (
    <div className="status-field">
      <label htmlFor={`${id}-sort`}>{TEXT.sortBy}</label>
      <select id={`${id}-sort`} value={sort} onChange={e => setSort(e.target.value)}>
        {SORTS.map(option => <option key={option.value} value={option.value}>{i18n.t(option.labelKey)}</option>)}
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
        noun="status.nounHotels"
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
          { header: TEXT.columns.created, render: row => formatDate(row.created_at, i18n) },
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
