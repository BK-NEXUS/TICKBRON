import { useI18n } from '../i18n/I18nContext'
import { SORT_OPTIONS } from '../utils/searchFilters'

interface SearchSortProps {
  sortBy: string
  onSortChange: (sortBy: string) => void
}

/**
 * SearchSort component for sorting search results
 * Provides sorting options for relevance, price, rating, and reviews
 */
export function SearchSort({ sortBy, onSortChange }: SearchSortProps) {
  const { t } = useI18n()
  return (
    <div className="search-sort">
      <label htmlFor="sort-select" className="search-sort-label">
        {t('sort.label')}
      </label>
      <select
        id="sort-select"
        value={sortBy}
        onChange={(e) => onSortChange(e.target.value)}
        className="search-sort-select"
        aria-label={t('sort.aria')}
      >
        {SORT_OPTIONS.map(option => (
          <option key={option.id} value={option.id}>
            {t(option.labelKey)}
          </option>
        ))}
      </select>
    </div>
  )
}