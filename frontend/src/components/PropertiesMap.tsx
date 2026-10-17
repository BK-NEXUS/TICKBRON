import { useEffect, useMemo, useRef, useState } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { X } from 'lucide-react'
import { useI18n } from '../i18n/I18nContext'
import type { Property } from '../adapters/propertyAdapter'
import { toCoordinates } from '../utils/coordinates'
import { PropertyCard } from './PropertyCard'
import { DEFAULT_CENTER, DEFAULT_ZOOM, TILE_ATTRIBUTION, TILE_URL } from './mapTiles'

// Pins close together overlap; the hovered or focused pin comes to the front, the chosen one stays there
const ACTIVE_Z_OFFSET = 10_000
const RAISED_Z_OFFSET = 20_000

interface PropertiesMapProps {
  properties: Property[]
}

interface Pin {
  property: Property
  lat: number
  lng: number
}

/** Search results as price pins; choosing a pin shows the property card, which opens the property page (rooms, booking). */
export function PropertiesMap({ properties }: PropertiesMapProps) {
  const { t, tp, formatMoney } = useI18n()
  const containerRef = useRef<HTMLDivElement>(null)
  const mapRef = useRef<L.Map | null>(null)
  const markersRef = useRef<Map<number, L.Marker>>(new Map())
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const selectedIdRef = useRef<number | null>(null)
  selectedIdRef.current = selectedId

  const pins = useMemo<Pin[]>(() => properties.flatMap(property => {
    const point = toCoordinates(property.latitude, property.longitude)
    return point ? [{ property, ...point }] : []
  }), [properties])
  const missing = properties.length - pins.length
  const selected = pins.find(pin => pin.property.id === selectedId)?.property ?? null
  const hasPins = pins.length > 0

  // The map is created once, when there is something to show
  useEffect(() => {
    if (!hasPins || !containerRef.current) return
    const map = L.map(containerRef.current, {
      center: DEFAULT_CENTER, zoom: DEFAULT_ZOOM, zoomControl: false, attributionControl: true,
    })
    L.control.zoom({ zoomInTitle: t('map.zoomIn'), zoomOutTitle: t('map.zoomOut') }).addTo(map)
    L.tileLayer(TILE_URL, { attribution: TILE_ATTRIBUTION, maxZoom: 19 }).addTo(map)
    mapRef.current = map
    const markers = markersRef.current
    return () => {
      map.remove()
      mapRef.current = null
      markers.clear()
    }
    // The zoom titles follow the language when the pins are redrawn below; the map itself is not rebuilt
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [hasPins])

  // Pins follow the results and the language
  useEffect(() => {
    const map = mapRef.current
    if (!map) return
    const markers = markersRef.current
    markers.forEach(marker => marker.remove())
    markers.clear()
    for (const { property, lat, lng } of pins) {
      const name = property.translations[0]?.name ?? t('card.unknown')
      const price = formatMoney(property.base_price, property.currency, { minDecimals: 0, maxDecimals: 0 })
      const pin = document.createElement('button')
      pin.type = 'button'
      pin.className = 'map-pin'
      pin.textContent = price
      pin.setAttribute('aria-label', t('map.pinLabel', { name, price }))
      pin.addEventListener('click', () => setSelectedId(property.id))
      const icon = L.divIcon({ html: pin, className: 'map-pin-icon', iconSize: undefined })
      const marker = L.marker([lat, lng], { icon, keyboard: false }).addTo(map)
      const raise = () => marker.setZIndexOffset(RAISED_Z_OFFSET)
      const lower = () => marker.setZIndexOffset(selectedIdRef.current === property.id ? ACTIVE_Z_OFFSET : 0)
      pin.addEventListener('mouseenter', raise)
      pin.addEventListener('focus', raise)
      pin.addEventListener('mouseleave', lower)
      pin.addEventListener('blur', lower)
      markers.set(property.id, marker)
    }
    const points = pins.map(pin => L.latLng(pin.lat, pin.lng))
    if (points.length === 1) map.setView(points[0], 13)
    else if (points.length > 1) map.fitBounds(L.latLngBounds(points), { padding: [48, 48], maxZoom: 14 })
  }, [pins, t, formatMoney, hasPins])

  // The chosen pin is marked; a new search that drops it clears the card
  useEffect(() => {
    markersRef.current.forEach((marker, id) => {
      marker.getElement()?.classList.toggle('map-pin--active', id === selectedId)
      marker.setZIndexOffset(id === selectedId ? ACTIVE_Z_OFFSET : 0)
    })
  }, [selectedId, pins])
  useEffect(() => {
    if (selectedId !== null && !selected) setSelectedId(null)
  }, [selectedId, selected])

  if (!hasPins) {
    return <p className="search-results-map-empty" role="status">{t('map.noLocations')}</p>
  }

  return (
    <div className="properties-map">
      <div ref={containerRef} className="properties-map-canvas" role="region" aria-label={t('map.label')} />
      {missing > 0 && <p className="geography-picker-hint">{tp('map.someMissing', missing)}</p>}
      {selected ? (
        <div className="properties-map-card" data-testid="map-selected-card">
          <button type="button" className="properties-map-card-close btn btn-secondary btn-sm" onClick={() => setSelectedId(null)}>
            <X size={16} aria-hidden="true" /> {t('map.closeCard')}
          </button>
          <PropertyCard property={selected} />
        </div>
      ) : (
        <p className="geography-picker-hint">{t('map.selectHint')}</p>
      )}
    </div>
  )
}
