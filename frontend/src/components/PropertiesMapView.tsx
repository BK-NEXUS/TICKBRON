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
 * The map and the list of the same properties side by side (stacked on a phone): pointing at a card marks its pin,
 * choosing a pin marks and scrolls to its card.
 */
export function PropertiesMapView({ properties, onSearchArea }: PropertiesMapViewProps) {
  const { t } = useI18n()
  const sideBySide = useMatchMedia(MEDIA_QUERIES.desktop)
  const [hoveredId, setHoveredId] = useState<number | null>(null)
  const [selectedId, setSelectedId] = useState<number | null>(null)

  // Choosing a pin brings its card into view; on a narrow screen the card sits under the map instead
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
