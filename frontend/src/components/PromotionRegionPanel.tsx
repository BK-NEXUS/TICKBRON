import { useCallback, useEffect, useState } from 'react'
import { useI18n } from '../i18n/I18nContext'
import { promotionAdapter, type PromotionRegion } from '../adapters/promotionAdapter'
import { geographyName } from '../adapters/geographyAdapter'

interface PromotionRegionPanelProps {
  /** Tómendegi dizim shekemlengen region, yamasa hámmesi ushın null */
  selected: number | null
  onSelect: (regionId: number | null) => void
  /** Reklamalar ózgergende ózgeredi, sonda sanlar qayta oqıladı */
  refreshKey: number
}

/** Region boyınsha reklama paneli: hár regionda neshe reklama isleydi hám olardı qaysı mehmanxanalar júrgizedi. */
export function PromotionRegionPanel({ selected, onSelect, refreshKey }: PromotionRegionPanelProps) {
  const { t, language } = useI18n()
  const [regions, setRegions] = useState<PromotionRegion[] | null>(null)
  const [failed, setFailed] = useState(false)

  // Try Again túymesi sıyaqlı isleydi
  const load = useCallback(async () => {
    setFailed(false)
    const result = await promotionAdapter.getRegionPanel()
    if (result.data) setRegions(result.data)
    else setFailed(true)
  }, [])

  useEffect(() => { void load() }, [load, refreshKey])

  if (failed) {
    return (
      <div className="alert alert-error" role="alert">
        <p>{t('promoAdmin.regionsError')}</p>
        <button type="button" className="btn btn-secondary btn-sm" onClick={() => void load()}>{t('common.tryAgain')}</button>
      </div>
    )
  }
  if (regions === null) return <p className="loading-state" role="status">{t('promoAdmin.regionsLoading')}</p>

  return (
    <section className="promotion-regions" aria-labelledby="promotion-regions-title">
      <h3 id="promotion-regions-title" className="admin-section-title">{t('promoAdmin.regionsTitle')}</h3>
      <p className="admin-view-subtitle">{t('promoAdmin.regionsHint')}</p>
      <ul className="promotion-region-list">
        <li>
          <button
            type="button"
            className={`promotion-region${selected === null ? ' promotion-region--selected' : ''}`}
            aria-pressed={selected === null}
            onClick={() => onSelect(null)}
          >
            <span className="promotion-region-name">{t('promoAdmin.regionAll')}</span>
          </button>
        </li>
        {regions.map(region => (
          <li key={region.id}>
            <button
              type="button"
              className={`promotion-region${selected === region.id ? ' promotion-region--selected' : ''}`}
              aria-pressed={selected === region.id}
              onClick={() => onSelect(selected === region.id ? null : region.id)}
            >
              <span className="promotion-region-name">{geographyName(region, language)}</span>
              {region.running + region.waiting === 0 ? (
                <span className="promotion-region-empty">{t('promoAdmin.regionNoAds')}</span>
              ) : (
                <span className="promotion-region-counts">
                  <span>{t('promoAdmin.regionRunning', { count: region.running })}</span>
                  {region.waiting > 0 && <span>{t('promoAdmin.regionWaiting', { count: region.waiting })}</span>}
                </span>
              )}
              {region.hotels.length > 0 && (
                <span className="promotion-region-hotels">{region.hotels.map(hotel => hotel.name).join(', ')}</span>
              )}
            </button>
          </li>
        ))}
      </ul>
    </section>
  )
}
