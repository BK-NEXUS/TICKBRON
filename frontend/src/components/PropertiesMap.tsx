import { useEffect, useMemo, useRef, useState } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import 'leaflet.markercluster'
import 'leaflet.markercluster/dist/MarkerCluster.css'
import { X } from 'lucide-react'
import { useI18n } from '../i18n/I18nContext'
import { priceIn } from '../utils/price'
import type { Property } from '../adapters/propertyAdapter'
import { toCoordinates } from '../utils/coordinates'
import { PropertyCard } from './PropertyCard'
import { DEFAULT_CENTER, DEFAULT_ZOOM } from './mapTiles'
import { addBaseLayers } from './mapLayers'

// Pins close together overlap; the hovered or focused pin comes to the front, the chosen one stays there
const ACTIVE_Z_OFFSET = 10_000
/** Groups of this many pins or more get a bigger bubble */
const CLUSTER_MEDIUM = 10
const CLUSTER_LARGE = 50
const RAISED_Z_OFFSET = 20_000

/** The visible part of the map as the backend's search takes it: a centre and a radius in whole kilometres (1-100). */
export interface MapArea {
  lat: number
  lng: number
  radius: number
}

interface PropertiesMapProps {
  properties: Property[]
  /** The property a list next to the map is pointing at */
  highlightedId?: number | null
  /** Told which pin the guest chose (null when the choice is cleared) */
  onSelectedChange?: (id: number | null) => void
  /** False when a list next to the map shows the chosen property instead */
  showSelectedCard?: boolean
  /** Offers "Search this area" once the guest has moved the map */
  onSearchArea?: (area: MapArea) => void
}

const MIN_RADIUS_KM = 1
const MAX_RADIUS_KM = 100

function visibleArea(map: L.Map): MapArea {
  const bounds = map.getBounds()
  const center = bounds.getCenter()
  const halfWidth = map.distance(center, L.latLng(center.lat, bounds.getEast()))
  const halfHeight = map.distance(center, L.latLng(bounds.getNorth(), center.lng))
  const radius = Math.ceil(Math.max(halfWidth, halfHeight) / 1000)
  return {
    lat: Math.round(center.lat * 1e6) / 1e6,
    lng: Math.round(center.lng * 1e6) / 1e6,
    radius: Math.min(MAX_RADIUS_KM, Math.max(MIN_RADIUS_KM, radius)),
  }
}

interface Pin {
  property: Property
  lat: number
  lng: number
}

/** Search results as price pins; choosing a pin shows the property card, which opens the property page (rooms, booking). */
export function PropertiesMap({
  properties, highlightedId = null, onSelectedChange, showSelectedCard = true, onSearchArea,
}: PropertiesMapProps) {
  const { t, tp, formatMoney, currency } = useI18n()
  const containerRef = useRef<HTMLDivElement>(null)
  const mapRef = useRef<L.Map | null>(null)
  const groupRef = useRef<L.MarkerClusterGroup | null>(null)
  const markersRef = useRef<Map<number, L.Marker>>(new Map())
  const pinsRef = useRef<Map<number, HTMLButtonElement>>(new Map())
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const selectedIdRef = useRef<number | null>(null)
  selectedIdRef.current = selectedId
  const highlightedIdRef = useRef<number | null>(null)
  highlightedIdRef.current = highlightedId
  const [moved, setMoved] = useState(false)
  // True while the page itself moves the map (new results), so that is not taken for the guest moving it
  const programmaticRef = useRef(false)
  // The pin buttons are built once per set of results: they must reach the latest callback
  const onSelectedChangeRef = useRef(onSelectedChange)
  onSelectedChangeRef.current = onSelectedChange
  const select = (id: number | null) => {
    setSelectedId(id)
    onSelectedChangeRef.current?.(id)
  }

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
    addBaseLayers(map, { group: t('map.layerGroup'), street: t('map.layerStreet'), satellite: t('map.layerSatellite') })
    // Pins that would cover each other become one numbered group; clicking it zooms in
    const group = L.markerClusterGroup({
      showCoverageOnHover: false,
      maxClusterRadius: 40,
      iconCreateFunction: cluster => {
        const count = cluster.getChildCount()
        const badge = document.createElement('button')
        badge.type = 'button'
        badge.className = `map-cluster${count >= CLUSTER_LARGE ? ' map-cluster--lg' : count >= CLUSTER_MEDIUM ? ' map-cluster--md' : ''}`
        badge.textContent = String(count)
        badge.setAttribute('aria-label', tp('map.clusterLabel', count))
        return L.divIcon({ html: badge, className: 'map-pin-icon', iconSize: undefined })
      },
    }).addTo(map)
    const onUserMove = () => { if (!programmaticRef.current) setMoved(true) }
    map.on('dragend', onUserMove)
    map.on('zoomend', onUserMove)
    mapRef.current = map
    groupRef.current = group
    const markers = markersRef.current
    const pinButtons = pinsRef.current
    return () => {
      map.remove()
      mapRef.current = null
      groupRef.current = null
      markers.clear()
      pinButtons.clear()
    }
    // The zoom titles follow the language when the pins are redrawn below; the map itself is not rebuilt
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [hasPins])

  // Pins follow the results and the language
  useEffect(() => {
    const map = mapRef.current
    const group = groupRef.current
    if (!map || !group) return
    const markers = markersRef.current
    group.clearLayers()
    markers.clear()
    pinsRef.current.clear()
    for (const { property, lat, lng } of pins) {
      const name = property.translations[0]?.name ?? t('card.unknown')
      // The "from" price in the chosen currency (≈ for a conversion)
      const shown = priceIn(property, currency)
      const amount = formatMoney(shown.amount, shown.currency, { minDecimals: 0, maxDecimals: 0 })
      const price = shown.approximate ? t('charge.approx', { amount }) : amount
      const pin = document.createElement('button')
      pin.type = 'button'
      pin.className = 'map-pin'
      pin.textContent = price
      pin.setAttribute('aria-label', t('map.pinLabel', { name, price }))
      pin.addEventListener('click', () => select(property.id))
      const icon = L.divIcon({ html: pin, className: 'map-pin-icon', iconSize: undefined })
      const marker = L.marker([lat, lng], { icon, keyboard: false })
      group.addLayer(marker)
      pinsRef.current.set(property.id, pin)
      const raise = () => marker.setZIndexOffset(RAISED_Z_OFFSET)
      const lower = () => marker.setZIndexOffset(
        highlightedIdRef.current === property.id ? RAISED_Z_OFFSET : selectedIdRef.current === property.id ? ACTIVE_Z_OFFSET : 0)
      pin.addEventListener('mouseenter', raise)
      pin.addEventListener('focus', raise)
      pin.addEventListener('mouseleave', lower)
      pin.addEventListener('blur', lower)
      markers.set(property.id, marker)
    }
    const points = pins.map(pin => L.latLng(pin.lat, pin.lng))
    programmaticRef.current = true
    if (points.length === 1) map.setView(points[0], 13, { animate: false })
    else if (points.length > 1) map.fitBounds(L.latLngBounds(points), { padding: [48, 48], maxZoom: 14, animate: false })
    programmaticRef.current = false
    setMoved(false)
  }, [pins, t, tp, formatMoney, currency, hasPins])

  // The chosen pin is marked; a new search that drops it clears the card
  useEffect(() => {
    // The class sits on the pin button itself: it stays right while a group hides and shows the marker
    pinsRef.current.forEach((pin, id) => {
      pin.classList.toggle('map-pin--active', id === selectedId)
      pin.classList.toggle('map-pin--hover', id === highlightedId)
    })
    markersRef.current.forEach((marker, id) => marker.setZIndexOffset(
      id === highlightedId ? RAISED_Z_OFFSET : id === selectedId ? ACTIVE_Z_OFFSET : 0))
  }, [selectedId, highlightedId, pins])
  useEffect(() => {
    if (selectedId !== null && !selected) select(null)
    // `select` only sets state and calls the callback; it is not a dependency on purpose
  }, [selectedId, selected])

  if (!hasPins) {
    return <p className="search-results-map-empty" role="status">{t('map.noLocations')}</p>
  }

  return (
    <div className="properties-map">
      <div className="properties-map-frame">
        <div ref={containerRef} className="properties-map-canvas" role="region" aria-label={t('map.label')} />
        {onSearchArea && moved && mapRef.current && (
          <button type="button" className="properties-map-search-area btn btn-primary btn-sm"
            onClick={() => {
              onSearchArea(visibleArea(mapRef.current as L.Map))
              setMoved(false)
            }}>
            {t('map.searchArea')}
          </button>
        )}
      </div>
      {missing > 0 && <p className="geography-picker-hint">{tp('map.someMissing', missing)}</p>}
      {!showSelectedCard ? null : selected ? (
        <div className="properties-map-card" data-testid="map-selected-card">
          <button type="button" className="properties-map-card-close btn btn-secondary btn-sm" onClick={() => select(null)}>
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
