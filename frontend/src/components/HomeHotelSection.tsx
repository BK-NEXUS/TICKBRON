import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { ChevronRight } from 'lucide-react'
import { propertyAdapter, type Property, type SearchParams } from '../adapters/propertyAdapter'
import { useI18n } from '../i18n/I18nContext'
import { PropertyCard } from './PropertyCard'

const SKELETON_CARDS = 4

interface HomeHotelSectionProps {
  title: string
  /** The search page showing the same list, with its own filters */
  seeAllTo: string
  /** What this list is: a sort order and how many hotels */
  search: SearchParams
}

/**
 * One list of real hotels on the home page (for example "Top rated"): a heading, a grid of hotel cards
 * and a link to the full list. While loading it shows card skeletons; with an error or no hotels it
 * shows nothing, so the home page never has an empty frame.
 */
export function HomeHotelSection({ title, seeAllTo, search }: HomeHotelSectionProps) {
  const { t } = useI18n()
  const [hotels, setHotels] = useState<Property[] | null>(null)
  const [failed, setFailed] = useState(false)

  // The search object is rebuilt on every render of the page, so the request is keyed by its content
  const key = JSON.stringify(search)
  useEffect(() => {
    let cancelled = false
    propertyAdapter.searchProperties(JSON.parse(key) as SearchParams)
      .then((response) => {
        if (cancelled) return
        if (response.data) setHotels(response.data.results)
        else setFailed(true)
      })
      .catch(() => { if (!cancelled) setFailed(true) })
    return () => { cancelled = true }
  }, [key])

  if (failed || (hotels !== null && hotels.length === 0)) return null

  if (hotels === null) {
    return (
      <section className="home-hotels container" role="status" aria-label={t('home.section.loading')}>
        <div className="home-hotel-grid" aria-hidden="true">
          {Array.from({ length: SKELETON_CARDS }).map((_, index) => (
            <div key={index} className="property-card skeleton-card">
              <div className="skeleton skeleton-image"></div>
              <div className="skeleton-card-content">
                <div className="skeleton skeleton-text"></div>
                <div className="skeleton skeleton-text"></div>
              </div>
            </div>
          ))}
        </div>
      </section>
    )
  }

  const headingId = `home-hotels-${seeAllTo.replace(/[^a-z0-9]+/gi, '-')}`
  return (
    <section className="home-hotels container" aria-labelledby={headingId}>
      <div className="home-hotels-header">
        <h2 id={headingId} className="home-hotels-title">{title}</h2>
        <Link to={seeAllTo} className="home-hotels-link">
          {t('home.section.seeAll')} <ChevronRight size={16} aria-hidden="true" />
        </Link>
      </div>
      <div className="home-hotel-grid">
        {hotels.map((hotel) => <PropertyCard key={hotel.id} property={hotel} />)}
      </div>
    </section>
  )
}
