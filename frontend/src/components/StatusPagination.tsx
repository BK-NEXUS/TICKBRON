import { textKeys, useI18n, useTexts } from '../i18n/I18nContext'
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

const TEXT_KEYS = textKeys({ pagination: 'status.pagination', previous: 'admin.previous', next: 'partner.next', previousLabel: 'admin.previousPage', nextLabel: 'admin.nextPage' })

/** Previous / Next with "Page X of Y" for the server-paginated Status lists */
export function StatusPagination({
  page, count, pageSize = STATUS_PAGE_SIZE, hasPrevious, hasNext, onPage,
}: StatusPaginationProps) {
  const TEXT = useTexts(TEXT_KEYS)
  const { t } = useI18n()
  const totalPages = Math.max(1, Math.ceil(count / pageSize))
  return (
    <div className="pagination-controls" role="navigation" aria-label={TEXT.pagination}>
      <button
        type="button"
        className="btn btn-secondary btn-sm"
        onClick={() => onPage(page - 1)}
        disabled={!hasPrevious}
        aria-label={TEXT.previousLabel}
      >
        {TEXT.previous}
      </button>
      <div className="pagination-info">
        <span aria-live="polite">{t('admin.pageOf', { page, total: formatCount(totalPages) })}</span>
      </div>
      <button
        type="button"
        className="btn btn-secondary btn-sm"
        onClick={() => onPage(page + 1)}
        disabled={!hasNext}
        aria-label={TEXT.nextLabel}
      >
        {TEXT.next}
      </button>
    </div>
  )
}
