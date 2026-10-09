import { useNavigate } from 'react-router-dom'
import { SearchForm } from '../components/SearchForm'
import { useI18n } from '../i18n/I18nContext'
import type { MessageKey } from '../i18n/messages/en'
import { ArrowRight, BadgeCheck, Building, Building2, Globe, Headset, Hotel, House, MapPin, ShieldCheck, Smartphone, Star, type LucideIcon } from 'lucide-react'

// Mock data for homepage content
// TODO: Replace with real data from backend API when available
const FEATURED_DESTINATIONS = [
  { id: 1, name: 'Paris', country: 'France', propertyCount: 1250 },
  { id: 2, name: 'Tokyo', country: 'Japan', propertyCount: 980 },
  { id: 3, name: 'New York', country: 'USA', propertyCount: 1100 },
  { id: 4, name: 'London', country: 'UK', propertyCount: 890 },
]

interface PropertyType {
  id: number
  nameKey: MessageKey
  icon: LucideIcon
  descriptionKey: MessageKey
}

const PROPERTY_TYPES: PropertyType[] = [
  { id: 1, nameKey: 'home.type.apartments', icon: Building2, descriptionKey: 'home.type.apartmentsText' },
  { id: 2, nameKey: 'home.type.houses', icon: House, descriptionKey: 'home.type.housesText' },
  { id: 3, nameKey: 'home.type.villas', icon: Hotel, descriptionKey: 'home.type.villasText' },
  { id: 4, nameKey: 'home.type.studios', icon: Building, descriptionKey: 'home.type.studiosText' },
]

interface Feature {
  id: number
  icon: LucideIcon
  titleKey: MessageKey
  descriptionKey: MessageKey
}

const FEATURES: Feature[] = [
  { id: 1, icon: BadgeCheck, titleKey: 'home.feature.verified', descriptionKey: 'home.feature.verifiedText' },
  { id: 2, icon: ShieldCheck, titleKey: 'home.feature.payments', descriptionKey: 'home.feature.paymentsText' },
  { id: 3, icon: Headset, titleKey: 'home.feature.support', descriptionKey: 'home.feature.supportText' },
  { id: 4, icon: Star, titleKey: 'home.feature.price', descriptionKey: 'home.feature.priceText' },
  { id: 5, icon: Globe, titleKey: 'home.feature.global', descriptionKey: 'home.feature.globalText' },
  { id: 6, icon: Smartphone, titleKey: 'home.feature.booking', descriptionKey: 'home.feature.bookingText' },
]

const TESTIMONIALS = [
  {
    id: 1,
    name: 'Sarah Johnson',
    location: 'New York, USA',
    text: 'TICKBRON made finding our family vacation rental so easy. The property was exactly as described!',
    rating: 5,
  },
  {
    id: 2,
    name: 'Michael Chen',
    location: 'Singapore',
    text: 'Best platform for business travel. Always reliable and great customer service.',
    rating: 5,
  },
  {
    id: 3,
    name: 'Emma Wilson',
    location: 'London, UK',
    text: 'Found my dream apartment through TICKBRON. The verification process gave me peace of mind.',
    rating: 5,
  },
]

const STATS: Array<{ value: string; labelKey: MessageKey }> = [
  { value: '50K+', labelKey: 'home.stat.properties' },
  { value: '100K+', labelKey: 'home.stat.guests' },
  { value: '120+', labelKey: 'home.stat.countries' },
  { value: '4.9', labelKey: 'home.stat.rating' },
]

export function HomePage() {
  const navigate = useNavigate()
  const { t, tp } = useI18n()
  return (
    <div className="home-page">
      {/* Hero Section */}
      <section className="hero" aria-label={t('home.heroLabel')}>
        <div className="hero-content">
          <p className="hero-eyebrow">{t('home.eyebrow')}</p>
          <h1 className="hero-title">{t('home.title')}</h1>
          <p className="hero-subtitle">{t('home.subtitle')}</p>
          <div className="hero-search">
            <SearchForm />
          </div>
          <div className="hero-stats" role="region" aria-label={t('home.statsLabel')}>
            {STATS.map((stat) => (
              <div key={stat.labelKey} className="hero-stat">
                <div className="hero-stat-value">{stat.value}</div>
                <div className="hero-stat-label">{t(stat.labelKey)}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Featured Destinations */}
      <section className="destinations" aria-labelledby="destinations-title">
        <div className="container">
          <h2 id="destinations-title" className="section-title">{t('home.destinations.title')}</h2>
          <p className="section-subtitle">{t('home.destinations.subtitle')}</p>
          <div className="destinations-grid" role="list">
            {FEATURED_DESTINATIONS.map((destination) => (
              <article key={destination.id} className="destination-card" role="listitem">
                <div className="destination-image" aria-hidden="true">
                  <MapPin size={28} />
                </div>
                <div className="destination-info">
                  <h3 className="destination-name">{destination.name}</h3>
                  <p className="destination-country">{destination.country}</p>
                  <p className="destination-count">{tp('home.properties', destination.propertyCount)}</p>
                </div>
              </article>
            ))}
          </div>
        </div>
      </section>

      {/* Property Types */}
      <section className="property-types" aria-labelledby="property-types-title">
        <div className="container">
          <h2 id="property-types-title" className="section-title">{t('home.types.title')}</h2>
          <p className="section-subtitle">{t('home.types.subtitle')}</p>
          <div className="property-types-grid" role="list">
            {PROPERTY_TYPES.map((type) => (
              <article key={type.id} className="property-type-card" role="listitem">
                <div className="property-type-icon" aria-hidden="true">
                  <type.icon size={28} />
                </div>
                <h3 className="property-type-name">{t(type.nameKey)}</h3>
                <p className="property-type-description">{t(type.descriptionKey)}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="features" aria-labelledby="features-title">
        <div className="container">
          <h2 id="features-title" className="section-title">{t('home.features.title')}</h2>
          <p className="section-subtitle">{t('home.features.subtitle')}</p>
          <div className="features-grid" role="list">
            {FEATURES.map((feature) => (
              <div key={feature.id} className="feature-card" role="listitem">
                <div className="feature-icon" aria-hidden="true">
                  <feature.icon size={24} />
                </div>
                <h3 className="feature-title">{t(feature.titleKey)}</h3>
                <p className="feature-description">{t(feature.descriptionKey)}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Testimonials */}
      <section className="testimonials" aria-labelledby="testimonials-title">
        <div className="container">
          <h2 id="testimonials-title" className="section-title">{t('home.testimonials.title')}</h2>
          <p className="section-subtitle">{t('home.testimonials.subtitle')}</p>
          <div className="testimonials-grid" role="list">
            {TESTIMONIALS.map((testimonial) => (
              <article key={testimonial.id} className="testimonial-card" role="listitem">
                <div className="testimonial-rating" aria-label={t('home.testimonials.rating', { rating: testimonial.rating })}>
                  {Array.from({ length: testimonial.rating }).map((_, index) => (
                    <Star key={index} size={16} />
                  ))}
                </div>
                <p className="testimonial-text">"{testimonial.text}"</p>
                <div className="testimonial-author">
                  <div className="testimonial-name">{testimonial.name}</div>
                  <div className="testimonial-location">{testimonial.location}</div>
                </div>
              </article>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="cta" aria-labelledby="cta-title">
        <div className="container">
          <div className="cta-content">
            <h2 id="cta-title" className="cta-title">{t('home.cta.title')}</h2>
            <p className="cta-subtitle">{t('home.cta.subtitle')}</p>
            <div className="cta-buttons">
              <button className="btn btn-primary btn-large" onClick={() => navigate('/search')}>
                {t('home.cta.browse')}
                <ArrowRight size={18} />
              </button>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}

export default HomePage
