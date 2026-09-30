import { ReactNode, useEffect, useId, useState } from 'react'
import type { StatusListParams, StatusPage, StatusResponse } from '../adapters/statusAdapter'
import { StatusPeriodSelector } from './StatusPeriodSelector'
import { formatCount } from '../utils/statusFormat'

const PAGE_SIZE = 20
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
  title, subtitle, noun, period, onPeriodChange, load, rowKey, rowLabel, onOpen, columns,
}: StatusRankedTableProps<T>) {
  const id = useId()
  const [searchInput, setSearchInput] = useState('')
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [data, setData] = useState<StatusPage<T> | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Search after the user stops typing, from the first page
  useEffect(() => {
    if (searchInput === search) return
    const timer = setTimeout(() => {
      setSearch(searchInput)
      setPage(1)
    }, SEARCH_DELAY_MS)
    return () => clearTimeout(timer)
  }, [searchInput, search])

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)
    load({ period, search, page }).then(response => {
      if (cancelled) return
      setData(response.data)
      setError(response.error)
      setLoading(false)
    })
    return () => { cancelled = true }
    // `load` is a new function every render; the list depends on what it is asked for
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [period, search, page])

  const handlePeriod = (next: string) => {
    setPage(1)
    onPeriodChange(next)
  }

  const totalPages = data ? Math.max(1, Math.ceil(data.count / PAGE_SIZE)) : 1
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
        <StatusPeriodSelector value={period} onChange={handlePeriod} />
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

          <div className="pagination-controls" role="navigation" aria-label="Pagination">
            <button
              type="button"
              className="pagination-button"
              onClick={() => setPage(p => p - 1)}
              disabled={!data?.previous}
              aria-label="Previous page"
            >
              Previous
            </button>
            <div className="pagination-info">
              <span aria-live="polite">Page {page} of {formatCount(totalPages)}</span>
            </div>
            <button
              type="button"
              className="pagination-button"
              onClick={() => setPage(p => p + 1)}
              disabled={!data?.next}
              aria-label="Next page"
            >
              Next
            </button>
          </div>
        </>
      )}
    </section>
  )
}
