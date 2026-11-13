import { useCallback, useEffect, useState, type ReactElement } from 'react'
import { Link } from 'react-router'
import { ImageOff } from 'lucide-react'
import { useI18n } from '../i18n/I18nContext'
import { SoftImage } from './SoftImage'
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
  // Faylı serverde joq súwret súwretsiz orın menen birdey placeholder kórsetedi
  const [pictureMissing, setPictureMissing] = useState(false)
  const body = (
    <>
      <span className="where-to-picture">
        {place.image_url && !pictureMissing
          ? <SoftImage src={place.image_url} alt="" loading="lazy" onError={() => setPictureMissing(true)} />
          : <ImageOff size={24} aria-hidden="true" />}
      </span>
      <span className="where-to-name">{geographyName(place, language)}</span>
      <span className="where-to-count">{tp('home.properties', place.hotel_count)}</span>
    </>
  )
  return children(body)
}

/**
 * Izlew formasınıń astında "Qayaqqa?": súwretleri menen aktiv mámleketler; birin tańlaw onıń
 * regionların dizimleydi, hám region sol orın ushın izlewdi ashadı. Atlar super admin saqlaytuǵın
 * Geography sózliginen keledi. Aktiv mámleket joq waqıtta hesh nárse kórsetilmeydi.
 */
interface HomeWhereToProps {
  /** Mehmann ashqan mámleket penen shaqırıladı, yamasa barlıq mámleketlerge qaytqanda null */
  onCountryChange?: (country: GeographyCountry | null) => void
}

export function HomeWhereTo({ onCountryChange }: HomeWhereToProps) {
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
    onCountryChange?.(chosen)
  }

  const back = () => {
    setCountry(null)
    setRegions(null)
    onCountryChange?.(null)
  }

  const retry = () => (country ? loadRegions(country) : loadCountries())

  if (countries !== null && countries.length === 0 && !countriesFailed) return null

  const failed = country ? regionsFailed : countriesFailed
  const loading = country ? regions === null && !regionsFailed : countries === null && !countriesFailed

  return (
    <section className="where-to container" aria-labelledby="where-to-title">
      {country ? (
        <div className="where-to-header">
          <button type="button" className="btn btn-tertiary btn-sm" onClick={back}>
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

      {loading && (
        <>
          <p role="status" className="loading-state">{t('home.whereToLoading')}</p>
          <div className="where-to-skeletons" aria-hidden="true">
            {Array.from({ length: 4 }).map((_, index) => (
              <div key={index} className="where-to-skeleton">
                <div className="skeleton where-to-skeleton-picture"></div>
                <div className="skeleton skeleton-text"></div>
              </div>
            ))}
          </div>
        </>
      )}
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
