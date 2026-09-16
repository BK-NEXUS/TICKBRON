interface SearchSortProps {
  sortBy: string
  onSortChange: (sortBy: string) => void
}

const SORT_OPTIONS = [
  { id: 'relevance', label: 'Relevance' },
  { id: 'price_low', label: 'Price: Low to High' },
  { id: 'price_high', label: 'Price: High to Low' },
  { id: 'rating', label: 'Rating' },
  { id: 'reviews', label: 'Number of Reviews' },
]

/**
 * SearchSort component for sorting search results
 * Provides sorting options for relevance, price, rating, and reviews
 */
export function SearchSort({ sortBy, onSortChange }: SearchSortProps) {
  return (
    <div className="search-sort">
      <label htmlFor="sort-select" className="search-sort-label">
        Sort by:
      </label>
      <select
        id="sort-select"
        value={sortBy}
        onChange={(e) => onSortChange(e.target.value)}
        className="search-sort-select"
        aria-label="Sort search results"
      >
        {SORT_OPTIONS.map(option => (
          <option key={option.id} value={option.id}>
            {option.label}
          </option>
        ))}
      </select>
    </div>
  )
}