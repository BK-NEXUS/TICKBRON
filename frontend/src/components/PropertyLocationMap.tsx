import { useEffect, useRef } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { useI18n } from '../i18n/I18nContext'
import { toCoordinates } from '../utils/coordinates'
import { addBaseLayers } from './mapLayers'

interface PropertyLocationMapProps {
  /** As the API sends them: decimal strings, or null when the owner has not set a location */
  latitude: unknown
  longitude: unknown
  name: string
}

const ZOOM = 15

/** A small map of the property page with one pin where the hotel is. Nothing when there is no location. */
export function PropertyLocationMap({ latitude, longitude, name }: PropertyLocationMapProps) {
  const { t } = useI18n()
  const containerRef = useRef<HTMLDivElement>(null)
  const point = toCoordinates(latitude, longitude)
  const lat = point?.lat
  const lng = point?.lng

  useEffect(() => {
    if (lat === undefined || lng === undefined || !containerRef.current) return
    const map = L.map(containerRef.current, { center: [lat, lng], zoom: ZOOM, zoomControl: false, scrollWheelZoom: false })
    L.control.zoom({ zoomInTitle: t('map.zoomIn'), zoomOutTitle: t('map.zoomOut') }).addTo(map)
    addBaseLayers(map, { group: t('map.layerGroup'), street: t('map.layerStreet'), satellite: t('map.layerSatellite') })
    L.marker([lat, lng], { title: name, alt: name, keyboard: false }).addTo(map)
    return () => { map.remove() }
    // Titles follow the language the next time the map is drawn; the pin and tiles do not depend on it
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [lat, lng, name])

  if (!point) return null
  return (
    <div className="property-location-map">
      <div ref={containerRef} className="property-location-map-canvas" role="region" aria-label={t('map.propertyLabel', { name })} />
      <a
        className="property-location-map-link"
        href={`https://www.openstreetmap.org/?mlat=${point.lat}&mlon=${point.lng}#map=16/${point.lat}/${point.lng}`}
        target="_blank"
        rel="noopener noreferrer"
      >
        {t('map.openLarger')}
      </a>
    </div>
  )
}
