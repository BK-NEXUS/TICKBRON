import { useCallback, useEffect, useRef, useState } from 'react'
import type { KeyboardEvent, PointerEvent } from 'react'
import { Link } from 'react-router'
import { ChevronLeft, ChevronRight, House, MapPin, Pause, Play } from 'lucide-react'
import { promotionAdapter, type PromotedProperty } from '../adapters/promotionAdapter'
import { useI18n } from '../i18n/I18nContext'
import { priceIn } from '../utils/price'
import { StarIcon } from './StarIcon'

const ROTATE_MS = 5000
// Reklama 10 ǵa shekem súwret alıp júre aladı: hárbiri usı waqıt kórsetiledi, hám banner olardıń hámmesin kórsetiwge jetetuǵın
// waqıt turadı
const PHOTO_MS = 1800
const MAX_SLIDE_MS = 12000
// Usıdan qısqa kursor háreketi banner ge tap, swipe emes
const SWIPE_MIN_PX = 40

interface PromoCarouselProps {
  items: PromotedProperty[]
  loading?: boolean
  /** Reklama ushın orın (mámleket, region); belgili bolsa bannerdiń ústinde kórsetiledi */
  placeName?: string
}

/** Banner súwretleri: reklamanıń óziki, bolmasa mehmanxananıń muqabası */
function photosOf(item: PromotedProperty): string[] {
  if (item.promo_photos && item.promo_photos.length > 0) return item.promo_photos
  return item.primary_photo?.photo ? [item.primary_photo.photo] : []
}

/** Banner qansha turadı: eń kemi ROTATE_MS, súwret kóp bolsa kóbirek, hesh qashan MAX_SLIDE_MS tan artıq emes */
function stayMs(item: PromotedProperty): number {
  return Math.min(MAX_SLIDE_MS, Math.max(ROTATE_MS, photosOf(item).length * PHOTO_MS))
}

function prefersReducedMotion(): boolean {
  return typeof window.matchMedia === 'function' && window.matchMedia('(prefers-reduced-motion: reduce)').matches
}

/**
 * Tólengen "Reklama" banner i: bir waqıtta bir úlken mehmanxana banner i, ózi aylanadı.
 * Kursor ústine kelgende, klaviatura fokusında, jasırın tabta hám pauza túymesinde toqtaydı, hám
 * háreketti azaytıwdı qáleytuǵın kelwshiler ushın hesh qashan aylanbaydı. Kórsetiwge hesh nárse joq bolsa hesh nárse
 * jasamaydı.
 */
export function PromoCarousel({ items, loading = false, placeName }: PromoCarouselProps) {
  const { t } = useI18n()
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
  const idle = !reducedMotion && !hovered && !focused && !userPaused && !tabHidden
  const canRotate = count > 1 && idle

  const show = useCallback((next: number) => setIndex(((next % count) + count) % count), [count])

  useEffect(() => {
    const onVisibility = () => setTabHidden(document.hidden)
    document.addEventListener('visibilitychange', onVisibility)
    return () => document.removeEventListener('visibilitychange', onVisibility)
  }, [])

  // Taymer hár banner ózgeriwinen keyin qayta baslanadı, sol sebepli qolda kóshiriw toliq 5 sekund aladı
  useEffect(() => {
    if (!canRotate) return
    const timer = setTimeout(() => show(current + 1), stayMs(items[current]))
    return () => clearTimeout(timer)
  }, [canRotate, current, show, items])

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
    <>
    {placeName && <h2 className="promo-carousel-place">{t('promo.inPlace', { place: placeName })}</h2>}
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
            moving={idle}
            position={position + 1}
            total={count}
            onOpen={(event) => {
              // Swipe aqırı siltemege klik te payda etedi: sonda mehmanxananı ashpań
              if (justSwiped.current) {
                justSwiped.current = false
                event.preventDefault()
                return
              }
              void promotionAdapter.trackClick(item.promotion_id)
            }}
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
    </>
  )
}

interface PromoSlideProps {
  item: PromotedProperty
  active: boolean
  /** Súwretler háreketlene aladı (kursor ústinde emes, toqtatılmaǵan, háreketke ruxsat berilgen) */
  moving: boolean
  position: number
  total: number
  onOpen: (event: React.MouseEvent) => void
}

function PromoSlide({ item, active, moving, position, total, onOpen }: PromoSlideProps) {
  const { t, formatMoney, currency } = useI18n()
  // Tańlanǵan valyutadaǵı "dan" bahası (konvertaciya ushın ≈); backend te joq bolsa mehmanxananıń óz bahası
  const shown = priceIn(item, currency)
  const priceText = formatMoney(shown.amount, shown.currency, { minDecimals: 0, maxDecimals: 0 })
  const name = item.translations[0]?.name || t('card.unknown')
  const rating = item.average_rating ?? item.rating ?? 0
  const photos = photosOf(item)
  const [photoIndex, setPhotoIndex] = useState(0)

  // Kórsetilmeytuǵın banner qaytadan baslanadı, sonda keyingi ret birinshi súwretinen ashıladı
  useEffect(() => {
    if (!active) { setPhotoIndex(0); return }
    if (!moving || photos.length < 2) return
    const timer = setTimeout(() => setPhotoIndex(index => (index + 1) % photos.length), PHOTO_MS)
    return () => clearTimeout(timer)
  }, [active, moving, photos.length, photoIndex])

  return (
    <div
      className={`promo-slide${active ? ' promo-slide--active' : ''}`}
      role="group"
      aria-roledescription="slide"
      aria-label={t('promo.slideLabel', { number: position, total })}
      aria-hidden={!active}
    >
      <Link to={`/property/${item.id}`} className="promo-slide-link" tabIndex={active ? 0 : -1} onClick={onOpen}>
        {photos.length > 0 ? (
          photos.map((photo, number) => (
            <img
              key={photo}
              className={`promo-slide-photo${number === photoIndex ? ' promo-slide-photo--on' : ''}`}
              src={photo}
              alt=""
              loading={position === 1 && number === 0 ? 'eager' : 'lazy'}
            />
          ))
        ) : (
          <div className="promo-slide-placeholder" data-testid="promo-image-placeholder">
            <House size={72} aria-hidden="true" />
          </div>
        )}
        <span className="promo-slide-badge">{t('promo.label')}</span>
        {photos.length > 1 && (
          <span className="promo-slide-photodots" aria-hidden="true">
            {photos.map((photo, number) => (
              <span key={photo} className={`promo-slide-photodot${number === photoIndex ? ' promo-slide-photodot--on' : ''}`} />
            ))}
          </span>
        )}
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
              {t('promo.perNight', { price: shown.approximate ? t('charge.approx', { amount: priceText }) : priceText })}
            </span>
          </span>
        </span>
      </Link>
    </div>
  )
}
