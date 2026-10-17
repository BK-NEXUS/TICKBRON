// One place for the tile source: the host must also be listed in the CSP `img-src` (.ai/RELEASE_CHECKLIST.md).
export const TILE_URL = 'https://tile.openstreetmap.org/{z}/{x}/{y}.png'

// The OpenStreetMap tile licence requires this credit on every map
export const TILE_ATTRIBUTION = '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener noreferrer">OpenStreetMap</a> contributors'

/** Uzbekistan, shown when nothing says where to look */
export const DEFAULT_CENTER: [number, number] = [41.3, 64.6]
export const DEFAULT_ZOOM = 5
