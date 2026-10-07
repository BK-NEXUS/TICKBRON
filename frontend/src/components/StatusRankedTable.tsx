import { ReactNode, useEffect, useId, useState } from 'react'
import type { StatusListParams, StatusPage, StatusResponse } from '../adapters/statusAdapter'
import { StatusPeriodSelector } from './StatusPeriodSelector'
import { formatCount } from '../utils/statusFormat'
import { StatusPagination } from './StatusPagination'
import type { DateRange } from '../utils/statusPeriod'

const SEARCH_DELAY_MS = 300

export interface StatusColumn<T> {
  header: string
  render: (row: T) => ReactNode
  numeric?: boolean
}

interface StatusRankedTableProps<T> {
  title: string
  subtitle?: string
  /** e.g. "countries": used in the search label and the empty message */
  noun: string
  period: string
  onPeriodChange: (period: string) => void
  /** The applied custom range; with `onRangeChange` the selector offers the custom option */
  range?: DateRange | null
  onRangeChange?: (range: DateRange) => void
  /** Extra controls next to the search box, e.g. a sort order */
  toolbar?: ReactNode
  /** Extra actions that need the current search, e.g. an export button */
  renderActions?: (state: { search: string }) => ReactNode
  /** Changing it reloads the list from the first page (use it for the options `load` closes over) */
  reloadKey?: string
  load: (params: StatusListParams) => Promise<StatusResponse<StatusPage<T>>>
  rowKey: (row: T) => string | number
  /** Text of the row's link button (the first column) */
  rowLabel: (row: T) => string
  onOpen: (row: T) => void
  columns: StatusColumn<T>[]
}

/**
 * One ranked, paginated Status list with its own search box (searches this list only)
 * and the shared period selector. Loading, empty and error states included.
 */
export function StatusRankedTable<T>({
  title, subtitle, noun, period, onPeriodChange, range, onRangeChange, toolbar, renderActions, reloadKey = '',
  load, rowKey, rowLabel, onOpen, columns,
}: StatusRankedTableProps<T>) {
  const id = useId()
  const [searchInput, setSearchInput] = useState('')
  const [search, setSearch] = useState('')
  const [pageState, setPageState] = useState({ key: reloadKey, page: 1 })
  // A new reloadKey starts again from the first page without a second request
  const page = pageState.key === reloadKey ? pageState.page : 1
  const goToPage = (next: number) => setPageState({ key: reloadKey, page: next })
  const [data, setData] = useState<StatusPage<T> | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Search after the user stops typing, from the first page
  useEffect(() => {
    if (searchInput === search) return
    const timer = setTimeout(() => {
      setSearch(searchInput)
      goToPage(1)
    }, SEARCH_DELAY_MS)
    return () => clearTimeout(timer)
  }, [searchInput, search])

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)
    const applied = period === 'custom' && range ? { from: range.from, to: range.to } : {}
    load({ period, ...applied, search, page }).then(response => {
      if (cancelled) return
      setData(response.data)
      setError(response.error)
      setLoading(false)
    })
    return () => { cancelled = true }
    // `load` is a new function every render; the list depends on what it is asked for
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [period, range, search, page, reloadKey])

  const handlePeriod = (next: string) => {
    goToPage(1)
    onPeriodChange(next)
  }

  const handleRange = (next: DateRange) => {
    goToPage(1)
    onRangeChange?.(next)
  }

  const rows = data?.results ?? []

  return (
    <section className="status-list" aria-labelledby={`${id}-title`}>
      <div className="admin-view-header">
        <h2 id={`${id}-title`} className="admin-view-title">{title}</h2>
        {subtitle && <p className="admin-view-subtitle">{subtitle}</p>}
      </div>

      <div className="status-controls">
        <div className="status-search">
          <label htmlFor={`${id}-search`} className="sr-only">Search {noun}</label>
          <input
            id={`${id}-search`}
            type="search"
            className="search-input"
            placeholder={`Search ${noun}...`}
            value={searchInput}
            onChange={e => setSearchInput(e.target.value)}
          />
        </div>
        {toolbar}
        <StatusPeriodSelector
          value={period} range={range} onChange={handlePeriod} onRangeChange={onRangeChange && handleRange}
        />
        {renderActions?.({ search })}
      </div>

      {error ? (
        <div className="alert alert-error" role="alert">{error}</div>
      ) : loading ? (
        <div className="loading-state" role="status" aria-live="polite">Loading {noun}...</div>
      ) : rows.length === 0 ? (
        <div className="empty-state">
          <p>{search ? `No ${noun} match "${search}".` : `No ${noun} found for this period.`}</p>
        </div>
      ) : (
        <>
          <div className="customers-table-container">
            <table className="customers-table status-table">
              <thead>
                <tr>
                  <th scope="col" className="status-cell--numeric">#</th>
                  {columns.map(column => (
                    <th key={column.header} scope="col" className={column.numeric ? 'status-cell--numeric' : undefined}>
                      {column.header}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {rows.map(row => (
                  <tr key={rowKey(row)} className="status-row" onClick={() => onOpen(row)}>
                    <td className="status-cell--numeric">{formatCount((row as { rank: number }).rank)}</td>
                    {columns.map((column, index) => (
                      <td key={column.header} className={column.numeric ? 'status-cell--numeric' : undefined}>
                        {index === 0 ? (
                          <button
                            type="button"
                            className="status-row-link"
                            onClick={event => { event.stopPropagation(); onOpen(row) }}
                          >
                            {rowLabel(row)}
                          </button>
                        ) : column.render(row)}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <StatusPagination
            page={page} count={data?.count ?? 0} hasPrevious={Boolean(data?.previous)} hasNext={Boolean(data?.next)}
            onPage={goToPage}
          />
        </>
      )}
    </section>
  )
}
