import { useCallback, useEffect, useRef, useState } from 'react'
import type { KeyboardEvent, PointerEvent } from 'react'
import { Link } from 'react-router-dom'
import { ChevronLeft, ChevronRight, House, MapPin, Pause, Play } from 'lucide-react'
import { promotionAdapter, type PromotedProperty } from '../adapters/promotionAdapter'
import { useI18n } from '../i18n/I18nContext'
import { StarIcon } from './StarIcon'

const ROTATE_MS = 5000
// A pointer movement shorter than this is a tap on the banner, not a swipe
const SWIPE_MIN_PX = 40

interface PromoCarouselProps {
  items: PromotedProperty[]
  loading?: boolean
}

function prefersReducedMotion(): boolean {
  return typeof window.matchMedia === 'function' && window.matchMedia('(prefers-reduced-motion: reduce)').matches
}

/**
 * The paid "Reklama" banner: one big hotel banner at a time that rotates by itself.
 * It pauses on hover, keyboard focus, a hidden tab and the pause button, and never rotates
 * for visitors who prefer reduced motion. With nothing to show it renders nothing.
 */
export function PromoCarousel({ items, loading = false }: PromoCarouselProps) {
  const { t, formatMoney } = useI18n()
  const [index, setIndex] = useState(0)
  const [hovered, setHovered] = useState(false)
  const [focused, setFocused] = useState(false)
  const [userPaused, setUserPaused] = useState(false)
  const [tabHidden, setTabHidden] = useState(() => document.hidden)
  const [reducedMotion] = useState(prefersReducedMotion)
  const swipeStartX = useRef<number | null>(null)
  const justSwiped = useRef(false)

  const count = items.length
  const current = count === 0 ? 0 : Math.min(index, count - 1)
  const canRotate = count > 1 && !reducedMotion && !hovered && !focused && !userPaused && !tabHidden

  const show = useCallback((next: number) => setIndex(((next % count) + count) % count), [count])

  useEffect(() => {
    const onVisibility = () => setTabHidden(document.hidden)
    document.addEventListener('visibilitychange', onVisibility)
    return () => document.removeEventListener('visibilitychange', onVisibility)
  }, [])

  // The timer restarts after every change of banner, so a manual move gets a full 5 seconds
  useEffect(() => {
    if (!canRotate) return
    const timer = setTimeout(() => show(current + 1), ROTATE_MS)
    return () => clearTimeout(timer)
  }, [canRotate, current, show])

  if (loading && count === 0) {
    return (
      <div className="promo-carousel promo-carousel--loading" role="status" aria-label={t('promo.loading')} />
    )
  }
  if (count === 0) return null

  const onKeyDown = (event: KeyboardEvent) => {
    if (event.key === 'ArrowRight') show(current + 1)
    if (event.key === 'ArrowLeft') show(current - 1)
  }

  const onPointerDown = (event: PointerEvent) => {
    swipeStartX.current = event.clientX
  }

  const onPointerUp = (event: PointerEvent) => {
    if (swipeStartX.current === null) return
    const distance = event.clientX - swipeStartX.current
    swipeStartX.current = null
    if (!Number.isFinite(distance) || Math.abs(distance) < SWIPE_MIN_PX) return
    justSwiped.current = true
    show(distance < 0 ? current + 1 : current - 1)
  }

  return (
    <section
      className="promo-carousel"
      role="region"
      aria-roledescription="carousel"
      aria-label={t('promo.carouselLabel')}
      onKeyDown={onKeyDown}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      onFocus={() => setFocused(true)}
      onBlur={() => setFocused(false)}
    >
      <div
        className="promo-carousel-viewport"
        onPointerDown={onPointerDown}
        onPointerUp={onPointerUp}
        onPointerCancel={() => { swipeStartX.current = null }}
      >
        {items.map((item, position) => (
          <PromoSlide
            key={item.promotion_id}
            item={item}
            active={position === current}
            position={position + 1}
            total={count}
            onOpen={(event) => {
              // The end of a swipe also fires a click on the link: do not open the hotel then
              if (justSwiped.current) {
                justSwiped.current = false
                event.preventDefault()
                return
              }
              void promotionAdapter.trackClick(item.promotion_id)
            }}
            formatPrice={(value, currency) => formatMoney(value, currency, { minDecimals: 0, maxDecimals: 0 })}
          />
        ))}
      </div>

      {count > 1 && (
        <>
          <button
            type="button"
            className="promo-carousel-nav promo-carousel-nav--prev"
            aria-label={t('promo.previous')}
            onClick={() => show(current - 1)}
          >
            <ChevronLeft size={22} aria-hidden="true" />
          </button>
          <button
            type="button"
            className="promo-carousel-nav promo-carousel-nav--next"
            aria-label={t('promo.next')}
            onClick={() => show(current + 1)}
          >
            <ChevronRight size={22} aria-hidden="true" />
          </button>
          <div className="promo-carousel-controls">
            <div className="promo-carousel-dots" role="tablist">
              {items.map((item, position) => (
                <button
                  key={item.promotion_id}
                  type="button"
                  role="tab"
                  className={`promo-carousel-dot${position === current ? ' promo-carousel-dot--active' : ''}`}
                  aria-selected={position === current}
                  aria-label={t('promo.goTo', { number: position + 1 })}
                  onClick={() => show(position)}
                />
              ))}
            </div>
            {!reducedMotion && (
              <button
                type="button"
                className="promo-carousel-pause"
                aria-label={userPaused ? t('promo.play') : t('promo.pause')}
                onClick={() => setUserPaused((paused) => !paused)}
              >
                {userPaused ? <Play size={16} aria-hidden="true" /> : <Pause size={16} aria-hidden="true" />}
              </button>
            )}
          </div>
        </>
      )}
    </section>
  )
}

interface PromoSlideProps {
  item: PromotedProperty
  active: boolean
  position: number
  total: number
  onOpen: (event: React.MouseEvent) => void
  formatPrice: (value: number, currency: string) => string
}

function PromoSlide({ item, active, position, total, onOpen, formatPrice }: PromoSlideProps) {
  const { t } = useI18n()
  const name = item.translations[0]?.name || t('card.unknown')
  const rating = item.average_rating ?? item.rating ?? 0
  const photo = item.primary_photo?.photo

  return (
    <div
      className={`promo-slide${active ? ' promo-slide--active' : ''}`}
      role="group"
      aria-roledescription="slide"
      aria-label={t('promo.slideLabel', { number: position, total })}
      aria-hidden={!active}
    >
      <Link to={`/property/${item.id}`} className="promo-slide-link" tabIndex={active ? 0 : -1} onClick={onOpen}>
        {photo ? (
          <img className="promo-slide-photo" src={photo} alt="" loading={position === 1 ? 'eager' : 'lazy'} />
        ) : (
          <div className="promo-slide-placeholder" data-testid="promo-image-placeholder">
            <House size={72} aria-hidden="true" />
          </div>
        )}
        <span className="promo-slide-badge">{t('promo.label')}</span>
        <span className="promo-slide-info">
          <span className="promo-slide-name">{name}</span>
          <span className="promo-slide-meta">
            <span className="promo-slide-location">
              <MapPin size={15} aria-hidden="true" /> {item.city}
            </span>
            {rating > 0 && (
              <span className="promo-slide-rating">
                <StarIcon /> {rating.toFixed(1)}
              </span>
            )}
            <span className="promo-slide-price">
              {t('promo.perNight', { price: formatPrice(Number(item.base_price), item.currency) })}
            </span>
          </span>
        </span>
      </Link>
    </div>
  )
}
