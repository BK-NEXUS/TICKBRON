import { useI18n } from '../i18n/I18nContext'
import { useEffect, useState } from 'react'
import { Link } from 'react-router'
import {
  geographyAdapter,
  geographyName,
  type GeographyCountry,
  type GeographyRegion,
} from '../adapters/geographyAdapter'

interface CountryDestinations {
  country: GeographyCountry
  regions: GeographyRegion[]
}

/** Adapter nátiyjesin ashadı yamasa xabarın taslaydı, sol sebepli bir qátelik pútkil júklewdi tawsadı. */
function unwrap<T>(result: { data: T | null; error: string | null }): T {
  if (result.data === null) throw new Error(result.error ?? '')
  return result.data
}

/** Tek ashıq mehmanxanaları bar mámleketlerden regionları soraladı. */
async function loadDestinations(): Promise<CountryDestinations[]> {
  const countries = unwrap(await geographyAdapter.getCountries()).filter(c => c.hotel_count > 0)
  return Promise.all(countries.map(async country => {
    const regions = unwrap(await geographyAdapter.getRegions(country.code)).filter(r => r.hotel_count > 0)
    return { country, regions }
  }))
}

/** Mehmanxanaları bar regionlar, mámleket boyınsha toparlanǵan, hárbiri sol region ushın izlewge silteme */
export function DestinationsPage() {
  const { t, tp, language } = useI18n()
  const [destinations, setDestinations] = useState<CountryDestinations[] | null>(null)
  // Backend ten xabar, yamasa ózimiz táriyplep beretuǵın qátelik ushın '' (sol sebepli ol bet tilin izleydi)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    loadDestinations()
      .then(result => { if (!cancelled) setDestinations(result.filter(group => group.regions.length > 0)) })
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
      {destinations?.map(({ country, regions }) => (
        <section key={country.id}>
          <h2 className="destinations-country">{geographyName(country, language)}</h2>
          <ul className="destinations-list">
            {regions.map(region => {
              const name = geographyName(region, language)
              return (
                <li key={region.id}>
                  <Link to={`/search?destination=${encodeURIComponent(name)}`} className="destinations-link">
                    <span className="destinations-city">{name}</span>
                    <span className="destinations-meta">{tp('home.properties', region.hotel_count)}</span>
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
