import { useCallback, useEffect, useState, type ReactElement } from 'react'
import { Link } from 'react-router-dom'
import { ImageOff } from 'lucide-react'
import { useI18n } from '../i18n/I18nContext'
import {
  geographyAdapter, geographyName,
  type GeographyCountry, type GeographyNames, type GeographyRegion,
} from '../adapters/geographyAdapter'

interface Place extends GeographyNames {
  hotel_count: number
  image_url: string | null
}

function PlaceCard({ place, children }: { place: Place; children: (body: ReactElement) => ReactElement }) {
  const { tp, language } = useI18n()
  const body = (
    <>
      <span className="where-to-picture">
        {place.image_url
          ? <img src={place.image_url} alt="" loading="lazy" />
          : <ImageOff size={24} aria-hidden="true" />}
      </span>
      <span className="where-to-name">{geographyName(place, language)}</span>
      <span className="where-to-count">{tp('home.properties', place.hotel_count)}</span>
    </>
  )
  return children(body)
}

/**
 * "Where to?" under the search form: the active countries with their pictures; choosing one lists its
 * regions, and a region opens the search for that place. The names come from the Geography dictionary
 * the super admin keeps. Nothing is shown while there is no active country.
 */
export function HomeWhereTo() {
  const { t, language } = useI18n()
  const [countries, setCountries] = useState<GeographyCountry[] | null>(null)
  const [countriesFailed, setCountriesFailed] = useState(false)
  const [country, setCountry] = useState<GeographyCountry | null>(null)
  const [regions, setRegions] = useState<GeographyRegion[] | null>(null)
  const [regionsFailed, setRegionsFailed] = useState(false)

  const loadCountries = useCallback(() => {
    setCountriesFailed(false)
    setCountries(null)
    void geographyAdapter.getCountries().then(({ data, error }) => {
      if (error || !data) setCountriesFailed(true)
      else setCountries(data)
    })
  }, [])

  const loadRegions = useCallback((chosen: GeographyCountry) => {
    setRegionsFailed(false)
    setRegions(null)
    void geographyAdapter.getRegions(chosen.code).then(({ data, error }) => {
      if (error || !data) setRegionsFailed(true)
      else setRegions(data)
    })
  }, [])

  useEffect(() => { loadCountries() }, [loadCountries])

  const choose = (chosen: GeographyCountry) => {
    setCountry(chosen)
    loadRegions(chosen)
  }

  const retry = () => (country ? loadRegions(country) : loadCountries())

  if (countries !== null && countries.length === 0 && !countriesFailed) return null

  const failed = country ? regionsFailed : countriesFailed
  const loading = country ? regions === null && !regionsFailed : countries === null && !countriesFailed

  return (
    <section className="where-to container" aria-labelledby="where-to-title">
      {country ? (
        <div className="where-to-header">
          <button type="button" className="btn btn-tertiary btn-sm" onClick={() => { setCountry(null); setRegions(null) }}>
            {t('home.allCountries')}
          </button>
          <h2 id="where-to-title" className="where-to-title">{geographyName(country, language)}</h2>
        </div>
      ) : (
        <div className="where-to-header">
          <h2 id="where-to-title" className="where-to-title">{t('home.whereTo')}</h2>
          <p className="where-to-hint">{t('home.whereToHint')}</p>
        </div>
      )}

      {loading && <p role="status" className="loading-state">{t('home.whereToLoading')}</p>}
      {failed && (
        <div className="alert alert-error" role="alert">
          <p>{t('home.whereToError')}</p>
          <button type="button" className="btn btn-secondary" onClick={retry}>{t('common.tryAgain')}</button>
        </div>
      )}

      {!country && countries && countries.length > 0 && (
        <ul className="where-to-list">
          {countries.map(item => (
            <li key={item.id}>
              <PlaceCard place={item}>
                {body => <button type="button" className="where-to-card" onClick={() => choose(item)}>{body}</button>}
              </PlaceCard>
            </li>
          ))}
        </ul>
      )}

      {country && regions && regions.length === 0 && <p className="empty-state">{t('home.whereToNoRegions')}</p>}
      {country && regions && regions.length > 0 && (
        <ul className="where-to-list">
          {regions.map(item => (
            <li key={item.id}>
              <PlaceCard place={item}>
                {body => (
                  <Link className="where-to-card" to={`/search?destination=${encodeURIComponent(geographyName(item, language))}`}>
                    {body}
                  </Link>
                )}
              </PlaceCard>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
