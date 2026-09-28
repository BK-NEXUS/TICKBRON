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
  const [destinations, setDestinations] = useState<Destination[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    propertyAdapter.searchProperties({ page_size: 100 }).then(response => {
      if (cancelled) return
      if (response.error || !response.data) {
        setError(response.error ?? 'Could not load destinations.')
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
      if (!cancelled) setError('Could not load destinations.')
    })
    return () => { cancelled = true }
  }, [])

  return (
    <div className="info-page container">
      <h1 className="info-page-title">Destinations</h1>
      <p className="info-page-intro">Cities where you can book a stay with TICKBRON.</p>
      {error && <p role="alert">{error}</p>}
      {!destinations && !error && <p role="status">Loading destinations...</p>}
      {destinations && destinations.length === 0 && <p>No destinations yet.</p>}
      {destinations && destinations.length > 0 && (
        <ul className="destinations-list">
          {destinations.map(d => (
            <li key={`${d.city}|${d.country}`}>
              <Link to={`/search?destination=${encodeURIComponent(d.city)}`} className="destinations-link">
                <span className="destinations-city">{d.city}</span>
                <span className="destinations-meta">{d.country} · {d.count} {d.count === 1 ? 'property' : 'properties'}</span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

export default DestinationsPage
