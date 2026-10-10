import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { propertyAdapter, type FilterOptions } from '../adapters/propertyAdapter'
import { useI18n } from '../i18n/I18nContext'

type PropertyTypeChip = FilterOptions['property_types'][number]

/**
 * Pill links for the property types that really exist, each with its hotel count. A type
 * without hotels is not shown; with an error or no types the strip is not shown at all.
 */
export function HomePropertyTypes() {
  const { t } = useI18n()
  const [types, setTypes] = useState<PropertyTypeChip[] | null>(null)

  useEffect(() => {
    let cancelled = false
    propertyAdapter.getFilterOptions()
      .then((response) => {
        if (!cancelled) setTypes(response.data?.property_types.filter((type) => type.count > 0) ?? [])
      })
      .catch(() => { if (!cancelled) setTypes([]) })
    return () => { cancelled = true }
  }, [])

  if (types !== null && types.length === 0) return null

  if (types === null) {
    return (
      <div className="home-types container" role="status" aria-label={t('home.typeChips.loading')}>
        <div className="home-types-list" aria-hidden="true">
          {[0, 1, 2].map((index) => <div key={index} className="skeleton home-types-skeleton"></div>)}
        </div>
      </div>
    )
  }

  return (
    <nav className="home-types container" aria-label={t('home.typeChips.label')}>
      <ul className="home-types-list">
        {types.map((type) => (
          <li key={type.id}>
            <Link to={`/search?property_type=${type.id}`} className="home-type-chip">
              <span>{type.name}</span>
              <span className="home-type-chip-count">{type.count}</span>
            </Link>
          </li>
        ))}
      </ul>
    </nav>
  )
}
