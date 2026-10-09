import { useI18n } from '../i18n/I18nContext'
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { propertyAdapter } from '../adapters/propertyAdapter'

interface Destination {
  city: string
  country: string
  count: number
}

/** Cities that have properties, each linking to a search for that city */
export function DestinationsPage() {
  const { t, tp } = useI18n()
  const [destinations, setDestinations] = useState<Destination[] | null>(null)
  // A message from the backend, or '' for a failure we describe ourselves (so it follows the page language)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    propertyAdapter.searchProperties({ page_size: 100 }).then(response => {
      if (cancelled) return
      if (response.error || !response.data) {
        setError(response.error ?? '')
        return
      }
      const byCity = new Map<string, Destination>()
      for (const property of response.data.results) {
        const key = `${property.city}|${property.country}`
        const entry = byCity.get(key) ?? { city: property.city, country: property.country, count: 0 }
        entry.count += 1
        byCity.set(key, entry)
      }
      setDestinations([...byCity.values()].sort((a, b) => b.count - a.count || a.city.localeCompare(b.city)))
    }).catch(() => {
      if (!cancelled) setError('')
    })
    return () => { cancelled = true }
  }, [])

  return (
    <div className="info-page container">
      <h1 className="info-page-title">{t('destinations.title')}</h1>
      <p className="info-page-intro">{t('destinations.intro')}</p>
      {error !== null && <p role="alert">{error || t('destinations.loadError')}</p>}
      {!destinations && error === null && <p role="status">{t('destinations.loading')}</p>}
      {destinations && destinations.length === 0 && <p>{t('destinations.empty')}</p>}
      {destinations && destinations.length > 0 && (
        <ul className="destinations-list">
          {destinations.map(d => (
            <li key={`${d.city}|${d.country}`}>
              <Link to={`/search?destination=${encodeURIComponent(d.city)}`} className="destinations-link">
                <span className="destinations-city">{d.city}</span>
                <span className="destinations-meta">{d.country} · {tp('home.properties', d.count)}</span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

export default DestinationsPage
