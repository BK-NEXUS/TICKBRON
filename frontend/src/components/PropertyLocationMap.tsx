import { useEffect, useRef } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { useI18n } from '../i18n/I18nContext'
import { toCoordinates } from '../utils/coordinates'
import { addBaseLayers } from './mapLayers'

interface PropertyLocationMapProps {
  /** API jibergenindey: onlıq qatarlar, yamasa iye orın belgilemegen bolsa null */
  latitude: unknown
  longitude: unknown
  name: string
}

const ZOOM = 15
// Ilova sızadı: Leaflet tiń óz belgisi súwret fayl, onıń mánzilin build buzadı, sol sebepli mehmanxana beti belgisiz kórinedi
const PIN = L.divIcon({ html: '<span class="map-pin-dot"></span>', className: 'map-pin-icon', iconSize: undefined })

/** Mehmanxananıń bir belgi menen mehmanxana betindegi kishi kartası. Orın joq bolsa hesh nárse. */
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
    L.marker([lat, lng], { icon: PIN, title: name, alt: name, keyboard: false }).addTo(map)
    return () => { map.remove() }
    // Sarlawhalar karta keyingi sızılǵanda tilge ılayıq boladı; belgi hám tayllar oǵan baylanıslı emes
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
