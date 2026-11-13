import { useEffect, useState } from 'react'
import { useI18n } from '../i18n/I18nContext'
import type { Property } from '../adapters/propertyAdapter'
import { useMatchMedia } from '../hooks/useMatchMedia'
import { MEDIA_QUERIES } from '../utils/breakpoints'
import { toCoordinates } from '../utils/coordinates'
import { PropertiesMap, type MapArea } from './PropertiesMap'
import { PropertyCard } from './PropertyCard'

interface PropertiesMapViewProps {
  properties: Property[]
  onSearchArea?: (area: MapArea) => void
}

/**
 * Birdey mehmanxanalardıń kartası hám dizimi qatar (telefonda ústi-ústine): kartaǵa baǵdarlaw onıń belgisin belgileydi,
 * belgini tańlaw onıń kartasın belgileydi hám sonı kóriwge aylandıradı.
 */
export function PropertiesMapView({ properties, onSearchArea }: PropertiesMapViewProps) {
  const { t } = useI18n()
  const sideBySide = useMatchMedia(MEDIA_QUERIES.desktop)
  const [hoveredId, setHoveredId] = useState<number | null>(null)
  const [selectedId, setSelectedId] = useState<number | null>(null)

  // Belgini tańlaw onıń kartasın kóriwge alıp keledi; tar ekranda karta ornına kartanıń astında turadı
  useEffect(() => {
    if (selectedId === null || !sideBySide) return
    document.querySelector(`[data-property-id="${selectedId}"]`)?.scrollIntoView({ block: 'nearest', behavior: 'smooth' })
  }, [selectedId, sideBySide])

  return (
    <div className="properties-map-view">
      <PropertiesMap
        properties={properties}
        highlightedId={hoveredId}
        onSelectedChange={setSelectedId}
        showSelectedCard={!sideBySide}
        onSearchArea={onSearchArea}
      />
      <ul className="properties-map-list" aria-label={t('map.listLabel')}>
        {properties.map(property => {
          const name = property.translations[0]?.name ?? t('card.unknown')
          const onMap = toCoordinates(property.latitude, property.longitude) !== null
          return (
            <li
              key={property.id}
              data-property-id={property.id}
              data-property-name={name}
              aria-current={sideBySide && property.id === selectedId ? 'true' : undefined}
              className={`properties-map-list-item${sideBySide && property.id === selectedId ? ' properties-map-list-item--active' : ''}`}
              onMouseEnter={() => setHoveredId(property.id)}
              onMouseLeave={() => setHoveredId(null)}
              onFocus={() => setHoveredId(property.id)}
              onBlur={() => setHoveredId(null)}
            >
              <PropertyCard property={property} />
              {!onMap && <p className="geography-picker-hint">{t('map.noPin')}</p>}
            </li>
          )
        })}
      </ul>
    </div>
  )
}
