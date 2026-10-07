import { formatCount } from '../utils/statusFormat'

interface StatusPaginationProps {
  page: number
  /** Items in the whole list */
  count: number
  /** Items per server page; the Status lists use 20 */
  pageSize?: number
  hasPrevious: boolean
  hasNext: boolean
  onPage: (page: number) => void
}

export const STATUS_PAGE_SIZE = 20

const TEXT = { previous: 'Previous', next: 'Next', previousLabel: 'Previous page', nextLabel: 'Next page' }

/** Previous / Next with "Page X of Y" for the server-paginated Status lists */
export function StatusPagination({
  page, count, pageSize = STATUS_PAGE_SIZE, hasPrevious, hasNext, onPage,
}: StatusPaginationProps) {
  const totalPages = Math.max(1, Math.ceil(count / pageSize))
  return (
    <div className="pagination-controls" role="navigation" aria-label="Pagination">
      <button
        type="button"
        className="pagination-button"
        onClick={() => onPage(page - 1)}
        disabled={!hasPrevious}
        aria-label={TEXT.previousLabel}
      >
        {TEXT.previous}
      </button>
      <div className="pagination-info">
        <span aria-live="polite">Page {page} of {formatCount(totalPages)}</span>
      </div>
      <button
        type="button"
        className="pagination-button"
        onClick={() => onPage(page + 1)}
        disabled={!hasNext}
        aria-label={TEXT.nextLabel}
      >
        {TEXT.next}
      </button>
    </div>
  )
}
