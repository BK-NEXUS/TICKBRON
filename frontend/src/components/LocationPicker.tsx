import { useEffect, useRef } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { useI18n } from '../i18n/I18nContext'
import { roundCoordinate, type Coordinates } from '../utils/coordinates'
import { DEFAULT_CENTER, DEFAULT_ZOOM } from './mapTiles'
import { addBaseLayers } from './mapLayers'

interface LocationPickerProps {
  value: Coordinates | null
  onChange: (value: Coordinates | null) => void
}

const PLACED_ZOOM = 14

const fromLatLng = ({ lat, lng }: L.LatLng): Coordinates =>
  ({ lat: roundCoordinate(lat), lng: roundCoordinate(lng, 'lng') })

/**
 * Mehmanxana iyesi mehmanxananıń qayerde ekenin belgileydi: kartaǵa basıw yamasa belgini súyrew.
 * Janındaǵı koordinata maydanları sonı islewdiń klaviatura jolı bolıp qaladı.
 */
export function LocationPicker({ value, onChange }: LocationPickerProps) {
  const { t } = useI18n()
  const containerRef = useRef<HTMLDivElement>(null)
  const mapRef = useRef<L.Map | null>(null)
  const markerRef = useRef<L.Marker | null>(null)
  // Karta bir márte quriladı; onıń handler leri hárdayım eń sońǵı onChange di shaqıradı
  const onChangeRef = useRef(onChange)
  onChangeRef.current = onChange

  useEffect(() => {
    if (!containerRef.current) return
    const map = L.map(containerRef.current, { center: DEFAULT_CENTER, zoom: DEFAULT_ZOOM, zoomControl: false })
    L.control.zoom({ zoomInTitle: t('map.zoomIn'), zoomOutTitle: t('map.zoomOut') }).addTo(map)
    addBaseLayers(map, { group: t('map.layerGroup'), street: t('map.layerStreet'), satellite: t('map.layerSatellite') })
    map.on('click', (event: L.LeafletMouseEvent) => onChangeRef.current(fromLatLng(event.latlng)))
    mapRef.current = map
    return () => {
      map.remove()
      mapRef.current = null
      markerRef.current = null
    }
    // Zoom sarlawhaları bir márte belgilenedi; til ózgeriwi karta keyingi ashılǵanda kúshke kiredi
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const latitude = value?.lat
  const longitude = value?.lng
  useEffect(() => {
    const map = mapRef.current
    if (!map) return
    if (latitude === undefined || longitude === undefined) {
      markerRef.current?.remove()
      markerRef.current = null
      return
    }
    const point = L.latLng(latitude, longitude)
    const label = `${t('map.pickMarker')}: ${latitude}, ${longitude}`
    if (markerRef.current) {
      markerRef.current.setLatLng(point)
      markerRef.current.getElement()?.setAttribute('title', label)
    } else {
      const marker = L.marker(point, { draggable: true, title: label, alt: label, keyboard: false })
      marker.on('dragend', () => onChangeRef.current(fromLatLng(marker.getLatLng())))
      marker.addTo(map)
      markerRef.current = marker
    }
    map.setView(point, Math.max(map.getZoom(), PLACED_ZOOM))
  }, [latitude, longitude, t])

  return (
    <div className="location-picker">
      <div ref={containerRef} className="location-picker-canvas" role="region" aria-label={t('map.pickLabel')} />
      <p className="geography-picker-hint">{t('map.pickHint')}</p>
      {value && (
        <button type="button" className="btn btn-secondary btn-sm" onClick={() => onChange(null)}>{t('map.clear')}</button>
      )}
    </div>
  )
}
