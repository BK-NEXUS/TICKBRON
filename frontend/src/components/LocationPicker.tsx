import { useEffect, useRef } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { useI18n } from '../i18n/I18nContext'
import { roundCoordinate, type Coordinates } from '../utils/coordinates'
import { DEFAULT_CENTER, DEFAULT_ZOOM, TILE_ATTRIBUTION, TILE_URL } from './mapTiles'

interface LocationPickerProps {
  value: Coordinates | null
  onChange: (value: Coordinates | null) => void
}

const PLACED_ZOOM = 14

const fromLatLng = ({ lat, lng }: L.LatLng): Coordinates =>
  ({ lat: roundCoordinate(lat), lng: roundCoordinate(lng, 'lng') })

/**
 * A hotel owner marks where the property is: click the map or drag the pin.
 * The coordinate fields next to it stay the keyboard way to do the same.
 */
export function LocationPicker({ value, onChange }: LocationPickerProps) {
  const { t } = useI18n()
  const containerRef = useRef<HTMLDivElement>(null)
  const mapRef = useRef<L.Map | null>(null)
  const markerRef = useRef<L.Marker | null>(null)
  // The map is built once; its handlers always call the latest onChange
  const onChangeRef = useRef(onChange)
  onChangeRef.current = onChange

  useEffect(() => {
    if (!containerRef.current) return
    const map = L.map(containerRef.current, { center: DEFAULT_CENTER, zoom: DEFAULT_ZOOM, zoomControl: false })
    L.control.zoom({ zoomInTitle: t('map.zoomIn'), zoomOutTitle: t('map.zoomOut') }).addTo(map)
    L.tileLayer(TILE_URL, { attribution: TILE_ATTRIBUTION, maxZoom: 19 }).addTo(map)
    map.on('click', (event: L.LeafletMouseEvent) => onChangeRef.current(fromLatLng(event.latlng)))
    mapRef.current = map
    return () => {
      map.remove()
      mapRef.current = null
      markerRef.current = null
    }
    // Zoom titles are set once; a language change takes effect the next time the map opens
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
