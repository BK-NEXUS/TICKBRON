import { useEffect, useState } from 'react'
import { useI18n } from '../i18n/I18nContext'
import { promotionAdapter, type HotelSearchRow } from '../adapters/promotionAdapter'

const SEARCH_DELAY_MS = 300
const MIN_LETTERS = 2

interface PromotionHotelFinderProps {
  onPromote: (hotel: HotelSearchRow) => void
}

/** Find a hotel by name; the "Promote" button of a row starts the create form. */
export function PromotionHotelFinder({ onPromote }: PromotionHotelFinderProps) {
  const { t } = useI18n()
  const [text, setText] = useState('')
  const [hotels, setHotels] = useState<HotelSearchRow[] | null>(null)
  const [searching, setSearching] = useState(false)

  useEffect(() => {
    const term = text.trim()
    if (term.length < MIN_LETTERS) {
      setHotels(null)
      setSearching(false)
      return
    }
    let cancelled = false
    setSearching(true)
    const timer = setTimeout(() => {
      promotionAdapter.searchHotels(term).then(result => {
        if (cancelled) return
        setHotels(result.data ?? [])
        setSearching(false)
      })
    }, SEARCH_DELAY_MS)
    return () => {
      cancelled = true
      clearTimeout(timer)
    }
  }, [text])

  return (
    <section className="promotion-finder" aria-labelledby="promotion-finder-title">
      <h2 id="promotion-finder-title" className="admin-section-title">{t('promoAdmin.findTitle')}</h2>
      <div className="search-bar">
        <label htmlFor="promotion-finder-input" className="search-label">{t('promoAdmin.findLabel')}</label>
        <input
          id="promotion-finder-input"
          type="search"
          className="search-input"
          value={text}
          placeholder={t('promoAdmin.findPlaceholder')}
          autoComplete="off"
          onChange={(e) => setText(e.target.value)}
        />
      </div>
      <div aria-live="polite">
        {searching && <p className="loading-state">{t('promoAdmin.searching')}</p>}
        {!searching && hotels && hotels.length === 0 && <p className="empty-state">{t('promoAdmin.noHotels')}</p>}
      </div>
      {!searching && hotels && hotels.length > 0 && (
        <ul className="promotion-finder-results">
          {hotels.map(hotel => (
            <li key={hotel.id} className="promotion-finder-row">
              <span className="promotion-finder-name">
                <strong>{hotel.name}</strong>
                <span className="promotion-finder-city">{hotel.city}</span>
              </span>
              {hotel.has_running_promotion && <span className="status-badge status-badge--pending">{t('promoAdmin.hasRunning')}</span>}
              <button
                type="button"
                className="btn btn-primary btn-sm"
                disabled={hotel.has_running_promotion}
                aria-label={t('promoAdmin.promoteHotel', { hotel: hotel.name })}
                onClick={() => onPromote(hotel)}
              >
                {t('promoAdmin.promote')}
              </button>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
