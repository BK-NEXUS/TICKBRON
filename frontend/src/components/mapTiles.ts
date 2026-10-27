// One place for the tile source: the host must also be listed in the CSP `img-src` (.ai/RELEASE_CHECKLIST.md).
export const TILE_URL = 'https://tile.openstreetmap.org/{z}/{x}/{y}.png'

// The OpenStreetMap tile licence requires this credit on every map
export const TILE_ATTRIBUTION = '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener noreferrer">OpenStreetMap</a> contributors'

/** Uzbekistan, shown when nothing says where to look */
export const DEFAULT_CENTER: [number, number] = [41.3, 64.6]
export const DEFAULT_ZOOM = 5

// The satellite pictures. Esri's World Imagery is the default (it needs its credit on the map). Its terms are
// for light use: before the site has real traffic choose a provider with a key and set both variables;
// its host must also be in the CSP `img-src` (.ai/RELEASE_CHECKLIST.md).
export const SATELLITE_URL: string =
  import.meta.env.VITE_SATELLITE_TILE_URL || 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'

export const SATELLITE_ATTRIBUTION: string =
  import.meta.env.VITE_SATELLITE_ATTRIBUTION || 'Tiles &copy; Esri &mdash; Source: Esri, Maxar, Earthstar Geographics, and the GIS User Community'
