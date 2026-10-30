import { useI18n } from '../i18n/I18nContext'
import { useEffect, useState } from 'react'
import { Link } from 'react-router'
import {
  geographyAdapter,
  geographyName,
  type GeographyCity,
  type GeographyCountry,
  type GeographyRegion,
} from '../adapters/geographyAdapter'

interface CountryDestinations {
  country: GeographyCountry
  cities: Array<{ city: GeographyCity; region: GeographyRegion }>
}

/** Unwraps an adapter result or throws its message, so one failure ends the whole load. */
function unwrap<T>(result: { data: T | null; error: string | null }): T {
  if (result.data === null) throw new Error(result.error ?? '')
  return result.data
}

/** Only places with public hotels are asked for their children. */
async function loadDestinations(): Promise<CountryDestinations[]> {
  const countries = unwrap(await geographyAdapter.getCountries()).filter(c => c.hotel_count > 0)
  return Promise.all(countries.map(async country => {
    const regions = unwrap(await geographyAdapter.getRegions(country.code)).filter(r => r.hotel_count > 0)
    const perRegion = await Promise.all(regions.map(async region => {
      const cities = unwrap(await geographyAdapter.getCities(region.id)).filter(c => c.hotel_count > 0)
      return cities.map(city => ({ city, region }))
    }))
    return { country, cities: perRegion.flat() }
  }))
}

/** Cities that have properties, grouped by country, each linking to a search for that city */
export function DestinationsPage() {
  const { t, tp, language } = useI18n()
  const [destinations, setDestinations] = useState<CountryDestinations[] | null>(null)
  // A message from the backend, or '' for a failure we describe ourselves (so it follows the page language)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    loadDestinations()
      .then(result => { if (!cancelled) setDestinations(result.filter(group => group.cities.length > 0)) })
      .catch((failure: unknown) => { if (!cancelled) setError(failure instanceof Error ? failure.message : '') })
    return () => { cancelled = true }
  }, [])

  return (
    <div className="info-page container">
      <h1 className="info-page-title">{t('destinations.title')}</h1>
      <p className="info-page-intro">{t('destinations.intro')}</p>
      {error !== null && <p role="alert">{error || t('destinations.loadError')}</p>}
      {!destinations && error === null && <p role="status">{t('destinations.loading')}</p>}
      {destinations && destinations.length === 0 && <p>{t('destinations.empty')}</p>}
      {destinations?.map(({ country, cities }) => (
        <section key={country.id}>
          <h2 className="destinations-country">{geographyName(country, language)}</h2>
          <ul className="destinations-list">
            {cities.map(({ city, region }) => {
              const name = geographyName(city, language)
              return (
                <li key={city.id}>
                  <Link to={`/search?destination=${encodeURIComponent(name)}`} className="destinations-link">
                    <span className="destinations-city">{name}</span>
                    <span className="destinations-meta">{geographyName(region, language)} · {tp('home.properties', city.hotel_count)}</span>
                  </Link>
                </li>
              )
            })}
          </ul>
        </section>
      ))}
    </div>
  )
}

export default DestinationsPage
