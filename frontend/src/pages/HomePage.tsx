import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { promotionAdapter, type PromotedProperty } from '../adapters/promotionAdapter'
import { HomeHotelSection } from '../components/HomeHotelSection'
import { HomePropertyTypes } from '../components/HomePropertyTypes'
import { PromoCarousel } from '../components/PromoCarousel'
import { SearchForm } from '../components/SearchForm'
import { useI18n } from '../i18n/I18nContext'

/** How many hotels each list on the home page shows */
const HOTELS_PER_LIST = 8

export function HomePage() {
  const navigate = useNavigate()
  const { t } = useI18n()
  // null until the answer arrives, so the banner space is reserved once and then kept or removed
  const [promoted, setPromoted] = useState<PromotedProperty[] | null>(null)

  useEffect(() => {
    let cancelled = false
    promotionAdapter.getHomePromotions()
      .then(result => { if (!cancelled) setPromoted(result.data ?? []) })
      .catch(() => { if (!cancelled) setPromoted([]) })
    return () => { cancelled = true }
  }, [])

  return (
    <div className="home-page">
      <section className="hero" aria-label={t('home.heroLabel')}>
        <div className="hero-content">
          <p className="hero-eyebrow">{t('home.eyebrow')}</p>
          <h1 className="hero-title">{t('home.title')}</h1>
          <p className="hero-subtitle">{t('home.subtitle')}</p>
          <div className="hero-search">
            <SearchForm />
          </div>
        </div>
      </section>

      <div className="container home-promo">
        <PromoCarousel items={promoted ?? []} loading={promoted === null} />
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
