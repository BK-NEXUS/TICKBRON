import { MapPin } from 'lucide-react'
import { useI18n } from '../i18n/I18nContext'

interface ShowOnMapCardProps {
  onShow: () => void
}

/** The card above the filters that opens the results on the map. */
export function ShowOnMapCard({ onShow }: ShowOnMapCardProps) {
  const { t } = useI18n()
  return (
    <div className="show-on-map-card">
      <MapPin size={28} aria-hidden="true" className="show-on-map-card-icon" />
      <p className="show-on-map-card-text">{t('map.showOnMapText')}</p>
      <button type="button" className="btn btn-secondary btn-sm" onClick={onShow}>{t('map.showOnMap')}</button>
    </div>
  )
}
