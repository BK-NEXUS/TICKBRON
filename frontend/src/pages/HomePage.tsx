import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router'
import { promotionAdapter, type PromotedProperty } from '../adapters/promotionAdapter'
import { geographyName, type GeographyCountry } from '../adapters/geographyAdapter'
import { HomeHotelSection } from '../components/HomeHotelSection'
import { HomePropertyTypes } from '../components/HomePropertyTypes'
import { HomeWhereTo } from '../components/HomeWhereTo'
import { PromoCarousel } from '../components/PromoCarousel'
import { SearchForm } from '../components/SearchForm'
import { useI18n } from '../i18n/I18nContext'
import { useTilt } from '../hooks/useTilt'
import { HeroScene } from '../components/HeroScene'

/** How many hotels each list on the home page shows */
const HOTELS_PER_LIST = 8

export function HomePage() {
  const navigate = useNavigate()
  const { t, language } = useI18n()
  const heroRef = useTilt<HTMLElement>(6)
  // null until the answer arrives, so the banner space is reserved once and then kept or removed
  const [promoted, setPromoted] = useState<PromotedProperty[] | null>(null)
  // The country the guest opened under "Where to?": the banner then shows the ads of hotels in it
  const [country, setCountry] = useState<GeographyCountry | null>(null)

  useEffect(() => {
    let cancelled = false
    const request = country ? promotionAdapter.getHomePromotions(country.id) : promotionAdapter.getHomePromotions()
    request
      .then(result => { if (!cancelled) setPromoted(result.data ?? []) })
      .catch(() => { if (!cancelled) setPromoted([]) })
    return () => { cancelled = true }
  }, [country])

  return (
    <div className="home-page">
      <section ref={heroRef} className="hero" aria-label={t('home.heroLabel')}>
        <HeroScene />
        <div className="hero-content">
          <p className="hero-eyebrow">{t('home.eyebrow')}</p>
          <h1 className="hero-title">{t('home.title')}</h1>
          <p className="hero-subtitle">{t('home.subtitle')}</p>
          <div className="hero-search">
            <SearchForm />
          </div>
        </div>
      </section>

      <HomeWhereTo onCountryChange={setCountry} />

      <div className="container home-promo">
        <PromoCarousel
          items={promoted ?? []}
          loading={promoted === null}
          placeName={country ? geographyName(country, language) : undefined}
        />
      </div>

      <HomePropertyTypes />

      <HomeHotelSection
        title={t('home.topRated')}
        seeAllTo="/search?sort=rating"
        search={{ sort: 'rating', page_size: HOTELS_PER_LIST }}
      />
      <HomeHotelSection
        title={t('home.bestPrices')}
        seeAllTo="/search?sort=price_asc"
        search={{ sort: 'price_asc', page_size: HOTELS_PER_LIST }}
      />

      <section className="home-browse container">
        <button type="button" className="btn btn-primary btn-lg" onClick={() => navigate('/search')}>
          {t('home.browseAll')}
        </button>
      </section>
    </div>
  )
}

export default HomePage
